from sympy import symbols, Eq, solve, simplify, factor, limit, oo

def check(left, right):
    assert simplify(left-right) == 0, (left,right)

# s = M1 source (input); x = M1 drain; o = output.
# g1,g2 stand for gm1,gm2; a,b,f stand for RD1,RD2,RF.
g1,g2,a,b,f = symbols("g1 g2 a b f", positive=True)
s,x,o,i,j = symbols("s x o i j")
# i injects into input, j injects into output.
eqs=[Eq(i, g1*s+(s-o)/f), Eq(x/a,g1*s), Eq(j,o/b+g2*x+(o-s)/f)]
sol = solve(eqs,(s,x,o),dict=True)[0]
Q=f+b+1/g1+g2*a*b
T=g2*a*b/f
# Open feedback resistor: no loading or return.
open_sol=solve([Eq(i,g1*s),Eq(x/a,g1*s),Eq(o/b,-g2*x)],(s,x,o),dict=True)[0]
R0 = -g2*a*b
check(open_sol[o]/i,R0)
z=factor(sol[o].subs(j,0)/i)
check(z,b*(1/g1-f*g2*a)/Q)
# An increase in s raises x and lowers the unloaded output, so return
# current (o-s)/f into the input has negative incremental slope.
return_slope=(open_sol[o]-open_sol[s]).diff(i)/f
assert return_slope.is_negative
# Unilateral teaching model: neglect RF loading and input-voltage term.
check(solve(Eq(o,R0*(i+o/f)),o)[0]/i, R0/(1+T))
print("a) Positive injected current raises s and x, depresses output; delta i_RF=(delta o-delta s)/RF opposes input in the intended large-RF regime.")
print("b) Open-loop transimpedance =", R0, "ohm")
print("c) Textbook large-RF transimpedance =",R0/(1+T),"ohm")
print("Direct nodal finite-RF check =", z,"ohm. Dropped resistances b and 1/g1 are small vs f; input-output feedthrough negligible when f*g1*g2*a >> 1.")
