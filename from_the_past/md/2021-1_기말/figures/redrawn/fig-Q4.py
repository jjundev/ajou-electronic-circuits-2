"""2021-1 기말 Q4 — 기준: Q4.md '회로 — Fig Q4'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, new_drawing, nmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 4.35, 11.0
    xw = 2.2          # X → M2 게이트 선과 M1 게이트 → V_F 선이 내려가는 x
    rail(d, (xl - 0.5, rail_y), (xr + 0.5, rail_y))
    d.add(elm.Label().right().at((xr + 0.7, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 왼쪽 세로줄 위→아래: R_D, X 접속점, M1 (게이트 오른쪽), 아래로 내려가 왼쪽 V_in 원
    rd = d.add(Resistor().down().at((xl, rail_y)).length(2.4)
               .label(r"$R_\mathrm{D}$", "top", ofst=GAP))
    d.add(elm.Line().down().at(rd.end).length(0.25)); x = dot(d)
    d.add(elm.Line().down().at(x.center).length(1.35))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True)
    # X: 접속점 아래, M1 드레인 선 오른쪽
    d.add(elm.Label().right().at((xl + 0.3, x.center.y - 0.6)).label(r"$X$", halign="left"))
    # M1: 왼쪽, 소스 화살표 높이
    d.add(elm.Label().right().at((xl - 0.3, m1.source.y + 0.35)).label(r"$M_\mathrm{1}$", halign="right"))
    # 오른쪽 세로줄: M2 (드레인 위로 레일), I_out 화살표, Laser 상자, V_F 접속점, R_M, 접지
    m2 = nmos(d, at=(xr, rail_y - 0.25), anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().up().at(m2.drain).toy(rail_y))
    box_top, box_bot = m2.source.y - 2.6, m2.source.y - 4.8
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at(m2.source).length(1.55)
          .label(r"$I_\mathrm{out}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().toy(box_top))
    # Laser 상자: 전용 기호가 없어 선 네 개로 그린다
    corners = [(xr - 1.6, box_top), (xr + 1.6, box_top), (xr + 1.6, box_bot), (xr - 1.6, box_bot)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        d.add(elm.Line().at(a).to(b))
    d.add(elm.Label().right().at((xr, (box_top + box_bot) / 2)).label(r"$\mathrm{Laser}$", halign="center"))
    d.add(elm.Line().down().at((xr, box_bot)).length(0.5)); vf = dot(d)
    # V_F: 접속점 오른쪽 아래
    d.add(elm.Label().right().at((xr + 0.25, vf.center.y - 0.35)).label(r"$V_\mathrm{F}$", halign="left"))
    rm = d.add(Resistor().down().at(vf.center).length(2.0).label(r"$R_\mathrm{M}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(rm.end).scale(0.8))
    # X → 오른쪽 → 위로 M2 게이트 높이 → 오른쪽 M2 게이트
    d.add(elm.Line().right().at(x.center).tox(xw))
    d.add(elm.Line().up().toy(m2.gate))
    d.add(elm.Line().right().tox(m2.gate))
    # M1 게이트 → 오른쪽 → 아래로 V_F 높이 → 오른쪽 V_F 접속점
    d.add(elm.Line().right().at(m1.gate).tox(xw))
    d.add(elm.Line().down().toy(vf.center))
    d.add(elm.Line().right().tox(vf.center))
    # M1 소스 → 아래로 V_F 높이 → 왼쪽 V_in 원
    d.add(elm.Line().down().at(m1.source).toy(vf.center))
    d.add(elm.Line().left().length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{in}$", "left", ofst=GAP))
    return d
