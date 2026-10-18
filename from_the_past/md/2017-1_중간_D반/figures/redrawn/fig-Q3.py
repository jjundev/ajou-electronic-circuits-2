"""2017-1 중간 (D반) Q3 — 기준: Q3.md '회로 — Fig Q3(a)', '회로 — Fig Q3(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.2    # V_CC 레일 높이 (두 패널 공통)
CAP_Y = -0.3    # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def open_terminal(d, at, label, length, right=False):
    """베이스에서 가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def vout_pair(d, left, right, xm):
    """두 출력 원이 가운데에서 마주 보고 그 사이에 V_out."""
    d.add(elm.Line().right().at(left.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(right.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, left.center.y)).label(r"$V_\mathrm{out}$"))


def vcc_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.1, RAIL_Y - 0.1)).label(r"$V_{CC}$", halign="left"))


def half_a(d, x, mirror):
    """(a)의 한쪽 세로줄 위→아래: R_C, X/Y 접속점, Q1/Q2, n1/n2 접속점, I_EE, 접지."""
    out_loc = "bottom" if mirror else "top"     # 아래로 그리는 소자: top=왼쪽, bottom=오른쪽
    rc = d.add(Resistor().down().at((x, RAIL_Y)).length(1.5).label(r"$R_\mathrm{C}$", out_loc, ofst=GAP))
    d.add(elm.Line().down().at(rc.end).length(0.3)); node = dot(d)
    d.add(elm.Line().down().at(node.center).length(0.8))
    q = bjt(d, elm.BjtNpn, d.here, "collector", mirror=mirror,
            label=r"$Q_\mathrm{2}$" if mirror else r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(q.emitter).length(0.4)); n = dot(d)
    iee = d.add(elm.SourceI().down().at(n.center).length(1.4).scale(0.6)
                .label(r"$I_\mathrm{EE}$", out_loc, ofst=0.3))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return node, q, n


def panel_a(d, x0):
    xl, xr = x0, x0 + 4.0
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.4, xr + 0.6)
    x_node, q1, n1 = half_a(d, xl, False)
    y_node, q2, n2 = half_a(d, xr, True)
    d.add(elm.Label().right().at((xl - 0.25, x_node.center.y - 0.15)).label(r"$X$", halign="right", valign="top"))
    d.add(elm.Label().right().at((xr + 0.25, y_node.center.y - 0.15)).label(r"$Y$", halign="left", valign="top"))
    vout_pair(d, x_node, y_node, xm)
    open_terminal(d, q1.base, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, q2.base, r"$V_\mathrm{in2}$", 0.6, right=True)
    d.add(Resistor().right().at(n1.center).to(n2.center).label(r"$R_\mathrm{E}$", "bottom", ofst=GAP))
    caption(d, (xm, CAP_Y), "(a)")


def panel_b(d, x0):
    xl, xr = x0, x0 + 4.8
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.4, xr + 0.6)
    # Q3, Q4: pnp 보통 방향, 이미터에서 위로 레일
    q3 = bjt(d, elm.BjtPnp, (xl, RAIL_Y - 0.3), "emitter")
    q4 = bjt(d, elm.BjtPnp, (xr, RAIL_Y - 0.3), "emitter")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    for q, name in ((q3, "3"), (q4, "4")):
        d.add(elm.Label().right().at((q.center.x - 0.7, q.center.y - 0.3))
              .label(rf"$Q_\mathrm{{{name}}}$", halign="right", valign="top"))
    # 베이스 공통선: V_b 점 단자 → Q3 베이스 → (Q3 막대를 지나) Q4 베이스
    gate_terminal(d, q3.base, r"$V_\mathrm{b}$")
    d.add(elm.Line().at(q3.base).tox(q4.base))
    # 컬렉터 → 위 접속점 (출력선) → 아래 접속점 (R_1·R_2) → Q1/Q2
    nodes = []
    for q in (q3, q4):
        d.add(elm.Line().down().at(q.collector).length(0.35)); up = dot(d)
        d.add(elm.Line().down().at(up.center).length(1.25)); lo = dot(d)
        nodes.append((up, lo))
    (up1, lo1), (up2, lo2) = nodes
    vout_pair(d, up1, up2, xm)
    d.add(Resistor().right().at(lo1.center).to((xm, lo1.center.y)).label(r"$R_\mathrm{1}$", "top", ofst=GAP))
    d.add(Resistor().right().at((xm, lo1.center.y)).to(lo2.center).label(r"$R_\mathrm{2}$", "top", ofst=GAP))
    d.add(elm.Line().down().at(lo1.center).length(0.3))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(lo2.center).length(0.3))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    open_terminal(d, q1.base, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, q2.base, r"$V_\mathrm{in2}$", 0.6, right=True)
    # 두 이미터 → 아래 → 가운데 P → I_EE → 접지
    yt = q1.emitter.y - 0.45
    d.add(elm.Line().down().at(q1.emitter).toy(yt))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    d.add(elm.Label().right().at((xm - 0.2, yt - 0.15)).label(r"$P$", halign="right", valign="top"))
    d.add(elm.Line().down().at(p.center).length(0.5))
    iee = d.add(elm.SourceI().down().length(1.2).scale(0.6).label(r"$I_\mathrm{EE}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    caption(d, (xm, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 2.0)
    panel_b(d, 12.3)
    return d
