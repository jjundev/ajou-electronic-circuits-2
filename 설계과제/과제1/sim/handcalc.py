"""설계과제1 손계산: 과제 주어진 값(µnCox=100µ, µpCox=50µ, λ 포함 square-law)으로 W/L·바이어스 결정."""
kn, kp = 100e-6, 50e-6
ln, lp = 0.1, 0.2
VTH, VDD, L = 0.4, 1.5, 0.18          # L in µm
ISS, I1 = 200e-6, 100e-6
ID = ISS / 2
# 설계 선택: 노드 전압과 Vov
VS, VX, VOUT = 0.25, 0.40, 0.95       # tail, cascode source, output CM
VOV_SS, VOV3, VOV5 = 0.2, 0.2, 0.2
AV_TARGET = 150

def ro(lam, i, vds):                  # Level-1: gds = λ·ID/(1+λVDS)
    return (1 + lam * vds) / (lam * i)

def gain(vov1):
    gm1, gm3 = 2 * ID / vov1, 2 * ID / VOV3
    ro1, ro3 = ro(ln, ID, VX - VS), ro(ln, ID, VOUT - VX)
    ro6 = ro(lp, ID, VDD - VOUT)
    rcas = ro1 + ro3 + gm3 * ro3 * ro1
    rout = ro6 * rcas / (ro6 + rcas)
    return gm1 * rout, dict(gm1=gm1, gm3=gm3, ro1=ro1, ro3=ro3, ro6=ro6, rcas=rcas, rout=rout)

lo, hi = 0.03, 0.2                    # gain은 Vov1에 대해 단조감소 → 이분법
for _ in range(60):
    m = (lo + hi) / 2
    lo, hi = (m, hi) if gain(m)[0] > AV_TARGET else (lo, m)
VOV1 = round(m, 4)
av, ss = gain(VOV1)

def wl(i, k, vov, lam, vds):
    return 2 * i / (k * vov**2 * (1 + lam * vds))

dev = {
    'M1,M2': wl(ID, kn, VOV1, ln, VX - VS),
    'M3,M4': wl(ID, kn, VOV3, ln, VOUT - VX),
    'MSS':   wl(ISS, kn, VOV_SS, ln, VS),
    'M5,M6': wl(ID, kp, VOV5, lp, VDD - VOUT),
    'M7':    wl(I1, kp, VOV5, lp, VTH + VOV5),
}
W = {k: round(v * L, 2) for k, v in dev.items()}
VINCM = VS + VTH + VOV1
VB2 = VX + VTH + VOV3
VB1 = VTH + VOV_SS
VG7 = VDD - VTH - VOV5

if __name__ == '__main__':
    print(f'Vov1 = {VOV1} V  ->  Av = {av:.1f}')
    for k, v in ss.items():
        print(f'  {k:5s} = {v:.4g}')
    for k in dev:
        print(f'{k:6s} W/L = {dev[k]:7.2f}  W = {W[k]:6.2f} um')
    print(f'Vin,CM = {VINCM:.4f}  Vb2 = {VB2:.2f}  Vb1 = {VB1:.2f}  VG7 = {VG7:.2f}')
    print(f'P = {(ISS + I1) * VDD * 1e3:.3f} mW')
    with open('params.inc', 'w') as f:
        f.write(f".param W1={W['M1,M2']}u W3={W['M3,M4']}u WSS={W['MSS']}u "
                f"W5={W['M5,M6']}u W7={W['M7']}u\n"
                f".param VCM={VINCM:.4f} VB2={VB2:.2f} I1V={I1}\n")
