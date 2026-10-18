# P10.45 independent: solve Eq.(10.147) = I_SS for dV = Vin1 - Vin2
import sympy as sp
k,Iss,x=sp.symbols('k I_SS x',positive=True)  # k = mu_n Cox W/L
eq=sp.Eq(sp.Rational(1,2)*k*x*sp.sqrt(4*Iss/k-x**2),Iss)
sols=sp.solve(eq,x)
print('solutions dV =',sols)
Vov_eq=sp.sqrt(Iss/k)
for s in sols:
    print('dV/Vov_equil =',sp.simplify(s/Vov_eq),'; dV - sqrt(2 Iss/k) =',sp.simplify(s-sp.sqrt(2*Iss/k)))
print('residual of eq at sqrt(2)Vov:',sp.simplify(eq.lhs.subs(x,sp.sqrt(2)*Vov_eq)-Iss))
