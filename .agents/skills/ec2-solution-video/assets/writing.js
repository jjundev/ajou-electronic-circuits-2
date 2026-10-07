/* The integer frame is the only source of state. SVG outlines and defs stay intact. */
(function(root){
 const clamp=n=>Math.max(0,Math.min(1,n));
 function frameState(t,g,frame){
  const span=(t.writing_spans||[]).find(s=>s.start_frame<=frame&&frame<s.end_frame)||null;
  return {span,progress:span?(span.end_frame-span.start_frame===1?1:clamp((frame-span.start_frame)/(span.end_frame-span.start_frame-1))):0};
 }
 function cameraAt(t,frame){let k=t.cameras[0];for(const v of t.cameras){if(v.at_frame<=frame)k=v;else break;}return k.viewbox;}
 function mirrored(t,f){let k=t.cameras[0];for(const v of t.cameras){if(v.at_frame<=f)k=v;else break;}return !!k.mirror;}
 function screen(pt,c,l){const s=Math.min(1920/c[2],l.height/c[3]);return [(1920-c[2]*s)/2+(pt[0]-c[0])*s,(l.height-c[3]*s)/2+(pt[1]-c[1])*s];}
 function createRenderer(svg,glyphs,pencil,meta){
  const ns='http://www.w3.org/2000/svg',groups=new Map(),defs=document.createElementNS(ns,'defs');svg.append(defs);
  for(const g of Object.values(glyphs)){
   const entries=[];
   for(const id of g.svg_ids){
    const node=svg.querySelector('[id="'+id+'"]');if(!node)throw Error('missing pencil glyph '+id);
    const parent=node.parentNode,wrapper=document.createElementNS(ns,'g'),clip=document.createElementNS(ns,'clipPath'),rect=document.createElementNS(ns,'rect');
    clip.id='writing-'+id;clip.setAttribute('clipPathUnits','userSpaceOnUse');clip.append(rect);defs.append(clip);
    // Capture page→parent before wrapping; this matrix is independent of the camera.
    const matrix=parent.getScreenCTM().inverse().multiply(svg.getScreenCTM());
    rect.setAttribute('transform',`matrix(${matrix.a} ${matrix.b} ${matrix.c} ${matrix.d} ${matrix.e} ${matrix.f})`);
    parent.insertBefore(wrapper,node);wrapper.append(node);entries.push({node,wrapper,rect,clip});
   }
   groups.set(g.id,entries);
  }
  let state={visible:false,masked_ids:[]};
  function render(t,frame,camera,layout){
   const {span,progress}=frameState(t,glyphs,frame),done=new Set(t.events.filter(e=>e.kind==='glyph'&&e.frame<=frame).map(e=>e.id));
   const active=span?.kind==='draw'?span.id:null,masked=[];
   groups.forEach((entries,id)=>{
    const b=glyphs[id].bbox,current=id===active;
    for(const e of entries){
     e.node.style.opacity=done.has(id)||current?'1':'0';
     if(current){
      const edge=b[0]+(b[2]-b[0])*progress;
      e.rect.setAttribute('x',b[0]-1);e.rect.setAttribute('y',b[1]-1);e.rect.setAttribute('height',b[3]-b[1]+2);
      e.rect.setAttribute('width',Math.max(0,edge-b[0]+1+(progress===1?1:0)));
      e.wrapper.setAttribute('clip-path','url(#'+e.clip.id+')');
     }else e.wrapper.removeAttribute('clip-path');
    }
    if(current)masked.push(id);
   });
   const g=span&&glyphs[span.id];
   let mirror=mirrored(t,frame);
   let show=!!g&&!g.text.match(/^\s*$/),tip=null,angle=0,bounds=null,length=t.writing.pencil_length_px;
   if(show){
    const b=g.bbox,dest=screen([b[0]+(span.kind==='draw'?(b[2]-b[0])*progress:0),b[1]+.8*(b[3]-b[1])],camera,layout);
    tip=dest;
    if(span.kind==='move'&&span.from_id){
     const a=glyphs[span.from_id].bbox;
     const previous=screen([a[2],a[1]+.8*(a[3]-a[1])],cameraAt(t,span.start_frame-1),layout);
     tip=[previous[0]+(dest[0]-previous[0])*progress,previous[1]+(dest[1]-previous[1])*progress-(span.lifted?8*Math.sin(Math.PI*progress):0)];
    }
    angle=span.kind==='draw'?t.writing.tilt_degrees*Math.sin(2*Math.PI*progress):0;
    const scale=length/Math.hypot(meta.end_px[0]-meta.tip_px[0],meta.end_px[1]-meta.tip_px[1]);
    pencil.style.width=meta.width+'px';pencil.style.height=meta.height+'px';pencil.style.transformOrigin=meta.tip_px[0]+'px '+meta.tip_px[1]+'px';
    pencil.style.transform=`translate(${tip[0]-meta.tip_px[0]}px,${tip[1]-meta.tip_px[1]}px) rotate(${angle}deg) scale(${mirror?-scale:scale},${scale})`;
    const rad=angle*Math.PI/180,[x0,y0,x1,y1]=meta.visible_bounds_px;
    const cornersFor=flip=>[[x0,y0],[x1,y0],[x1,y1],[x0,y1]].map(([x,y])=>{x=(x-meta.tip_px[0])*scale*(flip?-1:1);y=(y-meta.tip_px[1])*scale;return [tip[0]+x*Math.cos(rad)-y*Math.sin(rad),tip[1]+x*Math.sin(rad)+y*Math.cos(rad)];});
    let corners=cornersFor(mirror);
    const fits=cs=>cs.every(p=>p[0]>=0&&p[0]<=1920&&p[1]>=0&&p[1]<=900);
    if(!fits(corners)&&fits(cornersFor(!mirror))){mirror=!mirror;corners=cornersFor(mirror);pencil.style.transform=`translate(${tip[0]-meta.tip_px[0]}px,${tip[1]-meta.tip_px[1]}px) rotate(${angle}deg) scale(${mirror?-scale:scale},${scale})`;}
    bounds=[Math.min(...corners.map(p=>p[0])),Math.min(...corners.map(p=>p[1])),Math.max(...corners.map(p=>p[0])),Math.max(...corners.map(p=>p[1]))];
   }
   pencil.style.opacity=show?'1':'0';
   state={active_id:span?.id||null,kind:span?.kind||null,progress,visible:show,tip_screen:tip,pencil_length_px:length,pencil_bounds:bounds,tilt_degrees:angle,mirror,masked_ids:masked};
  }
  return {render,snapshot:()=>state};
 }
 const api={frameState,createRenderer};if(typeof module!=='undefined')module.exports=api;root.EC2Writing=api;
})(typeof window==='undefined'?globalThis:window);
