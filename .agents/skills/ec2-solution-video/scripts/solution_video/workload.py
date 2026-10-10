"""Estimate changing-frame coverage from the timeline actually embedded in a part.

Pencil/annotation spans and camera transitions are intervals; typing covers its
reveal cadence up to the last event. Holds contribute no motion. This is an
estimate of authored activity, not pixel sampling or a throughput guarantee.
"""
import json
import math
from pathlib import Path
from .contracts import InputError
from .util import local,read


def _integer(value):
    if type(value) is not int:
        raise InputError('motion metadata requires integer frames/samples')
    return value


def part_motion_profile(run,part):
    first=_integer(part['first_frame']);last=_integer(part['last_frame'])
    if first<0 or last<=first:raise InputError('invalid render part frame range')
    frames=last-first
    unknown=dict(status='unknown',part_frames=frames,animated_frames=None,animated_seconds=None,motion_ratio=None)
    html=local(Path(run).resolve(),part['entry']);path=html.parent/'timeline.json'
    try:
        # Parse every present file before falling back, so corruption stays visible.
        saved_present=path.is_file()
        saved=read(path) if saved_present else None
        text=html.read_text(encoding='utf-8') if html.is_file() else ''
        marker='window.solutionTimeline='
        count=text.count(marker)
        if count>1:raise InputError('repeated embedded solution timeline')
        embedded=json.JSONDecoder().raw_decode(text.split(marker,1)[1].lstrip())[0] if count else None
        if (saved_present and not isinstance(saved,dict)) or (count and not isinstance(embedded,dict)):
            raise InputError('solution timeline must be an object')
        missing=saved is None or embedded is None
        if not missing and saved!=embedded:
            raise InputError('compiled and embedded solution timelines differ')
        t=embedded if embedded is not None else saved
        if t is None:return unknown
        total=_integer(t['total_frames'])
        if t['fps']!=30 or t['rate']!=24000 or total<=0 or _integer(t['total_samples'])!=total*800 or last>total:
            raise InputError('motion timeline must match 24kHz/30fps part')
        intervals=[]
        def interval(left,right):
            left=_integer(left);right=_integer(right)
            if not 0<=left<right<=total:raise InputError('motion interval outside timeline')
            a,b=max(first,left),min(last,right)
            if b>a:intervals.append((a,b))
        def spans(rows,annotation=False):
            if not isinstance(rows,list):raise InputError('motion spans must be a list')
            for row in rows:
                if row['kind'] not in (('draw','move','space') if annotation else ('draw','move')):raise InputError('unknown motion span kind')
                left=_integer(row['start_frame']);right=_integer(row['end_frame'])
                if not 0<=left<right<=total:raise InputError('motion span outside timeline')
                if annotation:
                    hide=_integer(row['hide_frame'])
                    if not left<hide<=total:raise InputError('annotation hide outside timeline')
                    right=min(right,hide)
                if row['kind']!='space':interval(left,right)
        events=t['events'];segments=t['segments'];cameras=t['cameras']
        if not all(isinstance(rows,list) for rows in (events,segments,cameras)):
            raise InputError('motion events, segments and cameras must be lists')
        event_frames=[_integer(e['frame']) for e in events]
        if any(f<0 or f>=total for f in event_frames):raise InputError('reveal outside timeline')
        writing=t.get('writing')
        if writing is None:writing={}
        if not isinstance(writing,dict) or writing.get('mode','typing') not in ('typing','pencil'):
            raise InputError('unknown writing mode')
        # Validate available pencil metadata even in a legacy typing timeline.
        if 'writing_spans' in t:spans(t['writing_spans'])
        elif writing.get('mode')=='pencil':missing=True
        for seg in segments:
            left=_integer(seg['start_sample']);right=_integer(seg['end_sample'])
            if not 0<=left<right<=total*800:raise InputError('segment outside timeline')
            if writing.get('mode','typing')=='typing' and seg['kind']=='write':
                reveals=[f for f in event_frames if left<=f*800<right]
                if reveals:interval(left//800,min(total,max(reveals)+1))
        previous=None;previous_frame=-1;previous_mirror=False;camera_changes=[]
        for camera in cameras:
            at=_integer(camera['at_frame']);duration=_integer(camera.get('transition_frames',0));view=camera['viewbox']
            if not 0<=at<total or at<=previous_frame or duration<0 or at+duration>total:
                raise InputError('camera outside timeline or unordered')
            if not isinstance(view,list) or len(view)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in view) or view[2]<=0 or view[3]<=0:
                raise InputError('invalid camera viewbox')
            if previous is not None and previous!=view:
                camera_changes.append(at)
                if duration:interval(at,at+duration)
            elif previous is not None and previous_mirror!=bool(camera.get('mirror',False)):
                camera_changes.append(at)
            previous=view;previous_frame=at;previous_mirror=bool(camera.get('mirror',False))
        if t.get('teaching') is not None:spans(t['teaching']['spans'],annotation=True)
        # Instant reveal/page/camera changes count one frame; continuous movement
        # already included above is merged, never counted twice.
        for f in event_frames:interval(f,f+1)
        for at in camera_changes:interval(at,at+1)
        merged=[]
        for left,right in sorted(intervals):
            if merged and left<=merged[-1][1]:merged[-1]=(merged[-1][0],max(merged[-1][1],right))
            else:merged.append((left,right))
        active=sum(right-left for left,right in merged)
        if missing:return unknown
        return dict(status='known',part_frames=frames,animated_frames=active,animated_seconds=active/30,motion_ratio=active/frames)
    except (KeyError,TypeError,OverflowError,IndexError) as ex:
        raise InputError('invalid motion metadata: '+str(ex)) from ex
