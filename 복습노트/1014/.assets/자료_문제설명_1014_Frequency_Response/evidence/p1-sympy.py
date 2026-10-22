"""Blind independent qualitative reasoning; E11.03. No authored/reference solution read.
The optional first-order example illustrates the general loss of rapid changes; it is
not a claim that the unspecified video system has this exact transfer function.
"""
import sympy as sp
print('INPUT: video requires approximately 5 MHz; system upper bandwidth is insufficient.')
print('Independent physical derivation:')
print('1. Video voltage encodes brightness as the raster scans successive positions.')
print('2. A narrow bright/dark edge requires a rapid temporal voltage transition, hence high-frequency Fourier components.')
print('3. Insufficient upper bandwidth attenuates these rapid components relative to slowly varying/constant brightness.')
print('4. Output brightness cannot change as abruptly as the desired edge; adjacent picture details blend.')
print('CONCLUSION: edges and fine detail become blurred; sharp black-to-white boundaries become gradual brightness transitions.')
print('No numerical blur width, rise time or attenuation follows from 5 MHz alone; actual system transfer and scanning rate are unspecified.')
print('Illustrative first-order low-pass check only: H(s)=1/(1+s*tau), tau>0.')
s, t, tau, w = sp.symbols('s t tau w', positive=True)
y = sp.inverse_laplace_transform(1/(s*(1+s*tau)), s, t)
mag2 = 1/(1+(w*tau)**2)
print('Unit-step output:', y)
print('DC magnitude-squared limit:', sp.limit(mag2,w,0))
print('High-frequency magnitude-squared limit:', sp.limit(mag2,w,sp.oo))
print('Magnitude-squared derivative vs frequency:', sp.simplify(sp.diff(mag2,w)))
print('Settled unit-step value:', sp.limit(y,t,sp.oo))
print('With positive t, ideal unlimited-bandwidth tau->0 limit:', sp.limit(y,tau,0,dir='+'))
assert sp.limit(mag2,w,0)==1
assert sp.limit(mag2,w,sp.oo)==0
assert sp.limit(y,t,sp.oo)==1
assert sp.limit(y,tau,0,dir='+')==1
print('QUALITATIVE CHECK PASS: steady brightness retained but rapid spatial edges rounded.')
