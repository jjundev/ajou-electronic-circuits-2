"""2017-1 중간 (D반) Q5 — 기준: Q5.md '회로 — Fig Q5'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 9.5    # V_DD 레일 높이
DROP = 0.3      # 레일에서 pmos 소스까지 세로선


def open_terminal(d, at, label, length, right=False):
    """게이트에서 가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def draw():
    d = new_drawing()
    xl, xr = 0.0, 3.8
    xm = (xl + xr) / 2
    rail(d, (xl - 0.4, RAIL_Y), (xr + 0.6, RAIL_Y))
    d.add(elm.Label().right().at((xr + 0.7, RAIL_Y - 0.1)).label(r"$V_{DD}$", halign="left"))
    # M3, M4: pmos 보통 방향, 소스에서 위로 레일
    m3 = pmos(d, at=(xl, RAIL_Y - DROP), anchor="source")
    m4 = pmos(d, at=(xr, RAIL_Y - DROP), anchor="source", label=r"$M_\mathrm{4}$")
    for m in (m3, m4):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.3, m3.drain.y - 0.05))
          .label(r"$M_\mathrm{3}$", halign="right", valign="top"))
    # 게이트 공통선: V_b1 점 단자 → M3 게이트 → (M3 기호를 지나) M4 게이트
    gate_terminal(d, m3.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().at(m3.gate).tox(m4.gate))
    # 드레인 → out 접속점 → 출력 원 (가운데에서 마주 봄)
    d.add(elm.Line().down().at(m3.drain).length(0.5)); out1 = dot(d)
    d.add(elm.Line().down().at(m4.drain).length(0.5)); out2 = dot(d)
    d.add(elm.Line().right().at(out1.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.3))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(out2.center).length(0.3))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    open_terminal(d, m1.gate, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, m2.gate, r"$V_\mathrm{in2}$", 0.6, right=True)
    # 두 소스 → 아래 → 가운데 n1 → M5 → M6 → 접지
    yt = m1.source.y - 0.45
    d.add(elm.Line().down().at(m1.source).toy(yt))
    d.add(elm.Line().right().tox(xm)); n1 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Line().down().at(n1.center).length(0.3))
    m5 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{5}$")
    gate_terminal(d, m5.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Line().down().at(m5.source).length(0.15))
    m6 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{6}$")
    gate_terminal(d, m6.gate, r"$V_\mathrm{b3}$")
    d.add(elm.Ground().at(m6.source).scale(0.8))
    return d
