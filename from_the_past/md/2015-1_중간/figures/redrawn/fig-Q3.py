"""2015-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import Resistor, dot, gate_terminal, new_drawing, rail

RAIL_Y = 9.0


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def draw():
    d = new_drawing()
    R = RAIL_Y
    xl, xr = 0, 3.8
    xm = (xl + xr) / 2
    rail(d, (xl - 0.3, R), (xr + 0.3, R))
    d.add(elm.Label().right().at((xm, R + 0.15)).label(r"$V_{CC}$", valign="bottom"))
    # 위 pnp: Q3 보통, Q4 좌우 반전. 이미터가 레일에서 조금 아래
    ye = R - 0.5
    q3 = bjt(d, elm.BjtPnp, (xl, ye), "emitter", label=r"$Q_\mathrm{3}$")
    q4 = bjt(d, elm.BjtPnp, (xr, ye), "emitter", mirror=True, label=r"$Q_\mathrm{4}$")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(R))
    # 출력 접속점, 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().down().at(q3.collector).length(0.6)); out1 = dot(d)
    d.add(elm.Line().down().at(q4.collector).length(0.6)); out2 = dot(d)
    d.add(elm.Line().right().at(out1.center).length(0.6)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.6)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 귀환 저항: 베이스 → 가로 R → 바깥 끝에서 아래로 출력 높이 → 출력 접속점
    for q, out, s, name in ((q3, out1, -1, "1"), (q4, out2, 1, "2")):
        xa, xb = q.base.x + s * 0.15, q.base.x + s * 1.15   # 저항 안쪽 끝, 바깥 끝
        xo = xb + s * 0.15                                   # 귀환 세로선
        d.add(elm.Line().at(q.base).tox(xa))
        d.add(Resistor().right().at((min(xa, xb), q.base.y)).to((max(xa, xb), q.base.y))
              .label(r"$R_\mathrm{%s}$" % name, "top", ofst=0.2))
        d.add(elm.Line().at((xb, q.base.y)).tox(xo))
        d.add(elm.Line().down().toy(out.center.y))
        d.add(elm.Line().tox(out.center.x))
    # 입력 쌍: Q1 보통, Q2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.6))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(out2.center).length(0.6))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 이미터 → 아래 → 가운데 P 접속점 → I_EE → 접지
    ybot = q1.emitter.y - 0.5
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    d.add(elm.Line().down().at(p.center).length(0.6))
    d.add(elm.Label().right().at((xm - 0.35, ybot - 0.25)).label(r"$P$", halign="right", valign="top"))
    iee = d.add(elm.SourceI().down().length(1.4).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "top", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return d
