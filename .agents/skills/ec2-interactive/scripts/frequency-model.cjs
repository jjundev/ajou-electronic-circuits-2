function createFrequencyModel() {
  function positive(value,name) {
    if (!Number.isFinite(value) || value <= 0) throw new RangeError(name + ' must be positive SI');
    return value;
  }
  function frequency(w) {
    if (!Number.isFinite(w) || w < 0) throw new RangeError('omega must be finite and nonnegative');
    return w;
  }
  function response(A0,wp1,wp2,omega) {
    frequency(omega);
    const x = omega/wp1, y = wp2 ? omega/wp2 : 0;
    const inputLossDb = wp2 ? -10*Math.log10(1+x*x) : 0;
    const outputLossDb = -10*Math.log10(1+(wp2 ? y*y : x*x));
    const db = 20*Math.log10(A0)+inputLossDb+outputLossDb;
    const bodeDb = 20*Math.log10(A0)-20*Math.max(0,Math.log10(x))
      -(wp2 ? 20*Math.max(0,Math.log10(y)) : 0);
    let w3 = wp1;
    if (wp2) {
      const a = 1/(wp1*wp1)+1/(wp2*wp2);
      const b = 1/((wp1*wp2)*(wp1*wp2));
      w3 = Math.sqrt(2/(a+Math.sqrt(a*a+4*b)));
    }
    return {
      A0,wp1,wp2:wp2 || null,fp1:wp1/(2*Math.PI),
      fp2:wp2 ? wp2/(2*Math.PI) : null,f3db:w3/(2*Math.PI),
      mag:10**(db/20),db,bodeDb,
      phaseDeg:-180-(Math.atan(x)+(wp2 ? Math.atan(y) : 0))*180/Math.PI,
      inputLossDb,outputLossDb
    };
  }
  function cs(p,w=0) {
    const A0=positive(p.gm,'gm')*positive(p.RD,'RD');
    return response(A0,1/(p.RD*positive(p.CL,'CL')),null,w);
  }
  function two(p,w=0) {
    const A0=positive(p.gm,'gm')*positive(p.RD,'RD');
    const wp1=1/(positive(p.RS,'RS')*positive(p.Cin,'Cin'));
    const wp2=1/(p.RD*positive(p.CL,'CL'));
    return response(A0,wp1,wp2,w);
  }
  function wave(r,t,inputPeak=1e-4) {
    if (!Number.isFinite(t)) throw new RangeError('t/T must be finite');
    positive(inputPeak,'inputPeak');
    const theta=2*Math.PI*t;
    return {vin:inputPeak*Math.sin(theta),
      vout:r.mag*inputPeak*Math.sin(theta+r.phaseDeg*Math.PI/180),
      inputPeak,outputPeak:r.mag*inputPeak};
  }
  return Object.freeze({cs,two,wave});
}
module.exports={createFrequencyModel};
