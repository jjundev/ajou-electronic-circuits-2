# 음성과 작성 타이밍

음성 설정은 assets/defaults.json, 작성 설정은 assets/writing-defaults.json이며 각각 source/config.json과 source/writing.json에 동결한다. Aoede/한국어/24kHz mono PCM, 1920×1080/30fps이며 모델과 공급자를 자동 대체하지 않는다. 환경 GOOGLE_API_KEY 또는 GEMINI_API_KEY를 사용한다. --env-file은 메모리로만 읽고 config/로그에 키를 넣지 않는다. budget_usd=null은 상한 없음이며 명시 상한을 주면 price 요율과 기존 예산 규칙을 따른다. 모든 문항은 batch/usage.json 하나를 쓴다.

문제를 확인하는 발화로 시작한다. 판단 이유(reason), 원문을 쓰는 동안의 설명(write), 계산 확인(check), 답 확인(summary)을 원자료에 연결한다. PDF에 없는 새 계산이나 풀이를 만들지 않는다. 한 발화가 길면 PageMap 단계도 작은 연속 단위로 나눈다. 실패한 문항만 재개하고 성공 WAV는 내용/설정 해시로 재사용한다.

연필 기본은 최대 5글자/초이며 인접 글자마다 이동 1프레임 + 작성 5프레임이다. 긴 이동·줄바꿈·단계 이동은 최소 8프레임 이동을 사용하고 작성 시간을 줄이지 않는다. write 구간은 max(실제 WAV 길이, 모든 이동·작성 길이)+ceil(0.75×30)=23프레임이다. typing 선택은 기존 ceil(30/7) 프레임 간격을 사용한다. 작성 파일이 없는 legacy 실행은 기존 config의 속도/hold를 그대로 쓴다. 공백은 이동 시간만 사용하며 연필은 숨긴다. shape는 같은 단계의 anchor glyph 완료 시점에 공개한다. 전체 타이밍은 800샘플=1프레임이며 실제 PCM은 자르거나 늘이지 않고 남는 구간을 무음으로 채운다. 마지막은 최소 1초 전체 답안 확인이다. 단어별 실제 음성 정렬을 주장하지 않는다.

writing.json의 키: schema_version=1, mode=pencil|typing, chars_per_second=5(typing 기본 7), pencil_length_px=160, adjacent_move_frames=1, lifted_move_frames=8, tilt_degrees=2, read_hold_seconds=0.75, asset_id=pencil-yellow-v1. 명시 설정의 속도는 유한 수 0<값<=7, 길이는 양의 유한 수, 이동은 양의 정수, 기울기는 0~2°, hold는 0 이상의 유한 수다. 잘못된 값·알 수 없는 키/모드/asset은 실패한다.

`retime --run RUN --writing-config /ABS/writing.json`은 현재 내용 게이트와 voice 선행 단계, 모든 WAV의 샘플 수·mono·16-bit·24kHz·SHA256을 확인하고 저장 음성만 재배치한다. 공급자·usage ledger·음성 승인·WAV를 수정하지 않으며 paid_requests=0이다. 검증 실패 시 기존 timeline을 덮어쓰지 않는다. 성공 후 assemble부터 다시 실행한다.

연필 asset은 assets/pencil/pencil-yellow-v1.png 및 JSON이다. JSON의 tip_px/end_px로 촉 중심 회전과 화면 길이를 계산한다. PNG 형식·RGBA alpha·해시·좌표를 검사하고 composition에 복사한다. 실제 획순 데이터 없이 원본 SVG를 점진 공개하므로 획순 필기로 설명하지 않는다. 효과음은 추가하지 않는다.

개발 테스트는 fake transport와 로컬 PCM만 사용한다. 실제 Aoede 품질/발음/의미는 최종 파일을 청취하여 별도 현재 audio-review로 확인한다. fake PCM의 기술 검사로 실제 음성 의미 검토를 통과 처리하지 않는다.
