# 회로 검토 기록

`source/circuit-review.json`은 에이전트가 원자료·대본·SVG·수치 상태를 대조한 기록이다. 프로그램은 아래 구조와 현재 입력 일치만 검사한다. 물리적 정확성의 자동 증명이나 SPICE 검증으로 소개하지 않는다.

`lib.circuit.circuit_fingerprint(Path(RUN), manifest)`로 현재 input_hash를 얻는다. 입력은 manifest, source/inputs.json, 동결 출처, scene-fragments와 fragment가 참조하는 로컬 시각 자산이다. 보고서 자신·음성·검증 결과를 포함하지 않는다.

```json
{
  "schema_version": 1,
  "input_hash": "현재 circuit_fingerprint 값",
  "scenes": [{
    "scene_id": "scene-dm",
    "checks": [{
      "domain": "model",
      "status": "passed",
      "reason": "원문이 이상적 MOS 소신호 차동쌍이며 대본과 그림도 이 조건을 유지한다.",
      "source_ids": ["src-note"],
      "locators": ["#small-signal-differential-pair"]
    }]
  }],
  "evidence": [{"path": "source/numeric-states.json", "sha256": "해당 파일의 SHA256"}]
}
```

예시는 축약했다. **모든 장면에 아래 여섯 domain을 정확히 한 번씩** 쓴다. status는 passed 또는 not-applicable이며 이유는 필수다. passed는 존재하는 source_ids와 구체적인 locators를 요구한다. 해당 없는 장면 요소만 not-applicable로 설명하며 장면 전체를 건너뛰지 않는다. numerical evidence는 필요할 때만 만들고 RUN 내부 파일의 경로·해시를 기록한다.

| domain | 실제 대조 |
|---|---|
| model | MOS/BJT, DC 바이어스/AC 소신호, CM/DM, 단일 종단/차동 출력 정의 |
| topology | 연결, 소자 종류·단자, 노드, 전류원·부하·AC 접지; SVG 이동으로 연결 의미를 바꾸지 않음 |
| polarity | 전류 화살표, 입력·출력 차 순서, 이득의 부호; 그래프 색과 회로 상태의 대응 |
| derivation | 소신호 모델 → KCL/KVL → 대입 → 결과; 교수·교재 표기 g_m, r_O, R_out 유지 |
| assumptions | 포화/활성영역, 작은 입력, 대칭, 이상적 테일, r_O 무시 등 근사의 적용 구간 |
| numeric-visual | 독립 계산한 입력/출력·단위·대표 좌표와 표시값·발화·motion 최종 상태 일치 |

BJT에서 컬렉터 전류 합=이미터 테일 전류라고 쓰면 베이스 전류 무시 가정을 명시한다. 대칭 차동 입력의 가상 접지를 공통 모드 입력으로 일반화하지 않는다. 이상적 테일 전류원과 유한 R_SS의 공통 모드 응답을 구분한다. 캐스코드의 높은 출력 저항·이득에는 동작영역과 사용한 소신호 근사가 따른다.

직관 → 실제 회로 → 입력 변경과 원인 → 필요한 식 → 성립 조건 순으로 설명한다. 비유가 실제 전류/전압/에너지의 정의를 대체하지 않게 한다. 문제 원문과 풀이를 구분하고 모호한 조건은 원자료로 해결한다. 기출 답이나 누락 자료를 추측해 확정하지 않는다.

수치 예시는 `tests/fixtures/circuit-scene/`의 검증용 MOS 상태처럼 조건을 밝힌다. I_SS=100 μA, Δi=10 μA일 때 50±10 → 60/40 μA이며 합은 100 μA다. 예시는 수치 표시이며 실제 강의 회로나 시뮬레이션 결과라고 부르지 않는다. 계산식은 임의 문자열 eval로 실행하지 않는다.
