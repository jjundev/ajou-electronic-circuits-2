# p1 (E12.03) independent: break loop at A1 input, X=0
import sympy as sp
A1, K, Vt, X = sp.symbols('A1 K V_test X')
# closed-loop sanity: Y = A1*(X - K*Y)
Y = sp.symbols('Y')
Ycl = sp.solve(sp.Eq(Y, A1*(X - K*Y)), Y)[0]
print("closed-loop Y/X =", sp.simplify(Ycl/X))
# broken loop: M = A1 input side gets V_test; N = subtractor output side
Xin = 0
Yb = A1*Vt              # A1 output
XF = K*Yb               # feedback network output
VN = Xin - XF           # subtractor output (N)
print("V_N =", sp.simplify(VN))
LG = sp.simplify(-VN/Vt)
print("loop gain = -V_N/V_test =", LG)
print("check LG - K*A1 =", sp.simplify(LG - K*A1))
# consistency: closed-loop = A1/(1+LG)
print("check Y/X - A1/(1+LG) =", sp.simplify(Ycl/X - A1/(1+LG)))
