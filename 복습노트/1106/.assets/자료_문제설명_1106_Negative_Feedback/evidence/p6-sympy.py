# p6 (Ex 12.2) verify-B: why Y/X -> 1+R1/R2 when K*A1 >> 1  (method: proof, qualitative + limit)
import sympy as sp
A1,R1,R2,X=sp.symbols('A1 R1 R2 X',positive=True)
K=R2/(R1+R2)
G=A1/(1+K*A1)
print("Y/X =",G," = 1/(K + 1/A1)")
print("limit A1->oo :",sp.simplify(sp.limit(G,A1,sp.oo)),"= 1/K = 1+R1/R2")
print("relative error 1 - (Y/X)/(1/K) =",sp.simplify(1-G*K),"= 1/(1+K A1) -> 0")
E=X/(1+K*A1)
print("E = X - X_F =",E," -> limit",sp.limit(E,A1,sp.oo))
print("Argument: E->0 so X_F ~= X (good replica). X_F = K*Y fixed by divider -> Y = X/K = (1+R1/R2) X.")
print("Gain set only by resistor ratio, insensitive to A1 (desensitization).")
for a in [10,100,1000,10**4]:
    print(" A1=%6d K=1/8: Y/X=%.4f (1/K=8)"%(a,float(G.subs({A1:a,R1:7,R2:1}))))
