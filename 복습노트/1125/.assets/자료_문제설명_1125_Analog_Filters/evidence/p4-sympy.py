"""P4 (연습문제 12.32) 조정자 대조: 노턴 등가 I_N, R_N — explain-blind ↔ 설명 조각, 그리고 노턴 재결합이 식 12.171을 항등적으로 재현하는지 SymPy로 확인."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p3_common import *
G = g2*r2*RD*RM/(RF+RM+1/g1)
RN_b = r2 + par(RF,RM) + G
IN_b = (A_open/(1+T)).subs(RL,0)*Iin
RN_f = Ro*(1+T0)
IN_f = A0/(1+T0)*Iin
print('R_N blind - fragment:', sp.simplify(RN_b-RN_f))
print('I_N blind - fragment:', sp.simplify(IN_b-IN_f))
print('노턴 재결합 I_N R_N/(R_N+R_L) - A_I,closed I_in (식 12.171):', sp.simplify(IN_f*RN_f/(RN_f+RL) - A_open/(1+T)*Iin))
print('R_N에 R_L 없음:', RL not in RN_f.free_symbols and RL not in IN_f.free_symbols)
