"""Independent verification of P12.49."""
import sympy as s

Yin, Yout, h, f = s.symbols('Yin Yout h f', real=True, nonzero=True)
u, o, i_in, i_out = s.symbols('v_in v_out i_in i_out')

gm, rp, ro, RC = s.symbols('gm r_pi r_o RC',positive=True)
# Base is the input, emitter is grounded, collector is the output. VA < infinity.
g_input = 1/rp
g_output = 1/RC+1/ro
h_actual = gm

# Yin/Yout include the feedback network's short-circuit diagonal admittances.
# h is the forward dependent current leaving output per input voltage.
# f*vo is the feedback-network input current toward the summing node at vi=0.
# The reciprocal forward term -f*vi at output is present in the physical circuit.
trial = s.solve([Yin*u-f*o-i_in, (h-f)*u+Yout*o-i_out],(u,o))
det = Yin*Yout+f*(h-f)
assert s.factor(trial[o].diff(i_in)-(f-h)/det) == 0
assert s.factor(trial[u].diff(i_in)-Yout/det) == 0
assert s.factor(trial[o].diff(i_out)-Yin/det) == 0

R0 = -h/(Yin*Yout)
Rin0, Rout0 = 1/Yin, 1/Yout
T = -f*R0
replica = s.solve([Yin*u-f*o-i_in,h*u+Yout*o-i_out],(u,o))
assert s.factor(replica[o].diff(i_in)-R0/(1+T)) == 0
assert s.factor(replica[u].diff(i_in)-Rin0/(1+T)) == 0
assert s.factor(replica[o].diff(i_out)-Rout0/(1+T)) == 0
probes = [(o,i_in),(u,i_in),(o,i_out)]
for measured, injection in probes:
    exact_result = trial[measured].diff(injection)
    replica_result = replica[measured].diff(injection)
    assert s.factor(s.limit(exact_result-replica_result,f,0)) == 0
print('Loaded replica: R0 =',R0,'; Rin0 =',Rin0,'; Rout0 =',Rout0)
print('Return convention: i_in+i_f, i_f=f*vo at vi=0; f>0; T=-f*R0.')
print('Equivalent subtracting convention: i_in-K*vo with K=-f.')
print('Loaded replica closed: R=R0/(1+T); Rin=Rin0/(1+T); Rout=Rout0/(1+T).')
print('Exact closed physical circuit: replace h by h-f in the above expressions.')
print('Exact D = Yin*Yout+f*(h-f); R=(f-h)/D; Rin=Yout/D; Rout=Yin/D.')
print('Replica drops reciprocal forward feedthrough; R comparison requires |f/h| << 1.')
print('Close to D=0, also check that the determinant change f**2 is negligible.')

Rf = s.symbols('R_F',positive=True)
feedback = 1/Rf
yin, yout = g_input+feedback, g_output+feedback
physical_input = g_input*u+(u-o)/Rf
physical_output = g_output*o+h_actual*u+(o-u)/Rf
assert s.factor(physical_input-(Yin*u-f*o).subs({Yin:yin,f:feedback})) == 0
assert s.factor(physical_output-((h-f)*u+Yout*o).subs({h:h_actual,Yout:yout,f:feedback})) == 0
print('f=1/R_F; Yin=g_input+1/R_F; Yout=g_output+1/R_F.')
for label, value in [('g_input',g_input),('g_output',g_output),('h',h_actual)]:
    print(label,'=',s.factor(value))

print('Open transresistance = -gm*(r_pi||RF)*(RC||ro||RF).')
print('Open input = r_pi||RF; open output = RC||ro||RF.')
print('Exact full circuit high-gm limit: negative transresistance -> -RF.')
assert s.limit(((f-h)/det).subs(h,gm),gm,s.oo) == -1/f
