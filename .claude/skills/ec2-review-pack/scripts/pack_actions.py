"""Fixed, guarded machine actions. Review decisions remain in original gates.

A durable stopped.json is written only after wait() returns. An interrupted
controller without that evidence cannot launch another command or restore files.
"""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

import pack_flow as f
from pack_files import inventory_pack, prepare_pack, recover_pack
from pack_publication import publication_lock, child_lock_options

ACTIONS = frozenset(('prepare-pack','assemble-note','build-problems','precheck',
    'convert-md','publish-explanation','build-answers','publish-answer','final-check'))
READ_ONLY = frozenset(('precheck', 'final-check'))
# Writes only inside RUN (the answer PDF goes to RUN/answers); a failure leaves the pack untouched.
RUN_ONLY = frozenset(('build-answers',))


def _paths(state):
    import manifest
    run, repo = Path(state['run']), Path(state['repo'])
    m = f._read(run/'manifest.json')
    if m['range'] != state['range']: raise f.FlowError('manifest range differs from RUN')
    pack = repo/'복습노트'/state['range']
    for target in (pack,pack/'.assets',run/'answers'):
        root=repo if target.is_relative_to(repo) else run
        if not target.resolve().is_relative_to(root.resolve()): raise f.FlowError('output escapes owning root')
        for ancestor in [target,*target.parents]:
            if ancestor==root: break
            if ancestor.is_symlink(): raise f.FlowError('symlink output directory')
    return dict(run=run, repo=repo, m=m, pack=pack,
        note=pack/manifest.note_name(m), md=pack/'.assets'/Path(manifest.note_name(m)).with_suffix('.md'),
        problems=pack/manifest.problem_pdf_name(m), answer=pack/manifest.answer_pdf_name(m),
        answer_run=run/'answers'/manifest.answer_pdf_name(m),
        overlay=Path(state.get('published_overlay', str(pack/'.assets'/f"자료_문제설명_{m['range']}_{m['slug']}"/'answer-overlay.json'))))


def action_argv(state: dict, action: str) -> list[str]:
    if action not in ACTIONS or action == 'prepare-pack':
        raise f.FlowError('action has no permitted command: ' + action)
    p=_paths(state); run, repo, m=p['run'],p['repo'],p['m']
    scripts=repo/'.claude/skills/ec2-review-pack/scripts'
    if action=='assemble-note':
        args=[scripts/'assemble.py','--repo',repo,'--run',run,'--out',p['pack']]
    elif action in ('precheck','final-check'):
        args=[scripts/'check_html.py','--repo',repo,'--manifest',run/'manifest.json','--note',p['note']]
        if action=='precheck': args.append('--defer-answer-pdf')
    elif action=='convert-md':
        args=[scripts/'html2md.py',p['note'],'--check']
        if m['problems']: args += ['--manifest',run/'manifest.json','--defer-answer-pdf']
    elif action=='publish-explanation':
        if not state.get('explain_run'): raise f.FlowError('current child RUN required')
        args=[repo/'.claude/skills/ec2-problem-explain/scripts/epe_cli.py','publish','--run',state['explain_run']]
    elif action=='publish-answer':
        attempt=state['actions'][action]['attempt_dir']
        args=[scripts/'publish_answer.py','--repo',repo,'--overlay',p['overlay'],
            '--pdf',state['answer_pdf'],'--review',run/'answer-review.json',
            '--destination',p['answer'],'--backup-dir',Path(attempt)/'answer-backup']
    else:
        answers=action=='build-answers'
        args=[repo/'workbook/build_workbook.py','--ids',','.join(q['id'] for q in m['problems']),
            '--name',f"복습문제_{m['range']}_{m['slug']}",'--mode','answers' if answers else 'problems',
            '--selection',p['pack']/'.assets/selection.json','--display-titles',p['pack']/'.assets/display-titles.json',
            '--layout','video-16x9','--pdf-dir',run/'answers' if answers else p['pack'],
            '--build-dir',run/('answer-build' if answers else 'workbook-build')]
        if answers: args += ['--answer-overlay',p['overlay']]
    return [sys.executable,*map(str,args)]


def _gate_call(folder, function, *args, **kwargs):
    # Third-party imports may print warnings. Keep those in the same file logs.
    with (folder/'stdout.log').open('a',encoding='utf-8') as out, (folder/'stderr.log').open('a',encoding='utf-8') as err:
        with redirect_stdout(out), redirect_stderr(err):
            return function(*args,**kwargs)


def _records(paths):
    return [{'path':str(p.resolve()),'sha256':f._sha(p)} for p in sorted(set(map(Path,paths)),key=str)]


def _verify(items):
    from pack_receipts import verify_receipt_files
    errors=verify_receipt_files({'verified_files':items})
    if errors: raise f.FlowError('changed action evidence: '+ '; '.join(errors))


@contextmanager
def _action_lock(run):
    # Independent from short state transactions, held over the entire process.
    folder=Path(run)/'work/actions'; folder.mkdir(parents=True,exist_ok=True)
    with f._locked(folder): yield


@contextmanager
def _live_locks(run):
    with _action_lock(run):
        state = f.load_state(run)
        pack = Path(state['repo']) / '복습노트' / state['range']
        with publication_lock(pack):
            yield pack


def _retry_stopped_conversion(state, action):
    record=state['actions'].get(action,{})
    if action!='convert-md' or state['status']!='recovery_required' or record.get('status')!='recovery_required':
        return False
    if state.get('explain_run') or state.get('stale_explain_runs') or state['tasks'].get('child-coordinator',{}).get('attempt'):
        raise f.FlowError('conversion retry forbidden after child allocation/extract; parent revalidation required')
    if not record.get('inventory_trusted') or record.get('invalidated_active') or 'last_inventory' not in state['recovery']:
        raise f.FlowError('conversion retry requires trusted stopped failure')
    if any(name!=action and item.get('status')=='recovery_required' for name,item in state['actions'].items()):
        raise f.FlowError('another action still requires recovery')
    try:
        folder=Path(record['attempt_dir'])
        stopped=f._read(folder/'stopped.json'); result=f._read(folder/'result.json'); started=f._read(folder/'started.json')
        if (stopped.get('attempt')!=record['attempt'] or result.get('attempt')!=record['attempt']
            or started.get('attempt')!=record['attempt'] or result.get('action')!=action
            or type(stopped.get('exit_code')) is not int or stopped['exit_code']==0
            or result.get('exit_code')!=stopped['exit_code'] or record.get('exit_code')!=stopped['exit_code']
            or result.get('inventory_trusted') is not True or result.get('status')!='recovery_required'
            or not started.get('inputs') or started['inputs']!=result.get('inputs') or result['inputs']!=record.get('inputs')):
            raise f.FlowError('conversion retry failure/stop evidence mismatch')
        _verify(started['inputs'])
        if _pre_action_inventory(state)!=stopped['inventory']:
            raise f.FlowError('conversion retry inventory differs from stopped command')
        _verify_inventory_delta(started['inventory'],stopped['inventory'],started['write_set'])
    except (OSError,KeyError,TypeError,ValueError) as exc:
        raise f.FlowError('conversion retry requires intact stopped evidence: '+str(exc)) from exc
    return True


def _guard(state, action):
    if action not in ACTIONS: raise f.FlowError('unknown action: '+action)
    f._current(state)
    retry=_retry_stopped_conversion(state,action)
    if (state['status'] in ('recovery_required','withheld') and not retry) or state['stale_inputs']:
        raise f.FlowError('recovery or frozen input reconciliation required')
    record=state['actions'].get(action)
    if not record or record.get('invalidated_active') or (record['status'] not in ('pending','stale','needs_fix') and not retry):
        raise f.FlowError('action is not ready; reconcile prior attempt first')
    if any(not f._done(state,d) for d in record['dependencies']): raise f.FlowError('action dependencies not current')
    if record.get('attempt_dir') and not (Path(record['attempt_dir'])/'stopped.json').is_file():
        raise f.FlowError('prior command stopped evidence required')
    for other in state['actions'].values():
        if other.get('invalidated_active') or other['status']=='running': raise f.FlowError('prior command requires reconciliation')


def _inputs(state, action):
    p=_paths(state); run=p['run']
    frozen={str(Path(path).resolve()):digest for path,digest in state['hashes'].items()}
    paths={Path(x) for x in frozen}; paths.add(run/'manifest.json')
    record=state['actions'][action]
    for dep in record['dependencies']:
        predecessor=f._record(state,dep)
        evidence=predecessor.get('receipt',predecessor) or {}
        for item in evidence.get('verified_files',[]):
            path=str(Path(item['path']).resolve())
            if path in frozen and frozen[path]!=item['sha256']: raise f.FlowError('conflicting frozen action input')
            frozen[path]=item['sha256']; paths.add(Path(path))
    if action in ('prepare-pack','assemble-note'):
        paths.update(run/'sections'/ (s['id']+'.html') for s in p['m']['sections'])
        for name in ('selection.json','display-titles.json'):
            if (run/name).exists(): paths.add(run/name)
    if action not in ('prepare-pack','assemble-note'): paths.add(p['note'])
    if action in ('precheck','final-check'): paths.add(Path(state['active_audit']))
    if action=='final-check':
        paths.add(p['md'])
        paths.update((p['pack']/'.assets'/('figures_'+state['range'])).glob('*.svg'))
    if action in ('build-problems','build-answers'):
        import manifest
        for problem in p['m']['problems']:
            source=manifest.problem_md_path(p['repo'],problem['id'])
            paths.add(source)
            # Workbook figure metadata and local figures are immutable rendering inputs.
            figures=source.parent.parent/'figures' if source.parent.name in ('예제','연습문제','장말문제') else source.parent/'figures'
            if figures.is_dir(): paths.update(x for x in figures.rglob('*') if x.is_file())
            if (source.parent/'exam.yaml').exists(): paths.add(source.parent/'exam.yaml')
        paths.update(p['pack']/'.assets'/name for name in ('selection.json','display-titles.json','problems.txt'))
    if action=='publish-explanation':
        child=Path(state['explain_run'])/'child-receipt.json'; paths.add(child)
        receipt=f._read(child); _verify(receipt['files'])
        paths.update(Path(x['path']) for x in receipt['files'])
    if action in ('build-answers','publish-answer'):
        paths.update((p['overlay'],p['overlay'].with_name('validation.json')))
        _overlay(state)
        raw=f._read(p['overlay']); paths.update(p['repo']/name for name in raw['source_inputs'])
        validation=f._read(p['overlay'].with_name('validation.json'))
        paths.update(Path(item['path']) if Path(item['path']).is_absolute() else p['repo']/item['path'] for item in validation['references'])
        paths.update(p['pack']/name for name in validation['artifact_hashes'])
    if action=='publish-answer': paths.update((Path(state['answer_pdf']),Path(state['answer_overlay']),run/'answer-review.json'))
    records=_records(paths)
    if any(item['path'] in frozen and item['sha256']!=frozen[item['path']] for item in records):
        raise f.FlowError('frozen action input changed before launch')
    return records


def _overlay(state):
    workbook=Path(__file__).resolve().parents[4]/'workbook'
    if str(workbook) not in sys.path[:1]: sys.path.insert(0,str(workbook))
    from answer_overlay import load_answer_overlay
    p=_paths(state)
    overlay=load_answer_overlay(p['overlay'],p['repo'],[x['id'] for x in p['m']['problems']])
    return overlay


def _publication_outputs(state):
    """Compare every reviewed stage artifact plus validation against publication."""
    p=_paths(state); child=f._read(Path(state['explain_run'])/'child-receipt.json')
    stage=Path(child['stage']).resolve()
    items=[]
    for record in child['files']:
        source=Path(record['path']).resolve()
        if not source.is_relative_to(stage): continue
        if source.name=='validation.json': continue
        target=p['pack']/source.relative_to(stage)
        if not target.is_file() or f._sha(target)!=record['sha256']:
            raise f.FlowError('published stage mismatch: '+str(target))
        items.append(target)
    if not items: raise f.FlowError('empty reviewed publication')
    validation=p['overlay'].with_name('validation.json')
    review=Path(state['explain_run'])/child['bucket']/'review.json'
    if f._read(validation)!=f._read(review): raise f.FlowError('published validation differs from approved review')
    _overlay(state)
    return [*items,validation]


def _postconditions(state, action, folder):
    p=_paths(state)
    if action=='prepare-pack':
        data=f._read(folder/'prepare.json')
        from pack_files import _validate
        for name in ('basic','explanations'): _validate(f._read(data[name]),p['run'],state['range'])
        outputs=[Path(data['basic']),Path(data['explanations']),p['run']/'pack-first-inventory.json',folder/'prepare.json']
        if p['m']['problems']:
            title=p['pack']/'.assets/display-titles.json'
            if f._sha(title)!=f._sha(p['run']/'display-titles.json'): raise f.FlowError('title map copy mismatch')
            outputs.append(title)
        return outputs
    if action=='assemble-note':
        outputs=[p['note']]
        if p['m']['problems']:
            outputs += [p['pack']/'.assets/problems.txt']
            if p['m'].get('selection_policy')=='exam-first-v2':
                outputs += [p['pack']/'.assets/selection.json',p['pack']/'.pack/selection-review.json']
    elif action=='build-problems': outputs=[p['problems']]
    elif action in READ_ONLY:
        outputs=[p['note'],Path(state['active_audit'])]
        if action=='final-check':
            from html2md import check_md
            errors=check_md(p['note'],p['md'])  # Strict and read-only after child extract.
            if errors: raise f.FlowError('final MD check failed: '+'; '.join(errors))
            outputs.append(p['md'])
    elif action=='convert-md': outputs=[p['md'],*list((p['pack']/'.assets'/('figures_'+state['range'])).glob('*.svg'))]
    elif action=='publish-explanation': outputs=_publication_outputs(state)
    elif action=='build-answers':
        _overlay(state)
        outputs=[p['answer_run']]
    elif action=='publish-answer':
        _overlay(state)
        from publish_answer import _review
        review=_review(p['run']/'answer-review.json',Path(state['answer_pdf']),p['overlay'],f._read(p['overlay']))
        receipt_path=folder/'answer-backup/receipt.json'; receipt=f._read(receipt_path)
        if (receipt.get('destination')!=str(p['answer']) or receipt.get('pdf_sha256')!=f._sha(p['answer'])
            or receipt.get('pdf_sha256')!=review['pdf_sha256'] or receipt.get('overlay_sha256')!=f._sha(p['overlay'])
            or receipt.get('review_sha256')!=f._sha(p['run']/'answer-review.json')):
            raise f.FlowError('answer publication receipt mismatch')
        outputs=[p['answer'],receipt_path]
    for output in outputs:
        if not output.is_file() or output.stat().st_size==0: raise f.FlowError('expected output missing/empty: '+str(output))
    if action in ('build-answers','build-problems'):
        import pymupdf
        with pymupdf.open(outputs[0]) as pdf:
            if pdf.page_count<1: raise f.FlowError('empty PDF')
    return outputs


def _save_result(run, state, action, folder, result):
    f._atomic_json(folder/'result.json',result)
    def change(current):
        record=current['actions'][action]
        if record.get('attempt')!=result['attempt']: raise f.FlowError('action attempt changed')
        record.update(result)
        if result['status']=='done':
            record.pop('invalidated_active',None)
            record['verified_files']=[*result['inputs'],*result['outputs'],*_records([folder/'result.json',folder/'stopped.json'])]
            if action=='precheck': record['audit_sha256']=f._sha(Path(current['active_audit']))
            if action=='prepare-pack': current['backups']=f._read(folder/'prepare.json')
            if action=='publish-explanation':
                current['published_overlay']=str(_paths(current)['overlay'])
                current['publication']['explanation']=str(folder/'result.json')
            if action=='build-answers':
                p=_paths(current); copy=folder/'answer-overlay.json'
                shutil.copyfile(p['overlay'],copy)
                if f._sha(copy)!=f._sha(p['overlay']): raise f.FlowError('RUN overlay copy mismatch')
                current['answer_pdf']=str(p['answer_run']); current['answer_overlay']=str(copy)
                record['verified_files']+=_records([copy])
            if action=='publish-answer': current['publication']['answer']=str(folder/'result.json')
            current['status']='complete' if action=='final-check' else 'ready'
            f.refresh_tasks(current); f.write_briefs(current)
        else: current['status']='recovery_required' if result['status']=='recovery_required' else 'needs_fix'
        stopped=f._read(folder/'stopped.json') if (folder/'stopped.json').exists() else None
        if stopped and result.get('inventory_trusted'):
            current['recovery']['last_inventory']=stopped['inventory']
        return current
    f.update_state(run,f.load_state(run)['revision'],change)
    return result


def _pre_action_inventory(state):
    current=inventory_pack(Path(state['repo']),state['range'])
    trusted=state['recovery'].get('last_inventory')
    if trusted is not None and current!=trusted:
        raise f.FlowError('pack inventory differs from last trusted inventory; external change requires reconciliation')
    return current


def _write_set(state, action, before):
    """Freeze intended published writes before launch; RUN-only actions own none."""
    import re
    import unicodedata
    from pack_files import _kind
    p=_paths(state); m=p['m']; pack=p['pack']
    files=[]; removed=[]
    if action=='assemble-note':
        files=[p['note'],pack/'.assets/problems.txt']
        if m.get('selection_policy')=='exam-first-v2' and m['problems']:
            files += [pack/'.assets/selection.json',pack/'.pack/selection-review.json']
    elif action=='build-problems': files=[p['problems']]
    elif action=='publish-answer': files=[p['answer']]
    elif action=='convert-md':
        # Reuse the actual converter traversal and _fig_name contract on a RUN
        # snapshot. This covers sanitized IDs, collisions, anonymous SVGs and widgets.
        import html2md
        attempt=Path(state['actions'][action]['attempt_dir'])
        preview=attempt/'conversion-plan'; preview.mkdir()
        source=preview/p['note'].name; shutil.copyfile(p['note'],source)
        _gate_call(attempt,html2md.convert_note,source)
        root=f".assets/figures_{state['range']}"
        generated=[x.name for x in (preview/root).iterdir()] if (preview/root).exists() else []
        files=[p['md'],*[pack/root/name for name in generated]]
        # Legacy conversion removes old immediate SVGs before exporting; authorize
        # only those names already present, and only their deletion.
        removed += [name for name in before if name.startswith(root+'/')
                    and '/' not in name[len(root)+1:] and name.lower().endswith('.svg')]
        if not generated and root+'/' in before: removed.append(root+'/')
    elif action=='publish-explanation':
        child=f._read(Path(state['explain_run'])/'child-receipt.json'); stage=Path(child['stage']).resolve()
        files=[pack/Path(x['path']).resolve().relative_to(stage) for x in child['files']
               if Path(x['path']).resolve().is_relative_to(stage)]
        files.append(p['overlay'].with_name('validation.json'))
    elif action=='prepare-pack':
        keep={p['note'].relative_to(pack).as_posix(),p['md'].relative_to(pack).as_posix()}
        if m['problems']:
            files=[pack/'.assets/display-titles.json']; keep.add(p['problems'].name)
            listing=pack/'.assets/problems.txt'
            old_ids=[line.split('|',1)[0].strip() for line in listing.read_text(encoding='utf-8').splitlines() if line.strip()] if listing.exists() else []
            if old_ids==[q['id'] for q in m['problems']]: keep.add(p['answer'].name)
        for name in before:
            plain=name.rstrip('/'); nfc=unicodedata.normalize('NFC',plain)
            parents=[plain,*[q.as_posix() for q in Path(plain).parents if q.as_posix()!='.']]
            explanation=any(_kind(q,state['range'])=='explanations' for q in parents)
            obsolete=bool(re.fullmatch(r'정리노트_[^/]+\.html|복습문제_[^/]+-(문제|답안)\.pdf|\.assets/정리노트_[^/]+\.md',nfc)) and nfc not in keep
            if explanation or obsolete: removed.append(name)
    relative={x.relative_to(pack).as_posix() for x in files}
    directories={q.as_posix()+'/' for name in relative for q in Path(name).parents if q.as_posix()!='.'}
    return dict(files=sorted(relative),directories=sorted(directories),removed=removed)


def _verify_inventory_delta(before, after, writes):
    for name in before.keys() | after.keys():
        if before.get(name)==after.get(name): continue
        if name in writes['removed'] and name not in after: continue
        if name in writes['files']: continue
        if name in writes['directories'] and after.get(name)=='directory': continue
        raise f.FlowError('unexpected pack inventory change outside action write set: '+name)


def run_action(run: Path, action: str) -> dict:
    run=Path(run).resolve()
    with _live_locks(run) as public_pack:
        state=f.load_state(run); _guard(state,action)
        before=_pre_action_inventory(state)
        attempt=str(uuid4()); folder=run/'work/actions'/action/attempt; folder.mkdir(parents=True)
        result=dict(action=action,attempt=attempt,status='running',exit_code=None,
            stdout_path=str(folder/'stdout.log'),stderr_path=str(folder/'stderr.log'),inputs=[],outputs=[],error_code=None)
        def start(s):
            nonlocal before
            _guard(s,action)
            before=_pre_action_inventory(s)
            previous=s['actions'][action]
            if previous.get('attempt'):
                previous.setdefault('history',[]).append({k:v for k,v in previous.items() if k!='history'})
            previous.update(result,attempt_dir=str(folder))
            s['status']='running'; return s
        state=f.update_state(run,state['revision'],start)
        process=None
        mutation_started=False
        writes=None
        for key in ('stdout_path','stderr_path'): Path(result[key]).touch()
        try:
            if action in ('prepare-pack','assemble-note'):
                import manifest
                _gate_call(folder,manifest.load,run/'manifest.json',repo=Path(state['repo']))
            result['inputs']=_gate_call(folder,_inputs,state,action)
            if _pre_action_inventory(state)!=before: raise f.FlowError('pack inventory changed before launch')
            writes=_write_set(state,action,before)
            f._atomic_json(folder/'started.json',dict(result,inventory=before,write_set=writes))
            if action in ('precheck','final-check'):
                shutil.copyfile(state['active_audit'],run/'learning-style-audit.json')
            with open(result['stdout_path'],'ab') as stdout, open(result['stderr_path'],'ab') as stderr:
                if action=='prepare-pack':
                    titles=run/'display-titles.json'
                    if _paths(state)['m']['problems']:
                        from display_titles import load_display_titles
                        load_display_titles(titles,[q['id'] for q in _paths(state)['m']['problems']])
                    mutation_started=True
                    data=prepare_pack(Path(state['repo']),run,run/'manifest.json')
                    if _paths(state)['m']['problems']:
                        destination=_paths(state)['pack']/'.assets/display-titles.json'
                        destination.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copyfile(titles,destination)
                    f._atomic_json(folder/'prepare.json',data)
                    result['exit_code']=0
                else:
                    argv=action_argv(state,action)
                    f._atomic_json(folder/'command.json',{'argv':argv,'cwd':state['repo']})
                    with child_lock_options(public_pack) as options:
                        process=subprocess.Popen(argv,cwd=state['repo'],shell=False,stdout=stdout,stderr=stderr, **options)
                    mutation_started=True
                    f._atomic_json(folder/'process.json',{'pid':process.pid,'attempt':attempt})
                    result['exit_code']=process.wait()
            f._atomic_json(folder/'stopped.json',{'attempt':attempt,'exit_code':result['exit_code'],
                'inventory':inventory_pack(Path(state['repo']),state['range'])})
            _verify(result['inputs'])
            _verify_inventory_delta(before,inventory_pack(Path(state['repo']),state['range']),writes)
            result['inventory_trusted']=True
            if result['exit_code']!=0: raise f.FlowError('command failed')
            result['outputs']=_records(_gate_call(folder,_postconditions,state,action,folder))
            result['status']='done'
        except (Exception, KeyboardInterrupt) as exc:
            if process is not None and process.poll() is None:
                # No recovery may race this process. Preserve evidence for reconciliation.
                result['status']='recovery_required'
            else:
                f._atomic_json(folder/'stopped.json',{'attempt':attempt,'exit_code':result['exit_code'],
                    'inventory':inventory_pack(Path(state['repo']),state['range'])})
                try: changed=before is not None and inventory_pack(Path(state['repo']),state['range'])!=before
                except (OSError,ValueError): changed=True
                # RUN-only and read-only commands can be retried unless the pack itself changed.
                result['status']=('recovery_required' if changed or (mutation_started and action not in READ_ONLY|RUN_ONLY)
                                  else 'needs_fix')
            try:
                _verify(result['inputs'])
                if writes is None: raise f.FlowError('action write set not frozen')
                _verify_inventory_delta(before,inventory_pack(Path(state['repo']),state['range']),writes)
                result['inventory_trusted']=bool(result['inputs']) and ((process is not None and process.poll() is not None) or (action=='prepare-pack' and mutation_started))
            except (OSError,ValueError):
                result['inventory_trusted']=False
            result['error_code']=type(exc).__name__
            (folder/'error.txt').write_text(str(exc),encoding='utf-8')
        return _save_result(run,state,action,folder,result)


def reconcile_action(run: Path, action: str) -> dict:
    run=Path(run).resolve()
    with _live_locks(run):
        state=f.load_state(run)
        if action not in ACTIONS or action not in state['actions']: raise f.FlowError('unknown action')
        record=state['actions'][action]; folder=Path(record['attempt_dir'])
        result={k:record.get(k) for k in ('action','attempt','status','exit_code','stdout_path','stderr_path','inputs','outputs','error_code')}
        result.update(action=action,status='recovery_required',error_code='incomplete_evidence')
        try:
            stopped=f._read(folder/'stopped.json')
            if stopped['attempt']!=record['attempt'] or stopped['exit_code']!=0: raise f.FlowError('no successful stopped completion')
            started=f._read(folder/'started.json'); _verify(started['inputs'])
            _verify_inventory_delta(started['inventory'],stopped['inventory'],started['write_set'])
            if inventory_pack(Path(state['repo']),state['range'])!=stopped['inventory']: raise f.FlowError('pack changed since command stopped')
            f._current(state)
            if state['stale_inputs'] or any(not f._done(state,d) for d in record['dependencies']): raise f.FlowError('predecessor evidence changed')
            result.update(inputs=started['inputs'],outputs=_records(_gate_call(folder,_postconditions,state,action,folder)),exit_code=0,status='done',error_code=None,inventory_trusted=True)
        except (OSError,ValueError,KeyError) as exc:
            folder.mkdir(parents=True,exist_ok=True); (folder/'reconcile-error.txt').write_text(str(exc),encoding='utf-8')
        return _save_result(run,state,action,folder,result)


def _require_stopped(state, record):
    folder=Path(record['attempt_dir'])
    stopped=folder/'stopped.json'
    if stopped.is_file():
        if f._read(stopped).get('attempt')!=record['attempt']: raise f.FlowError('stopped attempt mismatch')
        return
    confirmation=folder/'stopped-confirmation.json'
    if not confirmation.is_file(): raise f.FlowError('command stopped completion evidence required')
    data=f._read(confirmation)
    if (data.get('schema_version')!=1 or data.get('attempt')!=record['attempt']
        or not isinstance(data.get('confirmed_by'),str) or not data['confirmed_by'].strip()
        or not isinstance(data.get('reason'),str) or not data['reason'].strip()
        or data.get('process')!=f._read(folder/'process.json')):
        raise f.FlowError('invalid main-owned stopped confirmation')
    # A human-confirmed stop says nothing about who wrote unknown current bytes.
    expected=state['recovery'].get('last_inventory')
    if expected is None or inventory_pack(Path(state['repo']),state['range'])!=expected:
        raise f.FlowError('stopped confirmed, but partial writes have no trusted inventory proof')


def recover_run(run: Path) -> dict:
    run=Path(run).resolve()
    with _live_locks(run):
        state=f.load_state(run)
        for record in state['actions'].values():
            for attempt in [*record.get('history',[]),record]:
                if attempt.get('attempt_dir'): _require_stopped(state,attempt)
        if 'last_inventory' not in state['recovery']: raise f.FlowError('saved post-write inventory required')
        result=recover_pack(Path(state['repo']),run,state['range'],state['recovery']['last_inventory'])
        def change(s):
            s['status']='withheld'; s['recovery'].update(result)
            for record in s['actions'].values():
                if record.get('attempt'): record['status']='withheld'; record.pop('invalidated_active',None)
            return s
        f.update_state(run,state['revision'],change)
        return result


def write_report(run: Path) -> Path:
    run=Path(run).resolve(); state=f.inspect_state(run)
    report=run/'report.json'
    selection=run/'selection.json'; scope=run/'scope.json'
    f._atomic_json(report,{'range':state['range'],'status':state['status'],'phase':state['phase'],
        'scope':f._read(scope) if scope.exists() else None,'selection':f._read(selection) if selection.exists() else None,
        'files':inventory_pack(Path(state['repo']),state['range']), 'checks':state['actions'],
        'backups':state['backups'],'recovery':state['recovery'],'publication':state['publication'],
        'concept_check': f.concept_check_result(state) or (
            {'status':'pending'} if state.get('concept_check_enabled') and state['status']=='complete' else None),
        'seeded_from':state.get('seeded_from')})
    return report


def compose_candidate_view(repo, public_pack, attempt, adopted):
    """Copy digest-bound producer files into an empty, attempt-private public layout."""
    import manifest  # initializes the shared workbook module path
    from pack_paths import ATTEMPT_MARKER, PackPaths, checked_file
    import unicodedata

    attempt = Path(attempt).absolute()
    public_pack = Path(public_pack)
    view_root = checked_file(attempt, Path('복습노트')/public_pack.name)
    paths = PackPaths(repo, public_pack, view_root)
    paths.work_pack.mkdir(parents=True, exist_ok=False)
    if attempt.resolve().is_relative_to(paths.repo.resolve()) and attempt.resolve() != paths.repo.resolve():
        checked_file(attempt, ATTEMPT_MARKER).touch(exist_ok=False)
    owners = {}
    for producer, record in adopted.items():
        root = Path(record['root']).absolute()
        if root.is_symlink() or not root.is_dir():
            raise f.FlowError(f'invalid adopted producer root: {root}')
        for relative, digest in record['files'].items():
            key = unicodedata.normalize('NFC', Path(relative).as_posix())
            if key in owners:
                raise f.FlowError(f'duplicate producer for {key}: {producer}, {owners[key]}')
            owners[key] = producer
            dst = paths.work_file(relative)
            # The source root is the accepted producer's pack view, not its RUN.
            src = checked_file(root, relative)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with src.open('rb') as incoming, dst.open('xb') as out:
                shutil.copyfileobj(incoming, out)
            if f._sha(dst) != digest:
                raise f.FlowError(f'adopted output hash mismatch: {relative}')
    return paths


def verify_note_view(manifest_data, paths, audit, *, preliminary=False):
    """Check a composed candidate or the published layout with identical link rules."""
    import manifest
    from check_html import check_pack
    from html2md import check_md
    note = paths.work_file(manifest.note_name(manifest_data))
    errors = list(map(str, check_pack(manifest_data, note, repo=paths.repo, style_audit=f._read(audit),
                                      defer_answer_pdf=preliminary, pack_paths=paths)))
    if not preliminary:
        md = paths.work_file('.assets/' + note.with_suffix('.md').name)
        errors.extend(check_md(note, md, pack_paths=paths))
    if manifest_data['problems']:
        required = [manifest.problem_pdf_name(manifest_data)]
        if not preliminary:
            required.append(manifest.answer_pdf_name(manifest_data))
        errors.extend('missing PDF: ' + name for name in required if not paths.work_file(name).is_file())
    if errors:
        raise f.FlowError('\n'.join(errors))


def publication_verifier(manifest_data, paths, audit, *, answer_review=None):
    """Build the same strict verifier for the staged and actual public roots."""
    import manifest
    from pack_paths import PackPaths

    def verify(root):
        if root == paths.public_pack:
            view = PackPaths(paths.repo, paths.public_pack)
        elif root == paths.work_pack:
            view = paths
        else:
            raise f.FlowError('unexpected publication verification root')
        if manifest_data['range'] != view.public_pack.name:
            raise f.FlowError('publication manifest date mismatch')
        verify_note_view(manifest_data, view, audit)
        if not manifest_data['problems']:
            from pack_files import _roots
            note_name = manifest.note_name(manifest_data)
            allowed = {note_name, '.assets/' + Path(note_name).with_suffix('.md').name,
                       '.assets/figures_' + manifest_data['range']}
            actual = {str(f.nfc_path(name)) for name in _roots(root, manifest_data['range'])}
            extra = actual - allowed
            if extra:
                raise f.FlowError('unexpected zero-problem pack outputs: ' + ', '.join(sorted(extra)))
            return
        if answer_review is None:
            raise f.FlowError('approved answer PDF screen review required')
        bundle = f".assets/자료_문제설명_{manifest_data['range']}_{manifest_data['slug']}"
        # The workbook and note builder each import a distinct assemble.py.
        # Isolate the workbook loader just as the existing answer CLI does.
        script = Path(__file__).with_name('publish_answer.py')
        args = [sys.executable, script, 'verify', '--repo', view.repo, '--public-pack', view.public_pack,
                '--ids', ','.join(p['id'] for p in manifest_data['problems']),
                '--overlay', view.work_file(bundle + '/answer-overlay.json'),
                '--pdf', view.work_file(manifest.answer_pdf_name(manifest_data)),
                '--problem-pdf', view.work_file(manifest.problem_pdf_name(manifest_data)), '--review', answer_review]
        if view.candidate_pack:
            args.extend(['--candidate-pack', view.candidate_pack])
            for private in view.private_roots:
                args.extend(['--private-root', private])
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode:
            raise f.FlowError('current overlay/PDF verification failed: ' + result.stderr)
    return verify


def candidate_action(state, action, paths, attempt, *, audit=None, explain_run=None):
    """Produce only this node's outputs; the scheduler owns adoption and retries."""
    import manifest
    run = Path(state['run'])
    attempt = Path(attempt).absolute()
    if not paths.candidate_pack or not paths.work_pack.resolve().is_relative_to(attempt.resolve()):
        raise f.FlowError('candidate pack must belong to this attempt')
    m = f._read(run/'manifest.json')
    if m['range'] != paths.public_pack.name or m['range'] != state['range']:
        raise f.FlowError('candidate range mismatch')
    note = paths.work_file(manifest.note_name(m))
    if action in ('stage-problem-index', 'assemble-note'):
        import assemble
        if action == 'stage-problem-index':
            return list(assemble.stage_problem_index(paths, m, run/'selection.json', run/'display-titles.json').values())
        return [assemble.assemble(run, paths.work_pack, repo=paths.repo, pack_paths=paths)]
    if action in ('precheck', 'final-check'):
        if audit is None:
            raise f.FlowError('approved learning-style audit required')
        verify_note_view(m, paths, audit, preliminary=action == 'precheck')
        return []
    if action == 'convert-md':
        from html2md import check_md, convert_note
        md = paths.work_file('.assets/' + note.with_suffix('.md').name)
        expected = manifest.answer_pdf_name(m)
        figures = paths.work_file(f".assets/figures_{m['range']}")
        if md.exists() or figures.exists():
            raise f.FlowError('duplicate producer for converted note or figures')
        convert_note(note)
        errors = check_md(note, md, deferred_answer=expected if m['problems'] else None, pack_paths=paths)
        outputs = [md, *sorted(figures.glob('*.svg'))]
        if errors:
            raise f.FlowError('\n'.join(errors))
        return outputs
    if action in ('explain-verify', 'build-problems', 'build-answers'):
        pair = ['--public-pack', paths.public_pack, '--candidate-pack', paths.work_pack]
        if action == 'explain-verify':
            if not explain_run:
                raise f.FlowError('reviewed explanation RUN required')
            script = paths.repo/'.claude/skills/ec2-problem-explain/scripts/epe_cli.py'
            args = [script, 'publish', '--repo', paths.repo, '--run', explain_run, *pair]
        else:
            answers = action == 'build-answers'
            pdf = paths.work_file(manifest.answer_pdf_name(m) if answers else manifest.problem_pdf_name(m))
            if pdf.exists():
                raise f.FlowError(f'duplicate PDF producer: {pdf}')
            args = [paths.repo/'workbook/build_workbook.py', '--ids', ','.join(q['id'] for q in m['problems']),
                    '--name', f"복습문제_{m['range']}_{m['slug']}", '--mode', 'answers' if answers else 'problems',
                    '--selection', paths.work_file('.assets/selection.json'), '--display-titles',
                    paths.work_file('.assets/display-titles.json'), '--layout', 'video-16x9',
                    '--pdf-dir', paths.work_pack, '--build-dir', attempt/'workbook-build', *pair]
            if answers:
                args += ['--answer-overlay', paths.work_file(f".assets/자료_문제설명_{m['range']}_{m['slug']}/answer-overlay.json")]
        proc = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
        (attempt/'producer-stdout.log').write_text(proc.stdout, encoding='utf-8')
        (attempt/'producer-stderr.log').write_text(proc.stderr, encoding='utf-8')
        if proc.returncode:
            raise f.FlowError(f'{action} failed: {proc.stderr}')
        if action == 'explain-verify':
            return [paths.work_file(str(Path(p).relative_to(paths.work_pack))) for p in json.loads(proc.stdout.splitlines()[-1])]
        import pymupdf
        with pymupdf.open(pdf) as doc:
            if not doc.page_count:
                raise f.FlowError('empty candidate PDF')
        return [pdf]
    raise f.FlowError(f'unknown candidate producer: {action}')
