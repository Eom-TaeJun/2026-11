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

현재 환경의 수치·시행 단계·전망을 갱신할 때는 `data/macro_observations.json`, `data/regulatory_watch.json`, `data/scenarios.json`도 해당 source ID에 연결한다. 정책결정·실적·전망, 규칙의 효력일·개별 인가일을 구분한다. 이 보조 원장의 참조·날짜는 실행 기록의 추가 검사로 확인하며, 기본 `validate`가 모든 경제·법적 의미를 자동 판정하는 것은 아니다.

소스 카드·주제 위키·관계 데이터를 build로 갱신하고, 통합 분석과 다음 관측은 reports/에 쓴다. runs/에는 실제 실행한 에이전트·읽은 범위·완료한 확인·남은 공백을 기록한다. 현재 저장소에는 정기 수집·외부 메시지·거래 실행 일정이 없다. 이후 주기를 정할 경우 의미 있는 판단 변경만 알리고 중복·무변화는 조용히 처리한다.

## 7. 기업·국가·역할을 이어서 조사한다

`data/institution_connections.json`은 법인·파트너·관할·사업 단계와 다음 관측을, `data/institution_focus.json`은 역할별 고객·자금·수익 질문과 국별 조사 대기를 보존한다. 경남은행의 상세 비교는 `data/bank_customer_functions.json`에서 이어간다. 새로운 국가는 실제 계약·고객·자금 경로에 필요할 때 추가한다. 법률 조사는 기존 `regulatory_watch.json`과 연결하되 미검토 관할은 조사 대기로 남긴다. 보조 원장은 기본 validate의 의미 검증 대상이 아니므로 출처 참조·단계·날짜·법인 귀속을 실행 기록에서 추가 확인한다.

## 8. 규제 이후의 미래를 갱신한다

`data/regulatory_regimes_2027.json`은 국가·관할·상품별 현재 단계와 2027Q1/2027~28 조건부 전망을, `data/regulatory_calendar_2027.json`은 확정 효력·마감·목표·계산 기한을 분리한다. `data/regulatory_scenarios_2027.json`은 지급자·비용·반대 경로·판별 관측·확대/중단 조건을 보존한다. 같은 법률 안에서도 조항별 효력·경과조치를 읽고, 제안의 예정일은 effective_date 대신 target_date로 둔다. 이미 실행된 시범과 향후 확대 목표가 함께 있으면 두 단계를 함께 기록한다.

다음 조사에서는 사건의 변화가 권한·고객·현금·비용·유통 중 무엇을 바꾸는지 적는다. 날짜 도래만으로 사업 실현을 표시하지 않는다. 과거 판단 수정은 ingest 이력에 남기고 보조 원장·보고서·자료 카드의 날짜 표현을 함께 대사한다.

## 9. 탑다운 미래와 기관별 결정을 이어간다

사용자의 지속 목적은 `docs/RESEARCH_MANDATE.md`다. `reports/11`~`15`의 현재 판단과 `data/strategy_decisions_2027.json`의 12개 검토 과제를 먼저 읽는다. 보고서 파일명은 README의 링크를 사용한다. 환경을 갱신한 뒤 경남은행 본사·교보 미래전략·한화생명 신사업의 서로 다른 고객·권리·현금·수익으로 좁힌다.

`agents/professor_reasoner.md`의 질문으로 명시적 미래 가정, 고객의 하루, 경쟁자의 가격·제휴·상품 대응을 전개한다. 제도 지연과 제도 이후 경제성 부족을 구분한다. 실제 강의·기관 주장과 연구자의 재구성은 출처 카드에서 분리한다.

새 정보가 들어오면 해당 전략 ID의 source_ids·claim_ids, 대안·다음 관측, 확대·중단 조건만 갱신한다. 소식이 많아졌다는 이유로 우선순위를 올리지 않는다. 실제 고객 시험·내부 단가·신사업 순이익은 증거가 확보될 때만 null을 바꾼다. 현재 원장은 연구 제안이며 상시 감시·고객 거래를 실행하지 않는다.

`data/kyongnam_baseline_2026q3.json`은 선정 IR 표의 기준선이다. 기말·평잔·분기·누적과 단위, 은행·그룹을 구분한다. 현재 고객별 실험 결과와 혼합하지 않는다. 이 두 보조 원장은 기본 validate가 모든 의미를 검사하지 않으므로 출처·주장 ID, 수치 산식, 문서 링크, 가설·제안 상태를 별도로 확인해 runs/에 남긴다.

## 10. 경남은행 수출기업의 업무를 이어간다

STR-KN-01의 상세 기록은 `reports/16_kyongnam_export_treasury_business_plan.md`, `reports/17_kyongnam_multiasset_cash_case.md`, `data/kyongnam_export_business_plan.json`이다. 이전 판단을 읽은 뒤 실제로 바뀐 계약·상품 조건·고객 업무·허가만 확인한다. 수집 담당은 기존 은행 기능·경쟁·원문 변경을, 메커니즘 담당은 고객의 돈·권리·기한을, 검증 담당은 현재 허용범위·기여식·반증과 산술을 살피고 총괄이 병합한다.

조회·소유·통제·처분·환매·은행현금·담보·채무이행은 별도 상태다. 고객의 계좌 밖 자산은 동의·권한·실제 현금화 경로와 함께 확인한다. 토큰 표시와 원채권, 담보 매각과 차입, 인출한 대출과 잔여한도, 예금 FTP 손실과 대체조달비를 중복 합산하지 않는다. 기존+AI를 온체인 추가 투자의 비교 기준선으로 유지한다.

설명용 현금 사례는 다음 명령으로 재현한다. 작은 사례의 시점 순서만 지원하며 실제 은행 달력·수수료·신용 승인·거래 실행을 구현하지 않았다. 다른 시점 구조를 사용하려면 가정을 먼저 다시 설계한다.

```sh
python scripts/export_cash_case.py
python -m unittest discover -s tests -v
```

지표 값·예산·실제 고객 시험·ROI는 증거가 생길 때만 null/false를 바꾼다. 보조 원장의 출처·주장 참조와 계산 결과는 별도로 대사하고 `runs/2026-11-03-kyongnam-export.json` 다음에 새 실행 기록을 만든다.

## 11. 교보 미래전략의 사업 결정을 이어간다

`reports/18`~`21`은 README의 정확한 링크로 연다. `data/kyobo_strategy_business_plan.json`의 다섯 업무와 `data/kyobo_ip_deal_checklist.json`의 한 거래를 먼저 읽고 STR-KY-01~05의 바뀐 판단만 갱신한다. [분업 지침](agents/kyobo_strategy_workflow.md)은 역할별 입력·출력·독립 검토 순서를 정한다.

자본 담당은 RCPS 납입·회계/감독 인정·신청/지정·개별 인가를, 권리 담당은 계약·채무자·양도·상계·계좌·회수를, 레일 담당은 고객/관할·체인·전환/상환·사용가능액·출금을 확인한다. AI 담당은 조회·권유·주문·출금·담보 권한과 외부 채널의 보수·고객 이전권을 따로 본다. 실제 읽기 없이 과거 source의 checked_at을 새 날짜로 바꾸지 않는다.

POD 공개 안내의 지급일 차이와 IBKR 요율·지원 토큰·출금보류·관할별 planned 차이는 개별 계약 확인 전 미해결로 둔다. 같은 법령의 다른 조문 카드를 독립 증거로 중복 세지 않는다. 계열 신용 제한·고객자산 분리·원권리·세금·수금 부족·복구를 통과한 뒤 기존+AI 대비 온체인 추가 편익을 평가한다.

새 자료가 생기면 ingest로 출처·주장과 이전 판단을 보존하고, 관련 사업 ID·보고서·체크리스트를 함께 갱신한다. 보조 원장의 참조·null·조건부 상태는 별도 검사한다. 실제 고객 시험·예산·수익·승인은 증거가 생길 때만 바꾼다. 정기 감시·계좌 연결·거래 실행을 자동으로 시작하지 않는다.

## 국가 수요에서 그룹 사업까지 이어가기

[그룹·국가 작업 지침](agents/group_country_opportunity_workflow.md)에 따라 기존 국가 관계→실제 고객 문제→그룹/외부 기능→권리·현금·손익→경쟁·검증을 갱신한다. [기회 원장](data/group_country_opportunities.json)은 BNK·교보·한화의 후보 10건이며 확정 사업·예산 목록이 아니다. [한화 실행 기록](runs/2026-11-03-hanwha-group-strategy.json)에 이번 실제 분업·읽기 범위·독립 검토·한계를 보존한다.

## 교수 원문과 글로벌 비교 갱신

[포지션 비교 절차](agents/position_comparison_workflow.md)를 따른다. 원문 계보 → 현재 상품 조건 → 경제 메커니즘 → 그룹의 고객 업무 → 독립 검토를 연결하고, 당시 설명과 현재 정정은 별도로 남긴다. [이번 실행](runs/2026-11-04-ondo-position-integration.json)의 중복 출처 통합·읽기 범위·검증을 참고한다.

## AI 고객 사례와 수익 귀속 갱신

[통합 사례](reports/31_agent_finance_customer_money_2027.md)의 공통 가정을 확인하고 [사례 원장](data/agent_finance_2027_cases.json)에 새 관측을 연결한다. 기초 원금 예시와 실제 요율·가격·이익을 섞지 않는다. 고객 접점·자산·수입이 다른 공급자로 이동하는지, 경쟁자의 재가격 뒤에도 기여가 남는지 갱신한다. 이는 거래 자동 실행이나 정기 모니터링 설정이 아니다.

## 실제 사업 기반과 우선 대응 갱신

[재무 관측](data/institution_business_baselines.json)은 법인·기간·단위·정의·예상 여부·출처 위치를 유지한다. [대응 원장](data/business_model_transition_priorities.json)은 근거→인과→기존 수익의 위기/새 기회→경쟁 대응→우선 업무와 반증 관측을 연결한다. [반복 절차](agents/business_model_reasoning_workflow.md)를 따른다. 기존 가상 흐름은 보조로 보존하며 실적이나 전망치로 승격하지 않는다.

## 도메인 기반 의견의 인계와 검토

[역할 명세](agents/roles.json)의 초기/후기 교수형 호출과 [의견 절차](agents/economic_opinion_workflow.md)를 적용한다. [도메인 지도](agents/economic_domain_lenses.md)에서 필요한 원리를 고르고 [카드](agents/templates/economic_opinion.md)의 필요한 항목만 남긴다. [세 그룹 검토 문항](agents/evaluations/domain_reasoning_cases.json)은 조건을 바꿨을 때 주장·행동이 정당하게 달라지는지 의미로 검토한다. 기존 build/validate/tests는 참조·구조·계산을 확인하며 미래 예측 성능을 증명하지 않는다.


## 2026-11-06 실제 적용의 다음 시작점

[통합 판단45](reports/45_2027_decisions_and_changes.md) → [구조화 갱신](data/outlook_2027_reassessment.json) → [실행 기록](runs/2026-11-06-outlook-reassessment.json)에서 이어간다. 초기 교수형 6가설을 고정한 뒤 표적 원문 확인·기업별 적용·후기 갱신·독립검토를 수행했다. 새 자료가 영향을 주는 가설과 행동만 갱신하고 과거 STR 순위와 관측 기간을 보존한다. 다음 조사에서는 시장규모 추정부터 늘리기보다 경쟁 견적·반복 외부 계약·위험 잔존·이전 비거래 사유를 우선한다. 이번 실행은 호스트의 다중 에이전트 호출이며 상시 서버·자동 일정·고객 거래 실행을 설정하지 않았다.
