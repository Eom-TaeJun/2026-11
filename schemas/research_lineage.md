# 연구 계보 명세 v1.0

이 명세는 공개 원문 원장 → 현재 주장 → 초기·후기 가설 → 우선 행동의 연결을 검사한다. `scripts/lineage.py`가 읽기 전용으로 검사하며 원장, 보고서, 원래 run 기록을 고치지 않는다. **구조 검사 통과는 원문의 실제 이해, 주장의 충분한 근거, 경제적 인과나 미래 예측의 정답을 뜻하지 않는다.** 출처의 유효기간과 실제 내용 재확인은 별도 연구 절차다.

현재 사례는 `data/research_lineage_20261106.json`이다. 2026-11-07에 기존 공개 기록 사이의 연결을 명시했으며, 이전 작성자가 후속 주장 모두를 직접 인용했다거나 기업이 이 행동을 확정했다는 뜻이 아니다. 기존 본문·STR 순위·판단을 변경하지 않는다.

## 실행과 재사용

```console
python scripts/lineage.py --root . --manifest data/research_lineage_20261106.json
python -m unittest discover -s tests -p test_lineage.py -v
```

CLI는 통과 시 JSON 요약과 종료 코드 0, 실패 시 오류 목록과 종료 코드 1을 반환한다. 표준 라이브러리만 사용한다.

```python
import lineage

problems = lineage.errors(root, manifest_path, data=proposed_data)
summary = lineage.validate(root, manifest_path, data_override=proposed_data)
inputs = lineage.input_paths(root, manifest_path)
```

- `errors(root, manifest, data=None)`는 문자열 오류 목록을 반환한다.
- `validate(root, manifest, data_override=None)`는 요약 dict를 반환하거나 `ValueError`를 발생시킨다.
- `input_paths(root, manifest)`는 명세와 참조된 파일의 절대 `Path` 목록을 반환한다. 실행 준비 단계에서 입력 파일 해시를 고정하는 용도다. 명세 자체를 dict로 전달하면 그 dict의 파일 경로는 목록에 포함할 수 없다.
- `manifest`는 저장소 내부 파일 경로 또는 dict다. `data`/`data_override`는 `sources`, `claims` 배열을 담는 dict다. 제안된 원장으로 참조 검사를 수행하되 초기·후기 가설, 보고서, 원래 읽기 로그는 실제 파일에서 읽는다. 어떤 파일도 쓰지 않는다.
- 이 범용 API의 제안 데이터는 명세가 지정한 원장 경로를 대신한다. `research.ingest`와 결합하는 실행기는 실제 쓰기 대상인 `data/sources.json`, `data/claims.json`과 명세 원장 경로가 같음을 쓰기 전에 확인해야 한다. 다른 스냅샷 경로에 대한 검사 결과를 고정 core 원장에 대한 쓰기 승인으로 사용할 수 없다.
- `tests/test_lineage.py`의 `make_fixture(root)`는 임시 root에 최소 테스트 자료를 만들고 명세의 상대 경로를 반환한다. 실제 연구 자료를 준비하는 도구는 아니다.

다음 연구는 새 `run_id`와 새 명세를 만든다. 기존 run의 해시를 자동으로 새 내용에 맞추거나 오래된 결론을 덮어쓰지 않는다. 기존 기록을 정정해야 한다면 변경 근거·영향을 검토하고 이전 상태가 보존되는 별도 기록을 남긴다.

## 원본 참조 형식

JSON 참조는 `path`, `pointer`, `sha256`, 선택적 `expected_id`를 가진다. `path`는 공개 저장소 상대 POSIX 경로이며 상위 경로 이동·절대 경로·저장소 밖 심볼릭 링크를 허용하지 않는다. `pointer`는 JSON Pointer다. `sha256`은 해당 값의 정규 JSON 직렬화(UTF-8, 키 정렬, 구분자 `,`와 `:`)에 대한 SHA-256이다. 같은 ID가 잘못된 배열 위치로 이동하거나 참조 값이 바뀌면 검토를 요구한다.

Markdown 행동은 `format: markdown_section`, `path`, 정확한 ATX `heading`, `sha256`으로 참조한다. 제목은 파일에서 한 번만 일치해야 한다. 해당 제목부터 다음 동급·상위 제목 전까지의 줄을 LF로 연결하고 뒤 공백을 제거한 문자열에 같은 `digest` 함수를 적용한다. JSON에 우선 행동 배열이 없는 교보 보고서의 기존 세 업무를 보존하기 위한 형식이다. 해당 그룹 JSON에 기록된 `report` 경로와 일치해야 하며, 원래 JSON 의사결정 ID도 함께 참조한다. 본문 사본은 명세에 넣지 않는다.

참조 해시는 변경을 알아내는 장치이며 서명이나 외부 원문의 진위 증명은 아니다. 작성자가 원문과 해시·명세를 함께 잘못 바꾸는 경우의 의미 검토를 대신하지 못한다.

## 필수 필드와 검사

| 필드 | 내용과 검사 |
|---|---|
| `schema_version` | 문자열 `1.0`. 알 수 없는 버전은 실패한다. |
| `run_id` | 비어 있지 않은 현재 run 식별자. 현재 주장 원장의 `run`과 같아야 한다. |
| `registries` | `sources.path`, `claims.path`. 각각 ID가 고유한 객체 배열이다. 일반 원장 전체 검증은 `research.py`와 함께 실행한다. |
| `read_events` | 원본 사건 배열 JSON 참조와 `expected_count`. 배열 전체 해시·개수, 출처 ID, 유효한 읽기 상태, 완전히 같은 사건 중복을 검사한다. 같은 출처의 서로 다른 재열람은 중복으로 단정하지 않는다. |
| `read_status_corrections` | 아래에 설명한 제한적인 부가 교정 배열. 원본 event에 쓰지 않는다. |
| `context_only_read_source_ids` | 해당 run에서 읽었지만 새 주장에 직접 연결되지 않은 출처를 명시한다. 실제 차집합과 같아야 한다. 문맥 자료를 새 결론의 근거처럼 세지 않는다. |
| `scope` | `claims`, `hypotheses`, `actions`의 기대 ID 배열. 명세의 실제 기록들과 정확히 일치해야 한다. 주장 원장에서 해당 `run_id`가 부여된 모든 주장을 포함해야 하며 일부를 조용히 생략할 수 없다. |
| `claims` | `id`, 원장 `ref`, `kind`, `source_ids`. 원래 ID·유형·출처·run·활성 상태를 확인한다. 가설형 주장은 `alternative`, `next_observation`이 있어야 한다. |
| `hypotheses` | `id`, `opening_ref`, `closing_ref`, `closing_sources_ref`, `alternative_ref`, `next_observations_ref`, `claim_links`. 초기·후기 ID가 같아야 한다. v1.0 후기 원본의 필드 이름은 `source_ids`, `strongest_alternative`, `next_observations`이며 해당 필드를 정확히 가리켜야 한다. 다른 비어 있지 않은 문자열을 대안/관측으로 대신할 수 없다. |
| `hypotheses[].claim_links` | `claim_id`, `source_ids`, `shared_closing_source_ids`. 출처 목록은 주장 원장과 같아야 한다. 공유 인용은 해당 주장과 후기 가설의 원래 출처 목록 교집합과 정확히 같고 비어 있으면 안 된다. 공유 출처는 구조적 연결 조건이며 의미적 지지의 증명이 아니다. |
| `groups` | 그룹명 → 원래 그룹 JSON 참조. |
| `actions` | 명세 전용 `id`, `group`, 본문 대신 `ref`, 원래 `decision_refs`, `hypothesis_ids`, `claim_ids`. JSON 행동은 해당 그룹의 `priorities` 원소를 가리키고, 의사결정은 해당 그룹에 속해야 한다. 각 행동의 주장들은 연결된 가설을 통해 도달 가능해야 하며 나열된 각 가설과도 적어도 한 주장을 공유해야 한다. |

주장·가설·행동·관계의 중복 ID와 중복 행동 참조를 거부한다. 사용되지 않은 현재 주장, 행동과 연결되지 않은 가설, 범위에서 빠진 행동도 실패한다. 식별자만 존재하는 임의의 주장 연결은 원장 ID·유형·원본 해시·출처 집합·그룹 범위·관계 교집합 중 해당하는 검사로 제한한다. 이 조건들을 모두 만족하지만 경제적 의미가 틀린 연결은 사람/후기 검토자의 과제다.

## 기존 읽기 로그 5건의 부가 교정

원본 `runs/2026-11-06-outlook-reassessment-sources.json`의 33개 사건은 그대로 둔다. 처음 다섯 사건의 `read_status`가 null이지만, 각 사건의 `read_scope`와 해당 출처 원장의 기존 읽은 범위가 정확히 일치한다.

| 원본 배열 위치 | 출처 | 부가 상태 |
|---|---|---|
| 0 | FIN-003 | selected_sections |
| 1 | FIN-008 | selected_sections |
| 2 | NOV-M07 | selected_sections |
| 3 | ST-TD-005 | selected_sections |
| 4 | NOV-M01 | selected_sections |

각 교정은 `event_index`, `source_id`, `event_ref`, `original_read_status: null`, `corrected_read_status: selected_sections`, `source_ref`, `source_scope_ref`, `new_read_performed: false`, 기록일과 `reason`을 가진다. v1.0은 이 제한적인 null→선택 열람 교정만 지원한다. 원래 사건·출처·범위가 일치하지 않거나 동일 사건을 두 번 고치거나 전문 열람/새 열람으로 승격하면 실패한다.

NOV-M01의 출처 원장에는 이전 `full_text` 상태가 있으나, 이번 재열람 범위를 전문 열람으로 확대하지 않는다. **새 원문을 읽었거나 새로운 사실을 확인했다는 기록이 아니다.** 실제 독해 여부를 자동 증명할 수 없으며 기존 관측 메타데이터의 누락만 보완한다.

`fact`·`institution_statement`가 미독/메타데이터 전용 출처 또는 그러한 해당 run 읽기 상태에 의존하면 실패한다. 이 상태 검사는 원장 선언의 일관성 검사이며, 읽었다는 사람이 정직했는지 또는 원문이 주장을 지지하는지 검증하는 기능은 아니다. 이전 열람만 재사용하는 별도 연구는 그 범위를 명시적으로 검토한 새 명세로 기록한다.

## 현재 연결 범위와 검증 한계

12개 주장 `C-421`~`C-432`, 6개 `OPEN-*`, BNK·교보·한화 각 3개 우선 행동이 연결된다. 새 주장에 직접 연결되는 출처는 28개, 문맥용 읽기 출처는 5개다. `A-BNK-*`, `A-KYOBO-*`, `A-HANWHA-*`는 연결 명세의 식별자이며 원래 회사 사업 ID나 새로운 전략 순위를 뜻하지 않는다.

자동 검사는 공식 원문의 현행성·법률 해석·수익성·경쟁사 반응의 타당성, 반증 관측의 실질적인 판별력, 외부 출처의 내용 변경을 판단하지 않는다. 공개 원문 확인 → 주장의 근거 검토 → 대안과 가정의 검토 → 행동 판단이라는 연구 절차와 함께 사용한다.
