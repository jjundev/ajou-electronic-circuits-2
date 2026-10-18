# P10.35 independent: tail node V_P = V_CM - V_TH - Vov, each device carries I_SS/2
import sympy as sp
mu,Cox,W,L,Iss,VCM,VTH,Vov=sp.symbols('mu C_ox W L I_SS V_CM V_TH V_ov',positive=True)
vov=sp.solve(sp.Eq(Iss/2,sp.Rational(1,2)*mu*Cox*W/L*Vov**2),Vov)[0]
VP=VCM-VTH-vov
print('Vov =',vov,'; V_P =',VP)
def dVP(sub):
    return sp.simplify(VP.subs(sub,simultaneous=True)-VP)
da=dVP({W:2*W}); db=dVP({Iss:2*Iss}); dc=dVP({Cox:Cox/2})
print('(a) W->2W : dV_P =',da,'= Vov*(1-1/sqrt2):',sp.simplify(da-vov*(1-1/sp.sqrt(2))))
print('(b) Iss->2Iss: dV_P =',db,'= -(sqrt2-1)Vov:',sp.simplify(db+(sp.sqrt(2)-1)*vov))
print('(c) tox->2tox (Cox->Cox/2): dV_P =',dc,'= -(sqrt2-1)Vov:',sp.simplify(dc+(sp.sqrt(2)-1)*vov))
print('signs: a>0 rises, b<0 falls, c<0 falls (V_TH held fixed; a thicker oxide also raises |V_TH| which lowers V_P further)')
