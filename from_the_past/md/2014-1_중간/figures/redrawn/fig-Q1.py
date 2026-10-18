"""2014-1 중간 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos

GAP = 0.2       # 소자 라벨과 기호 사이 간격
L = 0.25        # 소자 사이 짧은 배선


def draw():
    d = new_drawing()
    # 한 세로줄 위→아래: V_DD T 기호, M4, M3, Vout 접속점, M2, M1, 접지
    d.add(elm.Vdd().at((0, 0)).scale(0.8).label(r"$V_{DD}$", "right", ofst=GAP))
    m4 = pmos(d, at=(0, 0), anchor="source", label=r"$M_\mathrm{4}$")
    gate_terminal(d, m4.gate, r"$V_\mathrm{b3}$")
    m3 = pmos(d, at=m4.drain, anchor="source", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Line().down().at(m3.drain).length(L)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(L))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b1}$")
    m1 = nmos(d, at=m2.source, anchor="drain", label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(m1.source).scale(0.8))
    return d
