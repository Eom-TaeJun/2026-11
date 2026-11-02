# 다음 조사에서도 이어 쓰는 방법

## 1. 작업을 시작한다

AGENTS.md와 agents/roles.json을 읽고 대상 질문·기간·이전 판단을 정한다. 환경 변화와 기업 분석은 순서를 지킨다. 호스트의 에이전트 실행 기능에 역할별 지침을 전달한다. 역할 파일은 모델 실행 서비스가 아니며 별도 API 키나 상시 서버를 요구하지 않는다.

## 2. 근거를 추가한다

공식 원문을 실제로 열고 제목·URL·발행일·확인일·읽은 위치·핵심 요약·활용한 내용·한계를 적는다. 검색 결과에서 발견한 문서는 unread로, 공식 소개만 읽은 보고서는 official_summary로 기록한다. PDF 전문을 저장하지 않아도 원문 링크와 정확한 절·쪽수로 돌아갈 수 있어야 한다.

data/sources.json의 기존 자료 ID가 있으면 갱신하고, 새 자료만 새 ID를 부여한다. 주장 원장에서 source_ids와 topic_ids를 연결한다. facts와 hypotheses를 한 문장에 섞지 않는다. 세부 필드는 [자료 형식](schemas/records.md)에 있다.

## 3. 변경 이유를 붙여 병합한다

변경 파일은 sources·claims·topics 배열 중 바뀌는 항목과 change_reason을 가진 JSON이다. 기존 ID의 전체 새 레코드를 넣는다. 삭제 대신 상태를 superseded/withdrawn으로 바꾼다. 실제 새 근거가 기존 판단의 어느 부분을 바꾸는지 설명한다.

```sh
python scripts/research.py ingest path/to/batch.json
python scripts/research.py build
python scripts/research.py validate
python -m unittest discover -s tests -v
```

ingest는 검증 후 이전·이후 상태와 해시를 history/에 보존한다. 동일 내용 재입력은 기록을 늘리지 않는다. 현재 구현은 독립 체크아웃에서 한 작성자가 쓰는 방식이며 동시에 여러 프로세스로 쓰지 않는다. 중단되면 history 기록과 data/를 대사해 복구하고 검증·재생성한다. 자동 분산 트랜잭션을 구현한 것은 아니다.

## 4. 저장된 자료에서 찾는다

```sh
python scripts/research.py search "환매 은행 현금" --mode lexical
python scripts/research.py search "tokenized capital" --mode graph
```

lexical은 명시적 단어·부분문자열 기준선이다. graph는 같은 주장에 연결된 다른 근거를 추가로 탐색한다. 결과는 답변이 아니라 원문을 다시 확인할 후보 목록이다. 임베딩·벡터DB·LLM 생성이나 상용 GraphRAG 엔진은 현재 실행 경로에 없다. 용어 변형·복잡한 의미 검색의 품질은 보장하지 않는다.

## 5. AI 도구를 추가할지 결정한다

기준선의 구체적 실패가 있을 때만 최근 검증판의 도구를 비교한다. 같은 근거 묶음과 처음 보는 질문으로 인용 정확성·잘못된 날짜·주장 혼합·정정 전파·검토시간·비용을 측정한다. 원문 중복, 법인 혼동, 제안/시행 혼동, 환매/은행현금 혼동을 포함한다. 작은 개발용 검사는 일반 성능이나 사람시간 절감의 증거가 아니다.

선택 결과와 버전은 reports/02_ai_methods.md 및 data/ai_tools.json에 남긴다. 인기 수치는 data/ai_star_history.json에서 관측 범위와 정의를 보존한다. 알려진 출시일과 현재 릴리스를 월별 인기와 구분한다.

원본 스냅샷의 월별 집계는 외부 연결 없이 다음 명령으로 재현한다. `refresh`만 네트워크를 사용하며 기존 파일을 덮어쓰지 않는다. 요청 제한이 있으면 Retry-After를 기록하고 자동 대기·재시도는 하지 않는다.

```sh
python scripts/ai_stars.py validate --input data/ai_star_history.json
python scripts/ai_stars.py aggregate --input data/ai_star_history.json --compare data/ai_tools.json
python scripts/ai_stars.py refresh --output snapshots/stars-YYYY-MM-DD.json
```

## 6. 결과를 저장한다

소스 카드·주제 위키·관계 데이터를 build로 갱신하고, 통합 분석과 다음 관측은 reports/에 쓴다. runs/에는 실제 실행한 에이전트·읽은 범위·완료한 확인·남은 공백을 기록한다. 현재 저장소에는 정기 수집·외부 메시지·거래 실행 일정이 없다. 이후 주기를 정할 경우 의미 있는 판단 변경만 알리고 중복·무변화는 조용히 처리한다.
