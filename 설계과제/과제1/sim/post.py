"""ngspice 결과(op.txt, ac.txt, tran.txt) → 그래프 PNG + 포화 검증 표."""
import re, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
FIG = '../report/figs'
import os; os.makedirs(FIG, exist_ok=True)

# --- Transient ---
d = np.loadtxt('tran.txt'); t = d[:, 0] * 1e6
vin1, vin2, vop, von = d[:, 1], d[:, 3], d[:, 5], d[:, 7]
vid, vod = (vin1 - vin2) * 1e3, (vop - von) * 1e3
fig, ax = plt.subplots(3, 1, sharex=True, figsize=(7, 7))
ax[0].plot(t, vin1, label='$V_{in1}$'); ax[0].plot(t, vin2, '--', label='$V_{in2}$')
ax[0].set_ylabel('V'); ax[0].legend(loc='upper right'); ax[0].set_title('Inputs (CM 0.7236 V, ±0.5 mV each, 1 MHz)')
ax[1].plot(t, vop, label='$V_{out+}$ (M3/M5 drain)'); ax[1].plot(t, von, '--', label='$V_{out-}$ (M4/M6 drain)')
ax[1].set_ylabel('V'); ax[1].legend(loc='upper right'); ax[1].set_title('Single-ended outputs')
ax[2].plot(t, vid * 100, label='$V_{in1}-V_{in2}$  (×100)'); ax[2].plot(t, vod, label='$V_{out+}-V_{out-}$')
ax[2].set_ylabel('mV'); ax[2].set_xlabel('time [µs]'); ax[2].legend(loc='upper right')
ax[2].set_title('Differential input (×100) vs differential output')
for a in ax: a.grid(alpha=.3)
plt.tight_layout(); plt.savefig(f'{FIG}/tran_1MHz.png', dpi=130)
m = t > 2  # 초기 과도 제외
av_tran = np.ptp(vod[m]) / np.ptp(vid[m])
print(f'tran: vid_pp={np.ptp(vid[m]):.4f} mV  vod_pp={np.ptp(vod[m]):.2f} mV  Av={av_tran:.1f}')

# --- AC ---
a = np.loadtxt('ac.txt'); f, av, ph = a[:, 0], a[:, 1], a[:, 3]
plt.figure(figsize=(7, 3.5)); plt.semilogx(f, 20 * np.log10(av))
plt.axvline(1e6, ls=':', c='gray'); plt.text(1.1e6, 20*np.log10(av[0]) - 15, '1 MHz')
plt.xlabel('frequency [Hz]'); plt.ylabel('|Av| [dB]'); plt.grid(alpha=.3, which='both')
plt.title(f'Differential gain: {av[0]:.1f} ({20*np.log10(av[0]):.2f} dB)')
plt.tight_layout(); plt.savefig(f'{FIG}/ac_gain.png', dpi=130)

# --- Bode (크기·위상) ---
k = np.argmax(av < av[0] / np.sqrt(2))  # -3 dB 를 처음 넘는 점, 로그 주파수로 선형 보간
f3 = 10 ** np.interp(av[0] / np.sqrt(2), [av[k], av[k - 1]], np.log10([f[k], f[k - 1]]))
fig, ax = plt.subplots(2, 1, sharex=True, figsize=(7, 5.5))
ax[0].semilogx(f, 20 * np.log10(av)); ax[0].set_ylabel('|Av| [dB]')
ax[0].set_title(f'$(V_{{out+}}-V_{{out-}})/(V_{{in1}}-V_{{in2}})$ = {av[0]:.1f} ({20*np.log10(av[0]):.2f} dB),  $f_{{-3dB}}$ ≈ {f3/1e6:.0f} MHz', fontsize=11)
ax[0].text(1.15e6, 20*np.log10(av[0]) - 12, '1 MHz', color='gray')
ax[1].semilogx(f, ph); ax[1].set_ylabel('phase [deg]'); ax[1].set_xlabel('frequency [Hz]')
for x in ax:
    x.axvline(1e6, ls=':', c='gray'); x.axvline(f3, ls='--', c='tab:red', lw=.8); x.grid(alpha=.3, which='both')
plt.tight_layout(); plt.savefig(f'{FIG}/ac_bode.png', dpi=130)
print(f'ac: av_1k={av[0]:.3f}  f3db={f3/1e6:.1f} MHz  ph(1k)={ph[0]:.2f}  ph(1M)={np.interp(1e6, f, ph):.2f}')

# --- Saturation table ---
txt = open('op.txt').read().split('=== DEVICES ===')[1]
rows = {}
for line in txt.splitlines():
    p = line.split()
    if len(p) >= 2 and p[0] in ('device', 'id', 'vgs', 'vds', 'vdsat', 'gm', 'gds'):
        rows.setdefault(p[0], []).extend(p[1:])
names = [n.upper() for n in rows['device']]
order = ['M1', 'M2', 'MSS', 'M3', 'M4', 'M5', 'M6', 'M7']
out = ['| MOSFET | I_D [µA] | \\|V_GS\\| [V] | \\|V_GS\\|−V_TH [V] | \\|V_DS\\| [V] | margin [V] | region |',
       '|---|---|---|---|---|---|---|']
for n in order:
    i = names.index(n)
    idv, vgs, vds, vds_at = (abs(float(rows[k][i])) for k in ('id', 'vgs', 'vds', 'vdsat'))
    ok = vgs > 0.4 and vds >= vds_at
    out.append(f'| {n} | {idv*1e6:.2f} | {vgs:.4f} | {vds_at:.4f} | {vds:.4f} | {vds-vds_at:.4f} | {"saturation ✔" if ok else "✘"} |')
open('../report/sat_table.md', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
