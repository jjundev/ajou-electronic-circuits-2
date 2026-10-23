# 답안 도형 필기 속도 설계

## 의도와 근거
P10.72 신규 검토 영상의 마지막 write_part_3_0은 219.3667초에 시작한다. 음성은 19.7638초, 필기는 29.5초다. 답 상자 s00203의 24조각에 각각 최소 18프레임을 부여해 상자 draw만 432프레임(14.4초)을 쓴다. reveal.py:42의 조각별 최소 시간이 원인이다. reveal.py:40–41은 줄 변경 여부를 unit 내부의 모든 대상에 적용할 수 있다. narration_pacing.py:61–63은 긴 무음에 자유로운 이유만 있으면 통과시켜 필기 지연을 완성 화면 읽기로 오인할 수 있다.

## 확정 결정
1. 공통 spatial pencil 타이밍을 수정한다. 글자는 기존 7.5 chars/sec, interval=ceil(30/chars_per_second)를 유지한다.
2. 같은 step_id+shape_id의 전체 가로 폭 W와 representative_height H로 B=min(90,max(18,ceil(W/H*interval))) 프레임의 도형 draw 예산을 계산한다. 수직선 등 W=0인 도형은 한 조각에 18프레임을 부여한다. 이는 가로 공개 속도이며 둘레/실제 획순 모델이 아니다.
3. 양의 폭을 가진 각 clip에 전체 B를 폭 비례로 배분한다. 각 조각은 최소 1프레임, 합계는 B. 1프레임 하한을 적용한 비례 배분 후 최대 나머지 순서로 정수화하며 동률은 authored 순서로 정한다. 조각 수가 B보다 많으면 shape_id와 counts를 포함한 InputError로 저작 수정을 요구한다. 기존 완전 clip coverage 검사는 유지한다.
4. 들어 옮기기 비용은 새 줄의 첫 대상에만 적용한다. 기존 카메라 전환 12프레임, 일반 이동 비용, 글자/도형 공개 순서, 원본 PDF glyph/shape geometry는 유지한다.
5. 음성 종료는 PCM 영수증의 정확한 끝을 영상 프레임으로 올림한 시점이다. 음성 이후 필기가 60프레임(2초)을 초과하면 review-required다. 실제 speech energy 무음 검사는 따로 유지한다.
6. 필기 종료 이후 완성 화면 hold는 segment 끝-max(음성 끝,필기 끝)으로 계산한다. 이를 필기 중 무음과 구분한다. 2초 초과 필기 지연의 명시적 예외는 현재 input_hash를 가진 별도 writing_lags row에서만 승인한다. 기존 gaps 자유문구로 필기 지연을 승인할 수 없다.
7. #7 권장값 2초 초과 검토는 사용자 후속 writing-plans 호출로 confirmed by default. 실행은 기존 Native 방식 유지.

## 변경 범위
도형 draw 예산 helper, reveal integration/줄 이동, narration_pacing 보고서와 예외 형식, state fingerprint, 관련 tests/skill references. 음성/대본/PDF/청크 분할/typing/기존 non-spatial 동작을 변경하지 않는다. 음성 재합성 없이 retime→assemble→render→captions→verify한다. 앞 구간도 시간 변경에 영향을 받으므로 전체를 검토한다. 단어별 필기 발화 정렬은 범위 밖이다.

## 완료 기준
동일 도형을 다른 clip 수로 분할해도 허용 가능한 예산 내에서는 전체 draw 프레임이 같다. clip coverage와 최종 PDF 대응은 유지된다. 실제 P10.72 마지막 필기 지연은 60프레임 이하여야 하며 예외로 우회하지 않는다. 전체 하드 자막본에서 필기/카메라/청크 자막을 검증하고 raw/joined WAV SHA256이 보존되며 유료 요청은 0이다. 실제 청취가 불가능하면 audio_meaning=unverified/complete=false를 유지하고 publish/latest는 갱신하지 않는다. 기존 영상/검토 증거를 보존한다.

## 실행 중 확인한 구도 보완
글자 없는 shape-only chunk는 글자 높이에 맞춘 확대 대신 페이지 전체와 연필 여백이 들어오는 구도를 사용한다. 빈 상자 오른쪽으로 확대돼 답안이 사라지는 현상을 막는다. glyph가 있는 chunk의 26px 최소 크기/기존 전환은 유지한다. writing_camera.py와 test_writing_camera.py의 test_shape_only_chunk_keeps_page_context가 담당하며 RED→GREEN 확인 후 assemble/render/captions/verify를 다시 수행한다.
