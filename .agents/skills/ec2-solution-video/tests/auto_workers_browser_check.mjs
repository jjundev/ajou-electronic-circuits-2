/* Compare window-adapted GSAP seeking with the untouched original PDF player.
 * Software raster avoids Metal's observed 1-LSB color rounding between tabs.
 * Production render acceptance separately verifies browser GPU auto/Metal. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const args=process.argv.slice(2), opt=k=>args[args.indexOf('--'+k)+1];
for(const file of [path.join(opt('fixture'),'composition/index.html'),...['static','dynamic'].map(name=>path.join(opt('run'),'composition',name,'index.html'))]){
 if(!fs.existsSync(file))throw Error('missing browser-check input: '+file);
}
const require=createRequire(opt('puppeteer-package'));
const browserArgs=['--no-sandbox','--allow-file-access-from-files','--disable-gpu'];
const browser=await require('puppeteer-core').launch({executablePath:opt('chrome'),headless:true,args:browserArgs});
const dest=opt('destination');fs.mkdirSync(dest,{recursive:true});
const digest=data=>crypto.createHash('sha256').update(data).digest('hex');
try{
 const original=await browser.newPage(),windowed=await browser.newPage();
 for(const page of [original,windowed])await page.setViewport({width:1920,height:1080,deviceScaleFactor:1});
 const load=async(page,file)=>{
  process.stderr.write('Loading '+file+'\n');
  await page.bringToFront();
  await page.goto(pathToFileURL(file).href);
  await page.waitForFunction(()=>Boolean(window.__timelines?.solution),{polling:50,timeout:10000});
  await page.evaluate(async()=>{await document.fonts.ready;for(const image of document.images)await image.decode();const render=window.renderSolutionFrame;window.renderSolutionFrame=f=>{window.__checkedFrame=f;render(f);};});
 };
 await load(original,path.join(opt('fixture'),'composition/index.html'));
 const results=[];
 for(const [name,first] of [['static',0],['dynamic',6269]]){
  await load(windowed,path.join(opt('run'),'composition',name,'index.html'));
  const screenshot=async(page,seconds)=>{
   await page.bringToFront();
   await page.evaluate(at=>{window.__timelines.solution.seek(at,false);},seconds);
   return Buffer.from(await page.screenshot());
  };
  process.stderr.write('Comparing '+name+'\n');
  for(const frame of [0,450,150,899,0]){
   const reference=await screenshot(original,(first+frame)/30);
   const actual=await screenshot(windowed,frame/30);
   const state=await windowed.evaluate(()=>({frame:window.__checkedFrame,viewbox:document.querySelector('#answer-page>svg').getAttribute('viewBox')}));
   const originalState=await original.evaluate(()=>({frame:window.__checkedFrame,viewbox:document.querySelector('#answer-page>svg').getAttribute('viewBox')}));
   if(Math.abs(state.frame-(first+frame))>1e-4||Math.abs(originalState.frame-(first+frame))>1e-4||state.viewbox!==originalState.viewbox)throw Error(`${name} frame or camera mismatch at ${frame}`);
   fs.writeFileSync(path.join(dest,`${name}-${frame}-reference.png`),reference);
   const equal=reference.equals(actual);fs.writeFileSync(path.join(dest,`${name}-${frame}.png`),actual);
   results.push({name,frame,state,originalState,original_frame:first+frame,equal,reference_sha256:digest(reference),actual_sha256:digest(actual)});
   fs.writeFileSync(path.join(dest,'progress.json'),JSON.stringify(results,null,2));
   if(!equal)throw Error(`${name} seek at ${frame} differs from frozen original`);
  }
 }
 fs.writeFileSync(path.join(dest,'browser.json'),JSON.stringify({status:'passed',backend:'software',chrome:opt('chrome'),browserArgs,comparisons:results.length,results},null,2));
 process.stdout.write(JSON.stringify({status:'passed',comparisons:results.length}));
}finally{await browser.close();}
