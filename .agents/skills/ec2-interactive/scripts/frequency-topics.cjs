const CS = {
  kind:'cs',gm:0.002,title:'CS 이득과 대역폭',
  initial:{logRD:4,logCL:-13,logRatio:0,showApprox:true},
  controls:[
    {key:'logRD',label:'R_D (Ω)',min:2,max:5},
    {key:'logCL',label:'C_L (F)',min:-14,max:-12},
    {key:'logRatio',label:'입력 주파수 / 극점',min:-2,max:2}
  ],
  presets:[
    {key:'base',label:'기본',state:{logRD:4,logCL:-13,logRatio:0}},
    {key:'rd10',label:'R_D 10배',state:{logRD:5,logCL:-13,logRatio:0}},
    {key:'cl10',label:'C_L 10배',state:{logRD:4,logCL:-12,logRatio:0}}
  ],
  mistakes:[
    {title:'큰 이득과 넓은 대역폭',text:'R_D를 키우면 이득은 커지고 극점은 낮아져요. g_m과 C_L가 고정일 때 비교해요.'},
    {title:'CS 반전과 추가 위상',text:'CS 자체의 반전 -180°에 RC 위상이 더해져요. (교과서 보충)'},
    {title:'파형의 높이와 실제 진폭',text:'파형은 각 진폭으로 정규화해요. 실제 입력·출력 진폭은 숫자로 비교해요.'}
  ],
  steps:[
    {mode:'bode',title:'저주파 이득',who:'g_m R_D',text:'커패시터의 영향이 작은 곳에서 전달이득은 -g_m R_D예요. 부호와 크기를 구별해요.'},
    {mode:'bode',title:'극점과 대역폭',who:'R_D C_L',text:'ω_p=1/(R_D C_L)예요. 이 한 극점 모델에서 f_p가 전체 -3 dB 대역폭이에요.'},
    {mode:'bode',title:'저항과 커패시턴스',who:'대표 설정',text:'R_D 10배와 C_L 10배를 차례로 눌러 보세요. 둘 다 극점은 낮아지지만 저주파 이득은 다르게 변해요.'},
    {mode:'wave',f:1,phase:'정현파',title:'출력 파형 읽기',who:'정현파 입력',text:'입력 주파수/극점 비율을 바꾸며 반전·추가 위상과 실제 출력 진폭을 함께 읽어요. (교과서 보충)'}
  ]
};
const TWO = {
  kind:'two',gm:0.005,title:'두 극점과 보데 근사',
  initial:{logRS:3,logCin:-13,logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0,showApprox:true},
  controls:[
    {key:'logRS',label:'R_S (Ω)',min:2,max:4},
    {key:'logCin',label:'C_in (F)',min:-14,max:-12},
    {key:'logRD',label:'R_D (Ω)',min:2,max:5},
    {key:'logCL',label:'C_L (F)',min:-14,max:-12},
    {key:'logRatio',label:'관찰 주파수 / 낮은 극점',min:-2,max:2}
  ],
  presets:[
    {key:'base',label:'기본',state:{logRS:3,logCin:-13,logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0}},
    {key:'input',label:'입력 극점 먼저',state:{logRS:4,logCin:-12,logRD:Math.log10(2000),logCL:-13,logRatio:0}},
    {key:'equal',label:'극점 겹침',state:{logRS:Math.log10(2000),logCin:Math.log10(5e-13),logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0}},
    {key:'rd',label:'R_D 증가',state:{logRS:3,logCin:-13,logRD:4,logCL:Math.log10(5e-13),logRatio:0}}
  ],
  mistakes:[
    {title:'극점과 전체 대역폭',text:'극점이 겹치면 그 주파수에서 전체 -6 dB예요. 전체 -3 dB 대역폭은 더 낮아요.'},
    {title:'rad/s와 Hz',text:'Hz로 바꾸려면 2π로 나눠요. 그래프 축의 단위를 먼저 확인해요.'},
    {title:'정확식과 보데 근사',text:'점선은 직선 근사예요. 극점 근처의 실제 곡률과 오차를 실선에서 확인해요.'}
  ],
  steps:[
    {mode:'bode',title:'입력 노드',who:'R_S C_in',text:'입력 RC가 첫 번째 극점을 만들어요. 입력 값을 바꾸며 해당 표식을 확인해요.'},
    {mode:'bode',title:'출력 노드',who:'R_D C_L',text:'출력 RC가 두 번째 극점을 만들어요. R_D는 저주파 이득도 바꿔요.'},
    {mode:'parts',title:'노드별 손실',who:'dB 합',text:'노드별 dB 손실을 더하면 전체 상대 손실이 돼요. 이 모델에서는 두 RC가 독립이에요.'},
    {mode:'bode',title:'겹친 극점',who:'극점 겹침 설정',text:'극점 겹침을 누르고 극점과 전체 -3 dB 대역폭 숫자를 비교해 보세요.'}
  ]
};
const hooks = {
  topic() {
    const other=CFG.kind==='cs'?'wave':'parts';
    const mode=(key,label)=>({
      key,label,cam:{yaw:0,pitch:0,zoom:1},fit:[16,14],D:60,
      autoSpin:false,rotatable:false,
      playback:key==='wave'?{fmax:4,rate:0.5,label:f=>'정현파 · '+f.toFixed(1)+' / 4'}:null,
      canvasLabel:()=>CFG.title+'의 '+label+' 화면. 회로와 그래프를 함께 비교해요.'
    });
    return {
      MODES:[mode('bode','응답'),mode(other,other==='wave'?'파형':'기여')],
      STEPS:CFG.steps.map(s=>Object.assign({c:'#1677ff'},s)),
      MISTAKES:{bode:CFG.mistakes,[other]:CFG.mistakes},
      TOGGLES:{bode:[['showApprox','보데 근사']]},
      PAL:{
        light:{bg:'#ffffff',labelBg:'#f7f8fa',ink:'#111111',ring:'#111111',a:'#1677ff',b:'#d92d20',link:'#6b7280',blobAlpha:0.3},
        dark:{bg:'#17171c',labelBg:'#212128',ink:'#f2f4f6',ring:'#f2f4f6',a:'#6ea4ff',b:'#ff8a7a',link:'#a3abb8',blobAlpha:0.42}
      }
    };
  },
  buildScene(mode,I,O) { drawFrequencyScene(this,mode,I,O,CFG,FM); },
  extraState() { return Object.assign({},CFG.initial); },
  extraVals(st) {
    const p={gm:CFG.gm,RD:10**st.logRD,CL:10**st.logCL};
    if(CFG.kind==='two') Object.assign(p,{RS:10**st.logRS,Cin:10**st.logCin});
    const base=FM[CFG.kind](p,0);
    const omega=Math.min(base.wp1,base.wp2||base.wp1)*10**st.logRatio;
    const r=FM[CFG.kind](p,omega);
    const fmt=(x,u)=>x.toPrecision(4)+' '+u;
    const controls=CFG.controls.map(def=>Object.assign({},def,{
      value:String(st[def.key]),
      display:def.key==='logRatio'?fmt(10**st[def.key],'배'):fmt(10**st[def.key],def.label.includes('(F)')?'F':'Ω'),
      change:e=>{
        const v=Number(e.target.value);
        if(!Number.isFinite(v)) return;
        this.setState({[def.key]:Math.max(def.min,Math.min(def.max,v)),step:-1});
      }
    }));
    return {
      controls,
      presets:CFG.presets.map(preset=>({key:preset.key,label:preset.label,
        pick:()=>this.setState(Object.assign({},preset.state,{playing:false,step:-1}))})),
      numeric:{gainSigned:-r.A0,fp1:r.fp1,fp2:r.fp2,f3db:r.f3db,omega,mag:r.mag,phaseDeg:r.phaseDeg},
      tiles:[
        {label:'저주파 전달이득',value:fmt(-r.A0,'V/V')},
        {label:'전체 -3 dB 대역폭',value:fmt(r.f3db,'Hz')},
        {label:'현재 주파수',value:fmt(omega/(2*Math.PI),'Hz')},
        {label:'현재 크기',value:fmt(r.mag,'V/V')}
      ],
      poles:'ω_p1='+fmt(r.wp1,'rad/s')+(r.wp2?' · ω_p2='+fmt(r.wp2,'rad/s'):''),
      waveInfo:'위상 '+r.phaseDeg.toFixed(1)+'° · 입력 0.1000 mV · 출력 '+(r.mag*0.1).toFixed(4)+' mV (교과서 보충)',
      assumptions:CFG.kind==='cs'?'소신호 선형 모델 · r_o=∞ · g_m=2 mS 고정 · 클리핑 미포함':
        '입력·출력 RC 독립 · r_o=∞ · C_gd·몸체 효과 제외 · g_m=5 mS 고정',
      curveLegend:st.mode==='wave'?'파랑은 입력, 빨강은 출력이에요. 실제 진폭은 위 숫자로 비교해요.':
        st.mode==='parts'?'파랑은 입력 손실, 빨강은 출력 손실, 회색은 두 손실의 합이에요.':
        '파랑 실선은 정확한 크기, 회색 점선은 보데 근사예요.',
      legend:{a:this.pal().a,b:this.pal().b}
    };
  }
};
const left = '<div class="sec"><h2 class="sec-title">값 바꾸기</h2>'+
  '<sc-for list="{{controls}}" as="ctl"><div class="sub"><label style="display:block;min-height:2.8em" for="ec2-{{ctl.key}}">{{ctl.label}} · {{ctl.display}}</label>'+
  '<input style="display:block;width:100%;margin:8px 0 16px" id="ec2-{{ctl.key}}" type="range" min="{{ctl.min}}" max="{{ctl.max}}" step="any" value="{{ctl.value}}" onChange="{{ctl.change}}"></div></sc-for></div>'+
  '<div class="sec"><h2 class="sec-title">대표 설정</h2><sc-for list="{{presets}}" as="pre">'+
  '<button class="btn" type="button" onClick="{{pre.pick}}">{{pre.label}}</button></sc-for></div>';
const right='<div class="sec"><div class="tiles"><sc-for list="{{tiles}}" as="tile">'+
  '<div class="tile"><b>{{tile.value}}</b><span>{{tile.label}}</span></div></sc-for></div>'+
  '<p class="sub">{{poles}}</p><p class="sub">{{assumptions}}</p>'+
  '<sc-if value="{{is.wave}}"><div><p class="sub">{{waveInfo}}</p><p class="sub">t/T와 각 V/V_peak로 정규화한 파형이에요.</p></div></sc-if>'+
  '<p class="sub">{{curveLegend}}</p></div>';
function createTopic(kind) {
  const config=kind==='cs'?CS:kind==='two'?TWO:null;
  if(!config) throw new RangeError('kind must be cs or two');
  const markupRight=kind==='cs'?right:right.replace(/<sc-if value="\{\{is\.wave\}\}">[\s\S]*?<\/sc-if>/,'');
  return {title:config.title,config,left,right:markupRight,hooks,drawScene:drawFrequencyScene};
}
module.exports={createTopic};
function drawFrequencyScene(c,mode,I,O,cfg,M) {
  const st=c.state,pal=c.pal();
  const p={gm:cfg.gm,RD:10**st.logRD,CL:10**st.logCL};
  if(cfg.kind==='two') Object.assign(p,{RS:10**st.logRS,Cin:10**st.logCin});
  const base=M[cfg.kind](p,0), low=Math.min(base.wp1,base.wp2||base.wp1);
  const high=Math.max(base.wp1,base.wp2||base.wp1), w=low*10**st.logRatio;
  const r=M[cfg.kind](p,w);
  const line=(a,b,color=pal.link,width=0.035)=>I.push({k:1,p:[a[0],a[1],0],q:[b[0],b[1],0],w:width,c:color,flat:true});
  const text=(x,y,value,color=pal.ink)=>I.push({k:3,p:[x,y,0],text:value,size:13,c:color});
  const ground=(x,y)=>{line([x,y],[x,y-0.15]);for(let n=0;n<3;n++)line([x-0.3+n*0.07,y-0.15-n*0.1],[x+0.3-n*0.07,y-0.15-n*0.1]);};
  const resistor=(x,y)=>{line([x,y],[x,y-0.35]);let a=[x,y-0.35];for(let n=0;n<6;n++){const b=[x+(n%2?0.18:-0.18),y-0.5-n*0.15];line(a,b);a=b;}line(a,[x,y-1.55]);};
  const capacitor=(x,y)=>{line([x,y],[x,y-0.7]);line([x-0.35,y-0.7],[x+0.35,y-0.7]);line([x-0.35,y-0.9],[x+0.35,y-0.9]);line([x,y-0.9],[x,y-1.55]);};
  // Output R_D, C_L and downward gm*v_in/v_X controlled current source are parallel.
  line([2,4.8],[6,4.8]);line([2,2.5],[6,2.5]);
  resistor(4,4.8);line([4,3.25],[4,2.5]);
  capacitor(6,4.8);line([6,3.25],[6,2.5]);
  line([2,4.8],[2,4.2]);line([2,3.2],[2,2.5]);
  const diamond=[[2,4.2],[2.5,3.7],[2,3.2],[1.5,3.7],[2,4.2]];
  for(let n=1;n<diamond.length;n++)line(diamond[n-1],diamond[n]);
  line([2,4],[2,3.4],pal.b);I.push({k:4,p:[2,4,0],q:[2,3.4,0],c:pal.b});
  ground(4,2.5);text(4.2,5.5,'v_out');text(4.8,4,'R_D');text(6.6,3.1,'C_L');
  text(0.7,3,'g_m '+(cfg.kind==='two'?'v_X':'v_in'),pal.b);
  if(cfg.kind==='two') {
    line([-6,4.8],[-5.4,4.8]);
    let a=[-5.4,4.8];for(let n=0;n<6;n++){const b=[-5.2+n*0.22,4.8+(n%2?0.18:-0.18)];line(a,b);a=b;}
    line(a,[-2.5,4.8]);capacitor(-2.5,4.8);ground(-2.5,3.25);
    text(-5,5.5,'R_S');text(-1.2,3.1,'C_in');text(-2.5,5.5,'v_X');
  } else {line([-6,4.8],[-2.5,4.8]);text(-3.8,5.5,'v_in');}
  line([-6,3.3],[-4.5,3.3]);ground(-4.5,3.3);
  text(-6.1,4.4,'+');text(-6.1,3.3,'−');
  if(cfg.kind==='two') text(-6.2,5.5,'v_in');
  text(0,6.2,'AC 접지 기준 소신호 등가회로');
  const eng=(v,unit)=>{
    const powers=unit==='F'?[-15,-12,-9]:[0,3,6];
    const prefixes=unit==='F'?['f','p','n']:['','k','M'];
    let n=0;for(let i=0;i<powers.length;i++)if(v>=10**powers[i]*0.999999)n=i;
    return (v/10**powers[n]).toPrecision(3)+prefixes[n]+unit;
  };
  text(0,1.65,'R_D='+eng(p.RD,'Ω')+' · C_L='+eng(p.CL,'F'));
  if(cfg.kind==='two') text(0,7.05,'R_S='+eng(p.RS,'Ω')+' · C_in='+eng(p.Cin,'F'));
  const x0=-6,x1=6,y0=-5.2,y1=0.8;
  line([x0,y0],[x1,y0]);line([x0,y0],[x0,y1]);
  if(mode==='wave') {
    text(0,1,'정규화 파형');text(0,-6.55,'t/T');text(-6.1,0.2,'V/V_peak');
    for(let n=0;n<=4;n++) text(x0+(x1-x0)*n/4,-5.7,String(n));
    for(const v of [-1,0,1]) text(-6.4,-2.2+2*v,String(v));
    let lastIn=null,lastOut=null;
    for(let n=0;n<=240;n++){
      const t=n/60, wave=M.wave(r,t);
      const a=[x0+(x1-x0)*n/240,-2.2+2*wave.vin/wave.inputPeak];
      const b=[a[0],-2.2+2*wave.vout/wave.outputPeak];
      if(lastIn)line(lastIn,a,pal.a);if(lastOut)line(lastOut,b,pal.b);
      lastIn=a;lastOut=b;
    }
    const now=x0+(x1-x0)*c.sim.f/4;line([now,y0],[now,y1],pal.link);
    text(-2,0.5,'입력',pal.a);text(2,0.5,'출력',pal.b);
    return;
  }
  const lf0=Math.log10(low)-2,lf1=Math.log10(high)+2;
  const end=M[cfg.kind](p,high*100);
  const endDb=mode==='parts'?end.inputLossDb+end.outputLossDb:end.db;
  const maxDb=mode==='parts'?5:20*Math.log10(base.A0)+5;
  const minDb=Math.floor(endDb/10)*10-5;
  const xOf=q=>x0+(Math.log10(q)-lf0)/(lf1-lf0)*(x1-x0);
  const yOf=db=>y0+(db-minDb)/(maxDb-minDb)*(y1-y0);
  for(let n=0;n<=4;n++){const lf=lf0+(lf1-lf0)*n/4,x=xOf(10**lf);line([x,y0],[x,y1],pal.link,0.015);text(x,-5.7,'10^'+lf.toFixed(1));}
  for(let n=0;n<=4;n++){const db=minDb+(maxDb-minDb)*n/4; text(-6.5,yOf(db),db.toFixed(0));}
  text(0,-6.3,'ω (rad/s, 로그 축)');text(-6.2,1.3,mode==='parts'?'손실 dB':'|H| dB');
  const curve=(key,color,dashed=false)=>{
    let last=null;
    for(let n=0;n<=240;n++){
      const q=10**(lf0+(lf1-lf0)*n/240),value=M[cfg.kind](p,q);
      const db=key==='sum'?value.inputLossDb+value.outputLossDb:value[key];
      if(db<minDb||db>maxDb){last=null;continue;}
      const point=[xOf(q),yOf(db)];
      if(last&&(!dashed||n%4<2))line(last,point,color);
      last=point;
    }
  };
  if(mode==='parts'){curve('inputLossDb',pal.a);curve('outputLossDb',pal.b);curve('sum',pal.link);}
  else {curve('db',pal.a);if(st.showApprox)curve('bodeDb',pal.link,true);}
  const close=base.wp2&&Math.abs(xOf(base.wp1)-xOf(base.wp2))<1.8;
  [base.wp1,base.wp2].filter(Boolean).forEach((q,n)=>{
    line([xOf(q),y0],[xOf(q),y1],n?pal.b:pal.a,0.025);
    if(!close) text(xOf(q),y1+0.22,'ω_p'+(n+1),n?pal.b:pal.a);
  });
  if(close) text((xOf(base.wp1)+xOf(base.wp2))/2,y1+0.22,
    Math.abs(Math.log10(base.wp1/base.wp2))<1e-9?'ω_p1 = ω_p2':'ω_p1 · ω_p2',pal.ink);
  const currentDb=mode==='parts'?r.inputLossDb+r.outputLossDb:r.db;
  const markerY=yOf(currentDb);
  if(markerY>=y0&&markerY<=y1)I.push({k:0,p:[xOf(w),markerY,0],r:0.1,c:pal.a,flat:true});
}
