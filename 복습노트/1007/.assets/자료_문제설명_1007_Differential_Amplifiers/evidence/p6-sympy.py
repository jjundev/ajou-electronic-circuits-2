from independent_circuits import *
gm=.001;rd=10000.;rss=50000.;ro=100000.
# M1/2 size doubling with fixed total tail makes current steering cutoff shrink sqrt2.
cm=pair(gm,ro,rss,rd,rd+100.);dm=pair(gm,ro,rss,rd,rd+100.,common=False)
x=s.symbols('x');target=30000.;ac=pair(gm,ro,rss,rd,rd+100.)
# Use symbolic exact 3-node nodal matrix for inverse mismatch.
a,b,p=s.symbols('a b p');q=s.solve([a/rd+(a-p)/ro+gm*(1-p),b/(rd+x)+(b-p)/ro+gm*(1-p),p/rss+(2*p-a-b)/ro-2*gm*(1-p)],[a,b,p]);dcm=s.factor(q[a]-q[b]);qd=s.solve([a/rd+(a-p)/ro+gm*(.5-p),b/(rd+x)+(b-p)/ro+gm*(-.5-p),p/rss+(2*p-a-b)/ro+2*gm*p],[a,b,p]);ddm=s.factor(qd[a]-qd[b]);sol=s.nsolve(-ddm/dcm-target,34)
out({'source':'from_the_past/md/2015-1_중간/Q4.md','1':'X; vdiff cutoff =sqrt(2 ISS/K), K doubled ->1/sqrt2','2_course':-gm*rd,'3_course':-rd/(2*rss),'4_course':100/(2*rss),'5_course':2*gm*rss*rd/target,'5_retained1_roignored':gm*rd*(1/gm+2*rss)/target,'5_fulllinear':float(sol),'full_cm':cm,'full_dm':dm,'note':'原문 ro1≫RD 명시없음; ro=10RD. 강의모델 -10과 완전 -9.1을 같은 근사 수준으로 표시하지 말 것.'})

# Approximation acceptance proof from independent two-node symmetric KCL, with finite input ro retained.
G,O,T,R,D=s.symbols('G O T R D',positive=True)
CM=-G*R*O/(R+O+2*T*(1+G*O))
LEAK=s.factor(-CM*D/(R*(1+R/O))) # first derivative of full unequal-load pair at D=0
CMlead=-R/(2*T);Llead=D/(2*T*(1+R/O))
print('Symmetric CM exact internal =',CM)
print('First-order leakage from full coupled KCL =',LEAK)
print('limit CM/CMlead for G->infinity:',s.limit(CM/CMlead,G,s.oo))
print('limit leakage/large-product leakage for G->infinity:',s.limit(LEAK/Llead,G,s.oo))
print('limit same-model CMRR/leading CMRR:',s.limit((G*R/(1+R/O)/LEAK)/(2*G*T*R/D),G,s.oo))
assert s.simplify(s.limit(CM/CMlead,G,s.oo)-1)==0
assert s.simplify(s.limit(LEAK/Llead,G,s.oo)-1)==0
