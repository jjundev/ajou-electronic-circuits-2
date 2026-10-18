"""2014-1 중간 Q4 — 기준: Q4.md '회로 — Fig Q4(a)', '회로 — Fig Q4(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, caption, dot, gate_terminal, new_drawing

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"
VDD_H = 0.32    # 0.8배 T 전원 기호 높이
TOP = 0.0       # T 전원 기호 위 끝 높이
CAP_Y = -7.6    # 캡션 높이


def npn(d, at, anchor, label=None):
    """npn 보통 방향: 베이스 왼쪽, 컬렉터 위, 이미터 아래·화살표 바깥."""
    e = elm.BjtNpn().right().anchor(anchor).at(at)
    if label:
        e = e.label(label, loc="right")
    return d.add(e)


def supply_i1_vout(d, x):
    """위→아래: V_CC T 기호, I_1 전류원(화살표 아래), Vout 접속점(오른쪽 V_out 원). 접속점을 돌려준다."""
    d.add(elm.Vdd().at((x, TOP - VDD_H)).scale(0.8).label(VCC, "right", ofst=GAP))
    i1 = d.add(elm.SourceI().down().at((x, TOP - VDD_H)).length(1.3).scale(0.6)
               .label(r"$I_\mathrm{1}$", "top", ofst=0.3))
    d.add(elm.Line().down().at(i1.end).length(0.2)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    return vout


def panel_a(d, x0):
    # 왼쪽 세로줄 위→아래: V_CC, I_1, Vout 접속점, Q1, n1 접속점, Q2, 접지
    vout = supply_i1_vout(d, x0)
    d.add(elm.Line().down().at(vout.center).length(0.3))
    q1 = npn(d, d.here, "collector", r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(q1.emitter).length(0.7)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.45))
    q2 = npn(d, d.here, "collector", r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q2.emitter).scale(0.8))
    # Q3: 오른쪽, Q1보다 조금 아래. pnp 좌우 반전(베이스 오른쪽, 이미터 왼쪽 위, 컬렉터 왼쪽 아래)
    xq = x0 + 3.4
    q3 = d.add(elm.BjtPnp().right().reverse().anchor("collector").at((xq, n1.center.y + 0.15)))
    d.add(elm.Label().right().at((xq - 0.35, q3.center.y - 0.2)).label(r"$Q_\mathrm{3}$", halign="right"))
    d.add(elm.Line().up().at(q3.emitter).length(0.35))
    d.add(elm.Vdd().scale(0.8).label(VCC, "right", ofst=GAP))
    gate_terminal(d, q3.base, r"$V_\mathrm{b3}$", right=True)
    # Q3 컬렉터 → n1 높이 → 왼쪽 긴 가로선 → n1 접속점
    d.add(elm.Line().down().at(q3.collector).toy(n1.center))
    d.add(elm.Line().left().tox(n1.center))
    caption(d, (x0 + 1.6, CAP_Y), "(a)")


def panel_b(d, x0):
    # 한 세로줄 위→아래: V_CC, I_1, Vout 접속점, Q2, Q1, 접지 (위가 입력 소자)
    vout = supply_i1_vout(d, x0)
    d.add(elm.Line().down().at(vout.center).length(0.3))
    q2 = npn(d, d.here, "collector", r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Line().down().at(q2.emitter).length(0.6))
    q1 = npn(d, d.here, "collector", r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    caption(d, (x0 - 0.3, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 9.0)
    return d
