from sympy import symbols, Eq, solve, simplify, factor, limit, oo

def check(left, right):
    assert simplify(left-right) == 0, (left,right)

# Independent proof by equations. Positive test current ix enters DUT;
# terminal output current io is positive FROM the DUT. gm*va delivers
# current to output node where R is connected in parallel.
R,gm,k = symbols("R gm k",positive=True)
v,va,ix,io=symbols("v va ix io")
z=solve([Eq(io,-ix),Eq(va,-k*io),Eq(ix,v/R-gm*va)],(v,va,io),dict=True)[0][v]/ix
check(z,R*(1+gm*k))
print("Fig. 12.45 wires K in parallel from the output node; this supplies node voltage, and does not define/decode the net output current.")
print("For current-output, voltage-input feedback use a series current sensor in the load/test path, after the Rout split; retain Rout as a shunt to ground.")
print("Proof with nominal output current pointing out: io=-Ix, VA=-K io, Ix=Vx/Rout-Gm VA. Therefore Vx/Ix=Rout(1+Gm K). K here has impedance units and is taken positive for negative feedback.")
