from independent_circuits import *
gm=.01;ro=10000.;rd=500.;re=100.
g=s.symbols('g',positive=True);d,e,v=s.symbols('d e v');q=s.solve([d/rd+(d-e)/ro+gm*(v-e),e/re+(e-d)/ro-gm*(v-e)],[d,e]);av=s.simplify(q[d]/v)
out({'source':'from_the_past/md/2013-1_중간/Q4.md','1_mirror':'io=gm vid/2 +gm vid/2=gm vid; gain positive gm(ro2||ro4)','2_course_mirror':gm*ro/2,'2_full_mirror':mos_mirror(gm,1/ro,1/ro,gm),'3_diode':-gm/(gm+2/ro),'4_gmRe':gm*re,'4_full_linear':float(av),'4_no_ro':-rd/(1/gm+re),'4_cascode_Rout_separation_approx':-gm*(1/(1/rd+1/((1+gm*re)*ro)))/(1+gm*re),'note':'RSS/2=100ohm yields gmRe=1 -> cannot drop1. Full finite-ro gain -2.427184466; source -2.44 uses additional Rout separation approx; label clearly.'})

# Source -2.44 uses block approximation, author -2.43 uses direct finite-ro KCL. Both approach -2.5 at ro->infinity.
O=s.symbols('ro',positive=True);exact=-gm*rd*O/(O+rd+re*(1+gm*O));block=-gm*(1/(1/rd+1/((1+gm*re)*O)))/(1+gm*re)
print('limit exact/block ro->infinity=',s.limit(exact/block,O,s.oo));assert s.limit(exact/block,O,s.oo)==1
