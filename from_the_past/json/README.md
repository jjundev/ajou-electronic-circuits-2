# AI 선별용 기출 JSON

MD를 원본으로 유지하면서 전체 기출을 JSON으로 보관한다. PDF 템플릿용 HTML·base64 JSON과는 별개다.

- `index.json`: 문항 ID·제목·관련 장·의존성·전체 소문항·필요 개념·상세 경로.
- `problems/<id>.json`: MD 전체 문자열, 순서 있는 절, 원본 메타데이터, 시험 메모, 원본/다시 그린 그림 경로, 입력 해시.
- `detail_path`는 이 폴더 기준이고 `md_path`, 그림·input_hashes 경로는 저장소 기준이다. 경로의 Unicode 표기는 실제 파일을 따른다. ID는 NFC다.
- `adoption_unit: whole`: 복습문제로는 문항 전체만 채택한다. 일부 소문항이 범위 밖이면 그 문항은 제외한다.
- `eligible`은 참고 풀이 존재 여부이며 정확성 인증이 아니다. 풀이 없는 문항도 카탈로그에는 남는다.

저장소 루트에서 생성·검사한다.

```bash
python3 workbook/exam_catalog.py build
python3 workbook/exam_catalog.py check
```

두 명령은 Python 3.10+와 기존 PyYAML을 사용한다. `check`는 입력과 JSON의 바이트 동등성을 확인하며 변경·누락·남은 상세 파일에 종료 코드 1을 반환한다. `build`는 개별 JSON을 임시 파일로 쓴 뒤 교체하고 index를 마지막에 교체한다. 전체 디렉터리 트랜잭션은 아니므로 중단 후에는 check하고 재생성한다.

## 해석 메타데이터

문항 MD frontmatter의 `selection`이 분류의 원본이다. topics/circuit_types/required_concepts/learning_goals/evidence_sections는 문자열 목록이고 subpart_requirements는 `{label, required_concepts}` 목록이다. 태그는 초기 탐색용이며 원문 사실과 구분한다.

- `unclassified`: 분류 없음. 후보에서 자동 제외하지 않는다.
- `draft`: 아직 원문·회로·풀이를 함께 대조하지 않은 초기 분류. 수업 범위 적합성이나 정답을 검증한 상태가 아니다.
- `reviewed`: 해당 내용에 대해 분류를 검토하고 해시를 맞춘 상태. 정답 검산이나 특정 수업 범위 승인은 아니다.
- `stale`: MD 내용·시험 정보·그림/그림 설정과 분류 당시 해시가 달라짐. 다시 읽고 분류를 검토한다.

`reviewed_content_sha256`는 selection 자체를 제외한 메타데이터·본문·시험/그림 입력의 해시다. 검토 후 `workbook/exam_catalog.py`의 `content_hash(Path(md))`로 구한 값을 넣는다. 해시만 새로 대입해 검토를 생략하지 않는다. 소문항 개념은 비망라적이므로 전역 필요 개념과 전체 내용을 함께 읽는다.

61문항의 분류 대조 결과와 문항별 주의점은 [분류 검토 기록](../classification-review.md)에 둔다. `classification_note`에는 해당 문항의 회로 구조·조건·풀이에 근거한 분류 이유를 적는다. 원문 오식·출력 정의·근사 등 해석상 주의점이 있으면 함께 읽고 채택을 판단한다.

## 복습팩에서 사용

`ec2-review-pack`의 problem_index.py가 최신 MD에서 RUN 아래에 카탈로그를 만들고 관련 장·풀이·사용 이력을 반영한 candidates.json을 제공한다. 저장 카탈로그를 고치거나 생성물을 직접 편집하지 않는다. AI가 전체 내용과 실제 회로 그림을 확인한 뒤 기존 ID를 manifest에 채택한다. selection.json에 선택 이유와 해시를 기록하고 기존 PDF/문제설명 도구가 MD에서 문제를 가져온다.

JSON 생성·해시 검사는 원본 PDF 대조나 정답의 독립 검산이 아니다. 문제설명의 기존 발행 검토 절차를 유지한다.
