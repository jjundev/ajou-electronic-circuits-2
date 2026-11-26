from sympy import symbols,Eq,solve,simplify
G,K,R,x,i=symbols('G K Rout Vtest Itest',positive=True)
# A series current sensor reads the load current = -Itest (Itest enters amplifier).
# Return voltage K*(-Itest), error=+K*Itest, so Gm responds in the forward direction.
z=solve(Eq(i,x/R-G*K*i),x)[0]/i
assert simplify(z-R*(1+G*K))==0
print('A voltage pickoff is parallel and cannot represent a series output-current sensor.')
print('With a correctly oriented ideal series current sample, Vtest/Itest =',z)
