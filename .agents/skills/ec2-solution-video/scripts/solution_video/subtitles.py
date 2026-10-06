from pathlib import Path
import math,os,shutil,tempfile
from .util import checked
from .media import ffmpeg
from .contracts import InputError

def _stamp(samples,rate):
    ms=round(samples*1000/rate); sec,ms=divmod(ms,1000); minutes,sec=divmod(sec,60); hr,minutes=divmod(minutes,60)
    return f'{hr:02d}:{minutes:02d}:{sec:02d},{ms:03d}'
def write_srt(timeline,dest):
    lines=[]; num=0
    for seg in timeline['segments']:
        text=' '.join(seg['text'].split()); chunks=[]
        while text:
            pos=min(34,len(text))
            if pos<len(text):
                space=text.rfind(' ',0,pos+1)
                if space>12: pos=space
            chunks.append(text[:pos].strip()); text=text[pos:].lstrip()
        duration=seg.get('voice_samples',seg['end_sample']-seg['start_sample']); weights=sum(len(c) for c in chunks); start=seg['start_sample']; offset=0
        for c in chunks:
            end=start+round(duration*(offset+len(c))/weights); begin=start+round(duration*offset/weights); offset+=len(c)
            if end-begin<24: raise InputError('caption too short for millisecond resolution')
            num+=1; lines.append(f'{num}\n{_stamp(begin,timeline["rate"])} --> {_stamp(end,timeline["rate"])}\n{c}\n')
    dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text('\n'.join(lines),encoding='utf-8'); return dest

def burn_subtitles(master,srt,dest,font):
    master,srt,dest,font=map(lambda p:Path(p).resolve(),[master,srt,dest,font])
    if dest==master: raise InputError('cannot overwrite master with captions')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ec2-captions-') as td:
        work=Path(td); (work/'fonts').mkdir(); shutil.copyfile(font,work/'fonts/Pretendard-Bold.ttf'); shutil.copyfile(srt,work/'subs.srt')
        style='FontName=Pretendard,FontSize=14,Bold=1,Alignment=2,MarginV=22,Outline=4,Shadow=0,BorderStyle=3,PrimaryColour=&HFFFFFF&,OutlineColour=&H4D0E0B0B,BackColour=&H4D0E0B0B'
        pending=dest.with_name(dest.stem+'.pending.mp4')
        checked([ffmpeg(),'-y','-v','error','-i',master,'-vf',"subtitles=subs.srt:fontsdir=fonts:force_style='"+style+"'",'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','copy',pending],cwd=work,timeout=1800)
        os.replace(pending,dest)
    return dest
