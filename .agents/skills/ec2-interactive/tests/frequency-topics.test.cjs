const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {makeSource}=require('../scripts/make-frequency-example.cjs');
const {check}=require('../scripts/check.cjs');
const {loadComponent,makeCtx,makeCanvas}=require('../scripts/harness.cjs');
function source(kind) {
  const file=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'ec2-topic-')),'Main.dc.html');
  fs.writeFileSync(file,makeSource(kind)); return file;
}
test('both topics satisfy the shell and render at slider endpoints',()=>{
  for(const kind of ['cs','two']) {
    const file=source(kind);
    assert.deepEqual(check(file).errors,[]);
    const {c}=loadComponent(file);
    const {ctx,calls}=makeCtx(); c.attachCanvas(makeCanvas(ctx,375,640));
    for(const control of c.extraVals(c.state).controls) {
      for(const value of [control.min,control.max]) {
        control.change({target:{value:String(value)}});
        c.renderVals(); c.draw(0.016,0);
      }
    }
    assert.ok(calls.some(x=>x.op==='lineTo'));
    assert.ok(!calls.some(x=>x.args.some(v=>typeof v==='number'&&!Number.isFinite(v))));
    assert.ok(c.T.MODES.every(m=>!m.rotatable&&!m.autoSpin));
  }
});
test('invalid slider input retains the last valid state',()=>{
  const {c}=loadComponent(source('cs'));
  const before=JSON.stringify(c.state);
  c.extraVals(c.state).controls[0].change({target:{value:'bad'}});
  assert.equal(JSON.stringify(c.state),before);
});
test('equal-pole preset updates the total cutoff and every panel from one model',()=>{
  const {c}=loadComponent(source('two'));
  c.extraVals(c.state).presets.find(x=>x.key==='equal').pick();
  const v=c.extraVals(c.state);
  assert.ok(Math.abs(v.numeric.fp1-v.numeric.fp2)<1e-5);
  assert.ok(Math.abs(v.numeric.f3db-102431206.69545889)<0.01);
  assert.ok(v.numeric.f3db<v.numeric.fp1);
  assert.ok(Math.abs(v.numeric.gainSigned+10)<1e-10);
});

test('current marker remains visible at every preset frequency endpoint',()=>{
  for(const kind of ['cs','two']) {
    const {c}=loadComponent(source(kind));
    for(const preset of c.extraVals(c.state).presets) {
      preset.pick();
      for(const v of [-2,2]) {
        c.extraVals(c.state).controls.find(x=>x.key==='logRatio').change({target:{value:String(v)}});
        for(const mode of ['bode',...(kind==='two'?['parts']:[])]) {
          const I=[],O=[];c.buildScene(mode,I,O);
          assert.ok(I.some(it=>it.k===0),kind+' '+preset.key+' '+mode+' '+v);
        }
      }
    }
  }
});

test('circuit and panel expose gm and live component values',()=>{
  for(const kind of ['cs','two']) {
    const {c}=loadComponent(source(kind));
    const v=c.extraVals(c.state);
    assert.match(v.assumptions,kind==='cs'?/2 mS/:/5 mS/);
    const I=[],O=[];c.buildScene('bode',I,O);
    assert.ok(I.some(it=>it.k===3&&/R_D=.*Ω/.test(it.text)));
    c.extraVals(c.state).controls.find(x=>x.key==='logRD').change({target:{value:'5'}});
    const J=[];c.buildScene('bode',J,[]);
    assert.notEqual(J.find(it=>it.k===3&&/R_D=/.test(it.text)).text,I.find(it=>it.k===3&&/R_D=/.test(it.text)).text);
  }
});
