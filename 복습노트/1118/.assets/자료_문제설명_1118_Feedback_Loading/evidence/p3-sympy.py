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
zin=factor(sol[s].subs(j,0)/i)
check(zin,(f+b)/(g1*Q))
zin_text=1/(g1*(1+T))
# Compare normalized numerator/denominator exactly; both correction terms
# are small relative to unity/the retained denominator when f>>b,1/g1.
check(zin, (1/g1)*(1+b/f)/(1+T+(b+1/g1)/f))
print("Apply input test current, output test injection zero. Exact Zin =",zin,"ohm.")
print("With RF >> RD2, 1/gm1: Zin ~",zin_text,"ohm. gm1 is the input transistor's transconductance.")
