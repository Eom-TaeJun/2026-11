# 기록 형식

Python 검증기는 필수 필드, ID·URL 중복, 공개범위, 원문 읽기 상태, 주장·주제 참조와 가설의 반대 설명·다음 관측을 검사한다. 문장의 사실 여부·계약 해석·개인정보를 자동으로 판정하지는 않으므로 독립 원문 검토가 필요하다.

## sources

`id`, `title`, `publisher`, `url`, `published_at`(미확인 null), `checked_at`(YYYY-MM-DD), `visibility`(public), `read_status`, `read_scope`, `summary`, `used_for`, `limitations`, `topic_ids`.

read_status는 full_text / selected_sections / official_summary / metadata_only / unread다. full_text도 해당 HTML·FAQ의 본문을 의미할 수 있으므로 source_type과 read_scope에서 보고서 PDF 전체와 구분한다. 사건일·효력일·버전·정정 관계는 추가 필드로 남긴다. URL만 같고 본문 버전이 바뀌면 같은 ID를 갱신하며 history에 이전 값을 보존한다.

## claims

`id`, `kind`, `status`, `text`, `source_ids`, `topic_ids`, `limitations`. kind는 fact / institution_statement / interpretation / hypothesis / unknown이다. status는 active / superseded / withdrawn / needs_review다. hypothesis에는 alternative와 next_observation이 필요하다. 주장 연결은 원문이 해당 해석의 출발점이라는 뜻이며 인과효과가 검증됐다는 뜻은 아니다.

## topics

`id`, `name`, `question`. 분야를 추가할 때 목록을 늘리는 목적보다 어떤 판단 질문을 구분하는지 적는다.

## 변경 배치

```json
{
  "change_reason": "공식 정정 발표를 확인하여 시행 상태를 수정",
  "sources": [],
  "claims": [],
  "topics": []
}
```

빈 배열은 삭제를 뜻하지 않는다. 기존 ID가 있는 레코드는 교체되고 새 ID는 추가된다. 동일 배치 안의 중복 ID는 거부한다. 변경 전후 전체 상태의 해시와 기록을 남긴다.
