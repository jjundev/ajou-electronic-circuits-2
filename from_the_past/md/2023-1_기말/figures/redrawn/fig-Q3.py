"""2023-1 기말 Q3 — 기준: Q3.md '회로 — Fig Q3'. 답안지 손글씨("open", R_L, M4 게이트 선 아래 저항·접지 등)는 그리지 않는다."""
import schemdraw.elements as elm
from schem_style import DOT_R, Resistor, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
BOX_W, BOX_H = 2.7, 1.2   # Laser 상자


def draw():
    d = new_drawing()
    x5, x6, rail_y = 0, 2.8, 0
    x1 = x6 + 3.0
    rail(d, (x5 - 0.3, rail_y), (x1 + 0.6, rail_y))
    d.add(elm.Label().right().at((x1 + 0.75, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 위 pmos 셋: M5(좌우 반전), M6(다이오드 연결), M1
    m5 = pmos(d, at=(x5, rail_y), anchor="source", mirror=True, label=r"$M_\mathrm{5}$")
    m6 = pmos(d, at=(x6, rail_y), anchor="source", label=r"$M_\mathrm{6}$")
    m1 = pmos(d, at=(x1, rail_y), anchor="source", label=r"$M_\mathrm{1}$")
    # M5·M6 게이트 공통선, 가운데 접속점 → 아래 → n1 (다이오드 연결)
    d.add(elm.Line().right().at(m5.gate).tox(m6.gate))
    xg = (m5.gate.x + m6.gate.x) / 2
    d.add(elm.Dot(radius=DOT_R).at((xg, m5.gate.y)))
    y_n1 = m6.drain.y - 0.35
    d.add(elm.Line().down().at((xg, m5.gate.y)).toy(y_n1))
    d.add(elm.Line().right().tox(x6))
    d.add(elm.Line().down().at(m6.drain).toy(y_n1)); n1 = dot(d)
    # 왼쪽: M5 드레인 → X 접속점 → M3
    y_x = y_n1 - 0.5
    d.add(elm.Line().down().at(m5.drain).toy(y_x)); xdot = dot(d)
    d.add(elm.Label().right().at((x5 - 0.45, y_x)).label(r"$X$", halign="right"))
    # X → 오른쪽(n1–M4 세로선과 점 없이 교차) → 위 → M1 게이트
    xt = x1 - BOX_W / 2 - 0.4
    d.add(elm.Line().right().at(xdot.center).tox(xt))
    d.add(elm.Line().up().toy(m1.gate.y))
    d.add(elm.Line().right().tox(m1.gate.x))
    # 아래 nmos 쌍: M3 보통, M4 좌우 반전
    d.add(elm.Line().down().at(xdot.center).length(0.9))
    m3 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Line().down().at(n1.center).toy(m3.drain.y))
    m4 = nmos(d, at=d.here, anchor="drain", mirror=True, label=r"$M_\mathrm{4}$")
    # 오른쪽: M1 드레인 → I_out 화살표 → Laser 상자 → n3
    y_n3 = m4.gate.y
    box_top = y_n3 + 0.3 + BOX_H
    d.add(elm.Line().down().at(m1.drain).length(0.25))
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.3).down().length(0.4)
          .label(r"$I_\mathrm{out}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().toy(box_top))
    # 전용 기호가 없으므로 선 네 개로 상자를 그린다
    xa, xb, yb = x1 - BOX_W / 2, x1 + BOX_W / 2, box_top - BOX_H
    for p, q in (((xa, box_top), (xb, box_top)), ((xb, box_top), (xb, yb)),
                 ((xb, yb), (xa, yb)), ((xa, yb), (xa, box_top))):
        d.add(elm.Line().at(p).to(q))
    d.add(elm.Label().right().at((x1, box_top - BOX_H / 2)).label(r"$\mathrm{Laser}$"))
    d.add(elm.Line().down().at((x1, box_top - BOX_H)).toy(y_n3)); n3 = dot(d)
    d.add(elm.Line().left().at(n3.center).tox(m4.gate.x))
    rm = d.add(Resistor().down().at(n3.center).length(1.3).label(r"$R_\mathrm{M}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(rm.end).scale(0.8))
    # 두 소스 → 아래 → 가운데 n4 → I_SS(화살표 아래) → 접지
    ybot = m3.source.y - 0.35
    xm = (x5 + x6) / 2
    d.add(elm.Line().down().at(m3.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n4 = dot(d)
    d.add(elm.Line().right().tox(x6))
    d.add(elm.Line().up().toy(m4.source.y))
    iss = d.add(elm.SourceI().down().at(n4.center).length(1.3).scale(0.6)
                .label(r"$I_\mathrm{SS}$", "bottom", ofst=0.4))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    return d
