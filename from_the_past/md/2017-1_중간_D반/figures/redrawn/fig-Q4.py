"""2017-1 중간 (D반) Q4 — 기준: Q4.md '회로 — Fig Q4(a)', '회로 — Fig Q4(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.3    # V_DD 레일 높이 (두 패널 공통)
DROP = 0.3      # 레일에서 pmos 소스까지 세로선
CAP_Y = 0.0     # 캡션 높이


def vdd_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.1, RAIL_Y - 0.1)).label(r"$V_{DD}$", halign="left"))


def open_terminal(d, at, label, length, right=False):
    """게이트에서 가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def vout_pair(d, left, right, xm):
    """두 출력 원이 가운데에서 마주 보고 그 사이에 V_out."""
    d.add(elm.Line().right().at(left.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(right.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, left.center.y)).label(r"$V_\mathrm{out}$"))


def input_pair(d, top1, top2, xl, xr, length):
    """M1 보통, M2 좌우 반전. 드레인이 top1/top2 접속점 아래. 입력은 개방 원."""
    d.add(elm.Line().down().at(top1.center).length(0.3))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(top2.center).length(0.3))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    open_terminal(d, m1.gate, r"$V_\mathrm{in1}$", length)
    open_terminal(d, m2.gate, r"$V_\mathrm{in2}$", length, right=True)
    return m1, m2


def panel_a(d, x0):
    xl, xr = x0, x0 + 4.0
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.6, xr + 0.6)
    m3 = pmos(d, at=(xl, RAIL_Y - DROP), anchor="source")
    m4 = pmos(d, at=(xr, RAIL_Y - DROP), anchor="source", mirror=True)
    d.add(elm.Label().right().at((xl + 0.25, m3.center.y)).label(r"$M_\mathrm{3}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m4.center.y)).label(r"$M_\mathrm{4}$", halign="right"))
    outs = []
    for m, side in ((m3, -1), (m4, 1)):
        x = m.drain.x
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
        d.add(elm.Line().down().at(m.drain).length(0.4)); diode = dot(d)
        # 게이트 → 바깥쪽 → 아래 → 다이오드 접속점
        xg = m.gate.x + side * 0.35
        d.add(elm.Line().at(m.gate).tox(xg))
        d.add(elm.Line().down().toy(diode.center.y))
        d.add(elm.Line().tox(x))
        d.add(elm.Line().down().at(diode.center).length(0.7)); outs.append(dot(d))
    out1, out2 = outs
    vout_pair(d, out1, out2, xm)
    m1, m2 = input_pair(d, out1, out2, xl, xr, 0.6)
    # 두 소스 → 아래 → 가운데 n1 → I_SS → 접지
    yt = m1.source.y - 0.45
    d.add(elm.Line().down().at(m1.source).toy(yt))
    d.add(elm.Line().right().tox(xm)); n1 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Line().down().at(n1.center).length(0.2))
    iss = d.add(elm.SourceI().down().length(1.3).scale(0.6).label(r"$I_\mathrm{SS}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    caption(d, (xm, CAP_Y), "(a)")


def panel_b(d, x0):
    xl, xr = x0, x0 + 4.0
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.4, xr + 0.6)
    m3 = pmos(d, at=(xl, RAIL_Y - DROP), anchor="source")
    m4 = pmos(d, at=(xr, RAIL_Y - DROP), anchor="source")
    for m in (m3, m4):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    # 게이트 공통선: V_b 점 단자 → M3 게이트 → (M3 기호를 지나) M4 게이트
    gate_terminal(d, m3.gate, r"$V_\mathrm{b}$")
    d.add(elm.Line().at(m3.gate).tox(m4.gate))
    for m, name in ((m3, "3"), (m4, "4")):
        d.add(elm.Label().right().at((m.gate.x - 0.1, m.center.y + 0.25))
              .label(rf"$M_\mathrm{{{name}}}$", halign="right", valign="bottom"))
    d.add(elm.Line().down().at(m3.drain).length(0.5)); out1 = dot(d)
    d.add(elm.Line().down().at(m4.drain).length(0.5)); out2 = dot(d)
    vout_pair(d, out1, out2, xm)
    m1, m2 = input_pair(d, out1, out2, xl, xr, 0.6)
    # 소스 → n1, n2 접속점 → 라벨 없는 전류원 → 접지, n1–n2 사이 R_SS
    ns = []
    for m in (m1, m2):
        d.add(elm.Line().down().at(m.source).length(0.35)); n = dot(d)
        src = d.add(elm.SourceI().down().at(n.center).length(1.3).scale(0.6))
        d.add(elm.Ground().at(src.end).scale(0.8))
        ns.append(n)
    d.add(Resistor().right().at(ns[0].center).to(ns[1].center).label(r"$R_\mathrm{SS}$", "bottom", ofst=GAP))
    caption(d, (xm, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 2.3)
    panel_b(d, 12.4)
    return d
