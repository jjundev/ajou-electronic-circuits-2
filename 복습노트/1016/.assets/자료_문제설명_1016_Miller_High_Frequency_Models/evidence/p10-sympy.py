import sympy as s
vi,vx,vo,z=s.symbols('v_in v_x v_out s')
gm1,gm2,rpi1,rpi2,ro1,ro2,Rc=s.symbols('g_m1 g_m2 r_pi1 r_pi2 r_O1 r_O2 R_C',positive=True)
Cpi1,Cmu1,Ccs1,Cpi2,Cmu2,Ccs2=s.symbols('C_pi1 C_mu1 C_cs1 C_pi2 C_mu2 C_cs2')
# Q2 v_pi2 = v_b2-v_e2 = -vx. Collector->emitter controlled current = -gm2*vx.
vpi1=vi; vpi2=-vx
q1_collector_to_emitter=gm1*vpi1
q2_collector_to_emitter=gm2*vpi2
kin=vi/rpi1+z*(Cpi1*vi+Cmu1*(vi-vx))
kx=vx/ro1+vx/rpi2+(vx-vo)/ro2+q1_collector_to_emitter-q2_collector_to_emitter+z*(Cmu1*(vx-vi)+(Ccs1+Cpi2)*vx)
kout=vo/Rc+(vo-vx)/ro2+q2_collector_to_emitter+z*(Cmu2+Ccs2)*vo
print('Q1 vpi, collector->emitter gm current:',vpi1,q1_collector_to_emitter)
print('Q2 vpi, collector->emitter gm current:',vpi2,q2_collector_to_emitter)
print('ro1=x-ground; ro2=out-x; rpi1=in-ground; rpi2=x-ground; RC=out-ground')
print('KCL in:',s.expand(kin))
print('KCL x:',s.expand(kx))
print('KCL out:',s.expand(kout))
assert s.diff(kx,gm2)==vx
assert s.diff(kout,gm2)==-vx
