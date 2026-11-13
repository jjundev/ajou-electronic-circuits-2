# p2 (X12.03) independent: break loop at subtractor (-) input (X_F path), X=0
import sympy as sp
A1, K, Vt = sp.symbols('A1 K V_test')
Xin = 0
# M = subtractor '-' input side receives V_test; N = feedback network output side
e = Xin - Vt            # subtractor output
Yb = A1*e               # A1 output
VN = K*Yb               # K output observed at N
print("V_N =", sp.simplify(VN))
LG = sp.simplify(-VN/Vt)
print("loop gain = -V_N/V_test =", LG)
print("check LG - K*A1 =", sp.simplify(LG - K*A1))
# compare with breaking at A1 input (p1): same loop gain regardless of break point
VN1 = Xin - K*A1*Vt
print("break-at-A1-input LG =", sp.simplify(-VN1/Vt), " diff =", sp.simplify(-VN1/Vt - LG))
# note: breaking the '+' (X) input does not cut the loop -> not a valid break point
