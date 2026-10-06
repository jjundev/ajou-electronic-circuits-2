"""Resolve only requested problem closures, without importing workbook tooling."""
from pathlib import Path
import re, unicodedata
from urllib.parse import unquote, urlsplit
from .sources import SourceError

def normalized(value):
    return unicodedata.normalize('NFC', str(value))

def local_file(repo, path):
    repo=Path(repo).resolve(); path=Path(path)
    if not path.is_absolute(): path=repo/path
    candidate=path.resolve()
    if not candidate.is_relative_to(repo): raise SourceError('unsafe-asset: '+str(path))
    if candidate.is_file(): return candidate
    # Resolve Unicode spellings against the actual directory entries, including .. .
    current=repo
    for part in path.relative_to(repo).parts:
        if part=='.': continue
        if part=='..': current=current.parent; continue
        matches=[p for p in current.iterdir() if normalized(p.name)==normalized(part)] if current.is_dir() else []
        if len(matches)!=1: raise SourceError('missing or ambiguous local source: '+str(path))
        current=matches[0]
    candidate=current.resolve()
    if not candidate.is_relative_to(repo) or not candidate.is_file(): raise SourceError('unsafe or missing source: '+str(path))
    return candidate

def resolve_problem_sources(repo: Path, ids: list[str]) -> dict:
    import yaml
    repo=Path(repo).resolve(); index={}; files={}; relations=[]; missing=[]; visiting=set(); done=set()
    for folder in repo.iterdir():
        if normalized(folder.name) not in ('교과서','from_the_past'): continue
        for path in sorted(folder.rglob('*.md')):
            text=path.read_text(encoding='utf-8-sig')
            match=re.match(r'^---\s*\n(.*?)\n---(?:\n|$)',text,re.S)
            if not match: continue
            try: meta=yaml.safe_load(match[1])
            except yaml.YAMLError as ex: raise SourceError('invalid frontmatter: '+str(path)) from ex
            if isinstance(meta,dict) and isinstance(meta.get('id'),str):
                index.setdefault(normalized(meta['id']),[]).append((path,meta,text))
    def visit(id):
        id=normalized(id)
        if id in visiting: raise SourceError('problem dependency cycle: '+id)
        if id in done: return
        rows=index.get(id,[])
        if not rows:
            if id not in missing: missing.append(id)
            return
        if len(rows)!=1: raise SourceError('duplicate problem id: '+id)
        p,meta,text=rows[0];p=local_file(repo,p);files[p]='problem-md';visiting.add(id)
        for key,role in [('depends_on','depends_on'),('refs','reference')]:
            values=meta.get(key,[]) or []
            if not isinstance(values,list): raise SourceError('expected list '+key+': '+id)
            for value in values:
                value=normalized(value)
                if not re.fullmatch(r'(?:[EXP]\d+\.\d+|\d{4}-\d+_.+-Q\d+)',value): continue
                visit(value)
                if value in index and len(index[value])==1:
                    relations.append({'from_path':str(p),'to_path':str(index[value][0][0].resolve()),'role':role})
        targets=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
        for fig in meta.get('figures',[]) or []:
            if isinstance(fig,str): targets.append(fig)
            elif isinstance(fig,dict) and fig.get('path'): targets.append(fig['path'])
        for target in targets:
            target=target.strip().split(' "',1)[0].strip('<>')
            parsed=urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path: continue
            q=local_file(repo,p.parent/unquote(parsed.path))
            if q.suffix.lower() in ('.svg','.png','.jpg','.jpeg','.webp'):
                files[q]='figure';relations.append({'from_path':str(p),'to_path':str(q),'role':'figure'})
            elif q.suffix.lower()=='.md':
                rows=[k for k,v in index.items() if any(x[0].resolve()==q for x in v)]
                if rows: visit(rows[0])
                else: files[q]='problem-md'
                relations.append({'from_path':str(p),'to_path':str(q),'role':'reference'})
        visiting.remove(id);done.add(id)
    for id in ids: visit(id)
    unique={tuple(x.items()):x for x in relations}
    return {'files':[{'kind':kind,'path':str(path)} for path,kind in files.items()],
            'missing_problem_ids':missing,'relations':list(unique.values())}
