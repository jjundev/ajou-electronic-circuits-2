import fs from 'node:fs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const argv=process.argv.slice(2), opt=k=>argv.includes('--'+k)?argv[argv.indexOf('--'+k)+1]:undefined;
const require=createRequire(opt('puppeteer-package'));
const puppeteer=require('puppeteer-core');
const browser=await puppeteer.launch({executablePath:opt('chrome'),headless:true,args:['--no-sandbox','--allow-file-access-from-files']});
try {
 const page=await browser.newPage();
 const mode=opt('mode');
 const file=opt('svg')||opt('entry');
 await page.setViewport({width:1200,height:850,deviceScaleFactor:1});
 if(mode==='inventory') {
   const svg=fs.readFileSync(file,'utf8');
   await page.setContent(svg);
   const result=await page.evaluate(()=>{
     const all=[...document.querySelectorAll('svg use[data-text],svg path,svg rect,svg line,svg circle,svg ellipse,svg polygon,svg image')].filter(n=>!n.closest('defs'));
     return all.map((n,i)=>{
       const b=n.getBBox(),m=n.getCTM();
       const points=[[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].map(([x,y])=>new DOMPoint(x,y).matrixTransform(m));
       return {id:'sv-'+i,index:i,tag:n.tagName,text:n.getAttribute('data-text'),bbox:[Math.min(...points.map(p=>p.x)),Math.min(...points.map(p=>p.y)),Math.max(...points.map(p=>p.x)),Math.max(...points.map(p=>p.y))]};
     });
   });
   console.log(JSON.stringify(result));
 } else if(mode==='gate') {
   const dest=opt('dest'); fs.mkdirSync(dest,{recursive:true});
   const layers=JSON.parse(fs.readFileSync(opt('layers'),'utf8'));
   const original=fs.readFileSync(layers.original_svg,'utf8'), animated=fs.readFileSync(layers.animated_svg,'utf8');
   const [w,h]=await (async()=>{await page.setContent(original);return page.evaluate(()=>{const b=document.querySelector('svg').viewBox.baseVal;return [Math.ceil(b.width*2),Math.ceil(b.height*2)];});})();
   await page.setViewport({width:w,height:h});
   const shot=async(svg,name,action)=>{
     await page.setContent('<style>html,body{margin:0;background:white}svg{width:100vw;height:100vh}</style>'+svg);
     if(action) await page.evaluate(action);
     await page.screenshot({path:dest+'/'+name+'.png'});
   };
   await shot(original,'original');
   await shot(animated,'empty');
   await shot(animated,'removed',()=>document.querySelectorAll('[data-reveal]').forEach(n=>n.remove()));
   await shot(animated,'complete',()=>document.querySelectorAll('[data-reveal]').forEach(n=>n.style.opacity='1'));
   await shot(animated,'partial',()=>{const nodes=[...document.querySelectorAll('[data-reveal]')];nodes.slice(0,Math.floor(nodes.length/2)).forEach(n=>n.style.opacity='1');});
   console.log(JSON.stringify({width:w,height:h,evidence:['original.png','empty.png','removed.png','complete.png','partial.png']}));
 } else if(mode==='timeline') {
   await page.setViewport({width:1920,height:1080});
   await page.goto(pathToFileURL(file).href);
   await page.waitForFunction(()=>typeof window.renderSolutionFrame==='function');
   const end=await page.evaluate(()=>window.solutionTimeline.total_frames-1);
   const sequence=[0,end,Math.floor(end/2),0];
   const shots=[];
   for(const f of sequence){await page.evaluate(f=>window.renderSolutionFrame(f),f);shots.push((await page.screenshot()).toString('base64'));}
   await page.evaluate(f=>window.renderSolutionFrame(f),Math.floor(end/2));
   const direct=(await page.screenshot()).toString('base64');
   const state=await page.evaluate(()=>({cursor:document.getElementById('cursor').style.opacity,box:document.getElementById('pdf-viewport').getBoundingClientRect().toJSON()}));
   await page.evaluate(f=>window.renderSolutionFrame(f),end);
   const last=await page.evaluate(()=>document.getElementById('cursor').style.opacity);
   console.log(JSON.stringify({seek_equal:shots[0]===shots[3]&&shots[2]===direct,final_cursor:last,viewport:state.box}));
 } else throw new Error('unknown mode');
} finally {await browser.close();}
