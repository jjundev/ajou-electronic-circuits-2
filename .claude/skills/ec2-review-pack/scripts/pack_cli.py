"""Compact resumable runner CLI. This module never dispatches agents."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
from uuid import uuid4

ACTIONS = ('prepare-pack','assemble-note','build-problems','precheck','convert-md',
           'publish-explanation','build-answers','publish-answer','final-check')

class UsageError(ValueError): pass
class HelpRequested(Exception): pass
class Parser(argparse.ArgumentParser):
    def error(self, message): raise UsageError(message)
    def print_help(self, file=None): raise HelpRequested(self.format_help())


def format_result(result: dict, *, limit: int=2000) -> str:
    """One JSON document, newline included; collapse to durable existing references."""
    def encode(value): return json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
    data=dict(schema_version=1,status='ready',phase=None,next=None,counts={},details_path=None,error_code=None)
    data.update(result); data['schema_version']=1
    text=encode(data)
    if len(text)<=limit: return text
    data['error_code']=data.get('error_code') or 'details_compacted'
    nxt=data.get('next')
    if isinstance(nxt,dict):
        tasks=nxt.get('tasks',[])
        data['next']={k:v for k,v in nxt.items() if k in ('kind','action','attempt','task_id','brief')}
        if tasks:
            data['counts']=dict(data.get('counts') or {},tasks=len(tasks))
            data['next']['tasks_ref']=data.get('details_path')
    data.pop('details',None); data.pop('reason',None)
    text=encode(data)
    if len(text)<=limit: return text
    # Keep the original full detail path whenever it alone fits the envelope.
    base={k:data[k] for k in ('schema_version','status','phase','counts','details_path','error_code')}
    base['next']={'kind':nxt.get('kind')} if isinstance(nxt,dict) else None
    text=encode(base)
    if len(text)<=limit: return text
    base.update(details_path=None,counts={},status='failed' if data['status']=='failed' else 'details_compacted')
    text=encode(base)
    if len(text)>limit: raise ValueError('limit too small for result envelope')
    return text


def parser():
    p=Parser(description='Resumable review-pack runner; all output is compact JSON.')
    sub=p.add_subparsers(dest='command',required=True)
    def command(name, parent=sub):
        c=parent.add_parser(name); c.add_argument('--run',required=True,type=absolute); return c
    c=command('init'); c.add_argument('--repo',required=True,type=absolute); c.add_argument('--range',required=True)
    c.add_argument('--lite',action='store_true')
    for owner in ('browser','pdf'): c.add_argument('--'+owner+'-owner',choices=('workers','main','unavailable'),default='main')
    command('status'); c=command('next'); c.add_argument('--slots',required=True,type=int)
    t=sub.add_parser('task'); ts=t.add_subparsers(dest='task_command',required=True)
    for name in ('claim','bind','accept','release','fix','authorize-fix'):
        c=command(name,ts)
        if name=='authorize-fix': c.add_argument('--authorization',required=True,type=absolute); continue
        if name=='fix': c.add_argument('--request',required=True,type=absolute); continue
        c.add_argument('--task',required=True)
        if name!='claim': c.add_argument('--attempt',required=True)
        if name=='bind': c.add_argument('--agent-id',required=True)
        if name=='accept': c.add_argument('--receipt',required=True,type=absolute)
        if name=='release': c.add_argument('--reason',required=True)
    for name in ('run', 'reconcile'):
        c=command(name); c.add_argument('--action',required=True,choices=ACTIONS)
    command('recover'); command('report')
    return p


def absolute(value):
    p=Path(value)
    if not p.is_absolute(): raise argparse.ArgumentTypeError('absolute path required')
    return p.resolve()


@contextmanager
def quiet_runtime():
    """Capture Python and native fd noise, including import-time warnings."""
    sys.stdout.flush(); sys.stderr.flush()
    with tempfile.TemporaryFile(mode='w+b') as sink:
        saved=[os.dup(fd) for fd in (1,2)]
        try:
            for fd in (1,2): os.dup2(sink.fileno(),fd)
            yield sink
        finally:
            sys.stdout.flush(); sys.stderr.flush()
            for fd,original in zip((1,2),saved): os.dup2(original,fd); os.close(original)


def execute(a):
    import pack_flow as f
    run=a.run
    extra=None
    if a.command=='init':
        f.init_run(a.repo,run,a.range,lite=a.lite,browser_owner=a.browser_owner,pdf_owner=a.pdf_owner)
    elif a.command=='status': pass
    elif a.command=='next': extra=f.next_work(run,slots=a.slots)
    elif a.command=='task':
        if a.task_command=='claim': extra=f.claim_task(run,a.task)
        elif a.task_command=='bind': f.bind_task(run,a.task,a.attempt,a.agent_id)
        elif a.task_command=='accept': f.accept_task(run,a.task,a.attempt,a.receipt)
        elif a.task_command=='release': f.release_task(run,a.task,a.attempt,a.reason)
        elif a.task_command=='authorize-fix': f.authorize_extra_fix(run,a.authorization)
        else: f.request_fixes(run,a.request)
    else:
        import pack_actions as actions
        if a.command in ('run', 'reconcile'):
            operation=actions.run_action if a.command=='run' else actions.reconcile_action
            result=operation(run,a.action)
            if result['status']!='done':
                return dict(status='failed',next=result,details_path=str(Path(result['stdout_path']).parent/'result.json'),error_code=result.get('error_code') or 'execution_failed'),1
        elif a.command=='recover': actions.recover_run(run)
        else:
            path=actions.write_report(run)
            state=f.inspect_state(run)
            return dict(status=state['status'],phase=state['phase'],counts={'partial':int(state['status']!='complete')},details_path=str(path)),0
    state=f.inspect_state(run)
    if extra is None: extra=f.next_work(run,slots=0)
    if isinstance(extra,dict) and 'tasks' in extra:
        extra=dict(extra,tasks=[{k:t[k] for k in ('id','role','brief','status') if k in t} for t in extra['tasks']])
    return dict(status=state['status'],phase=state['phase'],next=extra,
                counts={'tasks':len(state['tasks']),'actions':len(state['actions']),'stale_inputs':len(state['stale_inputs'])},
                details_path=str(run/'run-status.json')),0


def main(argv: list[str] | None=None) -> int:
    a=None; result=None; code=1; trace=''
    with quiet_runtime() as noise:
        try:
            a=parser().parse_args(argv)
            result,code=execute(a)
        except HelpRequested as exc:
            result,code=dict(status='help',details=str(exc)[:1000]),0
        except UsageError:
            result,code=dict(status='failed',error_code='usage_error',reason='Invalid command or arguments; use --help.'),2
        except Exception as exc:
            trace=traceback.format_exc()
            result=dict(status='failed',error_code='validation_failed' if isinstance(exc,(ValueError,OSError)) else 'execution_failed',reason=str(exc)[:240])
        # Read-only queries never create logs, including on failure/noisy imports.
        if a is not None and a.command not in ('status','next') and (a.run/'run-status.json').is_file():
            try:
                noise.flush(); noise.seek(0)
                raw=noise.read()
                if trace or raw:
                    folder=a.run/'work'/'cli'; folder.mkdir(parents=True,exist_ok=True)
                    path=folder/(str(uuid4())+'.log')
                    path.write_bytes(raw+trace.encode('utf-8'))
                    if trace: result['details_path']=str(path)
            except OSError: pass
    sys.stdout.write(format_result(result)); sys.stdout.flush()
    return code


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr,'reconfigure'): sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
