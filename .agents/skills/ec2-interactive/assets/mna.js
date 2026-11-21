// Lightweight complex small-signal Modified Nodal Analysis (MNA) solver.
// Zero dependencies; exposes globalThis.EC2MNA and CommonJS module.exports.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.EC2MNA = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const PIVOT_EPS = 1e-14;
  const SUPPORTED_TYPES = new Set(['R', 'C', 'L', 'vccs', 'vsrc', 'isrc', 'short', 'open']);

  function c(re, im = 0) {
    return { re, im };
  }

  function cAdd(a, b) {
    return { re: a.re + b.re, im: a.im + b.im };
  }

  function cSub(a, b) {
    return { re: a.re - b.re, im: a.im - b.im };
  }

  function cMul(a, b) {
    return {
      re: a.re * b.re - a.im * b.im,
      im: a.re * b.im + a.im * b.re,
    };
  }

  function cDiv(a, b) {
    const denom = b.re * b.re + b.im * b.im;
    return {
      re: (a.re * b.re + a.im * b.im) / denom,
      im: (a.im * b.re - a.re * b.im) / denom,
    };
  }

  function cAbs(a) {
    return Math.hypot(a.re, a.im);
  }

  function toPhasor(z) {
    const re = z.re === 0 ? 0 : z.re;
    const im = z.im === 0 ? 0 : z.im;
    const mag = Math.hypot(re, im);
    const phaseDeg = mag === 0 ? 0 : (Math.atan2(im, re) * 180) / Math.PI;
    return { re, im, mag, phaseDeg };
  }

  function fail(reason) {
    return { ok: false, singular: true, reason };
  }

  function isNonEmptyString(v) {
    return typeof v === 'string' && v.length > 0;
  }

  function parseComplexOrReal(v) {
    if (typeof v === 'number' && Number.isFinite(v)) {
      return c(v, 0);
    }
    if (v && typeof v === 'object' && Number.isFinite(v.re) && Number.isFinite(v.im)) {
      return c(v.re, v.im);
    }
    return null;
  }

  function solveLinearComplex(A, b, varNames) {
    const n = b.length;
    for (let col = 0; col < n; col++) {
      let pivotRow = col;
      let pivotMag = cAbs(A[col][col]);
      for (let row = col + 1; row < n; row++) {
        const mag = cAbs(A[row][col]);
        if (mag > pivotMag) {
          pivotMag = mag;
          pivotRow = row;
        }
      }
      if (!Number.isFinite(pivotMag) || pivotMag < PIVOT_EPS) {
        const label = varNames[col] || `col ${col}`;
        return { ok: false, reason: `Singular circuit matrix at ${label} (|pivot|=${pivotMag})` };
      }
      if (pivotRow !== col) {
        const tmpRow = A[col];
        A[col] = A[pivotRow];
        A[pivotRow] = tmpRow;
        const tmpB = b[col];
        b[col] = b[pivotRow];
        b[pivotRow] = tmpB;
      }
      const pivot = A[col][col];
      for (let row = col + 1; row < n; row++) {
        const entry = A[row][col];
        if (entry.re === 0 && entry.im === 0) continue;
        const factor = cDiv(entry, pivot);
        A[row][col] = c(0, 0);
        for (let j = col + 1; j < n; j++) {
          A[row][j] = cSub(A[row][j], cMul(factor, A[col][j]));
        }
        b[row] = cSub(b[row], cMul(factor, b[col]));
      }
    }

    const x = new Array(n);
    for (let row = n - 1; row >= 0; row--) {
      let sum = b[row];
      for (let j = row + 1; j < n; j++) {
        sum = cSub(sum, cMul(A[row][j], x[j]));
      }
      const val = cDiv(sum, A[row][row]);
      if (!Number.isFinite(val.re) || !Number.isFinite(val.im)) {
        return { ok: false, reason: `Non-finite solution at ${varNames[row] || row}` };
      }
      x[row] = val;
    }
    return { ok: true, x };
  }

  function validateElements(elements) {
    const seenIds = new Set();
    for (let i = 0; i < elements.length; i++) {
      const el = elements[i];
      if (!el || typeof el !== 'object') {
        return `Invalid element at index ${i}`;
      }
      if (!isNonEmptyString(el.id)) {
        return `Element at index ${i} is missing a valid id`;
      }
      if (seenIds.has(el.id)) {
        return `Duplicate element id: ${el.id}`;
      }
      seenIds.add(el.id);

      if (!SUPPORTED_TYPES.has(el.type)) {
        return `Unsupported element type "${el.type}" for ${el.id}`;
      }
      if (!isNonEmptyString(el.n1) || !isNonEmptyString(el.n2)) {
        return `Element ${el.id} is missing valid node names n1/n2`;
      }

      if (el.type === 'R') {
        if (typeof el.value !== 'number' || !Number.isFinite(el.value) || el.value <= 0 || !Number.isFinite(1 / el.value)) {
          return `Resistor ${el.id} must have finite value > 0`;
        }
      } else if (el.type === 'C' || el.type === 'L') {
        if (typeof el.value !== 'number' || !Number.isFinite(el.value) || el.value < 0) {
          return `${el.type} element ${el.id} must have finite value >= 0`;
        }
      } else if (el.type === 'vccs') {
        if (!isNonEmptyString(el.cp) || !isNonEmptyString(el.cn)) {
          return `VCCS ${el.id} is missing valid control nodes cp/cn`;
        }
        if (typeof el.gm !== 'number' || !Number.isFinite(el.gm)) {
          return `VCCS ${el.id} must have finite gm`;
        }
      } else if (el.type === 'vsrc' || el.type === 'isrc') {
        if (!parseComplexOrReal(el.value)) {
          return `Source ${el.id} must have finite numeric value`;
        }
      }
    }
    return null;
  }

  function solveCircuit(netlist, options = {}) {
    if (!netlist || typeof netlist !== 'object' || !Array.isArray(netlist.elements)) {
      return fail('Invalid netlist: elements array is required');
    }

    const ground = isNonEmptyString(netlist.ground) ? netlist.ground : '0';
    if (options !== undefined && options !== null && typeof options !== 'object') {
      return fail('Invalid options: expected an object');
    }
    const freqHz = options && options.freqHz !== undefined ? options.freqHz : 0;
    if (typeof freqHz !== 'number' || !Number.isFinite(freqHz) || freqHz < 0) {
      return fail('Invalid options.freqHz: must be a finite number >= 0');
    }

    const elements = netlist.elements;
    const validationError = validateElements(elements);
    if (validationError) {
      return fail(validationError);
    }

    const omega = 2 * Math.PI * freqHz;
    if (!Number.isFinite(omega)) {
      return fail('options.freqHz is too large (omega overflow)');
    }
    const isShortInductor = (el) => el.type === 'L' && (!Number.isFinite(1 / (omega * el.value)) || omega * el.value === 0);
    const nodeIndex = new Map();
    const nodeNames = [];
    const registerNode = (name) => {
      if (name === ground || nodeIndex.has(name)) return;
      nodeIndex.set(name, nodeNames.length);
      nodeNames.push(name);
    };

    const branchVars = [];
    for (const el of elements) {
      registerNode(el.n1);
      registerNode(el.n2);
      if (el.type === 'vccs') {
        registerNode(el.cp);
        registerNode(el.cn);
      }
      const isVsrcLike =
        el.type === 'vsrc' ||
        el.type === 'short' ||
        isShortInductor(el);
      if (isVsrcLike) {
        branchVars.push(el.id);
      }
    }

    const numNodes = nodeNames.length;
    const dim = numNodes + branchVars.length;
    if (dim === 0) {
      const branches = {};
      for (const el of elements) {
        if (el.type === 'isrc') {
          branches[el.id] = toPhasor(parseComplexOrReal(el.value));
        } else {
          branches[el.id] = toPhasor(c(0, 0));
        }
      }
      return {
        ok: true,
        singular: false,
        nodes: { [ground]: toPhasor(c(0, 0)) },
        branches,
      };
    }

    const A = Array.from({ length: dim }, () => Array.from({ length: dim }, () => c(0, 0)));
    const b = Array.from({ length: dim }, () => c(0, 0));
    const idx = (name) => (name === ground ? -1 : nodeIndex.get(name));
    const addA = (r, col, re, im) => {
      if (r < 0 || col < 0) return;
      A[r][col].re += re;
      A[r][col].im += im;
    };
    const addB = (r, re, im) => {
      if (r < 0) return;
      b[r].re += re;
      b[r].im += im;
    };
    const stampAdmittance = (i1, i2, yRe, yIm) => {
      addA(i1, i1, yRe, yIm);
      addA(i2, i2, yRe, yIm);
      addA(i1, i2, -yRe, -yIm);
      addA(i2, i1, -yRe, -yIm);
    };

    const branchRowById = new Map();
    let branchCursor = 0;

    for (const el of elements) {
      const i1 = idx(el.n1);
      const i2 = idx(el.n2);

      if (el.type === 'R') {
        stampAdmittance(i1, i2, 1 / el.value, 0);
      } else if (el.type === 'C') {
        if (freqHz > 0 && el.value > 0) {
          const bCap = omega * el.value;
          if (!Number.isFinite(bCap)) {
            return fail(`Susceptance overflow for capacitor ${el.id}`);
          }
          stampAdmittance(i1, i2, 0, bCap);
        }
      } else if (el.type === 'L') {
        if (!isShortInductor(el)) {
          stampAdmittance(i1, i2, 0, -1 / (omega * el.value));
        } else {
          const k = numNodes + branchCursor++;
          branchRowById.set(el.id, k);
          addA(i1, k, 1, 0);
          addA(i2, k, -1, 0);
          addA(k, i1, 1, 0);
          addA(k, i2, -1, 0);
        }
      } else if (el.type === 'vccs') {
        const icp = idx(el.cp);
        const icn = idx(el.cn);
        addA(i1, icp, el.gm, 0);
        addA(i1, icn, -el.gm, 0);
        addA(i2, icp, -el.gm, 0);
        addA(i2, icn, el.gm, 0);
      } else if (el.type === 'isrc') {
        const val = parseComplexOrReal(el.value);
        addB(i1, -val.re, -val.im);
        addB(i2, val.re, val.im);
      } else if (el.type === 'vsrc' || el.type === 'short') {
        const k = numNodes + branchCursor++;
        branchRowById.set(el.id, k);
        addA(i1, k, 1, 0);
        addA(i2, k, -1, 0);
        addA(k, i1, 1, 0);
        addA(k, i2, -1, 0);
        if (el.type === 'vsrc') {
          const val = parseComplexOrReal(el.value);
          addB(k, val.re, val.im);
        }
      }
      // 'open' adds no stamps.
    }

    const varNames = [
      ...nodeNames.map((n) => `node ${n}`),
      ...branchVars.map((id) => `branch ${id}`),
    ];
    const solved = solveLinearComplex(A, b, varNames);
    if (!solved.ok) {
      return fail(solved.reason);
    }

    const x = solved.x;
    const nodeVoltage = (name) => {
      const i = idx(name);
      return i < 0 ? c(0, 0) : x[i];
    };

    const nodes = { [ground]: toPhasor(c(0, 0)) };
    for (let i = 0; i < nodeNames.length; i++) {
      nodes[nodeNames[i]] = toPhasor(x[i]);
    }

    const branches = {};
    for (const el of elements) {
      const v1 = nodeVoltage(el.n1);
      const v2 = nodeVoltage(el.n2);
      const vDiff = cSub(v1, v2);
      let current;

      if (el.type === 'R') {
        current = cMul(c(1 / el.value, 0), vDiff);
      } else if (el.type === 'C') {
        current = freqHz > 0 && el.value > 0
          ? cMul(c(0, omega * el.value), vDiff)
          : c(0, 0);
      } else if (el.type === 'L') {
        current = !isShortInductor(el)
          ? cMul(c(0, -1 / (omega * el.value)), vDiff)
          : x[branchRowById.get(el.id)];
      } else if (el.type === 'vccs') {
        const vc = cSub(nodeVoltage(el.cp), nodeVoltage(el.cn));
        current = cMul(c(el.gm, 0), vc);
      } else if (el.type === 'isrc') {
        current = parseComplexOrReal(el.value);
      } else if (el.type === 'vsrc' || el.type === 'short') {
        current = x[branchRowById.get(el.id)];
      } else {
        current = c(0, 0);
      }

      if (!Number.isFinite(current.re) || !Number.isFinite(current.im)) {
        return fail(`Non-finite branch current for ${el.id}`);
      }
      branches[el.id] = toPhasor(current);
    }

    return { ok: true, singular: false, nodes, branches };
  }

  return { solveCircuit };
});
