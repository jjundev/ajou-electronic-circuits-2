import sympy as s
vi,vx,vo=s.symbols('v_in v_x v_out')
Cpi1,Cmu1,Ccs1,Cpi2,Cmu2,Ccs2=s.symbols('C_pi1 C_mu1 C_cs1 C_pi2 C_mu2 C_cs2')
caps=[('Cpi1',Cpi1,vi,0),('Cmu1',Cmu1,vi,vx),('Ccs1',Ccs1,vx,0),('Cpi2',Cpi2,0,vx),('Cmu2',Cmu2,0,vo),('Ccs2',Ccs2,vo,0)]
energy=s.expand(sum(c*(a-b)**2/2 for _,c,a,b in caps))
print('node mapping: Q1 base=in emitter=ground collector=x; Q2 base=AC ground emitter=x collector=out')
for n,c,a,b in caps: print(n,':',a,'<->',b)
print('capacitor energy:',energy)
assert s.diff(energy,vi,vx)==-Cmu1
assert s.diff(energy,vx,vo)==0
