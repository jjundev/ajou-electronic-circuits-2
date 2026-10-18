# P9.48 (Fig. 9.70): I_copy error with base currents (bipolar mirrors, VA=inf)
import sympy as sp
I, b = sp.symbols('I_REF beta', positive=True)
Ic1, Ic2, Ic3, Ic4 = sp.symbols('I_C1 I_C2 I_C3 I_C4', positive=True)

def solve_case(nA1, nA2, pA3, pA4, label):
    # npn: Q1 diode (area nA1), Q2 (nA2); Ic2 = (nA2/nA1) Ic1 (same VBE)
    # KCL at Q1 collector/base node: I_REF = Ic1 + Ic1/b + Ic2/b
    # pnp: Q3 diode (pA3), Q4 (pA4); Ic4 = (pA4/pA3) Ic3
    # KCL at Q3 collector/base node: Ic2 = Ic3 + Ic3/b + Ic4/b
    eqs = [sp.Eq(Ic2, sp.Rational(nA2, nA1)*Ic1),
           sp.Eq(I, Ic1 + Ic1/b + Ic2/b),
           sp.Eq(Ic4, sp.Rational(pA4, pA3)*Ic3),
           sp.Eq(Ic2, Ic3 + Ic3/b + Ic4/b)]
    s = sp.solve(eqs, [Ic1, Ic2, Ic3, Ic4], dict=True)[0]
    Icopy = sp.factor(sp.simplify(s[Ic4]))
    ideal = sp.Rational(nA2, nA1)*sp.Rational(pA4, pA3)*I
    err = sp.factor(sp.simplify(ideal - Icopy))
    rel = sp.factor(sp.simplify(err/ideal))
    print(f"[{label}] I_copy = {Icopy}")
    print(f"[{label}] ideal I_copy = {ideal}")
    print(f"[{label}] error (ideal - actual) = {err}")
    print(f"[{label}] relative error = {rel}")
    lead = sp.limit(rel*b, b, sp.oo)
    print(f"[{label}] large-beta: relative error ~ {lead}/beta ; abs error ~ {sp.simplify(lead*ideal)}/beta")
    print(f"[{label}] check beta->oo I_copy -> {sp.limit(Icopy, b, sp.oo)}")
    print(f"[{label}] beta=100: I_copy/I_REF = {sp.N(Icopy.subs(b,100)/I, 6)}, rel err = {sp.N(rel.subs(b,100), 6)}")
    return Icopy, err

Ia, ea = solve_case(1, 1, 1, 1, 'a')
Ib, eb = solve_case(3, 2, 5, 9, 'b')
# cross-check closed forms
assert sp.simplify(Ia - I*b**2/(b+2)**2) == 0
assert sp.simplify(Ib - 18*b**2*I/((3*b+5)*(5*b+14))) == 0
print("ANSWER p6:main (a): I_copy = I_REF*beta^2/(beta+2)^2, error = I_REF*4(beta+1)/(beta+2)^2 ~ 4 I_REF/beta")
print("ANSWER p6:main (b): I_copy = 18 beta^2 I_REF/((3beta+5)(5beta+14)), error = (6/5)I_REF - I_copy ~ (6/5)(5/3+14/5)/beta I_REF = 5.36 I_REF/beta")
