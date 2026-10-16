import sympy as s
v_i,v_o=s.symbols('v_in v_out')
Cgs1,Cgd1,Cdb1,Csb1,Cgs2,Cgd2,Cdb2,Csb2=s.symbols('C_gs1 C_gd1 C_db1 C_sb1 C_gs2 C_gd2 C_db2 C_sb2')
# Charge energy identifies which physical device capacitors remain between distinct AC nodes.
caps=[('Cgs1',Cgs1,v_i,0),('Cgd1',Cgd1,v_i,v_o),('Cdb1',Cdb1,v_o,0),('Csb1',Csb1,0,0),('Cgs2',Cgs2,v_o,0),('Cgd2',Cgd2,v_o,v_o),('Cdb2',Cdb2,v_o,0),('Csb2',Csb2,0,0)]
energy=s.expand(sum(c*(a-b)**2/2 for _,c,a,b in caps))
active=[name for name,c,a,b in caps if s.simplify(a-b)!=0]
shorted=[name for name,c,a,b in caps if s.simplify(a-b)==0]
print('capacitor energy:',energy)
print('active:',active)
print('zero AC voltage:',shorted)
assert active==['Cgs1','Cgd1','Cdb1','Cgs2','Cdb2']
