"""2023-1 중간 Q4 — 기준: Q4.md '회로 — Fig Q4'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing, nmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 3.8, 9.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, rail_y), (xr + 0.35, rail_y))
    # V_DD: 레일 오른쪽 끝 오른쪽, 조금 위
    d.add(elm.Label().right().at((xr + 0.6, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 부하 저항: 레일 → 출력 접속점. R_D는 왼쪽, R_D + ΔR_D는 오른쪽
    # 아래로 그리는 소자의 라벨: loc="top"이면 왼쪽, "bottom"이면 오른쪽
    rd1 = d.add(Resistor().down().at((xl, rail_y)).length(2.6).label(r"$R_\mathrm{D}$", "top", ofst=GAP))
    out1 = dot(d)
    rd2 = d.add(Resistor().down().at((xr, rail_y)).length(2.6)
                .label(r"$R_\mathrm{D} + \Delta R_\mathrm{D}$", "bottom", ofst=GAP))
    out2 = dot(d)
    # 출력: 두 원이 바깥쪽을 향한다
    d.add(elm.Line().left().at(out1.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$v_\mathrm{out1}$", "left", ofst=GAP))
    d.add(elm.Line().right().at(out2.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$v_\mathrm{out2}$", "right", ofst=GAP))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.6))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(out2.center).length(0.6))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 소스 → 아래 → 가운데 P 접속점
    ybot = m1.source.y - 0.45
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Label().right().at((xm, ybot + 0.25)).label(r"$P$", valign="bottom"))
    # 테일: M3, 접지
    d.add(elm.Line().down().at(p.center).length(0.45))
    m3 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(m3.source).scale(0.8))
    return d
