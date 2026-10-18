"""2015-2 중간 Q2 둘째 그림 — 기준: Q2.md '회로 — Fig Q2-2'."""
import schemdraw.elements as elm
from schem_style import Resistor, dot, gate_terminal, new_drawing, rail

RAIL_Y = 14.0


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def text(d, xy, s, halign="left", valign="center"):
    return d.add(elm.Label().right().at(xy).label(s, halign=halign, valign=valign))


def pair(d, cls, xl, xr, y, anchor, vb):
    """보통 방향 트랜지스터 둘(왼쪽 xl, 오른쪽 xr). 왼쪽 베이스에 점 단자, 베이스 공통선이 오른쪽 베이스까지."""
    ql = bjt(d, cls, (xl, y), anchor)
    qr = bjt(d, cls, (xr, y), anchor)
    gate_terminal(d, ql.base, vb)
    d.add(elm.Line().at(ql.base).to(qr.base))
    return ql, qr


def draw():
    d = new_drawing()
    R = RAIL_Y
    xl, xr = 0, 4.0             # 왼쪽 세로줄, 오른쪽 세로줄
    x2 = xr + 0.6               # Q2 (조금 오른쪽)
    xm = (xl + x2) / 2
    rail(d, (xl - 0.3, R), (xr + 0.35, R))
    text(d, (xr + 0.5, R + 0.05), r"$V_{CC}$")
    # Q7, Q8: pnp, 이미터가 레일에서 조금 아래
    q7, q8 = pair(d, elm.BjtPnp, xl, xr, R - 0.35, "emitter", r"$V_\mathrm{b3}$")
    for q in (q7, q8):
        d.add(elm.Line().up().at(q.emitter).toy(R))
    # A, B 접속점과 그 사이 R_1
    d.add(elm.Line().down().at(q7.collector).length(1.1)); a = dot(d)
    d.add(elm.Line().down().at(q8.collector).length(1.1)); b = dot(d)
    d.add(Resistor().right().at(a.center).to(b.center).label(r"$R_\mathrm{1}$", "bottom", ofst=0.2))
    text(d, (xl - 0.25, a.center.y), r"$A$", halign="right")
    text(d, (xr + 0.25, b.center.y), r"$B$")
    text(d, (xl + 0.3, a.center.y + 0.2), r"$Q_\mathrm{7}$", valign="bottom")
    text(d, (xr - 0.3, b.center.y + 0.2), r"$Q_\mathrm{8}$", halign="right", valign="bottom")
    # Q5, Q6: pnp, 이미터가 A, B
    q5, q6 = pair(d, elm.BjtPnp, xl, xr, a.center.y - 0.85, "emitter", r"$V_\mathrm{b2}$")
    for q, n in ((q5, a), (q6, b)):
        d.add(elm.Line().up().at(q.emitter).toy(n.center.y))
    # 출력 접속점, 두 원이 가운데에서 마주 봄. V_out은 왼쪽 원 바로 오른쪽
    d.add(elm.Line().down().at(q5.collector).length(1.3)); out1 = dot(d)
    d.add(elm.Line().down().at(q6.collector).length(1.3)); out2 = dot(d)
    d.add(elm.Line().right().at(out1.center).length(0.6)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.6)); dot(d, open_=True)
    text(d, (xl + 0.9, out1.center.y), r"$V_\mathrm{out}$")
    text(d, (xl - 0.3, out1.center.y + 0.3), r"$Q_\mathrm{5}$", halign="right", valign="bottom")
    text(d, (xr - 0.3, out2.center.y + 0.3), r"$Q_\mathrm{6}$", halign="right", valign="bottom")
    # Q3, Q4: npn, 컬렉터가 출력
    q3, q4 = pair(d, elm.BjtNpn, xl, xr, out1.center.y - 1.4, "collector", r"$V_\mathrm{b1}$")
    for q, n in ((q3, out1), (q4, out2)):
        d.add(elm.Line().down().at(n.center).toy(q.collector.y))
    text(d, (xl + 0.3, q3.collector.y + 0.15), r"$Q_\mathrm{3}$", valign="bottom")
    text(d, (xr + 0.3, q4.collector.y + 0.15), r"$Q_\mathrm{4}$", valign="bottom")
    # Q1 (보통): Q3 이미터 아래. Q2 (좌우 반전): Q4 이미터 → 아래 → 오른쪽 → Q2 컬렉터
    d.add(elm.Line().down().at(q3.emitter).length(1.9))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    q2 = bjt(d, elm.BjtNpn, (x2, q1.collector.y), "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    yk = q1.collector.y + 0.45
    d.add(elm.Line().down().at(q4.emitter).toy(yk))
    d.add(elm.Line().right().tox(x2))
    d.add(elm.Line().down().toy(q2.collector.y))
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 이미터 → 아래 → 가운데 n3 접속점 → I_EE → 접지
    ybot = q1.emitter.y - 0.7
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n3 = dot(d)
    d.add(elm.Line().right().tox(x2))
    d.add(elm.Line().up().toy(q2.emitter.y))
    iee = d.add(elm.SourceI().down().at(n3.center).length(1.8).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return d
