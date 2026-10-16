const assert=require('assert');const {loadComponent}=require('/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.agents/skills/ec2-interactive/scripts/harness.cjs');const {c}=loadComponent(__dirname+'/nodes/Main.dc.html');
c.setState({ideal:true,mode:'bode',kill:true});let I=[],O=[];c.buildScene('bode',I,O);assert(I.some(z=>z.k===3&&z.text==='C_in'),'Cin retained');
const input=I.filter(z=>z.k===1&&z.p[0]>=-5.41&&z.q[0]<=-2.49&&z.p[0]<=-2.49&&z.q[0]>=-5.41&&Math.abs(z.p[1]-4.8)<.21&&Math.abs(z.q[1]-4.8)<.21);
assert(input.every(z=>Math.abs(z.p[1]-4.8)<1e-9&&Math.abs(z.q[1]-4.8)<1e-9),'ideal RS input wire must be horizontal, no residual diagonal zigzag lead');assert(input.some(z=>z.p[0]<=-5.39&&z.q[0]>=-2.51),'wire connects both former RS terminals through to Cin');assert(c.extraVals(c.state).sourceInfo.includes('입력원이 동작'),'Bode sourceInfo active despite node kill flag');
console.log('independent ideal scene checks pass');
