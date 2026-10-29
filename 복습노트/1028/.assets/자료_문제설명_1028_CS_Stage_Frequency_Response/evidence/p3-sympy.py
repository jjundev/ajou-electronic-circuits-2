# p3: L -> 2L, same Vov, same I_D
import random
maxres=0
for _ in range(5):
    k=random.uniform(1e-4,1e-3); W=random.uniform(1e-6,1e-4); L=random.uniform(1e-7,1e-6); V=random.uniform(0.1,0.5)
    I=lambda W,L: 0.5*k*W/L*V**2
    fT=lambda W,L: (k*W/L*V)/(2/3*W*L)  # gm/Cgs per Cox normalisation (k=mu Cox, Cgs/Cox)
    W2=W*2
    rI=abs(I(W2,2*L)/I(W,L)-1)
    rf=fT(W2,2*L)/fT(W,L)
    gm_ratio=(k*W2/(2*L)*V)/(k*W/L*V)
    print(f"W'/W=2: I ratio-1={rI:.1e}, gm ratio={gm_ratio:.6f}, Cgs ratio={(W2*2*L)/(W*L):.3f}, fT ratio={rf:.6f}")
    maxres=max(maxres,rI,abs(rf-0.25))
print("max residual vs (W x2, fT x1/4):", maxres)
