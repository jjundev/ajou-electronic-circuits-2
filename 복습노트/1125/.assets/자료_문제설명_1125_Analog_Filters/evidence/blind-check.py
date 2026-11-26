"""Independent small-signal node-equation check (blind solver).
Each circuit is solved exactly by KCL (numpy linear solve) and compared with
the closed forms derived by the feedback two-port method."""
import numpy as np
rng = np.random.default_rng(1125)

def solve(names, eqs):
    """eqs(v: dict)->list of residuals, linear in unknowns."""
    n = len(names)
    def F(x):
        return np.array(eqs(dict(zip(names, x))), float)
    f0 = F(np.zeros(n))
    A = np.column_stack([F(np.eye(n)[j]) - f0 for j in range(n)])
    return dict(zip(names, np.linalg.solve(A, -f0)))

def par(*r):
    return 1/sum(1/x for x in r)

def rel(a, b):
    return abs(a-b)/max(abs(a), abs(b))

out = []
def log(*a):
    s = ' '.join(str(x) for x in a); print(s); out.append(s)

# ---------------- P1: CG M1 (source=Vin, gate=V_F) + NMOS SF M2, lambda=0 ----------
res = 0
resRout_conv = []
for _ in range(200):
    gm1, gm2 = rng.uniform(1e-3, 1e-2, 2); RD, RM, RL = rng.uniform(100, 1e4, 3)
    def circ(vin=1.0, vt_gate=None, port_i=None, RLx=RL):
        def eqs(v):
            vg1 = v['F'] if vt_gate is None else vt_gate
            id1 = gm1*(vg1 - vin)                 # drain->source of M1
            id2 = gm2*(v['X'] - v['S2'])           # M2 (drain at VDD) current into laser
            e = [-v['X']/RD - id1]                 # KCL at X
            if port_i is None:
                e += [id2 - (v['S2']-v['F'])/RLx, id2 - v['F']/RM]
            else:                                  # laser replaced by test current port_i (S2->F)
                e += [id2 - port_i, port_i - v['F']/RM]
            return e
        return solve(['X','S2','F'], eqs), gm1, gm2
    s,_,_ = circ()
    Iout = s['F']/RM
    A = gm1*RD/(1/gm2+RL+RM); T = gm1*RD*RM/(1/gm2+RL+RM)
    res = max(res, rel(Iout, A/(1+T)))
    # loop gain by breaking at M1 gate
    s,_,_ = circ(vin=0.0, vt_gate=1.0)
    res = max(res, rel(-s['F'], T))
    # input impedance: current delivered by Vin = -id1
    s,_,_ = circ()
    iin = -gm1*(s['F'] - 1.0)
    res = max(res, rel(1/iin, (1+T)/gm1))
    # output impedance seen by the laser (laser removed, test current)
    s,_,_ = circ(vin=0.0, port_i=1.0)
    Z = -(s['S2'] - s['F'])/1.0
    exact = 1/gm2 + RM + gm1*RD*RM
    res = max(res, rel(Z, exact))
    res = max(res, rel(Z, (1/gm2+RM)*(1+gm1*RD*RM/(1/gm2+RM))))
    resRout_conv.append(rel(Z, (1/gm2+RM)*(1+T)))
log('P1 max rel residual (gain, loop gain, Rin, Rout seen by laser):', res)
log('P1 textbook-convention Rout=(1/gm2+RM)(1+T incl RL) vs exact: max rel diff', max(resRout_conv), '(-> 0 as RL/(1/gm2+RM) -> 0)')

# ---------------- P2: 5T OTA (M3 Vin, M4 V_F, M5/M6 PMOS mirror, M6 diode) + PMOS CS M1 ----
def p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM, vin=1.0, gate4=None, port_i=None):
    def eqs(v):
        g4 = v['F'] if gate4 is None else gate4
        id3 = gmN*(vin - v['T']) + (v['X']-v['T'])/roN
        id4 = gmN*(g4 - v['T']) + (v['Y']-v['T'])/roN
        isd5 = gmP*(0 - v['Y']) + (0 - v['X'])/roP
        isd6 = gmP*(0 - v['Y']) + (0 - v['Y'])/roP
        isd1 = gm1*(0 - v['X']) + (0 - v['D'])/ro1
        e = [id3 + id4, isd5 - id3, isd6 - id4]
        if port_i is None:
            e += [isd1 - (v['D']-v['F'])/RL, isd1 - v['F']/RM]
        else:
            e += [isd1 - port_i, port_i - v['F']/RM]
        return e
    return solve(['T','X','Y','D','F'], eqs)

log('P2 scaling check: ratio exact/approx -> 1 as gm*ro grows')
for k in [10, 100, 1000, 10000]:
    gmN, gmP, gm1 = 2e-3, 1e-3, 5e-3
    roN, roP, ro1 = k/gmN, k/gmP, k/gm1
    RL, RM = 50.0, 1e3
    s = p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM)
    Iout = s['F']/RM
    A = gmN*par(roN, roP)*gm1*ro1/(ro1+RL+RM); T = RM*A
    # open loop (M4 gate at ac ground, RM kept in the output loop)
    so = p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM, gate4=0.0)
    Aex = so['F']/RM
    # loop gain by breaking at M4 gate
    sl = p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM, vin=0.0, gate4=1.0)
    Tex = -sl['F']
    # output impedance seen by laser (closed loop) and open loop (M4 gate grounded)
    sz = p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM, vin=0.0, port_i=1.0)
    Z = -(sz['D']-sz['F'])
    szo = p2(gmN, roN, gmP, roP, gm1, ro1, RL, RM, vin=0.0, gate4=0.0, port_i=1.0)
    Zo = -(szo['D']-szo['F'])
    Zex_formula = ro1 + RM + gmN*par(roN, roP)*gm1*ro1*RM
    log(f'  gm*ro={k}: A_open {Aex/A:.6f}, T {Tex/T:.6f}, Aclosed {Iout/(A/(1+T)):.6f}, '
        f'Rout_open {Zo/(ro1+RM):.6f}, Rout_closed(laser view) {Z/Zex_formula:.6f}, '
        f'textbook (ro1+RM)(1+T) {Z/((ro1+RM)*(1+T)):.6f}')

# ---------------- P3/P4: C-C laser driver (E12.32) ----------------
def p3(gm1, RD, gm2, ro2, RF, RM, RL, Iin=1.0, port_i=None, short=False):
    def eqs(v):
        id1 = gm1*(0 - v['S'])                      # M1 gate at ac ground
        isd2 = gm2*(0 - v['X']) + (0 - v['D'])/ro2   # PMOS M2
        e = [Iin + id1 - (v['S']-v['P'])/RF, -v['X']/RD - id1]
        if port_i is not None:
            I = port_i
        elif short:
            I = isd2
            e += [v['D'] - v['P']]
        else:
            I = (v['D']-v['P'])/RL
        e += [isd2 - I if port_i is not None else (isd2 - (v['D']-v['P'])/RL if not short else 0*v['S']),
              I + (v['S']-v['P'])/RF - v['P']/RM]
        if short:
            e = e[:3] + [e[4]]
        return e
    return solve(['S','X','D','P'], eqs)

def tp3(gm1, RD, gm2, ro2, RF, RM, RL):
    a = RD*(RF+RM)/(RF+RM+1/gm1)
    A = a*(-gm2*ro2)/(ro2+RL+par(RF,RM))
    K = -RM/(RM+RF)
    T = K*A
    G = gm2*ro2*RD*RM/(RF+RM+1/gm1)
    return dict(a=a, A=A, K=K, T=T, Acl=A/(1+T), Rin_o=par(1/gm1, RF+RM), Rin_c=par(1/gm1, RF+RM)/(1+T),
                Ro=ro2+par(RF,RM), G=G)

log('P3/P4 scaling check (gm1=gm2=g, ro2=k/g, RD=RF=2k, RM=500, RL=50)')
for k in [10, 100, 1000, 10000]:
    gm1 = gm2 = 4e-3; ro2 = k/gm2; RD, RF, RM, RL = 2e3, 2e3, 500.0, 50.0
    t = tp3(gm1, RD, gm2, ro2, RF, RM, RL)
    s = p3(gm1, RD, gm2, ro2, RF, RM, RL)
    Iout = (s['D']-s['P'])/RL; Rin = s['S']
    sz = p3(gm1, RD, gm2, ro2, RF, RM, RL, Iin=0.0, port_i=1.0)
    Z = -(sz['D']-sz['P'])
    Zexact = ro2 + par(RM, RF+1/gm1) + t['G']
    sn = p3(gm1, RD, gm2, ro2, RF, RM, RL, short=True)
    IN = (0 - gm2*sn['X'] - sn['D']/ro2)
    t0 = tp3(gm1, RD, gm2, ro2, RF, RM, 0.0)
    IN2p = t0['Acl']
    RN2p = t['Ro'] + t['G']
    log(f'  gm*ro={k}: Acl exact/2port {Iout/t["Acl"]:.6f}, Rin exact/2port {Rin/t["Rin_c"]:.6f}, '
        f'Rout exact vs closed-form exact {Z/Zexact:.9f}, Rout exact/(Ro+G) {Z/RN2p:.6f}, '
        f'Rout exact/textbook Ro(1+T(RL)) {Z/(t["Ro"]*(1+t["T"])):.6f}, IN exact/2port {IN/IN2p:.6f}, '
        f'Norton check IN*RN/(RN+RL) vs Iout {IN*Z/(Z+RL)/Iout:.9f}')

# random check of identity Acl(RL) == IN*RN/(RN+RL) within the two-port model
mx = 0
for _ in range(200):
    gm1, gm2 = rng.uniform(1e-3,1e-2,2); ro2 = rng.uniform(1e3,1e6); RD, RF, RM, RL = rng.uniform(50,1e4,4)
    t = tp3(gm1, RD, gm2, ro2, RF, RM, RL); t0 = tp3(gm1, RD, gm2, ro2, RF, RM, 0.0)
    RN = t['Ro'] + t['G']
    mx = max(mx, rel(t0['Acl']*RN/(RN+RL), t['Acl']), rel(RN, t0['Ro']*(1+t0['T'])))
    sz = p3(gm1, RD, gm2, ro2, RF, RM, RL, Iin=0.0, port_i=1.0)
    mx = max(mx, rel(-(sz['D']-sz['P']), ro2 + par(RM, RF+1/gm1) + t['G']))
log('P4 two-port identities (Acl = IN*RN/(RN+RL), RN = Ro(1+T|RL=0)) and exact Rout closed form: max rel residual', mx)

# ---------------- P5: V-C (E12.33), output V_out at node P ----------------
def p5(gm1, RD, gm2, ro2, RF, RM, Iin=1.0, inj=0.0):
    def eqs(v):
        id1 = gm1*(0 - v['S'])
        e = [Iin + id1 - (v['S']-v['P'])/RF, -v['X']/RD - id1,
             inj + gm2*(0 - v['X']) - v['P']/ro2 + (v['S']-v['P'])/RF - v['P']/RM]
        return e
    return solve(['S','X','P'], eqs)
mx = 0
log('P5 scaling (exact/2port)')
for k in [10, 100, 1000, 10000]:
    gm1 = gm2 = 4e-3*k/100; ro2 = 2.5e4; RD, RF, RM = 2e3, 2e3, 500.0
    Ro = par(ro2, RM, RF); RO = -gm2*RD*RF/(RF+1/gm1)*Ro; K = -1/RF; T = K*RO
    s = p5(gm1, RD, gm2, ro2, RF, RM)
    so = p5(gm1, RD, gm2, ro2, RF, RM, Iin=0.0, inj=1.0)
    log(f'  gm1*gm2*RD*RF={gm1*gm2*RD*RF:.3g}: Vout/Iin {s["P"]/(RO/(1+T)):.6f}, Rin {s["S"]/(par(1/gm1,RF)/(1+T)):.6f}, '
        f'Rout {so["P"]/(Ro/(1+T)):.6f}')
for _ in range(200):
    gm1, gm2 = rng.uniform(1e-3,1e-2,2); ro2 = rng.uniform(1e3,1e6); RD, RF, RM = rng.uniform(50,1e4,3)
    Ro = par(ro2, RM, RF)
    s = p5(gm1, RD, gm2, ro2, RF, RM); so = p5(gm1, RD, gm2, ro2, RF, RM, Iin=0.0, inj=1.0)
    ex_RO = (1/gm1 - gm2*RD*RF)*Ro/(RF + 1/gm1 + gm2*RD*Ro - Ro/(gm1*RF))
    ex_Rout = 1/(1/ro2 + 1/RM + 1/(RF+1/gm1) + gm1*gm2*RD/(1+gm1*RF))
    ex_Rin = (RF/gm1)/(RF + 1/gm1 + gm2*RD*Ro - Ro/(gm1*RF))
    mx = max(mx, rel(s['P'], ex_RO), rel(so['P'], ex_Rout), rel(s['S'], ex_Rin))
log('P5 exact closed forms vs node solve: max rel residual', mx)
