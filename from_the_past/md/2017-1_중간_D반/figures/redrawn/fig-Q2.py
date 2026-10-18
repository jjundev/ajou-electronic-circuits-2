"""2017-1 중간 (D반) Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""
import schemdraw.elements as elm
from schem_style import Resistor, caption, dot, new_drawing

GAP = 0.2       # 소자 라벨과 기호 사이 간격
TOP = 6.8       # V_CC T 기호 아래 끝 높이
CAP_Y = 0.75    # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽), 컬렉터 위, 이미터 아래."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def panel(d, x0, rp_on_ref):
    """rp_on_ref=False면 (a): R_P가 Q1 이미터 아래. True면 (b): R_P가 Q_REF 이미터 아래."""
    xref = x0
    xdio = xref + 1.3      # 다이오드 연결선
    xq1 = xref + 3.1       # Q1 줄
    # 왼쪽 세로줄: V_CC, I_REF, 위 n1 접속점, Q_REF
    d.add(elm.Vdd().at((xref, TOP)).scale(0.8).label(r"$V_{CC}$", "right", ofst=GAP))
    iref = d.add(elm.SourceI().down().at((xref, TOP)).length(1.4).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.3))
    d.add(elm.Line().down().at(iref.end).length(0.2)); n1_top = dot(d)
    d.add(elm.Line().down().at(n1_top.center).length(0.35))
    qref = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True)
    d.add(elm.Label().right().at((xref - 0.35, qref.center.y + 0.1)).label(r"$Q_\mathrm{REF}$", halign="right"))
    # 베이스 공통선 (아래 n1 접속점) + 다이오드 연결
    d.add(elm.Line().at(qref.base).tox(xdio)); n1_bot = dot(d)
    d.add(elm.Line().at(n1_top.center).tox(xdio))
    d.add(elm.Line().down().toy(n1_bot.center.y))
    q1 = bjt(d, elm.BjtNpn, (xq1, qref.collector.y), "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().at(n1_bot.center).tox(q1.base))
    # I_1: Q1 컬렉터 위 선 끝에서 아래로 들어가는 화살표
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at((xq1, TOP - 0.2)).length(1.0)
          .label(r"$I_\mathrm{1}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().toy(q1.collector.y))
    # 이미터 쪽: R_P와 접지
    rp_from, gnd_q = (qref, q1) if rp_on_ref else (q1, qref)
    d.add(elm.Line().down().at(rp_from.emitter).length(0.2))
    rp = d.add(Resistor().down().length(1.3).label(r"$R_\mathrm{P}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(rp.end).scale(0.8))
    d.add(elm.Ground().at(gnd_q.emitter).scale(0.8))
    return (xref + xq1) / 2


def draw():
    d = new_drawing()
    xa = panel(d, 0, rp_on_ref=False)
    caption(d, (xa, CAP_Y), "(a)")
    xb = panel(d, 7.2, rp_on_ref=True)
    caption(d, (xb, CAP_Y), "(b)")
    return d
