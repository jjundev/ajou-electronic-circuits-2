"""Independent verification of P12.47."""
import sympy as s

Yin, Yout, h, f = s.symbols('Yin Yout h f', real=True, nonzero=True)
u, o, i_in, i_out = s.symbols('v_in v_out i_in i_out')

g1, g2, go1, go2, RD1, Raux = s.symbols('gm1 gm2 go1 go2 RD1 R_aux',positive=True)
x = s.symbols('v_x')
# Drain of common-gate M1 drives the insulated gate of M2.
xsol = s.solve(x/RD1 + go1*(x-u)-g1*u,x)[0]
g_input = s.factor((g1*u+go1*(u-xsol))/u)
assert s.factor(xsol-RD1*g_input*u) == 0

# M2 is NMOS common-source with ideal bias current source at output (AC open).
g_output = go2
h_actual = g2*xsol/u

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

Rf, R1, R2 = s.symbols('R_F R_1 R_2',positive=True)
z = s.symbols('v_tap')
tap = s.solve((z-u)/Rf+(z-o)/R1+z/R2,z)[0]
i_1 = s.factor((u-tap)/Rf)
i_2 = s.factor((o-tap)/R1)
Y11 = 1/(Rf+R1*R2/(R1+R2))
Y22 = 1/(R1+Rf*R2/(Rf+R2))
feedback = R2/(Rf*R1+Rf*R2+R1*R2)
assert s.factor(i_1-(Y11*u-feedback*o)) == 0
assert s.factor(i_2-(Y22*o-feedback*u)) == 0
yin, yout = g_input+Y11,g_output+Y22
assert s.factor(g_input*u+i_1-(Yin*u-f*o).subs({Yin:yin,f:feedback})) == 0
assert s.factor(g_output*o+h_actual*u+i_2-
                ((h-f)*u+Yout*o).subs({h:h_actual,Yout:yout,f:feedback})) == 0
assert s.limit(Y11,R2,s.oo) == 1/(Rf+R1)
assert s.limit(Y22,R2,s.oo) == 1/(Rf+R1)
assert s.limit(feedback,R2,s.oo) == 1/(Rf+R1)
assert s.limit(feedback,R2,0) == 0
assert s.limit(Y11,R2,0) == 1/Rf
assert s.limit(Y22,R2,0) == 1/R1
print('G_input=',s.factor(g_input),'; G_output=',g_output,'; h=',s.factor(h_actual))
print('Yin=G_input+1/(RF+(R1||R2)); Yout=go2+1/(R1+(RF||R2)).')
print('f=R2/(RF*R1+RF*R2+R1*R2).')
print('R2 -> infinity reduces to RF+R1 series feedback; R2 -> 0 breaks return and grounds tap.')
