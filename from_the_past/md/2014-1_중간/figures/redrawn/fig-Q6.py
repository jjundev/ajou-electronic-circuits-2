"""2014-1 중간 Q6 — 기준: Q6.md '회로 — Fig Q6(a)', '회로 — Fig Q6(b)', '회로 — Fig Q6(c)'."""
import schemdraw.elements as elm
from schem_style import Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # 세 패널 레일 높이
CAP_Y = -8.5    # 캡션 높이
BX = 0.752      # BJT 베이스에서 컬렉터·이미터 줄까지 가로 거리
VCC = r"$V_{CC}$"


def bjt(d, cls, col, yb, mirror=False, label=None, loc=None):
    """컬렉터·이미터 줄 x=col, 베이스 높이 yb. 베이스 왼쪽(mirror면 오른쪽)."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor("base").at((col + BX if mirror else col - BX, yb))
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def vcc_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.2, RAIL_Y + 0.05)).label(VCC, halign="left"))


def label(d, xy, text, ha="center", va="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=ha, valign=va))


def facing_outputs(d, j1, j2):
    """두 출력 원이 가운데에서 마주 보고 그 사이에 V_out."""
    d.add(elm.Line().right().at(j1.center).length(0.6)); dot(d, open_=True)
    d.add(elm.Line().left().at(j2.center).length(0.6)); dot(d, open_=True)
    label(d, ((j1.center.x + j2.center.x) / 2, j1.center.y), r"$V_\mathrm{out}$")


def input_pair(d, xl, xr, yb, lead=0.0):
    """Q1(보통)·Q2(좌우 반전)와 V_in1·V_in2 원. lead만큼 입력선을 더 늘인다."""
    q1 = bjt(d, elm.BjtNpn, xl, yb, label=r"$Q_\mathrm{1}$")
    q2 = bjt(d, elm.BjtNpn, xr, yb, mirror=True, label=r"$Q_\mathrm{2}$")
    d.add(elm.Line().left().at(q1.base).length(lead))
    gate_terminal(d, d.here, r"$V_\mathrm{in1}$", open_=True)
    d.add(elm.Line().right().at(q2.base).length(lead))
    gate_terminal(d, d.here, r"$V_\mathrm{in2}$", open_=True, right=True)
    return q1, q2


def iee_ground(d, at, length, side="bottom", drop=0.0):
    """at에서 drop만큼 내려 I_EE 전류원(화살표 아래), 접지."""
    d.add(elm.Line().down().at(at).length(drop))
    iee = d.add(elm.SourceI().down().length(length).scale(0.6)
                .label(r"$I_\mathrm{EE}$", side, ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))


def panel_a(d):
    xl, xr = 3.9, 10.2
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.3, xr + 0.3)
    # 부하 저항: 아래로 그리는 소자의 라벨, loc="top"이면 왼쪽, "bottom"이면 오른쪽
    d.add(Resistor().down().at((xl, RAIL_Y)).length(2.4).label(r"$R_\mathrm{C}$", "top", ofst=GAP)); x = dot(d)
    d.add(Resistor().down().at((xr, RAIL_Y)).length(2.4).label(r"$R_\mathrm{C}$", "bottom", ofst=GAP)); o2 = dot(d)
    label(d, (xl - 0.55, x.center.y - 0.2), r"$X$", "right", "top")
    facing_outputs(d, x, o2)
    q1, q2 = input_pair(d, xl, xr, RAIL_Y - 3.6, lead=1.0)
    d.add(elm.Line().down().at(x.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(o2.center).toy(q2.collector.y))
    # 이미터 → 아래 → 가로선: 왼쪽 이미터 — R_E — P — R_E — 오른쪽 이미터
    yr = q1.emitter.y - 0.6
    d.add(elm.Line().down().at(q1.emitter).toy(yr)); d.add(elm.Line().right().length(0.6))
    d.add(Resistor().right().tox(xm - 0.6).label(r"$R_\mathrm{E}$", "bottom", ofst=0.25))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().length(0.6))
    d.add(Resistor().right().tox(xr - 0.6).label(r"$R_\mathrm{E}$", "bottom", ofst=0.25))
    d.add(elm.Line().right().tox(xr)); d.add(elm.Line().up().toy(q2.emitter.y))
    label(d, (xm - 0.35, yr - 0.25), r"$P$", "right", "top")
    iee_ground(d, p.center, 1.3, drop=0.7)
    caption(d, (xm - 0.3, CAP_Y), "(a)")


def panel_b(d):
    xl, xr = 17.0, 20.4
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.3, xr + 0.3)
    # Q3, Q4: pnp 보통. 이미터에서 세로선이 위로 레일
    yb = RAIL_Y - 1.1
    q3 = bjt(d, elm.BjtPnp, xl, yb)
    q4 = bjt(d, elm.BjtPnp, xr, yb)
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    for q, text in ((q3, r"$Q_\mathrm{3}$"), (q4, r"$Q_\mathrm{4}$")):
        label(d, (q.base.x + 0.25, q.collector.y - 0.1), text, "right", "top")
    # V_b 원 → Q3 베이스, 같은 높이로 Q4 베이스까지 (Q3 리드 사이를 지남)
    d.add(elm.Line().left().at(q3.base).length(0.6))
    gate_terminal(d, d.here, r"$V_\mathrm{b}$", open_=True)
    d.add(elm.Line().right().at(q3.base).tox(q4.base))
    yo = RAIL_Y - 2.9
    d.add(elm.Line().down().at(q3.collector).toy(yo)); o1 = dot(d)
    d.add(elm.Line().down().at(q4.collector).toy(yo)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    q1, q2 = input_pair(d, xl, xr, RAIL_Y - 4.1)
    d.add(elm.Line().down().at(o1.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(o2.center).toy(q2.collector.y))
    # 두 이미터 → 아래 → P 접속점 → I_EE → 접지
    ybot = q1.emitter.y - 0.4
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr)); d.add(elm.Line().up().toy(q2.emitter.y))
    label(d, (xm - 0.35, ybot - 0.25), r"$P$", "right", "top")
    iee_ground(d, p.center, 1.3, drop=0.4)
    caption(d, (xm - 0.3, CAP_Y), "(b)")


def panel_c(d):
    xl, xr = 26.0, 30.0
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 1.4, xr + 1.4)
    # Q3: npn 보통, Q4: npn 좌우 반전. 컬렉터가 레일로, 베이스도 레일에서 내려와 꺾인 선
    yb = RAIL_Y - 1.1
    q3 = bjt(d, elm.BjtNpn, xl, yb, label=r"$Q_\mathrm{3}$")
    q4 = bjt(d, elm.BjtNpn, xr, yb, mirror=True, label=r"$Q_\mathrm{4}$")
    for q, sgn in ((q3, -1), (q4, 1)):
        d.add(elm.Line().up().at(q.collector).toy(RAIL_Y))
        xb = q.base.x + sgn * 0.45
        d.add(elm.Line().down().at((xb, RAIL_Y)).toy(q.base.y))
        d.add(elm.Line().tox(q.base.x))
    # R_C: 이미터 → 출력 접속점
    d.add(Resistor().down().at(q3.emitter).length(1.6).label(r"$R_\mathrm{C}$", "top", ofst=GAP)); o1 = dot(d)
    d.add(Resistor().down().at(q4.emitter).length(1.6).label(r"$R_\mathrm{C}$", "bottom", ofst=GAP)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    q1, q2 = input_pair(d, xl, xr, o1.center.y - 1.1)
    d.add(elm.Line().down().at(o1.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(o2.center).toy(q2.collector.y))
    # 이미터 → n3/n4 접속점, 그 사이 R_E, 아래로 I_EE, 접지
    ns = []
    for q, side in ((q1, "top"), (q2, "bottom")):
        d.add(elm.Line().down().at(q.emitter).length(0.5)); ns.append(dot(d))
        iee_ground(d, ns[-1].center, 1.4, side)
    d.add(Resistor().right().at(ns[0].center).to(ns[1].center).label(r"$R_\mathrm{E}$", "bottom", ofst=0.25))
    caption(d, (xm - 0.3, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d)
    panel_b(d)
    panel_c(d)
    return d
