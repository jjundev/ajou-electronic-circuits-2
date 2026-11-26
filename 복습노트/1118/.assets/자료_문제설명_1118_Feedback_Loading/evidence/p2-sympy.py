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
s_per_i=sol[s].subs(j,0)/i
o_per_i=sol[o].subs(j,0)/i
check(limit(s_per_i,a,oo),0)
check(limit(o_per_i,a,oo),-f)
check(limit(g1*s_per_i,a,oo),0)
check(limit((s_per_i-o_per_i)/f,a,oo),1)
print("RD1 -> infinity: vout/iin = -RF, vs/iin -> 0, gm1*vs/iin -> 0, (vs-vout)/(RF*iin) -> 1.")
print("Small-signal virtual ground at M1 source. For a fixed input, current is conveyed from this node through RF to output.")
