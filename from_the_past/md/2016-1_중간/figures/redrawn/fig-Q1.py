"""2016-1 중간 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import Resistor, dot, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 12.0   # V_DD 레일 높이
DROP = 0.4      # 레일에서 pmos 소스까지 세로선


def line_terminal(d, at, label, length, right=False):
    """게이트에서 가로선을 긋고 선 끝에 라벨만 단다 (원본은 점·원 없는 선 끝)."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    x, y = d.here
    d.add(elm.Label().right().at((x + 0.1 if right else x - 0.25, y))
          .label(label, halign="left" if right else "right"))


def draw():
    d = new_drawing()
    xl, x5, x6 = 3.3, 11.0, 14.6     # M7·M1 줄, M5·M3 줄, M6·M4 줄
    xg, xn2, xref = 5.2, 12.95, 6.95  # n1 게이트 접속점, n2 줄, VREF 접속점
    rail(d, (1.0, RAIL_Y), (17.6, RAIL_Y))
    d.add(elm.Label().right().at((1.0, RAIL_Y + 0.2)).label(r"$V_{DD}$", halign="left", valign="bottom"))
    # 위 pmos 세 개: M7 좌우 반전, M5·M6 보통. 소스는 레일에서 짧게 내려옴
    m7 = pmos(d, at=(xl, RAIL_Y - DROP), anchor="source", mirror=True)
    m5 = pmos(d, at=(x5, RAIL_Y - DROP), anchor="source")
    m6 = pmos(d, at=(x6, RAIL_Y - DROP), anchor="source")
    for m in (m7, m5, m6):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.3, m7.center.y)).label(r"$M_\mathrm{7}$", halign="right"))
    for m, name in ((m5, "5"), (m6, "6")):
        d.add(elm.Label().right().at((m.center.x + 0.25, m.center.y + 0.25))
              .label(rf"$M_\mathrm{{{name}}}$", halign="left", valign="bottom"))
    # 게이트 공통선: M7 게이트 → n1 게이트 접속점 → M5 게이트 → (M5 기호를 지나) M6 게이트
    d.add(elm.Line().at(m7.gate).tox(xg)); n1g = dot(d)
    d.add(elm.Line().at(n1g.center).tox(m5.gate))
    d.add(elm.Line().at(m5.gate).tox(m6.gate))
    # 왼쪽 세로줄: M7 드레인 → n1 드레인 접속점 → I_REF 화살표 → M1 → 접지
    d.add(elm.Line().down().at(m7.drain).toy(9.3)); n1d = dot(d)
    d.add(elm.Line().down().at(n1g.center).toy(n1d.center.y))
    d.add(elm.Line().left().tox(xl))
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at(n1d.center).length(2.5)
          .label(r"$I_\mathrm{REF}$", "top", ofst=GAP))
    m1_drain_y = 4.53
    d.add(elm.Line().down().toy(m1_drain_y))
    m1 = nmos(d, at=(xl, m1_drain_y), anchor="drain", mirror=True)
    d.add(elm.Ground().at(m1.source).scale(0.8))
    d.add(elm.Label().right().at((xl - 0.3, m1.center.y)).label(r"$M_\mathrm{1}$", halign="right"))
    # M5·M6 드레인 세로줄: 첫 접속점(V_out 선), 둘째 접속점(R_D), M3·M4
    outs = []
    for m in (m5, m6):
        d.add(elm.Line().down().at(m.drain).toy(9.3)); first = dot(d)
        d.add(elm.Line().down().at(first.center).toy(8.1)); second = dot(d)
        outs.append((first, second))
    (o1a, o1b), (o2a, o2b) = outs
    d.add(elm.Line().right().at(o1a.center).length(0.8))
    d.add(elm.Line().left().at(o2a.center).length(0.8))
    d.add(elm.Label().right().at(((x5 + x6) / 2, o1a.center.y)).label(r"$V_\mathrm{out}$"))
    d.add(Resistor().right().at(o1b.center).to(o2b.center).label(r"$R_\mathrm{D}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().at(o1b.center).length(0.6))
    m3 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(o2b.center).length(0.6))
    m4 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((x5 + 0.25, m3.center.y)).label(r"$M_\mathrm{3}$", halign="left"))
    d.add(elm.Label().right().at((x6 - 0.25, m4.center.y)).label(r"$M_\mathrm{4}$", halign="right"))
    line_terminal(d, m3.gate, r"$V_\mathrm{in1}$", 1.7)
    line_terminal(d, m4.gate, r"$V_\mathrm{in2}$", 1.7, right=True)
    # 두 소스 → 아래 → n2 접속점 (가운데보다 조금 오른쪽) → M2 → 접지
    yn2 = m3.source.y - 0.6
    d.add(elm.Line().down().at(m3.source).toy(yn2))
    d.add(elm.Line().right().tox(xn2)); n2 = dot(d)
    d.add(elm.Line().right().tox(x6))
    d.add(elm.Line().up().toy(m4.source.y))
    d.add(elm.Line().down().at(n2.center).toy(m1_drain_y))
    m2 = nmos(d, at=(xn2, m1_drain_y), anchor="drain")
    d.add(elm.Ground().at(m2.source).scale(0.8))
    d.add(elm.Label().right().at((xn2 + 0.3, m2.center.y)).label(r"$M_\mathrm{2}$", halign="left"))
    # M1 게이트 → VREF 접속점 → M2 게이트, VREF 접속점 → 아래 선 끝 V_REF
    d.add(elm.Line().at(m1.gate).tox(xref)); vref = dot(d)
    d.add(elm.Line().at(vref.center).tox(m2.gate))
    d.add(elm.Line().down().at(vref.center).length(1.7))
    d.add(elm.Label().right().at((xref, d.here.y - 0.3)).label(r"$V_\mathrm{REF}$", halign="center", valign="top"))
    return d
