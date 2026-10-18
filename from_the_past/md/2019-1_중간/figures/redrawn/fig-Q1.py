"""2019-1 중간 Q1 — 기준: Q1.md '회로 — Fig Q1(a)', '회로 — Fig Q1(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12        # 소자 사이 짧은 배선
GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.6    # 두 패널 레일 높이
CAP_Y = -0.35   # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    return d.add(e.anchor(anchor).at(at))


def tag(d, xy, text, halign, valign="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=halign, valign=valign))


def panel_a(d, x0):
    x5, xs = x0, x0 + 3.4          # M5 줄, 오른쪽 세로줄
    rail(d, (x5 - 0.3, RAIL_Y), (xs + 0.3, RAIL_Y))
    tag(d, (xs + 0.4, RAIL_Y + 0.05), r"$V_{DD}$", "left")
    # M5: 왼쪽 위 pmos, 소스가 레일
    m5 = pmos(d, at=(x5, RAIL_Y), anchor="source")
    gate_terminal(d, m5.gate, r"$V_\mathrm{in}$", open_=True)
    tag(d, (x5 - 0.3, m5.drain.y - 0.3), r"$M_\mathrm{5}$", "right", "top")
    # 오른쪽 세로줄 위→아래: M4, M3, Vout 접속점, M2, n1 접속점, M1, 접지
    m4 = pmos(d, at=(xs, RAIL_Y), anchor="source", label=r"$M_\mathrm{4}$")
    gate_terminal(d, m4.gate, r"$V_\mathrm{b4}$")
    m3 = pmos(d, at=m4.drain, anchor="source", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b3}$")
    d.add(elm.Line().down().at(m3.drain).length(0.3)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(L))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Line().down().at(m2.source).length(0.25)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(L))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M5 드레인 → n1 높이 → 오른쪽 n1 접속점
    d.add(elm.Line().down().at(m5.drain).toy(n1.center.y))
    d.add(elm.Line().right().tox(xs))
    caption(d, (x0 + 1.6, CAP_Y), "(a)")


def half_b(d, x, left):
    """(b) 한쪽 세로줄 위→아래: 전류원, 출력 접속점, Q3/Q4, Q1/Q2, 이미터 접속점, 전류원, 접지."""
    top = d.add(elm.SourceI().down().at((x, RAIL_Y)).length(1.3).scale(0.6))
    d.add(elm.Line().down().at(top.end).length(0.2)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(1.1))
    qc = bjt(d, elm.BjtNpn, d.here, "collector")
    d.add(elm.Line().down().at(qc.emitter).length(0.45))
    qi = bjt(d, elm.BjtNpn, d.here, "collector", mirror=not left)
    d.add(elm.Line().down().at(qi.emitter).length(0.3)); ne = dot(d)
    bot = d.add(elm.SourceI().down().at(ne.center).length(1.5).scale(0.6))
    d.add(elm.Ground().at(bot.end).scale(0.8))
    return out, qc, qi, ne


def panel_b(d, x0):
    xl, xr = x0, x0 + 3.9
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, RAIL_Y), (xr + 0.35, RAIL_Y))
    tag(d, (xr + 0.45, RAIL_Y + 0.05), r"$V_{CC}$", "left")
    out1, q3, q1, n3 = half_b(d, xl, True)
    out2, q4, q2, n4 = half_b(d, xr, False)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.8)); dot(d, open_=True)
    tag(d, (xm, out1.center.y), r"$V_\mathrm{out}$", "center")
    # V_b → Q3 베이스, 같은 높이로 Q3 막대를 지나 Q4 베이스 (베이스 공통선)
    gate_terminal(d, q3.base, r"$V_\mathrm{b}$")
    d.add(elm.Line().at(q3.base).to(q4.base))
    tag(d, (xl - 0.3, q3.collector.y + 0.05), r"$Q_\mathrm{3}$", "right", "bottom")
    tag(d, (xr - 0.3, q4.collector.y + 0.05), r"$Q_\mathrm{4}$", "right", "bottom")
    tag(d, (xl + 0.3, q1.center.y - 0.15), r"$Q_\mathrm{1}$", "left")
    tag(d, (xr - 0.3, q2.center.y - 0.15), r"$Q_\mathrm{2}$", "right")
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{S}$", "bottom", ofst=GAP))
    caption(d, (xm, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 1.6)
    panel_b(d, 11.4)
    return d
