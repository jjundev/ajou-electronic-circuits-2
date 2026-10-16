import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I,k,V,t=s.symbols('I k V t',positive=True);ov=s.sqrt(I/k);print('baseline',V-t-ov);print('width2 delta',ov*(1-1/s.sqrt(2)));print('Iss2/tox2 delta',ov*(1-s.sqrt(2)))
print("Independent conclusion: tail VP=VCM-VTH-sqrt(Iss/k); width2 raises VP,Iss2 or tox2 lowers VP")
