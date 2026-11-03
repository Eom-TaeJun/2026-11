# BlackRock과 Ondo: 상품별 권리·현금·보수와 실제 사업 위치

기준일: **2026-11-04 KST**. 공식 공개 문서와 발표를 선택 열람했다. 이는 상품 비교와 금융기관 사업 설계를 위한 조사이며, 특정 고객의 가입 가능성이나 최종 계약 효력을 판정한 문서는 아니다. 출처는 [자료별 기록](../sources/README.md)과 [상품 경제성 원장](../data/blackrock_ondo_product_economics.json)에 연결했다. 겹친 원문은 P 식별자로 통합했다. 발표일 없는 문서는 기준일에 읽은 변경 가능한 페이지이며 과거 계약의 고정 사본이 아니다.

## 1. 먼저 고쳐야 할 비교 구도

BlackRock과 Ondo를 각각 ‘전통 운용사’와 ‘블록체인 유통사’로 고정하면 실제 계약과 보수 경로가 빠진다. BlackRock은 BUIDL에서는 **투자운용자**, OUSG가 BUIDL을 보유하는 관계에서는 **기초상품 공급자**, OIP에서는 **일부 모델 제공자**다. Ondo는 OUSG의 펀드·자문·토큰화 구조, Stocks의 별도 발행법인과 채권 포장, OIP의 포트폴리오 집행·관리, Network의 인프라를 나눠 봐야 한다. 두 회사는 같은 고객의 자금을 두고 경쟁하면서 다른 단계에서는 함께 보수를 얻을 수 있다. [BUIDL 역할 공시](https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx), [OUSG 법인·자산](https://ondo.finance/ousg), [OIP 모델 제공자](https://docs.ondo.finance/intelligent-portfolios/model-providers)

‘BlackRock은 USDC만 쓰고 Ondo는 은행을 없앤다’는 이분법도 이 자료에서 성립하지 않는다. 펀드·주식 보관, 매매 집행, 송금과 환매에는 기존 금융기관과 별도 운영자가 계속 관여한다. 고객에게 중요한 것은 토큰이 이동했는지뿐 아니라 **누구에 대한 어떤 청구권을 가지고, 언제 어떤 통화의 사용 가능한 은행잔액으로 바꿀 수 있는가**다.

| 상품 | 고객이 갖는 권리와 상대방 | 접근 조건 | 기초자산·모델 | 현금 전환의 핵심 |
|---|---|---|---|---|
| BUIDL | BlackRock USD Institutional Digital Liquidity Fund Ltd. 지분. BlackRock Financial Management, Inc.는 운용자 | 사모 적격 투자자, 온보딩·허용 지갑. 2024 최초 최소액을 모든 현행 클래스에 적용하지 않음 | 현금·미국 단기국채·repo | 펀드 USD 경로와 Circle 등에 지분을 넘겨 USDC를 받는 별도 경로 |
| OUSG | Ondo I LP 지분. 투자자문사는 Ondo Capital Management LLC | Accredited investor **및** qualified purchaser, 국가·온보딩 조건 | 현재 공개 표에 SWEEP·BUIDL·BENJI·FYOXX 등이 공존 | 즉시 환매는 USDC. 영업일 환매와 한도·잔여용량 별도 |
| USDY | 토큰화 채권. 개별 발행시점·약관·환매 상대방 확인 필요 | 적격 비미국 투자자, 국가별 추가 제한 | 발행시점에 따라 단기국채·단기국채 ETF 지분·은행예금 등 | 기존 LLC의 비미국 은행계좌 USD 환매와 BVI 법인 USDC 환매 구분 |
| Ondo Stocks / Global Markets | Ondo Global Markets (BVI) Limited 발행 구조화 채권. 기초 주식의 직접 주주권 아님 | 비미국·국가별 자격 및 KYC. 2차 보유와 직접 환매 자격 별도 | 대응 주식·ETF와 관련 현금, 담보 구조 | 기본 USDon, USDC는 조건부 교환 결합. 은행현금은 후속 단계 |
| OIP | Ondo Global Markets (BVI) Limited 발행 포트폴리오 토큰. 펀드·ETF 지분 아님 | Stocks 자격 적용 | BlackRock 3개 모델, Ondo 4개 모델. 실제 기초자산 묶음은 상품별 | 직접 발행환매는 미국 시장 영업시간 일부. 24시간 이전·2차 거래와 다름 |

근거: OBX-E-001~002, 004~010, 012, 014, 016, 019~025. 아래 절에서 계약·시점·비용의 한계를 더 구체화한다.

## 2. BUIDL: 운용·기록·판매·현금전환이 서로 다른 사업

2024년 공식 출시 문서는 BlackRock Financial Management를 투자운용자, BNY Mellon을 수탁·관리자, Securitize를 이전대행·토큰화 제공자, Securitize Markets를 판매대행자로 구분한다. 2026년 Tempo 확장 발표도 정확한 펀드명과 사모·이전 제한을 명시한다. 펀드 지분이 토큰으로 표시되어도 특정 국채의 직접 소유나 현물 인도를 요구하는 권리로 바뀌지 않는다. 은행예금·스테이블코인이 아니며 손실 가능성이 있다. [2024 역할](https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx), [2026 상품 고지](https://investors.securitize.io/news/news-details/2026/Tempo-expands-onchain-yield-offering-with-BlackRocks-BUIDL-fund/default.aspx)

보수도 분리해야 한다. 출시 문서상 운용자가 Securitize Markets에 소개 투자자와 연동한 판매대행 보상을 지급한다. 선급 정액은 이후 NAV 연동 보상에서 공제되므로 두 항목을 그대로 더해 비용을 부풀리면 안 된다. 정확한 비율·수취 법인별 전체 계약비용은 공개 범위에서 확정하지 못했다. 현재 BUIDL 안내 페이지에는 네트워크별 서로 다른 요율·최소금액의 복수 표가 있어 적용 클래스를 확인하지 않은 단일 보수율은 **null**로 남긴다. [보수 구조 공시](https://investors.securitize.io/news/news-details/2024/BlackRock-Launches-Its-First-Tokenized-Fund-BUIDL-on-the-Ethereum-Network-03-20-2024/default.aspx), [현재 안내와 한계](https://securitize.io/blackrock/buidl)

Circle의 2024 발표에서 고객은 지분을 **Circle에 넘기고 USDC를 받는다**. 이는 펀드에 직접 환매를 청구해 은행 달러를 받는 거래와 다르다. 이 역사적 발표만으로 현재 모든 투자자의 24시간 매도가 동일 가격·무제한 용량으로 가능하다고 할 수 없다. 고객이 은행현금을 원한다면 USDC에서 은행잔액으로 바꾸는 자격·계약·수수료·은행 영업시간을 추가 확인해야 한다. Circle이 지분을 인수한 뒤 어떤 계약·시점으로 자금을 회수하는지는 이번 자료에서 확정하지 않았다. [Circle 공식 발표, KNX-M-002](https://www.circle.com/pressroom/circle-announces-usdc-smart-contract-for-transfers-by-blackrocks-buidl-fund-investors)

**사업 해석:** 운용자에게는 운용보수, 이전대행자에게는 기록·이전·규정준수 운영 보수, 판매자에게는 판매대행 보수, 유동성 제공자에게는 계약상 보상 가능성이 각각 있다. 마지막 항목의 실제 가격·이익은 미확인이다. 고객자산 전체나 이동액을 이들 회사 매출로 계산하지 않는다.

## 3. OUSG: 기초펀드 공급자와 상위 상품 운영자는 경쟁과 보완을 동시에 한다

OUSG 발행자는 Delaware limited partnership인 **Ondo I LP**다. Ondo Finance Inc.는 토큰화 서비스를 제공하고 펀드 GP와 투자자문사의 유일 구성원이라고 하단 법적 고지가 설명한다. 투자자문사는 **Ondo Capital Management LLC**다. 펀드 지분을 보유하는 고객, 펀드, 자문사, 토큰화 서비스 법인을 한 회사의 현금으로 합쳐서는 안 된다. [OUSG 법적 고지](https://ondo.finance/ousg)

동일 페이지의 **2026-11-02 16:00 EST** 보유표는 SWEEP 47.79%, BUIDL 32.16%, BENJI 11.59%, FYOXX 7.44% 등을 표시한다. 이는 선택 열람한 회사 공개 표이며 수탁기관 자료와 독립 대조하지 않았다. 같은 페이지 FAQ에는 여전히 BUIDL 대부분이라는 설명이 남아 있다. 날짜 있는 표의 ‘복수 기초상품 공존’을 채택하되 이 내부 불일치를 지우지 않는다. 이 비중은 영구 배분·현재 매매 주문이 아니며 반올림된 항목이다. [날짜 있는 보유표와 FAQ](https://ondo.finance/ousg)

경제적으로 고객은 기초자산 수익에서 여러 단계의 비용을 부담한다. 문서에 따르면 연 0.15% 관리보수는 **2027-01-01까지 면제**, 펀드 비용은 연 0.15% 상한이며, 기초펀드 비용은 해당 펀드 수익에서 별도로 차감된다. 관리보수 면제는 기초펀드·운영·거래 비용 전체의 면제가 아니다. 관리보수와 비용상한의 정확한 포함관계는 최종 계약 미확인으로 남기며 두 0.15%를 기계적으로 더해 총 0.30%라고 계산하지 않는다. 현행 상품 페이지의 즉시거래 표시와 문서의 추가 비용 가능성을 함께 확인해야 한다. 2027년 부과·면제 연장의 실제 상태는 후속 관측 사항이다. [OUSG 비용](https://docs.ondo.finance/qualified-access-products/ousg/fees-and-taxes)

즉시 환매는 USDC를 받는 경로다. 공개 한도는 최소 5천 달러, 글로벌·개별 24시간 한도와 남은 용량을 함께 적용한다. 기초 펀드·은행이 닫혀도 먼저 환매해 주려면 누군가 USDC 재고·신용·헤지·재조달 부담을 감당한다는 것이 경제적 해석이다. 토큰화가 그 비용을 없애지는 않는다. [환매](https://docs.ondo.finance/qualified-access-products/ousg/redeeming), [한도](https://docs.ondo.finance/qualified-access-products/ousg/instant-limits)

**고객 예시 — 조건부:** 적격 기업 재무팀이 OUSG를 보유하다 지급일에 USDC 환매를 실행한다. 거래 한도가 충분해도 기업의 최종 채무가 은행 USD 지급이라면 오프램프 완료 전에는 지급 가능 은행현금으로 세지 않는다. 반대로 계약 상대방이 USDC 수취로 채무 이행을 인정한다면 후속 송금 단계를 줄일 수 있다. 이는 계약상 선택이며 ‘모든 달러 채무에 동일’한 사실이 아니다.

## 4. USDY: 과거 설명을 현재 발행분 전체에 복사하면 권리와 환매 법인이 틀린다

현재 공식 Basics는 USDY를 과거 Ondo USDY LLC가 발행한 토큰화 채권으로 소개하고 **2025-12-15부터 Ondo Stocks 범주에 편입**됐다고 설명한다. 담보는 발행시점에 따라 단기국채, iShares Short Treasury Bond ETF 지분, 은행 요구불예금 등이 될 수 있다. 따라서 ‘USDY는 항상 같은 미국 LLC의 동일 담보채권’ 또는 ‘현재 모두 동일 BVI 계약으로 바뀌었다’는 두 단정 모두 피해야 한다. [USDY 현재 설명](https://docs.ondo.finance/general-access-products/usdy/basics)

현재 앱 구매에는 Stocks 약관을 안내한다. 같은 문서는 **Ondo USDY LLC의 은행송금 USD 환매는 비미국 은행계좌만 가능**하고, **USDC 환매는 Ondo Global Markets (BVI) Limited 경로**라고 나눈다. 특정 기존 보유분의 경개·교환·담보순위는 개별 발행 문서 확인 전까지 null이다. 일반 상품 페이지의 미국 소재 표시가 이 복잡성을 모두 설명하지 못한다는 점도 보존한다. [발행·환매 상대방](https://docs.ondo.finance/general-access-products/usdy/basics), [일반 상품 페이지](https://ondo.finance/usdy)

USDY는 국채 그 자체나 국채 인도를 요구하는 권리가 아니다. USDY 가격에 수익이 누적되는 형태와 rUSDY 수량이 변하는 형태도 은행예금·예금보호를 뜻하지 않는다. rUSDY가 잠근 USDY와 두 토큰의 가치를 함께 더하면 중복 계산한다. 비미국 대상이라는 조건도 모든 국가의 개인에게 판매할 수 있다는 뜻은 아니다. [권리 고지](https://docs.ondo.finance/general-access-products/usdy/important-notes), [자격](https://docs.ondo.finance/general-access-products/usdy/eligibility), [wrapper 구조](https://docs.ondo.finance/general-access-products/usdy/basics)

**수익의 미확인:** 현재 공개 페이지는 계약에 따른 월별 적용 APY 결정을 설명하지만, 발행분별 명확한 관리보수·스프레드·이익수취 법인 전체를 이번 조사에서 확정하지 못했다. ‘기초수익률−USDY APY’를 바로 Ondo 순이익이라고 쓰면 보관·유동성·운영·담보 버퍼·세금·시차를 빠뜨린다. 해당 값은 null로 둔다.

## 5. Stocks: 주식이 그대로 지갑에 들어오는 것이 아니라 발행자에 대한 다른 청구권이다

현재 문서가 Ondo Stocks라고 부르는 Global Markets 상품은 **Ondo Global Markets (BVI) Limited의 구조화 채권**이다. 기초 주식·ETF를 보관하고 대응 경제적 노출을 제공하지만 토큰 보유자에게 기초 기업의 의결권 등 직접 주주권을 부여하지 않는다. 자산 분리·담보권·담보대리 구조는 발행자 부도 때의 보호 장치지만 ‘즉시 원금 회수 보증’은 아니다. Ankura 집행은 정해진 사건·절차·보유자 지시와 관련된다. 최종 Sales Terms와 모든 도산 조항은 가입 후 문서여서 이번에는 읽지 않았다. [법적 구조](https://docs.ondo.finance/ondo-stocks/legal-and-regulatory), [담보와 집행](https://docs.ondo.finance/ondo-stocks/trust-and-transparency)

현금 경로는 다음처럼 분리한다.

1. 고객 온보딩과 국가·투자자 자격 확인.
2. 발행·환매 기본 결제수단은 **USDon**.
3. USDC로 거래할 때는 USDon↔USDC 교환을 묶을 수 있으나 상대 토큰 재고 등 조건이 있다. 직접 USDon 교환은 별도 승인·접근 조건이 있다.
4. USDC를 받았어도 은행 USD는 아직 아니다. Stocks의 은행송금 환매는 지원되지 않는다고 안내하므로, USDY의 기존 LLC 송금 경로를 Stocks 전체에 가져오지 않는다.
5. 최종 은행현금을 원하면 적격 오프램프·은행계좌·송금·FX 조건을 별도 확인한다.

[발행·환매 및 USDon](https://docs.ondo.finance/ondo-stocks/investing-and-redeeming)

문서의 즉시성·시장위험 관련 홍보 문구를 무위험 현금 판정으로 채택하지 않았다. USDon 준비자산·발행 법률관계 전체를 이번 조사에서 독립 검증하지 못했고, 교환·발행·수탁·운영·권한 위험은 구분해서 남겨야 한다.

보수는 호가와 실제 기초자산 집행가격의 차이, 별도 수수료, 고객 가스비, 제3자 거래비용으로 갈린다. ‘플랫폼이 취득한다’는 설명은 있지만 정확한 수취 법인·요율·순마진은 null이다. 배당 등 기초 현금흐름은 발행자 단계의 원천징수 후 반영되며 모든 자산·고객에 하나의 세율을 적용하지 않는다. [비용·세금](https://docs.ondo.finance/ondo-stocks/fees-and-taxes)

## 6. OIP: BlackRock 모델과 BlackRock이 운용하는 펀드는 다르다

공식 발표상 **2026-09-24 출시**, **10-29 Solana 확장**이 확인된다. 현재 명단에는 BlackRock 모델의 BLKHIon·BLKDIGon·BLKGRWon과 Ondo 모델의 MAG7Xon·BRAINon·YLD5on·YLD8on, 총 일곱 상품이 있다. YLD5·YLD8 등의 이름·목표가 보장수익을 뜻하지 않는다. 가능한 기초자산 범주는 확인했지만 상품별 **현재 ETF 전체 목록과 비중은 앱 자료 미열람으로 null**이다. IBITon 같은 예시 하나를 모든 포트폴리오의 구성으로 확대하지 않는다. [출시](https://ondo.finance/blog/introducing-ondo-intelligent-portfolios), [Solana 확장](https://ondo.finance/blog/intelligent-portfolios-go-live-on-solana), [상품 범위](https://docs.ondo.finance/intelligent-portfolios/available-assets)

OIP 발행자는 Ondo Global Markets (BVI) Limited다. 공식 문서는 OIP가 펀드·ETF 자체도 그 지분도 아니라고 한다. 모델 제공자는 자산과 목표 비중을 정하고, Ondo가 실제 거래·재조정·발행환매를 수행한다. 특히 **모델 제공자는 토큰 발행·후원·운용·관리·수탁자가 아니며 토큰 보유자와의 계약관계도 아니다.** 따라서 BlackRock 이름만으로 BlackRock이 이 토큰의 환매·손실·운영을 책임진다고 하면 틀린다. [OIP 구조](https://docs.ondo.finance/intelligent-portfolios/overview), [모델 제공 역할과 제외](https://docs.ondo.finance/intelligent-portfolios/model-providers)

연간 서비스비는 매일 토큰 가치에서 반영되고 기초토큰의 발행환매 비용·호가 차이·가스·제3자 비용과 구분된다. 실제 요율은 상품별 페이지를 읽지 못해 null이다. 기초 ETF를 보유하는 구조라면 그 ETF 수준의 비용도 투자자 최종 수익에 반영되는지 확인해야 하며, 모든 비용이 Ondo 매출인 것은 아니다. **BlackRock 모델 제공에 별도 보수가 있는지, 누가 지급하는지, 어떤 법인이 받는지는 공개 계약 미확인**이다. iShares 상품 보유로 발생하는 해당 펀드의 보수와 모델 보수를 임의로 합치지 않는다. [OIP 비용과 원천징수](https://docs.ondo.finance/intelligent-portfolios/fees-taxes)

발행은 모델의 목표 비중, 환매는 당시 현재 비중에 따라 이루어진다. 신규 자금이 목표 비중으로 들어오면 기존 편차를 일부 줄일 수 있다는 것은 계산상 해석일 뿐, 유입만으로 완전한 재조정이 되거나 거래·세금 비용이 사라진다는 뜻은 아니다. 공식 설계는 대략 분기 재조정이다. [발행·환매 비중](https://docs.ondo.finance/intelligent-portfolios/investing-redeeming)

직접 발행환매는 일반적으로 미국 시장 영업일 **ET 09:30~15:45**이며 구성자산 하나의 거래 정지로 묶음 전체가 멈출 수 있다. 현재 포트폴리오 토큰은 Stocks 일부 단일자산의 off-hours 기능 대상도 아니다. 제한 조건 아래 24시간 온체인 이전·2차 거래가 가능하다는 것과 발행자 환매가 24시간이라는 것은 다르다. 장외시간 2차시장은 스프레드·가격 괴리가 커질 수 있다. [거래시간·중단 조건](https://docs.ondo.finance/intelligent-portfolios/market-hours)

2차 취득만으로 직접 환매 자격이 생기지 않는다. Stocks와 같은 자격 및 KYC를 충족해야 한다. 이 점은 ‘개인 AI가 언제든 상품을 조합·매수·현금화한다’는 사업 가정에서 중요한 문턱이다. [자격](https://docs.ondo.finance/intelligent-portfolios/eligibility)

## 7. ONDO와 Ondo Network: 상품 성장의 이익 귀속을 별도 입증해야 한다

ONDO의 공식 설명은 DAO·Flux Finance 거버넌스 기능이다. 공개 판매 위험 고지는 ONDO 보유가 회사·계열사·플랫폼의 지분·배당·매출·이익에 대한 권리를 부여하지 않는다고 명시한다. 이는 해당 계약 문서의 범위이며 미래의 모든 거버넌스 변경을 단정하는 말은 아니다. 그러나 현재 자료로 상품 운용자산이나 수수료 증가를 ONDO 보유자의 자동 현금배당으로 연결할 근거는 없다. [거버넌스](https://docs.ondo.foundation/ondo-token), [판매 위험 고지](https://docs.ondo.foundation/coinlist/coinlist-risk-factors)

2026-07-27 공식 발표는 초기 Ondo Chain 구상에서 Ondo Network로 방향이 바뀌었으며 당시 Network는 블록체인이 아니라고 명시한다. Perps를 첫 실서비스로 제시하고 실행·증명 구조를 설명한다. 이 발표를 독립적인 가동·보안·수익 검증으로 읽거나 ‘ONDO가 반드시 체인 가스이며 모든 이용료를 받는다’고 확대하면 안 된다. Network의 수수료·자본비용·ONDO 귀속은 별도 계약·운영자료가 필요하다. [Network 전환 발표](https://ondo.finance/blog/introducing-the-ondo-network)

## 8. 보수와 비용을 끝까지 연결하는 계산 틀

다음은 실적 추정치가 아닌 **같은 고객·기간·통화로 비교할 계산 항목**이다. 계약이 없으므로 수치는 채우지 않는다.

- **기초 운용자 기여:** 실제 운용보수 수입 − 해당 고객·상품에 귀속되는 판매보상·관리·수탁·기타 비용. 이미 순액으로 기록한 비용을 재차 차감하지 않는다.
- **포장·운영자 기여:** 계약상 서비스·관리·거래 수입 + 실현된 가격차 수입 − 집행·수탁·법률·온보딩·감사·데이터·기술·유동성·사고회수 비용. 고객 투자원금·기초 수익·AUM 증가를 매출로 추가하지 않는다.
- **고객의 기간 성과:** 기간 중 분배·매각·환매 현금 + 기말 잔존가치 − 기초 보유가치 − 기간 중 추가납입 − 아직 반영하지 않은 직접비용. 평가할 자산·포트폴리오 범위를 먼저 고정하고, 현금은 그 범위 밖으로 실제 지급된 금액만 더한다. 범위 안의 재투자·자산 간 교환이나 기말가치에 포함된 유보현금은 현금유출입으로 다시 세지 않는다. 비용이 이미 NAV·가격·수취현금에 반영됐다면 재차 차감하지 않는다. 원천징수와 투자자 개별 세금, FX 및 은행현금 도달 시점을 별도 기록한다.
- **유동성 제공자 기여:** 계약 수입·실현 가격차 − 재고 조달·헤지·유동성·불이행·운영 비용. 24시간 교환을 제공하려고 확보한 재고는 무상 자금이 아니다.

같은 ‘담보’라는 단어도 세 종류다. **발행자의 의무를 뒷받침하는 기초담보**, **고객이 토큰을 맡겨 차입할 때 대주가 인정하는 담보**, **스테이블코인 발행자의 법정 준비자산 적격성**은 서로 다르다. 어느 하나를 확인했다고 나머지가 성립하지 않는다. 법률·대주 계약·평가와 haircut·회수권·운영 통제 각각을 확인해야 한다.

## 9. 은행·증권·보험 신사업으로 가져갈 때의 경쟁 경로

**기준 경로:** 고객이 합법적으로 기존 ETF·펀드를 낮은 비용으로 사고, 필요한 시점에 기존 은행현금을 받을 수 있다면 기존+AI가 우세할 수 있다. AI는 적격성·비용·세금·환매시간을 비교하고 사람이 승인할 거래안을 만든다. 단순 토큰 포장만으로 추가 보수를 받기 어렵다.

**강한 변화 가정:** 합법적 유통, 안전한 수탁·권리집행, 실제 담보 수용, 고객의 지급·투자 계약이 성립하고 AI가 여러 상품을 비교·조합한다고 가정한다. 그러면 금융기관은 가격뿐 아니라 ‘이 고객이 실제 보유·환매 가능한 상품’, 기한 내 가용 현금, 자산별 담보 조건, 주문 취소·오류복구·회사행위 처리를 기계가 확인할 수 있게 제공해야 한다. 고객은 접속 자체보다 실행·관리·회수의 신뢰성에 지불할 수 있다. 상품추천은 AI가 하더라도 금액·한도·상충 주문·중복담보·적합성·권한은 결정론적 검증과 책임 주체가 필요하다.

**다음 경쟁 반응:** 기초 운용사가 직접 온체인 상품과 API를 늘리면 중간 포장자가 받던 접근 프리미엄이 줄 수 있다. 반대로 복수 운용사 비교·현금전환·국가별 고객 자격·사후관리를 묶는 사업자는 규모를 얻을 수 있다. 기존 은행은 예금금리·결제·신용과 연계하고 증권사는 기존 ETF 매매·담보대출 비용을 낮출 수 있다. 고객 비용 절감이 누구의 보수 감소인지까지 봐야 한다.

따라서 한국 금융기관이 지금 비교할 작은 실험은 ‘Ondo 복제’가 아니라 **한 고객·한 목적·한 통화·한 지급기한**의 두 경로다. 같은 투자노출에 대해 기존+AI와 온체인+AI의 자격 확인, 실제 견적, 권리, 총비용, 은행현금 도착 시각, 장애 복구, 담당자 시간을 대조한다. 토큰 이동속도만 측정해서 총비용 절감을 주장하지 않는다. 한국 판매·중개·수탁·외환·세금 조건은 외국 상품 존재에서 자동 도출하지 않는다.

## 10. 판단을 바꿀 다음 자료

| 미확인 | 현재 처리 | 무엇을 확인하면 판단이 바뀌는가 |
|---|---|---|
| BUIDL 현행 클래스·투자자별 요율 및 판매 보상 | null | 날짜·클래스가 지정된 설명서·보수계약 |
| OUSG 최신 구성과 오래된 FAQ 충돌 | 날짜 있는 표를 제한적으로 채택 | 같은 날짜의 NAV/수탁 검증 자료·정정 문서 |
| USDY 기존·신규 발행분의 정확한 채무자·담보·경개 | 발행분별 null | 당시 청약·교환·담보 문서와 변경 통지 |
| Stocks USDon의 법적 권리·준비자산 및 교환 계약 전체 | 상품 결제 경로만 채택 | 발행 약관·준비자산·상환자격·교환 제한 |
| OIP 개별 현재 ETF·비중·서비스 요율 | null | 해당 상품·시각의 앱 표와 계약 |
| BlackRock 모델 보수·법인별 배분 | null | 모델 공급 계약 또는 명시 공시 |
| 유동성·상시 실행·수익성 | 회사 설명과 별도 | 실제 실패율·한도 사용·은행현금 도달·원가·수취 보수 |
| ONDO 현금흐름 귀속 | 자동 귀속 근거 없음 | 법적·거버넌스 변경과 집행되는 수익 배분 계약 |

출처 패킷은 공개 원문별 읽은 범위, 시점, 한계와 주장 식별자를 보존한다. 이번 분석은 현재 상품 설명의 차이를 확인하는 데 집중했으며 모든 관할 법률·최종 계약·독립 수탁자료를 검증한 것은 아니다.



연결: [전체 환경 판단](29_tokenization_competition_group_strategy.md) · [상품 경제성](../data/blackrock_ondo_product_economics.json) · [그룹 대응 원장](../data/global_position_group_map.json) · [실행·검증](../runs/2026-11-04-ondo-position-integration.json)
