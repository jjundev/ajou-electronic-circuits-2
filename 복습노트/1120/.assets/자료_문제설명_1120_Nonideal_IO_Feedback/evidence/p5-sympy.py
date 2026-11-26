import sympy as s

g1, g2, go1, go2, D1, D2, R1, R2 = s.symbols('gm1 gm2 go1 go2 RD1 RD2 R1 R2', positive=True)
u, x, v, o, j = s.symbols('vin x vs vo i_test')
d1 = g1*(u-v)+go1*(x-v)
laws = [x/D1+d1, v/R2+(v-o)/R1-d1, o/D2+go2*o+g2*x+(o-v)/R1-j]
sol = s.solve(laws,(x,v,o),simplify=False)
K = R2/(R1+R2)
Rth = R1*R2/(R1+R2)
RL = 1/(1/D2+go2+1/(R1+R2))
D = 1+go1*D1+(g1+go1)*Rth
P = g1/D
Q = K*(g1+go1)/D
B = g2*D1
a0 = B*P*RL
T = B*Q*RL
a_exact = (B+K)*P*RL/(1+(B+K)*Q*RL)
ro_exact = RL/(1+(B+K)*Q*RL)
a_replica = a0/(1+T)
ro_replica = RL/(1+T)
assert s.factor(sol[o].diff(u)-a_exact) == 0
assert s.factor(sol[o].diff(j)-ro_exact) == 0
for exact, replica in [(a_exact,a_replica),(ro_exact,ro_replica)]:
    assert s.factor(s.limit(s.factor(exact/replica),g2,s.oo)-1) == 0
assert s.factor(a0.subs(go1,0)-g1*g2*D1*RL/(1+g1*Rth)) == 0
assert s.factor(T.subs(go1,0)-K*a0.subs(go1,0)) == 0
print('Rth=R1||R2; R_L=RD2||ro2||(R1+R2); K=R2/(R1+R2)')
print('D=1+go1*RD1+(gm1+go1)*Rth; P=gm1/D; Q=K*(gm1+go1)/D; B=gm2*RD1')
print('Open replicas: A0=B*P*R_L; Rin0=infinity; Rout0=R_L')
print('Closed replicas: A=A0/(1+B*Q*R_L); Rin=infinity; Rout=R_L/(1+B*Q*R_L)')
print('Original closed circuit: replace B by B+K in A and Rout.')
print('Direct +K path is due to M1 source current contributing to the output through R1.')
print('At lambda1=0, P=gm1/(1+gm1*Rth), Q=K*P, so replica loop gain=K*A0.')
print('At lambda2=0, remove ro2 from R_L.')
