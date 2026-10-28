#!/usr/bin/env python3
"""
Context inference and electronic circuits glossary extractor for ec2-stt.

- Infers class date (MMDD) from audio filename or explicit argument.
- Infers syllabus chapter(s) from 복습노트/ and 강의노트/.
  Around a chapter switch (new lecture PDF uploaded, no review note yet) both chapters are used.
- Extracts key technical terms from 강의노트/2026F_Lec*.pdf slide titles and
  교과서/마이크로전자회로/chNN/README.md section titles.
- Builds domain guidance prompt for STT transcription subagents.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import unicodedata

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

DATE_PATTERNS = [
    # 20261002, 2026-10-02, 2026.10.02, 2026_1002
    re.compile(r"(?:20\d{2})[-_.]?([01]\d)[-_.]?([0-3]\d)"),
    # 1002 전회2, 1002.m4a, 녹음_0923.wav, 0930
    re.compile(r"(?:^|[^\d])([01]\d)([0-3]\d)(?:[^\d]|$)"),
]

# 모든 단원에 공통으로 적용하는 발음 교정 규칙
COMMON_RULES = [
    ("케스코드/카스코드/캐스코트/케스 코드", "캐스코드 (Cascode)"),
    ("디퍼렌셜/디프런셜/디퍼렌샬", "디퍼렌셜 (Differential)"),
    ("커런트 미라/커런트밀러", "커런트 미러 (Current mirror)"),
    ("지엠/GM", "gm (트랜스컨덕턴스 gm)"),
    ("알파이/알 파이", "r파이 (소신호 베이스 저항 r_pi)"),
    ("알오/알 오", "ro (소신호 출력 저항 ro)"),
    ("알이/알 이", "re (에미터 저항 re)"),
    ("지엠비/gmb", "gmb (바디 효과 트랜스컨덕턴스 gmb)"),
    ("하프서킷/하프 서키트", "하프 서킷 (Half-circuit)"),
    ("버추얼 그라운드/가상접지", "버추얼 그라운드 (Virtual ground / AC ground)"),
    ("테일 커런트/테일 소스/테일 노드", "테일 (Tail current / node)"),
    ("오버드라이브", "오버드라이브 전압 (Vov = VGS - VTH)"),
    ("싱글 엔디드/싱글엔디드", "싱글 엔디드 (Single-ended)"),
    ("커먼 모드/시엠", "커먼 모드 (VCM, Common-mode)"),
    ("다이오드 커넥티드", "다이오드 커넥티드 (Diode-connected)"),
    ("바디 이펙트/바디 효과", "바디 이펙트 (Body effect)"),
]

BASE_SEEDS = [
    "MOSFET", "BJT", "소신호", "대신호", "트랜스컨덕턴스", "출력 저항", "오버드라이브 전압",
    "얼리 전압", "채널 길이 변조", "바디 이펙트", "다이오드 커넥티드",
    "gm", "ro", "r파이", "re", "gmb", "VTH", "VGS", "VDS", "VBE", "VCE", "IC", "ID", "ISS", "IEE"
]

# 단원 레지스트리: 새 강의노트가 올라오면 여기에 항목을 추가/보강한다.
# keys: 강의노트 PDF·정리노트 파일명에서 단원을 알아보는 키워드
CHAPTERS: dict[int, dict] = {
    9: {
        "title": "캐스코드 증폭기와 전류 거울 (Cascode Stages and Current Mirrors)",
        "keys": ("Cascode", "캐스코드"),
        "seeds": [
            "캐스코드", "커런트 미러", "출력 임피던스", "전압 헤드룸", "소신호 출력 저항",
            "Cascode", "Current Mirror", "gm", "ro", "r파이", "re", "Rout", "R_out", "VA"
        ],
        "rules": [],
    },
    10: {
        "title": "차동 증폭기 (Differential Amplifiers)",
        "keys": ("Differential", "차동"),
        "seeds": [
            "디퍼렌셜 페어", "차동 증폭기", "차동 신호", "동상 신호", "하프 서킷",
            "버추얼 그라운드", "AC 그라운드", "테일 커런트", "테일 소스", "테일 노드",
            "커먼 모드", "커먼 모드 리젝션", "CMRR", "소신호 해석", "스몰 시그널",
            "Differential Pair", "Differential Amplifier", "Half-Circuit",
            "Virtual Ground", "Tail Current", "Common-Mode", "gm", "ro", "r파이", "re"
        ],
        "rules": [],
    },
    11: {
        "title": "증폭기의 주파수 응답 (Frequency Response of Amplifiers)",
        "keys": ("FrequencyResponse", "Frequency", "주파수"),
        "seeds": [
            "주파수 응답", "밀러 효과", "밀러 정리", "밀러 커패시턴스", "지배적 극점", "유니티 게인 주파수",
            "차단 주파수", "기생 커패시턴스", "고주파 모델", "극점", "영점", "폴", "제로", "보드 플롯",
            "커패시티브 커플링", "다이렉트 커플링", "로우패스 필터", "하이패스 필터", "다이렉트 어낼리시스",
            "입력 커패시턴스", "CS 스테이지", "CG 스테이지", "CB 스테이지", "소스 팔로워", "에미터 팔로워",
            "Frequency Response", "Miller Effect", "Miller's Theorem", "Dominant Pole", "Bode Plot",
            "C_GS", "C_GD", "C_DB", "C_SB", "C_π", "C_μ", "f_T", "ω_T", "ω_p", "3dB", "decade"
        ],
        "rules": [
            ("씨지에스/시지에스", "C_GS (게이트-소스 커패시턴스)"),
            ("씨지디/시지디", "C_GD (게이트-드레인 커패시턴스)"),
            ("씨디비/씨에스비", "C_DB / C_SB (접합 커패시턴스)"),
            ("씨파이/씨뮤", "C_π / C_μ (BJT 고주파 모델)"),
            ("보데/보드 플랏", "보드 플롯 (Bode plot)"),
            ("에프티/트랜짓/트랜싯", "f_T (트랜짓 주파수)"),
            ("오메가 피/오메가 티", "ω_p / ω_T"),
            ("쓰리디비/삼디비", "3dB"),
            ("디케이드/데케이드", "decade (디케이드)"),
            ("커패시티브 커플링/다이렉트 커플링", "커패시티브 커플링 / 다이렉트 커플링 (Capacitive / Direct coupling)"),
            ("소스 폴로워/폴로어", "소스 팔로워 (Source follower)"),
            ("도미넌트 폴/도미넌트 폴점", "도미넌트 폴 (Dominant pole / 지배적 극점)"),
            ("밀러 캐패시턴스/밀러 이펙트/밀러 띠어렘", "밀러 커패시턴스 / 밀러 효과 / 밀러 정리 (Miller)"),
        ],
    },
    12: {
        "title": "귀환 (Feedback)",
        "keys": ("Feedback", "피드백", "귀환"),
        "seeds": [
            "피드백", "귀환", "루프 게인", "루프 이득", "오픈 루프", "클로즈드 루프", "개루프", "폐루프",
            "피드백 팩터", "귀환율", "β", "게인 디센시타이제이션", "이득 둔감화", "대역폭 확장",
            "감지", "반송", "센싱", "리턴", "시리즈", "션트", "귀환의 극성", "네거티브 피드백",
            "전압-전압 귀환", "전압-전류 귀환", "전류-전압 귀환", "전류-전류 귀환",
            "트랜스임피던스 증폭기", "트랜스컨덕턴스 증폭기", "비반전 증폭기", "입출력 임피던스",
            "위상 마진", "주파수 보상", "안정 조건",
            "Feedback", "Loop Gain", "Open-Loop", "Closed-Loop", "Feedback Factor",
            "Gain Desensitization", "Bandwidth Extension", "Sense", "Return",
            "Voltage-Voltage", "Voltage-Current", "Current-Voltage", "Current-Current",
            "Transimpedance", "Phase Margin", "Frequency Compensation"
        ],
        "rules": [
            ("루프게인/루프 개인", "루프 게인 (Loop gain)"),
            ("베타", "β (피드백 팩터)"),
            ("셴트/쉔트/션 트", "션트 (Shunt)"),
            ("디센시타이제이션/디센서티제이션", "게인 디센시타이제이션 (Gain desensitization)"),
            ("오픈루프/클로즈루프", "오픈 루프 / 클로즈드 루프 (Open / Closed loop)"),
            ("트랜스 임피던스", "트랜스임피던스 (Transimpedance)"),
            ("페이즈 마진", "위상 마진 (Phase margin)"),
        ],
    },
}

SLIDE_TITLE_SKIP = {"contents", "전자회로2", "analysis summary"}
SECTION_SKIP = {"일반적인 고찰", "추가 예제", "General Considerations", "Additional Examples"}


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def parse_date(filename_or_path: str, date_override: str | None = None) -> str:
    """Extract MMDD string from filename or override."""
    if date_override:
        clean = date_override.strip()
        m = re.fullmatch(r"(\d{2})(\d{2})", clean)
        if m and (1 <= int(m.group(1)) <= 12) and (1 <= int(m.group(2)) <= 31):
            return m.group(0)
        raise ValueError(f"유효하지 않은 날짜 형식입니다: {date_override!r} (예: 1002)")

    base = nfc(Path(filename_or_path).name)

    for pat in DATE_PATTERNS:
        match = pat.search(base)
        if match:
            mm, dd = match.group(1), match.group(2)
            if (1 <= int(mm) <= 12) and (1 <= int(dd) <= 31):
                return f"{mm}{dd}"

    raise ValueError(
        f"파일명에서 수업 날짜(MMDD)를 찾을 수 없습니다: {base!r}\n"
        f"--date MMDD 옵션으로 날짜를 직접 지정해 주세요. (예: /ec2-stt audio.m4a --date 1002)"
    )


def chapter_from_name(name: str) -> int | None:
    """Map a lecture/review file name to a chapter via 'ChNN' or registry keywords."""
    name = nfc(name)
    m = re.search(r"Ch0?(\d{1,2})(?!\d)", name)
    if m and int(m.group(1)) in CHAPTERS:
        return int(m.group(1))
    # 큰 장부터: "Frequency_Response_of_Differential" 같은 이름은 뒤 단원이 맞다
    for chapter, info in sorted(CHAPTERS.items(), reverse=True):
        if any(k in name for k in info["keys"]):
            return chapter
    return None


def lecture_pdfs(repo_root: Path | str, chapter: int) -> list[Path]:
    lec_dir = Path(repo_root) / "강의노트"
    if not lec_dir.is_dir():
        return []
    return sorted(f for f in lec_dir.iterdir() if f.suffix == ".pdf" and chapter_from_name(f.name) == chapter)


def latest_lecture_chapter(repo_root: Path | str) -> int | None:
    lec_dir = Path(repo_root) / "강의노트"
    if not lec_dir.is_dir():
        return None
    chapters = [chapter_from_name(f.name) for f in lec_dir.iterdir() if f.suffix == ".pdf"]
    chapters = [c for c in chapters if c is not None]
    return max(chapters) if chapters else None


def review_folders(repo_root: Path | str) -> list[str]:
    review_root = Path(repo_root) / "복습노트"
    if not review_root.is_dir():
        return []
    return sorted(
        nfc(d.name) for d in review_root.iterdir()
        if d.is_dir() and re.fullmatch(r"\d{4}", nfc(d.name))
    )


def review_chapter(repo_root: Path | str, mmdd: str) -> int | None:
    """Chapter of the latest review note on or before mmdd."""
    folders = review_folders(repo_root)
    past_folders = [d for d in folders if d <= mmdd]
    target_folder = past_folders[-1] if past_folders else (folders[-1] if folders else None)
    if not target_folder:
        return None

    f_dir = Path(repo_root) / "복습노트" / target_folder / ".assets"
    if not f_dir.is_dir():
        return None
    for f in f_dir.iterdir():
        name = nfc(f.name)
        # .assets/정리노트_MMDD_<slug>.md 검사
        if not (name.startswith(f"정리노트_{target_folder}_") and name.endswith(".md")):
            continue
        # 파일명 자체에서 우선 판정
        chapter = chapter_from_name(name)
        if chapter:
            return chapter
        try:
            content = f.read_text(encoding="utf-8")
            m = re.search(r"Razavi\s*(\d+)장", content)
            if m:
                return int(m.group(1))
            m2 = re.search(r"(?:Ch|ch|Chapter|제|강의노트)\s*(\d+)", content)
            if m2:
                return int(m2.group(1))
        except Exception:
            pass
    return None


def infer_chapters(repo_root: Path | str, mmdd: str) -> list[int]:
    """Infer chapter(s) for a class date.

    Uses the latest review note's chapter. If mmdd is after every review note and a
    newer chapter's lecture PDF is already uploaded, the class may have switched
    chapters, so both are returned (old first).
    """
    reviewed = review_chapter(repo_root, mmdd)
    latest_lec = latest_lecture_chapter(repo_root)
    folders = review_folders(repo_root)
    after_reviews = not folders or mmdd > folders[-1]

    if reviewed is None:
        # 기본 fallback: 최신 강의노트 단원, 없으면 10장 (차동 증폭기)
        return [latest_lec or 10]
    if after_reviews and latest_lec and latest_lec > reviewed:
        return [reviewed, latest_lec]
    return [reviewed]


def infer_chapter(repo_root: Path | str, mmdd: str) -> int:
    """Single-chapter view of infer_chapters (the newest candidate)."""
    return infer_chapters(repo_root, mmdd)[-1]


def get_chapter_title(repo_root: Path | str, chapter: int) -> str:
    """Find chapter title from registry or 강의노트."""
    if chapter in CHAPTERS:
        return CHAPTERS[chapter]["title"]

    lec_dir = Path(repo_root) / "강의노트"
    if lec_dir.is_dir():
        for f in lec_dir.iterdir():
            m = re.search(rf"Ch0?{chapter}_([A-Za-z0-9_&]+)", nfc(f.name))
            if m:
                return m.group(1).replace("_", " ").strip()

    return f"{chapter}장"


def slide_titles(pdf_path: Path) -> list[str]:
    """First text line of each slide, minus page numbers and boilerplate."""
    if not fitz:
        return []
    titles: list[str] = []
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return []
    for page in doc:
        lines = [ln.strip() for ln in page.get_text().splitlines() if ln.strip()]
        if not lines:
            continue
        title = re.sub(r"^(?:Ex\)|Example:)\s*", "", lines[0]).strip()
        title = re.sub(r"\s+", " ", title)
        if len(title) < 4 or title.isdigit() or title.lower() in SLIDE_TITLE_SKIP:
            continue
        if title not in titles:
            titles.append(title)
    return titles


def textbook_sections(repo_root: Path | str, chapter: int) -> list[str]:
    """Section names (절 column) from 교과서/마이크로전자회로/chNN/README.md."""
    readme = Path(repo_root) / "교과서" / "마이크로전자회로" / f"ch{chapter:02d}" / "README.md"
    if not readme.is_file():
        return []
    sections: list[str] = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 4 and re.match(r"\d+\.\d", cells[3]):
            name = re.sub(r"^[\d.]+\s*", "", cells[3])
            if name and name not in SECTION_SKIP and name not in sections:
                sections.append(name)
    return sections


def extract_chapter_terms(repo_root: Path | str, chapter: int | list[int], max_terms: int = 140) -> list[str]:
    """Collect key circuit terms: seeds -> lecture slide titles -> textbook sections -> base seeds."""
    chapters = [chapter] if isinstance(chapter, int) else list(chapter)

    seeds: list[str] = []
    titles: list[str] = []
    sections: list[str] = []
    for ch in chapters:
        seeds += CHAPTERS.get(ch, {}).get("seeds", [])
        for pdf in lecture_pdfs(repo_root, ch):
            titles += slide_titles(pdf)
        sections += textbook_sections(repo_root, ch)

    combined: list[str] = []
    seen: set[str] = set()
    for item in seeds + titles + sections + BASE_SEEDS:
        if item not in seen:
            seen.add(item)
            combined.append(item)
    return combined[:max_terms]


def chapter_rules(chapters: list[int]) -> list[tuple[str, str]]:
    rules = list(COMMON_RULES)
    for ch in chapters:
        rules += CHAPTERS.get(ch, {}).get("rules", [])
    return rules


def build_stt_prompt(chapter: int | list[int], chapter_title: str, terms: list[str]) -> str:
    """Format domain guidance block to inject into the subagent STT prompt."""
    chapters = [chapter] if isinstance(chapter, int) else list(chapter)
    if not re.match(r"\d+장", chapter_title):
        chapter_title = f"{'/'.join(str(c) for c in chapters)}장 {chapter_title}"
    sample_terms = ", ".join(terms)
    homophone_guide = "\n".join(f"  - '{err}'로 들리면 -> '{cor}'" for err, cor in chapter_rules(chapters))

    return f"""[전자회로2 강의 도메인 가이드 (Razavi Fundamentals of Microelectronics)]
- 본 오디오는 아주대학교 전자공학과 전자회로2 (권익진 교수님) 강의 녹음입니다.
- 단원 범위: {chapter_title}
- 주요 전자회로 고유명사 및 파라미터:
  {sample_terms}

- 필수 전사 및 발음 교정 규칙:
  1. 전자회로 표준 용어 최우선: 교수님의 발음이 뭉개지거나 일상 단어로 들리기 쉬운 경우, 회로 이론 문맥상 올바른 전자회로 표준 용어로 정확히 전사하세요.
{homophone_guide}
  2. 표기 원칙: 회로 기호 및 수식 파라미터 약어(gm, ro, r파이, re, VTH, VGS, VDS, VCM, CMRR, ISS, IEE, C_GS, C_GD, f_T 등)는 통용되는 수식/기호 표기를 따르세요.
  3. 철저한 축어성(Verbatim): 요약이나 어미 생략 없이 실제 발화된 내용을 있는 그대로 기록하세요.
"""


def chapters_label(repo_root: Path | str, chapters: list[int]) -> str:
    return " / ".join(f"{ch}장 {get_chapter_title(repo_root, ch)}" for ch in chapters)


def main():
    parser = argparse.ArgumentParser(description="Infer electronic circuits context and terms for ec2-stt")
    parser.add_argument("audio", help="Path to audio file (or filename)")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--date", help="Class date override (MMDD)")
    parser.add_argument("--chapter", type=int, help="Chapter override (e.g. 10)")
    parser.add_argument("--json", action="store_true", help="Output JSON structure")
    parser.add_argument("--prompt-only", action="store_true", help="Print prompt injection text only")

    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    date = parse_date(args.audio, args.date)
    chapters = [args.chapter] if args.chapter else infer_chapters(repo, date)
    chapter = chapters[-1]
    label = chapters_label(repo, chapters)
    terms = extract_chapter_terms(repo, chapters)
    prompt_guide = build_stt_prompt(chapters, label, terms)

    if args.prompt_only:
        print(prompt_guide)
        return

    result = {
        "audio": args.audio,
        "date": date,
        "chapter": chapter,
        "chapters": chapters,
        "chapter_title": get_chapter_title(repo, chapter),
        "chapters_label": label,
        "output_filename": f"{date} 전회2.md",
        "output_path": str(repo / "STT" / f"{date} 전회2.md"),
        "terms_count": len(terms),
        "terms": terms,
        "prompt_guide": prompt_guide,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"수업 날짜: {date} (파일명에서 추출)")
        print(f"진도 단원: {label}")
        print(f"추출 용어: {len(terms)}개")
        print(f"최종 저장: STT/{date} 전회2.md")


if __name__ == "__main__":
    main()
