const fs=require('fs'),crypto=require('crypto'),assert=require('assert');
const root='/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2',run=__dirname;
const {loadComponent}=require(root+'/.agents/skills/ec2-interactive/scripts/harness.cjs');
const file=run+'/nodes/Main.dc.html';
const near=(a,b,msg)=>assert(Math.abs(a-b)<1e-8*Math.max(1,Math.abs(b)),msg+': '+a+' vs '+b);
// Independent complex division of -gm RD by (1+jw tauin)(1+jw tauout).
// Deliberately does not import or call FM for expected values.
function expected(st,omega){
 const ti=st.ideal?0:10**st.logRS*10**st.logCin,to=2000*10**st.logCL;
 const re=1-omega*omega*ti*to,im=omega*(ti+to),den=re*re+im*im;
 const hr=-10*re/den,hi=10*im/den,mag=Math.hypot(hr,hi);
 const poles=ti?[1/ti,1/to]:[1/to];
 let lo=0,high=Math.min(...poles)*2;
 for(let n=0;n<120;n++){const mid=(lo+high)/2;const gain=1/Math.hypot(1,mid*ti)/Math.hypot(1,mid*to);if(gain>Math.SQRT1_2)lo=mid;else high=mid;}
 const phase=-180-(Math.atan2(omega*ti,1)+Math.atan2(omega*to,1))*180/Math.PI;
 const bode=20-poles.reduce((a,q)=>a+20*Math.max(0,Math.log10(omega/q)),0);
 return {ti,to,mag,db:20*Math.log10(mag),phase,bode,f3db:(lo+high)/2/(2*Math.PI),poles,slope:-20*poles.filter(q=>omega>=q*(1-1e-12)).length};
}
let checks=0,rows=[];function verify(c,label){const v=c.extraVals(c.state),s=c.state,n=v.numeric,e=expected(s,n.omega);for(const [k,k2] of [['mag','mag'],['db','db'],['phaseDeg','phase'],['bodeDb','bode'],['f3db','f3db'],['inputTau','ti'],['outputTau','to'],['slope','slope']]){near(n[k],e[k2],label+' '+k);checks++;}near(n.fp1,e.poles[0]/(2*Math.PI),'fp1');if(e.poles[1])near(n.fp2,e.poles[1]/(2*Math.PI),'fp2');checks++;rows.push({label,omega:n.omega,mag:n.mag,db:n.db,f3db:n.f3db,slope:n.slope});}
let {c}=loadComponent(file);verify(c,'default');
for(let i=0;i<4;i++){({c}=loadComponent(file));c.extraVals(c.state).settings[i].pick();verify(c,'preset '+i);}
for(const ideal of [false,true])for(const logRS of [2,4])for(const logCin of [-14,-12])for(const logCL of [-14,-12])for(const logRatio of [-2,-1,0,1,2]){c.setState({ideal,logRS,logCin,logCL,logRatio});verify(c,'endpoint '+JSON.stringify({ideal,logRS,logCin,logCL,logRatio}));}
({c}=loadComponent(file));c.extraVals(c.state).settings[2].pick();let n=c.extraVals(c.state).numeric;near(n.db-20,-6.020599913279624,'overlap -6.0206 dB');near(n.f3db/(n.wp1/(2*Math.PI)),Math.sqrt(Math.sqrt(2)-1),'overlap bandwidth');checks+=2;
c.extraVals(c.state).settings[1].pick();c.setState({logRatio:0});n=c.extraVals(c.state).numeric;near(n.db-20,-3.010299956639812,'ideal single pole -3.0103');checks++;
for(const mode of ['nodes','bode'])for(const kill of [false,true])for(const selected of ['x','wire','y','source','ground']){c.setState({mode,kill,selected});verify(c,'state '+mode+kill+selected);const I=[],O=[];c.buildScene(mode,I,O);assert(I.length>10);checks++;}
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const sources=[file,run+'/nodes/brief.md',root+'/STT/1014 전회2.md',root+'/복습노트/1014/.assets/정리노트_1014_Frequency_Response.md',run+'/slide9.png',root+'/.agents/skills/ec2-interactive/references/circuit-verification.md'];
fs.writeFileSync(run+'/numeric-independent.json',JSON.stringify({status:'pass',checks,states:rows.length,method:'Explicit complex division; bisection half-power bandwidth; direct pole asymptote sum; no FM used for expected values',examples:rows.slice(0,5),source_sha256:Object.fromEntries(sources.map(f=>[f,hash(f)]))},null,2));
console.log(JSON.stringify({status:'pass',checks,states:rows.length,examples:rows.slice(0,5)},null,2));
