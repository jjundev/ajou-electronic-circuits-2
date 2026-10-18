"""2013-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)', '회로 — Fig Q2(c)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # 세 패널 레일 높이
CAP_Y = -9.2    # 캡션 높이
GND_Y = -6.9    # 접지 기호 위 끝 높이 (세 패널 공통)
VCC = r"$V_{CC}$"
WL_N = r"(\frac{W}{L})_\mathrm{n}"   # 원본처럼 괄호 안 분수
WL_P = r"(\frac{W}{L})_\mathrm{p}"


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def ground_at(d, xy):
    """xy에서 세로선을 GND_Y까지 내리고 접지."""
    d.add(elm.Line().down().at(xy).toy(GND_Y))
    d.add(elm.Ground().scale(0.8))


def rail_label(d, x, text, left=False):
    """레일 끝 위의 전원 라벨 (left면 왼쪽 끝에서 왼쪽으로)."""
    d.add(elm.Label().right().at((x, RAIL_Y + 0.15))
          .label(text, halign="right" if left else "left", valign="bottom"))


def panel_a(d, x0):
    xl, xr = x0 + 3.2, x0 + 9.2          # 왼쪽 세로줄, 오른쪽 세로줄
    yb = RAIL_Y - 1.8                    # 베이스 높이
    rail(d, (xl - 0.4, RAIL_Y), (xr + 0.9, RAIL_Y))
    rail_label(d, xr + 1.1, VCC)
    # Q_REF: pnp 좌우 반전, Q2: pnp 보통. 이미터에서 세로선이 위로 레일
    qref = bjt(d, elm.BjtPnp, (xl + 0.752, yb), "base", mirror=True)
    q2 = bjt(d, elm.BjtPnp, (xr - 0.752, yb), "base", label=r"$Q_\mathrm{2}$")
    for q in (qref, q2):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.35, yb + 0.1)).label(r"$Q_\mathrm{REF}$", halign="right"))
    # 베이스 공통선과 X 접속점
    xx = x0 + 5.4
    d.add(elm.Line().at(qref.base).tox(xx)); x = dot(d)
    d.add(elm.Line().at(x.center).tox(q2.base))
    d.add(elm.Label().right().at((xx + 0.3, yb - 0.3)).label(r"$X$", halign="left", valign="top"))
    # 컬렉터 접속점 → 오른쪽 → 위로 X (다이오드 연결)
    d.add(elm.Line().down().at(qref.collector).toy(RAIL_Y - 3.5)); c = dot(d)
    d.add(elm.Line().right().at(c.center).tox(xx))
    d.add(elm.Line().up().toy(yb))
    iref = d.add(elm.SourceI().down().at(c.center).length(2.2).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    ground_at(d, iref.end)
    # 오른쪽 세로줄: Q2 컬렉터 → Vout 접속점 → Q1 → 접지
    d.add(elm.Line().down().at(q2.collector).toy(RAIL_Y - 3.4)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(2.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    q1 = bjt(d, elm.BjtNpn, (xr, RAIL_Y - 4.5), "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().up().at(q1.collector).toy(vout.center.y))
    d.add(elm.Line().left().at(q1.base).length(1.0))
    gate_terminal(d, d.here, r"$v_\mathrm{in}$", open_=True)
    ground_at(d, q1.emitter)
    caption(d, (x0 + 5.6, CAP_Y), "(a)")


def panel_b(d, x0):
    xi, xc, x4 = x0 + 2.9, x0 + 6.7, x0 + 11.0   # I_REF·Q1 줄, Q2·Q3 줄, Q4 줄
    rail(d, (xi - 0.6, RAIL_Y), (x4 + 0.4, RAIL_Y))
    rail_label(d, x4 + 0.6, VCC)
    # 왼쪽 세로줄: I_REF(화살표 아래), n1 접속점, Q1(npn 좌우 반전), 접지
    iref = d.add(elm.SourceI().down().at((xi, RAIL_Y)).length(2.6).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).length(0.6)); n1 = dot(d)
    ybl = RAIL_Y - 4.6                   # 아래 베이스 높이
    q1 = bjt(d, elm.BjtNpn, (xi + 0.752, ybl), "base", mirror=True)
    d.add(elm.Line().up().at(q1.collector).toy(n1.center.y))
    d.add(elm.Label().right().at((xi - 0.35, q1.emitter.y + 0.1)).label(r"$3A_\mathrm{E}$", halign="right"))
    ground_at(d, q1.emitter)
    # n1 → 오른쪽 → 아래로 베이스 접속점, 베이스 공통선 → Q2
    xj = xi + 1.6
    d.add(elm.Line().right().at(n1.center).tox(xj))
    d.add(elm.Line().down().toy(ybl)); bj = dot(d)
    d.add(elm.Line().left().at(bj.center).tox(q1.base))
    q2 = bjt(d, elm.BjtNpn, (xc - 0.752, ybl), "base", label=r"$2A_\mathrm{E}$")
    d.add(elm.Line().at(bj.center).tox(q2.base))
    ground_at(d, q2.emitter)
    # Q3: pnp 좌우 반전, 가운데 위. Q4: pnp 보통, 오른쪽
    ybu = RAIL_Y - 1.45                  # 위 베이스 높이
    q3 = bjt(d, elm.BjtPnp, (xc + 0.752, ybu), "base", mirror=True)
    q4 = bjt(d, elm.BjtPnp, (x4 - 0.752, ybu), "base", label=r"$9A_\mathrm{E}$")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    d.add(elm.Label().right().at((xc - 0.35, ybu + 0.1)).label(r"$5A_\mathrm{E}$", halign="right"))
    # Q2 컬렉터 ↑ n2 접속점 ↑ Q3 컬렉터, n2 → 오른쪽 → 위로 위 베이스 접속점
    d.add(elm.Line().up().at(q2.collector).toy(RAIL_Y - 2.9)); n2 = dot(d)
    d.add(elm.Line().up().at(n2.center).toy(q3.collector.y))
    xk = xc + 1.6
    d.add(elm.Line().right().at(n2.center).tox(xk))
    d.add(elm.Line().up().toy(ybu)); bk = dot(d)
    d.add(elm.Line().left().at(bk.center).tox(q3.base))
    d.add(elm.Line().right().at(bk.center).tox(q4.base))
    # Q4 컬렉터 → 아래 → I_copy 화살표 → 선 끝
    d.add(elm.Line().down().at(q4.collector).length(1.0))
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().length(1.3)
          .label(r"$I_\mathrm{copy}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().length(0.25))
    caption(d, (x0 + 6.4, CAP_Y), "(b)")


def panel_c(d, x0):
    xi, xc, x3 = x0 + 2.1, x0 + 6.9, x0 + 12.1   # I_REF·M_REF 줄, M1·M2 줄, M3·M4 줄
    rail(d, (xi - 0.1, RAIL_Y), (x3 + 0.4, RAIL_Y))
    rail_label(d, xi - 0.1, r"$V_{DD}$", left=True)
    # 왼쪽 세로줄: I_REF(화살표 아래), n1 접속점, M_REF(nmos 좌우 반전), 접지
    iref = d.add(elm.SourceI().down().at((xi, RAIL_Y)).length(2.8).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).length(0.45)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.6))
    mref = nmos(d, at=d.here, anchor="drain", mirror=True)
    ground_at(d, mref.source)
    d.add(elm.Label().right().at((xi + 0.4, GND_Y - 0.45)).label(r"$M_\mathrm{REF}$", halign="left"))
    d.add(elm.Label().right().at((xi - 0.35, mref.center.y)).label("$" + WL_N + "$", halign="right"))
    # n1 → 오른쪽 → 아래로 M_REF 게이트 접속점 → 게이트 가로선 → 둘째 게이트 접속점 → M1 게이트
    xg = mref.gate.x + 0.4
    d.add(elm.Line().right().at(n1.center).tox(xg))
    d.add(elm.Line().down().toy(mref.gate.y)); g1 = dot(d)
    d.add(elm.Line().left().at(g1.center).tox(mref.gate))
    m1 = nmos(d, at=(xc, mref.drain.y), anchor="drain", label="$5" + WL_N + "$")
    xg2 = m1.gate.x - 0.9
    d.add(elm.Line().right().at(g1.center).tox(xg2)); g2 = dot(d)
    d.add(elm.Line().right().at(g2.center).tox(m1.gate))
    ground_at(d, m1.source)
    # M2: pmos 좌우 반전, 가운데 위. M3: pmos 보통, 오른쪽 위. 소스에서 세로선이 위로 레일
    ys = RAIL_Y - 0.6
    m2 = pmos(d, at=(xc, ys), anchor="source", mirror=True)
    m3 = pmos(d, at=(x3, ys), anchor="source", label="$2" + WL_P + "$")
    for m in (m2, m3):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    d.add(elm.Label().right().at((xc - 0.35, m2.center.y)).label("$" + WL_P + "$", halign="right"))
    # M1 드레인 ↑ n2 접속점 ↑ M2 드레인, n2 → 오른쪽 → 위로 M2 게이트 접속점 → M3 게이트
    d.add(elm.Line().down().at(m2.drain).length(0.35)); n2 = dot(d)
    d.add(elm.Line().down().at(n2.center).toy(m1.drain.y))
    xk = m2.gate.x + 0.4
    d.add(elm.Line().right().at(n2.center).tox(xk))
    d.add(elm.Line().up().toy(m2.gate.y)); g3 = dot(d)
    d.add(elm.Line().left().at(g3.center).tox(m2.gate))
    d.add(elm.Line().right().at(g3.center).tox(m3.gate))
    # 오른쪽 세로줄: M3 → out 접속점 → M4 → 접지
    m4 = nmos(d, at=(x3, m1.drain.y), anchor="drain", label="$3" + WL_N + "$")
    d.add(elm.Line().down().at(m3.drain).toy(n2.center.y)); out = dot(d)
    d.add(elm.Line().down().at(out.center).toy(m4.drain.y))
    ground_at(d, m4.source)
    # out → 오른쪽 → I_copy 화살표 → 선 끝
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).right().at(out.center).length(2.4)
          .label(r"$I_\mathrm{copy}$", "bottom", ofst=GAP))
    d.add(elm.Line().right().length(0.3))
    # 둘째 게이트 접속점 ↓ 맨 아래 긴 가로선 → M4 왼쪽에서 위로 M4 게이트
    ylow = GND_Y - 0.9
    xm4 = m4.gate.x - 0.6
    d.add(elm.Line().down().at(g2.center).toy(ylow))
    d.add(elm.Line().right().tox(xm4))
    d.add(elm.Line().up().toy(m4.gate.y))
    d.add(elm.Line().right().tox(m4.gate))
    caption(d, (x0 + 7.2, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 15.2)
    panel_c(d, 31.4)
    return d
