from pathlib import Path
from datetime import datetime
import hashlib, re, unicodedata

class SourceError(ValueError):
    pass

def _n(value):
    return unicodedata.normalize('NFC', str(value))

def _range(value):
    if not re.fullmatch(r'\d{4}(?:-\d{4})?',value):
        raise SourceError('invalid-date: '+value)
    parts=value.split('-')
    try:
        for p in parts: datetime.strptime('2000'+p,'%Y%m%d')
    except ValueError:
        raise SourceError('invalid-date: '+value) from None
    if parts[0]>parts[-1]: raise SourceError('invalid-date: reversed range')
    return parts[0],parts[-1]

def asset_path(root, relative):
    base=Path(root).resolve()
    result=(base/relative).resolve()
    if not result.is_relative_to(base) or not result.is_file():
        raise SourceError('unsafe-asset: '+str(relative))
    return result

def discover(repo, selector, *, extra_sources=()):
    from .course_sources import resolve_problem_sources, local_file
    repo=Path(repo).resolve()
    requested=Path(selector)
    folders=[]
    if requested.is_dir():
        folders=[requested.resolve()]
        names={m.group(1) for f in folders[0].iterdir()
               if (m:=re.match(r'정리노트_(\d{4}(?:-\d{4})?)_',_n(f.name)))}
        if len(names)!=1: raise SourceError('ambiguous: folder note ranges')
        selected=names.pop(); _range(selected)
    else:
        selected=_n(selector); lo,hi=_range(selected)
        base=repo/'복습노트'
        if not base.is_dir(): raise SourceError('missing: 복습노트')
        candidates=[]
        for p in base.iterdir():
            if p.is_dir() and re.fullmatch(r'\d{4}(?:-\d{4})?',_n(p.name)):
                a,b=_range(_n(p.name))
                if a<=hi and b>=lo: candidates.append((a,b,p))
        exact=[p for a,b,p in candidates if _n(p.name)==selected]
        if len(exact)>1: raise SourceError('ambiguous: '+str(exact))
        if exact: folders=exact
        else:
            candidates.sort(key=lambda x:x[0])
            for i,(a,b,p) in enumerate(candidates):
                if a<lo or b>hi or (i and a<=candidates[i-1][1]):
                    raise SourceError('ambiguous: overlapping ranges '+str([str(x[2]) for x in candidates]))
            folders=[p for a,b,p in candidates]
    if not folders: raise SourceError('missing: '+selected)
    if any(not f.is_relative_to(repo) for f in folders): raise SourceError('unsafe-asset: folder outside repo')
    files=[]; seen=set(); problem_ids=[]
    for folder in folders:
        for p in sorted(folder.rglob('*')):
            if not p.is_file(): continue
            relative=_n(str(p.relative_to(folder)))
            logical=(_n(str(folder)),relative)
            if logical in seen: raise SourceError('ambiguous: Unicode duplicate '+relative)
            seen.add(logical)
            name=_n(p.name)
            if name=='problems.txt':
                kind='problem-list'
                problem_ids.extend(_n(line.split('|',1)[0].strip()) for line in p.read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.lstrip().startswith('#'))
            elif p.suffix.lower()=='.pdf' and ('답안' in name or '해설' in name): kind='answers-pdf'
            elif name.startswith('복습문제_') and p.suffix.lower()=='.pdf': kind='questions-pdf'
            elif name.startswith('정리노트_') and p.suffix in ('.html','.md'): kind='note-'+p.suffix[1:]
            elif name.startswith('복습문제_') and p.suffix in ('.html','.md'): kind='questions-'+p.suffix[1:]
            elif name.startswith('장마감_') and p.suffix=='.md': kind='chapter-audit'
            elif p.suffix.lower() in ('.svg','.png','.jpg','.jpeg','.webp'): kind='figure'
            else: continue
            if not p.resolve().is_relative_to(folder.resolve()): raise SourceError('unsafe-asset: symlink')
            try: stable=_n(p.relative_to(repo))
            except ValueError: stable=_n(p)
            files.append({'id':'src-'+hashlib.sha256(stable.encode()).hexdigest()[:16],
                          'kind':kind,'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    resolved=resolve_problem_sources(repo,problem_ids)
    added=resolved['files'][:]
    for extra in extra_sources:
        p=local_file(repo,extra)
        ext=p.suffix.lower()
        kind='supplemental-'+ext[1:] if ext in ('.md','.pdf','.html') else 'supplemental-figure' if ext in ('.svg','.png','.jpg','.jpeg','.webp') else None
        if not kind: raise SourceError('unsupported supplemental source: '+str(p))
        added.append({'kind':kind,'path':str(p)})
    for rec in added:
        p=Path(rec['path'])
        if any(x['path']==str(p) for x in files): continue
        stable=_n(p.relative_to(repo))
        files.append({'id':'src-'+hashlib.sha256(stable.encode()).hexdigest()[:16],'kind':rec['kind'],'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    by_path={x['path']:x['id'] for x in files}
    relations=[{'from_id':by_path[x['from_path']],'to_id':by_path[x['to_path']],'role':x['role']} for x in resolved['relations']]
    if len({x['id'] for x in files})!=len(files): raise SourceError('ambiguous: Unicode source duplicate')
    if not any(x['kind'].startswith('note-') for x in files): raise SourceError('missing: note HTML/MD')
    missing=[k for k in ('questions','chapter-audit') if not any(x['kind'].startswith(k) for x in files)]
    return {'range':selected,'files':files,'missing_optional':missing,'missing_problem_ids':resolved['missing_problem_ids'],'relations':relations}
