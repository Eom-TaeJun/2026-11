# 변경 자료 18개와 최근 원문의 검토 범위

2026-11-07 KST. **18개 현재판을 확인했고, 그 안내가 가리킨 관련 자료 6개를 추가로 읽었다.** 18개는 독립된 보고서 18편을 뜻하지 않는다. 안내·전략 본문·구조화 데이터·파생 텍스트·검증 기록이 섞여 있다. 비공개 원문과 경로 색인은 로컬에 보존했다. 아래는 익명 식별자와 실제 읽은 범위다.

## 18개 현재판 확인

| ID | 자료 종류 | 열람 범위 | 검증 |
|---|---|---|---|
| INPUT-01 | 전체 읽기 안내 | 전체 본문·읽는 순서·최신 연결 읽음 | 현재 고정본 해시 일치 |
| INPUT-02 | BNK 전략 자료 | 1~156행 전체. 첫 출력에서 잘린137~156행 별도 재열람 | 현재 고정본 해시 일치 |
| INPUT-03 | 비교군 JB 전략 자료 | 2~106행 본문·표·근거 링크 읽음. 제목은 파일명/목차 확인 | 현재 고정본 해시 일치 |
| INPUT-04 | 교보 전략 자료 | 1~100행 전체 | 현재 고정본 해시 일치 |
| INPUT-05 | 한화 전략 자료 | 1~135행 전체 | 현재 고정본 해시 일치 |
| INPUT-06 | 금융그룹 비교 자료 | 1~151행 전체 | 현재 고정본 해시 일치 |
| INPUT-07 | 본사 핵심 판단 자료 | 1~38행 전체 | 현재 고정본 해시 일치 |
| INPUT-08 | 전체 흐름 자료 | 1~59행 전체 | 현재 고정본 해시 일치 |
| INPUT-09 | 인계 자료 | 전체 본문과 최신BNK심화·교정·실제범위 읽음 | 현재 고정본 해시 일치 |
| INPUT-10 | 추가 자료의 통합 판단 | 전체 본문·통합표·Meta/Dot단계구분·추가자료 근거 읽음 | 현재 고정본 해시 일치 |
| INPUT-11 | 추가 자료 시작 안내 | 전체. 다음GPT_읽기안내와 동일SHA 확인 | 현재 고정본 해시 일치 |
| INPUT-12 | ETF 자금흐름 구조화 자료 | 스키마·CF01~10 ID/제목·가정예시3개·모니터링6개·actual=null·저장/범위 필드 선택읽기. 10개body가 읽은MD/TXT에전부문자열일치함을검사 | 현재 고정본 해시 일치 |
| INPUT-13 | ETF 자금흐름 해설 자료 | 1~211행 전체,CF01~10 및40개출처목록 | 현재 고정본 해시 일치 |
| INPUT-14 | ETF 자금흐름 텍스트 자료 | 1~34행·전체CF제목·171~471출처제목/배열구조 선택읽기. CF10개body는MD/JSON과문자열일치검사; 출처세부는별도source register선택필드로읽음 | 현재 고정본 해시 일치 |
| INPUT-15 | 저장 체크섬 기록 | 16개해시항목전체읽고현재스냅샷과선별대조 | 현재 고정본 해시 일치 |
| INPUT-16 | 다음 읽기 안내 | 전체. AI_START와동일SHA/내용 | 현재 고정본 해시 일치 |
| INPUT-17 | 이전 저장 검증 기록 | 전체메타/remote verification항목/local hashes/status/latest_verification읽음 | 현재 고정본 해시 일치 |
| INPUT-18 | 추가 읽기 순서 | 전체 | 현재 고정본 해시 일치 |

18개 중 바이트가 같은 안내 1쌍이 있어 고유 내용은 17개이며, PDF/JSON/텍스트 표현이 비슷해도 독립 수요 증거로 더하지 않았다. 직전 관측 이후 다시 달라진 파일은 5개다. 이전 체크섬과 현재 안내 3개가 일치하지 않았으나 원자료를 임의로 복원하지 않았다.

**이전 본문은 이번에 확보하지 못했다.** 따라서 정확한 문장별 변경이나 작성 시점은 주장하지 않는다. 이번 “변경”은 관측된 파일 해시 변화와, 현재판을 기존 공개 보고서35~47에 대조한 의미 변화다. 과거 원본 복구 후보는 로컬에 남겨 두었다. [해시·범위 기록](../data/market_update_20261107_input_audit.json)

## 무엇이 신규이고 무엇이 구체화인가

| 내용 | 판정 | 활용 |
|---|---|---|
| 예금 유출·무료 경쟁·상계/선자금·권리/현금 구분 | 기존41~45에도 존재 | 새 발견으로 세지 않고 실제 고객·계약·경쟁 사례를 보강 |
| OUSG 복수 제조사·날짜 있는 구성과 보수면제 | 기존 역할 구분의 날짜별 재확인 | 배타적 제조/유통 가정과 수익 계산을 경계 |
| OIP→USDon→USDC→은행현금 | 기존 권리/현금 구분을 상품 경로로 구체화 | 지급기일·환매·승인·유동성별 책임 |
| 2027 외담대 개편·우리은행 발주 금융 | 기존 자료 후보의 공식 재확인 및 첨부 독해 | BNK 운영 출발점과 신규 수요 탐색 범위 분리 |
| 보험료 기일 관리·해외 기관 USD 의무·소기업 흐름 | 현재판의 구체 고객 업무를 기존43/44/47과 대조 | 기존 개선·새 거래·타행 이전을 분리 |
| JB 비교군 | 참고 범위 확장 | 이번 핵심 결과는 세 그룹이며 JB 독립 사업안으로 확대하지 않음 |

새 교수 강의 파일 후보도 발견했지만 이번에 원문을 읽은 것으로 기록하지 않았다. 기존 [cschung7 원문 지도](46_cschung7_reasoning_and_market_discovery.md)와 v2.2 역할을 적용했고, 새 후보를 교수의 확인된 견해 변경으로 쓰지 않았다. USDon 개별 최신 계약/Final Terms 등 추가 확인이 필요한 항목도 본문 확인 범위를 넘어 사실로 승격하지 않았다.

## 최근 기관 자료를 어디에 썼는가

이번 공개 원문 읽기 사건은 **31건**이다. 원장에는 새 URL 19개와 기존 URL 재확인 12개를 반영한다. 이는 보고서 전문 정독 수가 아니다. 본문·첨부가 같은 사건인 FSC/우리은행, 같은 상장 사건인 ADX/ETC는 독립 수요 증거 2건으로 세지 않는다. 기존 회사 재무·관계 근거는 원 확인일과 보고기간을 유지했다.

| 출처 | 발표일 / 구분 | 이번 읽기 | 활용 |
|---|---|---|
| [NU-B-003: BNK금융그룹, 부산시·기보와 손잡고 기후테크 기업 금융지원 확대](https://www.bnkfg.com/02/03.jsp?dataPageNo=1&dataSeqNo=6995&dataWhere=) | 2026-11-06 | 공식 HTML 제목·등록일 및 28~40행의 협약·과거 지원·기관별 역할. | 지역 산업 전환의 정보·정책금융·장기 자금 수요를 실제 BNK 신호와 연결 / 기존 주기 확장의 구체 대상 탐색 |
| [NU-H-004: KSSK Perkuat Koordinasi Dan Sinergi Kebijakan Untuk Menjaga Fundamental Ekonomi Dan Ketahanan Sistem Keuangan Nasional](https://www.bi.go.id/id/publikasi/ruang-media/news-release/Pages/sp_2824026.aspx) | 2026-11-03 | 공식 HTML 170–205행(발표·평가), 216–255행(통화/거시건전성·지급·LCT·은행/보험). 선택 본문 대조. | H3 소액 지급 유료화 반대증거 / 신용 연결·현지통화 거래의 기존 대안 / 금리·FX·보험료 부담 스트레스 |
| [NU-M-005: Broadridge to Bring OnChain Governance and Digital Transfer Agency to NYSE Tokenized Securities Platform](https://www.broadridge.com/press-release/2026/broadridge-to-bring-onchain-governance-and-digital-transfer-agency) | 2026-11-02 | HTML 533–555행: 발표일·규제승인 후 플랫폼 개시 조건·주주권/명의개서/투표·기존 인터페이스 연결. | 교보의 범용 발행 플랫폼 투자 대안과 실질 권리 서비스 경쟁 |
| [NU-H-003: ADX Introduces the Region’s First Exposure to Korean Funds](https://apigateway.adx.ae/adx/cdn/1.0/content/download/5904510) | 2026-11-02 | 2쪽 PDF 텍스트 전체; 특히 p1 상장·현지 거래시간·지수, p2 시장 전체 거래대금. 레이아웃/원시 거래자료 미검증. | H2 실제 상장과 MOU 구분 / 현지 접근·장소 이동·신규 투자 분리 |
| [NU-B-004: Standard Chartered launches Tokenised Deposits in Hong Kong](https://www.sc.com/en/press-release/standard-chartered-launches-tokenised-deposits-in-hong-kong/) | 2026-11-02 | 공식 발표 HTML 8~28행: 홍콩 첫 출시·기업 자금·참여 고객·MMF·파트너 및 확장 계획. | 경쟁 은행도 예금·펀드·기업 유동성을 통합한다는 실제 대응 신호 / BNK의 범용 지갑 경쟁보다 원화 의무·지역 신용 접점 선택 |
| [NU-B-002: 우리은행 발표: 신용보증기금 보증을 결합한 발주단계 공급망금융 사례](https://www.fsc.go.kr/comm/getFile?fileNo=8&fileTy=ATTACH&srvcId=BBSTY1&upperNo=88052) | 2026-11-02 | 10쪽 PDF 텍스트 추출. 표지·목차 확인, 물리 3~9쪽(자료 표기 1/7~7/7)의 공급망·플랫폼·보증·자금 흐름을 읽고 5~8쪽 재확인. 이미지 시각 검수는 하지 않음. | BNK 확정채권 가설과 다른 발주 단계의 실제 경쟁 설계 / 비용 절감만이 아니라 위험분담·정보 접근이 새 금융 계약의 조건임을 확인 |
| [NU-B-001: 생산적 금융의 온기를 지방과 중소기업까지 이어갑니다. - 제6차 생산적 금융 대전환 회의](https://www.fsc.go.kr/no010101/88052) | 2026-11-02 | 공식 HTML 등록일·본문 296~311, 322~385, 389~499, 503~514행. 지역 보증대출·외상매출채권/상생결제 개편 및 은행 사례. 첨부 전체 읽기 아님. | 단기 조달 수요·판매기업 위험부담·구매기업 평가의 변화 / Hana/NH의 대기자금 금리 및 KB의 대출금리 인센티브라는 경쟁 신호 / 기존 정책 입력 재확인 |
| [HWX-A-004: Exchange Traded Concepts Takes Client ETFs to the Abu Dhabi Securities Exchange](https://www.exchangetradedconcepts.com/posts/exchange-traded-concepts-takes-client-etfs-to-the-abu-dhabi-securities-exchange) | 2026-11-02 | 2026-11-07 재열람: 공식 HTML 0–18·41–54행; 날짜, Hanwha sponsor/ETC adviser, Oceane/Waystone, Foreside distributor, 위험. | H2 제조/자문/유통/운영 수익 귀속 |
| [NU-M-007: Protecting people and businesses in an agentic economy — joint statement landing](https://www.drcf.org.uk/publications/joint-statements/joint-statement-on-protecting-people-and-businesses-in-an-agentic-economy) | 2026-10-30 | 공식 HTML 32–39행 발표일·4개 규제기관 협업·기존 규칙 적용 설명. 연결 statement 전문 미독. | AI 위임이 기존 금융 책임을 자동 제거한다는 가정 배제 |
| [ST-HW-002: Hanwha Investment & Securities and Chainlink Form Strategic Partnership to Tokenize, Connect, and Collateralize Real-World Assets Worldwide](https://chain.link/press-releases/hanwha-investment-securities-and-chainlink-form-strategic-partnership-to-tokenize-connect-and-collateralize-real-world-assets-worldwide) | 2026-10-29 | 2026-11-07 재열람: HTML 10–33행; 날짜·채택·구축·논의·작업반. 42–44행 최종갱신 2026-11-03. | H2 담보·거래후 업무의 실행 신호와 남은 계약 |
| [NU-B-005: Eurosystem report on the public consultation on the Appia Roadmap](https://www.ecb.europa.eu/paym/pdf/consultations/Eurosystem_report_on_the_public_consultation_on_the_Appia_Roadmap.pdf) | 2026-10-28 | 21쪽 PDF의 1~5, 8~11, 14~15, 19~20쪽 중심 선택 읽기. 127건 의견·공동 인프라/경쟁 기능·복수 망의 분절·향후 작업. 10/28 공식 발표에서 발간일 대조. | BNK가 공통 인프라를 이용하되 신용·현장 확인·관리 책임에서 차별화할 이유 / 내부 통합과 외부 분업의 조정비·경쟁 변화 |
| [NU-K-001: BlackRock, SBI Holdings and Startale MOU: tokenized MMFs and JPYSC](https://www.startale.com/en/blog/blackrock-startale-sbi) | 2026-10-27 | Startale 공식 발표 48~70행. SBI URL은 검색에 노출된 공식 본문을 확인했으나 직접 열기에서는 iframe만 표시되어 직접 본문 열람으로 세지 않음. | 교보 기존 방향과 최근 경쟁·무료 대안·현행 권한의 범위 검증 |
| [NU-M-006: Lloyds uses agentic AI platform to strengthen customer fraud support](https://www.lloydsbankinggroup.com/media/press-releases/2026/lloyds/lloyds-strengthens-fraud-support-agentic-ai.html) | 2026-10-26 | HTML 596–632행 본문: 실제 사례 자기보고·직원 판단 책임·연속 수정·원가/전체 AI 예상가치의 범위. | 기존 대형은행도 AI로 비용을 낮추고 책임 있는 고객 접점을 강화한다는 경쟁 근거 |
| [NU-H-001: Speech: International insurance regulation in a fast-changing world](https://www.iais.org/2026/10/speech-international-insurance-regulation-in-a-fast-changing-world/) | 2026-10-22 | 본문 Structural shifts in the life insurance sector, Technology, Protection gaps; 날짜 및 Gerry Cross 연설자 확인. 웹 초기 본문 후 직접 공식 HTML에서 해당 세 절을 재확인. | H1 접근비용과 위험인수 분리 / H2 보험 ALM와 운용상품 유통 분리 / H3 미가입을 유료수요로 바꾸지 않는 조건 |
| [NU-M-001: Sound Practices for Responsible Adoption of AI — final report, official summary](https://www.fsb.org/2026/10/sound-practices-for-responsible-adoption-of-artificial-intelligence-ai-final-report/) | 2026-10-15 | 공식 HTML 전체 요약·12개 sound practices. PDF 링크 확인했으나 PDF fetch timeout; 보고서 전문 미독. | 위임·실행·복구 책임을 운영원가와 상품 조건에 포함 |
| [NU-M-003: The Next US Treasury Market Evolution](https://prodcs.bny.com/corporate/global/en/institute/next-us-treasury-market-evolution.html) | 2026-10-13 | HTML 본문 114–187행: 운영시간 불일치, 법인·지역·현금 위치, 기존 시장 신용·상계, 미래 운영계획. | 동일 고객 업무의 기존 레일 개선도 경쟁 기준선에 포함 / 해외 법인 USD 지급의무와 운용·환매의 시간 불일치 분석 |
| [NU-M-002: The Digital Frontier: Collateral in a Tokenized World](https://www.citigroup.com/rcs/citigpa/storage/public/citi_services_digital_frontier_collateral_tokenized_world.pdf) | 2026-10-13 | PDF 첫 3쪽 중 본문 0–152행 선택: 실시간 재고·현금/담보 결합·가상 사례·토큰화와 기초 유동성 구분. 후반 재접근 timeout. 공식 landing에서 10/13 날짜 확인. | 유동성 창출과 이동·활용 개선을 분리 / 은행·수탁사가 기존 고객과 자본을 바탕으로 재통합하는 대안 |
| [NOV-M07: GFSR October 2026, Chapter 3: Scaling Tokenization: New Efficiencies, New Vulnerabilities](https://www.imf.org/-/media/files/publications/gfsr/2026/october/english/ch3.pdf) | 2026-10-13 | 2026-11-07 선택 재열람: PDF p1–3/인쇄43–45 요약·서론; p22/인쇄64 Box3.2 상계·사전조달·배치; p13·19의 위험·결제자산 연결 부분. 표/회귀/전체 장 미독. | 기존 판단의 반대 경로 재검증; 빠른 결제와 자본 절감을 동일시하지 않음 |
| [SRC-BOK-HANGANG: 프로젝트 한강의 기관용 디지털화폐, 일반인용 CBDC와 어떻게 다를까](https://www.bok.or.kr/portal/bbs/B0000347/view.do?menuNo=201106&nttId=11065408) | 2026-10-08 | 공식 HTML 제목·등록일 850~858행 및 873, 883~925행. 진행 상태·예금토큰과 기관용 화폐·기존 지급망 설명. | 상시 이체 자체를 온체인의 신규 편익으로 과장하지 않음 / 은행 부채인 예금토큰·외부 펀드·스테이블코인 권리 차이 |
| [NU-K-002: 메리츠증권 종합금융투자사업자 지정 및 단기금융업 인가](https://www.fsc.go.kr/no010101/87782) | 2026-09-23 | 본문 296~343행과 종투사 지정·단기금융업 표의 검색 위치 확인. | 교보 기존 방향과 최근 경쟁·무료 대안·현행 권한의 범위 검증 |
| [NU-H-002: Scaling AI in finance: systemic risks, resilience and European sovereignty](https://www.eiopa.europa.eu/publications/scaling-ai-finance-systemic-risks-resilience-and-european-sovereignty_en) | 2026-09-16 | 공식 HTML 40–68행: 게시일·2025 설문 분모·AI 위험·의존성 지도·복구·대체 공급자 | H1 동일 AI 경쟁과 운영책임 / H2 거래후 예외·복구의 비용 |
| [NOV-M08: [제2026-22호] 달러 스테이블코인과 외환시장 간 연계성: 글로벌 거래소의 역할을 중심으로](https://www.bok.or.kr/portal/bbs/P0002353/view.do?depth=200433&menuNo=200433&nttId=11064416&programType=newsData&relate=Y) | 2026-09-03 | 공식 HTML 제목·등록일 859~885행과 요약 882~885행. 첨부 실증 전문·표본·인과식별 검토 없음. | 달러 토큰 액면과 원하는 시각의 원화 현금을 구분 / 환전·환매·시장 접근·프리미엄을 고객 현금 관리에 넣음 |
| [KYO-GEO-004: Digital Capital Group–Kyobo Securities strategic technology partnership](https://www.dcg.earth/newsroom/digital-capital-group-and-kyobo-securities-sign-strategic-technology-partnership-to-advance-tokenized-securities-in-asia-pacific) | 2026-04-08 | 공식 웹 본문 19~36행, 법인 안내 83행 참고. 기관용 RWA 발굴·토큰화·유통 MOU와 역할. | 교보 기존 방향과 최근 경쟁·무료 대안·현행 권한의 범위 검증 |
| [OBX-P-007: Ondo Intelligent Portfolios Market Hours and Trading Availability](https://docs.ondo.finance/intelligent-portfolios/market-hours) | 발행일 미확인; 11/7 관측 | 2026-11-07 HTML 137–184행 본문 | 24/7 체인 가동과 고객 지급기한 충족을 구분 |
| [OBX-P-006: Ondo Intelligent Portfolios Investing and Redeeming](https://docs.ondo.finance/intelligent-portfolios/investing-redeeming) | 발행일 미확인; 11/7 관측 | 2026-11-07 HTML 134–148행 본문 | 포트폴리오에서 현금 의무까지 전체 경로 비교 |
| [OBX-P-005: Ondo Intelligent Portfolios Fees and Taxes](https://docs.ondo.finance/intelligent-portfolios/fees-taxes) | 발행일 미확인; 11/7 관측 | 2026-11-07 HTML 137–156행 본문 | 수익 제조·모델·구현·접근 비용과 투자자 순수익을 분리 |
| [OBX-E-020: Ondo Intelligent Portfolios Model Providers](https://docs.ondo.finance/intelligent-portfolios/model-providers) | 발행일 미확인; 11/7 관측 | 2026-11-07 HTML 137–156행 본문 | BlackRock 브랜드·모델 제공과 토큰 발행/보유자 책임 구분 |
| [OBX-E-014: Ondo Stocks Investing and Redeeming](https://docs.ondo.finance/ondo-stocks/investing-and-redeeming) | 발행일 미확인; 11/7 관측 | 2026-11-07 HTML 142–209행 전체 Q&A | 자산 환매·스테이블코인 교환·은행 현금화를 별도 단계로 관리 |
| [OBX-E-004: OUSG | Tokenized Treasuries for Institutions](https://ondo.finance/ousg) | 발행일 미확인; 11/7 관측 | 2026-11-07 상품 조건·11/5 16:00 EST 표·FAQ·법적 고지·각주 | 복수 제조사 선택·포장·유동성 관리의 분업과 보수 경쟁 |
| [NU-M-004: Agentic Finance: Building the foundations for trusted, bounded autonomy](https://www.uobgroup.com/assets/web-resources/research/pdf/da-261014.pdf) | 10/14 정보기준; 발행일 미확인 | PDF p1–7 서문·방법·가상 treasury 사례; p22–27 경계위험·도입 전망·결론. 도표 수치를 실측으로 채택하지 않음. | 자율 실행과 신용위험을 지는 자본 배분을 분리 / 정보 공급자 이해관계와 표본 제한 점검 |
| [NU-K-003: MY교보 이용안내](https://www.kyobo.com/dgt/web/customer/utilization-guidance) | 발행일 미확인; 11/7 관측 | 보험 계약 조회·보험료 납입·출금·계약 변경 안내 31~147행. | 교보 기존 방향과 최근 경쟁·무료 대안·현행 권한의 범위 검증 |

10월말 이후에는 공급망 정책·실제 은행 상품/협업·ADX 상장·AI 운영·일본 MOU 등 구체 신호를 우선했다. 9월 및 10월 중순 보고서는 원리와 경쟁 구조를 보완한다. 발행일 없는 제품 문서는 최신 조건의 관측으로 분리하고 새 11월 보고서라고 세지 않았다. 4월 DCG MOU는 과거 관계의 재확인이다.

UOB는 언론 10/28과 원문 정보기준 10/14가 다르다. IMF PDF는 검색 메타 제목이 April로 나타나지만 본문은 October2026 Chapter3임을 확인했다. FSB·DRCF는 공식 요약만, Citi는 선택 PDF 부분과 날짜 페이지를 읽었다. State Street의 등록형 전문·기존 후보만 확인한 문서·접근 실패 OJK 후보는 전문 독해로 추가하지 않았다.

## 재사용과 검증의 한계

자료를 찾은 경로, 최초/후기 입장, 원문 읽은 범위, 주장 유형, 경쟁 대안, 판단을 바꾸는 관측을 각각 남겼다. [초기 의견](../runs/2026-11-07-market-update-opening.json) → [후기·행동](../data/market_update_20261107_decisions.json) → [연결 검사](../data/research_lineage_20261107_market_update.json).

구조 검사는 파일·참조·읽기 상태의 일관성을 확인하며 원문의 의미나 미래 수익성을 자동 인증하지 않는다. 독립 검토에서 기존 판단의 구체화를 신규 수정으로 센 표현, 신규 설정과 유통 보수의 혼동 가능성, 한화 기관업무의 기존 계보를 교정했다. 실제 고객 조사·계약·예측 성능 비교는 아직 수행하지 않았다.

읽기 순서: [거시 구조](49_2027_market_structure_update.md) → [통합 결정과 고객 사례](53_market_opportunities_and_decisions.md) → [BNK](50_bnk_market_update.md) / [교보](51_kyobo_market_update.md) / [한화](52_hanwha_market_update.md).

## 조사 중 추가 변경의 마지막 확인

최종 보존 검사에서 최초18개 중 안내·인계·흐름·체크섬·저장검증8개가 다시 달라진 것을 발견했다. 최초 고정본을 덮어쓰지 않고 별도 고정본으로 실제 차이를 확인했다. 핵심 회사 전략/ETF 본문과 처음 추가한6개 사업 자료는 그대로였다. 새 안내가 연결한 금융환경 해설2개와 현재 종합판단1개를 추가로 읽었다. 따라서 원자료18개, 초기 연결6개, 마지막 연결3개를 구분하며 후속3개를 새로운 공식 출처로 세지 않는다.

후속 입력은 중심 판단을 뒤집는 새 실증보다 장기 성장 경로와 읽기 순서를 보완했다. 이를 시장구조 보고서49의8절과 통합판단53의7절에 반영했다. 첫 실험과 장기 성장의 범위를 분리하고, 금융기관/외부 고객AI/글로벌 제휴의 세 공존 구조를 추가했다. 과거 이전본문 미확보라는 한계는 그대로이며, 이번 조사 시작 이후8개 변화는 보존한 두 고정본 사이의 실제 비교다. 상세 경로와 변경본은 로컬에만 남겼다.
