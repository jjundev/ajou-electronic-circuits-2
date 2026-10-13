#!/usr/bin/env python3
"""
Context inference and electronic circuits glossary extractor for ec2-stt.

- Infers class date (MMDD) from audio filename or explicit argument.
- Infers syllabus chapter from 복습노트/ or 강의노트/.
- Extracts key technical terms directly from 강의노트/2026F_Lec*.pdf and 교과서/마이크로전자회로/*.
- Builds domain guidance prompt for STT transcription subagents.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
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

COMMON_EC2_ERROR_RULES = [
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
    ("도미넌트 폴/도미넌트 폴점", "도미넌트 폴 (Dominant pole / 지배적 극점)"),
    ("밀러 캐패시턴스/밀러 이펙트", "밀러 커패시턴스 / 밀러 효과 (Miller effect)"),
    ("오버드라이브", "오버드라이브 전압 (Vov = VGS - VTH)"),
    ("싱글 엔디드/싱글엔디드", "싱글 엔디드 (Single-ended)"),
    ("커먼 모드/시엠", "커먼 모드 (VCM, Common-mode)"),
    ("다이오드 커넥티드", "다이오드 커넥티드 (Diode-connected)"),
    ("바디 이펙트/바디 효과", "바디 이펙트 (Body effect)"),
]

CHAPTER_TITLES = {
    9: "캐스코드 증폭기와 전류 거울 (Cascode Stages and Current Mirrors)",
    10: "차동 증폭기 (Differential Amplifiers)",
    11: "증폭기의 주파수 응답 (Frequency Response of Amplifiers)",
}


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


def infer_chapter(repo_root: Path | str, mmdd: str) -> int:
    """Infer chapter number from 복습노트/ or latest 강의노트/."""
    repo = Path(repo_root)

    # 1. 복습노트/ 디렉터리 확인
    review_root = repo / "복습노트"
    if review_root.is_dir():
        folders = sorted([
            nfc(d.name) for d in review_root.iterdir()
            if d.is_dir() and re.fullmatch(r"\d{4}", nfc(d.name))
        ])

        # mmdd 이하 중 가장 최근 복습노트
        past_folders = [d for d in folders if d <= mmdd]
        target_folder = past_folders[-1] if past_folders else (folders[-1] if folders else None)

        f_dir = review_root / target_folder / ".assets" if target_folder else None
        if f_dir and f_dir.is_dir():
            for f in f_dir.iterdir():
                name = nfc(f.name)
                # .assets/정리노트_MMDD_<slug>.md 검사
                if name.startswith(f"정리노트_{target_folder}_") and name.endswith(".md"):
                    # 파일명 자체에서 우선 판정
                    if "Cascode" in name or "캐스코드" in name:
                        return 9
                    if "Differential" in name or "차동" in name:
                        return 10
                    if "Frequency" in name or "주파수" in name:
                        return 11

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

    # 2. mmdd가 기존 복습노트 범위 이후일 경우 (새 강의노트 탐색)
    lec_dir = repo / "강의노트"
    if lec_dir.is_dir():
        lec_files = sorted([nfc(f.name) for f in lec_dir.iterdir() if f.suffix == ".pdf"])
        if lec_files:
            latest_pdf = lec_files[-1]
            if "FrequencyResponse" in latest_pdf or "Ch11" in latest_pdf:
                return 11
            if "Differential" in latest_pdf or "Ch10" in latest_pdf:
                return 10
            if "Cascode" in latest_pdf or "Ch9" in latest_pdf:
                return 9

    # 기본 fallback: 10장 (차동 증폭기)
    return 10


def get_chapter_title(repo_root: Path | str, chapter: int) -> str:
    """Find chapter title from dictionary or 강의노트."""
    if chapter in CHAPTER_TITLES:
        return CHAPTER_TITLES[chapter]

    repo = Path(repo_root)
    lec_dir = repo / "강의노트"
    if lec_dir.is_dir():
        for f in lec_dir.iterdir():
            name = nfc(f.name)
            m = re.search(rf"Ch0?{chapter}_([A-Za-z0-9_&]+)", name)
            if m:
                return m.group(1).replace("_", " ").strip()

    return f"{chapter}장"


COMMON_STOPWORDS = {
    "and", "the", "for", "with", "from", "that", "this", "page", "slide",
    "considerations", "nonidealities", "proportional", "respectively",
    "engineering", "ickjin", "kwon", "university", "department", "fall",
    "lecture", "edition", "chapter", "example", "figure", "table", "section"
}


def extract_chapter_terms(repo_root: Path | str, chapter: int, max_terms: int = 80) -> list[str]:
    """Extract key circuit terms from lecture PDF and textbook."""
    repo = Path(repo_root)
    extracted: set[str] = set()

    # 1. 핵심 필수 공통 회로 어휘 (항상 최우선 보장)
    chapter_seeds: dict[int, list[str]] = {
        9: [
            "캐스코드", "커런트 미러", "출력 임피던스", "전압 헤드룸", "소신호 출력 저항",
            "Cascode", "Current Mirror", "gm", "ro", "r파이", "re", "Rout", "R_out", "VA"
        ],
        10: [
            "디퍼렌셜 페어", "차동 증폭기", "차동 신호", "동상 신호", "하프 서킷",
            "버추얼 그라운드", "AC 그라운드", "테일 커런트", "테일 소스", "테일 노드",
            "커먼 모드", "커먼 모드 리젝션", "CMRR", "소신호 해석", "스몰 시그널",
            "Differential Pair", "Differential Amplifier", "Half-Circuit",
            "Virtual Ground", "Tail Current", "Common-Mode", "gm", "ro", "r파이", "re"
        ],
        11: [
            "주파수 응답", "밀러 효과", "밀러 커패시턴스", "지배적 극점", "유니티 게인 주파수",
            "차단 주파수", "기생 커패시턴스", "고주파 모델", "극점", "영점", "보데 플롯",
            "Frequency Response", "Miller Effect", "Dominant Pole", "Cgs", "Cgd", "fT", "wT"
        ],
    }

    base_seeds = [
        "MOSFET", "BJT", "소신호", "대신호", "트랜스컨덕턴스", "출력 저항", "오버드라이브 전압",
        "얼리 전압", "채널 길이 변조", "바디 이펙트", "다이오드 커넥티드",
        "gm", "ro", "r파이", "re", "gmb", "VTH", "VGS", "VDS", "VBE", "VCE", "IC", "ID", "ISS", "IEE"
    ]

    # 2. 강의노트 PDF 매칭
    lec_dir = repo / "강의노트"
    pdf_paths: list[Path] = []
    if lec_dir.is_dir():
        for f in lec_dir.iterdir():
            name = nfc(f.name)
            if chapter == 9 and ("Ch9" in name or "Cascode" in name):
                pdf_paths.append(f)
            elif chapter == 10 and ("Ch10" in name or "Differential" in name):
                pdf_paths.append(f)
            elif chapter == 11 and ("Ch11" in name or "FrequencyResponse" in name):
                pdf_paths.append(f)

    # 교과서 장 PDF도 추가
    tb_dir = repo / "교과서" / "마이크로전자회로"
    if tb_dir.is_dir():
        for f in tb_dir.iterdir():
            if nfc(f.name).startswith(f"{chapter}장"):
                pdf_paths.append(f)

    if fitz:
        for pdf_path in pdf_paths:
            try:
                doc = fitz.open(pdf_path)
                full_text = "\n".join(page.get_text() for page in doc)

                # (1) 영문 회로 기호 및 용어
                for m in re.finditer(r"\b[A-Za-z]{2,}(?:-[A-Za-z0-9]+)?\b", full_text):
                    word = m.group(0)
                    if word.lower() not in COMMON_STOPWORDS and len(word) >= 2:
                        extracted.add(word)

                # (2) 한글 회로 전문용어 패턴
                circuit_pat = re.compile(
                    r"[가-힣]{2,8}(?:증폭기|스테이지|회로|해석|바이어스|전류|전압|저항|임피던스|접지|노드|커런트|커패시턴스|극점|영점|신호|소자|모스|에미터|컬렉터|베이스|드레인|소스|게이트|하프|페어)"
                )
                for m in circuit_pat.finditer(full_text):
                    extracted.add(m.group(0))

                # (3) 괄호 안 영문 병기
                for m in re.finditer(r"([가-힣]{2,10})\s*\(([A-Za-z0-9_\s]+)\)", full_text):
                    extracted.add(m.group(1).strip())
                    en = m.group(2).strip()
                    if len(en) < 25 and en.lower() not in COMMON_STOPWORDS:
                        extracted.add(en)
            except Exception:
                pass

    # 결과 구성: 단원별 핵심 시드 -> 공통 시드 -> 추출 용어 순
    combined: list[str] = []
    seen: set[str] = set()

    for item in chapter_seeds.get(chapter, []) + base_seeds:
        if item not in seen:
            seen.add(item)
            combined.append(item)

    sorted_extracted = sorted(extracted, key=lambda x: (-len(x), x))
    for item in sorted_extracted:
        if item not in seen:
            seen.add(item)
            combined.append(item)
            if len(combined) >= max_terms:
                break

    return combined[:max_terms]


def build_stt_prompt(chapter: int, chapter_title: str, terms: list[str]) -> str:
    """Format domain guidance block to inject into the subagent STT prompt."""
    sample_terms = ", ".join(terms[:50])
    homophone_guide = "\n".join(f"  - '{err}'로 들리면 -> '{cor}'" for err, cor in COMMON_EC2_ERROR_RULES)

    return f"""[전자회로2 강의 도메인 가이드 (Razavi Fundamentals of Microelectronics)]
- 본 오디오는 아주대학교 전자공학과 전자회로2 (권익진 교수님) 강의 녹음입니다.
- 단원 범위: {chapter}장 {chapter_title}
- 주요 전자회로 고유명사 및 파라미터:
  {sample_terms}

- 필수 전사 및 발음 교정 규칙:
  1. 전자회로 표준 용어 최우선: 교수님의 발음이 뭉개지거나 일상 단어로 들리기 쉬운 경우, 회로 이론 문맥상 올바른 전자회로 표준 용어로 정확히 전사하세요.
{homophone_guide}
  2. 표기 원칙: 회로 기호 및 수식 파라미터 약어(gm, ro, r파이, re, VTH, VGS, VDS, VCM, CMRR, ISS, IEE 등)는 통용되는 수식/기호 표기를 따르세요.
  3. 철저한 축어성(Verbatim): 요약이나 어미 생략 없이 실제 발화된 내용을 있는 그대로 기록하세요.
"""


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
    chapter = args.chapter if args.chapter else infer_chapter(repo, date)
    chapter_title = get_chapter_title(repo, chapter)
    terms = extract_chapter_terms(repo, chapter)
    prompt_guide = build_stt_prompt(chapter, chapter_title, terms)

    if args.prompt_only:
        print(prompt_guide)
        return

    result = {
        "audio": args.audio,
        "date": date,
        "chapter": chapter,
        "chapter_title": chapter_title,
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
        print(f"진도 단원: {chapter}장 ({chapter_title})")
        print(f"추출 용어: {len(terms)}개")
        print(f"최종 저장: STT/{date} 전회2.md")


if __name__ == "__main__":
    main()
