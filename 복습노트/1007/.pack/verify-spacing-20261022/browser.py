from pathlib import Path
import functools,http.server,threading,json,hashlib
from playwright.sync_api import sync_playwright
run=Path(__file__).parent;b=next(run.glob('review-*'));s=json.loads((b/'stage.json').read_text(encoding='utf8'));stage=b/s['stage'];html=stage/s['html']
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/favicon.ico':self.send_response(204);self.end_headers();return
  super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(stage)));threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='chrome')
 for width in [1280,1024,375]:
  for theme in ['light','dark']:
   page=browser.new_page(viewport={'width':width,'height':900},color_scheme=theme);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{server.server_port}/'+html.name);page.evaluate('()=>document.fonts.ready');page.wait_for_timeout(1100)
   checks=[]
   for i in range(1,15):
    page.evaluate('(id)=>location.hash="#"+id','p'+str(i));page.wait_for_timeout(65);page.evaluate('()=>document.getAnimations().forEach(a=>a.finish())')
    data=page.evaluate('''() => {
     const gap=(a,b)=>b.getBoundingClientRect().top-a.getBoundingClientRect().bottom;
     const t=document.getElementById(location.hash.slice(1)),result=[];
     for(const section of ['solve','verify']) {
      const layer=t.querySelector('[data-explanation="'+section+'"]'),ps=[...layer.querySelectorAll(':scope > [data-subpart]')];
      result.push({section,first:gap(ps[0].previousElementSibling,ps[0]),siblings:ps.slice(1).map((p,i)=>gap(ps[i],p))});
     }
     return {id:t.id,parts:result,mathErrors:t.querySelectorAll('.katex-error').length,broken:[...t.querySelectorAll('img')].filter(n=>!n.complete||!n.naturalWidth).map(n=>n.src)};
    }''')
    assert not data['mathErrors'] and not data['broken'],data
    for v in data['parts']:
     assert abs(v['first']-24)<.2,(width,data)
     assert all(abs(x-(32 if width>=1024 else 24))<.2 for x in v['siblings']),(width,data)
    checks.append(data)
   page.evaluate('()=>location.hash="#p13"');page.wait_for_timeout(150)
   for selector in ['#toggle-left','#toggle-prob','#toggle-right']:
    button=page.locator(selector)
    if button.get_attribute('aria-expanded')=='true':button.click()
   page.wait_for_timeout(100)
   page.locator('#p13 [data-explanation="verify"]').evaluate('n=>{const s=document.querySelector(".content");s.scrollTop+=n.getBoundingClientRect().top-90}')
   page.screenshot(path=str(run/f'verify-{width}-{theme}.png'))
   assert not errors,errors
   rows.append({'width':width,'theme':theme,'topics':checks});page.close()
 browser.close()
server.shutdown();server.server_close()
result={'status':'pass','html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),'rows':rows}
(run/'browser.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS:84 actual topic views; solve/verify first24, siblings32desktop/24mobile; no math errors or broken images')

