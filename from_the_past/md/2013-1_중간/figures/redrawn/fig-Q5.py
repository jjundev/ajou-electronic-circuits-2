"""2013-1 중간 Q5 — 기준: Q5.md '회로 — Fig Q5(a)', '회로 — Fig Q5(b)', '회로 — Fig Q5(c)'."""
import schemdraw.elements as elm
from schem_style import Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # 세 패널 레일 높이
CAP_Y = -12.6   # 캡션 높이
LEAD = 1.2      # 입력 원까지 늘이는 가로선 (gate_terminal 앞)
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


def inputs(d, q1, q2):
    """V_in1 원 → 가로선 → Q1 베이스, Q2 베이스 → 가로선 → V_in2 원."""
    d.add(elm.Line().left().at(q1.base).length(LEAD))
    gate_terminal(d, d.here, r"$V_\mathrm{in1}$", open_=True)
    d.add(elm.Line().right().at(q2.base).length(LEAD))
    gate_terminal(d, d.here, r"$V_\mathrm{in2}$", open_=True, right=True)


def facing_outputs(d, j1, j2):
    """두 출력 원이 가운데에서 마주 보고 그 사이에 V_out."""
    d.add(elm.Line().right().at(j1.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Line().left().at(j2.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Label().right().at(((j1.center.x + j2.center.x) / 2, j1.center.y)).label(r"$V_\mathrm{out}$"))


def input_pair_tail(d, xl, xr, yb, drop, iee_len):
    """Q1(보통)·Q2(좌우 반전), 두 이미터 → 아래 → P 접속점 → I_EE → 접지. (q1, q2) 돌려줌."""
    xm = (xl + xr) / 2
    q1 = bjt(d, elm.BjtNpn, xl, yb, label=r"$Q_\mathrm{1}$")
    q2 = bjt(d, elm.BjtNpn, xr, yb, mirror=True, label=r"$Q_\mathrm{2}$")
    inputs(d, q1, q2)
    ybot = q1.emitter.y - drop
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    d.add(elm.Label().right().at((xm - 0.4, ybot - 0.25)).label(r"$P$", halign="right", valign="top"))
    iee = d.add(elm.SourceI().down().at(p.center).length(2.2).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Line().down().at(iee.end).length(iee_len))
    d.add(elm.Ground().scale(0.8))
    return q1, q2


def panel_a(d):
    xl, xr = 4.0, 8.6
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.4, xr + 0.4)
    # Q3: pnp 좌우 반전, Q4: pnp 보통. 이미터에서 세로선이 위로 레일
    yb = RAIL_Y - 1.5
    q3 = bjt(d, elm.BjtPnp, xl, yb, mirror=True)
    q4 = bjt(d, elm.BjtPnp, xr, yb, label=r"$Q_\mathrm{4}$")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.35, yb + 0.15)).label(r"$Q_\mathrm{3}$", halign="right"))
    # 베이스 공통선, 위 X 접속점 → 아래로 R1–R2 사이 아래 X 접속점
    d.add(elm.Line().at(q3.base).tox(xm)); xt = dot(d)
    d.add(elm.Line().at(xt.center).tox(q4.base))
    d.add(elm.Label().right().at((xm, yb + 0.3)).label(r"$X$", valign="bottom"))
    yr = RAIL_Y - 3.0
    d.add(elm.Line().down().at(q3.collector).toy(yr)); r1j = dot(d)
    d.add(elm.Line().down().at(q4.collector).toy(yr)); r2j = dot(d)
    d.add(elm.Line().down().at(xt.center).toy(yr)); xb = dot(d)
    d.add(Resistor().right().at(r1j.center).to(xb.center).label(r"$R_\mathrm{1}$", "bottom", ofst=0.25))
    d.add(Resistor().right().at(xb.center).to(r2j.center).label(r"$R_\mathrm{2}$", "bottom", ofst=0.25))
    # 출력 접속점, 두 원이 마주 봄
    yo = RAIL_Y - 4.9
    d.add(elm.Line().down().at(r1j.center).toy(yo)); o1 = dot(d)
    d.add(elm.Line().down().at(r2j.center).toy(yo)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    q1, q2 = input_pair_tail(d, xl, xr, RAIL_Y - 6.5, 0.6, 0.3)
    d.add(elm.Line().down().at(o1.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(o2.center).toy(q2.collector.y))
    caption(d, (xm - 0.4, CAP_Y), "(a)")


def panel_b(d):
    xl, xr = 19.0, 25.4
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.4, xr + 0.3)
    # 부하 저항: 아래로 그리는 소자의 라벨, loc="top"이면 왼쪽, "bottom"이면 오른쪽
    d.add(Resistor().down().at((xl, RAIL_Y)).length(3.4).label(r"$R_\mathrm{C}$", "top", ofst=GAP)); x = dot(d)
    d.add(Resistor().down().at((xr, RAIL_Y)).length(3.4).label(r"$R_\mathrm{C}$", "bottom", ofst=GAP)); y = dot(d)
    d.add(elm.Label().right().at((xl - 0.4, x.center.y - 0.25)).label(r"$X$", halign="right", valign="top"))
    d.add(elm.Label().right().at((xr + 0.3, y.center.y - 0.2)).label(r"$Y$", halign="left", valign="top"))
    facing_outputs(d, x, y)
    yb = RAIL_Y - 5.2
    q1 = bjt(d, elm.BjtNpn, xl, yb, label=r"$Q_\mathrm{1}$")
    q2 = bjt(d, elm.BjtNpn, xr, yb, mirror=True, label=r"$Q_\mathrm{2}$")
    d.add(elm.Line().down().at(x.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(y.center).toy(q2.collector.y))
    inputs(d, q1, q2)
    # 이미터 → n1/n2 접속점, 그 사이 R_E, 아래로 I_EE, 접지
    for q, side in ((q1, "top"), (q2, "bottom")):
        d.add(elm.Line().down().at(q.emitter).length(1.0)); n = dot(d)
        iee = d.add(elm.SourceI().down().at(n.center).length(2.2).scale(0.6)
                    .label(r"$I_\mathrm{EE}$", side, ofst=0.35))
        d.add(elm.Line().down().at(iee.end).length(0.4))
        d.add(elm.Ground().scale(0.8))
        if q is q1:
            n1 = n
        else:
            n2 = n
    d.add(Resistor().right().at(n1.center).to(n2.center).label(r"$R_\mathrm{E}$", "bottom", ofst=0.25))
    caption(d, (xm - 0.4, CAP_Y), "(b)")


def panel_c(d):
    xl, xr = 36.5, 41.1
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.6, xr + 0.3)
    # Q3, Q4: pnp 보통. 이미터에서 세로선이 위로 레일
    yb = RAIL_Y - 1.3
    q3 = bjt(d, elm.BjtPnp, xl, yb)
    q4 = bjt(d, elm.BjtPnp, xr, yb)
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    for q, text in ((q3, r"$Q_\mathrm{3}$"), (q4, r"$Q_\mathrm{4}$")):
        d.add(elm.Label().right().at((q.base.x + 0.25, q.collector.y - 0.1))
              .label(text, halign="right", valign="top"))
    # V_b 원 → Q3 베이스, 같은 높이로 Q4 베이스까지
    d.add(elm.Line().left().at(q3.base).length(0.6))
    gate_terminal(d, d.here, r"$V_\mathrm{b}$", open_=True)
    d.add(elm.Line().right().at(q3.base).tox(q4.base))
    # 출력 접속점(마주 보는 두 원), 저항 접속점(R1–R2)
    yo = RAIL_Y - 3.4
    d.add(elm.Line().down().at(q3.collector).toy(yo)); o1 = dot(d)
    d.add(elm.Line().down().at(q4.collector).toy(yo)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    yr = RAIL_Y - 4.9
    d.add(elm.Line().down().at(o1.center).toy(yr)); r1j = dot(d)
    d.add(elm.Line().down().at(o2.center).toy(yr)); r2j = dot(d)
    d.add(Resistor().right().at(r1j.center).to((xm, yr)).label(r"$R_\mathrm{1}$", "top", ofst=0.25))
    d.add(Resistor().right().at((xm, yr)).to(r2j.center).label(r"$R_\mathrm{2}$", "top", ofst=0.25))
    q1, q2 = input_pair_tail(d, xl, xr, RAIL_Y - 6.4, 0.4, 0.3)
    d.add(elm.Line().down().at(r1j.center).toy(q1.collector.y))
    d.add(elm.Line().down().at(r2j.center).toy(q2.collector.y))
    caption(d, (xm - 0.4, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d)
    panel_b(d)
    panel_c(d)
    return d
