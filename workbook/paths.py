"""문제집 생성기의 저장소 경로. import하면 기존 도구 폴더(check_md, crop_figures, crop_exam)를 sys.path에 넣는다."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK = ROOT / "교과서" / "마이크로전자회로"
EXAMS = ROOT / "from_the_past" / "md"
WORKBOOK = ROOT / "workbook"
TEMPLATES = WORKBOOK / "templates"
# 렌더 때 CDN 대신 쓰는 KaTeX·Pretendard 사본 (vendor_route.py)
VENDOR = ROOT / ".claude" / "skills" / "ec2-problem-explain" / "assets" / "vendor"

for _tools in (TEXTBOOK / "_tools", EXAMS / "_tools"):
    if str(_tools) not in sys.path:
        sys.path.insert(0, str(_tools))
