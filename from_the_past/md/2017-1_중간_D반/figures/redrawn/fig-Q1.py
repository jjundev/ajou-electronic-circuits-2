"""2017-1 중간 (D반) Q1 — 기준: Q1.md '회로 — Fig Q1(a)', '회로 — Fig Q1(b)'."""
import schemdraw.elements as elm
from schem_style import GATE_LEAD, OPEN_R, caption, dot, gate_terminal, new_drawing, nmos

GAP = 0.2       # 소자 라벨과 기호 사이 간격
OUT_Y = 6.9     # out 개방 원 높이
CAP_Y = -0.6    # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def out_terminal(d, x, y_top):
    """세로선 위 끝의 out 개방 원과, 도선 오른쪽의 ┌ 꺾인 R_out 화살표(아래 방향)."""
    d.add(elm.Line().up().at((x, y_top)).toy(OUT_Y))
    dot(d, open_=True)
    xa = x + 0.35
    d.add(elm.Line().right().at((xa, OUT_Y)).length(0.3))
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at((xa, OUT_Y)).length(0.9))
    d.add(elm.Label().right().at((xa + 0.4, OUT_Y + 0.05)).label(r"$R_\mathrm{out}$", halign="left"))


def panel_a(d, x0):
    x = x0 + GATE_LEAD + 0.92          # 세 nmos의 드레인·소스 줄
    m1 = nmos(d, at=(x, 6.0), anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Line().down().at(m1.source).length(0.15))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().down().at(m2.source).length(0.15))
    m3 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{3}$")
    d.add(elm.Ground().at(m3.source).scale(0.8))
    for m, name in ((m1, "1"), (m2, "2"), (m3, "3")):
        gate_terminal(d, m.gate, rf"$V_\mathrm{{b{name}}}$")
    out_terminal(d, x, m1.drain.y)
    caption(d, (x, CAP_Y), "(a)")


def panel_b(d, x0):
    x1 = x0 + GATE_LEAD + 0.75         # Q1·Q2 줄
    x3 = x1 + 3.6                      # Q3 줄
    q1 = bjt(d, elm.BjtNpn, (x1, 5.5), "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(q1.emitter).length(0.45)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.3))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{2}$")
    d.add(elm.Ground().at(q2.emitter).scale(0.8))
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{b2}$")
    out_terminal(d, x1, q1.collector.y)
    # Q3: Q1 높이, pnp 좌우 반전. 이미터 → V_CC, 베이스 → V_b3, 컬렉터 → n1
    q3 = bjt(d, elm.BjtPnp, (x3, q1.collector.y), "emitter", mirror=True)
    d.add(elm.Line().up().at(q3.emitter).length(0.35))
    d.add(elm.Vdd().scale(0.8).label(r"$V_{CC}$", "right", ofst=GAP))
    gate_terminal(d, q3.base, r"$V_\mathrm{b3}$", right=True)
    d.add(elm.Line().down().at(q3.collector).toy(n1.center.y))
    d.add(elm.Line().left().tox(x1))
    d.add(elm.Label().right().at((x3 - 0.35, q3.center.y - 0.3)).label(r"$Q_\mathrm{3}$", halign="right"))
    caption(d, ((x1 + x3) / 2, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 7.0)
    return d
