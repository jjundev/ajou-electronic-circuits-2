# 문제풀이 영상의 지침 발화 제거와 청크 동기화 설계

## 목표와 완료 기준

P10.72 영상의 음성 생성 지침 발화와 자막 싱크 오류를 함께 수정한다. 자막 한 청크에 읽을 대본 한 청크를 명시적으로 대응시키고, 생성된 PCM의 실측 샘플 위치로 자막 시간을 결정한다. 필기·회로·원본 PDF의 의미와 단계는 유지한다.

실제 발화에 지침·추가 발화·누락이 없고, 최종 MP4의 모든 청크 전환이 대응하는 음성 경계와 일치해야 완료다. 자동 검사만으로 실제 청취를 승인하지 않는다. 청취 수단이 없다면 기술 검증 결과와 청취 미검증 상태를 함께 전달하고 게시 게이트를 유지한다.

## 확인한 원인

- `.agents/skills/ec2-review-video/scripts/lib/vertex_tts.py:23`은 direction과 원고를 같은 텍스트 입력에 연결한다.
- 문제풀이 기본 direction에는 “수식은 뜻을 설명하며 정확하게 읽습니다. 과장하지 않습니다.”가 들어 있다. 사용자가 27초에서 유사한 발화를 들었다고 보고했다. 직접 청취로 확인한 원인은 아니지만, 이 지침이 요청에 들어가는 경로는 코드로 확인됐다.
- `.agents/skills/ec2-solution-video/scripts/solution_video/subtitles.py:129`는 caption_text 글자 수 비율로 cue 시간을 계산한다. 실제 문장 발화 경계를 측정하지 않는다.
- 기존 manifest는 PageMap 단계마다 write segment 하나를 요구하고, 렌더는 segment별 WAV를 사용한다. 내부 청크를 추가해 이 계약을 유지한다.

## 결정

1. 문제풀이 영상 전용 요청 생성기는 읽을 대본만 텍스트 입력에 넣는다. direction과 “원고:” 같은 안내 문구는 전송하지 않는다. Aoede·언어·모델·오디오 형식은 설정 필드로 유지한다.
2. 공용 ec2-review-video의 코드·출력은 수정하지 않는다. 기존 transport, 비밀정보 처리, cache와 budget을 재사용하면서 문제풀이 전용 합성을 만든다.
3. 기존 segment 내부에 chunks를 추가한다. 각 chunk는 id, text, caption_text를 갖고 자막 cue 하나에 대응한다. 현재 47개 cue를 시작점으로 원문 의미와 대응시킨다.
4. 새 동기화 모드에서는 전 segment에 청크가 있어야 한다. 일부 청크가 빠졌다고 글자 수 방식으로 대체하지 않는다. 기존 청크 없는 legacy 실행은 기존 타이밍으로 읽되 새 동기화 완료로 표시하지 않는다.
5. 청크별 WAV를 생성하고 segment WAV로 순서대로 연결한다. 원시 PCM을 연결하며 중간 AAC 인코딩을 하지 않는다. 청크 시작·끝은 실측 샘플의 누적값이다.
6. 기본은 청크 WAV 전체를 사용한다. 긴 앞뒤 무음은 사람이 확인한 정수 샘플 절단 위치를 명시했을 때만 자른다. 자동 에너지 탐지로 약한 발음을 잘라내지 않는다. 원본 WAV는 보존한다.
7. 자막은 같은 절단본의 청크 경계를 따른다. SRT 밀리초 반올림 오차는 1ms 이하이고, 30fps 영상의 표시 전환 허용치는 1프레임이다. 단어 내부 동기화는 범위 밖이다.
8. 청크 간 추가 무음을 자동 삽입하지 않는다. 발화 자체의 쉼은 WAV에 포함한다. 필기·카메라 때문에 생기는 segment 끝 hold에는 마지막 자막을 늘리지 않는다.
9. 요청 방식과 실제 전송 대본을 캐시 키에 포함한다. 기존 지침 포함 요청의 캐시는 재사용하지 않는다. caption_text 변경만으로 TTS를 재생성하지 않는다.
10. P10.72 기존 자료를 보존하고 새 sibling run에서 전체 음성을 새 방식으로 생성한다. source snapshots·glyph·shape·PageMap·기존 step ID는 보존한다. 청크 표시는 기존 숫자·기호 규칙을 따른다.

## 데이터 흐름

manifest → 청크 대응 검증 → spoken-text-only TTS → 청크 WAV/영수증 → 선택적 명시 절단 → segment PCM 연결 및 상대 샘플 경계 → 필기 타임라인의 절대 샘플 경계 → SRT → 최종 MP4 → 자동 검사 및 실제 청취/재생 검토.

### 데이터 계약

- manifest schema_version은 1을 유지하고 `caption_timing: "pcm-chunks-v1"`을 추가한다.
- segment.chunks: 비어 있지 않은 `{id, text, caption_text}` 목록. id는 segment 내부에서 고유한 안전한 ASCII 식별자다. 합성 ID는 `segment_id + "__" + chunk_id`이며 전체 요청에서 중복을 거부한다.
- 공백 정규화 후 청크 text들을 공백으로 연결한 값은 부모 text와 같아야 한다. caption_text에도 같은 규칙을 적용한다. 표시용 자동 온점 처리는 기존 caption 규칙과 일치시킨다.
- 각 청크 caption_text는 기존 `split_caption` 결과가 정확히 하나여야 한다. 화면상 두 줄 줄바꿈은 허용한다.
- `source/chunk-audio.json`: 정책 버전과 청크 합성 영수증 목록. 원본 WAV, 실제 payload hash, samples, rate, sha256, key, usage를 기록하며 비밀정보를 기록하지 않는다.
- 선택적 `source/chunk-trims.json`: schema_version=1, rows에 segment_id, chunk_id, raw_sha256, start_sample, end_sample, reason. `0 <= start_sample < end_sample <= raw_samples` 정수 범위만 허용하고 오래된 raw_sha256은 거부한다.
- `source/audio.json`: 기존 voices 목록을 유지한다. 청크 모드의 segment 영수증에는 순서 있는 chunks를 추가한다. 각 row는 id, source_id, raw_sha256, trim_start_sample, trim_end_sample, start_sample, end_sample을 가지며 start/end는 segment WAV에 대한 상대 위치다.
- timeline은 `caption_timing`과 `caption_cues`를 가진다. 각 cue는 segment_id, chunk_id, caption_text, start_sample, end_sample을 가지며 시간은 전체 영상의 절대 샘플 위치다.
- `verification/chunk-sync.json`: manifest·청크/segment WAV·timeline·SRT 해시와 구조 검증 결과. 실제 청취를 했다는 증거로 사용하지 않는다.
- 청크 모드의 audio-review에는 기존 검토 필드와 함께 모든 청크의 segment_id, chunk_id, transcript_match, no_instruction_speech, natural_join, sync_passed, notes를 기록한다. passed에는 모두 true와 실제 검토자의 확인이 필요하다.

## 검증 및 재발 방지

지침을 포함하지 않는 실제 요청 검사, 부분 실패 후 캐시 재개, 다른 길이의 합성 PCM 연결, 캡션 축약 후 동일 음성/시간 유지, 누락·중복·잘못된 절단·변조 WAV 차단, legacy 호환, 실제 청취 없는 게시 차단을 테스트한다. 재생성 뒤 27초 문제의 대응 segment와 모든 전환을 실제로 검토한다. 새 영상은 길이가 바뀌므로 과거 27초라는 시간에만 의존하지 않는다.

자동 검사와 실제 청취/재생 검토를 분리한다. 청취 완료가 없으면 complete/live_audio를 승인하지 않는다. 실제 모델 출력은 지침을 제외해도 발화 추가 가능성이 있으므로 구조 검사만으로 정확한 낭독을 주장하지 않는다.

## 범위 밖

단어 강조 자막, 별도 STT/forced-alignment 엔진, 공용 review-video 변경, 원본 PDF 풀이 수정, 기존 산출물 삭제, 자동 커밋·푸시. 구현 계획에는 범위별 커밋 지점을 두지만 커밋 실행은 사용자의 Git 지시를 따른다.
