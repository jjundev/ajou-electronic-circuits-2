"""2015-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import dot, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
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


def text(d, xy, s, halign="left", valign="center"):
    return d.add(elm.Label().right().at(xy).label(s, halign=halign, valign=valign))


def draw():
    d = new_drawing()
    R = RAIL_Y
    xref, xq1, xq2, xq3 = 0, 3.6, 8.0, 10.6     # Q_REF, Q1, Q2, Q3·Q4 세로줄
    rail(d, (xref - 0.3, R), (xq3 + 0.35, R))
    text(d, (xq3 + 0.5, R + 0.05), r"$V_{CC}$")
    # Q2(좌우 반전), Q3(보통): pnp, 이미터가 레일에서 조금 아래
    ye = R - 0.4
    q2 = bjt(d, elm.BjtPnp, (xq2, ye), "emitter", mirror=True)
    q3 = bjt(d, elm.BjtPnp, (xq3, ye), "emitter")
    for q in (q2, q3):
        d.add(elm.Line().up().at(q.emitter).toy(R))
    text(d, (xq2 - 0.3, q2.base.y - 0.45), r"$Q_\mathrm{2}$", halign="right")
    text(d, (xq2 - 0.3, q2.base.y + 0.4), r"$A_\mathrm{E}$", halign="right")
    text(d, (xq3 + 0.3, q3.base.y - 0.45), r"$Q_\mathrm{3}$")
    text(d, (xq3 + 0.3, q3.base.y + 0.4), r"$2A_\mathrm{E}$")
    # n2: Q2 컬렉터 아래 접속점. 다이오드 연결선이 오른쪽에서 위로 베이스 선의 n2 위 접속점
    d.add(elm.Line().down().at(q2.collector).length(0.55)); n2 = dot(d)
    xd2 = q2.base.x + 0.4
    d.add(elm.Line().right().at(n2.center).tox(xd2))
    d.add(elm.Line().up().toy(q2.base.y)); dot(d)
    d.add(elm.Line().at(q2.base).to(q3.base))
    # 오른쪽 세로줄: Q3 컬렉터 → out 접속점(I_copy 화살표 오른쪽) → Q4 → 접지
    d.add(elm.Line().down().at(q3.collector).length(0.55)); out = dot(d)
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).right().at(out.center).length(1.9))
    text(d, (xq3 + 1.05, out.center.y - 0.3), r"$I_\mathrm{copy}$", halign="center", valign="top")
    d.add(elm.Line().down().at(out.center).length(0.85))
    q4 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{4}$")
    d.add(elm.Ground().at(q4.emitter).scale(0.8))
    text(d, (xq3 + 0.55, q4.emitter.y - 0.25), r"$3A_\mathrm{E}$", valign="top")
    # Q_REF(좌우 반전), Q1(보통): npn, 컬렉터 같은 높이
    yc = n2.center.y - 2.6
    qref = bjt(d, elm.BjtNpn, (xref, yc), "collector", mirror=True)
    q1 = bjt(d, elm.BjtNpn, (xq1, yc), "collector")
    for q in (qref, q1):
        d.add(elm.Ground().at(q.emitter).scale(0.8))
    text(d, (xref - 0.35, qref.base.y - 0.2), r"$Q_\mathrm{REF}$", halign="right")
    text(d, (xref - 0.35, qref.base.y + 0.45), r"$A_\mathrm{E}$", halign="right")
    text(d, (xq1 + 0.3, q1.base.y - 0.35), r"$Q_\mathrm{1}$")
    text(d, (xq1 + 0.3, q1.base.y + 0.4), r"$5A_\mathrm{E}$")
    # Q1 컬렉터 ↑ → n2 높이 → 오른쪽 n2. 화살표는 아래(Q1 컬렉터로 들어감)
    d.add(elm.Line().at(n2.center).tox(xq1))
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().length(1.0))
    d.add(elm.Line().down().toy(q1.collector.y))
    # 왼쪽 세로줄: 레일 → I_REF(화살표 아래) → 긴 세로선 → n1 위 접속점 → Q_REF 컬렉터
    d.add(elm.Line().down().at((xref, R)).length(0.25))
    d.add(elm.SourceI().down().length(1.3).scale(0.6).label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    yn1 = yc + 0.4
    d.add(elm.Line().down().toy(yn1)); n1 = dot(d)
    d.add(elm.Line().down().toy(yc))
    # 다이오드 연결: n1 위 → 오른쪽 → 아래 n1 아래 접속점(베이스 선), 계속 맨 아래까지
    xd1 = qref.base.x + 0.4
    ybot = q1.emitter.y - 1.0
    d.add(elm.Line().right().at(n1.center).tox(xd1))
    d.add(elm.Line().down().toy(qref.base.y)); n1b = dot(d)
    d.add(elm.Line().at(qref.base).to(q1.base))
    d.add(elm.Line().down().at(n1b.center).toy(ybot))
    # 맨 아래 가로선 → Q4 베이스 왼쪽에서 위로 → Q4 베이스
    xb4 = q4.base.x - 0.4
    d.add(elm.Line().right().tox(xb4))
    d.add(elm.Line().up().toy(q4.base.y))
    d.add(elm.Line().right().tox(q4.base.x))
    return d
