const test = require('node:test');
const assert = require('node:assert/strict');
const {createFrequencyModel} = require('../scripts/frequency-model.cjs');
const M = createFrequencyModel();
const near = (actual,expected,eps=1e-10) =>
  assert.ok(Math.abs(actual-expected) <= eps*Math.max(1,Math.abs(expected)),
    actual + ' != ' + expected);
const p = {gm:0.002,RD:10000,CL:1e-13};
test('single-pole cutoff, inversion phase and gain-bandwidth product', () => {
  const r = M.cs(p,1e9);
  near(r.A0,20); near(r.wp1,1e9); near(r.fp1,159154943.09189534);
  near(r.mag,14.14213562373095); near(r.phaseDeg,-225);
  near(r.db,23.010299956639813);
  const biggerR = M.cs({...p,RD:100000},0);
  near(biggerR.A0,200); near(biggerR.fp1,r.fp1/10);
  near(biggerR.A0*biggerR.fp1,r.A0*r.fp1);
});
test('coincident poles have minus-six dB at the pole and a lower cutoff', () => {
  const same = {gm:0.005,RS:2000,Cin:5e-13,RD:2000,CL:5e-13};
  const r = M.two(same,1e9);
  near(r.A0,10); near(r.mag,5);
  near(r.db,13.979400086720375);
  near(r.phaseDeg,-270);
  near(r.f3db,102431206.69545889);
  near(M.two(same,2*Math.PI*r.f3db).mag,r.A0/Math.SQRT2);
});
test('wave output preserves the signed CS response at the cutoff', () => {
  const r = M.cs(p,1e9);
  near(M.wave(r,0).vout,0.001);
  near(M.wave(r,0.25).vout,-0.001);
});
test('positive component limits produce finite results; invalid units fail', () => {
  for (const RD of [100,100000]) for (const CL of [1e-14,1e-12]) {
    const r = M.cs({...p,RD,CL},1e9);
    for (const key of ['A0','wp1','fp1','f3db','mag','db','phaseDeg'])
      assert.ok(Number.isFinite(r[key]),key);
  }
  for (const value of [0,-1,NaN,Infinity])
    assert.throws(() => M.cs({...p,RD:value},1e9),RangeError);
  assert.throws(() => M.cs(p,-1),RangeError);
});
