from pathlib import Path
import hashlib,json,os,subprocess
from .contracts import InputError
S=Path(__file__).resolve().parents[2]
def digest(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_hash(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.pending'); tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8', newline='\n'); os.replace(tmp,p)
def command(args,cwd=None,timeout=120):
    return subprocess.run([str(a) for a in args],cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def checked(args,cwd=None,timeout=120):
    r=command(args,cwd,timeout)
    if r.returncode: raise InputError('command failed: '+str(args[0])+' '+r.stderr[-600:])
    return r

def local(run,path):
    p=(Path(run)/path).resolve()
    if not p.is_relative_to(Path(run).resolve()): raise InputError('path escapes run: '+str(path))
    return p

def node_package(name):
    explicit=os.environ.get('EC2_'+name.upper().replace('-','_')+'_PACKAGE')
    if explicit: return Path(explicit).resolve()
    caches=[Path.home()/'.npm/_npx']
    if os.environ.get('LOCALAPPDATA'): caches.append(Path(os.environ['LOCALAPPDATA'])/'npm-cache/_npx')
    candidates=[p for c in caches for p in c.glob('*/node_modules/'+name+'/package.json')]
    if not candidates: raise InputError('local '+name+' missing; supply EC2_'+name.upper().replace('-','_')+'_PACKAGE')
    return max(candidates,key=lambda p:p.stat().st_mtime)
def browser_config():
    import shutil
    chrome=os.environ.get('EC2_CHROME') or shutil.which('google-chrome') or next((str(p) for p in _chrome_paths() if p.is_file()),None)
    if not chrome or not Path(chrome).is_file(): raise InputError('Chrome missing; supply EC2_CHROME')
    return ['--puppeteer-package',str(node_package('puppeteer-core')),'--chrome',chrome]
def _chrome_paths():
    paths=[Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')]
    for name in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
        if os.environ.get(name): paths.append(Path(os.environ[name])/'Google/Chrome/Application/chrome.exe')
    return paths
def browser(args):
    r=checked(['node',S/'tests/browser_check.mjs',*args,*browser_config()],timeout=120)
    return json.loads(r.stdout)
