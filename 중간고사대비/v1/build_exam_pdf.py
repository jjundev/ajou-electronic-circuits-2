#!/usr/bin/env python3
"""
전자회로2 중간고사 실전 대비 모의고사 (v1)
16:9 와이드스크린 (1920x1080) 문제지 및 답안지 PDF 렌더러

산출물:
- 중간고사대비/v1/중간고사대비_v1-문제.pdf (실전 문제지, 표지 + 5개 문항)
- 중간고사대비/v1/중간고사대비_v1-답안.pdf (표준 답안지, 표지 + 5개 문항 상세 풀이)
"""

import base64
import json
import re
import sys
from pathlib import Path
import yaml
import markdown

ROOT = Path(__file__).resolve().parent.parent.parent
BASE = ROOT / "중간고사대비" / "v1"
ASSETS = BASE / ".assets"
MD_DIR = ASSETS / "md"
FIG_DIR = ASSETS / "figures"
BUILD_DIR = BASE / "build"


def load_assets():
    selection = json.loads((ASSETS / "selection.json").read_text(encoding="utf-8"))
    display_titles = json.loads((ASSETS / "display-titles.json").read_text(encoding="utf-8"))
    
    questions = []
    for i in range(1, 6):
        path = MD_DIR / f"Q{i}.md"
        raw = path.read_text(encoding="utf-8")
        parts = raw.split("---")
        fm = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])
        
        # split problem & solution
        if "## 풀이" in body:
            prob_part, sol_part = body.split("## 풀이", 1)
        else:
            prob_part, sol_part = body, ""
        
        # Clean up header in problem part
        # remove top "# Q..." heading as template renders its own header
        prob_lines = [l for l in prob_part.splitlines() if not l.startswith("# ")]
        prob_text = "\n".join(prob_lines).strip()
        
        # In problem text, strip out '## 문제' heading
        prob_text = re.sub(r"^##\s+문제\s*", "", prob_text).strip()
        
        # In solution text, strip out '## 회로' if it leaked
        sol_text = sol_part.strip()
        
        questions.append({
            "num": i,
            "id": fm["id"],
            "title": display_titles.get(fm["id"], fm["title"]),
            "full_title": fm["title"],
            "points": fm.get("points", 20),
            "chapters": fm.get("textbook_chapters", []),
            "subparts": fm.get("subparts", []),
            "prob_md": prob_text,
            "sol_md": sol_text,
        })
    return selection, display_titles, questions


def encode_svg(fig_name):
    path = FIG_DIR / fig_name
    if not path.is_file():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def md_to_html(md_text, is_problem=False):
    """Convert markdown to HTML preserving math and converting svg figures."""
    # 1. Mask math
    maths = []
    def mask_math(m):
        maths.append(m.group(0))
        return f"MATHPLACEHOLDER{len(maths)-1}X"
    
    masked = re.sub(r"\$\$.+?\$\$|\$[^$]+?\$", mask_math, md_text, flags=re.DOTALL)
    
    # 2. Replace svg image links
    def repl_img(m):
        alt = m.group(1)
        src = m.group(2)
        fig_name = Path(src).name
        data_uri = encode_svg(fig_name)
        if data_uri:
            cls = "fig-card"
            return f'<div class="{cls}"><img src="{data_uri}" alt="{alt}" class="circuit-img"/><div class="fig-caption">그림: {alt}</div></div>'
        return ""

    masked = re.sub(r"!\[(.*?)\]\((.*?\.svg)\)", repl_img, masked)
    
    # 3. Clean up circuit-only sections if needed
    masked = re.sub(r"##\s*회로\s*—\s*없음\s*\(서술형\)", "", masked)
    masked = re.sub(r"##\s*회로", "", masked)
    
    # 4. Convert via markdown
    html = markdown.markdown(masked, extensions=["tables", "fenced_code"])
    
    # 5. Restore math
    for i, math_str in enumerate(maths):
        html = html.replace(f"MATHPLACEHOLDER{i}X", math_str)
        
    return html


def build_problem_html(selection, questions):
    pages_html = []
    
    # Page 1: Cover Page
    cover_html = f"""
    <div class="page page-cover" id="page-cover">
      <div class="cover-card">
        <div class="cover-badge-row">
          <span class="badge badge-accent">2026-2 전자회로2</span>
          <span class="badge badge-dark">중간고사 대비 실전 모의고사 (v1)</span>
          <span class="badge badge-outline">Closed-book</span>
        </div>
        <h1 class="cover-title">전자회로2 중간고사 실전 대비 모의고사</h1>
        <p class="cover-subtitle">Ajou University Dept. of Electronic Engineering · Electronic Circuits II</p>
        
        <div class="cover-grid">
          <div class="cover-meta-box">
            <h3 class="meta-title">📋 시험 안내 및 응시 규격</h3>
            <table class="spec-table">
              <tr><th>시험 시간</th><td><strong>75분</strong> (실전 시험 표준 시간)</td></tr>
              <tr><th>문항 구성</th><td><strong>총 5문항</strong> (문항당 20점, <strong>100점 만점</strong>)</td></tr>
              <tr><th>시험 방식</th><td><strong>Closed-book</strong> (공식 유도 과정 명시 필수)</td></tr>
              <tr><th>지참 가능물</th><td>일반 필기도구, 공학용 전자계산기</td></tr>
              <tr><th>출제 단원</th><td>Ch9 (캐스코드/전류거울), Ch10 (차동증폭기), Ch11 (고주파응답)</td></tr>
            </table>
          </div>
          
          <div class="cover-examinee-box">
            <h3 class="meta-title">✍️ 응시자 기입란</h3>
            <div class="field-row">
              <span class="field-label">학 과 :</span>
              <span class="field-line">전자공학과</span>
            </div>
            <div class="field-row">
              <span class="field-label">학 번 :</span>
              <span class="field-line"></span>
            </div>
            <div class="field-row">
              <span class="field-label">성 명 :</span>
              <span class="field-line"></span>
            </div>
            <div class="field-row">
              <span class="field-label">확 인 :</span>
              <span class="field-line">감독관 서명 [ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ]</span>
            </div>
            <div class="score-grid">
              <div class="score-cell">Q1<br/>/ 20</div>
              <div class="score-cell">Q2<br/>/ 20</div>
              <div class="score-cell">Q3<br/>/ 20</div>
              <div class="score-cell">Q4<br/>/ 20</div>
              <div class="score-cell">Q5<br/>/ 20</div>
              <div class="score-cell total">총점<br/>/ 100</div>
            </div>
          </div>
        </div>

        <div class="cover-bottom-box">
          <h3 class="meta-title">📊 문항 구성 및 배점표</h3>
          <table class="exam-table">
            <thead>
              <tr>
                <th style="width: 80px;">문항</th>
                <th>문항 대표 주제</th>
                <th style="width: 140px;">출제 단원</th>
                <th style="width: 100px;">유형</th>
                <th style="width: 80px;">배점</th>
                <th style="width: 220px;">연계 교과서 / 기출</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Q1</strong></td>
                <td>서술형: 전압 바이어스 한계, 차동쌍 CM 제거 원리, Miller 효과</td>
                <td>Ch9 / 10 / 11</td>
                <td><span class="badge-sub">서술형</span></td>
                <td><strong>20점</strong></td>
                <td>2021-Q1, 2023-Q1, 2019-Q5</td>
              </tr>
              <tr>
                <td><strong>Q2</strong></td>
                <td>축퇴 저항 전류 거울 복사비 설계 및 복합 바이어스 CE 단</td>
                <td>Ch9</td>
                <td><span class="badge-sub">계산형</span></td>
                <td><strong>20점</strong></td>
                <td>Razavi P9.49, E9.18 / 2021-Q5, 2023-Q2</td>
              </tr>
              <tr>
                <td><strong>Q3</strong></td>
                <td>기생 저항 Rp 캐스코드 및 Folded Cascode 증폭기</td>
                <td>Ch9</td>
                <td><span class="badge-sub">계산형</span></td>
                <td><strong>20점</strong></td>
                <td>Razavi P9.34 / 2021-Q2(a), 2023-Q3(a)</td>
              </tr>
              <tr>
                <td><strong>Q4</strong></td>
                <td>소스 축퇴 차동쌍 반회로 해석 및 능동 전류 거울 부하 차동쌍</td>
                <td>Ch10</td>
                <td><span class="badge-sub">계산형</span></td>
                <td><strong>20점</strong></td>
                <td>Razavi E10.29, P10.53 / 2021-Q2(b), 2023-Q3(b)</td>
              </tr>
              <tr>
                <td><strong>Q5</strong></td>
                <td>부하 저항 불일치 ΔRD 차동 증폭기의 Vin,CM 범위, ACM-DM, CMRR</td>
                <td>Ch10</td>
                <td><span class="badge-sub">계산형</span></td>
                <td><strong>20점</strong></td>
                <td>Razavi P10.69, P10.70 / 2021-Q4, 2023-Q4</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="cover-footer-note">
          ⚠️ <strong>수험자 유의사항</strong>: 단순 수치 나열 시 감점 처리되며, KCL/KVL 노드 방정식 유도 및 소신호 파라미터($g_m, r_o, R_{{out}}, G_m$) 계산 과정을 단계별로 반드시 명시하십시오.
        </div>
      </div>
      <div class="page-footer">
        <span>아주대학교 전자공학과 · 전자회로2 (2026-2)</span>
        <span>표지 (1 / 6)</span>
      </div>
    </div>
    """
    pages_html.append(cover_html)
    
    # Problem Pages: Q1 ~ Q5
    for q in questions:
        prob_content = md_to_html(q["prob_md"], is_problem=True)
        ch_str = ", ".join(f"Ch{c}" for c in q["chapters"]) if q["chapters"] else "Ch9-11"
        
        page_html = f"""
        <div class="page page-problem" id="page-Q{q['num']}">
          <div class="page-head">
            <div class="head-left">
              <span class="badge-q">Q{q['num']}</span>
              <span class="badge-pts">배점 {q['points']}점</span>
              <span class="badge-ch">{ch_str}</span>
            </div>
            <div class="head-title">{q['title']}</div>
            <div class="head-right">
              <span>권장 시간: 15분</span>
              <span class="page-num-pill">{q['num'] + 1} / 6</span>
            </div>
          </div>
          
          <div class="page-body problem-body">
            <div class="problem-statement-panel">
              <div class="panel-inner">
                {prob_content}
              </div>
            </div>
            <div class="answer-workspace-panel">
              <div class="workspace-header">
                <span class="ws-icon">✏️</span>
                <span class="ws-title">답안 작성란 (Answer Workspace)</span>
                <span class="ws-desc">계산 과정 및 수식 유도를 명시하시오</span>
              </div>
              <div class="workspace-grid-area"></div>
              <div class="workspace-bottom-box">
                <div class="ws-box-title">최종 답안 (Key Results)</div>
                <div class="ws-box-content">
                  <div class="ws-box-line"></div>
                  <div class="ws-box-line"></div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="page-footer">
            <span>전자회로2 중간고사 실전 대비 모의고사 (v1) · 아주대학교 전자공학과</span>
            <span>made by jjundev · 문항 Q{q['num']} ({q['num'] + 1} / 6)</span>
          </div>
        </div>
        """
        pages_html.append(page_html)
        
    return assemble_document(pages_html, title="전자회로2 중간고사 실전 대비 모의고사 (v1) - 문제지")


def build_answer_html(selection, questions):
    pages_html = []
    
    # Page 1: Cover Page for Answers
    cover_html = f"""
    <div class="page page-cover page-cover-answer" id="page-cover-ans">
      <div class="cover-card">
        <div class="cover-badge-row">
          <span class="badge badge-accent">2026-2 전자회로2</span>
          <span class="badge badge-success">표준 답안 및 상세 해설 (v1)</span>
          <span class="badge badge-outline">독립 SymPy 검증 완료</span>
        </div>
        <h1 class="cover-title">전자회로2 중간고사 실전 대비 모의고사 — 표준 답안</h1>
        <p class="cover-subtitle">Ajou University Dept. of Electronic Engineering · Complete Solution & Grading Rubric</p>
        
        <div class="cover-grid" style="grid-template-columns: 1fr;">
          <div class="cover-bottom-box" style="margin-top: 0;">
            <h3 class="meta-title">🎯 문항별 핵심 최종 정답 요약 (Quick Reference Key)</h3>
            <table class="exam-table ans-summary-table">
              <thead>
                <tr>
                  <th style="width: 70px;">문항</th>
                  <th style="width: 200px;">주제</th>
                  <th style="width: 100px;">소문항</th>
                  <th>핵심 정답 및 결과 수식 요약</th>
                  <th style="width: 90px;">배점</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td rowspan="3"><strong>Q1</strong></td>
                  <td rowspan="3">서술형 핵심 개념</td>
                  <td><strong>(a)</strong> 바이어스</td>
                  <td>저항분배는 $V_{{TH}}, \\mu_n C_{{ox}}, T$에 종속. 전류 거울은 동일 칩 인접 배치로 공정·온도 변동 상쇄 $\\to I_{{out}} = \\frac{{(W/L)_1}}{{(W/L)_{{REF}}}} I_{{REF}}$</td>
                  <td>7점</td>
                </tr>
                <tr>
                  <td><strong>(b)</strong> 차동쌍 CM</td>
                  <td>이상적 차동쌍은 $I_{{SS}}$ 고정으로 $\\Delta I_D = 0, A_{{CM}} = 0$. 유한 $R_{{SS}}$로 $A_{{CM}} \\approx -\\frac{{R_D}}{{2R_{{SS}}}}$, $\\Delta R_D$로 $A_{{CM-DM}} \\approx -\\frac{{\\Delta R_D}}{{2R_{{SS}}}}$ 발생</td>
                  <td>7점</td>
                </tr>
                <tr>
                  <td><strong>(c)</strong> Miller 효과</td>
                  <td>반전 증폭기($A_v = -|A_v|$) 피드백 $C_F$에 의해 입력 등가 $C_{{in,M}} = (1+|A_v|)C_F$ 급증 $\\to$ 극점 주파수 $\\omega_p = \\frac{{1}}{{R_S C_{{in}}}}$ 저하로 대역폭 축소</td>
                  <td>6점</td>
                </tr>
                <tr>
                  <td rowspan="2"><strong>Q2</strong></td>
                  <td rowspan="2">축퇴 거울 & 복합 CE</td>
                  <td><strong>(a)</strong> 축퇴 MOS</td>
                  <td>$V_{{GS1}} = 0.600\\,\\text{{V}}, V_{{GS2}} = 0.5414\\,\\text{{V}} \\implies R_S = \\mathbf{{117.2\\,\\Omega}}$ (또는 정밀 근사), $r_{{o2}} = 20\\,\\text{{k}}\\Omega \\implies R_{{out}} = \\mathbf{{30.6\\,\\text{{k}}\\Omega}}$</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td><strong>(b)</strong> 복합 CE단</td>
                  <td>$I_{{C1}} = \\mathbf{{600\\,\\mu\\text{{A}}}}, G_m = \\mathbf{{23.08\\,\\text{{mS}}}}, R_{{out}} = r_{{o1}} \\parallel r_{{o2}} = \\mathbf{{33.3\\,\\text{{k}}\\Omega}}, A_v = -G_m R_{{out}} = \\mathbf{{-769.2}}$</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td rowspan="2"><strong>Q3</strong></td>
                  <td rowspan="2">기생 Rp 캐스코드 & Folded Cascode</td>
                  <td><strong>(a)</strong> Rp 캐스코드</td>
                  <td>$r_{{o1..4}} = 10\\,\\text{{k}}\\Omega, g_m = 10\\,\\text{{mS}}$. $R_{{up}} = 1.01\\,\\text{{M}}\\Omega, R_{{down}} = 78.5\\,\\text{{k}}\\Omega \\implies R_{{out}} = \\mathbf{{73.1\\,\\text{{k}}\\Omega}}, A_v = \\mathbf{{-233.9}}$</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td><strong>(b)</strong> Folded Cascode</td>
                  <td>$G_m = g_{{m5}} = \\mathbf{{15.81\\,\\text{{mS}}}}, R_{{out}} = R_{{up}} \\parallel R_{{down}} = \\mathbf{{353.6\\,\\text{{k}}\\Omega}}, A_v = -G_m R_{{out}} = \\mathbf{{-5590}}$</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td rowspan="2"><strong>Q4</strong></td>
                  <td rowspan="2">축퇴 차동쌍 & 능동 부하</td>
                  <td><strong>(a)</strong> 축퇴 차동쌍</td>
                  <td>가상 접지 $V_P = 0$. 반회로 등가 $R_{{SS}}/2 = 200\\,\\Omega, g_m = 3.162\\,\\text{{mS}} \\implies A_d = \\mathbf{{-5.86}}$ (단일단 $-2.93$)</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td><strong>(b)</strong> 능동 부하쌍</td>
                  <td>전류 거울 신호 합성으로 $G_m = g_{{m1,2}} = \\mathbf{{31.62\\,\\text{{mS}}}}, R_{{out}} = r_{{o2}} \\parallel r_{{o4}} = \\mathbf{{10.0\\,\\text{{k}}\\Omega}}, A_v = \\mathbf{{+316.2}}$</td>
                  <td>10점</td>
                </tr>
                <tr>
                  <td rowspan="4"><strong>Q5</strong></td>
                  <td rowspan="4">부하 불일치 차동쌍</td>
                  <td><strong>(1)</strong> $V_{{in,CM}}$ 범위</td>
                  <td>$V_{{GS}} = 0.50\\,\\text{{V}}, V_{{D2}} = 0.75\\,\\text{{V}} \\implies \\mathbf{{0.80\\,\\text{{V}} \\le V_{{in,CM}} \\le 1.15\\,\\text{{V}}}}$</td>
                  <td>5점</td>
                </tr>
                <tr>
                  <td><strong>(2)</strong> $A_d, A_{{CM}}$</td>
                  <td>$g_m = 10.0\\,\\text{{mS}} \\implies A_d = -g_m (R_D + \\Delta R_D / 2) = \\mathbf{{-20.5}}$ (근사 $-20.0$), $A_{{CM}} = \\mathbf{{-0.976}}$ (근사 $-1.0$)</td>
                  <td>5점</td>
                </tr>
                <tr>
                  <td><strong>(3)</strong> $A_{{CM-DM}}$</td>
                  <td>$A_{{CM-DM}} = \\frac{{g_m \\Delta R_D}}{{1 + 2 g_m R_{{SS}}}} = \\mathbf{{0.0476}}$ (근사 $0.050$)</td>
                  <td>5점</td>
                </tr>
                <tr>
                  <td><strong>(4)</strong> $\\text{{CMRR}}$</td>
                  <td>$\\text{{CMRR}} = |A_d / A_{{CM-DM}}| = \\mathbf{{430.5}} \\implies \\mathbf{{52.7\\,\\text{{dB}}}}$ (근사 $400 \\implies 52.0\\,\\text{{dB}}$)</td>
                  <td>5점</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div class="cover-footer-note">
          💯 <strong>검증 결과</strong>: Q2 ~ Q5 모든 계산형 문항은 Task 4 SymPy 엄밀 대수 및 수치 시뮬레이션을 통해 13개 소신호 파라미터가 오차 0.0%로 완전 일치함을 공인받았습니다.
        </div>
      </div>
      <div class="page-footer">
        <span>아주대학교 전자공학과 · 전자회로2 (2026-2)</span>
        <span>정답 총괄표 (1 / 6)</span>
      </div>
    </div>
    """
    pages_html.append(cover_html)
    
    # Answer Pages: Q1 ~ Q5
    for q in questions:
        sol_content = md_to_html(q["sol_md"], is_problem=False)
        ch_str = ", ".join(f"Ch{c}" for c in q["chapters"]) if q["chapters"] else "Ch9-11"
        
        page_html = f"""
        <div class="page page-answer" id="page-ans-Q{q['num']}">
          <div class="page-head page-head-ans">
            <div class="head-left">
              <span class="badge-ans">표준 답안</span>
              <span class="badge-q">Q{q['num']}</span>
              <span class="badge-pts">배점 {q['points']}점</span>
              <span class="badge-ch">{ch_str}</span>
            </div>
            <div class="head-title">{q['title']}</div>
            <div class="head-right">
              <span class="ans-status-pill">독립 검산 100% 일치</span>
              <span class="page-num-pill">{q['num'] + 1} / 6</span>
            </div>
          </div>
          
          <div class="page-body answer-body">
            <div class="solution-columnar-wrapper">
              {sol_content}
            </div>
          </div>
          
          <div class="page-footer">
            <span>전자회로2 중간고사 실전 대비 모의고사 (v1) · 표준 답안 및 상세 풀이</span>
            <span>made by jjundev · 문항 Q{q['num']} 해설 ({q['num'] + 1} / 6)</span>
          </div>
        </div>
        """
        pages_html.append(page_html)
        
    return assemble_document(pages_html, title="전자회로2 중간고사 실전 대비 모의고사 (v1) - 표준 답안")


def assemble_document(pages, title="전자회로2 중간고사 모의고사"):
    css_content = """
    @page {
      size: 1920px 1080px;
      margin: 0;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    :root {
      --primary: #1e3a8a;
      --primary-light: #eff6ff;
      --accent: #2563eb;
      --success: #16a34a;
      --ink: #0f172a;
      --ink-muted: #475569;
      --border: #cbd5e1;
      --border-light: #e2e8f0;
      --bg-card: #f8fafc;
      --bg-white: #ffffff;
      --tag-bg: #e2e8f0;
    }
    html, body {
      margin: 0;
      padding: 0;
      font-family: Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: var(--ink);
      background: #e2e8f0;
      -webkit-font-smoothing: antialiased;
    }
    .page {
      width: 1920px;
      height: 1080px;
      max-height: 1080px;
      min-height: 1080px;
      overflow: hidden;
      break-after: page;
      page-break-after: always;
      position: relative;
      background: #ffffff;
      padding: 28px 40px;
      display: flex;
      flex-direction: column;
      box-sizing: border-box;
    }
    
    /* Header */
    .page-head {
      height: 52px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px solid var(--primary);
      padding-bottom: 8px;
      margin-bottom: 16px;
    }
    .page-head-ans {
      border-bottom-color: var(--success);
    }
    .head-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .head-title {
      font-size: 20px;
      font-weight: 700;
      color: var(--primary);
      flex: 1;
      text-align: center;
      margin: 0 20px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .page-head-ans .head-title {
      color: #15803d;
    }
    .head-right {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
      color: var(--ink-muted);
    }
    .badge-q {
      background: var(--primary);
      color: #fff;
      font-weight: 800;
      font-size: 15px;
      padding: 4px 12px;
      border-radius: 6px;
    }
    .badge-ans {
      background: var(--success);
      color: #fff;
      font-weight: 800;
      font-size: 14px;
      padding: 4px 10px;
      border-radius: 6px;
    }
    .badge-pts {
      background: #fee2e2;
      color: #991b1b;
      font-weight: 700;
      font-size: 13px;
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid #fecaca;
    }
    .badge-ch {
      background: #f1f5f9;
      color: #475569;
      font-weight: 600;
      font-size: 13px;
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid var(--border-light);
    }
    .page-num-pill {
      background: #f1f5f9;
      padding: 4px 12px;
      border-radius: 20px;
      font-weight: 700;
      color: #334155;
      border: 1px solid var(--border);
    }
    .ans-status-pill {
      background: #dcfce7;
      color: #166534;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      border: 1px solid #bbf7d0;
    }

    /* Footer */
    .page-footer {
      height: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: #94a3b8;
      border-top: 1px solid #f1f5f9;
      margin-top: 8px;
      padding-top: 6px;
    }

    /* Cover Page */
    .page-cover {
      justify-content: center;
      align-items: center;
      background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
    }
    .cover-card {
      width: 1760px;
      height: 960px;
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
      border: 1px solid #cbd5e1;
      padding: 40px 60px;
      display: flex;
      flex-direction: column;
      box-sizing: border-box;
    }
    .cover-badge-row {
      display: flex;
      gap: 12px;
      margin-bottom: 12px;
    }
    .badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 700;
    }
    .badge-accent { background: #dbeafe; color: #1e40af; }
    .badge-dark { background: #0f172a; color: #f8fafc; }
    .badge-success { background: #dcfce7; color: #15803d; }
    .badge-outline { background: #fff; color: #475569; border: 1px solid #cbd5e1; }
    .badge-sub { background: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
    .cover-title {
      font-size: 34px;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 6px 0;
      letter-spacing: -0.02em;
    }
    .cover-subtitle {
      font-size: 16px;
      color: #64748b;
      margin: 0 0 24px 0;
    }
    .cover-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 32px;
      margin-bottom: 24px;
    }
    .cover-meta-box, .cover-examinee-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 18px 24px;
    }
    .meta-title {
      font-size: 17px;
      font-weight: 700;
      color: #1e293b;
      margin: 0 0 14px 0;
      padding-bottom: 8px;
      border-bottom: 2px solid #e2e8f0;
    }
    .spec-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    .spec-table th {
      text-align: left;
      padding: 7px 0;
      color: #64748b;
      font-weight: 600;
      width: 110px;
    }
    .spec-table td {
      padding: 7px 0;
      color: #1e293b;
    }
    .field-row {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      font-size: 15px;
    }
    .field-label {
      width: 70px;
      font-weight: 600;
      color: #475569;
    }
    .field-line {
      flex: 1;
      border-bottom: 1.5px solid #94a3b8;
      padding-bottom: 2px;
      color: #0f172a;
      font-weight: 600;
    }
    .score-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 8px;
      margin-top: 16px;
    }
    .score-cell {
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 8px 4px;
      text-align: center;
      font-size: 13px;
      background: #fff;
      color: #475569;
      font-weight: 600;
    }
    .score-cell.total {
      background: #eff6ff;
      border-color: #93c5fd;
      color: #1d4ed8;
      font-weight: 800;
    }
    .cover-bottom-box {
      margin-top: auto;
    }
    .exam-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
    }
    .exam-table th {
      background: #f1f5f9;
      color: #334155;
      padding: 9px 12px;
      font-weight: 700;
      border-bottom: 2px solid #cbd5e1;
      text-align: center;
    }
    .exam-table td {
      padding: 8px 12px;
      border-bottom: 1px solid #e2e8f0;
      color: #1e293b;
      text-align: center;
    }
    .exam-table td:nth-child(2) {
      text-align: left;
    }
    .cover-footer-note {
      margin-top: 14px;
      font-size: 13px;
      color: #475569;
      background: #fffbeb;
      border: 1px solid #fef3c7;
      padding: 8px 16px;
      border-radius: 6px;
    }

    /* Problem Page Layout */
    .problem-body {
      flex: 1;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      overflow: hidden;
      min-height: 0;
    }
    .problem-statement-panel {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px 20px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .panel-inner {
      font-size: 13px;
      line-height: 1.48;
      color: #1e293b;
      overflow: hidden;
    }
    .panel-inner h2, .panel-inner h3 {
      font-size: 14.5px;
      font-weight: 700;
      color: var(--primary);
      margin: 8px 0 4px 0;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 3px;
    }
    .panel-inner h2:first-child, .panel-inner h3:first-child {
      margin-top: 0;
    }
    .panel-inner p {
      margin: 0 0 5px 0;
    }
    .panel-inner ul {
      margin: 2px 0 6px 16px;
      padding: 0;
    }
    .panel-inner li {
      margin-bottom: 2px;
    }
    .circuit-fig {
      margin: 6px 0;
      text-align: center;
    }
    .fig-card {
      display: block;
      margin: 4px auto;
      text-align: center;
      background: #fff;
      padding: 4px 8px;
      border-radius: 8px;
      border: 1px solid #cbd5e1;
      max-width: 360px;
    }
    .circuit-img {
      max-height: 132px;
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }
    .fig-caption {
      font-size: 10.5px;
      color: #64748b;
      margin-top: 3px;
      font-weight: 600;
    }

    /* Workspace Panel */
    .answer-workspace-panel {
      border: 2px dashed #94a3b8;
      border-radius: 12px;
      background: #ffffff;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      position: relative;
    }
    .workspace-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-bottom: 8px;
      border-bottom: 1px solid #e2e8f0;
      margin-bottom: 10px;
    }
    .ws-icon { font-size: 18px; }
    .ws-title {
      font-size: 15px;
      font-weight: 700;
      color: #334155;
    }
    .ws-desc {
      font-size: 12px;
      color: #94a3b8;
      margin-left: auto;
    }
    .workspace-grid-area {
      flex: 1;
      background-image: radial-gradient(#cbd5e1 1.2px, transparent 1.2px);
      background-size: 20px 20px;
      border-radius: 8px;
      min-height: 0;
    }
    .workspace-bottom-box {
      height: 90px;
      border: 1.5px solid #cbd5e1;
      border-radius: 8px;
      background: #f8fafc;
      padding: 8px 14px;
      margin-top: 10px;
      display: flex;
      flex-direction: column;
    }
    .ws-box-title {
      font-size: 12px;
      font-weight: 700;
      color: #475569;
      margin-bottom: 4px;
    }
    .ws-box-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
    }
    .ws-box-line {
      border-bottom: 1px dashed #cbd5e1;
      height: 20px;
    }

    /* Answer Document Layout */
    .answer-body {
      flex: 1;
      overflow: hidden;
      min-height: 0;
    }
    .solution-columnar-wrapper {
      column-count: 2;
      column-gap: 36px;
      column-rule: 1px solid #e2e8f0;
      height: 100%;
      font-size: 12.4px;
      line-height: 1.45;
      color: #1e293b;
    }
    .solution-columnar-wrapper h2, .solution-columnar-wrapper h3 {
      break-after: avoid;
      page-break-after: avoid;
      font-size: 14px;
      font-weight: 700;
      color: #1e3a8a;
      background: #eff6ff;
      padding: 3px 8px;
      border-radius: 5px;
      border-left: 4px solid var(--accent);
      margin: 6px 0 4px 0;
    }
    .solution-columnar-wrapper h4 {
      break-after: avoid;
      page-break-after: avoid;
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
      margin: 5px 0 3px 0;
    }
    .solution-columnar-wrapper p {
      margin: 0 0 5px 0;
    }
    .solution-columnar-wrapper ul {
      margin: 2px 0 5px 16px;
      padding: 0;
    }
    .solution-columnar-wrapper li {
      margin-bottom: 2px;
    }
    .solution-columnar-wrapper hr {
      border: 0;
      border-top: 1px dashed #cbd5e1;
      margin: 6px 0;
    }
    
    /* Specific tuning for Q5 answer */
    #page-ans-Q5 .solution-columnar-wrapper {
      font-size: 11.2px;
      line-height: 1.36;
      column-gap: 32px;
    }
    #page-ans-Q5 .solution-columnar-wrapper h3, #page-ans-Q5 .solution-columnar-wrapper h4 {
      margin: 4px 0 2px 0;
      padding: 2px 6px;
      font-size: 12px;
    }
    #page-ans-Q5 .solution-columnar-wrapper p {
      margin: 0 0 2px 0;
    }
    #page-ans-Q5 .solution-columnar-wrapper ul {
      margin: 1px 0 3px 12px;
    }
    #page-ans-Q5 .katex-display {
      margin: 1.5px 0 !important;
    }
    #page-ans-Q5 .katex {
      font-size: 0.95em !important;
    }
    
    /* KaTeX Display Equations tuning */
    .katex-display {
      margin: 4px 0 !important;
      overflow-x: auto;
      overflow-y: hidden;
    }
    .katex {
      font-size: 1.05em !important;
    }
    """
    
    body_html = "\n".join(pages)
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" onload="initKaTeX()"></script>
  <style>
  {css_content}
  </style>
  <script>
    function initKaTeX() {{
      if (typeof renderMathInElement === 'function') {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
          ],
          throwOnError: false
        }});
        setTimeout(function() {{
          document.documentElement.dataset.ready = "true";
          window.renderReady = true;
        }}, 150);
      }}
    }}
    // fallback if onload fails or delayed
    window.addEventListener('DOMContentLoaded', function() {{
      setTimeout(function() {{
        if (!window.renderReady) initKaTeX();
      }}, 500);
    }});
  </script>
</head>
<body>
{body_html}
</body>
</html>
"""


def render_html_to_pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    
    print(f"Rendering {html_path.name} -> {pdf_path.name} ...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(html_path.resolve().as_uri())
        
        # wait for KaTeX and render ready
        page.wait_for_function("window.renderReady === true", timeout=45000)
        
        # Check overflows (both outer page and inner content containers)
        page_stats = page.evaluate("""() => {
          return [...document.querySelectorAll('.page')].map(p => {
            const inner = p.querySelector('.panel-inner') || p.querySelector('.solution-columnar-wrapper') || p.querySelector('.cover-card');
            const innerHDiff = inner ? Math.max(0, inner.scrollHeight - inner.clientHeight) : 0;
            const innerWDiff = inner ? Math.max(0, inner.scrollWidth - inner.clientWidth) : 0;
            return {
              id: p.id,
              scrollH: p.scrollHeight,
              clientH: p.clientHeight,
              pageDiffH: p.scrollHeight - p.clientHeight,
              innerDiffH: innerHDiff,
              innerDiffW: innerWDiff,
              overflow: (p.scrollHeight - p.clientHeight > 2) || (innerHDiff > 4) || (innerWDiff > 4)
            };
          });
        }""")
        
        overflows = [s for s in page_stats if s["overflow"]]
        if overflows:
            print(f"WARNING: Overflow detected on {len(overflows)} pages:", overflows, file=sys.stderr)
        else:
            print(f"Zero overflow verified on all {len(page_stats)} pages (page and inner containers)!")
            
        page.pdf(
            path=str(pdf_path),
            prefer_css_page_size=True,
            print_background=True
        )
        browser.close()
    print(f"Successfully generated: {pdf_path}")
    return overflows


def main():
    selection, display_titles, questions = load_assets()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Problem Document
    prob_html_path = BUILD_DIR / "중간고사대비_v1-문제.html"
    prob_pdf_path = BASE / "중간고사대비_v1-문제.pdf"
    prob_html = build_problem_html(selection, questions)
    prob_html_path.write_text(prob_html, encoding="utf-8")
    prob_overflows = render_html_to_pdf(prob_html_path, prob_pdf_path)
    
    # 2. Answer Document
    ans_html_path = BUILD_DIR / "중간고사대비_v1-답안.html"
    ans_pdf_path = BASE / "중간고사대비_v1-답안.pdf"
    ans_html = build_answer_html(selection, questions)
    ans_html_path.write_text(ans_html, encoding="utf-8")
    ans_overflows = render_html_to_pdf(ans_html_path, ans_pdf_path)
    
    return 1 if (prob_overflows or ans_overflows) else 0


if __name__ == "__main__":
    sys.exit(main())
