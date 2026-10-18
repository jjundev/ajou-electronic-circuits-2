"""2017-1 중간 (D반) Q6 — 기준: Q6.md '회로 — Fig Q6'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing, nmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.5    # V_DD 레일 높이


def open_terminal(d, at, label, length, right=False):
    """가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def draw():
    d = new_drawing()
    xl, xr = 0.0, 3.6
    xm = (xl + xr) / 2
    rail(d, (xl - 0.4, RAIL_Y), (xr + 0.6, RAIL_Y))
    d.add(elm.Label().right().at((xr + 0.7, RAIL_Y - 0.1)).label(r"$V_{DD}$", halign="left"))
    # 레일에 매달린 두 세로 저항 → vout 접속점 (출력 원은 바깥쪽)
    rd1 = d.add(Resistor().down().at((xl, RAIL_Y)).length(2.1).label(r"$R_\mathrm{D}$", "top", ofst=GAP))
    rd2 = d.add(Resistor().down().at((xr, RAIL_Y)).length(2.1)
                .label(r"$R_\mathrm{D} + \Delta R_\mathrm{D}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().at(rd1.end).length(0.3)); vo1 = dot(d)
    d.add(elm.Line().down().at(rd2.end).length(0.3)); vo2 = dot(d)
    open_terminal(d, vo1.center, r"$v_\mathrm{out1}$", 0.7)
    open_terminal(d, vo2.center, r"$v_\mathrm{out2}$", 0.7, right=True)
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(vo1.center).length(0.6))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(vo2.center).length(0.6))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    open_terminal(d, m1.gate, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, m2.gate, r"$V_\mathrm{in2}$", 0.6, right=True)
    # 두 소스 → 아래 → 가운데 P (라벨은 점 위) → M3 → 접지
    yt = m1.source.y - 0.7
    d.add(elm.Line().down().at(m1.source).toy(yt))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Label().right().at((xm, yt + 0.2)).label(r"$P$", halign="center", valign="bottom"))
    d.add(elm.Line().down().at(p.center).length(0.6))
    m3 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(m3.source).scale(0.8))
    return d
