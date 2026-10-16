import sympy as s
vi,vo,z=s.symbols('v_in v_out s')
gm1,gm2,ro1,ro2=s.symbols('g_m1 g_m2 r_O1 r_O2',positive=True)
Cgs1,Cgd1,Cdb1,Cgs2,Cdb2=s.symbols('C_gs1 C_gd1 C_db1 C_gs2 C_db2')
# PMOS source is AC ground: v_sg2 = -vo. Its source-to-drain current is gm2*(-vo),
# hence incremental current leaving output toward ground is +gm2*vo.
vsg2=-vo
i_pmos_source_to_drain=gm2*vsg2
i_pmos_out_to_ground=-i_pmos_source_to_drain
i_nmos_out_to_ground=gm1*vi
kcl_out=s.expand(vo/ro1+vo/ro2+i_pmos_out_to_ground+i_nmos_out_to_ground+z*((Cdb1+Cgs2+Cdb2)*vo+Cgd1*(vo-vi)))
kcl_in=s.expand(z*(Cgs1*vi+Cgd1*(vi-vo)))
H=s.factor(s.solve(kcl_out,vo)[0]/vi)
print('M2 control v_sg2:',vsg2)
print('M1 drain->source current:',i_nmos_out_to_ground)
print('M2 output->AC-ground current:',i_pmos_out_to_ground)
print('KCL input:',kcl_in)
print('KCL output:',kcl_out)
print('vo/vi for ideal voltage drive:',H)
assert s.simplify(i_pmos_out_to_ground-gm2*vo)==0
