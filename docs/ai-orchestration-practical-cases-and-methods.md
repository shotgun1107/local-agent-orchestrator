# AI 오케스트레이션 실용 사례와 구축 방법론 조사

- 조사 기준일: 2026-08-03
- 문서 목적: 실제 AI 오케스트라를 설계하거나 후속 조사를 수행할 때 재사용할 수 있는 사례, 방법론, 판단 기준을 보존한다.
- 범위: LLM 멀티에이전트에 한정하지 않고 업무 워크플로, SRE, 과학 연구, 소프트웨어 개발, 우주 자율 시스템, 프로세스 공학을 포함한다.
- 제외 범위: 특정 프로젝트를 위한 최소 구현 구조나 구체적인 코드 설계안은 다루지 않는다.

> **문서 상태:** 동결(freeze), 2026-08-03.
>
> **검증 수준:** 이 문서는 동료 심사와 링크 전수 점검을 거치지 않았다. 본문의 사실·수치 가운데 아래 §1과 §12에 반영한 `Measuring Agents in Production`·`Characterizing Agents in Production` 판본 구분 1건만 원문 대조로 확인됐다.
>
> **서지 형식:** 본문 인용은 저자·연도·발표 장소 없이 URL 중심이므로, 학술 인용에 그대로 옮기기 전에 원문 확인이 필요하다.
>
> **주 문서와의 관계:** [AI 오케스트레이션: 폭넓은 문헌조사와 분야 간 종합](./ai-orchestration-broad-literature-review.md)이 동료 심사와 링크 전수 점검을 거친 문서다. 두 문서에 같은 자료가 등장하면 서지 정보는 주 문서를 기준으로 삼는다.
>
> **갱신 정책:** 이 문서는 동결됐다. 새로운 사례나 수치가 필요하면 이 파일을 수정하지 말고 별도 문서를 만들거나 주 문서에 반영한다.

## 1. 먼저 읽을 결론

실제 운영 중인 AI 오케스트라는 흔히 상상하는 "여러 에이전트의 자유로운 회의"와 상당히 다르다.

1. 생산 시스템은 대체로 짧고 통제 가능한 워크플로를 사용한다.
2. 에이전트 수보다 업무 절차, 도구 인터페이스, 승인 단계, 평가 데이터가 성능을 더 크게 좌우한다.
3. 멀티에이전트는 병렬 조사, 전문 분야 분리, 후보 비교에는 유리하지만 엄격한 순차 작업에서는 성능을 악화시킬 수 있다.
4. 고위험 시스템은 조사와 실제 실행을 분리한다.
5. 높은 자율성은 한 번에 부여하지 않고, 관찰 전용에서 제한 자동 실행까지 단계적으로 확대한다.
6. 성공 여부는 답변 문장의 품질보다 외부 시스템의 실제 상태, 테스트, 실험 결과로 판정해야 한다.
7. 복잡한 멀티에이전트 방식은 항상 단순 파이프라인과 비용·정확도·신뢰도를 비교해야 한다.

ICML 2026 본회의에 채택된 확장판 `Characterizing Agents in Production`은 20개 심층 사례와 26개 도메인, 배포 시스템 실무자 306명을 조사했다. 초기판 `Measuring Agents in Production`은 ICLR 2026 `Agentic AI in the Wild` 워크숍에 게재됐으며 실무자 표본은 86명이었다. 두 판본 모두 조사 대상의 68%는 사람 개입 전에 최대 10단계만 실행했고, 70%는 파인튜닝보다 범용 모델과 프롬프트를 사용했으며, 74%는 사람 평가에 주로 의존한다고 보고했다. 가장 큰 개발 문제는 반복적으로 올바르게 행동하는 신뢰성이었다.

- 확장판: https://icml.cc/virtual/2026/poster/61834
- 초기판: https://openreview.net/forum?id=AsvLggSOvS
- 초기판 arXiv: https://arxiv.org/abs/2512.04123

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §9.2 참조.

## 2. 근거 수준을 읽는 방법

사례의 홍보성 주장과 재현 가능한 결과를 구분하기 위해 다음 수준으로 분류한다.

| 수준 | 의미 | 예시 |
|---|---|---|
| A | 동료 평가 논문이며 실제 환경 또는 외부 실험으로 결과를 확인 | Coscientist, Virtual Lab, Co-Scientist |
| B | 조직이 실제 운영했다고 공개했지만 성과 수치는 자체 보고 | Google AI Operator, Meta RCA, AWS Field Advisor, Ramp |
| C | 코드 또는 논문으로 재현할 수 있는 연구·벤치마크 시스템 | Magentic-One, MetaGPT, SWE-agent, Agentless |
| D | 공급사 고객 사례 또는 마케팅 자료 중심 | 일부 고객지원·워크플로 플랫폼 사례 |

수준이 낮다는 것은 사례가 쓸모없다는 뜻이 아니다. 다만 수치가 독립적으로 재현됐다고 간주하면 안 된다.

## 3. 기업 운영 사례

### 3.1 AWS Field Advisor

**근거 수준: B**

AWS 영업 조직에는 컴플라이언스, 제품 추천, 가격 분석 등 20개 이상의 전문 에이전트가 별도로 배치되어 있었다. 사용자가 어떤 에이전트를 선택해야 하는지 알아야 한다는 문제가 생기자 Field Advisor를 상위 통합 계층으로 구축했다.

운영 방식:

- CRM, Slack, 웹 포털에 단일 인터페이스 제공
- supervisor가 로컬 도구와 원격 전문 에이전트 중 하나를 선택
- 사용자 OAuth 신원을 하위 도구와 에이전트까지 전달
- 레코드 생성·수정 같은 민감 작업은 원클릭 승인 사용
- 사용자 세션별 격리 실행
- 공통 메모리, 인증, 관측 기능 사용

AWS 자체 보고 결과:

- 이전 인프라 대비 지연시간 41% 감소
- 일부 영업 담당자 기준 주당 최대 2시간 절약
- 7개 AWS 계정에 분산돼 있던 실행 인프라 통합
- 약 450개 계정 검증 작업에 활용

재사용할 교훈:

- 전문 기능이 이미 많을 때 상위 라우터가 사용자 인지 부담을 줄인다.
- 에이전트 간 대화보다 신원 전달, 세션 격리, 승인, 관측이 운영의 핵심이다.
- 원격 에이전트를 일반 도구처럼 감싸면 상위 supervisor의 인터페이스를 단순화할 수 있다.

출처:

- https://aws.amazon.com/blogs/machine-learning/powering-agentic-ai-sales-strategy-with-amazon-bedrock-agentcore/
- https://docs.aws.amazon.com/solutions/multi-agent-orchestration-on-aws/

### 3.2 Google AI Operator

**근거 수준: B**

Google의 AI Operator는 실제 생산 경보의 첫 조사자로 동작하며 수천 건의 사고에서 실행됐다.

운영 방식:

- 경보 수신 후 여러 조사를 병렬 수행
- 과거 전문가의 성공적인 조사 예시를 이용해 원인 가설 생성
- 로그, 이상 탐지, 경보 설명, 플레이북과 전문 스킬을 필요할 때만 선택
- 장기 조사에서 컨텍스트가 무너지지 않도록 단계별 토큰을 제한
- 낮은 위험의 경미한 사고는 자동 조치
- 중요한 생산 변경은 사람 SRE 승인 필요
- 조치 후 경보가 해제됐는지 확인하고, 계속되면 다시 조사
- 전체 조사 이력을 사고 관리 UI에 남겨 사람이 즉시 이어받을 수 있게 함

특히 AI Operator는 생산 명령을 직접 실행하지 않는다. 별도의 Actuation Agent가 다음을 담당한다.

- 허용된 완화 도구만 동적으로 노출
- LLM 의도를 구체적 실행 계획으로 변환
- dry-run과 사전 안전 검사
- 해당 행동이 현재 열린 사고를 대상으로 하는지 확인
- 동시에 실행 중인 다른 조치와 충돌하는지 확인
- 위험 증가 시 자동 실행을 사람 승인 단계로 강등
- 장기 실행 상태 추적과 사후 성공 확인
- 전체 자동 작업을 중지하는 Red Button 제공

Google은 모든 실행 흔적을 Spanner에 저장하고, 이상적인 사람 대응인 Golden Data와 비교한다. 실패한 실행에서는 LLM 기반 평가기가 비평과 개선 계획을 생성해 버그를 등록한다.

재사용할 교훈:

- 조사 에이전트와 실행 에이전트를 분리한다.
- 자율성은 고정 등급이 아니라 현재 위험에 따라 동적으로 낮출 수 있어야 한다.
- 사람이 이어받을 때 처음부터 재조사하지 않도록 조사 이력을 요약·보존한다.
- 실행 이후 실제 환경을 다시 관찰해야 작업 완료를 판정할 수 있다.

출처:

- https://sre.google/resources/practices-and-processes/ai-engineering-reliable-operations/

### 3.3 Meta의 AI 보조 장애 원인 분석

**근거 수준: B**

Meta는 웹 모노레포에서 장애 원인이 될 수 있는 수천 개 코드 변경을 한 번에 LLM에 제공하지 않았다.

처리 방식:

1. 코드 소유권, 디렉터리 정보, 런타임 코드 그래프를 이용해 수천 개 후보를 수백 개로 축소한다.
2. 한 프롬프트에 최대 20개 변경만 넣는다.
3. LLM이 그룹별 상위 5개를 선택한다.
4. 여러 그룹의 결과를 모아 선거식 순위 선정을 반복한다.
5. 최종 후보 5개를 사람 조사자에게 제시한다.

학습과 평가:

- 과거 장애를 기반으로 약 5,000개 RCA instruction-tuning 예시 구성
- 장애 생성 시점에 실제로 이용 가능했던 정보만으로 역테스트
- 실제 원인이 최종 상위 5개에 포함된 비율 42%

재사용할 교훈:

- 대규모 후보 탐색은 휴리스틱·그래프·검색 시스템이 먼저 담당한다.
- LLM은 작은 후보 집합의 의미 비교와 순위 선정에 집중시킨다.
- 결과 하나를 강제로 고르기보다 상위 후보 목록을 사람에게 주는 것이 초기 도입에 적합하다.
- 평가 시 미래 정보가 섞이는 데이터 누수를 막아야 한다.

출처:

- https://engineering.fb.com/2024/06/24/data-infrastructure/leveraging-ai-for-efficient-incident-response/

### 3.4 Ramp의 Prefect 기반 공통 워크플로 플랫폼

**근거 수준: B**

핀테크 기업 Ramp는 ML, ETL, LLM과 에이전트 작업을 Prefect 기반 공통 실행 플랫폼으로 통합했다.

자체 보고 결과:

- 한 분기 동안 기존 워크플로 200개 이전
- 총 350개 배포 워크플로 운영
- 70명 이상의 활성 기여자 지원
- 단순 작업은 아이디어에서 생산 배포까지 30분 이내 가능

운영 방식:

- 핵심 코드는 플랫폼 팀이 소유하고 사용자는 매개변수, 이벤트 트리거, 스케줄을 설정
- 코드 에이전트가 올바른 패턴으로 작업하도록 조직 전용 skills 제공
- 실제 생산 권한과 유사한 원격 환경에서 개발 단계부터 실행
- 경보 채널을 감시하고 장애 조사 후 수정 PR을 작성하는 Automated Debugger 운영

재사용할 교훈:

- 에이전트 프레임워크가 아니라 기존 워크플로 엔진을 실행·복구·관측 기반으로 사용할 수 있다.
- 프레임워크의 자유도를 그대로 노출하지 말고 조직이 템플릿과 권장 패턴을 제공한다.
- 업무를 아는 사람이 안전한 템플릿 안에서 자동화를 만들 수 있게 하면 중앙 ML 팀의 병목을 줄일 수 있다.

출처:

- https://www.prefect.io/blog/ramp-case-study

### 3.5 Trendyol의 n8n 운영

**근거 수준: D**

Trendyol은 판매자 지원, 법률 보조, 검색 관련성, 코드 리뷰와 소규모 자동화를 n8n 기반으로 운영한다.

자체 보고 규모:

- 사용자 1,000명 이상
- 활성 워크플로 700개
- 3개월간 약 500,000회 실행

재사용할 교훈:

- 시각적 워크플로 도구는 비개발자와 개발자가 프로세스를 함께 검토하는 공용 언어가 될 수 있다.
- 조직 전체 자동화에서는 단일 거대 오케스트라보다 여러 제한된 워크플로가 관리하기 쉽다.
- 장기적으로는 버전 관리, 권한 분리, 운영 환경 구분이 필수다.

출처:

- https://n8n.io/case-studies/trendyol/

### 3.6 TMNZ의 n8n과 에이전트 결합

**근거 수준: D**

TMNZ는 시장 조사, 송장 처리, 데이터 보강, HR, 재무와 운영 자동화를 n8n에서 실행한다.

자체 보고 규모:

- 월 약 150,000회 실행
- 월 약 400시간 절약
- OpenAI, Azure, Anthropic 등 여러 모델과 자체 PostgreSQL·벡터 저장소 사용
- MCP 서버와 대화형 에이전트를 n8n 워크플로에서 조합

특히 n8n을 최종 구현 도구로만 사용하지 않고 업무 로직을 빠르게 시각화·검증한 뒤, 필요한 경우 엔지니어링 팀이 정식 서비스로 다시 구현했다.

재사용할 교훈:

- 시각적 오케스트라는 업무 요구사항 발견과 프로토타입 검증에 강하다.
- 프로토타입을 영구 운영해야 한다는 강박 없이, 학습한 프로세스를 코드 서비스로 옮길 수 있다.
- 모델과 저장소를 교체 가능한 모듈로 취급하면 특정 공급자 종속을 줄일 수 있다.

출처:

- https://n8n.io/case-studies/tmnz/

### 3.7 Coinbase 고객지원

**근거 수준: D**

Coinbase는 고객지원 챗봇, 사람 상담원 보조, 도움말 검색에 AI를 적용했다.

공개된 처리 구성:

- 질의 재작성
- 지식 검색
- 응답 생성
- 출력 문체 조정
- 금융 컴플라이언스 가드레일
- 사람 상담원에게 설명과 초안 제공

운영 규모는 시간당 수천 개 메시지와 수백만 사용자로 보고됐다.

재사용할 교훈:

- 대규모 운영에서는 자유로운 에이전트 회의보다 단계별 전문 처리와 정책 검사가 더 일반적이다.
- 고객에게 직접 행동하는 시스템과 사람 상담원을 보조하는 시스템을 구분해 자율성 수준을 다르게 설정한다.

출처:

- https://www.anthropic.com/customers/coinbase

### 3.8 Intercom Fin

**근거 수준: D**

Intercom은 고객지원 에이전트를 지식, 행동 규칙, 실제 작업, 운영 분석의 네 영역으로 설명한다.

자체 보고 결과:

- 전체 고객 평균 자동 해결률 51%
- 일부 고객 환경에서 최대 86%
- 45개 이상 언어 지원
- 일부 고객 사례에서 지원량 50% 이상 자동화

재사용할 교훈:

- 지식 답변과 환불·계정 변경 같은 실제 행동을 분리한다.
- 조직별 정책과 문체는 모델의 일반 지식과 별도로 관리한다.
- 해결률만 보지 말고 정확도, 고객 만족, 사람 전환율을 함께 측정해야 한다.

출처:

- https://www.anthropic.com/customers/intercom

## 4. 과학과 물리 환경 사례

### 4.1 Coscientist

**근거 수준: A**

Coscientist는 계획 LLM, 웹 검색, 코드 실행, 하드웨어 문서 탐색, 클라우드 화학 실험실과 액체 처리 장비를 연결했다.

실증 범위:

- 알려진 화합물의 합성 계획
- 하드웨어 문서 검색과 해석
- 클라우드 실험실의 고수준 명령 실행
- 액체 처리 장비의 저수준 제어
- 여러 장비와 데이터 소스를 사용하는 복합 작업
- 수집된 실험 데이터 기반 최적화

재사용할 교훈:

- 자연어를 물리 장비 명령으로 바로 연결하지 않는다.
- 문헌 조사, 계획, 코드·명령 생성, 장비 실행, 측정 결과 회수, 재계획 단계를 분리한다.
- 최종 검증은 LLM 평가가 아니라 실제 실험 결과로 수행한다.

출처:

- https://www.nature.com/articles/s41586-023-06792-0

### 4.2 Virtual Lab

**근거 수준: A**

Virtual Lab은 LLM Principal Investigator가 면역학, 계산생물학, 머신러닝, 과학 비평 역할의 에이전트를 진행시키고 인간 연구자가 고수준 피드백을 제공하는 방식이다.

실증 결과:

- SARS-CoV-2 변이 대응 나노바디 92개 설계
- 실제 실험으로 기능성 후보 검증
- 두 후보가 최근 변이에 대해 개선된 결합 특성을 보임

재사용할 교훈:

- 역할은 사람 직함을 흉내 내기 위한 장치가 아니라 서로 다른 도구와 평가 기준을 소유해야 한다.
- AI 토론 결과를 현실 검증 단계와 연결해야 한다.
- 인간은 모든 대화를 감독하기보다 연구 방향과 고비용 실험 선택에 개입할 수 있다.

출처:

- https://doi.org/10.1038/s41586-025-09442-9

### 4.3 Google Co-Scientist

**근거 수준: A**

Co-Scientist는 다음 전문 작업을 비동기 큐로 운용한다.

- Generation: 가설 생성
- Reflection: 문헌·외부 검색을 이용한 반박
- Ranking: 가설 간 토론과 순위 결정
- Evolution: 상위 가설 변형과 개선
- Proximity: 가설 간 유사성과 관련성 확인
- Meta-review: 전체 결과의 경향과 빈틈 분석

Supervisor는 자연어 연구 목표를 계획 설정으로 바꾸고 작업 큐와 연산 자원을 배정한다. 가설은 토너먼트와 Elo식 자동 평가를 통해 반복적으로 비교·진화한다.

실증 범위:

- 약물 재창출
- 간 섬유증 치료 표적
- 항생제 내성 관련 유전자 전달 메커니즘
- 세 분야 모두 전문가 개입과 습식 실험을 통한 종단 검증 수행

논문의 절제 연구에서는 Reflection agent에 외부 검색을 제공했을 때 새로워 보이지만 불가능한 가설을 줄였고, Ranking 단계의 과학 토론은 순위의 위치 편향을 줄였으며, Evolution 단계의 반복 개선은 가설 품질을 높였다.

재사용할 교훈:

- 탐색 작업은 단일 정답 생성보다 후보군 생성과 경쟁에 적합하다.
- 비평 에이전트는 생성자와 같은 기억만 보지 말고 외부 검색·검증 도구를 가져야 한다.
- 자동 Elo는 우선순위 도구이지 실제 정답의 대체물이 아니다.
- 고비용 현실 검증으로 넘어갈 후보는 사람 전문가가 선택해야 한다.

출처:

- https://www.nature.com/articles/s41586-026-10644-y
- https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/

## 5. 소프트웨어 개발 사례

### 5.1 MetaGPT

**근거 수준: C**

MetaGPT는 제품 관리자, 설계자, 개발자, QA 역할을 두되 자유 대화보다 소프트웨어 개발 SOP와 중간 산출물을 강제한다.

재사용할 교훈:

- 역할별 입력과 출력 계약을 정의한다.
- 다음 역할은 전체 대화보다 필요한 중간 산출물을 받는다.
- 사람 조직의 직함이 아니라 검증 가능한 작업 단계를 옮긴다.
- 역할 프롬프트보다 SOP와 산출물 형식이 중요하다.

출처:

- https://arxiv.org/abs/2308.00352
- https://github.com/geekan/MetaGPT

### 5.2 ChatDev

**근거 수준: C**

ChatDev는 설계, 코딩, 테스트, 문서화 단계를 대화 체인으로 구성했다. 각 단계의 대화 상대와 목적을 제한하며 자연어는 설계, 프로그래밍 언어와 실행 피드백은 디버깅에 활용한다.

재사용할 교훈:

- 에이전트가 누구와 언제 통신하는지 제한한다.
- 산출물 종류에 맞는 언어와 도구를 사용한다.
- 모든 역할이 모든 단계에 참여하도록 만들지 않는다.

출처:

- https://arxiv.org/abs/2307.07924
- https://github.com/OpenBMB/ChatDev

### 5.3 SWE-agent

**근거 수준: C**

SWE-agent의 중요한 공헌은 멀티에이전트가 아니라 Agent-Computer Interface다. 저장소 탐색, 파일 편집, 테스트 실행을 모델이 이해하기 쉬운 명령과 관찰 형식으로 제공했다.

재사용할 교훈:

- 강력한 범용 셸보다 제한되고 예측 가능한 작업 명령이 나을 수 있다.
- 검색 결과와 테스트 로그를 무제한으로 반환하지 않는다.
- 편집 성공 여부와 현재 파일 위치를 명시적으로 알려준다.
- 잘못된 명령은 실행 전에 거부하고 수정 가능한 오류를 반환한다.
- 도구 사용성을 사람 UI가 아니라 모델의 인지 한계에 맞춰 평가한다.

출처:

- https://arxiv.org/abs/2405.15793
- https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md

### 5.4 Agentless

**근거 수준: C**

Agentless는 에이전트가 다음 행동을 자유롭게 선택하지 못하게 하고 다음 세 단계만 사용했다.

1. 오류 위치 탐색
2. 수정 후보 생성
3. 패치 검증

당시 SWE-bench Lite에서 32% 해결률과 문제당 약 0.70달러를 기록하며 더 복잡한 여러 오픈소스 에이전트를 능가했다.

재사용할 교훈:

- 복잡한 에이전트의 효과를 주장하려면 단순 단계식 처리와 비교해야 한다.
- 작업 순서가 이미 알려진 경우 LLM에 제어 흐름까지 맡길 이유가 적다.
- 지역화와 검증이 잘 정의된 문제에서는 후보 생성 부분만 확률적으로 두는 것이 유리할 수 있다.

출처:

- https://arxiv.org/abs/2407.01489

## 6. 범용 동적 오케스트레이션 사례

### 6.1 Microsoft Magentic-One

**근거 수준: C**

Magentic-One은 Orchestrator와 WebSurfer, FileSurfer, Coder, ComputerTerminal을 조합한다.

Orchestrator 내부에서는 두 종류의 장부를 분리한다.

- Task Ledger: 확인된 사실, 아직 확인되지 않은 추정, 전체 계획
- Progress Ledger: 현재 진행 상황, 담당 에이전트, 완료 여부, 정체 여부

진행이 없으면 바로 전체 계획을 다시 만들지 않고 정체 횟수를 센다. 일정 횟수 이상 진전이 없을 때만 바깥 루프에서 Task Ledger와 계획을 수정한다.

재사용할 교훈:

- 확인된 사실과 모델 추정을 분리한다.
- 전체 계획과 현재 실행 진척을 분리한다.
- "진행이 없음"을 판정할 기준과 정체 카운터를 둔다.
- 작업 완료 판정을 수행자에게만 맡기지 않는다.
- 해결 경로가 미리 알려지지 않은 문제에만 이런 동적 루프를 사용한다.

출처:

- https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §4.8 참조.

## 7. 멀티에이전트 사용 여부를 결정하는 정량적 결과

Google Research는 단일, 독립 병렬, 중앙집중, 분산, 혼합 구조를 포함한 180개 구성을 비교했다.

주요 결과:

- 병렬화 가능한 금융 분석에서는 중앙 오케스트레이터 방식이 단일 에이전트보다 80.9% 향상
- 엄격한 순차 계획에서는 모든 멀티에이전트 방식이 39~70% 악화
- 독립 병렬 에이전트는 오류를 최대 17.2배 증폭
- 중앙 오케스트레이터는 오류 증폭을 4.4배 수준으로 제한
- 도구가 16개 이상으로 많아지면 에이전트 조정 비용이 급격히 증가
- 작업의 분해 가능성과 도구 수를 이용한 예측 모델이 보지 않은 구성의 적절한 구조를 87% 식별

주의할 점:

- 이 결과는 특정 벤치마크와 모델군에 대한 연구 결과이며 모든 산업 환경에 그대로 적용되는 법칙은 아니다.
- 그러나 "에이전트가 많을수록 좋다"는 기본 가정을 반박하는 강한 근거다.

실용 선택표:

| 업무 성격 | 우선 검토할 방식 |
|---|---|
| 순서가 정해진 승인·처리 | 일반 워크플로에 필요한 LLM 단계만 삽입 |
| 독립적인 조사·분석 | 병렬 worker와 중앙 집계 |
| 명확한 품질 기준으로 반복 개선 가능 | 생성자–비평가–수정자 |
| 해결 경로가 사전에 알려지지 않음 | ledger 기반 동적 supervisor |
| 물리 장비·금융·생산 변경 | 조사와 실행을 분리한 단계적 자율성 |
| 코드·데이터처럼 자동 판정 가능 | 단순 파이프라인과 환경 검증 |
| 도구와 단계가 매우 많음 | 도메인 분할과 도구 지연 노출 |

출처:

- https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §9.1 참조.

## 8. AI 밖에서 가져올 방법론

### 8.1 NASA Deep Space 1 Remote Agent

**근거 수준: A에 준하는 실제 임무 기술 실증**

1999년 Deep Space 1 우주선의 Remote Agent는 다음 요소를 실제 우주에서 시험했다.

- 고수준 목표를 받는 planner/scheduler
- 계획을 구체적인 명령으로 변환하는 executive
- 우주선 상태를 진단하는 모델 기반 추론기
- 명령 결과를 감시하고 실패 시 수정·재계획
- 자체 해결 불가능 시 지상 운영자에게 도움 요청

네 종류의 모의 장애를 주입했고 각각 올바르게 구분하고 대응했다.

재사용할 교훈:

- 계획기와 실제 실행기를 분리한다.
- 실행기는 현재 자원·건강 상태·운영 제약을 다시 확인한다.
- 고위험 명령은 디지털 트윈, 시뮬레이션, dry-run으로 먼저 검증한다.
- 자율 시스템은 도움 요청 조건을 명시적으로 가져야 한다.

출처:

- https://www.jpl.nasa.gov/nmp/ds1/tech/autora.html
- https://www.jpl.nasa.gov/nmp/ds1/tech/autoraFAQ.html
- https://www.jpl.nasa.gov/news/remote-agent-experiment-meets-all-objectives/

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §7.5 참조.

### 8.2 Kubernetes reconciliation loop

Kubernetes controller와 kubelet은 원하는 상태와 실제 상태를 반복적으로 비교하고 차이를 줄인다.

AI 오케스트레이션에 적용할 원칙:

- 도구 호출 성공을 작업 완료로 간주하지 않는다.
- 실행 후 외부 시스템의 실제 상태를 다시 읽는다.
- 목표와 실제 상태의 차이가 있을 때만 추가 행동한다.
- 동일 명령의 반복 실행이 안전하도록 멱등성을 설계한다.
- 일회성 전체 계획보다 지속적인 상태 조정을 사용한다.

출처:

- https://kubernetes.io/docs/concepts/architecture/controller/
- https://kubernetes.io/docs/reference/node/kubelet-sync-loop/

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §6.4 참조.

### 8.3 FEMA Incident Command System

Incident Command System은 사고 규모와 복잡도에 따라 조직을 모듈식으로 확장·축소한다. 한 관리자의 직접 관리 범위는 보통 3~7개이며 이상적인 기준은 약 5개다.

AI 오케스트레이션에 적용할 원칙:

- 처음부터 모든 전문 에이전트를 생성하지 않는다.
- 사건 복잡도에 따라 필요한 기능만 추가하고 종료 후 해체한다.
- supervisor 하나에 수십 개 worker를 평면적으로 연결하지 않는다.
- command, planning, operations, logistics와 같은 기능 책임을 섞지 않는다.
- 에이전트와 도구의 현재 가용성·권한·비용을 자원 목록으로 관리한다.

출처:

- https://emilms.fema.gov/_is0200c/groups/376.html
- https://www.fema.gov/pdf/emergency/nims/nims_appendix.pdf

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §8.2 참조.

### 8.4 BPMN, CMMN, DMN

세 표준은 AI 이전부터 절차, 적응형 사례, 결정 규칙을 분리해 왔다.

| 표준 | 적합한 문제 | AI 오케스트레이션 적용 |
|---|---|---|
| BPMN | 순서와 예외를 미리 정의할 수 있는 업무 | 알려진 처리 흐름과 승인 단계 |
| CMMN | 조사, 법률, 민원처럼 진행 경로가 상황에 따라 달라지는 사례 | 에이전트가 증거를 모으며 다음 작업 선택 |
| DMN | 금액, 위험, 권한 등 명시적 결정 규칙 | LLM 밖의 정책·승인 결정표 |

재사용할 교훈:

- 명시할 수 있는 비즈니스 규칙을 프롬프트 속 자연어 판단으로 숨기지 않는다.
- 예측 가능한 업무는 프로세스 모델에 남기고, 불확실한 부분만 에이전트에 맡긴다.
- 사례 진행과 정책 결정을 분리하면 감사와 변경 관리가 쉬워진다.

출처:

- https://www.omg.org/bpmn/
- https://www.omg.org/cmmn/
- https://www.omg.org/dmn/

## 9. 사례에서 추출한 구축 방법론

### 단계 1: 실제 인간 업무를 관찰한다

에이전트 역할을 먼저 상상하지 않는다. 실제 작업자가 사용하는 입력, 산출물, 도구, 판단 기준, 예외, 승인 지점을 기록한다.

조사 항목:

- 작업을 시작하게 하는 사건은 무엇인가?
- 작업자가 처음 보는 정보는 무엇인가?
- 어떤 자료를 어떤 순서로 찾는가?
- 판단 가능한 후보를 어떻게 줄이는가?
- 완료를 무엇으로 확인하는가?
- 어떤 상황에서 다른 사람에게 넘기는가?
- 잘못 수행됐을 때 되돌릴 수 있는가?

### 단계 2: 세 가지 기준선을 만든다

동일한 평가 데이터에서 다음을 비교한다.

1. 단일 LLM 호출 또는 단일 도구 사용 에이전트
2. 고정된 단계식 워크플로
3. 동적 또는 멀티에이전트 방식

비교 지표:

- 최종 과업 성공률
- 반복 성공률
- 비용과 지연시간
- 사람 개입률
- 잘못된 외부 행동 비율
- 실패 원인 파악에 걸린 시간
- 재시도 후 복구율

### 단계 3: 역할보다 차별화된 능력을 설계한다

두 에이전트가 같은 모델, 프롬프트, 데이터와 도구를 사용하면 이름만 다른 복제본일 가능성이 높다.

전문 에이전트는 다음 중 하나 이상이 달라야 한다.

- 접근 가능한 데이터
- 사용 가능한 도구
- 평가 기준
- 모델 또는 추론 방식
- 탐색 전략
- 출력 계약
- 권한 범위

### 단계 4: 후보 생성과 실제 실행을 분리한다

특히 고위험 행동에서 다음을 구분한다.

- 조사와 증거 수집
- 후보 행동 생성
- 정책과 위험 검사
- 실행 계획 구체화
- 사람 승인 또는 자동 승인
- 실제 실행
- 사후 상태 검증

### 단계 5: 자율성을 단계적으로 확대한다

권장 도입 단계:

1. 과거 데이터 재생
2. 실제 입력을 처리하지만 결과를 사용하지 않는 shadow mode
3. 사람에게 후보와 근거만 제시
4. 사람 승인 후 실행
5. 낮은 위험·가역 작업만 자동 실행
6. 충분한 실패 데이터와 회귀 테스트가 있는 범위에서 권한 확대

### 단계 6: 실행 흔적을 평가 자료로 보존한다

각 실행에서 보존할 항목:

- 사용자 목표와 제약
- 당시 모델·프롬프트·도구 버전
- 관찰한 외부 상태
- 생성한 후보와 선택 결과
- 도구 호출과 반환값
- 승인 주체와 시점
- 실행 전후 상태
- 비용, 토큰, 지연시간
- 실패와 복구 과정

### 단계 7: 실패를 영구 회귀 테스트로 전환한다

실패가 발생하면 프롬프트만 수정하지 않는다.

1. 당시 입력과 필요한 외부 상태를 스냅샷으로 남긴다.
2. 실제 실패 조건을 재현하는 테스트를 만든다.
3. 수정 전 테스트가 실패하는지 확인한다.
4. 수정 후 해당 테스트와 기존 테스트가 모두 통과하는지 확인한다.
5. 모델·프롬프트·도구 변경 때마다 다시 실행한다.

LLM-as-a-Judge는 비용이 낮은 필터로 사용할 수 있지만 단독 품질 게이트로 사용하지 않는다. 배포된 다중 턴 거래 에이전트 연구에서도 LLM 평가기의 실제 결함 탐지 누락이 문제로 보고됐다.

- 관련 연구: https://arxiv.org/abs/2606.10315

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §9.5 참조.

## 10. 실행 기술 선택 시 참고

이 표는 제품 추천이 아니라 사례에서 관찰된 적합성 정리다.

| 상황 | 먼저 검토할 계열 | 이유 |
|---|---|---|
| 비개발자와 업무 흐름을 공동 설계 | n8n 같은 시각적 자동화 | 통합과 검토가 빠름 |
| Python 기반 데이터·ML·동적 작업 | Prefect 같은 코드 워크플로 | 동적 분기, 재시도, 관측과 기존 코드 결합 |
| 장시간 실행, 중단 후 정확한 재개 | Temporal 같은 durable execution | 상태 재생, timer, signal, activity retry |
| 미리 정의된 비즈니스 프로세스 | BPMN 엔진 | 승인·예외·업무 책임을 명시 가능 |
| 열린 문제의 동적 전문 작업 배정 | LangGraph, AutoGen 계열 또는 자체 supervisor | 런타임 작업 선택과 반복 계획 |
| 과학적 탐색과 후보 경쟁 | 비동기 작업 큐와 tournament/evolution | 후보 다양성·비교·연산시간 확장 |

Temporal은 워크플로 상태를 보존하고 실패한 활동을 재시도하며 중단 지점에서 재개하는 durable execution 방식을 제공한다. Prefect는 각 LLM·도구 호출을 개별 작업으로 관측하고 성공 결과를 캐시해 전체 재실행 비용을 줄이는 방식을 제공한다.

출처:

- https://temporal.io/
- https://www.prefect.io/blog/prefect-pydantic-integration
- https://www.prefect.io/blog/introducing-prefect-3-0

> 메커니즘과 이론적 계보는 [폭넓은 문헌조사](./ai-orchestration-broad-literature-review.md) §6.2 참조.

## 11. 후속 조사와 구현에서 피할 것

1. 역할 이름만 다르고 모델·도구·정보가 같은 에이전트를 여러 개 만드는 것
2. 모든 에이전트에게 모든 도구와 전체 대화 기록을 제공하는 것
3. 도구 호출 성공을 업무 완료로 간주하는 것
4. 단일 데모 성공을 생산 신뢰성으로 해석하는 것
5. 순차 작업을 억지로 여러 에이전트에게 분할하는 것
6. LLM 평가기만으로 배포 승인하는 것
7. 실제 실행 권한을 조사 에이전트에 직접 부여하는 것
8. 공급사 고객 사례의 성과 수치를 독립 검증된 결과로 인용하는 것
9. 프롬프트 변경과 모델 업그레이드를 버전 관리하지 않는 것
10. 실패 실행을 회귀 데이터로 보존하지 않는 것

## 12. 우선 읽을 문헌

### 생산 운영 현실

1. Pan et al.(2026). *Characterizing Agents in Production*. ICML 2026. [링크](https://icml.cc/virtual/2026/poster/61834)
   - 초기판: Pan et al.(2026). *Measuring Agents in Production*. ICLR 2026 `Agentic AI in the Wild` Workshop. [OpenReview](https://openreview.net/forum?id=AsvLggSOvS) · [arXiv](https://arxiv.org/abs/2512.04123)
2. Google AI Engineering for Reliable Operations  
   https://sre.google/resources/practices-and-processes/ai-engineering-reliable-operations/
3. Meta Engineering(2024). *Leveraging AI for efficient incident response*. Engineering at Meta. [링크](https://engineering.fb.com/2024/06/24/data-infrastructure/leveraging-ai-for-efficient-incident-response/)

### 구성 선택과 방법론

4. Kim & Liu(2026). *Towards a science of scaling agent systems: When and why agent systems work*. Google Research Blog. [링크](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)
5. Erik S. & Barry Zhang(2024). *Building effective agents*. Anthropic Engineering. [링크](https://www.anthropic.com/engineering/building-effective-agents)
6. Fourney, Bansal, Mozannar, Dibia & Amershi(2024). *Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks*. Microsoft Research Technical Article. [링크](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/)

### 소프트웨어 개발

7. Xia, Deng, Dunn & Zhang(2024). *Agentless: Demystifying LLM-based Software Engineering Agents*. arXiv:2407.01489. [링크](https://arxiv.org/abs/2407.01489)
8. Yang et al.(2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*. arXiv:2405.15793. [링크](https://arxiv.org/abs/2405.15793)
9. Hong et al.(2024). *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework*. ICLR 2024. [링크](https://arxiv.org/abs/2308.00352)
10. Qian et al.(2024). *ChatDev: Communicative Agents for Software Development*. ACL 2024. [링크](https://arxiv.org/abs/2307.07924)

### 현실 실험 검증

11. Boiko, MacKnight, Kline & Gomes(2023). *Autonomous chemical research with large language models*. Nature 624. [링크](https://www.nature.com/articles/s41586-023-06792-0)
12. Swanson et al.(2025). *The Virtual Lab of AI agents designs new SARS-CoV-2 nanobodies*. Nature 646. [링크](https://doi.org/10.1038/s41586-025-09442-9)
13. Gottweis et al.(2026). *Accelerating scientific discovery with Co-Scientist*. Nature 655. [링크](https://www.nature.com/articles/s41586-026-10644-y)

### 인접 분야

14. NASA JPL(1999). *Deep Space 1 Remote Agent*. NASA New Millennium Program. [링크](https://www.jpl.nasa.gov/nmp/ds1/tech/autora.html)
15. Kubernetes Authors(2024). *Controllers*. Kubernetes Documentation. [링크](https://kubernetes.io/docs/concepts/architecture/controller/)
16. BPMN, CMMN, DMN  
    https://www.omg.org/bpmn/  
    https://www.omg.org/cmmn/  
    https://www.omg.org/dmn/

## 13. 후속 AI 작업자를 위한 메모

이 문서를 기반으로 후속 설계나 코드 생성을 수행할 때 다음 원칙을 유지한다.

- 특정 프레임워크를 선택하기 전에 작업의 순차성, 병렬성, 도구 수, 위험도와 검증 가능성을 분류한다.
- 멀티에이전트 설계에는 반드시 단순 파이프라인 기준선을 포함한다.
- 공급사 사례와 동료 평가 결과를 같은 근거 수준으로 취급하지 않는다.
- 조사와 실행, 생성과 검증, 원하는 상태와 실제 상태를 분리한다.
- 자동화 범위보다 평가·복구·권한 경계를 먼저 문서화한다.
- 새로운 실패 사례가 발견되면 이 문서의 사례 목록과 프로젝트 회귀 테스트 목록을 함께 갱신한다.
