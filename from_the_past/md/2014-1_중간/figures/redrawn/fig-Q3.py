"""2014-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import dot, new_drawing, nmos

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VDD_H = 0.32    # 0.8배 T 전원 기호 높이
TOP = 0.0       # T 전원 기호 위 끝 높이


def dashed_box(d, x0, y0, x1, y1):
    """점선 직사각형 (도선이 아닌 묶음 표시)."""
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        d.add(elm.Line().at(a).to(b).linestyle("--"))


def draw():
    d = new_drawing()
    xl, x1 = 0.0, 3.5               # I_REF·M_REF 줄, M1 줄
    # 왼쪽 세로줄 위→아래: V_DD T 기호, I_REF(화살표 아래), X 위 접속점, M_REF, 접지
    d.add(elm.Vdd().at((xl, TOP - VDD_H)).scale(0.8).label(r"$V_{DD}$", "right", ofst=GAP))
    iref = d.add(elm.SourceI().down().at((xl, TOP - VDD_H)).length(1.6).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).length(0.45)); xt = dot(d)
    d.add(elm.Line().down().at(xt.center).length(0.35))
    mref = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Ground().at(mref.source).scale(0.8))
    d.add(elm.Label().right().at((xl - 0.35, mref.center.y - 0.2)).label(r"$M_\mathrm{REF}$", halign="right"))
    # X 위 접속점 → 오른쪽 → 아래로 X 게이트 접속점 (다이오드 연결) → M1 게이트
    xg = mref.gate.x + 0.4
    d.add(elm.Line().right().at(xt.center).tox(xg))
    d.add(elm.Line().down().toy(mref.gate.y)); xgd = dot(d)
    d.add(elm.Line().left().at(xgd.center).tox(mref.gate))
    m1 = nmos(d, at=(x1, mref.drain.y), anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Line().right().at(xgd.center).tox(m1.gate))
    d.add(elm.Label().right().at(((xg + m1.gate.x) / 2, mref.gate.y - 0.27)).label(r"$X$", valign="top"))
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M1 드레인 선: V_DD 높이의 선 끝에서 아래로 I_copy 화살표, M1 드레인까지
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at((x1, TOP)).length(1.0)
          .label(r"$I_\mathrm{copy}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().toy(m1.drain.y))
    # 점선 상자: X 위 접속점 바로 위부터 두 접지 아래까지, 오른쪽 끝 안에 "Current Mirror"
    xr = x1 + 4.15
    dashed_box(d, xl - 2.3, xt.center.y + 0.35, xr, mref.source.y - 0.75)
    d.add(elm.Label().right().at((xr - 0.35, m1.center.y + 0.3)).label(r"$\mathrm{Current}$", halign="right"))
    d.add(elm.Label().right().at((xr - 0.35, m1.center.y - 0.35)).label(r"$\mathrm{Mirror}$", halign="right"))
    return d
