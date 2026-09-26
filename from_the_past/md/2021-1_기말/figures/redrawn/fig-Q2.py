"""2021-1 기말 Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing

GAP = 0.2           # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭


def draw():
    d = new_drawing()
    # 한 세로줄 위→아래: V_CC T 기호, Q2 (pnp), Vout 접속점, Q1 (npn), 접지
    top = 7.0
    d.add(elm.Vdd().at((0, top)).scale(0.8).label(VCC, "right", ofst=GAP))
    d.add(elm.Line().down().at((0, top)).length(1.0))
    q2 = d.add(elm.BjtPnp().right().anchor("emitter").at(d.here).label(r"$Q_\mathrm{2}$", "right"))
    # V_b 점 단자: 원본처럼 게이트 가로선이 길다
    d.add(elm.Line().left().at(q2.base).length(0.6))
    gate_terminal(d, d.here, r"$V_\mathrm{b}$")
    d.add(elm.Line().down().at(q2.collector).length(1.1)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.6))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(1.1))
    q1 = d.add(elm.BjtNpn().right().anchor("collector").at(d.here).label(r"$Q_\mathrm{1}$", "right"))
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    # Q1 베이스(n1) ← 가로 R_S ← V_in 원
    d.add(elm.Line().left().at(q1.base).length(1.4))
    d.add(Resistor().left().length(1.2).label(r"$R_\mathrm{S}$", "top", ofst=GAP))
    d.add(elm.Line().left().length(0.7))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{in}$", "left", ofst=GAP))
    return d
