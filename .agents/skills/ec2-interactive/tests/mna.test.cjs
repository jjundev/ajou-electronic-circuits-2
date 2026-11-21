const test = require('node:test');
const assert = require('node:assert/strict');
const { solveCircuit } = require('../assets/mna.js');

const approx = (a, b, tol = 1e-4) => assert.ok(Math.abs(a - b) <= tol, `${a} != ${b}`);

test('resistive divider and branch current sign (n1 -> n2)', () => {
  const r = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 4 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'mid', value: 3000 },
      { id: 'r2', type: 'R', n1: 'mid', n2: '0', value: 1000 },
    ],
  });
  assert.equal(r.ok, true);
  assert.equal(r.singular, false);
  approx(r.nodes.mid.re, 1.0);
  approx(r.branches.r1.re, 1e-3, 1e-7);
  approx(r.branches.r2.re, 1e-3, 1e-7);
  approx(r.branches.vs.re, -1e-3, 1e-7);
  assert.deepEqual(r.nodes['0'], { re: 0, im: 0, mag: 0, phaseDeg: 0 });
});

test('RC low-pass at pole frequency has -3.0103 dB and -45 deg', () => {
  const R = 1000, C = 1e-6, fp = 1 / (2 * Math.PI * R * C);
  const r = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'out', value: R },
      { id: 'c1', type: 'C', n1: 'out', n2: '0', value: C },
    ],
  }, { freqHz: fp });
  assert.equal(r.ok, true);
  approx(20 * Math.log10(r.nodes.out.mag), -3.0103, 1e-3);
  approx(r.nodes.out.phaseDeg, -45, 1e-2);
});

test('Example I CG V-V closed loop matches 8/3 exactly', () => {
  const r = solveCircuit({
    elements: [
      { id: 'vin', type: 'vsrc', n1: 's', n2: '0', value: 1 },
      { id: 'gm1', type: 'vccs', cp: 'g', cn: 's', n1: 'out', n2: 's', gm: 4e-3 },
      { id: 'rd', type: 'R', n1: 'out', n2: '0', value: 4000 },
      { id: 'r1', type: 'R', n1: 'out', n2: 'g', value: 3000 },
      { id: 'r2', type: 'R', n1: 'g', n2: '0', value: 1000 },
    ],
  });
  assert.equal(r.ok, true);
  approx(r.nodes.out.re, 8 / 3, 1e-4);
  approx(r.nodes.g.re, 2 / 3, 1e-4);
  // Check VCCS branch current: gm * (V(g) - V(s)) = 4e-3 * (2/3 - 1) = -4/3 mA
  approx(r.branches.gm1.re, -4e-3 / 3, 1e-7);
});

test('short/open switches and singular circuit diagnostics (Review Focus #1)', () => {
  const shorted = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'a', n2: '0', value: 1 },
      { id: 'bad', type: 'short', n1: 'a', n2: '0' },
    ],
  });
  assert.equal(shorted.ok, false);
  assert.equal(shorted.singular, true);
  assert.ok(shorted.reason.length > 0);

  const floating = solveCircuit({
    elements: [
      { id: 'r1', type: 'R', n1: 'x', n2: 'y', value: 1000 },
      { id: 'op', type: 'open', n1: 'x', n2: '0' },
    ],
  });
  assert.equal(floating.ok, false);
  assert.equal(floating.singular, true);
  assert.ok(floating.reason.length > 0);

  const validOpen = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'a', n2: '0', value: 3 },
      { id: 'r1', type: 'R', n1: 'a', n2: '0', value: 1000 },
      { id: 'op', type: 'open', n1: 'a', n2: '0' },
    ],
  });
  assert.equal(validOpen.ok, true);
  assert.deepEqual(validOpen.branches.op, { re: 0, im: 0, mag: 0, phaseDeg: 0 });
});

test('inductor L behaves as short at DC and j*omega*L at AC', () => {
  const R = 1000;
  const L = 1e-3;
  const fp = R / (2 * Math.PI * L);

  // At DC (freqHz = 0), L is a short (0 V source), so out == in and I_L = 1 mA
  const dc = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'l1', type: 'L', n1: 'in', n2: 'out', value: L },
      { id: 'r1', type: 'R', n1: 'out', n2: '0', value: R },
    ],
  }, { freqHz: 0 });
  assert.equal(dc.ok, true);
  approx(dc.nodes.out.re, 1.0, 1e-6);
  approx(dc.nodes.out.im, 0.0, 1e-6);
  approx(dc.branches.l1.re, 1e-3, 1e-7);

  // At AC pole frequency, |H(jwp)| = 1/sqrt(2) (-3.0103 dB), phase = -45 deg
  const ac = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'l1', type: 'L', n1: 'in', n2: 'out', value: L },
      { id: 'r1', type: 'R', n1: 'out', n2: '0', value: R },
    ],
  }, { freqHz: fp });
  assert.equal(ac.ok, true);
  approx(20 * Math.log10(ac.nodes.out.mag), -3.0103, 1e-3);
  approx(ac.nodes.out.phaseDeg, -45, 1e-2);
  // Current through L equals current through R (n1 -> n2)
  approx(ac.branches.l1.re, ac.branches.r1.re, 1e-7);
  approx(ac.branches.l1.im, ac.branches.r1.im, 1e-7);
});

test('independent current source isrc and custom ground / ground-referenced ports', () => {
  // isrc from gnd -> out injects 2 mA into out, with R = 2000 || VCCS to ground
  const r = solveCircuit({
    ground: 'gnd',
    elements: [
      { id: 'is1', type: 'isrc', n1: 'gnd', n2: 'out', value: 2e-3 },
      { id: 'r1', type: 'R', n1: 'out', n2: 'gnd', value: 2000 },
      // VCCS with cp=gnd, cn=out: I(out -> gnd) = gm * (0 - Vout) => acts like negative conductance? No, leaves out: -gm * Vout => adds -gm to Y_out?
      // Wait: I = gm*(V(cp) - V(cn)) = gm*(0 - Vout) = -gm*Vout flowing out -> gnd.
      // KCL at out: Vout/2000 - gm*Vout = 2e-3 => Vout*(0.5e-3 - 0.25e-3) = 2e-3 => Vout = 8 V.
      { id: 'gm1', type: 'vccs', cp: 'gnd', cn: 'out', n1: 'out', n2: 'gnd', gm: 0.25e-3 },
    ],
  });
  assert.equal(r.ok, true);
  assert.deepEqual(r.nodes.gnd, { re: 0, im: 0, mag: 0, phaseDeg: 0 });
  approx(r.nodes.out.re, 8.0, 1e-4);
  approx(r.branches.is1.re, 2e-3, 1e-7);
  approx(r.branches.r1.re, 4e-3, 1e-7);
  approx(r.branches.gm1.re, -2e-3, 1e-7);

  // vsrc with n1 = ground, n2 = node
  const vneg = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: '0', n2: 'a', value: 5 },
      { id: 'r1', type: 'R', n1: 'a', n2: '0', value: 1000 },
    ],
  });
  assert.equal(vneg.ok, true);
  approx(vneg.nodes.a.re, -5.0, 1e-6);
  approx(vneg.branches.r1.re, -5e-3, 1e-7);
  approx(vneg.branches.vs.re, -5e-3, 1e-7);
});

test('edge cases: zero C/L, invalid element values, and globalThis.EC2MNA exposure', () => {
  assert.equal(typeof globalThis.EC2MNA?.solveCircuit, 'function');

  // C = 0 acts as open at AC; L = 0 acts as short at AC
  const zeroCL = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 2 },
      { id: 'l0', type: 'L', n1: 'in', n2: 'out', value: 0 },
      { id: 'c0', type: 'C', n1: 'out', n2: '0', value: 0 },
      { id: 'r1', type: 'R', n1: 'out', n2: '0', value: 1000 },
    ],
  }, { freqHz: 1e6 });
  assert.equal(zeroCL.ok, true);
  approx(zeroCL.nodes.out.re, 2.0, 1e-6);
  approx(zeroCL.branches.c0.mag, 0, 1e-9);
  approx(zeroCL.branches.l0.re, 2e-3, 1e-7);

  // R <= 0 returns clean error
  const badR = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'r0', type: 'R', n1: 'in', n2: '0', value: 0 },
    ],
  });
  assert.equal(badR.ok, false);
  assert.equal(badR.singular, true);
  assert.ok(badR.reason.length > 0);

  // NaN value returns clean error without throwing
  const nanVal = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: Number.NaN },
      { id: 'r1', type: 'R', n1: 'in', n2: '0', value: 1000 },
    ],
  });
  assert.equal(nanVal.ok, false);
  assert.equal(nanVal.singular, true);
  assert.ok(nanVal.reason.length > 0);
});
