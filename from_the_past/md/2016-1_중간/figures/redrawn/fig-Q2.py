"""2016-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import Resistor, dot, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 11.7   # V_CC 레일 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽), 컬렉터 위, 이미터 아래."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def line_terminal(d, at, label, length, right=False):
    """베이스에서 가로선을 긋고 선 끝에 라벨만 단다 (원본은 점·원 없는 선 끝)."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    x, y = d.here
    d.add(elm.Label().right().at((x + 0.1 if right else x - 0.1, y))
          .label(label, halign="left" if right else "right"))


def draw():
    d = new_drawing()
    xl, xr = 4.5, 8.7
    xm = (xl + xr) / 2
    rail(d, (xl - 0.9, RAIL_Y), (xr + 1.0, RAIL_Y))
    d.add(elm.Label().right().at((xr + 1.1, RAIL_Y + 0.05)).label(r"$V_{CC}$", halign="left"))
    # 레일에 매달린 두 세로 저항
    rc1 = d.add(Resistor().down().at((xl, RAIL_Y)).length(2.5).label(r"$R_\mathrm{C}$", "top", ofst=GAP))
    rc2 = d.add(Resistor().down().at((xr, RAIL_Y)).length(2.5))
    ymid = (RAIL_Y + rc2.end.y) / 2
    d.add(elm.Label().right().at((xr + 0.35, ymid + 0.33)).label(r"$R_\mathrm{C}$ +", halign="left"))
    d.add(elm.Label().right().at((xr + 0.35, ymid - 0.33)).label(r"$\Delta R_\mathrm{C}$", halign="left"))
    # Q3 보통, Q4 좌우 반전
    yc = rc1.end.y - 1.0
    for r in (rc1, rc2):
        d.add(elm.Line().down().at(r.end).toy(yc))
    q3 = bjt(d, elm.BjtNpn, (xl, yc), "collector", label=r"$Q_\mathrm{3}$")
    q4 = bjt(d, elm.BjtNpn, (xr, yc), "collector", mirror=True, label=r"$Q_\mathrm{4}$")
    line_terminal(d, q3.base, r"$V_\mathrm{in1}$", 1.8)
    line_terminal(d, q4.base, r"$V_\mathrm{in2}$", 1.8, right=True)
    # 두 이미터 → 아래 → 가운데 n3 접속점
    yt = q3.emitter.y - 0.7
    d.add(elm.Line().down().at(q3.emitter).toy(yt))
    d.add(elm.Line().right().tox(xm)); n3 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q4.emitter.y))
    # 가운데 세로줄: Q2, Q1, 접지
    d.add(elm.Line().down().at(n3.center).length(0.6))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{2}$")
    line_terminal(d, q2.base, r"$V_\mathrm{b2}$", 0.6)
    d.add(elm.Line().down().at(q2.emitter).length(1.05))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    line_terminal(d, q1.base, r"$V_\mathrm{b1}$", 0.6)
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    return d
