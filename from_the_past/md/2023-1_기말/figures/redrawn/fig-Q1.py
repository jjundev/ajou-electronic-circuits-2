"""2023-1 기말 Q1 — 기준: Q1.md '회로 — Fig Q1(a)', '회로 — Fig Q1(b)'. 답안지 손글씨(커패시터 등)는 그리지 않는다."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12       # 소자 사이 짧은 배선
GAP = 0.2      # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.0   # 두 패널의 V_DD 레일 높이


def vdd_label(d, x_end):
    """레일 오른쪽 끝의 V_DD 라벨."""
    d.add(elm.Label().right().at((x_end + 0.15, RAIL_Y + 0.05)).label(r"$V_{DD}$", halign="left"))


def panel_a(d, x0):
    """x0 = 오른쪽 세로줄(M4, M2, M1)."""
    xl = x0 - 3.2                       # M3 세로줄
    rail(d, (xl - 0.3, RAIL_Y), (x0 + 0.5, RAIL_Y))
    vdd_label(d, x0 + 0.5)
    # 왼쪽 위 M3: 드레인이 레일, 게이트 ← V_b2
    m3 = nmos(d, at=(xl, RAIL_Y), anchor="drain", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b2}$")
    # 오른쪽 세로줄: M4(다이오드 연결), 위 Vout, 아래 Vout, M2, n1, M1, 접지
    m4 = pmos(d, at=(x0, RAIL_Y), anchor="source", label=r"$M_\mathrm{4}$")
    d.add(elm.Line().down().at(m4.drain).length(0.3)); vo1 = dot(d)
    d.add(elm.Line().left().at(m4.gate).length(0.3))
    d.add(elm.Line().down().toy(vo1.center.y))
    d.add(elm.Line().right().tox(x0))
    d.add(elm.Line().down().at(vo1.center).length(0.5)); vo2 = dot(d)
    d.add(elm.Line().right().at(vo2.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vo2.center).length(L))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(m2.source).length(0.35)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.45))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M3 소스 → 긴 세로선 → n1 높이에서 오른쪽 → n1
    d.add(elm.Line().down().at(m3.source).toy(n1.center.y))
    d.add(elm.Line().right().tox(x0))
    # V_in 원 → 가로 R_G → M1 게이트
    # 저항은 왼쪽 끝에서 오른쪽으로 그린다(라벨 "bottom"이 아래에 오도록)
    rg = d.add(Resistor().right().at((m1.gate.x - 1.3, m1.gate.y)).to(m1.gate)
               .label(r"$R_\mathrm{G}$", "bottom", ofst=0.3))
    d.add(elm.Line().left().at(rg.start).length(0.4))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{in}$", "left"))
    return m1.source.y, (xl + x0) / 2


def half_b(d, xo, mirror):
    """(b)의 한쪽: xo = 출력 세로줄(M3/M4, out, M1/M2). 바깥쪽 pmos M5/M6."""
    out = 1 if mirror else -1          # 바깥 쪽 부호
    xp = xo + out * 1.9                # M5/M6 소스 세로줄
    mp = pmos(d, at=(xp, RAIL_Y), anchor="source", mirror=mirror)
    gate_terminal(d, mp.gate, r"$V_\mathrm{b1}$", right=mirror)
    mn = nmos(d, at=(xo, RAIL_Y), anchor="drain", mirror=mirror)
    # M3/M4 게이트 → 바깥으로 짧게 → 위로 레일
    d.add(elm.Line().at(mn.gate).tox(mn.gate.x + out * 0.3))
    d.add(elm.Line().up().toy(RAIL_Y))
    d.add(elm.Line().down().at(mn.source).length(0.35)); o = dot(d)
    # M5/M6 드레인 → 조금 아래 → 안쪽으로 출력 접속점
    d.add(elm.Line().down().at(mp.drain).toy(o.center.y))
    d.add(elm.Line().at((xp, o.center.y)).tox(xo))
    d.add(elm.Line().down().at(o.center).length(0.8))
    mi = nmos(d, at=d.here, anchor="drain", mirror=mirror)
    # V_in 원 → 가로 R_S → 게이트. 저항은 늘 왼쪽 끝에서 오른쪽으로 그려 라벨 "top"이 위에 오게 한다
    x_far = mi.gate.x + out * 1.2
    rs = d.add(Resistor().right().at((min(x_far, mi.gate.x), mi.gate.y)).tox(max(x_far, mi.gate.x))
               .label(r"$R_\mathrm{S}$", "top", ofst=0.25))
    d.add(elm.Line().at((x_far, mi.gate.y)).tox(x_far + out * 0.35))
    d.add(elm.Dot(open=True, radius=OPEN_R)
          .label(r"$V_\mathrm{in2}$" if mirror else r"$V_\mathrm{in1}$", "right" if mirror else "left"))
    return mp, mn, o, mi


def panel_b(d, xc):
    """xc = 가운데(M_SS 세로줄)."""
    xo1, xo2 = xc - 2.0, xc + 2.0
    m5, m3, o1, m1 = half_b(d, xo1, False)
    m6, m4, o2, m2 = half_b(d, xo2, True)
    rail(d, (m5.source.x - 0.3, RAIL_Y), (m6.source.x + 0.3, RAIL_Y))
    vdd_label(d, m6.source.x + 0.3)
    # 소자 라벨
    d.add(elm.Label().right().at((xo1 + 0.3, m3.center.y)).label(r"$M_\mathrm{3}$", halign="left"))
    d.add(elm.Label().right().at((xo2 - 0.3, m4.center.y)).label(r"$M_\mathrm{4}$", halign="right"))
    d.add(elm.Label().right().at((m5.gate.x + 0.05, m5.drain.y - 0.55)).label(r"$M_\mathrm{5}$", halign="center"))
    d.add(elm.Label().right().at((m6.gate.x - 0.05, m6.drain.y - 0.55)).label(r"$M_\mathrm{6}$", halign="center"))
    d.add(elm.Label().right().at((xo1 + 0.3, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xo2 - 0.3, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(o1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(o2.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Label().right().at((xc, o1.center.y)).label(r"$V_\mathrm{out}$"))
    # 두 소스 → 아래 → 가운데 n3 → M_SS → 접지
    ybot = m1.source.y - 0.4
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xc)); n3 = dot(d)
    d.add(elm.Line().right().tox(xo2))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Line().down().at(n3.center).length(L))
    mss = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xc + 0.3, mss.center.y)).label(r"$M_\mathrm{SS}$", halign="left"))
    gate_terminal(d, mss.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Ground().at(mss.source).scale(0.8))
    return mss.source.y


def draw():
    d = new_drawing()
    ya, xa = panel_a(d, 0)
    yb = panel_b(d, 11.6)
    cap_y = min(ya, yb) - 1.2
    caption(d, (xa - 0.15, cap_y), "(a)")
    caption(d, (11.6 - 0.15, cap_y), "(b)")
    return d
