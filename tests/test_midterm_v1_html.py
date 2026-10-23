from pathlib import Path
from bs4 import BeautifulSoup


def test_midterm_v1_explanation_html():
    html_path = Path("중간고사대비/v1/문제해설_중간고사대비_v1.html")
    assert html_path.is_file(), f"{html_path} does not exist"
    content = html_path.read_text(encoding="utf-8")
    assert len(content) > 5000, "HTML file is too short"
    soup = BeautifulSoup(content, "html.parser")

    # 5개 문항 topic section 존재 확인
    topics = soup.find_all("section", class_="topic")
    assert len(topics) == 5, f"Expected 5 topic sections, found {len(topics)}"

    # 7개 레이어 키워드 확인
    required_layers = [
        "문제를 읽어요",
        "이 개념과 공식을 떠올려요",
        "종이에 쓸 첫 줄",
        "이렇게 풀어요",
        "완성 답과 검산",
        "주의할 점",
        "조건을 바꾸어 생각해요"
    ]
    first_topic_text = topics[0].get_text()
    for layer in required_layers:
        assert layer in first_topic_text or any(layer in t.get_text() for t in topics), f"Missing layer keyword: {layer}"

    # 모든 5개 문항에 7개 레이어가 모두 존재하는지 검증
    for idx, t in enumerate(topics, start=1):
        text = t.get_text()
        for layer in required_layers:
            assert layer in text, f"Topic Q{idx} is missing layer: '{layer}'"

    # 헤더 필수 구성요소 확인 (진행률 바, 테마 토글, 바로가기 링크)
    assert soup.find(id="theme-toggle") or soup.find(class_="theme-toggle"), "Missing theme toggle button"
    assert soup.find(class_="bar") or soup.find(id="progress-bar") or soup.find(class_="progress"), "Missing progress bar"
    nav_links = soup.find_all("a", href=lambda h: h and h.startswith("#q"))
    assert len(nav_links) >= 5, f"Expected at least 5 navigation anchor links, found {len(nav_links)}"

    # KaTeX 및 Pretendard 포함 확인
    assert "katex" in content.lower(), "Missing KaTeX inclusion"
    assert "pretendard" in content.lower(), "Missing Pretendard font inclusion"

    # SVG 회로도 7개 포함/참조 확인
    svg_figures = ["fig-Q2a", "fig-Q2b", "fig-Q3a", "fig-Q3b", "fig-Q4a", "fig-Q4b", "fig-Q5"]
    for fig in svg_figures:
        assert fig in content, f"Missing figure {fig} in HTML"
