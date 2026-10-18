"""2016-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.5    # V_CC 레일 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽), 컬렉터 위, 이미터 아래."""
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


def draw():
    d = new_drawing()
    xl, xr = 3.6, 10.2                 # Q3·Q1 줄, Q4·Q2 줄
    xm = (xl + xr) / 2
    xr1, xr2 = xl + 1.65, xr - 1.65    # R1, R2 줄
    rail(d, (xl - 0.15, RAIL_Y), (xr + 0.85, RAIL_Y))
    d.add(elm.Label().right().at((xr + 0.95, RAIL_Y - 0.1)).label(r"$V_{CC}$", halign="left"))
    # Q3 좌우 반전, Q4 보통. 컬렉터는 레일에서 내려옴
    yc = RAIL_Y - 1.0
    q3 = bjt(d, elm.BjtNpn, (xl, yc), "collector", mirror=True)
    q4 = bjt(d, elm.BjtNpn, (xr, yc), "collector")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.collector).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.3, q3.base.y - 0.25)).label(r"$Q_\mathrm{3}$", halign="right"))
    d.add(elm.Label().right().at((xr + 0.3, q4.base.y - 0.25)).label(r"$Q_\mathrm{4}$", halign="left"))
    # R1, R2: 레일에 매달려 out1, out2 접속점까지 (베이스 높이)
    r1 = d.add(Resistor().down().at((xr1, RAIL_Y)).toy(q3.base.y).label(r"$R_\mathrm{1}$", "bottom", ofst=GAP))
    out1 = dot(d)
    r2 = d.add(Resistor().down().at((xr2, RAIL_Y)).toy(q4.base.y).label(r"$R_\mathrm{2}$", "top", ofst=GAP))
    out2 = dot(d)
    d.add(elm.Line().at(q3.base).tox(r1.end))
    d.add(elm.Line().at(q4.base).tox(r2.end))
    # 출력: 두 원이 가운데에서 마주 보고, 왼쪽 원 바로 오른쪽에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.7))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=0.15))
    d.add(elm.Line().left().at(out2.center).length(0.7)); dot(d, open_=True)
    # Q3 이미터 → Q1 컬렉터 (n1), Q4 이미터 → Q2 컬렉터 (n2)
    d.add(elm.Line().down().at(q3.emitter).length(0.6))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(q4.emitter).length(0.6))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    open_terminal(d, q1.base, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, q2.base, r"$V_\mathrm{in2}$", 0.6, right=True)
    # 두 이미터 → 아래 → 가운데 P 접속점 → I_EE → 접지
    yt = q1.emitter.y - 0.8
    d.add(elm.Line().down().at(q1.emitter).toy(yt))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    d.add(elm.Label().right().at((xm - 0.2, yt - 0.2)).label(r"$P$", halign="right", valign="top"))
    d.add(elm.Line().down().at(p.center).length(0.6))
    iee = d.add(elm.SourceI().down().length(1.6).scale(0.6).label(r"$I_\mathrm{EE}$", "top", ofst=0.3))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return d
