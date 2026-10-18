import sympy as sp
I, Iref, b = sp.symbols('I_C_REF I_REF beta', positive=True)

def mirror(label, Aref, outs):
    # outs: list of (name, area); Ic_k = (A_k/Aref)*Ic_ref (same VBE, exponential model)
    Ics = {n: sp.Rational(A, Aref)*I for n, A in outs}
    kcl = sp.Eq(Iref, I + I/b + sum(Ic/b for Ic in Ics.values()))
    Isol = sp.solve(kcl, I)[0]
    print(f"--- ({label}) Q_REF area {Aref}A_E, outputs {outs}")
    for n, A in outs:
        Ic = sp.simplify(Ics[n].subs(I, Isol))
        nom = sp.Rational(A, Aref)*Iref
        err = sp.simplify(Ic/nom - 1)
        print(f"({label}) {n} = {sp.factor(Ic)} ; nominal = {nom}")
        print(f"({label}) {n} normalized error = {sp.factor(err)} ; leading order (beta->oo) = {sp.limit(err*b, b, sp.oo)}/beta")
        print(f"({label}) {n} check beta=100: Icopy/I_REF = {sp.N(Ic.subs(b,100)/Iref,6)}, error = {sp.N(err.subs(b,100),6)}")

mirror('a', 1, [('I_copy', 5)])
mirror('b', 5, [('I_copy', 1)])
mirror('c', 2, [('I_copy', 3), ('I_2', 5)])
