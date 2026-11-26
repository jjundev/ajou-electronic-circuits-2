from sympy import symbols, Eq, solve, simplify, factor, limit, oo

def check(left, right):
    assert simplify(left-right) == 0, (left,right)

# Circuit has RD--M1--M2 stack. s = common M1 source / M2 drain input;
# h = M2 gate, o = M1 drain output. i,j are injected port currents.
g1,g2,d,r1,r2 = symbols("g1 g2 d r1 r2", positive=True)
s,h,o,i,j = symbols("s h o i j")
eqs=[Eq(i,g1*s+g2*h), Eq(j,o/d+(o-h)/r1-g1*s), Eq((o-h)/r1,h/r2)]
sol=solve(eqs,(s,h,o),dict=True)[0]
beta=r2/(r1+r2)
D=1/(1/d+1/(r1+r2))
T=D*g2*beta
check(sol[o].subs(j,0)/i,D/(1+T))
check(sol[s].subs(j,0)/i,1/(g1*(1+T)))
check(sol[o].subs(i,0)/j,D/(1+T))
print("beta=R2/(R1+R2), D=RD || (R1+R2), T=gm2*beta*D.")
print("Closed-loop Vout/Iin = D/(1+T) [ohm] and positive.")
print("Input impedance = 1/[gm1*(1+T)] [ohm].")
print("Output impedance with Iin=0 open = D/(1+T) [ohm].")
print("For R1+R2 >> RD take D approximately RD throughout; beta is retained.")
