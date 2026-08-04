# 수정 작업 로그

- 작업일: 2026-08-03
- 수정 대상: `docs/research/ai-orchestration-broad-literature-review.md`
- 수정 전 줄 수 / 수정 후 줄 수: 1,111줄 / 1,238줄

## 완료 항목

| 항목 | 위치 | 변경 요약 | 확인한 출처 |
|---|---|---|---|
| P0-1 | 9.0 신설 | 다중 에이전트의 조건부 우위를 보고한 병렬 표본·협업 확장·토론 연구와 반대 결과를 함께 추가하고 14.6절의 동일 예산 기준으로 한계를 평가했다. | [More Agents](https://arxiv.org/abs/2402.05120), [Scaling Collaboration](https://arxiv.org/abs/2406.07155), [Du et al.](https://proceedings.mlr.press/v235/du24e.html), [Smit et al.](https://proceedings.mlr.press/v235/smit24a.html) |
| P0-2 | 9.1, 법칙 2·12, 16.7 #39 | Google 확장 연구의 논문판을 1차 출처로 올리고 블로그를 보조 출처로 바꿨다. 초기 R²=0.513과 arXiv v3의 R²=0.373/0.413, 87% 선택률을 판본별로 구분했다. | [arXiv:2512.08296](https://arxiv.org/abs/2512.08296), [Google 기술 요약](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/) |
| P0-3 | 5.3, 16.9 #68 | CIA를 수동 관찰이 아니라 블랙박스 접근자가 적대적 질의를 능동 주입하는 공격으로 정정하고 G-Designer 계열 최적화 토폴로지라는 평가 범위를 명시했다. | [CIA, ACL 2026](https://aclanthology.org/2026.acl-long.815/) |
| P0-4 | 3.2, 3.5, 16.1 #2a·2b·5a·5b | Hearsay-II를 블랙보드 계보의 원류로 보강하고 Barbara Hayes-Roth의 제어 블랙보드를 구분했다. Subsumption의 1986년 1차 출처와 LLM 적용이 설계적 유추라는 제한을 추가했다. | [Hearsay-II](https://mas.cs.umass.edu/Documents/Erman_Hearsay80.pdf), [Hayes-Roth 1985](https://www.sciencedirect.com/science/article/pii/0004370285900633), [Brooks 1986](https://doi.org/10.1109/JRA.1986.1087032) |
| P0-5 | 7.2, 16.5 #27 | MPC 서적 저자를 Wook Hyun Kwon과 Soohee Han으로 정정하고, LLM 에이전트에 직접 전이되는 부분을 후퇴 지평 원리로 한정했다. | [Springer 도서 페이지](https://link.springer.com/book/10.1007/b136204) |
| P0-6 | 7.1, 16.4 #23a·23b | 1993년 자료를 AAAI Spring Symposium 워킹노트로 정정하고 형식적 HTN 절차인 UMCP/AIPS 1994를 병기했다. | [HTN 1993](https://cdn.aaai.org/Symposia/Spring/1993/SS-93-03/SS93-03-005.pdf), [UMCP 1994](https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf) |
| P0-7 | 5.2, 16.7 #35 | SILO-BENCH PDF의 실험 규모 N={2, 5, 10, 20, 50, 100}을 확인해 최대 100개 에이전트 표현을 유지했다. | [SILO-BENCH](https://aclanthology.org/2026.acl-long.1354/), [PDF](https://aclanthology.org/2026.acl-long.1354.pdf) |
| P0-8 | 11.2, 12.2~12.4, 16.8 #45·47·48 | A2A의 Linux Foundation 기증과 다기관 TSC, OpenTelemetry GenAI schema 1.42.0, NIST 이니셔티브의 자발적·초기 산출물 성격을 반영했다. | [A2A](https://a2a-protocol.org/latest/), [OpenTelemetry](https://github.com/open-telemetry/semantic-conventions-genai), [NIST](https://www.nist.gov/artificial-intelligence/ai-agent-standards-initiative) |
| P0-9 | 11.3, 12.1, 16.8 #46 | MCP의 클라이언트 기능 Elicitation과 Skills over MCP·MCP Apps 확장을 추가하고 사람 개입 절과 상호 참조했다. | [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) |
| P1-10 | 1.3, 본문 전반, 16장 | 지정 문헌의 최종 게재지를 재확인해 근거 등급을 기계적으로 재산정하고, 주석 문헌 지도 전체를 저자·연도·제목·발표 장소·링크·등급·주석 형식으로 통일했다. | [OpenReview](https://openreview.net/), [ACL Anthology](https://aclanthology.org/), [NeurIPS Proceedings](https://proceedings.neurips.cc/), [TMLR Anthology](https://mlanthology.org/tmlr/) |
| P1-11 | 5.2 | SILO-BENCH와 MAS-BENCH의 중복 저자와 알고리즘 과제 계열을 밝혀 독립 재현으로 볼 수 없다는 제한을 추가했다. | [SILO-BENCH](https://aclanthology.org/2026.acl-long.1354/), [MAS-BENCH](https://aclanthology.org/2026.findings-acl.1698/) |
| P1-12 | 5.2, 법칙 3 | MAS-BENCH의 경량 완화책 CAMOC와 공유 상태 상호작용에서 가장 큰 이득을 본 결과를 추가했다. | [MAS-BENCH](https://aclanthology.org/2026.findings-acl.1698/) |
| P1-13 | 5.1, 7.4, 10장, 11.3 | 무출처 종합을 저자의 종합으로 표시하고 토폴로지·시장 기반 조정·실패 분류에 대표 근거를 연결했다. | [Smith 1980](https://www.eecs.ucf.edu/~lboloni/Teaching/EEL6788_2008/papers/The_Contract_Net_Protocol_Dec-1980.pdf), [Gerkey & Matarić](https://ai.stanford.edu/~gerkey/research/mrta.html), [Vickrey 1961](https://doi.org/10.1111/j.1540-6261.1961.tb02789.x) |
| P1-14 | 8.4, 15.5 | N_eff 결과를 RMET/MRMET 강제 선택형 감정 인식 과제로 한정하고 사람+AI 혼합 집계가 양쪽 단독보다 좋았다는 결과를 추가했다. | [Scientific Reports 2026](https://www.nature.com/articles/s41598-026-45331-5) |
| P1-15 | 9.5, 16.9 #67 | Judge가 체계적 문제 9개 중 2개만 판별하고 운영 게이트가 100라운드 중 0건을 표시한 수치와 턴 내부·턴 간 상태 오류 차이를 반영했다. | [arXiv:2606.10315](https://arxiv.org/abs/2606.10315) |
| P1-16 | 6.1 | 이벤트 소싱의 효과를 재현이 아니라 감사·인과 추적·부분 재실행으로 정정하고 seed·모델 버전·도구 응답 스냅샷 조건을 추가했다. | [Event Sourcing](https://www.martinfowler.com/eaaDev/EventSourcing.html) |
| P1-17 | 법칙 9, 15.3 | 동적 확장·축소에는 직접 통제 실험이 부족하다고 명시하고 연구 공백 절과 연결했다. | [AMAS](https://aclanthology.org/2025.emnlp-industry.144/), [FEMA ICS](https://emilms.fema.gov/_is0200c/groups/376.html) |
| P1-18 | 4.4·4.9, 6.7, 7.3·7.4, 11.3, 12.4, 14.3, 15.2·15.5, 16.9 | 모델 라우팅, 분산 합의·CRDT, 자동화 편향, 메커니즘 디자인, 메모리 관리, 큐잉 이론, EU AI Act와 ISO/IEC 42001 문헌을 추가하고 각 전이 한계를 명시했다. | [FrugalGPT](https://mlanthology.org/tmlr/2024/chen2024tmlr-frugalgpt/), [RouteLLM](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html), [FLP](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf), [Raft](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro), [CRDT](https://www.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf), [EU AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689), [ISO/IEC 42001](https://www.iso.org/standard/42001) |
| P2-19 | 문서 상단 | 장과 주요 절을 포함한 2단계 목차를 추가했다. | 해당 없음(문서 구조 편집) |
| P2-20 | 13장, 14.7, 이후 장 번호 | 기존 오해 장을 각 법칙의 `흔한 오해`로 흡수하고 분석 질문 장을 14.7 체크리스트로 병합한 뒤 장 번호와 참조를 재정렬했다. | 해당 없음(문서 구조 편집) |
| P2-21 | 초록, 3.2, 8.4 및 상호 참조 | 상태 저장소와 상관 다양성 명제를 지정 절에서만 근거와 함께 완전 서술하고 나머지는 요약 또는 상호 참조로 바꿨다. | 해당 없음(중복 편집) |
| P2-22 | 3장 Mermaid | 각 역사적 계보에서 전이된 상태·제어·실패 처리·독립성·자원 배분을 엣지 라벨로 표시했다. | 해당 없음(도식 편집) |
| P2-23 | 4.6·4.8, 6.2·6.4, 7.5, 8.2, 9.1·9.2 | 두 문서에 겹치는 9개 사례마다 운영 수치와 상세 사례를 보조 문서에서 읽도록 절 수준 단방향 링크를 추가했다. | [실용 사례와 구축 방법론](../research/ai-orchestration-practical-cases-and-methods.md) |

## 미완료 또는 보류 항목

| 항목 | 이유 | 필요한 후속 조치 |
|---|---|---|
| 없음 | P0 9건, P1 9건, P2 5건을 모두 반영했다. | 없음 |

## 웹으로 확인한 사실

| 확인 대상 | URL | 확인 결과 |
|---|---|---|
| Google 확장 연구 판본 | https://arxiv.org/abs/2512.08296 | 논문판의 존재와 v3의 260개 구성, R²=0.373/0.413, 87% 선택률을 확인했다. 초기 기술 요약의 R²=0.513과 판본을 구분했다. |
| 다중 에이전트 우위·반론 | https://arxiv.org/abs/2402.05120 | TMLR 게재와 병렬 표본·투표 실험을 확인했다. |
| 협업 확장 연구 | https://arxiv.org/abs/2406.07155 | ICLR 2025 게재와 1,000개 이상 규모의 MacNet 실험을 확인했다. |
| MPC 서적 | https://link.springer.com/book/10.1007/b136204 | 저자가 Wook Hyun Kwon과 Soohee Han임을 확인했다. |
| CIA 위협 모델 | https://aclanthology.org/2026.acl-long.815/ | 능동 적대 질의를 사용하는 블랙박스 공격이며 최적화된 통신 토폴로지를 평가함을 확인했다. |
| SILO-BENCH 규모 | https://aclanthology.org/2026.acl-long.1354.pdf | 평가 규모가 N={2, 5, 10, 20, 50, 100}임을 확인했다. |
| Hearsay-II와 Subsumption 계보 | https://mas.cs.umass.edu/Documents/Erman_Hearsay80.pdf | Hearsay-II의 저자·발표지와 Brooks 1986의 1차 출처를 각각 확인했다. |
| HTN 발표 장소 | https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf | 1993년 워킹노트와 AIPS 1994 UMCP의 발표 장소를 구분했다. |
| MCP·A2A·OpenTelemetry·NIST 현행 상태 | https://modelcontextprotocol.io/specification/2026-07-28 | 조사 기준일의 기능·거버넌스·스키마·자발적 지침 성격을 각 공식 페이지에서 확인했다. |
| 새로 추가한 인접 분야 문헌 | https://eur-lex.europa.eu/eli/reg/2024/1689 | 논문·법령·표준의 저자 또는 발행 주체, 연도, 발표 장소와 식별자를 각 1차·공식 페이지에서 확인했다. |

## 확인하지 못한 항목

이번 수정에서 새로 추가하거나 서지 상태를 변경한 문헌 중 `검증 불가`로 남긴 항목은 없다. 기존 문헌 전체의 원문 결과를 재현한 것은 아니며, 이번 지시에서 요구한 서지 사실과 수정 주장만 확인했다.

## 상호 참조 검증 결과

- 장 번호 재정렬 후 깨진 참조: 없음. 1장부터 17장까지 순차성을 확인했고 `N장`, `N.M절`, `§N.M` 표기를 실제 제목과 대조했다.
- 내부 앵커 링크: 목차 링크 29개가 모두 실제 제목에서 생성되는 앵커와 대응함을 확인했다.
- 외부 링크 개수 및 형식 통일 여부: Markdown 외부 링크 155개를 확인했다. 주석 문헌 지도 72개 항목(2a·2b·5a·5b·23a·23b 포함)은 모두 정식 서지 형식과 근거 등급을 갖는다.
- Markdown 구조: 제목 114개, 코드 펜스 2개(짝 일치), `git diff --no-index --check` 기준 공백 오류 없음.
- diff 검토: 저장소에 최초 커밋이 없어 일반 `git diff` 기준선은 없었다. 전체 문서를 신규 파일 기준으로 검사하고, 통합 대상 6개 오해와 기존 6개 소제목의 질문 내용이 각각 13장과 14.7절에 보존됐는지 확인했다.
- 보호 파일 무결성: 심사 보고서 SHA-256 `32824BD1D8D8EF552EAEBD59C58E6B256B7CF3A3CDE9C7A8D1E5832DC290A874`, 실용 문서 SHA-256 `41766BA96D98149C4B8D33DB6D331227D7CED231004E868F881CC261A2C868AE`로 작업 전 값과 동일하다.

## 2차 검증 (링크·서지 전수 점검)

### 점검 범위

- 점검일: 2026-08-03.
- 현재 파일에서 정규식으로 다시 센 주석 문헌 지도는 **72개 항목**이다. 접미 번호 `2a·2b·5a·5b·23a·23b`를 각각 한 항목으로 셌다. 참고문헌에 든 URL은 **73개**이며, #39가 논문과 기술 요약 URL을 함께 가진다.
- 본문을 포함한 문서 전체의 **고유 외부 URL은 82개**다. 작업 지시의 명목 수치 84개와 달라서 84개로 간주하지 않았다. PowerShell 정규식 추출 결과를 중복 제거한 뒤 `curl -L`의 실제 HTTP GET(1 KiB 범위 요청, 30초 제한)으로 **82개를 모두 열었고, 미확인 URL은 0개**다. 수정 도중 바뀐 URL은 교체 후 주소를 다시 GET했다.
- 각 URL의 최초 주소·HTTP 상태·리다이렉트 최종 주소를 기록했다. 공식성은 도메인과 문헌 유형을 대조했다. 학회·저널은 공식 프로시딩/출판사/DOI, 사전출판물은 arXiv를 기준으로 삼았고, 지시에서 예외로 든 기관·프로젝트·기업의 원자료는 그대로 인정했다.
- 본문과 참고문헌은 URL을 키로 대조했다. 72개 중 **67개는 본문 인라인 인용과 연결**되며, 정식 제목 문자열이 본문에도 존재하는지 검사했다. #8·#9·#10·#49·#50은 참고문헌 지도에만 있어 본문과 대조할 인라인 짝이 없다. 이 5개는 링크 공식성·생존 상태만 확인했다.
- 근거 등급은 문헌 유형 및 게재 상태가 바뀐 #40·#42를 원문 게재처 기준으로 재판정했다. 나머지는 본문과 참고문헌의 등급 문자열이 충돌하지 않는지 대조했으며, 개별 논문의 실험 결과를 전부 재현한 것은 아니다.

### 교체한 링크

| 번호 | 문헌 | 기존 URL | 교체 URL | 교체 사유 |
|---|---|---|---|---|
| #1 | Contract Net Protocol | https://www.eecs.ucf.edu/~lboloni/Teaching/EEL6788_2008/papers/The_Contract_Net_Protocol_Dec-1980.pdf | https://ieeexplore.ieee.org/document/1675516 | 대학 강의용 PDF 사본에서 IEEE 공식 게재 페이지로 교체 |
| #2a | Hearsay-II | https://mas.cs.umass.edu/Documents/Erman_Hearsay80.pdf | https://doi.org/10.1145/356810.356816 | 대학 자료실 PDF 사본에서 ACM 공식 DOI로 교체 |
| #23b | UMCP | https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf | https://cdn.aaai.org/AIPS/1994/AIPS94-042.pdf | 저자 소속 대학 사본에서 AAAI 공식 프로시딩 PDF로 교체 |
| 본문 8.2 | Team Implicit Coordination Based on Transactive Memory Systems | https://www.sciencedirect.com/org/science/article/pii/S1352759220000123 | https://doi.org/10.1108/TPM-03-2020-0024 | ScienceDirect의 타 출판사 색인에서 Emerald 공식 DOI로 교체 |
| #40 | Measuring Agents in Production | https://arxiv.org/abs/2512.04123 | https://openreview.net/forum?id=AsvLggSOvS | 최종 확인된 ICLR 2026 Agentic AI in the Wild 워크숍 공식 페이지로 교체 |
| #42 | τ-bench | https://arxiv.org/abs/2406.12045 | https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html | arXiv 사전출판물에서 ICLR 2025 공식 프로시딩으로 교체 |
| 본문 9.3 | AgentBench | https://arxiv.org/abs/2308.03688 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html | arXiv에서 ICLR 2024 공식 프로시딩으로 교체 |
| 본문 9.3 | GAIA | https://arxiv.org/abs/2311.12983 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/25ae35b5b1738d80f1f03a8713e405ec-Abstract-Conference.html | arXiv에서 ICLR 2024 공식 프로시딩으로 교체 |
| 본문 9.3 | AgentBoard | https://arxiv.org/abs/2401.13178 | https://proceedings.neurips.cc/paper_files/paper/2024/hash/877b40688e330a0e2a3fc24084208dfa-Abstract-Datasets_and_Benchmarks_Track.html | arXiv에서 NeurIPS 2024 공식 프로시딩으로 교체 |
| 본문 9.3 | TheAgentCompany | https://arxiv.org/abs/2412.14161 | https://proceedings.neurips.cc/paper_files/paper/2025/hash/0d744742f6fac4d1134c019b7cef3c8a-Abstract-Datasets_and_Benchmarks_Track.html | arXiv에서 NeurIPS 2025 공식 프로시딩으로 교체 |
| #53 | More Agents Is All You Need | https://arxiv.org/abs/2402.05120 | https://openreview.net/forum?id=bgzUSZ8aeg | arXiv에서 TMLR 공식 게재 페이지로 교체 |
| #54 | Scaling Large Language Model-based Multi-Agent Collaboration | https://arxiv.org/abs/2406.07155 | https://proceedings.iclr.cc/paper_files/paper/2025/hash/66a026c0d17040889b50f0dfa650e5e0-Abstract-Conference.html | arXiv에서 ICLR 2025 공식 프로시딩으로 교체 |
| #57 | FLP | https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf | https://doi.org/10.1145/3149.214121 | 대학 연구실 PDF 사본에서 ACM 공식 DOI로 교체 |
| #59 | CRDT | https://www.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf | https://doi.org/10.1007/978-3-642-24550-3_29 | 저자·대학 PDF 사본에서 Springer 공식 DOI로 교체 |

사용자가 먼저 반영한 FrugalGPT와 AI Agents That Matter의 OpenReview 링크, RouteLLM의 `from Preference Data` 제목은 현재 파일에서 그대로 유지했으며 다시 수정하지 않았다.

### 서지 불일치 정정

| 번호 | 문헌 | 불일치 내용 | 어느 쪽이 틀렸는가 | 정정 결과 |
|---|---|---|---|---|
| #16 | MetaGPT | 정식 제목의 `A Multi-Agent`에서 `A`가 빠져 있었다. | 본문과 참고문헌 모두 불완전 | 양쪽을 *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework*로 통일 |
| #29 | Transactive Memory System Links Work Team Characteristics and Performance | 본문 링크 라벨은 Lewis의 문헌처럼 적혀 있었으나 URL과 참고문헌은 Zhang et al.(2007)이었다. | 본문 | 본문을 Zhang, Hempel, Han & Tjosvold의 정식 서지로 교체 |
| #40 | Measuring Agents in Production | `ICML 2026 oral`로 적혀 있었으나 공식 페이지는 ICLR 2026 Agentic AI in the Wild 워크숍 포스터다. | 본문과 참고문헌 모두 | 발표 장소와 링크를 워크숍 포스터/OpenReview로 통일 |
| #42 | τ-bench | 참고문헌이 2024년 arXiv·근거 B에 머물렀고 본문도 사전출판물 링크를 사용했다. | 참고문헌의 연도·장소·등급과 본문 링크 | ICLR 2025·근거 A·공식 프로시딩으로 통일 |
| #56 | Should We Be Going MAD? | 본문 제목의 대문자 표기가 참고문헌·공식 제목과 달랐다. | 본문 표기 | 공식 제목의 대문자 표기로 통일 |
| #63 | MemGPT | 2024년으로만 적어 최초 제출 연도와 개정 연도를 구분하지 않았다. | 본문과 참고문헌 모두 불완전 | `2023; rev. 2024`로 통일 |
| #1·#2a·#7·#25·#31–#38·#43·#46·#48·#61·#65–#69 | 인라인 인용 축약 표기 | 정식 제목 일부, 저자 또는 발표 장소가 생략되거나 대소문자·구두점이 달랐다. 사실관계의 반대는 아니지만 문자열 전수 대조에서 차이로 검출됐다. | 본문 인라인 표기 | 참고문헌의 정식 제목을 본문에도 넣고 저자·연도·발표 장소·근거 등급을 충돌 없이 맞춤 |

### 링크 상태

| 상태 | 개수 | 해당 항목 |
|---|---:|---|
| 정상 | 57 | `curl -L` GET 결과 2xx이고 공식 문서 또는 예상한 공식 리다이렉트에 도달한 URL. 아래 접근제한·깨짐 항목을 제외한 57개 |
| 페이월·접근제한 | 24 | HTTP 403/400: #2a·#2b·#3·#5b·#28·#57·#62·#64 및 본문 8.2의 Nawata et al.; OpenReview 브라우저 확인 챌린지: #6·#11·#15·#18·#40·#41·#51·#53; 쿠키 제한 페이지로 리다이렉트: #27·#31·#32·#33·#34·#59·#61. DOI 또는 공식 URL 자체는 살아 있는 것으로 판정 |
| 깨짐 | 1 | OpenTelemetry GenAI 스키마 식별자 `https://opentelemetry.io/schemas/gen-ai/1.42.0` — 공식 저장소가 이 식별자를 선언하지만 HTTP GET은 404. 본문에 탐색용 문서 링크가 아니라 식별자라고 명시 |
| 미확인 | 0 | 현재 파일에서 추출한 고유 외부 URL 82개를 모두 GET함 |

HTTP 206은 Range 요청에 대한 정상 부분 응답으로 처리했다. DOI가 해당 출판사 문서로 이동한 경우, 동일 DOI의 공식 랜딩임을 확인하고 다른 문서로 잘못 이동한 것으로 세지 않았다. OpenReview의 HTTP 200은 최종 URL이 논문 페이지가 아니라 `/challenge`였으므로 정상으로 세지 않았다.

### 1차 보고의 정확하지 않았던 부분

1차 검증은 새로 추가하거나 변경한 문헌의 실재 여부와 일부 서지 사실, Markdown 구조에 집중했고, 모든 외부 URL에 대해 공식 게재처 도메인·리다이렉트 최종 주소·HTTP GET을 확인하는 절차와 본문/참고문헌의 필드별 전수 대조를 수행하지 않았다. 그 결과 제3자·대학 PDF 링크와 제목 불일치를 놓쳤는데도 `확인하지 못한 항목 없음`이라고 범위를 넓게 표현했다. 2차에서는 URL 정적 추출, 실제 GET, 공식 도메인 판정, URL 기반 본문/참고문헌 매핑을 별도 단계로 나눴다.

## 보조 문서 동결

### 작업 범위와 상태

- 작업일: 2026-08-03.
- 수정 대상: `docs/research/ai-orchestration-practical-cases-and-methods.md`와 이 작업 로그뿐이다.
- 작업 전 보조 문서: 772줄, SHA-256 `41766BA96D98149C4B8D33DB6D331227D7CED231004E868F881CC261A2C868AE`.
- 작업 후 보조 문서: 787줄, SHA-256 `A6328DC9F02D77709B27B8F2FA07870F8A3DED68AD602F9FE0DA0A584F2EEF6A`.
- 지정된 동결 헤더, 판본 오류 1건, 중복 사례 참조 8개, §12 서지 보강 외에는 사례·수치·구조를 고치지 않았다. 이 작업 완료 후 보조 문서는 다시 수정 금지 대상으로 둔다.

### 작업 1. 확인된 사실 오류 정정

- 완료.
- §1의 `Measuring Agents in Production` 단일 판본 서술을 다음처럼 구분했다.
  - 확장판 `Characterizing Agents in Production`: ICML 2026 본회의, 실무자 306명.
  - 초기판 `Measuring Agents in Production`: ICLR 2026 `Agentic AI in the Wild` 워크숍, 실무자 86명, OpenReview와 arXiv를 함께 표시.
  - 두 판본에 공통인 20개 심층 사례, 26개 도메인, 68%·70%·74%, 신뢰성이 최대 과제라는 내용은 유지했다.
- §12의 1번 항목도 확장판을 1차 인용으로 두고 초기판을 별도로 병기했다.

### 작업 2. 동결 상태 헤더

- 완료. 문서 제목 아래 기존 메타 정보 다음에 상태·검증 수준·서지 형식·주 문서와의 관계·갱신 정책을 추가했다.
- 검증 수준 문구 전문:

> **검증 수준:** 이 문서는 동료 심사와 링크 전수 점검을 거치지 않았다. 본문의 사실·수치 가운데 아래 §1과 §12에 반영한 `Measuring Agents in Production`·`Characterizing Agents in Production` 판본 구분 1건만 원문 대조로 확인됐다.

### 작업 3. 주 문서와의 중복 항목 표시

- 완료. 작업 전 두 문서의 고유 URL 교집합을 정적 추출했을 때 정확히 8개였다. 작업 1에서 ICML·OpenReview 공식 URL이 보조 문서에 추가됐지만 이는 새로운 사례가 아니라 기존 생산 에이전트 조사 사례의 판본 링크다.

| 보조 문서 위치 | 중복 사례 | 주 문서 참조 |
|---|---|---|
| §1 | Measuring/Characterizing Agents in Production | §9.2 |
| §6.1 | Magentic-One | §4.8 |
| §7 | Towards a Science of Scaling Agent Systems | §9.1 |
| §8.1 | NASA Deep Space 1 Remote Agent | §7.5 |
| §8.2 | Kubernetes Controllers | §6.4 |
| §8.3 | FEMA Incident Command System | §8.2 |
| §9 단계 7 | Catching One in Five | §9.5 |
| §10 | Temporal Durable Execution | §6.2 |

각 위치에는 `메커니즘과 이론적 계보는 폭넓은 문헌조사 §N 참조` 형식의 단방향 링크 한 줄만 추가했다. 주 문서에는 역방향 링크를 추가하지 않았다.

### 작업 4. §12 참고문헌 서지 보강

- 수행함. 16개 항목 중 **14개**를 공식 원문에서 저자 또는 발행 주체·연도·정식 제목·발표 장소를 확인한 뒤 `저자(연도). 제목. 발표 장소. [링크]` 형식으로 바꿨다.
- 원문 확인 후 보강한 항목: #1, #3–#15.
- 확인 불가로 원형을 유지한 항목: **2개**.
  - #2 Google SRE 자료: 공식 페이지에서 저자와 정식 제목은 확인했지만 발행 연도를 확인할 수 없어 기존 제목·URL 형식을 유지했다.
  - #16 BPMN·CMMN·DMN: 서로 다른 세 표준을 하나로 묶은 항목이며 각 사양의 단일 저자·연도·발표 장소로 통일할 수 없어 기존 제목·URL 형식을 유지했다.
- 본문 인라인 링크는 작업 1의 판본 정정과 작업 3의 참조 추가 외에는 교체하지 않았다. §12 밖의 기존 링크는 링크 점검·교체 대상으로 삼지 않았다.

### 확인한 것과 확인하지 않은 것

**확인한 것**

- 작업 전 주 문서와 보조 문서를 현재 디스크 기준으로 처음부터 끝까지 다시 읽었다.
- 중복 URL 8개를 정규식 추출과 집합 교집합으로 확인했고, 보조 문서에 단방향 참조가 정확히 8줄 존재하는지 검사했다.
- §12에서 바꾼 14개 항목은 각 공식 학회·출판사·기관·기업 페이지 또는 arXiv 원문에서 서지 필드를 확인했다.
- 보조 문서의 제목·주요 장 구조는 유지했고 코드 펜스 불균형은 없다.

**확인하지 않은 것**

- 보조 문서 전체는 동료 심사, 링크 전수 점검, 전체 수치 재검증을 수행하지 않았다.
- §12의 #2와 #16은 완전한 서지 형식으로 확인하지 못해 바꾸지 않았다.
- 지정된 판본 오류 1건 외의 본문 주장·수치는 검증하거나 수정하지 않았다.

### 보호 파일 무결성

| 파일 | 작업 전 줄 수·SHA-256 | 작업 후 결과 |
|---|---|---|
| `ai-orchestration-broad-literature-review.md` | 1,242줄 · `912A4A2C0B6F53B04A3404929D3B7A81F970E1FAC7DBA36C3565351FC492A89F` | 동일 |
| `claude-review-ai-orchestration-broad-literature-review.md` | 460줄 · `32824BD1D8D8EF552EAEBD59C58E6B256B7CF3A3CDE9C7A8D1E5832DC290A874` | 동일 |
| `codex-revision-prompt.md` | 333줄 · `49FF360EF555D947906C49BC96010C0256F783E6C9C40D7D2654347D567B1695` | 동일 |

## 집 PC 작업 인수인계

### 작업 범위

- 작업일: 2026-08-03.
- 새 문서 `docs/operations/home-codex-handoff.md`를 작성했다.
- 목적은 집 PC의 새 Codex 작업에 연구 결과와 목표를 전달하고, 범용 Codex 세션 오케스트레이터의 설계 작업을 이어가는 것이다.
- EU4 전용 세션 컨트롤러는 참고 사례 하나로만 기록하고 범용 설계의 기반이나 고정 역할 구조로 두지 않았다.
- 개별 파일 설명보다 범용 폴더 책임, 실행별 상태, 세션 수명 주기, 통신 구조와 다음 설계 범위를 중심으로 정리했다.
- 집 PC에서 그대로 전달할 시작 프롬프트를 인수인계 문서 9절에 포함했다.

### 생성 결과

- `docs/operations/home-codex-handoff.md`: 263줄.
- 작성 직후 SHA-256: `C3CB9A44419E91634B1B4F671820534449E66A0E50EDE88A726D5D0FCBE05A07`.
- 범용 오케스트레이터의 구현은 아직 시작하지 않았다. 다음 세션은 문헌 결론을 구현 요구사항으로 변환하고 범용 코어와 프로젝트 전용 구성의 경계를 설계하는 단계부터 시작한다.

### 확인한 것과 확인하지 않은 것

**확인한 것**

- 인수인계 작성 전 현재 저장소가 `main` 브랜치이고 작업 트리가 깨끗한 것을 확인했다.
- 기존 커밋 `799ac34`, `2510aa2`를 확인했다.
- 작성 시작 시 등록된 Git 원격 저장소가 없음을 `git remote`와 `remote.*` 설정 조회로 확인했다.
- 별도 저장소 `C:\Users\SSAFY\Documents\이어서 작업`의 폴더 구조, 세션 운영 문서, 컨트롤러 구조, 테스트 목록과 현재 이식성 문제를 읽기 전용으로 표본 확인했다.

**확인하지 않은 것**

- 별도 EU4 저장소의 세션 컨트롤러는 이전 절대경로를 가리키고 전용 Python 런타임이 없어 실제 세션 실행과 전체 테스트를 수행하지 않았다.
- 범용 오케스트레이터의 구현 언어, 세부 저장 스키마와 Codex 런타임 인터페이스는 아직 확정하지 않았다.
- Git 원격 저장소가 없어 인수인계 작성 시점에는 push 대상을 확인하지 못했다.

### 보호 문서 무결성

인수인계 문서와 이 로그 외에는 수정하지 않았다.

| 파일 | 줄 수 | SHA-256 |
|---|---:|---|
| `ai-orchestration-broad-literature-review.md` | 1,242 | `912A4A2C0B6F53B04A3404929D3B7A81F970E1FAC7DBA36C3565351FC492A89F` |
| `ai-orchestration-practical-cases-and-methods.md` | 787 | `A6328DC9F02D77709B27B8F2FA07870F8A3DED68AD602F9FE0DA0A584F2EEF6A` |
| `claude-review-ai-orchestration-broad-literature-review.md` | 460 | `32824BD1D8D8EF552EAEBD59C58E6B256B7CF3A3CDE9C7A8D1E5832DC290A874` |
| `claude-review-prompt.md` | 232 | `A2C8790211FA778B84A042E8C9079705BEFB4E406B1E1B2DD2F51050E826C67C` |

## Fork 기반 구조 독립 심사 프롬프트

- 작업일: 2026-08-04.
- 새 문서 `docs/archive/fork-based/claude-review-prompt-fork-based-session-orchestrator.md`를 작성했다.
- 목적은 “하나의 범용 엔진이 여러 프로젝트를 등록·관리한다”는 이전 가정을 배제하고, 검증된 범용 원본에서 프로젝트별 전용 오케스트레이터가 fork·복사되어 나오는 구조를 클로드에게 설명받고 독립 평가받는 것이다.
- 클로드에게 구조 재설명, 전체 Git fork·template·공용 core package·plugin·멀티프로젝트 플랫폼 비교, fork drift와 upstream 병합 비용, 팀·세션 수명, 통신, 검증, 성능 기준선과 MVP를 검토하도록 요구했다.
- 심사는 읽기 전용으로 지정했으며 구현이나 파일 수정을 요청하지 않았다.
- 프롬프트는 154줄이며 작성 직후 SHA-256은 `D7FC5DEDE40E54425E352BFD58B74E274D6CD7522102A33AE04D35F25E5844A2`다.
- 기존 문헌조사, 동결 문서, 기존 심사 프롬프트와 인수인계 문서는 수정하지 않았다.

## 범용 로컬 세션 오케스트레이터 설계

### 작업 범위

- 작업일: 2026-08-04.
- 새 문서 `docs/design/general-local-session-orchestrator-design.md`를 작성했다.
- 구현은 수행하지 않았다. 설계 문서만 작성했다.
- 검증 문헌, `C:\Users\SSAFY\Documents\이어서 작업`의 schema v1 코드·운영 문서·0-3/0-4 실행 기록, 사용자 제공 schema v2 복원 자료, Claude의 fork 구조 심사, 현재 Codex 공식 문서를 근거 수준별로 구분해 종합했다.

### 설계 결과

- 범용 원본 저장소와 실제 프로젝트 저장소를 서로 독립시켰다. 범용 저장소 아래에 프로젝트를 넣지 않는다.
- 프로젝트가 검증된 코어 버전과 `.orchestrator/` 프로젝트 팩을 채택하는 구조를 기본으로 하고, 코어 전체 fork는 확장 경계가 실제로 부족할 때의 탈출구로 두었다.
- 고정 `P1·P2·P3·V1·R1` 대신 `Run → Task → Attempt → Session` 실행 계층과 작업 단위 Worker·조건부 Reviewer를 설계했다.
- AI 세션은 의미 해석과 산출물 생성을 맡고, 일반 코드는 상태·권한·예산·충돌·검증·재시도·종료를 맡도록 경계를 정했다.
- 초기 상태 정본은 SQLite 원장과 append-only Event 테이블로 정했다. schema v2의 완전한 JSONL event sourcing은 필요성 검증 전에는 채택하지 않았다.
- 공유 작업장 쓰기는 기본 직렬, 읽기 중심 독립 작업만 기본 병렬, worktree 병렬 쓰기는 실측 뒤 여는 단계적 정책으로 설계했다.
- 범용 원본을 별도 코드·조사 기준 저장소에서 비교 검증한 뒤 실제 프로젝트가 채택하는 순서를 명시했다.

### 생성 결과

- `docs/design/general-local-session-orchestrator-design.md`: 1,028줄.
- 작성·검사 직후 SHA-256: `0102C2F6B520EDFB5C14E8C21FA63C0D71DF9A831B6952A35D24F83680E388C0`.
- Markdown 코드 펜스 30개가 짝을 이루며, 상대 링크 2개가 모두 실제 문서를 가리키는 것을 확인했다.

### 확인한 것과 확인하지 않은 것

**확인한 것**

- 주 문헌조사의 정의, 통신·분산시스템·실증·실패·설계 법칙·평가 절을 읽었다.
- 동결 보조 문서의 결론, 동적 오케스트레이션 사례, 정량 결과, 구축 방법론을 읽었다.
- `이어서 작업`의 `AGENTS.md`, v1 config·contract schema, controller 함수 구조, 시험 목록, 병렬 정책, Brain 인수인계와 사용자 제공 실행 복원 자료를 읽었다.
- 공식 Codex 문서에서 SDK의 thread 시작·재개, Python app-server 제어, turn별 sandbox, subagent, worktree, AGENTS.md, 인증·가격 경계를 확인했다.

**확인하지 않은 것**

- 설계의 코드는 생성·실행·시험하지 않았다.
- schema v2는 복원 자료대로 구현·시험 0건이며 이 작업에서도 구현된 것으로 취급하지 않았다.
- Codex SDK 프로그램 실행이 현재 로컬 ChatGPT 로그인에서 실제로 어느 사용량 한도에 기록되는지는 통제 실행하지 않았다.
- SQLite, JSONL event sourcing, 새 thread, 재사용 thread, worktree를 동일 과제로 비교하지 않았다.
- EU4 외 프로젝트에서 범용성을 실행 검증하지 않았다.

### 보호 문서 무결성

| 파일 | 줄 수 | SHA-256 |
|---|---:|---|
| `ai-orchestration-broad-literature-review.md` | 1,242 | `912A4A2C0B6F53B04A3404929D3B7A81F970E1FAC7DBA36C3565351FC492A89F` |
| `ai-orchestration-practical-cases-and-methods.md` | 787 | `A6328DC9F02D77709B27B8F2FA07870F8A3DED68AD602F9FE0DA0A584F2EEF6A` |
| `claude-review-ai-orchestration-broad-literature-review.md` | 460 | `32824BD1D8D8EF552EAEBD59C58E6B256B7CF3A3CDE9C7A8D1E5832DC290A874` |
| `claude-review-prompt.md` | 232 | `A2C8790211FA778B84A042E8C9079705BEFB4E406B1E1B2DD2F51050E826C67C` |

위 네 파일은 작업 전후 SHA-256이 동일하다. 기존 미커밋 심사 문서 두 개와 이 로그의 선행 미커밋 내용도 되돌리거나 덮어쓰지 않았다.

## 범용 설계 Claude 심사 프롬프트

- 작업일: 2026-08-04.
- 새 문서 `docs/prompts/general-design/claude-review-prompt-general-local-session-orchestrator-design.md`를 작성했다.
- 현재 사용자 상황, EU4 schema v1의 실제 구현·0-3/0-4 실행 경험, schema v2의 미구현 상태, 범용 원본 선검증과 프로젝트 독립성 요구를 심사 배경으로 요약했다.
- Claude에게 맥락을 가장 강하게 이해하는 심사와 역사·매몰비용을 정당화 근거로 인정하지 않는 맥락 비의존 심사를 분리해 수행하도록 했다.
- 기존 Codex 기능만으로 충분한지, 프로젝트를 만들지 않는 편이 나은지, clean-room 대안이 무엇인지까지 검토하도록 했다.
- 심사 대상 문서와 기존 자료는 읽기 전용으로 고정하고, 결과는 `docs/reviews/general-design/claude-review-general-local-session-orchestrator-design.md` 새 파일 하나에만 저장하도록 했다.
- 프롬프트는 389줄이며 SHA-256은 `7F6B301041059659E61CE5F10677D675B9E38816821673E8A1AEDBC7F6773A6F`다.
- Markdown 코드 펜스 4개가 짝을 이루고 trailing whitespace가 없음을 확인했다.

## 범용 설계 Claude 심사 확인 보고

- 작업일: 2026-08-04.
- Claude의 701줄 심사 보고서와 범용 설계 문서를 대조하고, 주요 P0·P1 근거를 Codex 공식 문서와 기존 v1 코드로 재확인했다.
- 새 문서 `docs/reviews/general-design/codex-response-to-claude-review-general-local-session-orchestrator-design.md`를 작성했다.
- 심사 14건 중 10건은 그대로 수용하고, 인증 경계·실제 프로젝트 검증 순서·Worktree 경계·SDK `interrupt()` 증거 수준 4건은 취지를 수용하되 근거 또는 적용 순서를 정정해 재검토하도록 요청했다.
- 현재 Codex 공식 문서상 Worktree root는 Settings에서 변경할 수 있으므로 심사의 “생성 위치 지정 불가” 근거를 사실 오류로 기록했다.
- `openai-codex==0.144.4`를 사용한 기존 v1의 `turn.interrupt()` 코드와 usage 테스트를 확인해, 완전 미확인이 아니라 “고정 베타 버전 로컬 증거 있음 / 현재 공개 계약 미확인”으로 구분했다.
- 가설 7은 B1 코드 없이 검증할 수 없으므로 `가설 1 → B1 최소 실험판 → 가설 7 → 전체 확장` 순서로 재정의하도록 요청했다.
- 원래 설계 문서는 1,028줄, 원래 심사 보고서는 701줄임을 확인했다. 두 파일은 수정하지 않았다.

## 범용 로컬 세션 오케스트레이터 설계 동결

### 작업 범위

- 작업일: 2026-08-04.
- 사용자 지시에 따라 `docs/design/general-local-session-orchestrator-design.md`에 Claude 원심과 Claude·Codex 교차 재검토의 합의사항을 반영하고 설계를 동결했다.
- 구현, 패키지 설치, SDK 통제 실행, 성능 시험은 수행하지 않았다.
- 원래 설계는 1,028줄, SHA-256 `0102C2F6B520EDFB5C14E8C21FA63C0D71DF9A831B6952A35D24F83680E388C0`였다.
- 동결 설계는 1,088줄, 52,111바이트, SHA-256 `F1722A3344F69EF9B85DF3FBF280F9B1BE027D3EAFFA20CDE4BC8AF816A102F3`다.

### 반영한 설계 지적

- P0: ChatGPT 로그인 SDK 실행의 지원·한도·과금 미확인을 분리하고 `auth_method`를 Run에 추가했다. 실제 프로젝트를 범용 코어의 종속 대상이 아닌 외부 pilot/fixture로 release candidate 전에 검증하도록 순서를 고쳤다.
- P1: 앱 managed worktree와 SDK 경계를 분리하고 코어가 일반 Git worktree adapter를 소유하도록 했다. `supports_interrupt` 등 runtime capability와 timeout·격리·늦은 결과 폐기 경로를 추가했다. 초기 세션 유형을 Worker·Reviewer로 줄이고 Coordinator·Integrator를 승격 조건이 있는 보류 항목으로 옮겼다. 작업 계열별 지표를 분리하고 정식 Requirement 엔티티를 Run 필드와 버전으로 축소했다.
- P2: 현재 상태 테이블을 유일한 정본, Event를 감사 기록으로 고정했다. 불일치 시 자동 재구축을 금지했다. `schema_version`, state root 배타 실행 락, DB·Artifact 일관 백업을 추가했다. 초기 범위를 Git 프로젝트로 한정했다. 코어 개발·디버깅 비용과 실험별 코어 변경량을 지표에 넣고 동적 worker의 조건을 READY Task가 슬롯보다 많은 경우로 한정했다.
- P3: `Brain 비용`을 `조정 비용`으로 일반화하고 §9.3을 상태 전이의 단일 규범으로 지정했다.
- Clean-room 권고: 초기 코드 구조를 `ledger`, `contract`, `runtime`, `verify`, `schedule`, `recover`, `cli` 7개 모듈로 축소했다.
- 교차 재검토: `가설 1 → B1 최소 실험판 → 가설 7 → 전체 확장` 순서를 명시했다. Worktree 위치 설정에 관한 공식 문서 판본 충돌은 어느 쪽에도 의존하지 않는 설계로 제거했다.

### 동결 검증

- 17개 설계 체크를 스크립트로 검사해 모두 통과했다: 상태 헤더, 인증 경계, 외부 pilot, 세션 유형 축소, Requirement 보류, interrupt 대체 경로, 상태 정본, schema·락·백업, Git 초기 범위, 작업 계열별 지표, 코어 비용, 동적 worker 조건, 조정 비용 명칭, 상태 규범, 7개 모듈, 구현 게이트.
- 상대 링크 2개가 모두 실제 파일을 가리킨다.
- Markdown 코드 펜스는 32개로 짝이 맞고 trailing whitespace는 0건이다.
- `git diff --check`에서 오류가 없었다. 표시된 LF→CRLF 메시지는 기존 저장소 줄바꿈 설정 경고이며 파일 내용 오류가 아니다.

### 보호 문서 무결성

| 파일 | 줄 수 | SHA-256 |
|---|---:|---|
| `ai-orchestration-broad-literature-review.md` | 1,242 | `912A4A2C0B6F53B04A3404929D3B7A81F970E1FAC7DBA36C3565351FC492A89F` |
| `ai-orchestration-practical-cases-and-methods.md` | 787 | `A6328DC9F02D77709B27B8F2FA07870F8A3DED68AD602F9FE0DA0A584F2EEF6A` |
| `claude-review-ai-orchestration-broad-literature-review.md` | 460 | `32824BD1D8D8EF552EAEBD59C58E6B256B7CF3A3CDE9C7A8D1E5832DC290A874` |
| `claude-review-prompt.md` | 232 | `A2C8790211FA778B84A042E8C9079705BEFB4E406B1E1B2DD2F51050E826C67C` |
| `claude-review-general-local-session-orchestrator-design.md` | 701 | `446C8C708B215F6CB7E63D65EE4422C589A23B696E7327B29225BF90A39E32DC` |
| `claude-recheck-codex-response-general-local-session-orchestrator.md` | 364 | `12A6542ADD09154E8B379C26D48D1A1B2BF95FC3277A887734470097AD61C547` |
| `codex-response-to-claude-review-general-local-session-orchestrator-design.md` | 209 | `CE6E7ACCB9DD82DF0D80F1C2B4C434D727FA685233E92E666AD8727977D8465B` |

위 보호 문서는 이번 동결 작업에서 수정하지 않았다. 동결된 설계의 다음 작업은 §16.6 가설 1의 인증·과금 통제 확인이며, 그 전에는 B1 코드를 작성하지 않는다.

## 인증·사용량 사전 점검

### 점검 범위

- 작업일: 2026-08-04.
- 동결 설계 §16.6 가설 1 가운데 비용 없이 확인할 수 있는 인증 방식, 공식 지원 범위, 로컬 SDK 계약, 계정 사용량 기준선을 점검했다.
- 결과는 `docs/experiments/codex-auth-usage-preflight.md`에 기록했다.
- 실제 Codex SDK turn은 실행하지 않았다. 이번 점검의 AI 실행 횟수는 0회다.

### 확인 결과

- 현재 인증 모드는 `chatgpt`이며 캐시된 API 키와 `OPENAI_API_KEY`·`CODEX_API_KEY` 환경 변수는 없었다. 인증 토큰 값은 출력하거나 기록하지 않았다.
- OpenAI 공식 문서에서 ChatGPT 플랜이 Codex SDK, `codex exec`, scriptable workflow를 지원하고, API 키는 별도의 사용량 기반 과금 경로임을 확인했다.
- 공식 문서는 ChatGPT 인증 캐시를 신뢰할 수 있는 자동화 환경에서 사용하는 경로를 설명하지만, 자동화의 권장 기본값은 API 키라고 함께 밝힌다.
- 시스템 Python에는 `openai-codex`가 없었다. 임시 venv에만 최신 배포판 0.144.4를 설치했고, 기존 `이어서 작업` 프로젝트의 고정 버전과 같음을 확인했다.
- SDK 0.144.4 소스에서 공개 `TurnHandle.interrupt()`와 `TurnResult.usage`를 정적으로 확인했다. 실제 동작과 반환값은 실행하지 않아 미확인이다.
- 생성된 내부 프로토콜에는 계정 usage와 rate limit 조회 메서드가 있으나 공개 고수준 래퍼가 없어 v0 설계 의존 대상에서 제외했다.
- 공식 대시보드 기준 주간 한도는 21% 남았고 추가 크레딧은 0이었다. 남은 한도가 적어 원래 생각했던 3회 통제 실행을 하지 않았다.

### 다음 게이트

- 사용자 승인 또는 한도 초기화 뒤 `gpt-5.6-luna`, read-only, 동시성 1, 재시도 0 조건으로 최소 turn 1회만 실행한다.
- 실행 직전 ChatGPT 인증과 API 키 부재를 다시 확인하고, 조건이 다르면 fail-closed로 중단한다.
- 전후 대시보드 값과 `TurnResult.usage`를 함께 기록한 뒤에만 B1 최소 실행기 구현으로 이동한다.

### 동결 문서 무결성

- `docs/design/general-local-session-orchestrator-design.md`는 수정하지 않았다.
- 점검 직전 SHA-256은 동결 시점과 같은 `F1722A3344F69EF9B85DF3FBF280F9B1BE027D3EAFFA20CDE4BC8AF816A102F3`였다.

## Codex SDK 최소 turn 1회 실험

### 실행 범위

- 작업일: 2026-08-04.
- 사용자 승인 후 `gpt-5.6-luna` SDK turn을 정확히 1회 실행했다. 재시도는 0회다.
- fail-closed 실행기는 `experiments/codex_sdk_single_turn_precheck.py`, 결과 보고서는 `docs/experiments/codex-sdk-single-turn-experiment.md`에 저장했다.
- 동결 설계 문서는 수정하지 않았다.

### 결과

- 실행 직전 인증 모드는 `chatgpt`였고 `OPENAI_API_KEY`와 `CODEX_API_KEY`는 없었다.
- `openai-codex==0.144.4`, read-only sandbox, `deny_all`, ephemeral thread 조건에서 `completed`로 끝났다.
- 최종 응답은 요청한 `PRECHECK_OK`와 정확히 같았다.
- SDK 보고 시간은 2,972 ms, 외부 관측 시간은 3,881 ms였다.
- `TurnResult.usage`는 input 12,571, output 7, total 12,578 tokens를 반환했다. cached input과 reasoning output은 0이었다.
- 대시보드는 실행 직전과 직후 모두 주간 잔여 17%, 935 turns, 추가 크레딧 0으로 표시됐다. 반영 지연이나 정수 표시의 영향을 배제할 수 없어 SDK turn의 대시보드 매핑은 미확인으로 남겼다.
- 초기 점검의 21%에서 실행 직전 17%로 감소했지만 SDK 실행 전에 발생한 변화이므로 이번 실험에 귀속하지 않았다.

### 판정과 다음 게이트

- 공식 지원 경로, 로컬 ChatGPT 인증 SDK 실행, API 키 경로 차단, turn별 usage 수집을 확인했으므로 가설 1의 B1 구현 착수 게이트는 통과로 판정했다.
- 최소 응답에도 input 12,571 tokens가 들어가 새 thread 시작 비용이 작지 않다는 신호를 얻었다. session 재사용과 새 session 정책의 비교는 후속 가설로 남겼다.
- 현재 주간 잔여가 17%이므로 추가 live turn은 실행하지 않는다. B1은 mock/fake runtime과 단위 시험부터 구현하고 실제 SDK 통합 시험은 한도 초기화 후 예산을 고정해 수행한다.

## B1 최소 오케스트레이터 구현 명세

### 작업 범위

- 작업일: 2026-08-04.
- 사용자 요청에 따라 코드 구현 없이 `docs/design/b1-minimum-orchestrator-implementation-spec.md`를 작성했다.
- 동결 설계를 수정하지 않고 B1 범위의 디렉터리, 기술 선택, Project Pack, 공개 계약, SQLite DDL, 상태 기계, 실행 의사코드, 복구, FakeRuntime, CLI, 시험, 완료 기준을 구체화했다.
- B1 reference 언어는 Python 3.12, controller는 동기식 단일 프로세스, 상태 정본은 SQLite, 실제 Worker는 한 번에 하나로 확정했다.
- 병렬 Worker, Reviewer, Coordinator·Integrator, worktree, 외부 행동, UI는 B1 명세에서 제외했다.

### 핵심 안전 결정

- 모든 상태 전이는 `ledger.py`의 한 경로와 같은 트랜잭션의 Event 기록을 사용한다.
- AI의 completed claim은 `REPORTED`까지만 허용하고 scope·stale·Artifact·Project Check를 통과해야 성공한다.
- runtime 시작과 runtime ID 저장 사이에 controller가 중단되면 `DISPATCH_UNCERTAIN`으로 차단하고 자동 재시도하지 않는다.
- B1은 API key 환경을 fail-closed하고 현재 검증한 ChatGPT 인증 경로를 사용하도록 명세했다.
- FakeRuntime을 첫 실행기로 두고 필수 실패·경합 scenario를 통과하기 전 실제 Codex를 호출하지 않는다.
- Project Check는 argv 배열과 `shell=False`만 허용한다.

### 검증 결과

- 명세 안의 schema version 1 DDL을 in-memory SQLite에서 실행했고 10개 규범 테이블 생성과 `foreign_key_check=[]`를 확인했다.
- Markdown 코드 fence는 짝이 맞고 trailing whitespace는 0건이다.
- 구현 파일과 패키지 구조는 생성하지 않았다. 기존 1회 SDK 사전 실험 스크립트 외 B1 코드는 없다.
- `docs/design/general-local-session-orchestrator-design.md`는 1,088줄, SHA-256 `F1722A3344F69EF9B85DF3FBF280F9B1BE027D3EAFFA20CDE4BC8AF816A102F3`로 동결 상태와 같다.

## B1 구현 명세 Claude 심사 프롬프트

- 작업일: 2026-08-04.
- `docs/prompts/b1/claude-review-prompt-b1-minimum-orchestrator-implementation-spec.md`를 작성했다.
- Claude가 B1 명세의 구현 가능성, B2 범위 유입, DDL·상태 전이, 중단·복구, 포트 책임, 보안, FakeRuntime 시험, Codex SDK 경계를 집중 심사하도록 했다.
- 결과 저장 경로는 `docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md`로 지정했다.
- 주 대상과 동결 설계를 수정하지 않도록 명시했다.

## B1 구현 명세 심사 반영·동결

### 작업 범위

- 작업일: 2026-08-04.
- Claude 심사 보고서 `docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md`의 P0 2건, P1 6건, P2 6건, P3 2건을 모두 `docs/design/b1-minimum-orchestrator-implementation-spec.md`에 반영했다.
- B1 코드 구현, 패키지 설치, 추가 Codex live turn은 수행하지 않았다.
- 수정 전 명세는 1,236줄, SHA-256 `476AC496915999313733C82D65C1A0211CDD9046FFC005B7D441FC6355BB5A5D`였다.
- 동결 명세는 1,415줄, 56,894바이트, SHA-256 `8011161CCCF842F90D853B8383AD8457C1C51CBF7FC81E1F77ECBAC0B9CDD7A7`이다.

### P0·P1 반영

- SDK 0.144.4에 없는 `observe()`를 제거하고 `await_terminal(handle, monotonic_deadline)` 포트로 교체했다. Codex adapter는 daemon consumer thread에서 blocking `TurnHandle.run()`을 소비하고 main controller가 deadline, interrupt grace, quarantine을 집행하도록 고정했다.
- `AsyncCodex`도 내부적으로 `asyncio.to_thread()`를 사용하므로 단순 coroutine 취소가 blocking queue consumer를 끝낸다고 가정하지 않도록 했다.
- `thread_start()`와 `thread.turn()` 양쪽에 `ApprovalMode.deny_all`을 강제하고 SDK 기본 `auto_review`에 의존하지 않게 했다.
- SDK 예외를 `RuntimeFailure`로 정규화하고 알 수 없는 오류는 `retryable=false`로 두었다.
- FakeRuntime도 실제 adapter와 같은 blocking notification·deadline 경계를 사용하도록 바꿨다.
- thread 누적 usage snapshot과 turn별 delta 계산을 명시했다.
- Artifact 경로 기준을 state root POSIX 상대 경로로 확정했다.
- Attempt terminal 전이와 `tasks.active_attempt_id=NULL`을 한 트랜잭션으로 처리하도록 했다.
- 상태 전이·결과 채택·Check의 자연 idempotency key 규칙을 확정했다.

### P2·P3 반영

- migration `up_sql` SHA-256, DDL·migration 이력 insert 원자성, 시작 시 checksum 재검증을 명시했다.
- `read_scope`는 접근 통제가 아니라 fingerprint·컨텍스트 범위임을 분리했다.
- Check가 Worker 수정 코드를 실행하므로 신뢰 경계가 아니며 사용자 소유 신뢰 저장소만 대상으로 한다고 명시했다.
- clean worktree를 Run 생성 전에 검사하고 위반 시 exit code 2로 거부하도록 했다.
- `project_pack_sha256`을 저장하고 dispatch·검증·완료 전에 다시 검사하도록 했다.
- controller lock 아래 SQLite online backup과 Artifact 복사의 시점 정합성을 명시했다.
- Project Pack `check_name`과 원장 `check_id`를 분리했다.
- 비상태 문자열 enum을 확정하고 DDL CHECK 제약에 반영했다.

### 추가 범위 축소와 구현 순서

- 실행하지 않는 빈 `hooks/` 확장점과 중복 Check kind를 B1 구조에서 제거했다.
- 기존 I1~I12 horizontal 순서를 S0~S6 vertical slice로 교체했다.
- 첫 S0은 FakeRuntime read-only Task 하나가 SUCCEEDED까지 관통하는 500줄 미만 목표이며 Artifact·Check·Decision·lock·재시도·Codex adapter를 제외한다.
- 같은 Attempt resume에서 결과가 덮어써지지 않도록 turn별 Result Artifact 경로와 active runtime turn ID를 명시했다.

### 재검증

- SDK 0.144.4 소스에서 동기 TurnHandle에 `observe()`가 없고 blocking `stream()`, `interrupt()`, 기본 `approval_mode=auto_review`, async client의 `asyncio.to_thread()`를 다시 확인했다.
- 규범 DDL을 in-memory SQLite에서 실행해 10개 테이블 생성과 `foreign_key_check=[]`를 확인했다.
- Run→Task→Attempt→Session 표본을 실제 DDL에 insert하고 순환 FK 삽입 순서, Attempt terminal 후 `active_attempt_id=NULL`, 전후 foreign key 무결성을 확인했다.
- Claude 지적 16건의 대응 문구가 모두 존재하고 제거 대상인 `observe(turn_handle)`, `check_ids_json`, 빈 `hooks/`, 옛 I1 순서가 없음을 검사했다.
- Markdown code fence 짝, 상대 링크, trailing whitespace, `git diff --check`를 검사해 내용 오류가 없었다. Git의 LF→CRLF 메시지는 기존 저장소 설정 경고다.

### 보호 문서 무결성

| 파일 | 줄 수 | SHA-256 |
|---|---:|---|
| `general-local-session-orchestrator-design.md` | 1,088 | `F1722A3344F69EF9B85DF3FBF280F9B1BE027D3EAFFA20CDE4BC8AF816A102F3` |
| `claude-review-b1-minimum-orchestrator-implementation-spec.md` | 523 | `169504BC9BDF3E885C53441D8243E575B918A71E9D9A53A344B8585C407302F6` |
| `codex-sdk-single-turn-experiment.md` | 111 | `B4144CEC3F7C083411BBAE46452D5CA17CF5071D70CF052ED8D59FF63E72F8AE` |

상위 설계와 Claude 심사 보고서는 이번 심사 반영 작업에서 수정하지 않았다. SDK 실험 보고서는 커밋 전 `git diff --check`가 지적한 EOF 빈 줄 1개만 제거했으며 내용은 바꾸지 않았다. B1 명세는 구현 전 상태로 동결했으며 다음 작업은 §17의 S0 vertical slice 구현이다.

## docs 디렉터리 구조 정리

### 작업 범위

- 작업일: 2026-08-04.
- `docs/` 루트에 섞여 있던 기존 Markdown 문서 18개를 역할별 디렉터리로 이동했다.
- `docs/README.md`를 새로 만들어 현재 문서, 권장 읽기 순서, 각 디렉터리의 역할을 한곳에서 찾을 수 있게 했다.
- 문헌조사·설계·실험·심사·심사 프롬프트·운영 기록·폐기된 fork 설계를 각각 `research/`, `design/`, `experiments/`, `reviews/`, `prompts/`, `operations/`, `archive/`로 분리했다.
- 구현 코드와 문서의 의미 내용은 수정하지 않았다. 이동으로 깨지는 파일 경로와 상대 링크만 새 위치에 맞게 고쳤다.

### 이동·참조 검증

- 기존 문서 18개를 `HEAD`의 원본과 파일별로 비교했다. 새 경로 치환과 필요한 상대 링크 조정만 적용한 예상 결과에 18개 전부 정확히 일치했다.
- 경로 참조가 실제로 바뀐 문서는 15개이고, 나머지 3개는 내용 변경 없이 이동만 했다.
- `docs/` 아래 Markdown 19개에서 로컬 링크 37개를 파일 기준으로 해석해 확인했으며 누락 대상은 0개였다.
- 예전 `docs/<파일명>.md` 평면 경로 18종을 전수 검색했으며 잔존 참조는 0개였다.
- `docs/` 최상위 파일은 안내용 `README.md` 하나만 남겼다.

### 동결·보호 문서 해시 영향

문서 이동 자체는 파일 해시를 바꾸지 않는다. 다만 현재 위치를 가리키는 경로 문자열이나 상대 링크를 가진 동결·보호 문서는 경로만 고치면서 해시가 바뀌었다. 이전 로그의 해시는 당시 판본을 확인하는 역사적 값으로 유지하고, 구조 정리 직후 값을 아래에 기록한다.

| 문서 | 구조 정리 직후 줄 수 | 구조 정리 직후 SHA-256 | 변경 성격 |
|---|---:|---|---|
| `docs/design/general-local-session-orchestrator-design.md` | 1,088 | `9E8BC884A42D9D1EE44C369A75B1D7B8B408273C31D696C0C2835B725D797BFE` | 문헌조사 상대 링크와 문서 경로만 조정 |
| `docs/design/b1-minimum-orchestrator-implementation-spec.md` | 1,415 | `40BDBB81DABEDBCCA0D3400590E1E224E14B9DFBE961EA57AEF078703005B900` | 심사 보고서 경로만 조정 |
| `docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md` | 523 | `A21EE022357035F3EE995C99CDFA093894FCEA4B5973A5CEEF2CF493878C07FB` | 대상·관련 문서 경로만 조정 |
| `docs/experiments/codex-sdk-single-turn-experiment.md` | 111 | `43072BF20D1A1FFC365E46F8540C57C16FB8226E22FE6B3EB8E30EEDAA0FFD5A` | 저장소 루트의 실험 스크립트 상대 링크만 조정 |

문헌조사 두 문서는 내용 변경 없이 이동됐다. SHA-256은 각각 `912A4A2C0B6F53B04A3404929D3B7A81F970E1FAC7DBA36C3565351FC492A89F`, `A6328DC9F02D77709B27B8F2FA07870F8A3DED68AD602F9FE0DA0A584F2EEF6A`로 구조 정리 전과 같다.
