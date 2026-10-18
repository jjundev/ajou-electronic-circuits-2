"""2015-1 중간 Q3 둘째 그림 — 기준: Q3.md '회로 — Fig Q3-2'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, rail

GAP = 0.2
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
    xl, xr = 0, 4.2
    xm = (xl + xr) / 2
    rail(d, (xl - 0.3, R), (xr + 0.3, R))
    d.add(elm.Label().right().at((xr + 0.45, R + 0.05)).label(r"$V_{CC}$", halign="left"))
    # 위 pnp: Q3 좌우 반전, Q4 보통. 이미터가 레일에서 조금 아래
    ye = R - 0.35
    q3 = bjt(d, elm.BjtPnp, (xl, ye), "emitter", mirror=True, label=r"$Q_\mathrm{3}$")
    q4 = bjt(d, elm.BjtPnp, (xr, ye), "emitter", label=r"$Q_\mathrm{4}$")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(R))
    # 베이스 공통선과 Q3 베이스 바로 오른쪽 접속점, 아래로 n1 (다이오드 연결)
    xb = q3.base.x + 0.35
    d.add(elm.Line().at(q3.base).tox(xb)); b = dot(d)
    d.add(elm.Line().at(b.center).tox(q4.base.x))
    d.add(elm.Line().down().at(q3.collector).length(0.6)); n1 = dot(d)
    d.add(elm.Line().down().at(b.center).toy(n1.center.y))
    d.add(elm.Line().left().tox(xl))
    d.add(elm.Line().down().at(q4.collector).length(0.6)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.2))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    # 입력 쌍: Q1 보통, Q2 좌우 반전
    d.add(elm.Line().down().at(n1.center).length(0.7))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(vout.center).length(0.7))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 이미터 → 아래 → 가운데 n2 접속점 → I_EE → 접지
    ybot = q1.emitter.y - 0.45
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n2 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    iee = d.add(elm.SourceI().down().at(n2.center).length(1.6).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return d
