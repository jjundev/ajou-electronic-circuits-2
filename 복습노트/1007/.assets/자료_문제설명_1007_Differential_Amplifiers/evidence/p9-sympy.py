from independent_circuits import *
# 2019-1 Q4; author fragments not read. Actual source figure: PMOS M5/M3 and M6/M4 are upper cascodes; M7 is simple NMOS tail.
g,ro,rs=s.symbols('gm ro RS',positive=True);d,e,v,x,it=s.symbols('d e v x it')
# Upper common-gate cascode test: upper PMOS ro5 at source e to ACground, lower ro3 d-e, controlled source sign is gm*(0-e) in drain->source convention.
q=s.solve([(x-e)/ro-g*e-it,e/ro+(e-x)/ro+g*e],[x,e]);rup=s.simplify(q[x]/it)
# CM half: 2rO7 as RS, upper cascode load Rup, input rO1 from drain to moving source.
qh=s.solve([d/rup+(d-e)/ro+g*(v-e),e/rs+(e-d)/ro-g*(v-e)],[d,e]);acm=s.factor(qh[d]/v)
adm=s.factor(-g/(1/ro+1/rup))
print('exact upper cascode internal:',rup)
print('exact CM half KCL:',acm)
print('exact DM half:',adm)
# Here inputro and cascode per-device ro all10000, gm.01, tailro5000 -> RS10000.
vals={g:.01,ro:10000.,rs:10000.}
out({'source':'from_the_past/md/2019-1_중간/Q4.md','bias':{'ID1_6':.001,'ID7':.002,'gm1_6':.01,'gm7':.02,'ro1_6':10000.,'ro7':5000.},'1_course':-.01/(1/10000+1/1000000),'1_exact_linear':float(adm.subs(vals)),'2_course':-(1/(1/1000000+1/1000000))/10000,'2_exact_linear':float(acm.subs(vals)),'CM_differential_output':0,'CM_half_reason':'두입력이같아두소스동일; 테일ro7을2ro7둘의병렬로분할. PMOS상부큰Rup에대해입력ro1는소스움직임으로커져Rdn≈gm1ro1*2ro7이고Rup와비슷하다. 소스는AC접지가아니다.','source_figure':'from_the_past/md/2019-1_중간/figures/fig-Q4.png'})
k=s.symbols('k',positive=True)
# With RS=ro and intrinsic gmro=k, relative error in source course expression tends 0.
print('limit exactCM/courseCM at gmro infinity:',s.limit(s.simplify(acm.subs(rs,ro)/(-g*ro/2)).subs(g,k/ro),k,s.oo))
print('limit exactDM/courseDM at gmro infinity:',s.limit(s.simplify(adm/(-g/(1/ro+1/(g*ro**2)))) .subs(g,k/ro),k,s.oo))
