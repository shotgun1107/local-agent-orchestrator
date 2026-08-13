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

## B1 순차 세션 오케스트레이터 구현

### 구현 범위

- 작업일: 2026-08-04.
- 구현 위치: `stages/b1-sequential/`.
- 기능 코어는 `contract.py`, `ledger.py`, `runtime.py`, `verify.py`, `schedule.py`, `recover.py`, `cli.py`의 7개 모듈로 제한했다.
- Pydantic 계약과 JSON Schema, SQLite 원장과 migration checksum, 순차 스케줄러, FakeRuntime·CodexRuntime, 검증·Artifact 저장, 복구·백업, CLI를 구현했다.
- `benchmarks/`에는 B0/B1 동결 manifest와 서로 독립적인 `code-change`, `document-read` fixture를 추가했다. 두 fixture 모두 FakeRuntime 경로로 관통 검증했다.
- B2 병렬 실행, B3 적응형 라우팅, Reviewer·Coordinator·Integrator 역할, Codex 앱 worktree 제어는 구현하지 않았다.

### 확인한 항목

- Python 3.12 가상환경에서 `pytest -q`를 실행해 60개 테스트가 모두 통과했다.
- 12개 FakeRuntime 고장 시나리오, fixed fixture 두 개, CLI, 상태 전이와 Event 원자성, 재시도, timeout·interrupt, 재시작, backup·integrity, schema 동기화를 자동 테스트로 확인했다.
- `openai-codex==0.144.4` 실제 설치본의 공개 API를 기준으로 `account()`, `thread_start()`, `turn()`, blocking `TurnHandle.run()`, `interrupt()` 경계를 맞췄다. thread와 turn 양쪽의 approval mode는 명시적으로 `deny_all`이다.
- CodexRuntime은 `OPENAI_API_KEY`가 있으면 실패하고, SDK `account()` 결과가 `chatgpt`가 아니거나 확인 불가이면 실패하도록 했다. 계정 식별자와 토큰은 출력하지 않는다.
- JSON 파일 17개 파싱, 로컬 Markdown 링크 48개 해석, 기능 코어 7개 여부, `shell=True` 부재, pilot 고유 역할 문자열 부재, B2·B3 구현 디렉터리 부재를 정적 점검했다.

### 확인하지 못한 항목

- 실제 Codex 모델을 호출하는 live smoke는 사용자 요청에 따라 집 PC 검증으로 넘겼다. 이 작업 중 실제 모델 turn 호출 수는 0회다.
- isolated wheel 빌드는 build backend 다운로드가 필요한 시점에 현재 세션 사용 한도 때문에 승인을 완료하지 못해 미확인이다. editable 설치는 성공했다. wheel 내부 Project Pack 포함 여부도 집 PC에서 확인해야 한다.
- 실제 ChatGPT 구독의 동시 세션 제한, usage 계측 위치, 장시간 timeout 후 app-server의 실제 종료 거동은 미확인이다.

### 문서와 해시

- 집 PC 실행 절차와 중단 조건은 `docs/operations/b1-home-test-handoff.md`에 기록했다.
- B1 명세는 상태와 구현 링크만 바꿨다. 변경 전 Git blob은 `24a28759babf4cf54c1f61ce756166593a0c472a`, 변경 후 작업 트리 blob은 `54f06a40b8eea09d802673aa319ba26aec99c4ec`, 변경 후 SHA-256은 `5CC76E7B7E0D3419A48E1CB1A291B13C20F3322D7283243D2491B41EC82233D2`다.
- 동결된 연구·심사 문서는 이 구현 작업에서 수정하지 않았다.

## B1 실제 Codex smoke 검증

### 실행 범위와 사전 게이트

- 실행일: 2026-08-05.
- Python 3.12.10, `openai-codex==0.144.4`에서 smoke 직전 비라이브 회귀시험 60개를 실행해 모두 통과했다.
- isolated wheel 빌드가 통과했다. wheel SHA-256은 `23D8F64F8659CCB355F0BBEDF95EFD664E899D20CDDFAE4AD2C1A7081FC55FA5`이며, 7개 코어 모듈과 `orchestrator/_project_pack/`의 포함을 archive 목록으로 확인했다.
- 공식 `codex login status`와 SDK `account()`에서 ChatGPT 인증을 확인했다. `OPENAI_API_KEY`는 없었다.
- 원본 fixture를 수정하지 않고 임시 경로에 복사한 뒤 새 Git 저장소로 초기화했다. 승인 실행 사용자와 임시 저장소 소유자 차이는 전역 Git 설정을 바꾸지 않고 해당 프로세스의 `safe.directory` 값으로만 처리했다.
- `lao doctor`에서 SDK pin, ChatGPT 인증, Git root, clean worktree를 확인했고 Run Spec validation도 통과했다.

### 실제 호출 결과

- 실제 모델 호출은 `document-read` smoke 1회뿐이며, 생성된 Codex turn도 1개다.
- Run ID: `run_be31ab80d7294e88bf875fcc27514b6a`.
- Run `COMPLETED`, Task `SUCCEEDED`, Attempt 1 `SUCCEEDED`, Session `COMPLETED`; resume 0, interrupt 요청 없음이다.
- `acceptance`, `diff_check`가 모두 exit code 0으로 `PASSED`했다.
- ResultEnvelope SHA-256은 `ADD1F9DF22082931E088D132A85BB908C83C27695FAA44AAB5DA73EE9AC032A6`이고 원장 값과 실제 파일 hash가 일치했다.
- Run Artifact는 17개다. `recover check` 결과 SQLite quick check `ok`, foreign key 위반 0, 손상 Artifact 0, 비밀 탐지 0이다.
- online backup을 만든 뒤 별도의 `recover verify-backup`으로 manifest와 모든 파일 hash가 일치함을 확인했다.
- usage는 `measured`다. input 85,328, output 771, total 86,099 tokens이며 원장 wall-clock은 39.698초, CLI 관측은 약 41초다.
- input 수치는 작업 문서 분량만이 아니라 새 thread에 들어간 시스템·도구·환경 컨텍스트를 포함한 thread 누적값이다. B0 비교 전에는 효율성 수치로 해석하지 않는다.

### Definition of Done 감사

- §16의 1~11번은 코어 구조·상태 원장·검증 순서·고장 fixture와 자동시험으로 확인했다.
- 12번은 위 실제 Codex smoke에서 ResultEnvelope와 measured usage 수집으로 확인했다.
- 13번은 실제 Run의 secret scan 0건으로 확인했다.
- 14번은 Project Pack만 다른 `code-change`, `document-read` 독립 Git fixture의 FakeRuntime 관통 시험으로 확인했다.
- 15번 감사 중 fixture `commit`이 `TO_BE_RECORDED_AFTER_CHECKOUT`으로 남은 것을 발견했다. 실제 비교 전에 출처 commit과 fixture별 Git tree를 고정하고 회귀시험을 추가했으며, 최종 비라이브 시험은 61개가 모두 통과했다.
- 16번은 B2·B3 디렉터리와 병렬·Reviewer·worktree 구현 부재를 정적으로 확인했다.
- 이에 따라 B1 Definition of Done은 통과했다. 단, B1이 B0보다 효율적인지를 묻는 가설 7은 반복 비교 전이므로 미확인이다.

### 문서와 남은 범위

- 최신 실행 기록은 `docs/operations/b1-home-test-handoff.md` §8에 반영했다.
- B1 명세 상태 줄은 실제 smoke 완료로만 갱신했다. 현재 Git blob은 `17f3ca281cd49abb9f10cf9b5283728f4c95ee42`, SHA-256은 `3097DA304731DDFC6A030C9AE07AD386CEDF767F2B7617B6DF1E55193E188F2E`다.
- 연구·심사·범용 설계 문서는 수정하지 않았다.
- 남은 작업은 동결 manifest에 따른 B0/B1 두 fixture × 각 3회 비교와 가설 7 판정이다. 그 전에는 B2를 구현하지 않는다.

## 구현 오류 해결 로그 하네스

### 작업 범위

- 작업일: 2026-08-05.
- 실행 원장이 아니라 오케스트레이터 구축 중 발견한 설계·구현·시험·통합 오류를 기록하는 하네스를 `tools/implementation-log/`에 추가했다.
- 저장소 소유권 이전, remote URL 변경 같은 저장소 관리 작업은 기록 범위에서 명시적으로 제외했다.
- JSON incident를 원본으로 두고 `docs/operations/implementation-incidents/index.md`를 결정론적으로 생성한다.

### 강제하는 기록

- 증상, 재현 절차, 증거 수준, 근본 원인, 검토한 대안과 채택 여부, 해결 내용, 수정 파일, 회귀시험, 검증 결과, 남은 위험, 관련 커밋을 분리했다.
- 해결 상태로 바꾸려면 근본 원인·해결·회귀시험·검증 결과가 모두 있어야 한다.
- 위험한 상대 경로, 알 수 없는 필드, 중복 ID, 대표적인 API·GitHub token 문자열을 검증 단계에서 거부한다.
- 사람용 Markdown을 직접 수정하면 `check`가 JSON 원본과의 불일치를 실패로 보고한다.

### 초기 이관

- 기존 기록에서 직접 근거가 있는 오류 3건을 incident로 이관했다: SDK에 없는 `observe()` 가정, `approval_mode=auto_review` 기본값, benchmark fixture commit placeholder.
- 이관하지 않은 과거 항목은 근본 원인·회귀시험·증거를 현재 자료로 확정할 수 있을 때만 추가한다.

### 검증

- 표준 라이브러리만 사용하는 하네스 단위시험 10개가 통과했다.
- 기존 기록에서 이관한 incident 3건과 하네스 검증 중 발견한 Python launcher 환경 가정 오류 1건, 총 4건이 validation을 통과했다.
- 생성 문서와 JSON 원본의 결정론적 일치 검사는 최종 작업 검증에서 수행한다.

## 범용 Benchmark Runner 설계

### 작업 범위

- 작업일: 2026-08-05.
- `docs/design/general-benchmark-runner-design.md`를 새로 작성했다.
- 대상은 B1 내부 기능이 아니라 B0~B3 단계의 실행 조건을 고정하고 결과를 공통 형식으로 측정·판정하는 중립 실험 제어기다.
- 최초 실험은 동결된 B0/B1 manifest의 두 fixture × 두 variant × 3회, 총 12 Cell이다.

### 주요 결정

- Runner 코어는 variant 이름의 의미를 해석하지 않고 `VariantAdapter` 계약으로 B0·B1과 이후 B2·B3를 연결한다.
- 현재 구현 대상으로는 B0 Manual Adapter와 B1 Sequential Adapter만 정의했다. B2·B3 자체와 그 Adapter는 해당 단계의 채택 게이트를 통과하기 전에는 구현하지 않는다.
- Runner는 B1 Python 내부 모듈이나 SQLite를 직접 읽지 않고 공개 CLI·JSON report만 사용한다.
- 활성 상태와 임시 workspace는 Git 밖의 사용자 state root에 두고, redaction·hash·봉인을 통과한 결과만 `benchmarks/results/`로 내보낸다.
- source worktree 복사 대신 manifest의 source commit에서 fixture를 복원하고 Git tree를 다시 계산한다.
- B0/B1 자체 완료 보고와 내부 Check를 최종 판정으로 사용하지 않고, Runner의 독립 Judge가 같은 acceptance·scope·diff 검사를 두 결과에 적용한다.
- 사람 개입은 회상이 아니라 append-only Event로 즉시 기록하며, 측정 불가 값은 0 대신 `unknown`으로 보존한다.
- Experiment·Cell 상태기계, 균형 Block 순서, 실패 보존, 자동 재실행 금지, revision 교체, Evidence seal을 명시했다.
- 공통 Core Measurement와 variant별 namespaced metrics를 분리해 B2 병렬성과 B3 Reviewer 지표가 생겨도 코어 계약을 불필요하게 변경하지 않게 했다.

### 구현 계획과 게이트

- Fake Adapter vertical slice, fixture·Judge, B0 Adapter, B1 Adapter, 상태·복구, 비교·export, 실제 실행 전 동결의 R0~R6 순서를 제안했다.
- Runner Definition of Done 18개를 정의했다. 실제 비교 turn은 Runner와 B1 artifact, 실행계획, decision policy를 hash로 고정하고 비라이브 회귀시험을 통과한 뒤에만 시작한다.
- B1 채택 판정은 품질 비열화 방지, 사람 중계·복구 부담 감소, scope·integrity 조건을 함께 사용하며 `ADOPT_B1`, `REJECT_B1`, `INCONCLUSIVE`를 구분한다.

### 확인한 것과 확인하지 않은 것

- 확인: 현재 동결 manifest, B0 runbook·measurement schema, 두 fixture의 Run Spec·Check, B1 공개 CLI·report 지표와 설계가 충돌하지 않는지 대조했다.
- 확인: 기존 `benchmarks/`에는 입력·결과만 두고 구현 코드는 두지 않는 규칙에 따라 Runner 소스 위치를 `tools/benchmark-runner/`로 정했다.
- 미확인: B0에서 model을 검증 가능하게 고정하는 실제 Codex 표면, B0 usage 직접 회수 가능성, 최초 실행 seed, B1 수정 후 새 wheel hash는 구현·preflight에서 확정해야 한다.
- 미구현: Runner 코드, 공통 Schema, Adapter, 실제 12 Cell, 비교 결과는 아직 없다.
- 이 작업에서 모델 turn을 호출하지 않았고 B0/B1 동결 manifest와 fixture는 수정하지 않았다.

## Benchmark Runner 설계 Claude 심사 프롬프트

### 작업 범위

- 작업일: 2026-08-05.
- `docs/prompts/benchmark-runner/claude-review-prompt-general-benchmark-runner-design.md`를 작성했다.
- 주 심사 대상은 `docs/design/general-benchmark-runner-design.md` 하나이며 기존 설계·manifest·B0·B1·운영 로그는 사실 대조용 읽기 전용 자료로 지정했다.
- 심사 결과는 `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` 새 파일 하나에만 저장하도록 제한했다.

### 심사 축

- 맥락 이해, 맥락 비의존, clean-room 최소 설계를 분리했다.
- 실험 타당성, B0/B1 공정성, manifest 사전 등록, 상태·복구, 독립 Judge, 측정 계약, 결과 봉인, CLI 운용, 채택 정책을 필수 질문으로 지정했다.
- B2/B3 확장성이 실제 Adapter 경계에서 성립하는지와 아직 존재하지 않는 단계를 위한 조기 추상화인지 둘 다 검토하게 했다.
- 현재 전체 설계와 단일 script·pytest·작은 CLI·수동 측정·기존 도구 대안을 같은 기준으로 비교하게 했다.
- P0~P3 문제, 실험 타당성 표, 범용성 표, 계약 구현 가능성, clean-room 구조, R0~R6 재판정, 최종 판정을 필수 산출물로 지정했다.

### 제한

- 이 프롬프트 작성 시점에는 Claude 심사를 아직 실행하지 않았다. 이후 결과는 다음 개정 절에 기록한다.
- 주 설계와 보호 파일은 이 프롬프트 작업에서 수정하지 않았다.

## Benchmark Runner 1차 심사 반영과 재심사 준비

### 작업 범위

- 작업일: 2026-08-05.
- `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md`의 P0 3건, P1 7건, P2 6건, P3 2건을 `docs/design/general-benchmark-runner-design.md`에 반영했다.
- 1차 심사 보고서는 개정 이력으로 보존하고 수정하지 않았다.
- Runner와 B1 코드는 구현·수정하지 않았고 모델 turn도 호출하지 않았다.

### 실험 계약 정정

- B0 최초 prompt와 B1 start를 `startup_action_count`로 대칭 기록하고, primary 사람 부담 gate는 시작을 제외한 실행 중 중계만 사용하게 했다.
- manifest bytes를 최상위 권위로 두고 baseline/candidate, seed, 숫자 판정식, reasoning 통제 같은 보충값을 Plan fingerprint와 Experiment ID에 포함했다.
- B1 `partial_or_unknown` usage는 core `unknown`으로 정규화하고 정수 subtotal은 variant 원시 지표로만 보존한다.
- B1 Adapter 전에 status/report 공개 JSON Schema와 contract test를 추가하도록 R2 선행 조건을 만들었다.
- exit 130, exit 0 nonterminal, stale lock, Judge 고아 process, B0 Event 정본, 실행 표면 차이와 반복 학습효과를 계약·시험·해석 한계에 반영했다.

### 구조 축소

- 구현 모듈을 9개에서 7개(`contract`, `plan`, `workspace`, `adapter`, `runner`, `judge`, `cli`)로 줄였다.
- 공개 Schema를 6개에서 3개(Execution Plan, Measurement, Intervention Event)로 줄였다.
- Evidence 목록은 Measurement에 포함하고 Summary는 결정론적 파생 출력으로 뒀다.
- Experiment의 두 번째 상태기계를 없애고 Cell 상태와 최소 제어 기록에서 표시 상태를 파생한다.
- Adapter Protocol은 `id`, `capabilities`, `preflight`, `run` 네 method로 축소했다. 실제 B2 공개 경계가 생기기 전에는 `observe/request_stop`을 추가하지 않는다.

### 구현 순서 변경

- R0은 실제 모델 없이 단일 Fake Cell을 관통하는 작은 vertical slice다.
- R1은 fixture와 Judge, R2는 B1 공개 Schema와 FakeRuntime Adapter, R3는 B0 Manual Adapter 순서다.
- 기존 `23D8F64F8659CC…` wheel은 `53cb512` doctor 수정과 새 출력 Schema 이전 artifact라 실행 Plan에 재사용하지 않도록 명시했다.

### 직접 확인

- 동결 manifest 43줄을 다시 읽어 reasoning effort, baseline/candidate 방향, 숫자 decision policy가 없고 12 Cell은 2×2×3의 유도값임을 확인했다.
- B1 `schedule.py`에서 `usage_status`가 `measured` 또는 `partial_or_unknown`이고 `token_usage`가 정수 dict로 반환되는 경로를 확인했다.
- `run-status.schema.json`, `run-report.schema.json`이 현재 B1에 없음을 파일 검색으로 확인했다.
- Git 이력에서 기존 smoke 이후 `53cb512 fix: require ChatGPT authentication in doctor`가 추가됐음을 확인했다.
- 개정 설계에 `git diff --check`를 실행해 whitespace 오류가 없음을 확인했다.

### 산출물과 미확정

- 개정 설계: 1,620줄, SHA-256 `A2B834EF12035C64633F488233643B0B1A3D851E73FF70011FB152914D1F83E5`.
- 재심사 프롬프트: `docs/prompts/benchmark-runner/claude-rereview-prompt-general-benchmark-runner-design.md`, 225줄, SHA-256 `B3161DAFF558FBD93505FFBFA75B020FE0F2F450DBF29E5A9F2AF3A33A4F3F41`.
- 재심사 결과 저장 위치는 `docs/reviews/benchmark-runner/claude-rereview-general-benchmark-runner-design.md`로 지정했다. 이 작업에서는 재심사를 실행하지 않았다.
- B0 model/reasoning 확인 표면, surface 통제 수준, 고정 seed, 새 B1 wheel 빌드 환경·hash, 사람 사후 검수, 기존 wall-clock 문구의 Plan상 의미는 미확정이다.

## Benchmark Runner 재심사 반영과 설계 동결

### 재심사 결과

- 작업일: 2026-08-05.
- 재심사 보고서 `docs/reviews/benchmark-runner/claude-rereview-general-benchmark-runner-design.md`는 315줄, SHA-256 `4CDBCE89D01C069B8866F4A48550EC6F22D417295C9302D3CBC486E79FA0825C`다.
- 최종 판정은 `경미한 수정 후 동결`이었다.
- 1차 지적 18건은 `해결 18 / 부분 0 / 미해결 0 / 회귀 0`으로 판정됐다.
- 새 문제는 P2 3건, P3 2건이었고 P0·P1 이월 문제는 없었다.

### 동결 전 반영

- export에 Experiment 단위 `seals.json`을 추가해 내부 Cell 상태의 `sealed_measurement_sha256`과 저장소의 canonical Measurement를 대조할 수 있게 했다.
- B1 `_status()`와 `generate_report()`의 평범한 dict를 `RunStatusEnvelope`, `RunReportEnvelope` Pydantic 공개 계약으로 승격하고 Schema를 `export_schemas.py`에서 생성하도록 R2를 구체화했다.
- B1 usage의 session 층(`measured|unknown|unsupported`)과 report 집계 층(`measured|partial_or_unknown`)을 분리했다. core 총합은 report만 사용하고 session 값과 subtotal은 variant namespace에 보존하며 `unsupported`는 core unknown으로 취급한다.
- B0 attestation 부재·거부는 미봉인 상태로 남기지 않고 `measurement_attestation_missing` infrastructure error로 봉인한 뒤 Experiment를 중단한다.
- 유효한 preflight Evidence hash와 동결 Plan fingerprint 일치가 없으면 workspace 준비와 Cell 상태 전이를 시작하지 못하게 했다.
- 관련 요구를 §24 R2·R3·R5, §25 계약·Adapter·상태 시험, Definition of Done 21·22까지 연결했다.

### 동결 상태

- `docs/design/general-benchmark-runner-design.md`의 상태를 `동결(freeze)`, 설계 판본 3, 동결일 2026-08-05로 확정했다.
- 최종 동결본은 1,663줄, SHA-256 `47CDFAFC2C51876C966047E56A285A60AE4A954DC1463C20064898BE22ABAE73`이다.
- §27의 model/reasoning 확인 경로, surface 통제 수준, seed, 새 B1 wheel 환경·hash, 사람 사후 검수, wall-clock 의미는 설계 누락이 아니라 첫 Cell 전 증거로 채울 Execution Plan 입력값이라 계속 `미확정`으로 남겼다.
- 다음 구현 단계는 §24 R0의 실제 모델 호출 없는 단일 Fake Cell vertical slice다.

### 변경 제한과 검증

- 두 Claude 심사 보고서는 수정하지 않았다. 1차 심사 SHA-256은 `5799469A1EC56DBBCD440AFEE949EF895DA6BA5F1F88F2FD08CC63B3455D0502`, 재심사는 위 hash와 일치한다.
- `benchmarks/**`, `stages/**`, Runner 구현 코드는 수정하지 않았다.
- 이 동결 작업에서 실제 모델 turn은 0회다.
- 동결본과 인덱스의 로컬 링크, UTF-8 읽기, trailing whitespace, Markdown code fence, Git diff whitespace를 최종 점검한다.

## Benchmark Runner R0 Fake vertical slice 구현

### 구현 범위

- 작업일: 2026-08-05.
- 동결 설계 §24 R0만 구현했다. 실제 fixture 복원, B0/B1 Adapter, controller lock, retry, 비교 summary, Git export는 구현하지 않았다.
- `tools/benchmark-runner/`에 Python 3.12·Pydantic 기반 독립 패키지와 `lao-bench` CLI를 추가했다.
- 공개 계약은 `execution-plan`, `measurement`, `intervention-event` 세 Schema이며 Pydantic 모델에서 결정론적으로 생성한다.
- 한 개의 read-only Fake Cell이 `PLANNED → PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED`를 통과한다.
- Fake Adapter는 모델·도구를 호출하지 않고 `model_turns=0` Evidence를 반환한다. Stub Judge는 completed를 통과, requested failure를 실패로 판정한다.
- 성공과 실패 모두 canonical Measurement와 Evidence hash를 가진 `SEALED` 결과로 남는다. `SEALED`는 성공과 동일하지 않다.

### 계약과 안전성

- `MetricValue`는 measured zero와 unknown을 구분하며 `unknown|not_applicable`에 값을 넣는 것을 거부한다.
- Evidence 경로는 정규화된 POSIX 상대 경로만 허용하고 절대 경로, `..`, Windows 역슬래시, symlink를 거부한다.
- Cell 상태와 Measurement는 같은 디렉터리의 임시 파일에 `fsync` 후 `os.replace`하는 원자적 write를 사용한다.
- Measurement는 자기 자신을 Evidence 목록에 넣지 않고, Cell 상태의 `sealed_measurement_sha256`으로 canonical bytes를 봉인한다.
- 동일 Experiment ID가 이미 있으면 기존 실행을 덮어쓰지 않는다.

### 구현 중 발견한 계약 오류

- §8.1 공통 envelope의 `kind`와 §8.7 Intervention Event 예시의 `kind=correction`이 동일 필드에 두 의미를 요구하는 충돌을 발견했다.
- `kind=intervention_event`, `intervention_kind=correction|...`으로 분리하고 설계 판본 4를 다시 동결했다.
- 증상·근본 원인·검토 대안·해결·회귀시험은 `DEV-20260805-004`에 기록했다.
- 판본 4 설계는 1,672줄, SHA-256 `841EACEF0C2FE81D72E0702371AF7B4CBEB62D6703431C54C92BE8D220D2030F`다.

### 검증

- B1 가상환경의 Python 3.12.10, Pydantic 2.13.4, pytest 8.4.2를 사용했다.
- 계약·Schema 동기화·Plan fingerprint·CLI·상태 전이·성공/실패 봉인·Evidence 변조·Measurement 변조·중복 실행 거부 시험 18개가 통과했다.
- 별도 임시 state root에서 실제 CLI 관통을 실행해 Cell `SEALED`, outcome `completed`, check success, `model_turns=0`을 확인하고 `r0 verify`로 재검증했다. 임시 결과는 검증 후 삭제했다.
- 실제 Codex·OpenAI 모델 turn은 0회다.
- 구현 오류 로그 6개 원본의 validation·render 일치 검사가 통과했고 하네스 자체 단위시험 10개도 통과했다.

### 크기와 미확인

- `src/benchmark_runner`는 Python 파일 8개, 물리 964줄·공백/주석 제외 795줄이다. 설계의 약 600줄 목표보다 크지만 공개 Schema 3개의 전체 필드와 명시적 Measurement 조립을 포함하며 R1 이후 기능은 넣지 않았다. R1 확장 전에 불필요한 중복을 다시 감사한다.
- editable install과 wheel 빌드는 실행하지 않았다. 현재 검증은 `src`를 직접 import했으며 packaging artifact 고정은 R6 범위다.
- R0는 실제 fixture·Judge·B0/B1 효율성을 증명하지 않는다. 다음 단계는 R1 fixture 복원과 독립 Judge다.

## Benchmark Runner R0 감사와 R1 착수 명세 보강

### R0 계약 수정

- 작업일: 2026-08-05.
- `ExecutionPlan`이 fixture·variant·baseline·candidate·Cell 교차참조를 검증하도록 보강했다.
- 새 검사가 기존 Plan의 Variant artifact `r0-fake`와 Cell·Adapter `fake` 불일치를 발견해 정식 Variant ID를 `fake`로 통일했다.
- Pydantic `frozen=True`가 중첩 dict mutation까지 막지 않는 한계를 숨기지 않고, Plan 생성 직후·Cell 실행 직전·봉인 검증 시 canonical fingerprint와 Experiment ID를 재검산해 변경된 Plan을 거부한다.
- 봉인 검증은 Plan 자체의 무결성, Cell 선언 존재, Measurement identity와 manifest hash 일치까지 확인한다.
- 회귀시험은 18개에서 23개로 늘었고 전부 통과했다. 실제 모델 turn은 0회다.

### R1 명세 수정

- 두 동결 fixture의 source commit과 manifest tree를 직접 대조했고 모두 일치했다.
- 복원한 baseline acceptance는 두 fixture 모두 exit 1이었다. 이는 결함이 아니라 아직 과제를 풀지 않은 출발점의 의도된 상태다.
- 기존 “두 fixture 원본에서 통과”를 baseline 복원/의도적 실패, hash가 고정된 test-only golden positive, Check 변조·scope 위반·tree 불일치 negative로 분리했다.
- write scope v1은 exact POSIX file과 `<directory>/**` 두 형태만 허용한다.
- Python Judge는 `PYTHONDONTWRITEBYTECODE=1`을 강제한다. 미설정 재현에서는 `benchmark_checks/__pycache__`, `src/__pycache__`가 생성됐고 설정 시 Judge 뒤 worktree가 clean이었다.
- Judge stream은 각 1 MiB만 보존하되 전체 크기·SHA-256·잘림 여부를 기록하고, timeout process group 종료 grace는 5초로 고정했다.
- YAML loader는 R1 구현 시 `PyYAML>=6,<7`과 `safe_load`, `extra=forbid` 내부 계약을 함께 추가한다. 아직 R1 코드는 구현하지 않았다.

### 기록과 동결

- `DEV-20260805-005`: Execution Plan 교차참조와 fingerprint 경계 검증 누락.
- `DEV-20260805-006`: R1 baseline 통과 조건 모순과 Python Check workspace 부작용.
- Benchmark Runner 설계 판본 5를 다시 동결했다.
- 판본 5는 1,710줄, SHA-256 `A6E6789DA54C9A314C1551FE71B8F1424ED2A86E64A8E8A50D8AF7540E924B85`다.
- 다른 세션이 소유한 tradition·Claude skill·handoff 경로는 읽거나 수정하지 않았다.

## Benchmark Runner R1 fixture 복원·독립 Judge 구현

### 구현 범위

- 작업일: 2026-08-05.
- 동결 manifest를 `PyYAML safe_load`와 `extra=forbid` Pydantic 계약으로 읽고, source commit의 fixture tree를 검증한 뒤 `git archive`에서 Cell별 clean Git worktree를 만든다.
- archive 추출은 절대 경로·`..`·역슬래시·중복·대소문자 충돌·symlink·hardlink·특수 항목을 거부한다.
- write scope는 exact POSIX 상대 파일과 `<directory>/**`만 허용한다. Check 실행 전에 changed path, symlink component, `.orchestrator/checks.yaml`과 `benchmark_checks/**` 보호 hash를 검사한다.
- acceptance와 `diff_check`를 Variant 외부의 같은 Judge가 순서대로 실행한다. `python`과 `git`은 preflight에서 받은 절대 executable로 치환하고 shell은 사용하지 않는다.
- Check는 별도 process group에서 실행한다. timeout이면 협조 종료와 grace 뒤 group 강제 종료를 수행한다.
- stdout/stderr는 stream별 1 MiB까지만 파일에 보존하지만 전체 bytes를 끝까지 읽어 전체 크기·SHA-256·잘림 여부를 결과에 남긴다.
- Judge는 `result.json`, Check별 stdout/stderr, `final.diff`, baseline/final tree를 Evidence로 남긴다.

### baseline·positive·negative 검증

- 두 동결 fixture는 source commit에서 manifest tree와 동일하게 복원됐고 최초 worktree가 clean이었다.
- 두 baseline은 과제를 아직 풀지 않은 상태이므로 acceptance 실패·diff 통과로 정확히 판정됐다.
- 저장소 밖 실험 입력을 바꾸지 않도록 test-only golden patch 두 개를 별도로 만들고 LF bytes와 SHA-256을 고정했다. 두 patch는 허용 scope 안에서 acceptance·diff를 모두 통과했다.
- Check 변조와 scope 위반은 Check command 실행 전에 실패했다. manifest source tree 불일치, archive traversal, symlink도 복원 단계에서 거부됐다.
- Python Check 뒤 `__pycache__` 등 Judge 자체 worktree 변경은 없었다. final diff hash와 저장된 `result.json`의 재파싱 일치도 확인했다.

### 구현 중 오류와 해결

- `DEV-20260805-007`: 정상 `git archive`가 포함하는 fixture 상위 디렉터리를 경로 탈출로 오판했다. prefix의 조상은 디렉터리 항목일 때만 허용하고 내용 생성 없이 건너뛰도록 수정했다.
- `DEV-20260805-008`: Windows의 비강제 `taskkill /T`가 timeout process group을 실제 종료하지 않았다. `CTRL_BREAK_EVENT → grace → taskkill /T /F → 최후 parent kill`과 종료 확인 순서로 수정했다.
- `DEV-20260805-009`: Git rename의 destination만 검사해 범위 밖 source 삭제를 놓칠 수 있었다. rename은 source와 destination 모두, copy는 destination만 검사하도록 수정했다.
- `DEV-20260805-010`: Check 전후 changed path 목록만 비교해 같은 파일의 내용 변조를 놓칠 수 있었다. 경로 목록과 실제 Git tree를 함께 비교하도록 수정했다.
- 네 오류 모두 재현 절차·근본 원인·대안·회귀시험을 구현 오류 로그 JSON과 자동 생성 index에 기록했다.

### 검증과 경계

- 전체 Benchmark Runner 회귀시험 48개가 통과했다. R0의 계약·Plan·CLI·봉인 시험을 포함하므로 R1 추가로 기존 vertical slice가 깨지지 않았음을 함께 확인했다.
- R1 구현과 시험에서 실제 Codex·OpenAI 모델 turn은 0회다.
- R1 구성요소는 아직 CLI/Cell 상태기계와 연결하지 않았다. B0/B1 실제 효율성이나 세션 자동화 성공을 증명하지 않으며, 다음 단계 R2가 B1 FakeRuntime으로 `fixture → run → Judge → seal`을 연결한다.
- 다른 세션이 소유한 tradition·Claude skill·handoff 경로는 수정하지 않았다.

## Benchmark Runner R2 1~3단계 정상 관통

### B1 공개 계약

- 작업일: 2026-08-05.
- 기존 dict 출력인 `run status`와 JSON report를 `RunStatusEnvelope`, `RunReportEnvelope` Pydantic 공개 계약으로 승격했다.
- `run-status.schema.json`, `run-report.schema.json`은 `scripts/export_schemas.py`가 같은 모델에서 생성한다. CLI 실제 JSON과 모델·checked-in Schema의 동기화 시험을 추가했다.
- status는 session별 `measured|unknown|unsupported`를 공개한다. report 집계는 `measured|partial_or_unknown`을 사용하며, 후자의 정수 token 값은 불완전한 부분합이라는 의미를 Schema 설명에 명시했다.

### B1SequentialAdapter

- Runner는 B1 내부 모듈과 SQLite를 import하지 않고 `lao` CLI argv와 공개 JSON Schema만 사용한다.
- Cell 전용 `LAO_STATE_ROOT`, Run Spec validate, CLI 실행, status·report·integrity 수집을 구현했다.
- stdout/stderr는 임시 파일로 받아 메모리 사용을 제한하고, 각 1 MiB만 보존하면서 전체 byte 수·SHA-256·잘림 여부를 기록한다.
- report 집계가 `measured`일 때만 core token usage를 측정값으로 사용한다. 원래 subtotal과 session usage 상태는 B1 variant namespace에 보존한다.

### FakeRuntime 전체 관통

- 두 동결 fixture 모두 `source commit 복원 → B1 FakeRuntime → B1 내부 Check → Runner 독립 Judge → canonical Measurement → SEALED`를 통과했다.
- Measurement Evidence에는 공개 Adapter 결과, FakeRuntime 시험 입력, Judge 결과·stdout/stderr·final diff를 포함했다. B1 내부 SQLite와 variant state는 Evidence에서 제외했다.
- B1 source·공개 Schema·Project Pack과 Runner source를 각각 결정론적으로 fingerprint해 Execution Plan과 Measurement provenance에 기록했다.
- B1 runtime turn은 1회지만 실제 Codex·OpenAI 모델 turn은 0회이며, 두 값을 혼동하지 않도록 variant metrics에 `actual_model_turns=0`을 별도로 기록했다.

### 검증 범위와 미완료

- B1 전체 단위·계약·통합 시험 63개가 통과했다.
- Benchmark Runner 전체 시험 53개가 통과했다. 이 중 R2 신규 정상 관통 시험은 Adapter 3개와 seal 2개다.
- R2 전체 완료 판정은 아직 아니다. schema 불일치, exit 130, exit 0 nonterminal, `partial_or_unknown` subtotal을 core measured로 승격하지 않는 실패 주입 시험은 사용자가 지정한 다음 단계 4에 남겼다.
- 실제 Codex 실행, B0 연결, B0/B1 비교 실험은 수행하지 않았다.

## Benchmark Runner R2 실패 주입 검증·완료

### Adapter 오류 경로

- 작업일: 2026-08-05.
- `run start` exit 130은 공개 JSON이 없어도 `interrupted`로 분류하고 `b1_interrupted` stop reason을 남긴다.
- exit 5·6·7은 각각 integrity failure·controller lock·runtime failure, 그 밖의 코드는 unknown exit infrastructure error로 분류한다.
- exit 0·3·4만 status 공개 Schema를 검증하고, exit code와 terminal state 또는 후속 status exit가 불일치하면 `b1_exit_state_mismatch`로 중단한다.
- CLI process 시작 자체 실패, malformed JSON, Run ID 누락, unknown field, report Schema 누락, Run ID 변경은 모두 구분 가능한 Evidence를 가진 infrastructure error로 정규화한다.
- 이 과정에서 발견한 “terminal exit보다 JSON parse를 먼저 수행한 결함”은 `DEV-20260805-011`에 원인·대안·해결·회귀시험을 기록했다.

### Usage 불변식

- report `usage_status=partial_or_unknown`이면 subtotal이 모두 0이어도 core token usage는 `unknown`, 값은 `null`로 봉인한다.
- subtotal 정수 dict는 `b1_token_usage_raw`, report 집계 상태는 `b1_report_usage_status`, session의 `unsupported`는 `b1_session_usage_statuses`에 원형 보존한다.
- 실제 R2 Cell 관통 시험에서도 unknown usage FakeRuntime 결과가 독립 Judge를 통과한 뒤 위 형식의 canonical Measurement로 봉인됨을 확인했다.

### R2 완료 판정

- B1 전체 단위·계약·통합 시험 63개가 통과했다.
- Benchmark Runner 전체 시험 68개가 통과했다. R2 실패 주입은 Adapter 14개와 unknown usage Measurement 관통 1개를 추가한다.
- Pydantic source에서 생성한 B1 Schema와 실제 CLI 출력의 동기화, Runner의 독립 Schema 재검증, 두 fixture 정상 seal, terminal·Schema·usage 실패 분류가 모두 통과했다.
- B1 source fingerprint가 Execution Plan Variant artifact와 Measurement provenance에 동일하게 기록되는 것도 확인했다.
- 따라서 동결 설계 §24 R2의 완료 조건을 충족한 것으로 판정한다. 다음 구현 단계는 R3 B0 Manual Adapter다.
- 실제 Codex·OpenAI 모델 turn은 0회다.

## Benchmark Runner R3 B0 Manual Adapter 구현

### 수동 세션 측정 sidecar

- 작업일: 2026-08-05.
- Runner는 B0 Codex 세션을 자동 실행하거나 UI를 조작하지 않는다. Cell별 독립 workspace와 고정 prompt를 제공하고, 별도 세션을 운영하는 사용자의 동작만 Event sidecar로 기록한다.
- console input loop와 주입 가능한 `B0ManualInputProvider` 경계를 구현했다. 시험에서는 Fake provider가 같은 경계를 사용해 workspace 변경과 사용자 입력을 결정론적으로 재현한다.
- Intervention Event는 발생 즉시 append-only JSONL로 fsync한다. Cell ID·Event ID·monotonic 순서·B0/B1 kind 경계·단일 최초 prompt·최종 abort·복구 구간의 중첩과 완전성을 검증한다.
- 최초 prompt는 `startup_action_count=1`, 추가 prompt·correction·manual retry만 excluding-start 중계로 계산한다. turn은 모델에 전달된 prompt 수, session은 최초 1개와 replacement, attempt는 최초 1회와 manual retry로 파생한다.
- 기존 R2 B1 경로도 CLI 시작 직전에 `b1_start` Event를 남기고 startup 1·excluding-start 0·including-start 1로 봉인하도록 연결해 양쪽의 최초 기동 비용을 대칭 계수한다.

### attestation·Judge·중단

- 봉인 전 사용자가 Event 누락 없음과 model·reasoning·surface 값을 확인해야 한다. 확인된 Event에서만 사람 부담·session·turn·attempt 값을 Core Measurement에 `derived`로 기록한다.
- attestation이 없거나 거부되면 `measurement_attestation_missing`, B0에서 허용되지 않는 Event나 미종료 복구 구간은 `measurement_event_invalid` infrastructure error가 된다. 계산 가능한 값이 있어도 불완전할 수 있으므로 Core 값은 `unknown`으로 봉인한다.
- 실패 Cell도 가능한 Evidence와 독립 Judge 결과를 보존하고 `SEALED`로 닫는다. 동시에 Experiment 루트의 `experiment-stop.json`에 Cell과 stop reason을 기록해 다음 Cell 진행 금지를 표시한다.
- B0 작업자의 완료 선언과 관계없이 기존 FixtureJudge가 acceptance·scope·보호 hash·final tree를 독립 판정한다. token usage를 실제 runtime에서 받지 못하는 B0는 0이 아닌 `unknown`이다.
- 사용자가 완료를 확인했어도 독립 Judge가 실패하면 `independent_judge_failed`로 Experiment stop을 남긴다.

### 검증과 경계

- Fake 사용자 정상 경로는 `code-change`, `document-read` 두 fixture 모두 `restore → manual sidecar → Judge → Measurement → SEALED`를 통과했다.
- startup 1, excluding-start 3, including-start 4, turn 4, session 2, attempt 2, recovery 1의 파생값을 Measurement에서 확인했다.
- attestation 누락·명시적 거부, B0 timeline의 `b1_start`, 미종료 recovery를 각각 봉인·Experiment stop까지 fault injection했다.
- Benchmark Runner 전체 회귀시험 75개와 B1 전체 시험 63개가 통과했다. 구현 오류 로그 14개 검증과 하네스 단위시험 10개도 통과했다.
- R3 대조 중 발견한 B1 startup 지표 누락은 `DEV-20260805-012`에 원인·대안·수정·회귀시험을 기록했다.
- R3 시험에서 실제 Codex·OpenAI 모델 turn은 0회다. console provider는 구현됐지만 실제 사용자 B0 반복 실험은 하지 않았다.
- 다음 단계는 R4 Execution Plan controller, 한 번에 한 Cell 실행, lock·stop/resume·crash recovery다.

## Benchmark Runner R4 Execution Controller·crash recovery 구현

### 12-Cell Plan과 preflight

- 작업일: 2026-08-05.
- 동결 manifest의 fixture 2개·repetition 3회·B0/B1 두 Variant를 정확히 12개 Cell과 6개 Block으로 확장한다. 고정 seed로 B0-first와 B1-first를 각각 3 Block으로 균형화하고 ordinal 1~12를 Plan fingerprint에 고정한다.
- manifest factory는 exact manifest hash, fixture commit/tree, Runner·B0·B1 artifact hash, baseline/candidate, seed, decision policy, reasoning control, model/auth/surface fingerprint를 입력으로 canonical Plan을 만든다. 아직 정하지 않은 실험값을 추측하지 않고 호출자가 명시해야 한다.
- preflight는 controller lock 아래 manifest bytes·fixture source tree·Python 3.12·Git·artifact hash·driver capability·disk·model/auth 사전확인 Evidence를 검사한다. 실제 model turn은 0회이며 Evidence hash와 Plan fingerprint를 control record에 함께 기록한다.
- preflight Evidence가 없거나 한 byte라도 변조됐거나 artifact hash가 달라지면 Cell workspace 준비와 상태 전이를 시작하지 않는다.

### 한 Cell 실행과 중단·재개

- `run_next`는 Plan ordinal상 다음 Cell 하나만 `PLANNED → PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED`로 진행한다. 같은 명령에서 다음 Cell을 자동 시작하지 않는다.
- manifest의 `task_timeout_seconds=900`을 Cell driver 호출 경계에 전달한다. 실제 deadline 집행은 B0/B1별 실행 경계를 소유한 driver 책임이며, controller가 별도 Runner retry를 만들지 않는다.
- 설명되지 않은 실패는 control record의 `stop_reason`으로 남긴다. resume은 기존 reason·결정·결정자·시각·근거를 `stop_history`에 append한 뒤에만 reason을 해제한다.
- Runner/Variant artifact가 달라지면 같은 revision 재개를 거부하고 `artifact_fingerprint_changed`로 중단한다. 기존 Experiment는 `superseded_by`를 기록한 뒤 다시 실행할 수 없다.

### lock과 crash recovery

- Experiment lock은 exclusive create로 획득하고 controller ID·PID·hostname·획득 시각·Runner version·process start identity를 저장한다. 살아 있는 같은 프로세스의 lock은 확인 flag가 있어도 해제할 수 없다.
- 죽은 PID·PID 재사용·다른 host의 stale lock은 `confirm_no_controller`를 명시한 경우에만 제거하고 lifecycle Event를 남긴다.
- 재시작 시 `ACTIVE` Cell은 Variant를 호출하지 않고 `STOPPED`로 전환한다. terminal capture가 실제로 존재하는 경우 사용자가 이를 확인한 뒤에만 `STOPPED → CAPTURED`가 가능하다.
- `PREPARED`는 같은 Cell을 안전하게 시작할 수 있고, `CAPTURED`는 Variant 재호출 없이 Judge만 실행한다. `JUDGING`은 기록된 이전 Judge process group을 종료·검증한 뒤 Judge만 재개한다. `SEALED` 결과는 변경하지 않는다.
- PREPARED·ACTIVE·CAPTURED·JUDGING·SEALED 상태 write의 직전과 직후 10개 경계에 crash를 주입했다. 특히 ACTIVE 직후와 Variant capture 직후 crash 모두 자동 Variant 재호출 0회를 확인했다.

### Judge process 복구 오류와 검증

- Judge Check마다 PID·process start identity·process group 종류·상태를 `active-process.json`에 원자적으로 기록한다. 정상 종료도 terminal record로 바꾼다.
- Windows 관리 환경에서 `taskkill /T /F`가 Access denied를 반환하고 범용 PID probe가 종료 프로세스를 살아 있다고 오판한 문제를 발견했다. `DEV-20260805-013`에 원인·대안·해결·잔여 위험을 기록했다.
- 복구는 종료 전 Toolhelp snapshot으로 후손 PID를 고정하고 Windows process group에 CTRL_BREAK_EVENT를 먼저 보낸 뒤 taskkill·WinAPI TerminateProcess fallback과 GetExitCodeProcess로 부모·자식의 실제 종료를 확인한다. 단일 통과 뒤 전체 회귀에서 자식 생존이 한 차례 재검출돼 보강했으며, 보강 시험은 5회 연속 통과했다.
- 전체 회귀에서 `active-process.json` 원자 교체가 Windows의 일시적 공유 잠금으로 한 차례 실패했다. 원자성을 깨는 선삭제 대신 Windows PermissionError만 200ms 이내 bounded retry하고 지속 오류는 그대로 실패시키며, `DEV-20260805-014`에 기록했다.
- Benchmark Runner 전체 pytest 101개와 B1 전체 pytest 63개가 통과했다. 구현 오류 로그 16개와 하네스 단위시험 10개도 검증했다.
- R4 시험에서 실제 Codex·OpenAI model turn은 0회다. generic Fake driver로 상태·복구 계약을 검증했으며 실제 B0/B1 12-Cell 비교는 실행하지 않았다.
- 다음 단계는 R5 paired summary·판정·sanitized export다. 실제 비교 실행은 R6 artifact·환경 동결 뒤에만 시작한다.

## Benchmark Runner R5 비교·판정·sanitized export 구현

### 결정론적 paired summary와 판정

- 작업일: 2026-08-05.
- 12개 봉인 Measurement를 Execution Plan의 6개 Block으로 짝지어 Cell 원자료·pair delta·Variant 전체 집계·execution ordinal 추세를 같은 `summary.json`에 결정론적으로 만든다. 실패·중단·unknown Cell은 `cell_results`와 outcome count에서 빠지지 않는다.
- 첫 B0/B1 정책을 `b0-b1-v1`로 명명하고 Plan `decision_policy`와 정확히 일치할 때만 분석한다. fixture별 Judge 성공 비열등, B1 사람 사후 오류 비증가, 시작 제외 사람 중계 전체 합의 엄격한 감소, 수동 복구 시간 비증가를 gate로 고정했다.
- 중계 합 동률, 필수 지표 unknown, blocked·interrupted·timeout·infrastructure error, baseline 무결성 실패는 `INCONCLUSIVE`다. B1 품질 하락·사람 부담 악화·B1 무결성 실패는 `REJECT_B1`, 모든 gate 통과만 `ADOPT_B1`이다.
- B0와 B1이 모두 Judge 성공 0건인데 단순 비열등만으로 채택되는 것을 막기 위해 B1 Judge 성공 최소 1건을 사전 정책에 추가했다. 실제 첫 Cell 전 Plan fingerprint에 들어가므로 결과를 본 뒤 바꿀 수 없다.
- fixture별 사람 중계 median 악화는 전체 합 gate와 별개 경고로 남긴다. `treatment_control`이 전부 `full`이 아니면 오케스트레이션 하나의 인과효과가 아니라 실제 workflow 비교라는 한계를 JSON과 Markdown에 함께 기록한다.

### 봉인 export와 독립 검증

- `compare`, `export`, `verify-export` CLI를 추가했다. analysis hash는 canonical `summary.json` bytes에 고정되고 같은 입력의 JSON·Markdown은 byte-identical이다.
- 각 Cell의 canonical Measurement bytes와 그 Evidence를 `benchmarks/results/<variant>/<experiment>/<cell>/` 형태로 내보내고, 내부 Cell state의 Measurement hash·SEALED 시각을 Cell ID 순 `seals.json`에 기록한다.
- 독립 verifier는 export만으로 Plan fingerprint, 12개 Measurement hash, 각 Evidence size/hash, Measurement identity, summary 재계산 결과와 exact file set을 다시 확인한다. Measurement 한 byte 수정과 예상 밖 파일 추가를 모두 거부한다.
- 기존 export가 완전히 같으면 멱등 성공하고, 한 파일이라도 다르거나 추가되면 덮어쓰지 않는다. export tree 전체는 상대 경로·크기·file hash로 다시 hash해 control record의 `export_sha256`에 기록한다.
- 봉인 뒤 redaction은 원래 Measurement seal을 깨므로 R5는 bytes를 사후 변경하지 않는다. Adapter/Collector가 봉인 전에 공개 Evidence를 redaction하며, R5가 token 형태·email·홈 절대 경로·`auth.json`·금지 artifact를 찾으면 fail-closed로 export를 중단하고 새 revision을 요구한다.

### 오류와 검증

- JSON Evidence 안의 Windows 경로가 이중 백슬래시로 직렬화되면 홈 경로 탐지를 우회한 결함을 보안 시험에서 발견했다. 원본 hash를 바꾸지 않고 검사 입력만 실제 문자열 형태로 정규화했으며 `DEV-20260805-015`에 재현·원인·대안·회귀시험을 기록했다.
- UTF-8이 아닌 binary Evidence도 ASCII로 남은 token 형태 문자열은 검사하도록 보강했다. 압축·암호화되거나 미지 패턴인 비밀은 봉인 전 공개 Evidence에서 제외해야 한다.
- R5 전용 시험 19개와 Benchmark Runner 전체 회귀시험 120개, B1 전체 시험 63개, 구현 로그 17개 검증과 하네스 단위시험 10개가 통과했다.
- R5 구현과 시험에서 실제 Codex·OpenAI model turn은 0회다. 실제 B0/B1 결과가 없으므로 생성된 판정은 모두 합성 Measurement에 대한 계약 검증이며 B1 성능 결론이 아니다.
- 다음 단계는 R6에서 실제 driver·새 Runner/B1 artifact·환경·Execution Plan·decision policy·전체 비라이브 회귀 증거를 확정하고 첫 유료 Cell 직전 상태로 동결하는 것이다.

## Benchmark Runner R6 실제 실행 전 동결

### 실제 driver와 실행 경계

- 작업일: 2026-08-05.
- R4 controller에 실제 `R6B0ManualDriver`와 `R6B1SequentialDriver`를 연결했다. B0는 별도 Codex App 작업과 console Event sidecar를 사용하고, B1은 B1 내부 모듈을 import하지 않은 채 installed `lao` public CLI만 호출한다.
- Variant 전체를 별도 process group sidecar로 실행하고 manifest의 900초 deadline을 부모가 집행한다. timeout과 controller crash에서는 기록된 PID·process start identity를 대조해 process group을 회수하며 ACTIVE Variant를 자동 재호출하지 않는다.
- `r6 create`, `preflight`, `status`, `run-next`, `freeze` CLI를 추가했다. `run-next`는 `--confirm-model-usage`가 없으면 거부되므로 artifact 생성·preflight·동결이 실수로 유료 Cell을 시작하지 않는다.
- B1 공개 Schema 5개를 wheel에 포함하고 `lao schema export`로만 내보낸다. source checkout 밖의 임시 설치 환경에서 exact file set과 각 SHA-256을 확인했다.

### 재현 가능한 artifact와 Plan

- 최종 source commit은 `bef6f8e4b291d8724c8d78160d4559595cc0489c`다. Runner wheel SHA-256은 `6da66546d24aca56340d22a213c047859633f639474eb5eff09a46149e8171e1`, B1 wheel은 `596c98239491fdcb27e4cfc9afa00cbc020ea81830cb3bf1a67979e1023f367a`다.
- wheel 입력은 checkout bytes가 아니라 `git archive HEAD`의 blob snapshot이다. Plan과 fixture 복원은 `core.autocrlf=false`로 source commit을 detached checkout한 canonical local clone을 사용한다.
- 서로 다른 두 worktree와 local runtime 경로에서 build한 결과 Runner/B1 wheel hash, 공개 Schema 5개 hash, manifest SHA-256 `5633cb18…`, Plan fingerprint `d90cff38…`, Experiment ID `exp_20260805_d90cff38_1`이 모두 일치했다.
- 이전 `b188954`, `c413f66` bundle은 각각 preflight doctor 경계와 checkout 재현성 문제로 동결하지 않았으며 각 `NOT-FROZEN.md`에 사유를 남겼다. 최종 후보는 `benchmarks/artifacts/r6-b0-b1-bef6f8e/`뿐이다.

### 비라이브 회귀와 preflight

- 최종 source에서 B1 pytest 65개, Benchmark Runner pytest 128개, 구현 오류 로그 23건 검증, 로그 하네스 단위시험 10개가 한 번에 통과했다. 전체 기록은 `nonlive-regression.json`에 있으며 actual model turn은 0회다.
- Python `3.12.10`, Git `2.54.0.windows.1`, Codex CLI/SDK `0.144.4`, ChatGPT 인증, runtime profile의 `gpt-5.6-terra`·reasoning `low`, 두 fixture source tree, artifact hash를 모델 호출 없이 확인했다.
- B1 doctor는 Cell workspace가 아니라 source commit에서 복원한 임시 standalone Git fixture에서 실행한다. preflight Evidence SHA-256은 `32da949980bea634944853a9a76106dbe5123a20757a0e9877a207afeb1546ea`다.
- 고정 seed는 `20260805`, baseline은 B0, candidate는 B1, decision policy는 `b0-b1-v1`이다. B0 App과 B1 CLI/SDK 표면 차이 때문에 `treatment_control=partial`이며 B0 model·reasoning은 각 Cell 시작 시 사용자 attestation으로 다시 확인한다.
- 동결 시점 상태는 `PREFLIGHTED`, 12개 Cell 전부 `PLANNED`, sealed 0, stop reason 없음이다. `pre-execution-freeze.json`은 actual model turn 0과 “아직 채택 판정 없음”을 명시한다.

### 구현 중 발견한 경계 오류

- `DEV-20260805-016`: controller가 seal 뒤 lifecycle JSONL을 append해 Evidence hash가 달라지는 문제를 controller-owned lifecycle의 Measurement 제외로 해결했다.
- `DEV-20260805-017`: B1 source에만 있던 공개 Schema를 wheel bundle과 public export CLI로 승격했다.
- `DEV-20260805-018`: 한글 경로의 child JSON 출력에 UTF-8 환경을 명시했다.
- `DEV-20260805-019`: nested fixture를 직접 doctor하던 오류를 임시 standalone fixture doctor로 교체했다.
- `DEV-20260805-020`, `DEV-20260805-021`: checkout 줄바꿈에 따라 wheel hash와 Plan fingerprint가 달라지던 문제를 Git blob snapshot과 canonical source clone으로 닫았다.
- 이 단계는 B1이 B0보다 낫다는 결과가 아니다. 실제 12-Cell을 순서대로 실행하고 R5 policy가 봉인 결과를 분석해야만 `ADOPT_B1`, `REJECT_B1`, `INCONCLUSIVE` 중 하나를 낼 수 있다.

## R6 첫 라이브 실행 중단과 revision·대화형 입력 경계 보강

- 작업일: 2026-08-06.
- revision 1의 첫 B1 `code-change` Cell은 1 Attempt·1 Session·1 turn으로 Judge Check 2개를 통과해 봉인됐다. 측정값은 총 47.359초, 입력 86,194·출력 737 token이었다. 이 한 Cell만으로 B1 효율성 결론을 내리지 않는다.
- 다음 B0 Cell을 비대화형 명령 실행 환경에서 시작해 console sidecar의 `input()`이 EOF를 받았다. 모델 호출은 0회였지만 기존 구현은 이를 실행 전 환경 오류가 아니라 Cell 내부 infrastructure error로 봉인하고 Experiment를 중지했다.
- `r6 create --revision N`을 추가해 중단된 revision 1과 분리된 새 Plan·Experiment ID를 만들 수 있게 했다. artifact build harness에도 같은 인자를 전달한다.
- 다음 Cell이 `PLANNED/PREPARED` B0일 때 stdin이 TTY가 아니면 environment 수집·workspace 준비·상태 전이 전에 거부한다. B1 Cell과 crash/Judge 복구 경로에는 이 검사를 적용하지 않는다.
- revision 1의 로컬 runtime Evidence는 수정하거나 재사용하지 않는다. 수정된 Runner artifact와 전체 비라이브 회귀 결과로 revision 2를 새로 build·preflight·동결한 뒤 유료 비교를 재시작한다.

## R6 revision 2 재현 build 경계 보강

- 작업일: 2026-08-06.
- `2f4385d`에서 revision 2 wheel·runtime·Plan을 만들고 비라이브 회귀와 preflight까지 통과했으나, 독립 clean clone에서 다시 build한 wheel hash와 Plan fingerprint가 일치하지 않았다. 이 첫 bundle은 실행하지 않고 폐기 대상으로 분류했다.
- 두 build의 source commit은 같았지만 첫 저장소는 `core.autocrlf=true`, canonical clone은 `false`였다. 같은 HEAD의 `git archive` SHA가 달랐고, 명령에 `-c core.autocrlf=false`를 붙이면 두 archive SHA가 일치했다.
- build harness가 `git -c core.autocrlf=false archive`를 사용하도록 수정했다. `core.autocrlf=true/false`인 두 독립 clone을 실제 생성해 archive bytes가 같은지 확인하는 회귀시험을 추가했다.
- 수정 뒤 Benchmark Runner 132개, B1 65개가 통과했다. 원인·대안·해결·잔여 위험은 `DEV-20260806-002`에 기록했다.
- 실제 모델 호출은 0회다. revision 2는 이 수정이 포함된 새 clean commit에서 wheel·runtime·회귀 기록·preflight·freeze를 처음부터 다시 생성한다.
- 최종 source commit은 `2c335005e40b9c5e7fe2ed4b00a6d85b2e442f9f`다. Runner wheel SHA-256은 `76510b064a3d9202e53f6d75d64351fbb638870645a0e9e66525360a8f05eacb`, B1 wheel은 `fa42d6f225c1b4bafc40e194b916ebf7399e5525a65b7d95a5c361e6901039b1`다.
- `core.autocrlf=true`인 현재 저장소와 `false`인 canonical clone에서 독립 build한 결과 wheel 2개, 공개 Schema 5개, Plan fingerprint `3b2f0a7b6abb210ea2eedb1dfb4068db9409e0fd030e7b85dee301b483b521af`, Experiment ID `exp_20260805_3b2f0a7b_2`가 모두 일치했다.
- 최종 비라이브 기록은 B1 65개, Benchmark Runner 132개, 구현 오류 로그 25건, 로그 하네스 10개 통과다. preflight Evidence SHA-256은 `b8c786b420c76f4edcfe1adb96cc0fd79dbdd88181ce6cd8c91a8c73d477c928`다.
- 최종 상태는 `PREFLIGHTED`, 12개 Cell 전부 `PLANNED`, sealed 0, workspace 0, stop reason 없음이다. `benchmarks/artifacts/r6-b0-b1-2c33500-r2/`를 revision 2 실행 후보로 동결했고 실제 model turn은 0회다.
- 동결 JSON이 Windows checkout에서 CRLF로 바뀌어 exact hash가 깨지지 않도록 `benchmarks/artifacts/**/*.json -text`, wheel `binary` 속성을 추가했다. `core.autocrlf=true`인 새 clone에서 bundle 7개가 byte-identical이고 Plan·회귀 기록·wheel 내부 SHA가 모두 유효함을 확인했으며 `DEV-20260806-003`에 기록했다.

## R6 revision 2 라이브 결과와 B0 제어 경계 재구성

- 작업일: 2026-08-06.
- revision 2의 첫 B1 `code-change` Cell은 `src/config.py`만 수정하고 독립 Judge를 통과했다. 1 Attempt·1 Session·1 turn, 총 wall clock 46.781초, 입력 86,074·출력 750 token이며 Cell은 정상 봉인됐다.
- 이어진 B0 Codex App 작업도 `src/config.py`만 수정하고 독립 Judge를 통과했다. 그러나 `run-next`가 workspace 준비와 동시에 시작한 900초 deadline이 먼저 끝났고, console 포커스에 의존한 `p/d/y` Event는 Sidecar에 전달되지 않았다.
- 따라서 B0는 `check_success=true`지만 `outcome.state=timed_out`, `failure_kind=b0_deadline_exceeded`, `event_count=0`, `measurement_trusted=false`로 봉인됐다. 코드 정답은 확인됐지만 시간·개입량 비교 자료는 무효이며 Experiment는 STOPPED다. revision 2는 수정하거나 이어서 실행하지 않는다.
- 원인은 두 경계의 결합이다. 첫째, `PLANNED → PREPARED → ACTIVE`가 한 `run-next` 호출 안에서 이어져 App 작업을 준비하는 시간도 deadline에 포함됐다. 둘째, Event 입력이 포커스를 가진 단일 console `input()`에만 연결돼 비대화형 제어자가 같은 측정 계약을 사용할 수 없었다.
- Controller에 `prepare_next`를 추가하고 R6 공개 CLI를 `b0-prepare → b0-start → b0-event → b0-complete`로 분리했다. `PREPARED`는 deadline을 시작하지 않으며 `b0-start`가 별도 Controller process에서 Cell을 `ACTIVE`로 만든 뒤에만 900초 측정을 시작한다.
- B0 Event는 Cell별 원자적 명령 파일로 전달한다. Runner가 시각과 연속 sequence를 생성하고 최초 prompt 누락·중복, recovery 순서 오류, terminal 뒤 추가 Event, attestation 없는 완료를 거부한다. 기존 B0 Adapter의 Event JSONL·파생 지표·독립 Judge·Measurement seal은 그대로 유지한다.
- 회귀시험은 준비 상태에서 deadline·process가 시작되지 않는 경로, Event 순서·중복·terminal 검증, 비대화형 파일 제어로 `PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED`를 관통하는 경로를 추가했다. Benchmark Runner 전체 pytest 136개가 통과했다.
- 증상·원인·검토 대안·해결·잔여 위험은 `DEV-20260806-004`에 기록했다. 수정된 source commit에서 revision 3 wheel·runtime·Plan·비라이브 회귀·preflight·freeze를 새로 생성하고 첫 B1/B0 쌍부터 다시 실행한다.

## R6 revision 3 재현 build와 실행 전 동결

- 작업일: 2026-08-06.
- B0 제어 경계 수정이 포함된 source commit은 `d6c4383e13497e91c2ef1a839c12b72986aaa2f1`다. Runner wheel SHA-256은 `739414b2841e195dbc09a3700c4c854a12a42dc4869938d4338c39e8b9509337`, B1 wheel은 `5b9f83da2f3fa7b23eb2e8aaf9742632c51d2dbf795be833485521b65401dddc`다.
- 비라이브 회귀는 Benchmark Runner 136개, B1 65개, 구현 오류 로그 27건, 로그 하네스 10개를 통과했다. 이 과정의 실제 model turn은 0회다.
- 현재 저장소와 독립 canonical source에서 각각 build했다. 두 build의 source commit, Runner/B1 wheel, 공개 Schema 5개, Experiment ID `exp_20260806_3ccb5c55_3`, Plan fingerprint `3ccb5c550e93b75762faa579e7f60a58bfd4821fa1ca2eca6ef34f94dcaa85bb`가 모두 일치했다.
- preflight Evidence SHA-256은 `cb3fc2aa4d8ae3c75d517815ed842cd1830b974ce0b737b11df6e90b709695a8`다. 동결 상태는 `PREFLIGHTED`, 12개 Cell 전부 `PLANNED`, sealed 0, stop reason 없음이며 실제 model turn은 0회다.
- `benchmarks/artifacts/r6-b0-b1-d6c4383-r3/`를 revision 3 실행 후보로 동결했다. revision 2의 runtime과 봉인 결과는 수정·재사용하지 않으며 revision 3의 첫 B1/B0 쌍부터 새로 실행한다.

## R6 revision 3 첫 비교 쌍과 Python bytecode 정규화

- 작업일: 2026-08-06.
- 첫 B1 `code-change` Cell은 독립 Judge를 통과했다. 1 Attempt·1 Session·1 turn, 총 45.609초, 입력 86,094·출력 819 token으로 정상 봉인됐다.
- 첫 B0 App task도 요구된 `src/config.py` 수정과 자체 unittest를 완료했다. 1 Attempt·1 Session·1 turn, 추가 중계 0회, 총 52.141초로 측정됐지만 자체 unittest가 만든 `benchmark_checks/__pycache__/*.pyc`가 보호 경로 write scope 위반으로 판정됐다.
- B1 sidecar는 `PYTHONDONTWRITEBYTECODE=1`을 상속하지만 별도 App task인 B0는 상속하지 않아 동일한 테스트 동작의 부산물 처리가 비대칭이었다. 따라서 revision 3의 B0 실패는 구현 품질 비교에 사용하지 않고 Experiment는 봉인된 STOPPED 상태로 보존한다.
- Judge가 Check 전에 Git 비추적 `__pycache__/*.pyc|*.pyo`만 제거하고 `normalized_transient_paths`에 기록하도록 보강했다. 다른 확장자, Git 추적 파일, symlink 경로는 제거하지 않고 기존 scope 위반으로 유지한다.
- 실제 unittest로 두 pyc를 생성한 golden positive case와 `__pycache__` 안의 일반 파일을 숨기지 않는 negative case를 회귀시험으로 추가했다. 원인·대안·해결·잔여 위험은 `DEV-20260806-005`에 기록했다.
- 수정 뒤 새 source commit에서 revision 4를 build·독립 재현·preflight·동결하고 첫 B1/B0 쌍부터 다시 실행한다. revision 3 runtime과 봉인 결과는 수정하거나 재사용하지 않는다.

## R6 revision 4 첫 build의 비라이브 회귀 환경 오류

- 작업일: 2026-08-06.
- bytecode 정규화 commit `8968d4e`에서 revision 4 artifact와 runtime을 만들었고 이 단계의 실제 model turn은 0회였다.
- 동결용 `run_r6_nonlive_regression.py`가 pytest 기본 공용 임시 폴더를 사용해, 이전 실행에서 접근 불가능해진 `%TEMP%/pytest-of-SSAFY`의 ACL 때문에 B1 47건과 Runner 110건이 setup 단계에서 실패했다. 같은 commit의 짧은 명시적 `--basetemp` 수동 회귀는 Runner 138개와 B1 65개가 통과했다.
- 스크립트가 실행별 짧은 `TemporaryDirectory` 아래 B1·Runner 전용 `--basetemp`를 쓰고 pytest cache provider를 끄도록 수정했다. 다른 실행의 공용 폴더를 삭제하거나 재사용하지 않는다.
- 원인·대안·해결·잔여 위험은 `DEV-20260806-006`에 기록했다. 실패한 `r6-b0-b1-8968d4e-r4` bundle과 외부 runtime은 실행 전 동결·모델 호출 전에 폐기하고, 수정 commit에서 revision 4를 처음부터 다시 생성한다.

## R6 revision 4 최종 재현 build와 실행 전 동결

- 작업일: 2026-08-06.
- 최종 source commit은 `825e00cf3d1fba073f382c99fbbaa85f44c01586`다. Runner wheel SHA-256은 `908eb97be2a17b08518e23509ade58315fe1ca6558d316cd718519386672c415`, B1 wheel은 `c51dd7d0cfbfc311d729e0271ca2a23ecf1925c0ee35cfc6962b4ce4d6ac488b`다.
- 동결용 비라이브 회귀는 B1 65개, Benchmark Runner 138개, 구현 오류 로그 29건, 로그 하네스 10개를 통과했다. 이 과정의 실제 model turn은 0회다.
- 현재 저장소와 독립 canonical source에서 각각 build했다. 두 build의 source commit, Runner/B1 wheel, 공개 Schema 5개, Experiment ID `exp_20260806_7ff7d501_4`, Plan fingerprint `7ff7d501c4d711dca0e20e31d9b598530accd61ebb79c8e58b3c1a739ce24575`가 모두 일치했다.
- preflight Evidence SHA-256은 `cbfde47ad8ea86486e60c0394706c6cc3b5628816faed2e1489d35de380576ec`다. 동결 상태는 `PREFLIGHTED`, 12개 Cell 전부 `PLANNED`, sealed 0, stop reason 없음이며 실제 model turn은 0회다.
- `benchmarks/artifacts/r6-b0-b1-825e00c-r4/`를 revision 4 실행 후보로 동결했다. revision 3과 이전 runtime·봉인 결과는 수정·재사용하지 않으며 revision 4의 첫 B1/B0 쌍부터 새로 실행한다.

## R6 revision 4 첫 유효 B1/B0 비교 쌍

- 작업일: 2026-08-06.
- `code-change` repetition 1의 B1과 B0가 모두 `src/config.py`만 결과 변경으로 남기고 독립 acceptance·diff Check를 통과해 정상 봉인됐다. Experiment stop reason은 없고 12개 중 2개 Cell이 `SEALED`, 다음 Cell은 `cell_document-read_1_b0`다.
- B1은 총 41.094초, Variant 40.562초, 1 Attempt·1 Session·1 turn, 시작 제외 중계 0회였다. token usage는 입력 85,736·출력 735·합계 86,471로 측정됐다.
- B0는 총 58.657초, Variant 58.047초, 1 Attempt·1 Session·1 turn, 시작 제외 중계 0회였다. Codex App 표면이 runtime usage를 제공하지 않아 token usage는 0이 아니라 `unknown`으로 봉인됐다.
- B0 자체 unittest가 만든 `benchmark_checks/__pycache__/test_acceptance.cpython-312.pyc`와 `src/__pycache__/config.cpython-312.pyc`는 새 Judge의 `normalized_transient_paths`에 기록된 뒤 제거됐다. scope 위반·실패 Check는 0건이므로 revision 3의 비대칭이 실제 라이브 경로에서 해소됐음을 확인했다.
- 이 한 쌍에서는 B1이 B0보다 17.563초 짧았지만 6개 사전 등록 Block 중 1개뿐이므로 B1 채택·기각 결론을 내리지 않는다. B0 App task 생성이 사용자 직접 조작이 아니라 현재 제어 세션을 통해 이뤄졌고 두 surface가 다르므로 `treatment_control=partial` 해석 한계도 유지한다.

## R6 revision 5 고정 프로젝트 build와 실행 전 동결

- 작업일: 2026-08-06.
- source commit은 `f96e7184d8edede7772aaa8f6eb0ee728d9d0032`다. B0 작업이 Cell마다 별도 프로젝트로 보이던 문제와 App 포커스 이동 문제를 해결한 `DEV-20260806-007`을 포함한다.
- B0 작업은 Codex App의 `AI 오케스트레이터 실험실` 프로젝트 아래 단일 `active-workspace` 슬롯에서만 실행한다. `background_thread_only` 정책으로 시작하며 `codex app` 실행이나 화면 이동 API를 호출하지 않는다. 별도 백그라운드 task로 확인했을 때 사용자가 다른 작업 중인 App 화면은 이동하지 않았다. `active-workspace`는 B0 준비 중에만 존재하고 봉인 뒤 해당 Cell 보존 경로로 이동한다.
- Runner wheel SHA-256은 `d2d3e1d207f5e5ffa53e2245d2c28565b07071cb275c4e156b49ad228eeafeed`, B1 wheel은 `005f7c1c884285b5835a69c142b152207d2f07e90160449f098868a29d3b99b5`다.
- 동결용 비라이브 회귀는 B1 65개, Benchmark Runner 138개, 구현 오류 로그 30건, 로그 하네스 10개를 통과했다. 이 build·회귀·preflight·freeze 과정의 실제 model turn은 0회다.
- 현재 저장소와 독립 canonical source에서 각각 build했다. 두 build의 source commit, Runner/B1 wheel, 공개 Schema 5개, Experiment ID `exp_20260806_bc754895_5`, Plan fingerprint `bc754895358a5248e74f7df37a45a97ada0833dc6de7450d16920cb3be567ede`가 모두 일치했다.
- preflight Evidence SHA-256은 `3be2c616655d7b29811645139862bf436ad83b50c802185dad6287f6926908d7`다. 동결 상태는 `PREFLIGHTED`, 12개 Cell 전부 `PLANNED`, sealed 0, stop reason 없음이며 다음 Cell은 `cell_code-change_1_b1`이다.
- 첫 freeze 시도는 생성 대상인 `execution-plan.json`을 작업자가 미리 artifact에 복사해 둔 순서 오류를 fail-closed로 거부했다. 중복 파일만 제거하고 다시 실행해 정상 동결했으며 Cell 상태와 model turn에는 변화가 없었다.
- `benchmarks/artifacts/r6-b0-b1-f96e718-r5/`를 revision 5 실행 후보로 동결했다. revision 4의 첫 유효 B1/B0 쌍은 원시 사실로 보존하지만, B0 실행 경계가 바뀌었으므로 후속 Cell을 이어서 실행하거나 revision 5 결과와 한 Experiment처럼 합치지 않는다.

## R6 revision 5 12-Cell 완료와 판정

- 작업일: 2026-08-06.
- `exp_20260806_bc754895_5`의 12개 Cell을 사전 등록 순서대로 모두 실행했다. B0와 B1 각각 6개가 모두 `completed`·Check 성공·scope 정상·비밀정보 0으로 봉인됐고 Experiment는 stop reason 없이 `COMPLETED`가 됐다.
- 모든 Cell은 1 Attempt·1 Session·1 turn이었다. 시작을 제외한 사람 중계와 수동 복구는 B0·B1 모두 총 0회였다. B0 App 표면이 token usage를 제공하지 않으므로 B0는 6개 모두 `unknown`으로 유지했고, B1의 측정 합계는 563,240 tokens다.
- 전체 시간은 B0 290.701초, B1 265.518초로 B1이 25.183초(8.66%) 짧았다. 코드 수정에서는 B0 164.452초, B1 124.705초로 B1이 24.17% 짧았고, 문서 읽기에서는 B0 126.249초, B1 140.813초로 B1이 11.54% 길었다. 시간은 보조 지표이며 채택 정책을 사후 변경하지 않았다.
- 사전 등록 정책 `b0-b1-v1`의 판정은 `INCONCLUSIVE`다. candidate·baseline 무결성, terminal Measurement, fixture별 품질 비열등, 최소 품질 증거, 복구 시간 비증가는 통과했다. 주 지표인 `manual_relay_reduction`은 B0와 B1이 모두 0회라 B1의 엄격한 감소를 증명할 수 없어 `inconclusive`가 됐다.
- 이 결과는 B1의 실패나 범용 우위를 뜻하지 않는다. 현재 제어 세션이 B0 task도 백그라운드로 직접 생성해 단순한 1-turn 과제에서는 기준선의 추가 중계가 이미 0이었고, 2 fixture × 3 repetition의 로컬 방향성 게이트이며 두 surface 차이 때문에 `treatment_control=partial`이다.
- export는 172개 파일이며 SHA-256은 `b64c262538e069b81fd9cacb2d1f033cef5149083171a4d62ec20cf6494e98b1`이다. `verify-export`로 12개 Measurement와 Evidence를 재검증했고 두 번째 export는 같은 해시로 `idempotent=true`였다.
- 실제 export 뒤 결과가 `.gitignore`에 걸리고 Git 바이트 보존 속성이 없던 오류를 발견했다. `DEV-20260806-008`로 기록하고 results 무시 규칙 제거, `benchmarks/results/** -text -whitespace`, 추적 가능성·원시 Evidence 공백 허용 회귀시험을 추가했다. 짧은 독립 basetemp에서 Benchmark Runner 139개와 구현 로그 하네스 10개가 통과했고 export 해시는 수정 전후 동일했다.

## F1 순차 오케스트레이션 효용 후속 실험 준비

- 작업일: 2026-08-06.
- 선행 12-Cell은 단일 Task·단일 turn 과제라 B0와 B1의 시작 이후 사람 중계가 모두 0회였다. 판정식을 사후 변경하지 않고 `INCONCLUSIVE`를 유지하며, B1의 Task 의존성 자동 진행을 직접 시험하는 별도 F1 계획을 `docs/experiments/b1-sequential-value-followup.md`에 정의했다.
- F1의 B0는 같은 Codex 작업에서 T1 완료 뒤 사용자가 고정 T2 prompt를 전달하는 수동 순차 운영이고, B1은 동일한 `depends_on` 계약을 자동 진행한다. 이 비교는 모든 개발 방식의 우위를 주장하지 않고 Task 단위 순차 workflow 안의 중계 자동화만 측정한다.
- `sequential-code-change`와 `sequential-document` fixture를 추가했다. 두 fixture 모두 T1 산출물이 T2 입력이 되며 Task별 write scope와 Check가 분리된다.
- pristine 실패, T1 golden 적용 뒤 1단계 Check 통과·최종 Check 실패, T2 golden 적용 뒤 최종 통과를 자동시험했다. 두 Run Spec은 B1 공개 계약으로 각각 Task 2개가 유효함을 확인했다.
- Benchmark Runner 전체 회귀는 새 fixture 시험 4개를 포함해 143개가 통과했다. 다음 작업은 fixture source commit/tree 고정, B0 Task별 prompt hash 증거 구현, 새 manifest·artifact·preflight 동결이다. 이 조건을 통과하기 전에는 F1 라이브 Cell이나 B2를 시작하지 않는다.
- fixture source commit을 `dd8044b8818a4ca7b6af281fec5f8992bdd4cd43`으로 고정했다. `sequential-code-change` tree는 `7593579d0094e6254563127ae9f0d3508b8dc748`, `sequential-document` tree는 `84879dd6db89bb65ae8422f0d1932a102da0a2e9`이며 새 manifest가 이 값들을 가리킨다.
- Runner는 B0 준비 시 `benchmark-run.yaml`의 Task 순서대로 고정 prompt와 prompt plan을 생성한다. 각 전달 명령은 Task key와 prompt SHA-256을 함께 기록하고, 다중 Task Cell은 전체 순서가 정확하지 않거나 prompt 파일이 변조되면 완료를 거부한다.
- artifact build script는 저장소 상대 `--manifest`를 받도록 일반화했다. 기본 manifest는 유지되므로 기존 R6 재현 경계는 바뀌지 않는다.
- 표적 검사 9개, Benchmark Runner 전체 146개, B1 전체 65개가 각각 통과했다. 다음 작업은 이 Runner 변경을 commit한 뒤 F1 artifact를 두 번 독립 build해 일치성을 확인하고 preflight·실행 전 freeze를 만드는 것이다.
- Runner·manifest source commit `b8ad5bc4ad70bcae37b254c0e1c5b5153df1f5ac`에서 F1 artifact를 저장소 runtime과 별도 임시 runtime에 독립 build했다. source commit, manifest hash, Runner/B1 wheel, 공개 Schema 5개, Experiment ID `exp_20260806_d2099743_1`, Plan fingerprint `d20997433142cd445b22266c9ce3a4f37becfef3648c28e705ae20a77def581f`, 12개 Cell 순서가 모두 일치했다.
- 동결용 비라이브 회귀는 B1 65개, Benchmark Runner 147개, 구현 오류 로그 31건, 로그 하네스 10개를 통과했고 실제 model turn은 0회다.
- ChatGPT 인증·Codex SDK/CLI 0.144.4·fixture tree preflight를 통과했다. preflight Evidence SHA-256은 `b2c8e29a8b705684f00230d9bc863ef4c0506996f59503ec67e029e01646a540`이다.
- `benchmarks/artifacts/f1-b0-b1-b8ad5bc-r1/`에 실행 전 bundle을 동결했다. Experiment의 12개 Cell은 전부 `PLANNED`, sealed 0, stop reason 없음, 다음 Cell은 `cell_sequential-code-change_1_b1`이다. 다음 작업은 계획 순서대로 F1 라이브 Cell을 한 번에 하나씩 실행하는 것이다.

## F1 revision 1 중단과 revision 2 재동결

- 작업일: 2026-08-06.
- revision 1에서 첫 B1 Cell은 정상 봉인됐으나 첫 B0 Cell은 작업과 prompt 입력이 준비되기 전에 `b0-start`를 실행했다. 900초 중 대부분이 프로젝트 확인과 수동 안내에 소비됐고, T2 전달 전에 `b0_deadline_exceeded`로 봉인돼 Experiment가 중단됐다. 이는 Task 구현 실패가 아니라 실행 순서 오류이며 효율성 비교에 사용하지 않는다.
- 재발 방지 계약은 `b0-prepare → 작업 입력창에 T1 붙여넣기 → 사용자 READY → b0-start → 즉시 전송·Event 기록`이다. `docs/experiments/b1-sequential-value-followup.md`에 이 경계를 명시했다.
- source commit `c7953806966effec9e2a42effed9a2fcc3b89fb9`에서 revision 2를 두 경로로 독립 build했다. source commit, manifest, Runner/B1 wheel, 공개 Schema 5개, Experiment ID `exp_20260806_b7f3ca21_2`, Plan fingerprint `b7f3ca21157f0d52109575eae58ea9b1e86d0ca9f5efd0d2dc9f2528ade3463b`가 모두 일치했다.
- 비실시간 회귀는 B1 65개, Benchmark Runner 148개, 구현 오류 로그 31건, 로그 하네스 10개를 통과했고 실제 model turn은 0회다. preflight Evidence SHA-256은 `68a8ad1de9722feb29e22611630af4f8d055c4c4059102d731192d0b8a486d17`이다.
- `benchmarks/artifacts/f1-b0-b1-c795380-r2/`를 실행 전 동결했다. 12개 Cell 전부 `PLANNED`, sealed 0, stop reason 없음이며 revision 1의 runtime·Cell과 합치거나 이어서 사용하지 않는다.

## F1 revision 3 부분 종료

- 작업일: 2026-08-06.
- 사용자의 요청에 따라 revision 2의 독립 artifact를 재사용하고 새 독립 build·전체 회귀·freeze를 반복하지 않은 revision 3 `exp_20260806_bac45bc4_3`를 만들었다. 최소 preflight 뒤 코드·문서 fixture에서 B0/B1 한 쌍씩 실행했다.
- 4개 Cell은 모두 `completed`, Check 성공, scope 정상, 비밀정보 0건으로 봉인됐다. 각 B0는 시작 제외 사람 중계 1회, 각 B1은 0회였고 수동 복구는 모두 0초였다. 따라서 B1이 T1 검사 뒤 T2를 자동 진행한다는 기능은 두 종류의 과제에서 확인됐다.
- 코드 fixture의 Variant 시간은 B0 497.109초, B1 89.047초였고 문서 fixture는 B0 166.328초, B1 78.172초였다. 그러나 B0 시간에는 사용자가 다른 작업을 하며 T1 완료를 확인하고 T2를 전달하기까지의 통제되지 않은 지연이 포함됐다. 이 차이를 순수 실행 성능이나 B1 속도 우위로 해석하지 않는다.
- 12개 중 5번째 Cell `cell_sequential-code-change_2_b0`는 `PREPARED`였지만 타이머·모델 호출 전에 중단했다. `active-workspace`와 일치하는 소유권 표식은 로컬 runtime의 `abandoned-experiments` 보존 영역으로 이동했으며 Runner의 Cell 상태를 완료나 실패로 조작하지 않았다. 나머지 7개는 `PLANNED` 상태다.
- `benchmarks/results/partial/exp_20260806_bac45bc4_3/`에 봉인 Measurement 원본 4개와 부분 종료 기록을 저장했다. 전체 Evidence export는 만들지 않았으므로 저장소만으로 Evidence hash를 재검증할 수 없다고 명시했다.
- 최종 상태는 `기능 확인`, `성능 미판정`, `채택 판정 미발행`이다. 이후 성능 실험은 사람을 통제 실행 경로에서 제외하고, 실제 사용성은 장기간 자연 사용 로그로 별도 측정해야 한다.

## SDK 통제 비교 명세 1차 심사 반영

- 작업일: 2026-08-06.
- 수동 F1의 사람 지연을 제거하기 위해 C0(one-shot), C1(same-thread staged), C2(fresh-thread relay), B1(순차 오케스트레이터)을 같은 `openai-codex==0.144.4` SDK 표면에서 비교하는 명세를 작성했다. 실제 구현과 model turn은 수행하지 않았다.
- 1차 Claude 심사는 P0 3건·P1 6건·P2 5건·P3 2건을 보고했다. C2 handoff와 현재 B1 TaskEnvelope가 같다는 코드 대조는 유지했다.
- 심사의 P0-1은 재검증 결과 기각했다. `stage1` Check가 미추적 Python bytecode를 만드는 사실은 맞지만 최종 Judge가 scope 검사 전에 이를 정규화한다. 관련 positive·negative 회귀시험 2건을 Python 3.12.10으로 실행해 `2 passed`를 확인했고, B1 내부도 scope 검사 뒤 Check 실행 순서라 자기 Check 산출물로 즉시 scope 실패하지 않는다.
- 나머지 지적은 반영했다. F2를 union 밖 F2a와 union 안·T1 밖 F2b로 분리하고 failure-injection을 9-Cell 선행 조건으로 바꿨다. 비용은 B1 full outcome의 `ΣB1/ΣC2` token·wall 비율로 계산하며, 재시도 없는 first-attempt 비율은 통제 타당성 자료로만 사용한다.
- C0는 모든 Task goal·completion criteria를 받는 탐색 Variant로 고쳤다. 기본 채택 판단은 C2·B1 8 Cell에 집중하고, 32 Cell 의무 실행을 폐기했다. 새 순서는 `9 non-live → 4 pilot → 8 decision → 실제 프로젝트 3~5건 또는 2~4주 telemetry → 필요할 때만 16/32 confirmatory`다.
- 32 Cell 축소는 분리된 다른 프로젝트의 가치 판단이 아니라 이 비교 자체의 검증력과 비용만으로 결정했다. 기존 32 Cell 중 C0·C1 16개는 최종 판정식에 기여하지 않고, 정상 fixture에는 품질 천장 효과가 있으며 두 fixture로 범용성을 주장할 수도 없다. 그래서 C2·B1 기본 8 Cell 뒤 실제 판정이 바뀔 수 있을 때만 16/32 Cell로 확대한다.
- 개정 명세는 `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md`, 658줄, SHA-256 `9F20B34FBB2A7E0748BF37B5514906F1ECAEE1693F0C45CA13BD539816B932D5`다. 1차 심사 보고서는 수정하지 않았으며 469줄, SHA-256 `7A668F049236C291B7D7DCF227F6E27B77124C974EF5E86FC3FA50C0DCC65CAB`다.
- 재심사 프롬프트는 `docs/prompts/benchmark-runner/claude-rereview-prompt-sdk-controlled-comparison-spec.md`, 33줄, SHA-256 `E5C7CB779B81D2FEC486DFB676F0FE39922A56BE94E5FE85970A40B8FE6E6764`다. 이 실행용 프롬프트는 SHA-256 `E15D...` 명세를 대상으로 사용됐으며 재심사 결과 파일이 생성됐다.

## SDK 통제 비교 명세 재심사·v3 동결과 구현 1단계

- 작업일: 2026-08-06.
- Claude 재심사는 `경미한 수정 후 구현 착수`로 판정했다. 잔여 항목은 P0 0건·P1 1건·P2 4건·P3 3건이며, 1차 지적 16건 중 15건 해결·1건 심사 오류로 기각됐다. 재심사 보고서는 `docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md`, 352줄, SHA-256 `D51AF9043E15AE655BF754D131BA66B14878EBAAFA9B61F3F6ADD6C92AA61507`다.
- 1차 P0-1 기각 근거를 다시 확인했다. Judge는 scope 판정 전에 미추적 Python bytecode를 정규화하며, 해당 positive·negative 회귀시험 2건을 Python 3.12.10에서 실행해 `2 passed`를 확인했다.
- 재심사의 N1~N8을 명세에 반영했다. 공통 Check 환경 변경을 기능 revision으로 규정하고, 최종 Judge의 중간 Task Check 미실행 한계, F1의 즉시 `BLOCKED`, 재시도 0회 시 token gate `not_applicable`, telemetry의 제한된 결정 역할, `NOT_READY`, 정규화 경로 증거, C0 Check 이름 노출 가능성을 명시했다.
- 동결한 v3 명세는 `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md`, 709줄, SHA-256 `50F4A6E579DFA21443FD64D5303BD1D36157520234F76BCBED1F9B28D81E97BA`다. 재심사가 실제로 읽은 판본은 SHA-256 `E15D...`였고, 이후 별도 프로젝트에 근거하던 §21.3의 축소 사유만 이 비교 자체의 검증력·비용 근거로 교체한 뒤 N1~N8을 반영했다. 재심사 보고서는 읽기 전용으로 유지했다.
- 구현 1단계로 B1과 Benchmark Runner에 각각 독립된 결정적 Check 환경 builder를 적용했다. 최소 OS 변수와 Python·Git 실행 경로만 허용하고 `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`, UTF-8 변수를 고정한다. 두 패키지를 직접 결합하지 않고 동일 계약 시험으로 drift를 막는다.
- 코드 대조 중 `OPENAI_API_KEY`만 차단하고 `CODEX_API_KEY`는 차단하지 않던 간극을 발견했다. 두 패키지의 runtime·doctor·preflight가 두 변수 중 하나라도 존재하면 값 노출 없이 fail-closed하도록 수정했고, FakeRuntime 경계에서도 두 변수를 제거한다. 이는 공식 지원 여부 판단이 아니라 이 실험의 ChatGPT 구독 인증 통제 정책이다.
- 표적 회귀는 B1 23개와 Benchmark Runner 68개가 통과했다. 전체 회귀는 B1 69개와 Benchmark Runner 155개가 통과했으며 `git diff --check`도 통과했다. 이 단계에서 실제 model turn, 라이브 비교 Cell, 새 wheel·artifact build는 수행하지 않았다.
- 다음 구현 단위는 C0·C1·C2 중 하나를 따로 완성하는 방식이 아니라, 공통 Experiment 계약에서 세 Variant가 같은 fixture를 끝까지 통과하는 최소 vertical slice다. 그 뒤 9개 non-live failure-injection gate를 통과해야 4개 live pilot으로 진행한다.

## SDK 통제 vertical slice·failure gate·Measurement 봉인 완료

- 작업일: 2026-08-06.
- Windows 새 PC에서 저장소를 안전한 하위 폴더에 clone하고 main `5e6284cafef5e8c14dc4be932940bb1e3a2cd3c2` 및 origin/main 일치를 확인했다. Python 3.12.10과 분리된 B1·Runner 가상환경, Codex CLI/SDK 0.144.4의 ChatGPT 로그인을 사용했다.
- `codex/windows-runner-fixes`의 `740c15c5f5be1da37dfafa98c71e71b8d6b2e835`에서 Windows B1 subprocess `PYTHONPATH`, CRLF Schema 비교, 임시 fixture 긴 경로 문제를 수정했다. B1 69개와 Runner 155개가 통과했다.
- `codex/sdk-vertical-slice`의 `ccb71570f02c9270f02462ef100848f66a000f5f`에서 공통 Worker 계약과 C0·C1·C2 SDK Adapter를 구현했다. 정상 C0·C1·C2·B1 vertical slice와 F1·F2a·F2b 9-Cell 결정론적 gate를 연결했다. B1 72개와 Runner 166개가 통과했고 실제 model turn은 0회였다.
- `codex/sdk-measurement-seal`에서 명시적 SDK Execution Plan, Cell lifecycle, 원시 Evidence, FixtureJudge, Measurement, SHA-256 seal, `verify_sealed_cell()` 재검증을 연결했다. SDK turn의 ResultEnvelope, terminal 상태, prompt·Schema·Task 의미 hash, 누적 usage와 delta, downstream dispatch 여부를 보존한다.
- 정상 4개 Cell과 실패주입 9개 Cell이 모두 `SEALED`됐다. Evidence 변조 검출을 포함한 표적 시험 3개, B1 전체 72개, Benchmark Runner 전체 169개, `git diff --check`가 통과했다.
- 모델 호출 없는 SDK account preflight에서 `openai-codex==0.144.4`, API key 환경 변수 없음, account type `chatgpt`, actual model turns 0을 확인했다. live 고정값은 `gpt-5.6-terra`, low effort, thread·turn `workspace_write`, thread·turn `deny_all`, absolute Cell cwd, `ephemeral=False`, ResultEnvelope Schema로 fail-closed 검증한다.
- 실제 C0·C1·C2 Codex SDK runtime, live용 artifact·manifest·Plan, 4-Cell pilot은 아직 만들거나 실행하지 않았다. 원저장소 작업자는 `docs/operations/sdk-controlled-implementation-report.md`와 세 적층 브랜치의 diff를 검토하고 전체 회귀를 재검증해 채택 여부를 결정한다. 승인 뒤에도 실제 runtime adapter는 mocked SDK 시험으로 먼저 구현하고 live pilot 직전에서 다시 멈춘다.

## SDK 통제 비교 원저장소 인수·신뢰성 보강

- 작업일: 2026-08-07.
- 원저장소 `main`의 기준 commit `5e6284cafef5e8c14dc4be932940bb1e3a2cd3c2`에서 집 PC의 세 브랜치가 `740c15c → ccb7157 → d45db7f` 순서로 적층됐음을 확인했다. 원격 구현을 먼저 별도 `codex/sdk-measurement-hardening` 브랜치에서 검토·수정했으며 기존 로컬 변경은 없었다.
- 비라이브 경계의 모델 호출 0회가 Adapter의 자기 신고에 의존하던 문제를 제거했다. SDK baseline은 정확한 `FakeSdkRuntime` 형식만, B1은 `runtime=fake`만 실행 전에 허용하며 임의 Adapter와 Runtime은 dispatch 전에 거부한다.
- Execution Plan의 Cell 순서를 강제하고 모든 선행 Cell의 Measurement와 Evidence seal을 다음 Cell 전에 다시 검증한다. Runner provenance는 호출자가 문자열로 넣지 못하게 하고 실행 중인 Benchmark Runner의 `pyproject.toml`, `src/benchmark_runner`, `schemas` source tree SHA-256이 Plan과 일치할 때만 진행한다.
- Adapter·Judge Evidence는 봉인 전에 경로와 비밀정보를 redaction한다. OpenAI형 secret, bearer token, credential field가 발견되면 원문을 저장하지 않고 redaction 보고서와 `STOPPED` 상태를 남기며 Measurement를 만들거나 봉인하지 않는다.
- B1 공개 보고서에 각 Attempt의 Task 의미 hash, 최초 prompt hash, ResultEnvelope Schema hash를 추가했다. Benchmark Runner가 이를 공개 CLI 출력에서 읽어 Measurement의 turn Evidence로 보존하며 C2와 B1의 Task 의미·Schema hash 일치를 시험한다. 기존 schema v1 소비자를 깨지 않도록 새 필드는 선택형이지만, SDK 통제 비교 Adapter는 세 hash가 없으면 fail-closed한다.
- 함께 발견한 측정 오차도 보강했다. 다음 turn의 실제 dispatch가 성공한 뒤에만 이전 turn을 `downstream_dispatched=true`로 기록하고, terminal·ResultEnvelope 실패가 발생해도 그 turn에서 이미 측정된 duration과 token usage를 버리지 않는다.
- 공격·봉인 표적 시험은 비인가 Runtime 선행 차단, 순서 위반, 선행 seal 변조, 임의 Runner hash, 비밀정보 redaction·봉인 중단, B1/C2 hash 대조를 포함해 `test_sdk_cells.py` 7개가 통과했다. Python 3.12.10 전체 회귀는 B1 72개와 Benchmark Runner 173개가 통과했고 `git diff --check`도 통과했다.
- 환경 변수 이름만 검사해 `OPENAI_API_KEY`와 `CODEX_API_KEY`가 모두 없음을 확인했다. 이번 인수·보강에서는 실제 model turn, 실제 Codex SDK runtime, live pilot, 새 실험 artifact를 실행하거나 만들지 않았다. 검증된 변경은 `main`에 fast-forward 방식으로 병합한다.

## SDK 통제 baseline 실제 Runtime Adapter 비라이브 구현

- 작업일: 2026-08-07.
- 공식 Codex SDK 문서와 로컬에 설치된 `openai-codex==0.144.4` 소스를 함께 대조했다. 동기 `Thread.turn()`·`TurnHandle.run()`에는 timeout 인자가 없고 `TurnHandle.interrupt()`가 제공됨을 확인해, worker thread와 deadline 및 interrupt grace로 timeout 경계를 구현했다.
- `CodexSdkRuntime`은 정확한 SDK 버전과 ChatGPT 계정 인증만 허용한다. `OPENAI_API_KEY` 또는 `CODEX_API_KEY` 환경 변수 이름이 하나라도 존재하면 값을 읽거나 출력하지 않고 SDK client 생성 전에 중단한다.
- thread에는 model·sandbox·approval mode·절대 cwd·ephemeral을, turn에는 model·reasoning effort·sandbox·approval mode·절대 cwd·ResultEnvelope Schema를 명시한다. service tier와 summary는 고정 근거가 없어 전달하지 않는다.
- SDK 경계를 `CodexSdkBindings`로 주입 가능하게 분리해 실제 app-server나 model turn 없이 계약을 시험했다. C0는 1 thread·1 turn, C1은 1 thread·2 turns, C2는 2 threads·2 turns를 만들며, 동일 thread의 누적 token usage와 새 thread의 usage 재시작을 검증했다.
- timeout 시 interrupt 요청, 인증·버전·계정 fail-closed, preflight의 model turn 0회, 모든 고정 옵션 전달, ResultEnvelope JSON과 duration·usage 수집, context 종료를 포함한 신규 시험 10개가 통과했다. 기존 SDK Cell·봉인 시험과 묶은 표적 회귀는 17개가 통과했다.
- Python 3.12.10 전체 회귀는 B1 72개, Benchmark Runner 183개가 통과했다. 최초 병렬 전체 회귀에서 `cell-state.json` 원자 교체의 Windows `WinError 5`가 한 번 발생해 Runner가 182 passed·1 failed였으나, 같은 단일 시험과 Runner 전체를 새 basetemp에서 각각 다시 실행해 1 passed 및 183 passed를 확인했다. 원인은 확인되지 않아 `DEV-20260807-001`에 `investigating`으로 기록했고 근거 없는 자동 재시도는 추가하지 않았다.
- 이번 단계에서는 실제 Codex SDK client나 model turn을 호출하지 않았다. 실제 live Cell driver·artifact·Execution Plan 생성과 4-Cell pilot은 아직 수행하지 않았으며, 구현은 live pilot 직전 경계에서 멈춘다.

## SDK 통제 4-Cell live pilot

- 작업일: 2026-08-07.
- `254d991`에서 live Cell 실행기와 pilot manifest를 구현했다. C0·C1·C2는 실제 `CodexSdkRuntime`, B1은 기존 공개 CLI의 `runtime=codex`를 사용한다. B1도 baseline과 동일하게 turn·resume마다 model과 절대 cwd를 다시 명시하도록 통제를 맞췄다.
- B1 공개 report에 각 terminal Evidence의 `duration_ms` 합으로 계산한 `model_active_seconds`를 선택 필드로 추가하고 Schema를 재생성했다. local SDK thread·session·Run 식별자는 Git export 전에 SHA-256으로 바꾸고, 홈 경로·이메일·인증 파일·비밀 형태는 기존 redaction·export 검사를 통과해야 봉인되도록 했다.
- 모델 호출 전 표적 계약 시험 43개, B1 전체 73개, Benchmark Runner 전체 186개가 통과했다. 첫 Runner 전체 명령은 긴 basetemp 때문에 Windows `Filename too long` 5건이 발생했으며, 기존에 검증된 짧은 basetemp로 전체를 다시 실행해 186개 통과를 확인했다. 이는 코드 회귀가 아니며 기존 Windows 짧은 임시 경로 운영 규칙을 적용했다.
- revision 1 `exp_20260807_8b1cd12c_1`은 관리형 shell sandbox가 ChatGPT 인증 저장소를 SDK에 노출하지 않아 C0 preflight에서 종료했다. 동일 번들 CLI의 승인된 외부 실행에서는 `Logged in using ChatGPT`를 확인했다. 모델 호출은 0회였고 실패 artifact를 보존했으며 `DEV-20260807-002`에 기록했다.
- source commit `b4fa4f0` 기준 revision 2 `exp_20260807_a3046b4b_2`는 승인된 외부 실행 경계에서 C0·C1·C2·B1 네 preflight를 `account_type=chatgpt`, `openai-codex==0.144.4`, API key 환경 이름 0개, actual model turn 0회로 통과했다.
- 실제 pilot 결과는 C0 1 session·1 turn·90,232 tokens·53.172초, C1 1 session·2 turns·164,586 tokens·57.578초, C2 2 sessions·2 turns·197,566 tokens·99.390초, B1 2 sessions·2 turns·177,746 tokens·89.344초다. 네 Cell 모두 `completed`, 독립 Judge 성공, Measurement `SEALED`였다.
- 총 실제 model turn은 7회다. export-safe 파일 48개를 `benchmarks/results/sdk-controlled-pilot/exp_20260807_a3046b4b_2`로 내보냈고 집계 SHA-256 `388428fe70777a03a60a1c19d51a8d2cd6e38df189c3bf367aa0230f0b0d689f`를 독립 재검증했다. 판정은 `PILOT_PASS`지만 confirmatory 결과가 아니므로 B1 채택 판정에는 합산하지 않는다.
- 다음 단계는 이 pilot을 반복하는 것이 아니라 동결 명세의 C2·B1 기본 8-Cell 의사결정 표본이다. 이번 작업은 pilot 결과 보존과 push에서 멈춘다.

## SDK 라우팅 테스트 스위트 v1 심사 초안

- 작업일: 2026-08-07.
- 완료된 4-Cell pilot 뒤 기존 `2 fixture × C2/B1 × 2회` 8-Cell을 곧바로 실행하지 않고, 테스트가 단순·중간·복합 작업에 따른 B1의 손익분기점을 찾을 수 있는지 먼저 재검토했다. Sol Ultra 독립 검토는 기존 8-Cell을 같은 예산의 breadth-first calibration으로 교체하고 이후 3-Task·복합·실제 telemetry를 조건부로 여는 방향을 권고했다.
- 기존 시스템·호출·인증·측정·Judge·Evidence·봉인 계약과 완료된 pilot은 수정하지 않았다. 새 `docs/design/sdk-routing-suite-v1-design.md`가 미실행 표본 선택만 후속 계약으로 정의한다.
- S1은 기존 1-Task `code-change`, `document-read`와 2-Task `sequential-code-change`, `sequential-document`를 C2/B1 각 1회 실행하는 8 Cell, 정상 경로 12 turns다. S1은 `ADOPT_B1_DEFAULT`를 발행하지 않고 작은 deterministic fixture의 calibration으로만 해석한다.
- complexity는 Task 수, 의존 깊이·간선·fan-in, Worker read surface, 예상 write surface, 인계 종류, scope 중첩, 검증 종류, 실패 위험, 결과 모호성의 벡터로 기록하며 하나의 점수로 합치지 않는다.
- S0는 기존 F1·F2a·F2b 9-Cell을 유지한다. F3 recovery, F4 timeout, F5 input fingerprint 변조는 구현 가능성과 B1 특혜 여부를 심사받기 전까지 후보로만 두었다.
- S2는 3-Task 코드 migration과 3-Task incident analysis 후보를 각각 C2/B1 한 번씩 실행하는 4 Cell을 제안한다. S3는 S2가 routing 정책을 정하지 못하고 추가 결과가 실제 결정을 바꿀 때만 상세화한다. 최소 실용 live 범위는 S1+S2 정상 24 turns이며 반복과 S3를 자동 예약하지 않는다.
- 현재 Check가 Worker에게 보인다는 한계를 명시했다. S1은 `hidden_checks=false`로 제한하고, S2 전에는 `workspace_write`에서 Judge-only oracle이 실제로 읽히지 않는다는 경계를 증명하거나 `judge_only_unverified`·property 기반 검사로 주장을 낮춰야 한다.
- 설계 초안은 723줄, SHA-256 `B6BB912C066534A1515C56A935DF41505E1FD21C85A366EB4276344215F6CD07`다. Claude 심사 프롬프트는 149줄, SHA-256 `FC0A68E2F2DB6E926EAE5656E49090A50DBB5D1C2F930D83C70E47544D95FA44`다.
- 보호 기준 파일을 다시 확인했다. 선행 동결 명세는 709줄·SHA-256 `50F4A6E579DFA21443FD64D5303BD1D36157520234F76BCBED1F9B28D81E97BA`, pilot manifest는 38줄·`E6F360E0A7CD94FFF61F15DADFB382C5800A6B5E5AF08730ED7F47A811B6ECCE`, 선행 Claude 재심사는 352줄·`D51AF9043E15AE655BF754D131BA66B14878EBAAFA9B61F3F6ADD6C92AA61507`로 작업 전 값과 같다.
- 이번 단계에서는 suite manifest, fixture, Runner 구현, artifact, Execution Plan을 만들지 않았고 실제 model turn도 추가로 호출하지 않았다. 다음 작업은 Claude 심사 보고서를 받은 뒤 P0·P1을 반영해 v1 설계를 동결하는 것이다.

## SDK 라우팅 테스트 스위트 v1 심사 반영·동결

- 작업일: 2026-08-07.
- Claude 1차 심사는 `경미한 수정 후 동결`, P0 0건·P1 5건·P2 5건·P3 4건으로 판정했다. 심사 보고서는 664줄, SHA-256 `8C959D41DCE42D4733011BEC05F522E0A1D907A34B1CB187570E977B659C4EA9`이며 읽기 전용으로 유지했다. 심사자는 Python 3.10 환경과 프로젝트의 3.11+ 요구가 충돌해 코드 시험을 0개 실행했고 미확인 7건을 따로 남겼다.
- P1 5건을 모두 반영했다. S1은 profile route를 발행하지 않는 8-Cell calibration으로 제한했다. 선행 pilot과 반대인 `sequential-code-change` B1→C2 순서는 순서 효과 진단에만 쓰며 수치에 합산하지 않는다. token·wall 한도는 S1 네 pair 전체 합의 안전 guard로만 유지한다.
- F3 retry recovery는 B1만 교정된 두 번째 model 결과를 받는 비대칭 비교가 되므로 B1 단독 재dispatch 계약 시험으로 옮겼다. F4 timeout은 공통 runtime 회귀로 이동했고 F5 input fingerprint는 F2b와의 중복 때문에 S2 이후 조건부 계약으로 연기했다.
- 공식 Codex 문서와 설치된 `openai-codex==0.144.4` 경계를 다시 대조했다. `workspace_write`는 workspace 밖 읽기를 막지 않으며, permission profile의 read deny와 명시적 기존 sandbox 설정은 합성되지 않는다. native Windows 비상승 sandbox의 read/write carve-out 제한도 있어, 현 SDK 계약을 바꾸지 않는 S2 기본 검증을 Adapter 종료 뒤 공통 property·metamorphic 관계를 검사하는 `post_hoc_property`로 확정했다. permission profile은 새 runtime revision과 전체 회귀를 요구하는 미래 후보로 남겼다.
- complexity vector에 `check_count`와 1-Task `scope_overlap=not_applicable`를 추가하고, 네 S1 fixture의 Worker read surface가 고정돼 있음을 명시했다. 1-Task는 coordination negative control일 뿐 retry negative control이 아니며 `document-read`의 acceptance는 문자열·기본 구조 검사 수준이라고 제한했다.
- 최소 실용 live 범위는 `S0 + S1` 정상 12 turns로 낮췄다. 완료된 pilot 7 turns와 조건부 S2 최초 12 turns를 합친 이 판본의 누적 상한은 31 turns이며, 그 이후는 새 Plan·예산·사용자 승인이 필요하다.
- 시험 방법의 판단 오류와 해결은 `DEV-20260807-003`에 등록했다. 원인은 breadth-first calibration과 profile route 결정을 분리하지 않고 단일 pair의 확률 변동과 비대칭 재시도를 판정식에 사용하려 한 것이다. S1 calibration·S2 이후 route·사후 속성 검사로 역할을 분리해 해결했다.
- 동결한 `docs/design/sdk-routing-suite-v1-design.md` 판본 2는 804줄, SHA-256 `6A5CF1863515BEACEE51F8DCCD90C5F468BE0D67DEACE429C0AFB5250E1D520F`다. 심사 프롬프트는 149줄·`FC0A68E2F2DB6E926EAE5656E49090A50DBB5D1C2F930D83C70E47544D95FA44`로 수정하지 않았다.
- 보호 파일은 그대로다. 선행 비교 명세는 709줄·`50F4A6E579DFA21443FD64D5303BD1D36157520234F76BCBED1F9B28D81E97BA`, pilot manifest는 38줄·`E6F360E0A7CD94FFF61F15DADFB382C5800A6B5E5AF08730ED7F47A811B6ECCE`, 선행 재심사는 352줄·`D51AF9043E15AE655BF754D131BA66B14878EBAAFA9B61F3F6ADD6C92AA61507`다.
- 구현 오류 로그 `check`는 38개 entry를 검증했고 하네스 단위시험 10개가 통과했다. 당시 tracked diff의 `git diff --check`는 통과했으나, 전체 파일을 staging한 뒤 Claude 심사 원문 255행에서 후행 공백 1건을 확인했다. 심사 원문 SHA-256을 보존하기 위해 수정하지 않고 알려진 형식 예외로 남겼다. 설계·로그·인덱스만 변경했으므로 B1·Runner 전체 회귀는 실행하지 않았고 실제 model turn은 0회다.
- 다음 구현 단위는 S0 9-Cell과 B1 retry 단위 계약을 Python 3.12로 재확인한 뒤, manifest 기반 suite runner의 model-free 최소 vertical slice를 만드는 것이다.

## SDK 라우팅 S0 재검증

- 작업일: 2026-08-07. 기준 commit은 `11f76a9e7916776f7aa77b1a933d5b701c2630f1`이며 작업 시작 시 `main`과 `origin/main`이 일치했다.
- Python 3.12.10과 B1 가상환경을 사용했다. Runner 전용 가상환경은 없었지만 같은 환경에 `pytest 8.4.2`, `pydantic 2.13.4`, PyYAML, jsonschema와 Runner import가 모두 준비돼 있음을 확인했다.
- Fake Runtime만 사용하는 S0 F1·F2a·F2b 9-Cell 공통 Plan·Measurement·seal 시험이 `1 passed`로 통과했다. B1의 Check 실패 2-Attempt, transient failure 뒤 새 Attempt·고유 artifact, malformed ResultEnvelope 뒤 동일 session resume 계약은 `3 passed`로 통과했다.
- 첫 표적 실행은 저장소 내부의 존재하지 않는 `.test-tmp` 부모를 `--basetemp`로 지정해 pytest setup 3건이 `FileNotFoundError`로 끝났다. 테스트 본체와 model turn은 시작되지 않았다. 이미 무시되는 `benchmarks/.local-r6/s0-tests/` 부모를 만든 뒤 같은 표적 시험을 재실행해 통과했다.
- 첫 Runner 전체 회귀는 저장소 내부의 긴 basetemp를 사용해 `176 passed, 10 failed`였다. 4건은 R6가 B0 프로젝트 경로를 source repository 밖으로 강제하는 안전 계약에 의해 의도적으로 거부됐고, 나머지는 중첩된 한글 Windows 경로의 `Filename too long`과 한 번의 `WinError 5` 원자 교체 실패였다. 같은 코드에서 저장소 밖의 짧은 독립 `%TEMP%/lao-s0-*-r2` basetemp로 재실행했다.
- 최종 전체 회귀는 B1 `73 passed`, Benchmark Runner `186 passed`다. 첫 10건은 코드 회귀가 아니라 이미 문서화된 Windows 짧은 외부 basetemp 운영 규칙을 지키지 않은 시험 호출 오류로 판정했다. 기존 `DEV-20260806-006`, `DEV-20260807-001` 및 앞선 pilot 로그와 중복되므로 새 incident ID는 만들지 않았다.
- 전체 과정에서 실제 model turn은 0회다. source·fixture·Runner·B1 코드는 수정하지 않았고 S0 판정은 `PASS`다. 다음 작업은 manifest 기반 suite runner의 model-free 최소 vertical slice 구현이다.

## SDK 라우팅 Suite Runner 최소 vertical slice

- 작업일: 2026-08-07. 기준 commit은 `11f76a9e7916776f7aa77b1a933d5b701c2630f1`이다. 이 절은 직전 `SDK 라우팅 S0 재검증`과 같은 미커밋 작업 묶음에 이어서 기록했다.
- `benchmarks/suites/sdk-routing-v1/`에 strict suite·S1 stage manifest와 생성된 JSON Schema 3개를 추가했다. S1은 동결 fixture 4개, C2/B1 8-Cell 순서, live 실행 시 12 model turn 상한을 고정하지만 상태는 `implementation_candidate`이며 아직 동결·live 실행하지 않았다.
- `routing_suite.py`는 동결 Git tree에서 task 수, 의존 깊이·edge·fan-in, worker read 파일·byte, write module, Check 수, handoff, scope overlap을 다시 계산해 manifest 선언과 다르면 Plan 생성을 거부한다. Plan은 기존 `build_sdk_controlled_plan`, Experiment는 `initialize_sdk_experiment`, Cell 실행·Judge·Measurement·seal은 `run_sdk_nonlive_cell`을 재사용한다.
- exact 실행 순서는 code-change C2→B1, document-read B1→C2, sequential-code-change B1→C2, sequential-document C2→B1이다. Plan의 `route_decision_allowed`는 `false`이고 S1 허용 결과는 `CALIBRATION_PASS`, `CALIBRATION_STOP`, `CALIBRATION_INCONCLUSIVE`뿐이다.
- 새 단위시험 4개는 strict manifest·Schema 재현, 동결 tree 기반 복잡도 재계산, exact 8-Cell Plan·보정 전용 정책, 첫 C2 code-change Cell의 `fixture 복원 → FakeSdkRuntime → Judge → Measurement → seal` 관통을 검증했다. 두 차례 표적 실행 모두 `4 passed`였고 기존 SDK 9개 실패 Cell 공통 Plan·seal 게이트는 `1 passed`였다.
- 최종 전체 회귀는 Python 3.12.10에서 B1 `73 passed`, Benchmark Runner `190 passed`다. `git diff --check`와 Schema 재생성은 통과했다. 전체 과정의 실제 model turn은 0회이며 live artifact·live Execution Plan·route 판정은 생성하지 않았다.
- 현재 완료 범위는 한 Cell을 끝까지 관통한 최소 vertical slice다. 다음 비라이브 단위는 같은 manifest와 Plan으로 8개 Cell 전부를 Fake SDK로 실행하고, suite 수준 완료·봉인·export 계약을 추가하는 것이다.

## SDK 라우팅 S1 8-Cell 비라이브 봉인·export

- 작업일: 2026-08-07. 기준 commit은 `4f8b50240b29f9cc1fce248b3a6a93e7816c3ed1`이다. 동결 설계·fixture·suite manifest의 Cell 구성과 예산은 수정하지 않았다.
- 같은 Execution Plan에서 남은 Cell을 한 번에 하나씩 실행하는 `run_all_routing_s1_nonlive_cells`, Cell seal을 다시 열어 완료 상태를 계산하는 `routing_s1_nonlive_status`, 독립 export·검증 경로를 추가했다. 각 Cell의 실행·Judge·Measurement·seal은 기존 `run_next_routing_s1_nonlive_cell`과 `run_sdk_nonlive_cell`을 그대로 재사용한다.
- code-change C2→B1, document-read B1→C2, sequential-code-change B1→C2, sequential-document C2→B1의 정확한 8-Cell 순서를 Fake SDK/B1 fake runtime으로 모두 실행했다. 8개 모두 `SEALED`, Judge 성공, actual model turn 0회였다.
- export는 Execution Plan, suite·stage manifest, 8개 Measurement와 참조 Evidence, Cell별 `seals.json`, 전체 `export-seal.json`, JSON·Markdown 요약을 보존한다. verifier는 원본 workspace를 신뢰하지 않고 manifest·Plan·Cell 순서·Measurement·Evidence·전체 파일 hash를 다시 계산한다. Measurement 한 바이트를 바꾼 회귀시험은 `Measurement seal differs`로 거부됐다.
- 비라이브 결과는 `MODEL_FREE_PASS|FAIL|INCOMPLETE`만 사용한다. 요약에는 `calibration_outcome_issued=false`, `route_decision_issued=false`를 고정했으며 Fake 결과로 `CALIBRATION_*`, `ROUTE_*`, B1 채택·성능 주장을 발행하지 않는다.
- 최초 확장 표적 시험은 `ExecutionPlan.track` 직접 필드를 가정해 4 passed·2 failed였다. 실제 builder는 `track`을 `plan_supplemented`에 기록한다. 공개 Plan Schema를 바꾸지 않고 해당 보충 항목이 정확히 하나인지 검사하도록 고쳐 6 passed를 확인했고, 발견·원인·해결은 `DEV-20260807-004`에 기록했다.
- 첫 Runner 전체 회귀는 191 passed·1 failed였다. 새 8-Cell 시험의 `cell-state.json` PREPARED 저장 중 Windows `os.replace`가 `WinError 5`를 한 번 반환했다. 새 basetemp에서 같은 시험은 1 passed, 독립 전체 회귀는 192 passed였다. 같은 유형의 두 번째 관측이므로 기존 `DEV-20260807-001`을 갱신해 `investigating`으로 유지했으며 원인 미확인 상태에서 자동 재시도를 추가하지 않았다.
- 최종 회귀는 B1 `73 passed`, Benchmark Runner `192 passed`다. 전체 작업의 실제 model turn은 0회다. 다음 단계는 변경분 심사와 S1 fixture tree·manifest·Cell 순서·예산의 실행 전 동결이며, 그 전에는 live 12-turn 실행을 시작하지 않는다.

## 집 PC 인수인계 최신화와 공홈 심사 프로젝트 준비

- 작업일: 2026-08-07. 기능 기준 commit은 `a99aa5846af172070cdb8a44c10ade0233abcba7`이다.
- 기존 `home-codex-handoff.md`가 SDK vertical slice 구현 전 상태와 B1 69개·Runner 155개 회귀를 가리키고 있어, S0 재검증·Suite Runner·S1 8-Cell 비라이브 봉인·export 완료 상태로 전면 최신화했다.
- 인수인계 문서에 현재 확인된 범위와 미확정 주장, 다음 게이트인 live 전 감사·실행 후보 동결, Python 3.12 짧은 외부 basetemp 규칙, ChatGPT 구독 인증 전용 정책을 기록했다. 사용자는 집 PC clone과 이전 인수 경험이 있으므로 시작 프롬프트는 새 clone 설명을 생략하고 dirty worktree fail-closed·ff-only 동기화부터 시작한다.
- 공홈 ChatGPT에 `Local Agent Orchestrator 심사실` 프로젝트를 만들고 Plus 한도인 소스 25개를 업로드했다. 역할 지침은 작업 PC Codex·집 Codex·사용자 소유 Codex 작업·내부 하위 에이전트·Claude를 구분하며, 분리된 `개인 AI 개발 전통 체계`의 혼입을 금지한다.
- 공홈 준비 점검은 25개 파일을 읽고 S1 설계·manifest·주요 코드의 정적 심사가 가능하다고 봤다. 다만 전체 fixture tree·Git object·원본 실행 artifact가 없어 독립 재현 심사는 제한된다고 판정했으므로, 공홈은 정적 심사 보조 채널이고 Git·코드·독립 시험 artifact가 정본이다.
- 이번 최신화는 문서 작업뿐이며 B1·Runner 코드와 manifest를 수정하지 않았다. 실제 model turn, S1 live 실행, 새 artifact 생성은 수행하지 않았다.

## 집 PC 인수인계 목적 재정의

- 작업일: 2026-08-07. 사용자 피드백에 따라 기존 인수인계가 다음 기술 감사 지시를 앞세우고 프로젝트의 문제의식·범용 코어 우선 전략·수정 과정을 충분히 시험하지 못한다는 점을 바로잡았다.
- `home-codex-handoff.md`를 작업 체크리스트가 아니라 프로젝트 정신모델 인수인계로 재구성했다. 실제 프로젝트 특화 오케스트레이션에서 출발한 의문, 범용 저장소를 독립 검증한 뒤 프로젝트별 fork로 재구성하는 구조, B1이 최종 제품이 아닌 순차 기준선이라는 위치를 명시했다.
- 수동 B0 지연, 비교 표면 불일치, Fake/live 주장 경계 등 설계·시험 방법을 수정한 이유와 `부분 확인은 실패가 아니며 미확인을 확인했다고 보고하는 것이 실패`라는 증거 원칙을 인수 대상에 포함했다.
- 역할을 다시 분리했다. 집 Codex는 기술 구현과 필요시 내부 하위 에이전트 병렬 검증을 담당한다. 공홈 ChatGPT는 S1 기술 동결 판정자가 아니라 집 Codex가 목표·맥락·과정·역할을 이해했는지 평가하는 메타 심사자다. Claude는 외부 기술 심사자이며 Git·코드·시험 artifact가 정본이다.
- 새 시작 프롬프트는 첫 세션에서 테스트·하위 에이전트·파일 수정·commit·model turn을 금지하고, 집 Codex가 자기 언어로 프로젝트 이해 보고서를 작성한 뒤 멈추도록 한다. 공홈 이해도 평가가 끝난 뒤에만 S1 live 전 감사와 내부 하위 에이전트 기술 검증으로 넘어간다.
- 이번 변경은 인수인계와 작업 로그 문서뿐이다. 구현·manifest·시험·artifact는 수정하지 않았고 실제 model turn은 0회다.

## SDK 라우팅 S1 live 실행 후보 동결

- 작업일: 2026-08-07. 공홈 이해도 심사는 통과했고, 내부 하위 에이전트 3개가 계약·runtime·seal 경계를 read-only로 나누어 감사했다. 발견된 P1을 수정한 뒤 최신 재감사 판정은 잔여 P0 0건·P1 0건이다.
- source commit `e7b616354dda0e0a85c4d327228fe8982a764084`에 별도 fail-closed live controller를 추가했다. `create`는 clean source, frozen suite·stage·fixture manifest, 같은 commit의 0-turn 회귀, ChatGPT 구독 runtime profile을 요구한다. `run-next`는 invocation마다 명시적 model 사용 승인을 요구하고 정확히 한 Cell만 dispatch하며 자동 연속 실행은 없다.
- Python executable, Git executable, Codex SDK와 bundled CLI, Runner/B1 source, controller, runtime profile, suite·stage·fixture manifest를 hash로 고정했다. B1은 frozen Python `-P -m orchestrator`, source `PYTHONPATH`, cwd, Schema root와 남은 전역 예산 이하의 내부 max-turn을 강제한다. artifact에는 사용자 절대경로 대신 path SHA만 기록한다.
- Plan은 별도 짧은 임시 경로의 clean checkout과 별도 process에서 재구성한다. 독립 process가 Runner/B1 source와 두 fixture manifest hash를 다시 계산하고 원본 Plan과 byte·fingerprint가 다르면 후보 생성을 거부한다. Windows clone 간 바이트 차이를 막기 위해 hash-bound source와 artifact의 EOL 속성을 고정했다.
- Cell dispatch 전 durable claim을 원자적으로 남겨 상태·stop 기록이 모두 실패해도 implicit retry를 금지한다. status는 봉인된 Measurement의 전체 identity, provenance, environment, resource, token, B1 control metric을 검증한 뒤에만 누적 turn과 calibration 결과를 계산한다. 전역 실제 turn은 12가 절대 상한이고 B1의 반복 가능한 `check_failed` 품질 회귀만 safety STOP으로 분류한다.
- S1은 `CALIBRATION_PASS|STOP|INCONCLUSIVE`만 발행할 수 있고 `route_decision_issued=false`다. 일반 Task/runtime 실패는 PASS가 아니라 INCONCLUSIVE이며, 안전 실패나 예산 소진은 partial terminal STOP export로 보존한다. export verifier는 freeze bundle, raw Plan SHA, 모든 Measurement/Evidence와 정확한 파일 집합을 독립 재검증한다.
- 최종 비라이브 회귀 record는 같은 source commit에서 S0 gate `9 passed`, B1 retry 계약 `3 passed`, B1 전체 `74 passed`, Benchmark Runner 전체 `203 passed`, 구현 incident 41개와 로그 하네스 10개 통과를 기록했다. 실제 model turn은 0회다.
- 8개 ChatGPT 구독 preflight 뒤 `benchmarks/artifacts/sdk-routing-v1-e7b6163-r1/`을 실행 후보로 동결했다. Experiment는 `exp_20260807_d1e9fdb8_1`, Plan fingerprint는 `d1e9fdb8b4856fa5bd35cfa75cb05b7eed1be400bc5ec4358cce9f595bbd2a42`, raw Plan SHA-256은 `83baaf3c57df94de8e4e72205e6feb28cbc85873794002b3a14ce384f88400e1`, freeze SHA-256은 `2a287039526ebd919b50110c2fd10a0e905fbf3d0638036e3a91738d7ad34171`이다.
- 별도 verifier와 status에서 8개 Cell 전부 `PLANNED`, sealed 0, actual model turn 0, calibration outcome 없음, route 미발행, stop 없음이 확인됐다. 다음 행동은 자동 실행이 아니라 사용자 별도 승인 뒤 첫 `cell_s1_code-change_1_c2` 한 Cell만 실행하는 것이다. S2·S3와 route 정책은 선행하지 않는다.
- artifact commit `df7cbddba3c40966c4b14ec459b38de29ce3cc86`을 `core.autocrlf=true`와 `false`인 두 별도 clean clone에서 각각 검증했다. 두 verifier 모두 같은 Experiment, Plan fingerprint, raw Plan SHA와 freeze SHA를 반환해 Windows EOL 설정 사이에서 bundle bytes가 보존됨을 확인했다. 두 임시 clone은 검증 뒤 삭제했다.
- 과거 문서의 프로젝트별 `fork` 표현은 현재 동결 설계의 기본 적용 방식이 아니다. 기본은 검증된 버전 코어와 프로젝트별 `.orchestrator/` project pack이며 전체 Git fork는 설정·hook으로 표현할 수 없는 필요가 생겼을 때의 escape hatch다.

## SDK 라우팅 S1 live 8-Cell 완료와 정식 export

- 작업일: 2026-08-08. 동결 후보 `exp_20260807_d1e9fdb8_1`을 변경하거나 `create`를 다시 실행하지 않고, 사용자 승인 범위에서 `run-next`를 Cell마다 순차 호출했다.
- code-change C2→B1, document-read B1→C2, sequential-code-change B1→C2, sequential-document C2→B1의 8개 Cell이 모두 `completed`·`SEALED`에 도달했다. Judge·scope·protected file·Evidence 무결성은 모두 성공했고 stop은 없었다. 실제 model turn은 계획된 정상 예산과 같은 12회다.
- 최종 status는 `CALIBRATION_PASS`, `route_decision_issued=false`다. B1 네 Cell의 retry·resume는 모두 0회였다.
- C2 4개 합계는 6 turns, 662,143 tokens, 273.125초이고 B1 4개 합계는 6 turns, 541,145 tokens, 259.032초다. B1 합계는 token 18.3%, wall-clock 5.2% 작았지만 차이 대부분은 `sequential-document` 한 pair에서 발생했다. profile당 pair 하나인 S1 결과로 범용 우위·profile route·B1 채택을 발행하지 않는다.
- live export는 108개 파일을 `benchmarks/results/sdk-routing-v1/exp_20260807_d1e9fdb8_1/`에 보존했다. export SHA-256은 `ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8`이며 생성 시 freeze bundle, 8개 Measurement와 Evidence, 정확한 파일 집합을 다시 열어 검증했다.
- 사람이 읽는 해석은 `docs/experiments/sdk-routing-s1-live-result.md`에 기록했다. 추가 회귀·하위 에이전트·새 하네스·추가 model turn은 실행하지 않았다. 다음 기술 후보는 S2 intermediate v1 최소 구현이며 S3는 선행하지 않는다.

## SDK 라우팅 S2 intermediate 명세 review candidate

- 작업일: 2026-08-08. S1 `CALIBRATION_PASS` 뒤 구현을 시작하지 않고 `docs/design/sdk-routing-s2-intermediate-spec.md`에 S2 전용 구현·시험 계약을 작성했다.
- 3단계 config migration과 incident analysis의 Task graph·dependency·inputs·read/write scope·산출물 6/7개, 공개 Task Check와 각각 5개 사후 property를 구현 가능한 수준으로 고정했다. 사후 검사는 Worker turn 뒤 C2/B1에 동일하게 적용하며 hidden oracle이라고 주장하지 않는다.
- 최초 순서는 config C2→B1, incident B1→C2이고 정상 4 Cell·12 turns다. 사용자가 Plan 전체를 승인하면 Cell은 순차 실행하되 Cell마다 사용자에게 재승인을 묻지 않는다. 역순은 사전 등록된 조건이 있을 때 새 Plan·예산·승인으로만 연다.
- profile별 route 결정식, `routing-policy-v1` 최소 필드, S2 stage 상태와 정지 규칙을 명시했다. S1 수치와 단일 S2 pair의 속도만으로 B1 route를 발행하지 않으며 미측정 저위험 fallback은 C2다.
- 새 S2 전용 대형 Controller·상태 기계·Judge·seal 복제를 금지하고 기존 `routing_live.py`의 stage-generic 최소 확장만 허용했다. 검증은 새 계약 표적 시험, Fake 4-Cell 관통, 안정화 뒤 최종 회귀로 제한하고 하위 에이전트 P1-zero 감사를 gate에서 제외했다.
- `docs/reviews/benchmark-runner/claude-review-prompt-sdk-routing-s2-intermediate-spec.md`에 read-only Claude 심사 프롬프트를 작성했다. 현재 상태는 `review_candidate`이며 Claude 심사와 사용자 동결 전에는 구현·시험·model turn을 시작하지 않는다.

## SDK 라우팅 S2 revision 3 Claude 심사와 revision 4 candidate

- 작업일: 2026-08-08. Claude의 read-only 심사는 revision 3을 `재설계 필요`로 판정했다. 지적 수는 P0 6건·P1 10건·P2 8건·P3 4건이며, 하네스-for-하네스나 관성적 재검증 문제는 없고 manifest 하위 호환·turn 예산·incident omission·route 증거 수준이 핵심 차단점이라고 봤다.
- 심사 원문에서 실행 가능한 지적과 근거를 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s2-intermediate-spec.md`에 정규화해 보존했다. Claude는 파일 수정·테스트·model turn·하위 에이전트를 사용하지 않았다.
- `docs/design/sdk-routing-s2-intermediate-spec.md`를 revision 4 candidate로 다시 작성했다. 과거 S1 manifest 분기를 보존하는 additive schema, 기존 S1 export 재검증 1회, stage별 `route_decision_allowed` exact 결합을 명시했다.
- 최초 예산은 네 Cell의 최초 Task 12 turns를 먼저 보전하고 B1 retry/resume 전용 reserve 3을 분리하는 최대 15-turn 안으로 제안했다. 역순 profile pair는 base 6 + reserve 3의 최대 9 turns이며 각각 새 사용자 승인을 요구한다. 이 문서 선택은 live model 사용 승인이 아니다.
- 최초 단일 pair에서는 route를 발행하지 않고 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`만 기록한다. 역순은 정확히 한 Variant만 성공하거나 봉인된 B1 control effect가 있을 때만 열며, 1.50/2.00 비율과 사람의 모델 변동 판단은 확대·route에서 삭제했다.
- config fixture는 exact import·signature·오류 class·CLI 계약을, incident fixture는 Worker 공개 topic catalog·`canonical_claim_text`·exact JSON key·report/action render를 갖도록 수정했다. property 결과는 `judge/posthoc`에 별도 봉인하고 profile 성공은 Judge AND property로 유도한다.
- 짧은 S2 Cell ID, 40자 state root, freeze path preflight, fixture tree 밖 golden, `s2_posthoc_property_contracts` regression record, B1 3,300초 adapter timeout과 retry first/full outcome 이중 보고를 명시했다.
- `docs/reviews/benchmark-runner/claude-rereview-prompt-sdk-routing-s2-intermediate-spec.md`에 이전 P0/P1 closure만 확인하는 집중 재심사 프롬프트를 작성했다. 현재 다음 관문은 이 재심사와 사용자 동결이며 구현·시험·model turn은 아직 0건이다.

## SDK 라우팅 S2 revision 4 집중 재심사와 revision 5 동결 후보

- 작업일: 2026-08-08. Claude 집중 재심사는 `경미한 수정 후 동결`로 판정했다. 이전 P0 6건은 모두 closed, 이전 P1은 9건 closed·P1-7 partially closed였고 새 P1 2건이 발견됐다. 구조 재설계나 재실행은 요구하지 않았다.
- 재심사는 B1 공개 report에 per-attempt turn·token·Judge 값이 없다는 사실, C2가 Task 실패 시 조기 반환할 수 있다는 사실, incident status 값 도메인이 report section 검증에 필요하다는 사실을 코드와 대조했다. 파일 수정·테스트·model turn·하위 에이전트는 0건이었다.
- `docs/reviews/benchmark-runner/claude-rereview-sdk-routing-s2-intermediate-spec.md`에 closure 표, 새 P1 세부와 확인 사실을 정규화해 보존했다.
- `docs/design/sdk-routing-s2-intermediate-spec.md`를 revision 5 사용자 동결 후보로 갱신했다. B1 reserve는 봉인된 `b1_retry_count + b1_resume_count`로 직접 차감하며 C2/B1의 미소비 최초 turn은 다른 Cell reserve로 재배정하지 않는다. 이는 Claude가 제안한 `actual_turns - task_count` 식이 B1 조기 종료에서 실제 retry를 가릴 수 있는 경계까지 닫는다.
- incident contract는 evidence `observed|reported|derived`, event `confirmed|conflicting|uncertain`, claim `confirmed|conflicting` 값 집합과 claim status의 report section mapping을 고정했다. 공개 catalog의 conflicting topic claim은 confirmed가 될 수 없다.
- retry 이중 보고는 현재 B1 공개 report에서 관측 가능한 first-attempt Task state·failure kind와 full-run state·Judge·turn·usage로 축소했다. per-attempt 비용은 `not_available`로 기록하고 추정하거나 B1 report schema를 확장하지 않는다.
- stage discriminator가 반대 stage bytes를 받아들이는 완화형 회귀를 막기 위해 S1/S2 분기 상호 거부 음성 계약 시험 1건을 기존 표적 model-free 시험 예산에 포함했다. 새 하네스·추가 전체 회귀·교차 clone은 추가하지 않았다.
- 현재 남은 관문은 revision 5의 사용자 동결이다. 구현·시험·model turn은 아직 시작하지 않았고 live 사용 승인은 별도다.

## SDK 라우팅 S2 revision 5 사용자 동결

- 작업일: 2026-08-08. 사용자가 `docs/design/sdk-routing-s2-intermediate-spec.md` revision 5를 구현·시험 정본으로 승인했다. 문서 상태를 `frozen_before_implementation`으로 바꾸고 사용자 동결일을 기록했다.
- 동결 문서는 526줄·36,948 bytes이며 SHA-256은 `1b5046b667bb6b3cc7c882bb3124dec4d8b9fe7ff4363471586aa24d94db1dc5`다.
- 동결 범위는 manifest 하위 호환, 두 3-Task fixture, post-hoc property, 최초 base 12 + B1 reserve 3의 최대 15-turn 예산, 역순 확대와 결정론적 route, 구현·검증 예산이다.
- 이 승인은 명세 동결이며 S2 live model 사용 승인이 아니다. 다음 기술 단계는 기존 Runner의 stage-generic 최소 확장과 fixture/property 구현이다. 최초 live 4 Cell은 구현·시험·실행 후보 동결 뒤 최대 15 turns를 적은 별도 사용자 승인을 받아야 한다.
- 사용자 승인 시점까지 구현·테스트·model turn·하위 에이전트·commit·push는 실행하지 않았다.

## SDK 라우팅 S2 revision 5 구현 후보

- 작업일: 2026-08-08. 사용자 승인 뒤 기존 Benchmark Runner를 stage-generic하게 확장했다. S1/S2 stage는 discriminator가 분리된 strict 계약으로 읽고, 기존 S1 manifest·Plan·비라이브·live 경로는 호환 wrapper로 유지했다. S2를 위한 두 번째 Controller나 별도 상태 기계는 만들지 않았다.
- `three-stage-config-migration`과 `three-stage-incident-analysis` 3-Task fixture, fixture 밖 golden, 각 5개 사후 property checker를 구현했다. 사후 검사는 공통 Judge 뒤, Measurement·seal 전에 C2/B1에 동일하게 실행되며 checker 오류와 workspace 변경을 fail-closed로 처리한다.
- 최초 S2 Plan은 4 Cell·base 12 turns와 B1 retry/resume 전용 reserve 3, 최대 15 turns를 고정한다. 남은 reserve는 앞서 봉인된 B1 Measurement의 retry+resume만 차감하고, 미소비 최초 turn은 재배정하지 않는다. B1 추가 turn이 있으면 first-attempt Task 결과와 전체 오케스트레이션 결과를 함께 봉인하고 Attempt별 비용은 `not_available`로 둔다.
- `routing-policy-v1`은 봉인된 Cell·Measurement·Judge·property·resource·B1 control field만으로 단일-pair 관측, 역순 확대 필요, 잠정 B1 route, B1 제외 또는 inconclusive를 유도한다. source·Runner·Variant·checker identity와 Measurement/seal 참조를 함께 보존하고 전역 B1 기본값은 발행하지 않는다.
- S2 표적 model-free 시험은 `15 passed`다. pristine 실패, golden 통과, 10개 property 개별 mutation 거부, C2/B1 label parity, stage 상호 거부, 독립 reserve, Fake 4-Cell Plan→Judge→property→seal→export, 확대 조건과 역순 잠정 route를 포함한다. 실제 model turn은 0회다.
- 최종 기존 계약은 S0 `9 passed`, B1 retry `3 passed`를 통과했다. B1 전체는 대체 Python 경로에서 SDK 패키지를 처음 찾지 못해 `68 passed, 6 failed`였고 같은 여섯 환경 표적을 기존 venv package 경로로 바로잡아 `6 passed`로 확인했다. B1 코드 실패는 남지 않았다.
- Runner 전체의 첫 실행은 `206 passed, 12 failed`였다. 9건은 저장소 내부의 긴 basetemp가 R6 외부 격리·Windows 경로 계약을 위반한 시험 환경 오류였고 짧은 외부 basetemp에서 통과했다. 2건은 대체 Python의 `sys.prefix` 밖에 있던 기존 SDK·PyYAML을 임시 venv에 연결해 통과했다. 마지막 1건을 조사하면서 Python 3.12.10과 두 프로젝트 venv가 실제로는 정상이며 Codex 파일 샌드박스가 사용자 프로그램 폴더 실행을 거부해 없어진 것처럼 보였음을 확인했다. 기존 B1 venv를 승인된 실행 경계에서 사용해 exact `3.12.10` live-freeze runtime 관문도 `1 passed`로 통과했다. 따라서 실패 표적을 포함한 Runner 218개 계약 경로를 모두 확인했으며, Docker나 Python 재설치는 하지 않았다.
- 기존 S1 export는 현재 verifier로 정확히 한 번 재검증했다. Experiment `exp_20260807_d1e9fdb8_1`, `CALIBRATION_PASS`, 108 files, export SHA-256 `ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8`이 그대로다.
- 현재 결과는 구현 후보이지 live 실행 후보 동결이 아니다. fixture를 포함한 source commit/tree identity, revision 3 suite manifest, frozen S2 stage·fixture manifest, clean source의 regression record와 freeze artifact는 아직 만들지 않았다. 기존 Python 3.12.10 venv를 사용해 source commit 뒤 clean regression record와 freeze 전용 경로 preflight를 통과해야 한다. commit·push와 실제 model turn은 0회다.

## SDK 라우팅 S2 live 실행 후보 revision 2 동결

- 작업일: 2026-08-08. S2 구현·fixture를 `59694b4d30d4910e59d1c146644a57ec8fbc63ae`에, suite revision 3과 frozen stage·fixture identity를 `76c30b455cf98a10cdf666ff9a0ba2699e3b9213`에 커밋했다. 최종 실행 source commit은 `56c91334fb32c4699d11ef80769831f14a0431d6`이다.
- 기존 Python 3.12.10 B1 venv와 bundled Codex CLI 0.144.4를 사용했다. `codex login status`는 `Logged in using ChatGPT`, 금지된 `OPENAI_API_KEY`·`CODEX_API_KEY` 환경 이름은 0개였다. Docker·WSL·Python 재설치는 하지 않았다.
- source-bound 최종 회귀 record는 S0 gate `9 passed`, B1 retry 계약 `3 passed`, B1 전체 `74 passed`, Benchmark Runner 전체 `219 passed`, S2 post-hoc 계약 `16 passed`다. 실제 model turn은 0회다.
- 최초 revision 1 create는 실제 model turn 전에 fixture manifest의 `model` block이 기존 verifier의 exact 두 필드 계약보다 넓어 fail-closed로 중단됐다. 런타임 제어는 이미 Plan environment에 봉인되므로 manifest 중복 필드 4개를 제거하고 exact 계약 시험을 추가했다. 원인·대안·해결은 `DEV-20260808-001`에 기록했으며 실패 state와 artifact는 실행 후보 밖 외부 경로에 보존했다.
- 성공한 revision 2 artifact는 `benchmarks/artifacts/sdk-routing-s2-v1-56c9133-r2/`이다. Experiment는 `exp_20260808_5f4f41a7_2`, Plan fingerprint는 `5f4f41a7fe53f29e13095b7992f3ed24ef7ed8af6d0e4e02f16213ce29ecf373`, raw Plan SHA-256은 `fcc5fe129fb0ad62f8eda697252f11cfa3b02c184cb11c4a2a15fb9866ce68f4`, freeze SHA-256은 `24c7d4a96d993ccaffdc81c70da878d7c172375e0d71e7e8a617a53daadae980`이다.
- 별도 clean checkout·별도 process의 Plan build가 동일했고 4개 Cell 경로 preflight의 최대 생성 경로 길이는 모두 105자였다. verifier는 source commit·Python/Git path hash·7개 sealed source file을 다시 확인했다.
- status에서 `cell_s2_a_1_c2`, `cell_s2_a_1_b1`, `cell_s2_b_1_b1`, `cell_s2_b_1_c2`는 모두 `PLANNED`다. sealed 0, actual model turn 0, 남은 B1 retry/resume reserve 3, route 미발행, `S2_INCOMPLETE`, stop 없음이다.
- 다음 행동은 반복 검증이나 새 하네스가 아니다. 사용자가 최초 4-Cell Plan과 절대 상한 15 turns를 별도로 승인할 때만 같은 동결 state에서 순차 실행한다. 승인 전에는 `create`, 회귀, freeze 재검증, live Cell, 역순 확대, S3를 실행하지 않는다.

## SDK 라우팅 S2 최초 live 4-Cell 완료와 정식 export

- 작업일: 2026-08-08. 사용자가 최초 S2 4-Cell Plan과 최대 15 model turns를 승인해 동결된 `exp_20260808_5f4f41a7_2`를 config C2→B1, incident B1→C2 순서로 실행했다. 4개 모두 `completed`·`SEALED`, Judge 성공에 도달했다.
- 각 Cell은 정확히 3 turns를 사용해 전체 actual model turn은 12회다. B1 두 Cell의 retry·resume와 intermediate control effect는 모두 0이며 전용 reserve 3 turns는 사용하지 않았다.
- Config migration은 C2/B1 모두 사후 속성까지 통과했다. B1은 token 7.6% 감소, wall-clock 6.9% 증가였고 단일 pair에 품질 차이나 control effect가 없어 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`, route 미발행으로 남았다.
- Incident analysis는 C2가 사후 속성까지 통과했지만 B1은 공개 Judge 성공 뒤 `INC-P1`, `INC-P3`에 실패했다. evidence source locator가 원 source line과 어긋났고 action이 허용된 evidence/uncertainty ID 대신 hypothesis ID를 참조했다. B1은 C2보다 token 20.2%, wall-clock 6.6% 많았다.
- 최초 incident 순서가 B1→C2인 단일 pair이므로 B1 제외 route를 즉시 발행하지 않았다. terminal state는 `S2_EXPANSION_REQUIRED`, route와 global B1 default는 모두 미발행이다.
- 정식 export 63개 파일을 `benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_5f4f41a7_2/`에 보존했다. export SHA-256은 `5577d8bf54352a9b9930331e3c99d1af761d85211b197ebb9c959cee6de83d55`이며 정확한 경로에서 verifier가 freeze·Measurement·post-hoc·policy·전체 파일을 다시 열어 통과했다.
- 사람용 해석은 `docs/experiments/sdk-routing-s2-live-result.md`에 기록했다. 다음 후보는 incident profile의 반대 순서 C2→B1 pair이며 별도 새 Plan과 최대 9 model turns 사용자 승인이 필요하다. Config 확대와 S3는 시작하지 않는다.

## SDK 라우팅 S2 incident 역순 live pair 완료

- 작업일: 2026-08-08. 사용자가 incident profile의 반대 순서 실행과 별도 최대 9 model turns를 승인했다. 기존 정책 계산기를 바꾸거나 새 하네스를 만들지 않고, stage-generic live controller에 최초 export 결박·선택 profile 역순 Plan·결합 status/export 경로를 연결했다.
- source commit `faecb246ec442b79d375ad4ebd51a230dca11c1e`의 회귀 record는 S0 `9 passed`, B1 retry `3 passed`, B1 전체 `74 passed`, Runner 전체 `220 passed`, S2 표적 `17 passed`다. Candidate artifact commit은 `4507686`이다.
- 첫 zero-turn create는 역순 Plan이 선택하지 않은 config fixture identity까지 유지해 preflight semantics 집합 검증에서 fail-closed로 중단됐다. 역순 Plan fixture를 승인된 incident profile 하나로 제한했고 `DEV-20260808-002`에 원인과 해결을 기록했다. 거부된 artifact 8개와 외부 state 파일 46개는 정확한 두 경로 확인 뒤 삭제했으며 model turn은 0회였다.
- 최종 candidate는 `benchmarks/artifacts/sdk-routing-s2-reverse-faecb24-r3/`이다. Experiment `exp_20260808_e2f0a870_3`, Plan fingerprint `e2f0a870804075172b0d6ccaccb643ff2b03e161beed1592fc9edfe87650ccae`, raw Plan SHA-256 `1fc920efdfe4f1e3d44c61b0b2aa062d6e2ff8167c3fe3f09e3a85ff4f39a070`, freeze SHA-256 `555dd4297d1a7c4bd012fb4f75f1bd74298be3df3f1da0acfa128a9bc031bc7d`이다.
- C2→B1 두 Cell은 각각 3 turns로 `completed`·`SEALED`, 공개 Judge 성공에 도달했다. C2는 320,404 tokens·180.390초이며 사후 `INC-P2`에 실패했다. B1은 320,581 tokens·208.141초이며 사후 `INC-P1`에 실패했다. B1 retry·resume와 control effect는 0이고 reserve 3 turns는 미사용이다.
- 최초 B1의 `INC-P1`은 역순에서도 관측됐지만 최초 `INC-P3`는 재현되지 않았고, 최초에 성공한 C2도 역순 `INC-P2`에 실패했다. 두 frozen route 조건 모두 충족되지 않아 결합 stage는 `S2_POLICY_READY`, incident profile은 `ROUTING_INCONCLUSIVE`, route와 global B1 default는 미발행이다.
- 최초 63-file export 전체를 포함한 결합 export는 102개 파일이며 `benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/`에 보존했다. aggregate SHA-256은 `df682d5a13945bc8cc9ef0b3a468800112c720fada89eca2f10bd6b46ae72bc8`이다. 사람용 보고서는 `docs/experiments/sdk-routing-s2-reverse-live-result.md`다. S3는 자동으로 열지 않는다.

## SDK 라우팅 S3 complex/high-risk revision 1 명세 후보

- 작업일: 2026-08-08. 사용자가 S2 `ROUTING_INCONCLUSIVE` 뒤 S3 명세 작성과 Claude read-only 심사를 요청했다. 이 단계에서는 구현, fixture·checker 생성, 테스트, 실제 model turn, 하위 에이전트 호출을 하지 않았다.
- `docs/design/sdk-routing-s3-complex-high-risk-spec.md`에 revision 1 `review_candidate`를 작성했다. 419줄·26,222 bytes, SHA-256 `420828ad1993f441e778ec98237d028ee4965a51f2ac46eec26ca4a53e06e0ac`다.
- S3 질문을 “4-Task high-risk 작업에서 B1 Task 경계·중간 Check·retry/resume가 C2가 남기는 실제 결함을 차단·수정하는가”로 제한했다. 단순 Variant 승패는 route 근거가 아니며 최초 Check 실패→downstream 차단→reserve turn 수정→같은 Check 통과→C2 mapped property 실패가 봉인돼야 attributable control effect로 센다.
- Fixture A는 4단계 compatibility refactor, Fixture B는 다중 predecessor conflicting incident report다. 두 fixture 모두 공개 입력·Check·property 관계만 사용하며 hidden golden, Variant별 fixture와 비공개 정답은 금지했다.
- 최초 Plan은 4 Cell base 16 + B1 profile별 reserve 2의 최대 20 turns다. Mechanistic replication predicate가 있는 profile만 반대 순서 pair를 별도 최대 10 turns로 한 번 열 수 있다. 두 order의 같은 control/property 패턴이 재현되지 않으면 `ROUTING_INCONCLUSIVE`로 닫고 S4·세 번째 pair·추가 synthetic fixture를 금지했다.
- 기존 stage-generic Runner·controller·runtime·Adapter·Judge·Measurement·seal을 재사용한다. 새 S3 controller·상태 기계·하네스, S1/S2 재실행과 artifact 변경은 허용하지 않는다. 구현 전 관문은 Claude 심사와 사용자 동결이다.
- Claude 전체 심사 정본은 `docs/prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-complex-high-risk-spec.md`, 95줄·7,744 bytes, SHA-256 `4828e03edf743c9140324444115ba652e8f99c8f93c5cf06965e709b165be701`이다. 새 세션 복붙 입력은 `docs/prompts/benchmark-runner/claude-session-input-sdk-routing-s3-review.md`, 15줄·1,105 bytes, SHA-256 `f2f093b5dcc5bc221af84a02c88add809c48cec1dbfdbc619a60999cee7d8ff8`다.
- 심사는 파일 수정·테스트·model turn·하위 에이전트 없이 명세 동결 가능성만 판정한다. 추가 시험을 권고할 때 어떤 route·동결 결정·fail-closed 경계를 바꾸는지 요구하며, 무결정 재검증·반복 전체 회귀·cross-clone·P1-zero gate·새 하네스 권고를 금지했다.

## SDK 라우팅 S3 revision 1 Claude 심사와 revision 2 closure 후보

- 작업일: 2026-08-08. Claude read-only 심사는 revision 1을 `경미한 수정 후 동결`로 판정했다. 지적은 P0 1건·P1 5건·P2 4건·P3 0건이며, 추가 시험·cross-clone·전체 회귀 없이 명세 문언만 수정해 닫을 수 있다고 했다. 심사 원문은 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md`, 249줄·25,528 bytes, SHA-256 `7b08a47cbbca63445cc21d4374766b71de5c28965660b9140cabb23138916709`로 첨부 원문과 byte-identical하게 보존했다.
- P0은 A2 시점에 평가 불가능했던 `HCR-P5`를 migration idempotence `HCR-P5a`와 pipeline idempotence `HCR-P5b`로 나누고 A2와 A3/A4에 각각 연결해 닫았다. `HCR-P6`은 safety/integrity 전용이며 route 귀속 대상이 아니라고 고정했다.
- 단일 order 확대 조건은 `single_order_b1_quality_failure`, 두 order 최종 reject 조건은 `repeatable_quality_regression`으로 분리했다. 선행 S1+S2 live Cell 14개에서 B1 retry·resume·attributable control effect가 0회였음을 사전 기대와 residual uncertainty에 기록하고, inconclusive를 B1 열등 판정으로 확대하지 않도록 했다.
- S2 §7의 post-hoc isolated subprocess·exact result schema·120초·`profile_success`·checker error 계약을 상속했다. S3 checker/golden/result 경로를 고정하고 S2 결과 data 비재사용과 실행·seal 계약 재사용을 분리했다. Resolved state root 40자와 실제 frozen fixture 최장 경로·Git object write preflight를 live DoD에 넣었다.
- 기존 `routing_suite.py`와 `routing_live.py`는 exact S1/S2/S3 분기와 stage별 reverse gate state·Task/예산 parameterization으로 확장한다. `s3_posthoc.py`는 허용하고 `s3_policy.py`와 새 S3 controller는 금지하며 역사적 `s2_policy.py`에 S3 함수를 additive하게 넣는 정책을 선택했다. Worker의 Cell-local scope 위반은 상대 Variant로 pair만 닫은 뒤 stage를 종료하고 전역 무결성 실패는 즉시 전체 정지한다.
- Revision 2 명세는 450줄·34,035 bytes, SHA-256 `1d7accba63189ef812c48fd9bd24f13db1344ce80473671f58f3a37379530797`다. Claude closure 재심사 정본은 `docs/prompts/benchmark-runner/claude-rereview-prompt-sdk-routing-s3-complex-high-risk-spec.md`, 86줄·4,686 bytes, SHA-256 `4df42df42f3f061b4d98abaac9aa96987e4642136e240a527da82afc1c24b35a`이며 새 세션 입력은 13줄·910 bytes, SHA-256 `ce460850aa280ac808226d6b7ae23d426ae421f5413890eb5a1438c0ecbfe5fa`다.
- 이번 작업은 명세 closure와 재심사 입력 작성뿐이다. 구현·fixture 생성·테스트·verifier·model turn·live Cell·하위 에이전트 호출은 0회이며, 다음 관문은 Claude의 closure 집중 재심사와 사용자의 명세 동결이다.

## SDK 라우팅 S3 revision 2 closure 재심사 통과

- 작업일: 2026-08-08. Claude가 commit `1f8fc8c438e4e4ac9b69a0a49e20686bbe8ba077`의 revision 2를 전체 재감사가 아닌 closure 범위로 read-only 재심사했다.
- 최종 판정은 `동결 가능`이다. P0-01과 P1-01~P1-05는 모두 `CLOSED`, 수용한 P2-01~P2-04는 모두 `ACCEPTED_CLOSED`이며 새 P0/P1과 사용자 미결정 항목은 각각 0건이다.
- 재심사는 P5a/P5b 시간적 mapping, stage-neutral reverse builder와 S1/S2/S3 gate 분리, 단일 order와 반복 회귀 술어 분리, retain arm 도달성·residual uncertainty, post-hoc subprocess·seal 계약, 40자 state root와 실제 최장 경로 preflight를 closure 근거로 확인했다.
- 원문은 `docs/reviews/benchmark-runner/claude-rereview-sdk-routing-s3-complex-high-risk-spec.md`, 65줄·7,567 bytes, SHA-256 `f3682a0c95ae7df82fca2144d4f382b119ddaa35feead58ffbe16c79320f70b1`로 첨부와 byte-identical하게 보존했다.
- 이번 단계에서도 파일 보존과 운영 문서 갱신 외 구현·fixture 생성·테스트·verifier·script·model turn·live Cell·하위 에이전트 호출은 하지 않았다. Claude의 기술 심사 통과는 사용자 동결 승인을 대신하지 않으므로 S3 명세 상태는 `review_candidate`로 유지하며, 다음 관문은 사용자의 명시적 동결 승인이다.

## SDK 라우팅 S3 revision 2 사용자 동결

- 작업일: 2026-08-08. 사용자가 Claude closure 재심사를 통과한 `docs/design/sdk-routing-s3-complex-high-risk-spec.md` revision 2를 구현·시험 정본으로 명시 승인했다.
- 문서 상태를 `frozen_before_implementation`으로 바꾸고 사용자 동결일과 revision 2 재심사 근거를 header에 기록했다. 설계 본문, Task graph, property mapping, 최초 20-turn·역순 10-turn 예산, route 술어와 종료선은 변경하지 않았다.
- 동결 문서는 452줄·34,278 bytes, SHA-256 `f2ef81fa39119610345576252c4bb35b7dee395ed895af9f10dd00b301fc8b81`다.
- 이 승인은 명세 동결만 의미한다. 구현·fixture 생성·model-free 테스트·candidate freeze·model turn·live Cell은 시작하지 않았으며 구현 착수에는 별도 사용자 지시가 필요하다.

## SDK 라우팅 S3 구현과 zero-turn 실행 후보 동결

- 작업일: 2026-08-08. 사용자 구현 승인 뒤 frozen revision 2 범위만 기존 Benchmark Runner에 추가했다. 구현 source는 `03eb4a772893130cd3d1000b12fe8a20e0e3643a`, candidate artifact commit은 `b8e6b76`이다.
- 두 4-Task fixture, 공개 Check 8개, fixture 밖 golden, HCR/HCI post-hoc checker와 S3 policy를 구현했다. 새 S3 controller·runtime·Adapter·Judge·Measurement·seal·상태 기계는 만들지 않고 기존 `routing_suite.py`, `routing_live.py`, 역사적 `s2_policy.py`를 stage-generic하게 확장했다.
- 최초 Plan은 compatibility C2→B1, incident B1→C2의 4 Cell, base 16 + profile별 B1 retry/resume reserve 2씩, 절대 상한 20 turns다. Control attribution 양성·음성, 최초 replication, 역순 retain/reject, inconclusive, profile-local reserve와 S1/S2/S3 상호 거부를 deterministic 시험으로 고정했다.
- 최종 source-bound 회귀는 S0 `9 passed`, B1 retry `3 passed`, B1 전체 `74 passed`, Runner 전체 `239 passed`, S3 표적 `19 passed`다. 첫 S0 시도는 pytest 임시 부모 누락, 첫 Runner 전체 시도는 repo 내부 긴 임시 경로가 Windows/R6 경로 계약을 위반해 setup에서 실패했으며 올바른 전용 경로에서 실패 묶음만 재실행했다. 제품 코드 수정과 model turn은 없었고 성공 실행만 regression record에 봉인했다.
- Candidate는 `benchmarks/artifacts/sdk-routing-s3-v1-03eb4a7-r1/`, Experiment `exp_20260808_66099ac3_1`, Plan fingerprint `66099ac3aa51e8184a8e0bec4ff86db722f891f0765bf2d74f602aaf761117e2`, raw Plan SHA-256 `a71bec8b8217b3f8ef5e3ed70cb592c6f83c37fd814ad4d260ac316181111c0d`, freeze SHA-256 `d574323a86002dd93d18313e33afd3fee121a3a8ffe025c232cde44d20c3559d`다.
- 별도 clean checkout·별도 process Plan build가 동일했고 resolved state root는 `C:\s3-03eb4a7-r1` 16자, 네 실제 경로 preflight 최대 길이는 각각 114자였다. SDK preflight는 네 Cell 모두 ChatGPT account, SDK 0.144.4, API key 환경 이름 0개, actual model turn 0을 확인했다.
- Status는 네 Cell 모두 `PLANNED`, sealed 0, actual/combined model turns 0, `S3_INCOMPLETE`, route 미발행, stop 없음이다. 구현 보고서는 `docs/experiments/sdk-routing-s3-implementation-freeze.md`다.
- Claude 구현 심사 정본은 `docs/prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-implementation-freeze.md`, 새 세션 복붙 입력은 `docs/prompts/benchmark-runner/claude-session-input-sdk-routing-s3-implementation-review.md`다. 둘 다 diff·artifact read-only 심사만 허용하고 테스트·verifier·model turn·하위 에이전트를 금지한다.
- 다음 관문은 Claude의 구현 diff·artifact read-only 심사다. 재테스트·verifier·새 구현은 하지 않는다. 심사 뒤에도 최초 네 Cell과 최대 20 turns는 별도 사용자 승인 없이는 실행하지 않으며, 조건부 역순은 최초 결과가 `S3_REPLICATION_REQUIRED`를 낸 profile에 대한 별도 최대 10-turn 승인으로만 연다.

## SDK 라우팅 S3 구현·동결 Claude read-only 심사 통과

- 작업일: 2026-08-08. Claude가 `ac27997..03eb4a7` 구현 diff와 `b8e6b76` candidate artifact를 테스트·verifier·model turn·하위 에이전트 없이 읽기 전용으로 심사했다. 최종 판정은 `실행 후보 승인 가능`, P0 0건, P1 0건, live 전에 반드시 고칠 항목 0건이다.
- 명세 coverage는 initial 4-Cell 순서, S1/S2/S3 discriminator, checker 격리·schema, 두 fixture Task graph, P5a/P5b 분리, HCR-P6 safety 제외, control attribution, 최초·역순 정책표, 20/10-turn 예산, profile-local reserve, local/global stop, 기존 controller 재사용과 40자 state-root preflight까지 모두 `일치`로 판정됐다.
- Artifact의 source commit, Plan fingerprint, Experiment ID, 독립 build, exact 회귀 5종, ChatGPT preflight, TaskEnvelope parity, checker identity와 zero-turn freeze seal도 모두 `OK`로 확인됐다. 실제 live 완주, checker 120초 완료와 WinError 5 재발 여부는 실행 전에는 확인할 수 없는 항목으로 남겼다.
- 비차단 개선은 property 입력 deep copy(P2-a), protected path 방어 중복(P2-b), 공용 controller의 S1 명칭(P3-c) 세 건이다. 현재 기능·결정론·scope·fail-closed를 깨지 않고, 반영하면 동결 source identity를 바꿔 candidate 재생성이 필요하므로 이번 후보에는 적용하지 않는다. 실제 결과 뒤 별도 maintenance 후보로 보존한다.
- 심사 원문은 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-implementation-freeze.md`다. 다음 관문은 네 initial Cell의 정확한 순서와 최대 20 model turns에 대한 사용자 승인뿐이며, 승인 전 추가 구현·재검증·candidate 재생성·`run-next`는 하지 않는다.

## SDK 라우팅 S3 initial live 완료와 synthetic 종료

- 작업일: 2026-08-08. 사용자가 frozen initial 네 Cell 전체와 최대 20 model turns를 승인했다. Controller 순서 `cell_s3_a_1_c2` → `cell_s3_a_1_b1` → `cell_s3_b_1_b1` → `cell_s3_b_1_c2`로 실행했고 네 Cell 모두 4 turns, `completed`·`SEALED`, 공개 Judge 성공에 도달했다. Infrastructure·controller·seal·scope·secret·WinError 5 오류는 없었다.
- 총 actual model turn은 16회, token은 1,489,373, Measurement 합산 wall-clock은 863.563초다. 두 B1 Cell 모두 retry·resume·intermediate control effect 0이며 profile별 reserve 2 turns는 사용하지 않았다.
- Compatibility profile은 C2/B1 모두 HCR post-hoc까지 통과해 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`다. B1은 C2보다 token 11.3%, wall-clock 6.2% 많았지만 단일 pair 효율 관측은 route 근거가 아니다.
- Incident profile은 C2/B1 모두 공개 Judge 성공 뒤 HCI-P1~P6 전체가 post-hoc `fail`로 봉인됐다. 두 `final-report.md`가 exact 한글 heading grammar를 위반했고 report 선행 parse 예외가 checker의 fail-closed 경로에서 모든 HCI를 실패 처리했다. 따라서 여섯 독립 결함을 각각 주장하지 않고 공통 report grammar 오류로 세부 판별이 닫혔다고 해석한다.
- Incident B1은 C2보다 token 21.3%, wall-clock 25.0% 많았으나 양쪽 모두 profile 실패이고 B1 control effect가 없어 귀속할 수 없다. Profile은 `ROUTING_INCONCLUSIVE`, stage는 `S3_INCONCLUSIVE`, replication·route·global B1 default는 모두 미발행이다.
- 정식 export 63개 파일을 `benchmarks/results/sdk-routing-s3-v1/exp_20260808_66099ac3_1/`에 보존했다. Aggregate SHA-256은 `16fcfddf337dc0b9244b99c816c4026414798543490e47f0194b33887b06adce`이며 verifier가 freeze·Measurement·Evidence·post-hoc·policy·exact 파일 집합을 다시 열어 통과했다.
- 사람용 보고서는 `docs/experiments/sdk-routing-s3-live-result.md`다. Frozen 종료선에 따라 역순 pair·세 번째 pair·추가 synthetic fixture·S4를 열지 않고 이번 시험을 종료한다. Checker의 전역 parse fail-closed와 public Check grammar 범위는 별도 maintenance 후보일 뿐, 현재 봉인 결과를 고치거나 처음부터 자동 재실행하지 않는다.

## 현실 고난도 Phase B 최초 중단과 SDK profile provenance 교정

- 작업일: 2026-08-09. 기준 source commit은 `5fe78aa5c6a357c08682684a258b41e7d84c4dbc`다. 사용자가 승인한 최초 model-free Phase B 실행은 SDK empty thread 생성 뒤 `SDK :workspace profile provenance was not proven`으로 P01 전에 fail-closed 중단됐다. 실제 model turn과 P01~P08 실행은 각각 0회이며 candidate bundle은 생성되지 않았다.
- 중단 원인은 sandbox 자체가 아니라 수집 계약이었다. 구현은 `thread/start`가 `thread/settings/updated`를 발생시킨다고 가정해 10초 동안 기다렸지만, 해당 notification은 thread 생성의 보장 이벤트가 아니다. 실패한 W/J/S root와 pending manifest는 삭제·정리·재사용하지 않고 보존했다.
- 동일 pinned `codex.exe`가 `app-server generate-json-schema --experimental`로 직접 생성한 protocol을 확인했다. 실제 executable surface에는 `thread/start.permissions`, `ThreadStartResponse.activePermissionProfile`, `permissionProfile/list`, `thread/started`가 있지만 설치된 Python generated response model은 이 필드 일부가 뒤처져 있었다.
- 교정 구현은 raw JSON-RPC로 `permissionProfile/list(cwd=W)`의 유일한 `:workspace`가 `allowed=true`인지 확인하고, `thread/start`에 `permissions=":workspace"`를 직접 보낸다. 통과하려면 raw response의 active profile·approval·cwd와 보장된 `thread/started`의 thread ID가 모두 맞아야 한다. legacy `sandbox` response는 여전히 provenance로 인정하지 않고 `turn/start` 0회를 강제한다.
- profile 실패는 이제 재계산된 구체적 reason code와 전체 방향 결합 transcript를 exact 4-file candidate bundle 밖의 `<bundle>.profile-failure.json`에 남긴다. 같은 경로의 자동 재시도와 실패 파일 덮어쓰기는 거부한다.
- 수정된 profile 계약·허용 거부·thread mismatch/turn 관측·raw collector 호출·failure artifact·기존 bundle 재검증을 포함한 표적 단위시험은 `8 passed`다. 첫 호출은 사용자 프로그램 폴더의 Python 실행을 샌드박스가 막아 시험 수집 전에 종료됐고, 승인된 실행 경계에서 같은 명령을 실행해 통과했다. `py_compile`과 `git diff --check`도 통과했다.
- 이번 수정에서는 전체 회귀, 실제 SDK handshake 재호출, P01~P08, model turn을 실행하지 않았다. 기존 pending manifest는 source commit이 바뀌므로 새 실행 후보에 사용할 수 없다. 다음 실제 Phase B는 이 수정 commit을 기준으로 새 manifest와 새 root token을 만들고 별도 실행 지시가 있을 때만 한 번 수행한다.

## 현실 고난도 Phase B effective-policy 교정과 P01 중단

- 작업일: 2026-08-09. source `ea4e1db01e2def366a1b7fd133f8e0a22976b2cc`의 `phaseb-20260809-002`는 SDK profile 통과 뒤 effective-policy 관문에서 중단됐다. 당시 구현은 policy 실패 surface를 보존하지 않아 세부 원인을 복구할 수 없었고, actual model turn과 P01~P08 실행은 모두 0회였다.
- commit `3a74545e013131a86a11885adf182f104dcf4ba9`에서 profile transcript, redacted policy projection, requirements/readiness response와 재계산 reason code를 exact candidate bundle 밖의 `<bundle>.policy-failure.json`에 기록하고 같은 경로 덮어쓰기·자동 재시도를 금지했다. 관련 표적 시험은 `9 passed`다.
- source `3a74545e013131a86a11885adf182f104dcf4ba9`의 `phaseb-20260809-003`은 같은 관문에서 중단됐지만 새 증거가 `LEGACY_SANDBOX_MODE_PRESENT`, `LEGACY_SANDBOX_WORKSPACE_WRITE_PRESENT`를 확정했다. 동시에 `default_permissions=:workspace`, active profile `:workspace`, `windows.sandbox=elevated`, readiness `ready`, ChatGPT account, turn/start 0회를 확인했다.
- pinned app-server Schema에서 두 legacy field는 optional이며 값이 없을 때도 top-level config에 `null`로 직렬화될 수 있다. 기존 판정은 key 존재만으로 legacy 사용이라 오판했다. commit `b59a78031bf95f8d0691316ecc8dee1394da67c1`에서 `null`은 미사용, non-null만 실제 legacy 설정으로 차단하도록 좁게 고쳤고, null 허용·non-null 거부 회귀를 포함한 표적 시험 `9 passed`, `py_compile`, `git diff --check`를 통과했다.
- source `b59a78031bf95f8d0691316ecc8dee1394da67c1`의 `phaseb-20260809-004`는 profile·effective policy·readiness·requirements·Controller identity 관문을 통과하고 P01을 정확히 1회 dispatch했다. 그러나 wrapper stdout이 빈 값 또는 JSON이 아닌 값이어서 `runtime-boundary probe stdout is not one JSON object`로 중단됐다. P02~P08은 실행하지 않았고 actual model turn은 0회이며 candidate bundle은 생성되지 않았다.
- 현재 P01 failure path는 capped stdout/stderr를 메모리에서 수집하지만 JSON parse 전에 실패하면 이를 artifact로 남기지 않는다. 따라서 004 종료 뒤 wrapper exit code와 stderr 내용을 복구할 수 없으며, sandbox 경계 실패와 wrapper 실행 실패를 아직 구분할 수 없다. 002·003·004 W/J/S root와 pending manifest는 삭제·재사용하지 않고 보존했다. Phase B는 `RUNTIME_BOUNDARY_CANDIDATE`가 아니며 Phase C는 계속 중단 상태다.

## 현실 고난도 Phase B P01 실패 증거와 obsolete CLI argv 확정

- 작업일: 2026-08-09. 최신 `main` merge commit `9804977bea4c1d4d8eeb0c7ff3f6d1b30a9cad89`에서 `codex/runtime-boundary-p01` 브랜치를 새로 만들었다. commit `d8f2ac1d257a2ae2f1ed459253e9d3bc3bfb9908`은 probe JSON 해석 전 실패 시 `<bundle>.probe-failure.json`에 frozen probe ID·argv hash·wrapper exit code·Controller 전후조건과 64 KiB capped stdout/stderr bytes, captured/full stream hash를 기록하고 같은 경로 재시도를 거부한다. 관련 표적 시험은 `10 passed`, `py_compile`과 `git diff --check`도 통과했다.
- source `d8f2ac1d257a2ae2f1ed459253e9d3bc3bfb9908`의 `phaseb-20260809-005`는 profile·effective policy·readiness·requirements·Controller identity를 통과하고 P01을 정확히 1회 dispatch했다. P01은 202 ms 뒤 wrapper exit 1, stdout 0 bytes, stderr 884 bytes로 종료됐다. Controller pre/postcondition은 모두 true, actual model turn은 0회이며 P02~P08과 candidate bundle 생성은 없었다.
- 실패 artifact의 재계산 코드는 `PROBE_STDOUT_NOT_JSON`, `PROBE_WRAPPER_EXIT_NONZERO`다. stderr는 `CreateProcessAsUserW failed: 2`와 함께 실제 child command가 `windows --cd ... -- C:\Python314\python.exe ...`였음을 보존했다. 즉 Python이나 W/J/S 접근을 시험하기 전에 존재하지 않는 `windows` executable을 spawn하려다 멈췄다.
- 같은 pinned `codex.exe`의 read-only `sandbox --help`는 실제 usage를 `codex sandbox [OPTIONS] [COMMAND]...`로 표시한다. `sandbox windows --help`는 help subcommand가 아니라 sandbox 안에서 `windows --help` 실행을 시도해 같은 `CreateProcessAsUserW` 오류 2로 실패했다. 따라서 manifest의 `['sandbox', 'windows', ...]` prefix가 현재 pinned CLI 0.144.4와 맞지 않는 obsolete argv임이 확정됐다.
- `phaseb-20260809-005` W/J/S root, pending manifest와 probe-failure artifact는 삭제·재사용하지 않고 보존했다. 다음 수정은 frozen prefix에서 `windows` token 하나를 제거하고 exact argv 시험·명세를 함께 고친 뒤 새 source commit과 새 root token으로만 실행해야 한다. Phase B와 Phase C는 계속 중단 상태다.

## 현실 고난도 Phase B CLI argv 교정과 W ACL transition 관측

- 작업일: 2026-08-09. commit `1b44ad3a48784ecd6d5675703f7371dc13bcc326`에서 pinned CLI 0.144.4의 실제 usage `codex sandbox [OPTIONS] [COMMAND]...`에 맞춰 frozen prefix의 obsolete `windows` token 하나를 제거했다. exact argv 시험과 runtime-boundary·상위 구현 후보 명세도 함께 고쳤고, 표적 시험 `10 passed`, `py_compile`, `git diff --check`를 통과했다.
- source `1b44ad3a48784ecd6d5675703f7371dc13bcc326`의 `phaseb-20260809-006`은 SDK profile·effective policy·readiness·requirements·Controller identity를 통과했지만 P01 command spawn 전 `verify_root_identity_contract`에서 중단됐다. 실제 model turn과 P01~P08 dispatch는 모두 0회이며 candidate bundle과 probe-failure artifact는 생성되지 않았다.
- 독립 read-only 비교에서 J와 S의 owner·ACL·volume은 manifest와 모두 같았고 W도 owner·volume은 같았다. W ACL만 manifest SHA-256 `0b3bcbc9cbec3ca8bba045802b277ad47b0ae9a48890b87f42aec7c22adebe01`에서 `41ffad743c3889293161edc98a20410449402f14df61af3c81f75415235ea032`로 바뀌었다.
- raw ACL 차이는 W에만 새 non-inherited allow ACE 하나가 추가된 것이다. 이 ACE는 새 SID에 `Modify, Synchronize`와 child object/container inheritance를 부여하며 J·S에는 추가되지 않았다. 이는 `:workspace` 준비가 dedicated sandbox user에게 W 접근만 부여한 정상 transition으로 추정된다. raw SID는 공개 기록에 남기지 않았다.
- 현재 exact-equality root gate는 안전한 W-only grant와 J/S scope 확장을 구분하지 못한다. 다음 교정은 초기 W ACL을 보존하면서 dispatch 전에는 이 exact W-only ACE delta만 잠정 허용하고, P01 결과의 sandbox process TokenUser SID가 추가 ACE SID와 같을 때만 최종 통과시켜야 한다. J·S owner·ACL·volume은 계속 bit-for-bit 동일해야 하며 다른 delta는 즉시 중단한다.
- `phaseb-20260809-006` W/J/S root와 pending manifest는 삭제·재사용하지 않고 보존했다. 자동 재시도는 하지 않았고 Phase B·Phase C는 계속 중단 상태다.

## 현실 고난도 Phase B W ACL 전이와 capability SID 교정

- 작업일: 2026-08-09. commit `b93ce1b1e5e970d5d64e2ad44f15c54f7b643051`에서 초기 W ACL과 준비 뒤 ACL의 multiset 차이를 비교해 explicit `A;OICI;0x1301bf` ACE 정확히 1개만 잠정 허용하고, W owner·group descriptor·volume·DACL control 및 J·S 전체 identity를 각 probe 전후에 고정하는 guard를 구현했다. 표적 시험 `13 passed`, 실제 SDK가 있는 B1 Python과 저장소 밖 short basetemp에서 Runner 전체 `252 passed`를 확인했다.
- source `b93ce1b1e5e970d5d64e2ad44f15c54f7b643051`의 `phaseb-20260809-007`은 profile·effective policy·readiness·requirements·Controller identity를 통과하고 P01을 정확히 1회 dispatch해 typed JSON과 sandbox process identity까지 수집했다. 그러나 추가 ACE SID를 P01 TokenUser SID와 직접 비교한 관문에서 다르다고 판정해 P02 전에 중단됐다. actual model turn은 0회이고 candidate bundle은 생성되지 않았다.
- 007 W의 explicit ACE 대상은 Controller SID, 현재 `CodexSandboxOffline`·`CodexSandboxOnline` 사용자 SID, `CodexSandboxUsers` 그룹 SID 어느 것과도 같지 않았으며 계정명으로 translate되지 않았다. 설치된 pinned runtime binary에는 sandbox spawn request의 `cap_sids`, capability SID file과 permission-profile ACL 적용 경로가 존재한다. 따라서 006의 “dedicated sandbox user SID 직접 grant” 추정은 폐기하고 **workspace capability SID grant**로 교정한다.
- 다음 계약은 추가 ACE raw SID의 SHA-256이 P01 `WindowsProcessIdentityObservation.capability_sid_sha256s`에 포함될 때만 결합을 통과시킨다. TokenUser는 여전히 Controller와 다른 dedicated sandbox user임을 별도로 증명한다. J·S exact identity와 W-only one-ACE delta는 완화하지 않는다.
- `phaseb-20260809-007` W/J/S root와 pending manifest는 삭제·재사용하지 않고 보존했다. P01 재시도는 하지 않았으며 새 source commit과 새 root token으로만 다음 model-free 실행을 수행한다. Phase B·Phase C는 계속 중단 상태다.
- source `0102f0de802a916975beafb6ed0b8342563e648b`의 `phaseb-20260809-008`도 profile·policy·readiness·Controller 관문을 통과하고 P01 typed JSON까지 수집했지만, 추가 ACE SID hash가 P01 `TokenCapabilities`에 없어서 P02 전에 중단됐다. 오류가 봉인한 실제 capability hash 목록은 빈 목록이었다. actual model turn은 0회이고 candidate bundle은 생성되지 않았다.
- 설치된 `codex-command-runner.exe`의 read-only binary surface는 spawn request의 `cap_sids`, `no capability SIDs provided`, `CreateRestrictedToken`과 `windows-sandbox-rs/src/token.rs` 경로를 함께 포함한다. 즉 runtime이 capability라고 부르는 SID는 Windows `TokenCapabilities`가 아니라 restricted token의 restricting SID로 적용된다.
- 다음 계약은 추가 ACE SID hash를 P01 `restricted_sid_sha256s`에 결합한다. TokenUser 차이, W-only exact one-ACE delta, J·S exact identity는 그대로 유지한다. `phaseb-20260809-008` W/J/S root와 pending manifest도 삭제·재사용하지 않고 보존했으며 새 source·새 root token만 허용한다.

## 현실 고난도 Phase B J read 노출과 전용 least-privilege profile 교정

- 작업일: 2026-08-09. source `b9de58ed8436309b88990c36b8a370f6d9f62b37`, pending manifest SHA-256 `70da017dac1bbe755bba8835062b2eaee4b2d03ec058e3d33cfee027cb5741c5`의 `phaseb-20260809-009`는 SDK profile·effective policy·readiness·Controller identity와 P01 W positive control, exact W ACL transition·restricted SID 결합을 통과했다.
- P02 J absolute read가 Controller-only content를 노출해 Controller가 `P02 disclosed or mutated a Controller-only boundary; NOT_READY`로 즉시 중단했다. P03~P08은 실행하지 않았고 actual model turn은 0회이며 candidate bundle은 생성되지 않았다. 이는 harness 오판이 아니라 built-in `:workspace`가 W 밖 read를 넓게 허용한다는 실제 격리 실패다.
- `phaseb-20260809-009` W/J/S root와 pending manifest는 삭제·재사용하지 않고 그대로 보존한다. 같은 source·root에서 P02를 재시도하지 않으며 다음 실행은 새 commit·새 root token만 사용한다.
- 공식 permission-profile 계약에 따라 새 `runtime-boundary-worker` profile은 `:workspace`를 상속하되 exact frozen override로 `:root="deny"`, `:minimal="read"`, network disabled를 적용한다. SDK empty thread와 bundled `codex sandbox`는 같은 profile ID와 같은 6개 override를 사용하고, 추가·누락 override를 Schema에서 거부한다. 이 교정은 모델 호출 없이 새 Phase B root에서 다시 증명하기 전까지 candidate 주장이 아니다.

## 현실 고난도 Phase B custom profile 직렬화 교정

- 작업일: 2026-08-09. source `a640a002707a3fc1aab865dab7803c7552ff3b5b`, pending manifest SHA-256 `ab76634dbc914342944bc8114352a22a86794c672581c00d5ba8287eaae3321b`의 `phaseb-20260809-010`은 SDK app-server initialize 단계에서 중단됐다. failure artifact는 client의 initialize request 1개와 server response 0개를 보존했고, actual model turn과 P01~P08은 모두 0회이며 candidate bundle은 생성되지 않았다.
- 별도 0-turn app-server 진단의 stderr는 `filesystem path '":minimal"' must be absolute, use '~/...', or start with ':'`를 확정했다. 설계한 access 값이 아니라 CLI dotted override에서 quoted key가 따옴표 포함 literal path로 해석된 직렬화 오류다.
- `phaseb-20260809-010` W/J/S root, pending manifest와 profile-failure artifact는 삭제·재사용하지 않고 보존한다. Filesystem 두 항목은 exact 단일 override `permissions.runtime-boundary-worker.filesystem={":minimal"="read",":root"="deny"}`로 교정한다. 같은 inline table을 적용한 pinned app-server 별도 initialize는 성공했으며 model turn은 0회였다. 새 source·새 root token의 전체 probe 전까지 candidate 주장은 계속 금지한다.

## 현실 고난도 Phase B explicit Controller-root deny 교정

- 작업일: 2026-08-09. source `2eff82d8489ae7d6d215f6f8f584b6ae3907b779`, pending manifest SHA-256 `86ddd9e9d9b8a099e8ab7c983a7f0b858b927e8abff5a005a1d8dcadc271733d`의 `phaseb-20260809-011`은 custom profile provenance·effective config·elevated readiness와 P01 W positive control·ACL restricted-SID 결합을 통과했다. 그러나 P02 J absolute read가 다시 내용을 노출해 즉시 `NOT_READY`로 중단됐다. P03~P08과 model turn은 0회이고 candidate bundle은 없다.
- 별도 `config/read`는 active default와 profile이 `runtime-boundary-worker`, `extends=:workspace`, filesystem `:minimal=read`·`:root=deny`, network disabled로 실제 적용됐음을 확인했다. 따라서 011은 설정 누락이 아니라 broad root deny가 Windows의 더 좁은 read grant에서 J를 제거하지 못한 결과다.
- `phaseb-20260809-011` W/J/S root와 pending manifest는 삭제·재사용하지 않고 보존한다. 다음 profile은 같은 inline table에 resolved W/J/S 공통 부모, J, S를 각각 exact deny로 추가한다. Manifest validator가 serialized path와 root identity를 직접 비교하며 다른 J/S로 바꾼 profile은 거부한다. 표적 회귀 15개는 통과했고 새 source·새 root token 전까지 candidate 주장은 금지한다.

## 현실 고난도 Phase B inherited ACL 원인 확정과 J/S hardening

- 작업일: 2026-08-09. source `f7b530f7826075efe417b5e4ade189ae6c25528c`, pending manifest SHA-256 `217a8a90475a075f04e0cc456f22c4eb80e73c4dbde3a6da0c4bd4f5e2248267`의 `phaseb-20260809-012`는 exact common-parent/J/S profile deny와 P01을 통과했지만 P02 J content가 다시 노출돼 `NOT_READY`로 중단됐다. P03~P08과 model turn은 0회이고 candidate bundle은 없다.
- Read-only `icacls`는 012 J에 Controller·SYSTEM·Administrators뿐 아니라 `CodexSandboxUsers`와 두 sandbox 관련 SID의 inherited `OI/CI Modify` ACE가 있음을 확인했다. Profile의 declarative deny가 active여도 dedicated sandbox user가 이 inherited allow를 통해 읽을 수 있었던 것이 반복 P02 성공의 실제 OS 원인이다.
- `phaseb-20260809-012` W/J/S root와 pending manifest는 삭제·재사용하지 않고 보존한다. 다음 준비 구현은 J/S를 서로 다른 opaque private parent 아래 만들고 parent와 leaf 모두 inheritance를 제거한 뒤 Controller SID, SYSTEM, BUILTIN Administrators의 `OICI Full Control` 세 explicit ACE만 허용한다. W는 기존 ACL과 capability transition 계약을 유지한다.
- 임시 폴더에서 `icacls /inheritance:r`와 SID 기반 `/grant:r` 문법, canonical `D:PAI`와 exact 세 ACE를 확인한 뒤 임시 폴더를 삭제했다. 실제 helper와 exact ACL 회귀를 포함한 runtime-boundary 표적 시험은 `16 passed`다. 새 source·새 root token에서 P01~P08을 다시 실행하기 전에는 candidate가 아니다.

## 현실 고난도 Phase B P05 junction cleanup 교정

- 작업일: 2026-08-09. source `5d9d1a544699af0738cb0f504f3e3e7be4da90d3`, pending manifest SHA-256 `b7871d23cc37ca68bdeb1022fbebdb130995238e63417b5a7a8e11cc892faa08`의 `phaseb-20260809-013`은 J/S protected ACL을 준비·검증하고 P02의 이전 content disclosure를 재발시키지 않은 채 P05까지 진행했다. P05 뒤 P06 dispatch 전 exact command 재검사에서 `P05 argv differs from frozen contract`로 중단됐고 actual model turn과 candidate bundle은 0이다.
- 보존된 W에는 P05 symlink는 없고 `escape-junction`만 남아 있었다. Junction target J가 unreadable하면 `Path.exists()`도 false가 될 수 있어 기존 cleanup 분기가 `os.rmdir`를 호출하지 않았고, 후속 `_probe_command_argvs()`의 `resolve()`가 남은 junction target을 따라가 frozen literal path와 달라진 것이 직접 원인이다. J content가 노출된 사건은 아니다.
- `phaseb-20260809-013` W/J/S와 pending manifest, 남은 junction은 진단 증거로 삭제·재사용하지 않는다. P05 fixture argv는 `abspath` 기반 no-follow lexical path로 고정하고, entry 존재는 `os.lstat`, 생성 성공 시 symlink는 `os.unlink`, junction은 `os.rmdir`로 cleanup한다.
- 실제 junction이 존재해도 command identity가 유지되는 회귀와 target unreadable 상황을 모사해 `Path.exists()`에 의존하지 않고 junction이 제거되는 회귀를 추가했다. Controller-only ACL 회귀를 포함한 표적 시험은 `18 passed`다. 새 source·새 root token 전까지 candidate 주장은 금지한다.

## 현실 고난도 Phase B 8-probe 완주와 P08 metadata 계약 교정

- 작업일: 2026-08-09. source `d21f3d86e738a18818c0d318b51864e33646f7bb`, pending/embedded manifest SHA-256 `9c2024a3294998dfb810886e3329d2c9af10e8a0a2a76475308f73948abfc351`의 `phaseb-20260809-014`는 P01~P08을 모두 실행하고 exact 4-file bundle을 생성·검증했다. P01~P07은 모두 true, P08만 false, actual model turn은 0이며 aggregate는 `RUNTIME_BOUNDARY_NOT_PROVEN`이다.
- P08 typed Evidence는 S sentinel read, absent target create, existing target replace가 모두 `access_denied`였고 S sentinel Controller hash와 W source hash는 전후 동일했다. Sandbox는 existing S replace target의 존재·hash도 볼 수 없어 before/after false·null을 반환했다. 과거 재계산식은 오히려 target 존재 true와 manifest hash 노출을 요구해 P08을 false로 만들었다.
- 이 결과는 mutation이나 content disclosure가 아니라 더 강한 metadata nondisclosure다. 새 계약은 Worker 쪽 existing S target을 false/null로 요구하고, 실제 target 존재·size·hash 불변과 create target 부재는 이미 실행 전후 `_probe_precondition`이 확인한 Controller evidence로만 증명한다. Worker가 S target 존재·hash를 관측하면 실패다.
- 014 bundle aggregate SHA-256은 `07ec2b31a49ad11b88f8e13570c9e72745e48aaf407efe642e012354a923468d`, result SHA-256은 `a1b4adc43d565e8c4337d7aa266046fff0317e9f5cb5da1f2246f0e792736cbc`다. Bundle과 W/J/S는 비candidate 진단 증거로 보존하며 재사용하지 않는다. P08 nondisclosure/metadata disclosure negative 회귀를 포함한 표적 시험은 `19 passed`다.

## 현실 고난도 Phase B runtime-boundary candidate 도달

- 작업일: 2026-08-09. source `9b29e781136e13b43b1e18f3fe1823bf496bef5c`의 `phaseb-20260809-015`는 pinned SDK/CLI `0.144.4`, ChatGPT account, custom `runtime-boundary-worker`, native Windows `elevated`, W capability ACL restricted-SID 결합과 Controller-only J/S protected ACL을 확인했다.
- P01~P08 derived result는 정확히 8/8 true이고 failure reason은 없으며 actual model turn은 0회다. Aggregate status는 최초로 `RUNTIME_BOUNDARY_CANDIDATE`에 도달했다. Manifest SHA-256은 `9d7b2c85991192fc78e6235f75636fe323ec057ed4920fa7e33b2217023829bc`, result SHA-256은 `1914fb39d263e3dec95fadfe49d24b7fec83c51606294972054287a019a74a9d`, bundle aggregate/files SHA-256은 `326017ab7ee33d5de9ce39ef4a9a721e7e770f27e9ecef14571bc293c96ea4c2`, bundle-seal SHA-256은 `144c0a11198699a6c5216745b71d4b1b596cdcfe67eee3c13b0e24a27bc5dd13`다.
- 실행과 다른 새 Python process가 exact 4-file bundle, stored/derived aggregate, P01~P08, frozen command identity와 현재 J/S root identity·exact protected ACL을 다시 열어 모두 통과했다. 이어 Benchmark Runner 전체 회귀 `258 passed in 200.38s`를 확인했다.
- 001~014의 실패 root와 artifact는 삭제·재사용하지 않고 보존한다. 015 candidate도 수정·재실행하지 않는다. 사람용 결과 보고서는 `docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md`다. 다음 관문은 이 Phase B 후보의 독립 closure이며, 그 전에는 `judge_only_verified`, Phase C, snapshot/checker 구현, live/model usage를 열지 않는다.

## 현실 고난도 Phase B 최종 closure와 Phase C 사용자 승인

- 작업일: 2026-08-09. ChatGPT Pro가 최종 심사 ZIP의 manifest 27개 파일, 선행 심사, 최종 명세, 실제 source/test snapshot, Phase B 결과와 exact four-file bundle을 테스트·SDK·Codex·probe·thread·model turn 없이 읽기 전용으로 심사했다.
- 최종 판정은 `승인`, P0/P1 각 0건이다. Actual SDK active-profile provenance, elevated 판별, P01~P08 typed Evidence와 독립 pass 재계산은 모두 `closed`로 판정됐다. Candidate 015의 exact executable·source·configuration·permission profile·root/ACL identity 범위에서 `judge_only_verified=YES`다.
- Phase C model-free 착수는 `GO`로 판정됐고 사용자가 별도로 진행을 승인했다. 허용 범위는 Schema, SS1 Fake Adapter, passive observer, property envelope·common triage 순수 로직과 targeted test다.
- Phase B 추가 probe·재심사·전체 회귀는 열지 않는다. Phase D snapshot·fixture·reference·checker, Phase E live candidate와 Phase F model turn은 승인되지 않았으며 별도 관문을 유지한다.
- 심사 원문은 `docs/reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md`에 보존했다.

## 현실 고난도 Phase C model-free 구현 완료

- 작업일: 2026-08-09. 사용자가 승인한 좁은 Phase C 범위인 strict Schema, SS1 Fake Adapter, passive observer record, property evaluation envelope와 common triage 순수 로직을 commit `cb730b820e1bbc18d4c1813f50b2cb2a2377c7ee`에 구현했다.
- SS1은 모든 Task와 선택적 self-review를 한 thread에서 실행하고, Task당 추가 1 turn·Variant당 추가 2 turns를 넘지 않는다. Check/Judge/stdout/stderr 정보는 prompt에서 차단하고 모든 terminal 뒤 observer를 호출한다. 일반 Task scope finding은 기록만 하며 secret·J/S 접근, observer 실패와 thread drift는 fail-closed로 끝낸다.
- Phase C 표적 시험은 `33 passed in 0.22s`다. 변경한 Fake SDK와 기존 기준선에 대한 영향 회귀는 `19 passed, 1 skipped in 28.12s`이며 skip은 현재 환경의 선택 의존성 `openai_codex` 부재다. 나머지 live-runtime 파일 시험은 가짜 client 주입으로 수행됐고 actual model turn은 0회다. `git diff --check`도 통과했다.
- 새 Docker 환경, Phase B probe, 실제 SDK thread, snapshot·fixture·reference·checker, B1 public hook, stage registry, live Plan·seal·export는 만들거나 실행하지 않았다. 다음 Phase D와 이후 live/model 단계는 별도 승인 전까지 닫혀 있다.

## Phase C exact prompt 교정과 Phase D 명세 후보 작성

- 작업일: 2026-08-09. Phase D 상위 계약 대조 중 Phase C의 `SS1_NEUTRAL_REVIEW_PROMPT`가 승인된 비교 명세의 exact four-line literal과 다름을 발견했다. 기능 시험이 통과했다는 사실로 literal 계약을 대신하지 않고 commit `c4df661f608a7580f28738687e1c47100b2e5093`에서 구현 문구를 교정하고 exact literal 회귀를 추가했다.
- 교정 뒤 Phase C 표적 시험은 `33 passed in 0.23s`, actual model turn은 0회다. 전체 회귀와 Phase B probe는 반복하지 않았다.
- Phase D는 artifact를 바로 만드는 단계가 아니라 별도 snapshot/checker 명세와 외부 심사를 먼저 통과해야 한다. revision 1 후보는 실제 historical window 두 개, 각 8-Task graph, 공개/Controller/judge-only 경계, reference·mutation positive evidence, property DAG와 OS-level Judge no-network proof를 고정한다.
- 두 후보가 같은 저장소의 다른 시점이라는 독립성 문제와 Profile I의 6-file 구조 예외는 외부 심사의 명시적 `accepted`를 요구한다. 하나라도 rejected이면 Phase D artifact 제작은 `NO-GO`다. snapshot·fixture·reference·checker·Judge probe·live Plan·model turn은 이번 작업에서 만들거나 실행하지 않았다.

## Phase D revision 1 외부 심사와 revision 2 closure 후보

- 작업일: 2026-08-09. ChatGPT Pro는 Phase D revision 1 패키지를 읽기 전용으로 심사해 same-repository independence와 Profile I의 6-file 구조 예외를 수용했지만 최종 `조건부 승인`, P0 0건, P1 3건, P2 2건, Phase D artifact `NO-GO`로 판정했다.
- P1은 Profile I의 I05~I07 goal이 historical solution을 노출한 점, Judge access matrix가 J write 계열·S 전체 접근·parent/child parity·pre/post identity를 닫지 못한 점, repository의 J bundle과 실제 protected runtime J를 구분하지 않은 점이다. P2는 Profile R raw 91-file 수에 generated/golden/history가 섞인 점과 R-P08/I-P10이 자유문 품질 판정으로 넓어질 수 있는 점이다.
- revision 2는 I05~I07을 증상과 공개 invariant로 교체하고 Worker-visible surface 전체의 provenance·forbidden fact·random canary 검사를 추가했다. Judge에는 fresh read/write O, W/J runtime/O/S의 operation별 parent/child matrix, J runtime·S의 pre/post root·ACL·tree·file hash 불변을 고정했다. repository의 versioned J source는 frozen Git object에서 별도 opaque protected runtime J로 byte-exact 복사·결합하고 실제 probe/checker는 runtime J만 사용한다.
- Profile R은 raw path를 authored/generated/golden/history category와 semantic group으로 분해하고 raw 파일 수를 난이도 근거로 쓰지 않는다. R-P08과 I-P10은 machine-readable command/status/claim-evidence 관계만 판정하며 자유문 품질은 점수·triage·route에서 제외한다.
- 이 변경은 `revision_2_external_rereview_candidate` 문서와 closure 심사 자료뿐이다. snapshot 추출·익명화, fixture/reference/checker, Judge probe, live Plan, SDK thread와 model turn은 만들거나 실행하지 않았고 Phase D artifact는 재심사 전까지 계속 `NO-GO`다.

## 집 로컬에서 회사 로컬로 현재 작업 반환

- 작업일: 2026-08-09. 프로젝트를 원래 주관하던 회사 로컬이 집 작업 branch를 안전하게 다시 받도록 `docs/operations/home-to-company-codex-handoff.md`와 회사용 시작 프롬프트를 작성했다.
- 완료 작업 기준은 `codex/runtime-boundary-p01`의 `0d0fa852b689bc06e036de50d5b3817ae6d70f00`이다. 작성 전 해당 HEAD와 원격 branch가 일치하고 working tree가 깨끗했으며, 당시 `origin/main` `9804977`의 직계 후손으로 20 commits ahead였다. 인수인계 commit은 그 뒤에 추가한다.
- 새 인수 문서는 Phase B Candidate 015와 Pro closure, Phase C model-free 구현·시험 기록, Phase D revision 1 심사와 revision 2 closure 후보를 구분한다. 현재 다음 gate는 ChatGPT Pro revision 2 재심 결과이며, 그 결과와 별도 사용자 승인 전에는 Phase D artifact 구현을 열지 않는다.
- 회사 첫 세션은 local change·local-only commit 보존, 집 branch ff-only 동기화, 정본 읽기와 인수 보고만 허용한다. 과거 시험 재실행, 내부 하위 에이전트, 파일 수정, main 병합, live/model 작업은 금지한다.
- 과거 `home-codex-handoff.md`에는 현재 회사 복귀 문서가 운영 절차를 대체한다는 banner만 추가했다. 코드·시험·artifact는 수정하거나 실행하지 않았고 actual model turn은 0회다.

## 집→회사 인수인계 목표를 exact Git tree 동일화로 교정

- 작업일: 2026-08-09. 사용자가 인수인계의 본뜻은 두 PC가 별도 프로젝트 상태를 유지하는 것이 아니라 해당 프로젝트의 모든 Git 관리 파일·디렉터리를 같은 commit/tree로 맞추고 Codex 컨텍스트만 별도로 복원하는 것이라고 명확히 했다.
- 인수인계 문서와 회사 시작 프롬프트를 revision 2로 다시 작성했다. 회사는 먼저 local change·untracked 작업·local-only commit을 보존하고, fetch 뒤 최신 `origin/main`의 unique commit을 확인한다. main-only commit이 없을 때만 `codex/runtime-boundary-p01` tip으로 ff-only 동기화한다.
- 동일성 통과 조건은 local/remote commit 일치, tree hash 일치, porcelain status 비어 있음과 remote branch 대비 tracked diff 0이다. `.venv`, cache, OS 설치, Codex 로그인·메모리와 repository 밖 state는 Git 정본이 아니므로 복사 대상에서 제외했다.
- main-only 작업이나 회사 local-only 작업이 있으면 어느 쪽도 덮지 않고 보고 후 중단한다. 첫 세션은 동일화·문서 읽기·보고만 허용하고 Phase D 구현과 과거 시험 재실행은 계속 금지한다.
- 이번 교정은 인수인계·프롬프트·revision log 문서뿐이다. 코드·시험·artifact·model turn은 변경하거나 실행하지 않았다.

## Phase D revision 2 closure 재심사 통과와 사용자 artifact 구현 승인

- 결과 수령일: 2026-08-10. ChatGPT Pro의 revision 2 closure 재심사는 최종 `승인`, revision 1 P1 3/3 `closed`, P2 2/2 `accepted`, 신규 P0/P1/P2 0건으로 판정했다. same-repository independence와 Profile I 6-file 예외의 `accepted`도 유지됐다.
- Phase D artifact 설계 관문은 `GO`다. Phase E live와 Phase F model turn은 계속 `NO-GO`이며 ChatGPT 구독 인증만 허용되고 API key는 허용되지 않는다.
- 외부 심사는 package source commit `0d0fa852b689bc06e036de50d5b3817ae6d70f00`의 28-file manifest를 28/28 일치로 확인했지만 `.git`이 없어 commit과 ancestry를 독립 검증하지 않았다. 회사 저장소에서 `0d0fa852...`가 현재 HEAD의 조상이고 두 historical base/reference 관계가 각각 유효하며, revision 2 prompt·revision 1 review·revision 2 spec의 LF-normalized SHA-256이 보고서와 일치함을 별도로 확인했다.
- 외부 심사는 테스트·Git·Python·SDK·Codex command·probe·thread·model turn을 실행하지 않은 읽기 전용 심사다. 원문은 `docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md`에 336줄·LF SHA-256 `5fbb69d66c05b52c06722a72c232f407975ce069ff76b7211f03793b7d372b64`로 보존했다.
- 사용자의 `ㄱㄱ` 지시는 Phase D 명세 §11~§12의 model-free artifact 구현에 대한 별도 승인으로 해석했다. 이 승인은 source gate 실패를 우회하거나 누락된 원시 증거를 추정·대체할 권한, Phase E/F 권한으로 확대되지 않는다.

## Phase D artifact source gate 중단

- 작업일: 2026-08-10. 구현의 첫 gate로 두 historical Git window와 Profile I 원시 `001~014` 실패 artifact의 가용성을 읽기 전용으로 점검했다. Profile R과 I의 base/reference commit은 모두 존재하고 ancestry가 유효하며 diff 규모도 각각 명세의 91 files·5,675 insertions·261 deletions, 6 files·1,997 insertions·216 deletions와 일치했다.
- Profile I의 원시 pending manifest, profile/policy/probe failure artifact, 보존 W/J/S root와 014 bundle은 현재 Git objects·working tree·사용자 Documents·Local Temp·`AppData/Local/local-agent-orchestrator`의 알려진 보존 위치에서 발견되지 않았다. exact run ID와 기록된 manifest hash 검색에서 revision log 요약과 Candidate 015 결과·심사만 확인됐다.
- Phase D 명세 §3.2는 원시 `001~014` artifact가 없거나 committed record와 hash로 결합할 수 없으면 문서 요약으로 재구성하지 말고 `CHALLENGE_NOT_READY`로 닫도록 한다. §13의 즉시 중단 규칙에 따라 phase-level 결과를 `PHASE_D_BLOCKED_SOURCE`, 원인 `PROFILE_I_RAW_EVIDENCE_ABSENT`로 기록했다.
- source gate 뒤 W snapshot·익명화·Task/J bundle·reference·mutation·checker·Judge filesystem/no-network probe·artifact seal·Phase D target/전체 회귀를 만들거나 실행하지 않았다. actual model turn은 0회다.
- 해제 방법은 집 PC 또는 백업의 원시 `001~014` 증거를 원본 hash와 함께 회수해 read-only inventory를 통과시키거나, 자료를 회수할 수 없으면 Profile I를 다른 실제 snapshot으로 교체한 새 revision을 심사받는 것이다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-phase-d-source-audit-result.md`에 기록했다.
- 사용자가 추가로 제공한 세 선행 심사 답변은 각각 manifest `25/25`, `38/38`, `39/39`가 일치한 설계·Schema 심사였으며 원시 Phase B artifact를 포함하지 않았다. 최종 승인 답변의 27-file package에는 Candidate 015 exact four-file bundle만 있었고 `001~014` 실패 bytes는 없었다. 따라서 심사 계보와 015 closure는 보강됐지만 `PROFILE_I_RAW_EVIDENCE_ABSENT` 차단은 유지된다.
- 추가 전수 감사에서 origin의 fetch refspec이 모든 head를 포함함을 확인하고 GitHub API의 branch cursor를 끝까지 조회했다. 원격은 `main`과 `codex/*` 5개, 총 6개 branch뿐이었다. 이들이 도달하는 unique commit 118개와 path object 2,656개, 유일한 PR head, tag·Release·조회 시점 보존 Actions artifact·LFS·submodule, local unreachable commit 2개·tree 211개·blob 97개를 filename·run ID·known hash로 검색했지만 raw Phase B artifact는 없었다. 과거 Actions artifact가 만료·삭제됐거나 알려지지 않은 외부 저장소에 있었을 가능성까지 부재로 단정하지는 않는다.

## Phase D historical reconstructed replay revision 3 후보

- 작업일: 2026-08-10. 사용자는 확인 가능한 현재 GitHub/Git 보존 표면과 알려진 로컬 보존 위치를 전수 확인한 뒤 원본이 없으면 다시 구축하도록 승인했다. 재구축을 원본 복원으로 오표기하지 않고, 당시 source commit `001~015`를 새로 동결한 같은 현재 환경에서 각각 한 번 실행해 새 관측을 만드는 별도 `historical_reconstructed_replay_v1` 계보로 정의했다.
- 기존 `realistic-incident-repair-001`의 `PHASE_D_BLOCKED_SOURCE`, 원인 `PROFILE_I_RAW_EVIDENCE_ABSENT`와 `CHALLENGE_NOT_READY`는 유지한다. 새 snapshot ID 후보는 `realistic-incident-repair-replay-001`이며 Candidate 015의 기존 `judge_only_verified` closure를 대체·재인증하지 않는다.
- 15개 source commit과 tree hash, 기록된 terminal gate와 당시 native writer surface를 전수 대조했다. 모든 source는 Git에 존재하지만 `001~013` 중 상당수는 해당 terminal gate용 writer가 없어 그대로 재실행해도 pending manifest만 남는다. historical source를 고치지 않고 별도 supervisor가 process 경계에서 exit·exception, capped stream과 생성 artifact inventory를 봉인하도록 설계했다.
- revision 3 후보는 reconstructed environment identity, exact `001→015` 순서, ordinal당 1회, outcome-driven retry·subset·permission 변경 금지, append-only raw/public artifact 분리, J-only historical claim ledger와 deterministic projection을 요구한다. 실행 결과는 execution 상태와 `MATCHED | DIVERGED | NOT_COMPARABLE` 역사 비교를 별도 축으로 보존한다.
- `REPLAY_COMPLETE`는 challenge ready가 아니다. replay 뒤에도 공개 projection만으로 I01~I08을 해결할 수 있는지, 같은 환경의 015 positive reference, leakage·mutation·property·Judge 경계를 별도 source-qualification 외부 심사로 다시 판정해야 한다.
- 새 source evidence class는 승인된 revision 2의 전제를 바꾸므로 외부 심사 전에는 harness와 probe를 구현·실행하지 않는다. 심사 후보 문서는 `docs/design/sdk-routing-realistic-high-difficulty-phase-d-reconstructed-replay-spec.md`, 프롬프트는 `docs/prompts/benchmark-runner/chatgpt-pro-review-prompt-sdk-routing-realistic-high-difficulty-phase-d-reconstructed-replay-r3.md`다. 이번 작업의 actual model turn, runtime-boundary probe와 app-server 호출은 0회다.
- 자체 다중 관점 감사에서 plan hash의 batch-path 순환, 민감 경로 plain hash, batch/ordinal process identity 혼합, 무한 filesystem 감시, deny-one no-model guard, replication durability와 실행 dependency bytes 미봉인 문제를 찾았다. Revision 3 후보는 host-only preimage/full environment identity 분리, raw-only key 기반 HMAC projection, exact `MonitoredHostSurface`, app-server method·subprocess argv allowlist, `turn_start_attempt_count > 0` invalidation, primary·replication 각각의 raw/J/W·restore 관문, Python stdlib·extension·third-party distribution file-set hash로 이를 닫았다.
- 외부 심사용 package는 `benchmarks/.local-r6/phase-d-replay-r3-pro-review-20260810-094448.zip`에 만들었다. ZIP은 Git 추적 대상이 아니며 136개 manifest payload를 압축 해제 후 전수 재검증해 누락·hash mismatch·extra 0건을 확인했다. ZIP SHA-256은 `23f50bbc5355147d3a6d071ce8ff13c9a2659323e929eb82d17c1b9957fc9557`, 크기는 2,381,708 bytes다. Package에는 historical source 15세트, claim-provenance log snapshot, SDK write 경계 발췌와 설계 문서만 있고 replay plan·harness·실행 artifact는 없다.
- Package 생성·검증에서도 historical source, probe, SDK, app-server, sandbox와 model turn을 실행하지 않았다. 실제 harness 구현과 15-ordinal batch는 외부 revision 3 심사 및 별도 사용자 승인 전 `NO-GO`다.

## Phase D reconstructed replay R3 조건부 심사와 closure 후보

- 작업일: 2026-08-10. ChatGPT Pro는 revision 3 package의 manifest 136/136과 source matrix를 읽기 전용으로 대조하고 lineage 분리를 accepted로 유지했지만, 최종 `조건부 승인`, `P0 0 / P1 2 / P2 2 / P3 0`, replay 설계와 harness 구현 `NO-GO`로 판정했다. 원문은 `docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-reconstructed-replay-r3.md`, 298줄·raw SHA-256 `70063571875ff556dd6ff12a0fc5ea188c70ddfe2e0c7ae21758ead8f0b21574`로 보존했다.
- `R3-P1-01`은 15개 source와 SDK 0.144.4를 다시 정적으로 대조해 profile/policy 두 connection, ordinal 001과 002~015의 차이, request·notification·response 방향, ordered legal prefix, successful count, request ID correlation을 고정했다. Outgoing 위반은 `_write_message` dispatch 전, incoming 위반은 `_read_message` 수신 뒤 invalidation하며 server request용 client response만 전송 전에 차단한다.
- `R3-P1-02`는 존재하지 않는 전역 subprocess pre-dispatch 주장을 삭제했다. Process를 Supervisor direct, Controller-side, top-level sandbox, sandbox descendant 네 종류로 분리하고 app-server·outer Codex·ordinal 013~015 `icacls.exe`에는 sandbox containment을 주장하지 않는다. P01~P08 top-level probe Python과 P05/P06을 누락 없이 기록하고 P05/P06은 `predispatch_enforced=false`와 제한된 관측 범위를 유지한다.
- `R3-P2-01`은 기존 6개 source를 `review_source_subset`으로 재명명하고, 15/15 commit에 공통인 9-file first-party execution closure를 별도 manifest로 고정했다. Nonliteral dynamic probe는 `archive probe blob → W/.orchestrator-probe/probe_runtime_boundary.py`의 source/destination byte parity와 static dataflow로 분리했다. `R3-P2-02`는 frozen subject deadline을 `OBSERVED + SUBJECT_DEADLINE_EXCEEDED`로 보존하고 process-control·I/O·seal 실패만 구체적 infrastructure error로 분류했다.
- 자체 병렬 재검토에서 최초 수정본의 incoming request pre-read 표현, policy connection start failure 분류, Controller process의 sandbox 오분류, P01~P08 top-level probe 누락과 dynamic probe alias 공백을 찾고 고쳤다. 최종 문서상 재검토는 네 finding 모두 `CLOSED`, 새 P0/P1 0건이다. 이는 외부 closure를 대신하지 않는다.
- Closure candidate 명세는 628줄·raw SHA-256 `a3e91511ecb35ccd1e56797696779907ae1bc60c0fef197a231b5ba97c4376af`, 정적 boundary inventory는 207줄·raw SHA-256 `e741118e15b60bbf2ab69aee5acc13399154970a695fad65096103adaa15152c`, 집중 재심사 프롬프트는 99줄·raw SHA-256 `a5b77585b1d49f66fc22770278d8026011996c0d1bfb8643db25ab98f493d55a`다.
- 새 외부 심사 package는 `benchmarks/.local-r6/phase-d-replay-r3-closure-review-20260810-123500.zip`이다. ZIP 크기는 1,676,439 bytes, SHA-256은 `c6497e3604ac4f2c3e816702cb66b8230d094ab9353e368873873a0d9c7e8e36`다. 압축 해제 뒤 manifest payload 209개를 독립 재계산해 missing·mismatch·extra 0건, ordinal별 closure manifest 9줄과 review subset 6줄 15/15, legacy `SOURCE-ALLOWLIST.sha256` 0개를 확인했다. Manifest SHA-256은 `655920db31b9dad57b9df69a2ea0cee458e975c66dae755a063a7c3f25c9c01f`다.
- 이어 15개 commit/tree, 두 source manifest의 총 225행, 각 raw file hash·Git blob ID와 matrix aggregate를 독립 대조해 오류 0건을 확인했다. Package 생성 첫 시도는 회사 PowerShell의 .NET에 `Path.GetRelativePath`가 없어 source 추출 뒤 manifest 작성에서 중단됐다. Source·probe를 실행한 오류가 아니며, package root 하위 prefix 검증과 substring 방식으로 바꿔 새 manifest를 처음부터 생성·검산했다.
- 이번 closure 작업에서 historical subject import, test, app-server, Codex command, sandbox probe, thread, model turn은 0회다. Replay harness와 실제 15-ordinal batch는 ChatGPT Pro closure와 별도 사용자 승인 전 계속 `NO-GO`다. Profile I source 채택, Phase E/F와 API key는 계속 금지다.

## Phase D reconstructed replay R3 closure 승인

- 결과 수령일: 2026-08-10. ChatGPT Pro는 closure package manifest 209/209, 15개 source matrix, ordinal별 6-file review subset과 9-file execution closure를 읽기 전용으로 대조했다. 최종 판정은 `승인`, 이전 네 finding 모두 `CLOSED`, 신규 `P0 0 / P1 0 / P2 0`이다.
- Reconstructed replay 설계와 model-free harness 구현은 `GO`다. 실제 15-ordinal batch, Profile I source 채택, Phase E live와 Phase F model turn은 계속 `NO-GO`다.
- 외부 심사는 historical source·테스트·SDK·Codex·app-server·sandbox·probe·thread·model turn을 실행하지 않았다. 원문은 `docs/reviews/benchmark-runner/chatgpt-pro-closure-review-sdk-routing-realistic-high-difficulty-phase-d-reconstructed-replay-r3.md`에 보존했다.
- 사용자의 후속 `ㄱㄱ`는 승인된 model-free harness 구현만 허용한 것으로 해석했다. Production adapter, 외부 storage write, 실제 replay batch와 model turn 권한으로 확대하지 않았다.

## Phase D reconstructed replay model-free harness 구현

- 작업일: 2026-08-10. 새 `replay_plan.py`, `replay_protocol.py`, `replay_supervisor.py`, `replay_harness.py`, `replay_artifacts.py`와 대응 테스트를 구현했다. 기존 runtime-boundary, probe, SDK routing·live registry 파일은 수정하지 않았다.
- Plan은 exact 15 ordinal·9-file execution closure·dynamic probe alias·환경 및 dependency identity를 고정한다. Protocol은 profile/policy connection의 방향·순서·correlation과 typed session ledger를 재계산하며 `turn/start`를 base writer 전에 차단한다. Supervisor는 4-process taxonomy, subject deadline과 infrastructure failure, one-pass bounded stream을 분리한다.
- Harness는 plan·protocol·supervisor 결과를 exact `001→015` one-shot으로 결합하고 verifier token이 있는 `BatchReadout`만 발행한다. Native transcript count는 canonical frame bytes에서 다시 계산하며 직접 만든 outcome·readout은 거부한다.
- Artifact는 raw/J/W 분리, native file inventory, deterministic projection, ordinal/batch seal, fake durability restore와 fake write-once external anchor를 구현했다. 실제 provider·network·production crypto는 없다.
- 교차 감사에서 기존 `raw_ordinal_seal_sha256`가 실제 raw directory seal이 아니라 Supervisor evidence seal이라는 의미 혼동과, raw JSON에서 self-authored harness input을 재구성할 수 있는 경로를 발견했다. 이를 `supervisor evidence seal → harness preseal → raw ordinal seal → verifier-produced combined input → external input-set anchor` 순서로 분리했다. Raw 내부 파일은 자기 디렉터리의 최종 seal을 포함하지 않는다.
- 최종화는 tokenized readout, raw binding과 실제 file hash, actual ordinal anchor, exact 15 input-set, fake durability primary·backup fresh restore, raw에서 독립 재생성한 J/W와 외부 anchor를 모두 최종 시점에 다시 확인한다. 요약 상태 함수만으로 `REPLAY_COMPLETE`를 만들 수 없다.
- Phase D 표적 회귀는 `154 passed in 34.17s`, B1 전체는 `74 passed in 20.16s`다. Benchmark Runner 전체는 `444 passed, 1 failed in 288.40s`이며 유일한 실패는 기존 Windows `core.autocrlf=true` checkout의 `stage.schema.json`·`suite.schema.json` raw CRLF와 생성 LF bytes의 비교다. 두 파일의 Git-filtered blob은 HEAD와 일치하고 frozen schema/test는 수정하지 않았다.
- 다섯 source·다섯 test `py_compile`, trailing whitespace 검사와 `git diff --check`를 통과했다. 실제 Git subject, subprocess, SDK, Codex, app-server, sandbox, probe, thread, model turn, 외부 upload는 0회다.
- 상세 구현·검증·미확인과 다음 관문은 `docs/operations/phase-d-reconstructed-replay-model-free-implementation-report.md`에 기록했다. 다음 단계는 현재 diff의 독립 코드 심사다. 그 뒤에도 production adapter/storage profile은 새 revision·외부 심사·별도 사용자 승인이 필요하며 실제 batch와 Phase E/F는 계속 닫혀 있다.

## Phase D ordinal 015 실제 non-evidence smoke

- 작업일: 2026-08-10. 추가 adversarial 방어 확장을 중단하고 실제 연결을 확인하기 위해 exact source commit `9b29e781136e13b43b1e18f3fe1823bf496bef5c`, tree `e60358524b274c5194bc6cbe76b262167b9451a2`의 ordinal 015를 disposable root에서 실행하는 단일 smoke 스크립트를 추가했다.
- Python `3.12.10`, SDK/CLI `0.144.4`, bundled executable SHA-256 `51398051c2332b6afe08dc3b9dbb4056085c197f35ca57a307ee303d450cada5`, ChatGPT OAuth를 사용했다. API-key 환경 이름은 없었다. 스크립트는 exact 9-file Git object closure를 추출하고 Python `-I` child에서 historical `prepare_runtime_boundary_roots()`와 `execute_runtime_boundary_probe(confirm_model_free_probe=True)`를 호출한다.
- 첫 실행 `smoke-015-20260810-073143-210ae8e3`은 base root에 CodexSandboxUsers Read만 상속돼 첫 sandbox 준비가 group Modify와 restricted SID Modify 두 ACE를 추가하면서 historical one-ACE 계약에서 중단됐다. 기존 root는 보존하고 새 disposable historical-state parent에만 expected workspace Modify baseline을 부여하도록 어댑터를 교정했다.
- 교정 뒤 새 root `smoke-015-20260810-073524-6b9b956a`와 `smoke-015-20260810-073802-b783e694`는 app-server profile/policy와 W ACL 관문을 통과하고 실제 P01 sandbox process까지 실행했지만, 최초 probe 결과에 `payload`가 없어 historical parser의 `runtime-boundary operation payload must be a JSON object`에서 동일하게 중단됐다. P02~P08은 실행하지 않았다.
- 실행 2의 실패 root에서 exact P01 command를 진단용으로 다시 호출하면 `operation_exit_code=0`으로 성공했다. 이 retry는 one-shot 계약에 사용할 수 없어 smoke 성공이나 evidence로 승격하지 않았다. Historical parser는 최초 failure JSON의 `error_type`·message hash를 raw artifact로 보존하지 못하므로 정확한 내부 원인은 미확인이다.
- 현재 판정은 `EXECUTED_WITH_SUBJECT_FAILURE`, 정식 15-ordinal batch `NO-GO`다. 실제 Git 추출과 app-server·Windows sandbox 연결은 확인됐지만 current fresh-root one-shot에서 Candidate 015는 재현되지 않았다. 세 실패 root는 삭제·재사용하지 않는다. 상세 결과는 `docs/experiments/phase-d-reconstructed-replay-ordinal-015-smoke-result.md`에 기록했다.

## Phase D ordinal 015 최초 P01 raw capture

- 작업일: 2026-08-10. `run_reconstructed_replay_smoke.py`에 진단용 `capture-first-p01` 모드를 추가했다. profile·policy·readiness 뒤 P01만 정확히 한 번 실행하며, historical parser 전에 stdout/stderr를 별도 로컬 파일로 보존한다. P02~P08과 retry는 실행하지 않는다.
- 새 root `capture-p01-015-20260810-074828-594c51fd`의 최초 P01은 wrapper/operation exit code `0/0`, payload 존재, pre/postcondition 통과, actual model turns `0`으로 성공했다. stdout은 2,191 bytes SHA-256 `86812a4d08603273b238f19d839cd1f22a4508e4891a472e8722bf8297c761d7`, stderr는 0 bytes였다.
- child wrapper가 정상 `SystemExit(0)`을 `BaseException`으로 잡아 부모 summary만 `FAILED`로 기록한 종료 처리 오류를 발견했고 `Exception`만 잡도록 수정했다. 기존 capture root와 summary는 수정·재사용하지 않았다.
- 별도 새 root `smoke-015-20260810-074938-2321f55a`에서 전체 P01~P08 smoke를 한 번 실행했으나 historical parser의 `runtime-boundary operation payload must be a JSON object`에서 다시 중단됐다. full mode는 개별 raw를 parser 전에 보존하지 않아 정확한 실패 probe는 미확인이다. retry하지 않았다.
- 결론: P01 최초 호출 실패는 항상 재현되는 현상이 아니다. 그러나 ordinal 015 전체 one-shot은 아직 성공하지 않았으므로 정식 15-ordinal batch는 계속 `NO-GO`다. 실제 model turn은 capture에서 0으로 직접 확인했다.

## Phase D reconstructed replay 우회 폐기와 정본 복귀

- 작업일: 2026-08-10. 사용자가 집 PC에 원본 Phase B `P001~P015` 자료가 모두 존재하며 다음 동기화 때 제공할 예정임을 확인했다. 따라서 `PROFILE_I_RAW_EVIDENCE_ABSENT`는 원본 부재가 아니라 현재 PC의 일시적 미동기화 상태로 재분류했다.
- 원본이 영구 소실됐다는 가정 아래 만든 historical reconstructed replay R3 명세·심사·구현·테스트·smoke 스크립트와 결과 문서, 로컬 review package와 AppData smoke root를 제거했다. 이 계보의 `REPLAY_COMPLETE`나 source qualification은 더 이상 프로젝트 경로로 사용하지 않는다.
- 원래 Phase D revision 2 정본, ChatGPT Pro 재심 결과, Candidate 015 closure와 Phase B/C 구현은 보존했다. 개발 과정에서 확인한 교훈은 “원본 가용성을 사용자에게 먼저 확인하고, 복원 우회에는 시간 제한을 둔다”는 절차로만 유지한다.
- 다음 작업은 원본 동기화를 기다리며 독립적으로 가능한 Profile R artifact 제작부터 진행한다. Profile I artifact는 집 PC의 P001~P015를 받은 뒤 raw hash·run lineage를 확인하고 원래 revision 2 명세로 만든다. Phase E/F와 actual model turn은 계속 `NO-GO`다.

## Phase D Profile R source intake

- 작업일: 2026-08-10. 원래 revision 2 명세의 Profile R `realistic-compat-migration-001` artifact 제작을 시작했다. base `dbd84422a315b8bc34d0fc2583862f5add8c7c44`와 reference `56c91334fb32c4699d11ef80769831f14a0431d6`의 commit/tree/ancestry를 Git object에서 확인했다.
- `source-intake.json`에 base/reference tree, 91개 changed path, 5,675 insertions, 261 deletions과 LF-normalized name-status/numstat SHA-256을 고정했다. 상태는 `SOURCE_VERIFIED_COMPOSITION_PENDING`이며 snapshot·checker·challenge ready를 주장하지 않는다.
- 새 표적 테스트는 Git이 계산한 tree·ancestry·diff counts·hash를 manifest와 직접 대조한다. `test_realistic_phase_d_fixtures.py` 결과는 `2 passed in 0.23s`, `git diff --check`는 통과했다. model·SDK·Codex·sandbox 호출은 0회다.
- 다음 작업은 91개 changed path를 명세의 7개 composition category와 중복 제거 semantic group으로 분류하는 `r-change-composition.json` 작성이다. Profile I는 P001~P015 원본 동기화 전까지 착수하지 않는다.

## Phase D Profile R change composition 후보

- 작업일: 2026-08-10. Profile R base/reference의 91개 changed path를 `r-change-composition.json`에 전수 분류했다. 결과는 authored source 21, authored test 11, authored spec/operator contract 32, generated schema 2, golden mirror 17, historical result/evidence 8개다.
- generated schema·golden mirror·historical record는 `counted_for_structure=false`로 두고, golden은 대응 reference fixture source와 같은 `semantic_group_id`로 결합했다. 중복 제거 뒤 실제 구조 집계는 64개 semantic group이다. 상태는 `COMPOSITION_CANDIDATE`이며 W snapshot·Task·checker ready를 주장하지 않는다.
- 재현 가능한 generator `build_profile_r_change_composition.py`와 검증 테스트를 추가했다. 테스트는 exact Git diff 91개와 1:1 path coverage, category 허용값, counted group 유일성, golden→canonical source 관계와 category count를 검사한다.
- 표적 결과는 `4 passed in 0.28s`, `git diff --check` 통과다. model·SDK·Codex·sandbox 호출은 0회다. 다음 작업은 집 PC 원본 동기화이며, 그 전에는 Profile R W snapshot과 Profile I를 확장하지 않는다.

## 회사→집 exact-tree 인수인계와 P001~P015 원본 보호 절차

- 작업일: 2026-08-10. 회사 기능 기준 commit `712ce8a13b86685f17696da93a42701bdc220f49`, tree `e978f80e16bbb126ba415f72c970cbd984bc8c3c`에서 집 PC로 작업을 돌려보내는 방향별 인수 문서와 시작 프롬프트를 작성했다.
- 인수 문서는 집 branch를 원격 tip과 ff-only로 맞추기 전에 dirty·untracked·ignored 자료, stash와 local-only commit을 먼저 보존하도록 한다. 집에 있는 P001~P015가 ignored 또는 repository 밖 raw일 수 있으므로 `reset`, `clean`, `stash`, 강제 checkout을 금지했다.
- P001~P015는 첫 세션에 바로 GitHub로 올리지 않는다. ordinal별 존재·run ID·파일 수·byte 수·manifest/hash와 민감정보 포함 여부를 읽기 전용으로 확인한 뒤 공개 가능 artifact, 별도 암호화가 필요한 Controller/Judge raw, 복사 금지 secret으로 분류해 사용자 승인을 받는다.
- 현재 경로는 원래 Phase D revision 2다. reconstructed replay R3는 부활시키지 않으며, Profile R은 source intake·91-path composition까지만 완료됐다. Profile I는 원본 인수 뒤 시작하고 main 병합도 원본 무결성 확인 뒤 검토한다.
- 이번 작업은 문서와 프롬프트 갱신뿐이다. 테스트·probe·SDK·Codex·model turn과 P001~P015 접근은 실행하지 않았다.

## 집 P001~P015 원본 inventory의 Git 정본화

- 작업일: 2026-08-10. 집 `codex/runtime-boundary-p01`을 회사 인수 commit `fde51c18590261b9073d22f44a9eb4f3f437b59b`과 ff-only로 맞추고 local/remote HEAD·tree·clean status·remote diff 일치를 확인했다.
- 저장소 밖 보존 root에서 P001~P015 명명 W root 15개를 모두 확인했다. P001~P012는 W/J/S에 접근해 ordinal마다 pending manifest가 참조하는 7개 파일의 hash·크기 7/7 일치를 확인했다. 이는 partial hash 검증이며 pending manifest를 sealed run으로 승격하지 않는다.
- protected private root는 6개다. P015 J/S가 서로 다른 2개 private root 아래 존재하는 것은 verified bundle manifest로 결합했지만, 남은 4개를 P013/P014 J/S에 ordinal별로 매핑하고 내용을 읽는 일은 ACL을 바꾸지 않고 수행할 수 없어 미확인으로 유지했다.
- P015 exact four-file bundle은 payload 2/2, files manifest/seal 결합을 통과했다. 심사 추출본과 ZIP은 각각 package manifest 27/27이 일치했다. 따라서 ordinal 기준 partial-or-better hash verified 13개, protected-unverified 2개, fully sealed verified 1개다.
- 접근 가능한 P001~P012 raw에는 SID·절대경로·인증 환경 metadata가 있고 P015에는 thread ID도 있다. 실제 secret value pattern은 발견하지 못했지만 P013/P014는 검사하지 못했다. raw를 공개 Git에 넣지 않고 민감값을 제거한 `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json`과 운영 보고서만 추가했다.
- 이 inventory는 원본 소실 오판을 막는 source-provenance 영수증이다. 같은 저장소에 reference가 존재하는 것은 승인된 same-repository independence와 모순되지 않지만, Profile I W에는 raw·reference·후속 원인 결론을 투영하지 않고 Phase D Worker/Judge 정보 경계와 누출 검사를 유지한다.
- 이번 후속은 inventory와 인수 상태 문서만 수정했다. P001~P015 원본 이동·수정·재실행, 테스트·probe·SDK·Codex·model turn은 0회다. 다음 gate는 P013/P014의 ACL 비변경 read-only inventory와 승인된 익명화 import다.

## 집 inventory 뒤 회사 로컬로 작업 반환

- 작업일: 2026-08-10. 사용자가 오늘 집 작업을 종료하고 원래 프로젝트를 주관한 회사 로컬에서 다시 이어가기로 했다. 현재 방향을 집→회사로 전환해 `home-to-company-codex-handoff.md` revision 3과 전용 회사 시작 프롬프트를 작성했다.
- 최소 포함 commit은 P001~P015 inventory를 Git 정본화한 `70a9a8adea7b7c492847f181c3901317332c9147`이다. 이 인수 문서를 포함하는 최종 원격 tip은 그 후손으로 전달하며 회사는 fetch 뒤 latest tip과 exact tree를 사용한다.
- 회사 첫 세션은 dirty·stash·local-only·main-only 보존 게이트, ff-only 동기화, local/remote commit·tree 확인과 inventory 이해 보고만 수행한다. 집의 raw hash 계산을 반복하거나 reconstructed replay R3, Profile R/I 구현, 테스트·probe·model을 선행하지 않는다.
- 다음 gate는 P013/P014 protected raw의 ACL 비변경 read-only inventory와 raw/익명화 projection import 경계에 대한 사용자 승인이다. Phase E/F와 main 병합은 계속 열지 않는다.
- 과거 회사→집 handoff와 양방향 시작 프롬프트에는 역사 표식을 추가했다. 이번 작업은 문서뿐이며 raw·코드·시험·artifact 의미와 model turn을 변경하지 않았다.

## Phase D Profile R 익명화 base W snapshot 후보

- 작업일: 2026-08-11. P013/P014 protected raw는 추후 검증된다고 가정하되 없는 byte를 재구성하지 않고, Git object만으로 독립 진행 가능한 Profile R의 base Worker snapshot을 만들었다.
- source allowlist는 base commit `dbd84422a315b8bc34d0fc2583862f5add8c7c44`의 S1 suite·manifest, 네 public fixture와 `tools/benchmark-runner` 전체로 제한된다. 결과는 99 files, source 929,726 bytes이며 reference diff·review·revision log·실행 결과는 포함하지 않는다.
- Controller-only mapping은 실제 프로젝트명, synthetic Windows user path, 역사 연도와 테스트용 예시 이메일 네 개를 고정 UTF-8 byte mapping으로 치환한다. W 후보에서 실제 사용자명·절대 user path·프로젝트명·2026 연도·email-like pattern을 다시 검색한 결과 잔여 0건이다.
- 생성기는 detached Git object의 regular blob만 허용하고 traversal, backslash/colon path, case-fold collision, symlink·gitlink와 기존 output 덮어쓰기를 거부한다. 각 source blob OID/hash와 W hash, 적용 mapping ID를 `worker-snapshot-manifest.json`에 기록한다.
- Profile root `.gitattributes`는 W의 generated bytes를 `-text`로 고정해 Windows `core.autocrlf`가 snapshot을 바꾸지 못하게 한다. 원본 golden patch의 의도된 trailing whitespace는 base byte와 함께 보존한다.
- W 후보는 99 files, tree aggregate SHA-256 `62cb754fb6b6bd107ad79d11024553948b0e1c1e9185eed3073d6249e6e6fa3`이다. 별도 두 output root에 재생성한 workspace와 manifest가 committed candidate bytes와 일치했다.
- 표적 시험은 `6 passed in 10.32s`, 두 Python 파일 `py_compile` 통과다. 첫 생성 명령은 존재하지 않는 `tools/benchmark-runner/.venv`를 지정해 Python 실행 전에 실패했고, 실제 Python 3.12 환경인 `stages/b1-sequential/.venv`로 교정했다. 제품 코드나 artifact 실패는 아니었다.
- 현재 상태는 `ANONYMIZED_BASE_SNAPSHOT_CANDIDATE`이며 `challenge_ready=false`다. 8-Task envelope, public requirement/check, J source bundle, reference·negative mutation·property checker는 아직 없다. SDK·Codex·probe·model turn은 실행하지 않았다.

## Phase D Profile R 8-Task·공개 검사 pack 후보

- 작업일: 2026-08-11. 익명화 base W 99 files 위에 `public_requirement` provenance의 공개 overlay 14 files를 결정론적으로 결합했다. 최종 W 후보는 113 files, tree aggregate SHA-256 `8ea7b95b7c512bbcbbfad7623e8ed92854b3c4debb1e3737f288a4751f571d79`, manifest SHA-256 `ee2604277fd553d7b5b8fe0b635d7c92734ed2af10243d4d69a46e9a1fe46767`이다.
- `benchmark-run.yaml`은 승인 명세의 R01~R08 의존 관계를 그대로 사용한다. R01에서 갈라진 R02·R03이 R04에서 합쳐지고 R05→R06→R07→R08로 이어져 Task 8개, 최장 깊이 7, fan-in R04~R08을 가진다. 각 Task는 같은 공개 goal·completion criteria·inputs·read/write scope를 SS1/B1에 제공할 수 있는 B1 `RunSpec` version 1로 파싱됐다.
- W의 고정 `benchmark_checks/check_profile_r.py`는 Task별 공개 정상 계약만 검사한다. R01 inventory/ledger, R02 discriminator, R03 fixture graph, R04 Plan identity/order, R05 reserve/lifecycle reuse, R06 status/property/export API, R07 model-free regression, R08 structured operator relation을 분리했다. 이 파일과 `.orchestrator/**`, public requirements, root RunSpec은 모든 Task write scope 밖의 보호 파일이다.
- pristine W에서 R01~R08 공개 completion check가 각각 exit 1과 고정 `Rxx_PUBLIC_CONTRACT_FAILED`만 반환하는 것을 확인했다. 이는 아직 Worker solution이나 reference를 넣지 않은 의도된 표적 실패다. public check는 실제 model·SDK·Codex·network를 호출하지 않는다.
- snapshot builder는 detached base Git object와 versioned public overlay를 별도 provenance로 결합하고 collision, unsafe path, symlink, case-fold duplicate와 민감 literal을 계속 거부한다. 두 재생성 결과와 committed W/manifest가 byte-identical임을 검증했다.
- 검증 결과는 B1 `RunSpec` parse `tasks=8`, `test_realistic_phase_d_fixtures.py` `9 passed in 9.41s`, Python compile, `git diff --check` 통과다. 첫 재검증에서 이전 compile이 만든 ignored `__pycache__` 1개 때문에 W file count가 114로 보였고, 생성물이 아닌 해당 cache만 제거한 뒤 113-file 정본으로 재검증했다.
- 현재 상태는 `ANONYMIZED_WORKER_TASK_PACK_CANDIDATE`, `challenge_ready=false`다. Worker/reference solution, versioned J source bundle, property checker, negative mutations, positive replay와 Judge boundary는 아직 만들지 않았다. Phase E live와 Phase F model turn은 계속 `NO-GO`다.

## Phase D Profile R W·J source bundle 검증

- 작업일: 2026-08-11. Profile R Worker가 공개 검사를 실제로 실행할 수 있도록 B1 schema/source를 base allowlist에 추가하고, 공개 overlay에 LF 고정 `.gitattributes`를 추가했다. 최종 W는 base 115 files와 overlay 15 files를 합친 130 files이며 tree aggregate SHA-256은 `d83ffcb39405eabc0fae45329737e4da424264523be4fa678e7bff5e5bbae950`이다.
- 공개 검사는 숨겨진 golden tree를 읽지 않는다. R06은 현재 fixture output과 공개 property/export 계약을 검사하며, R07은 독립 W에서 실행 가능한 S2 fake regression을 실행하고 Git history가 필요한 기존 S1 함수 다섯 개는 source 존재를 정적으로 확인한다. reference를 적용한 disposable W에서 R01~R08 공개 검사가 모두 `Rxx_PUBLIC_CONTRACT_OK`로 통과했다.
- Judge source bundle은 property catalog·선행 DAG·정보 경계·누출 catalog·reference patch·8개 negative mutation·pristine/reference/mutation evidence·checker를 포함한다. manifest 제외 31 files, payload aggregate SHA-256 `77c6f1a0ce9ee8cac1d96f1b406b5291e0bca00e00de1361e41cd29f06043f4e`, bundle manifest SHA-256 `083e262abfe80870062ae43eea40218a44cc2f8992fd04f40086e35cc6cf8a61`, reference patch SHA-256 `0a33bc75420c7b7f0fa8a213654feff8572712689bb4606c06a97c040829de44`다.
- pristine은 대상 property를 실패하고 reference는 R-P01~R-P08 8/8을 통과한다. 8개 negative mutation은 각각 목표 property를 실패시키며 관계없는 property는 통과하거나 선행 실패로 차단된다. 생성기를 서로 다른 Python process에서 두 번 실행했을 때 bundle manifest와 reference patch hash가 동일했다.
- 회귀 중 발견한 두 문제를 교정했다. W 파일 집계가 테스트가 만든 `__pycache__`를 정식 artifact로 세지 않도록 cache 디렉터리를 제외했고, Windows checkout의 CRLF였던 routing schema 두 개를 기존 schema exporter로 LF 정본화했다. 해당 두 회귀 시험은 `2 passed in 1.10s`, Profile R fixture 표적 시험은 `12 passed in 11.99s`, 최종 Benchmark Runner 전체 회귀는 `303 passed in 292.66s`다.
- 현재 상태는 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`, `challenge_ready=false`다. Worker/Judge 정보 분리와 source bundle은 준비됐지만 보호된 Judge filesystem/no-network 실행 경계를 아직 검증하지 않았다. 따라서 실제 Worker 실행, Phase E live, Phase F model turn은 계속 `NO-GO`다. 이번 작업의 model·SDK·Codex·app-server·sandbox·network 호출은 0회다.

## Phase D Profile R Judge 경계 구현 후보

- 작업일: 2026-08-11. 동결 명세 §10의 W read-only, protected runtime J read-only, fresh O read/write, S deny와 parent/child operation parity, loopback network denial을 기존 `runtime_boundary.py` primitive와 `probe_runtime_boundary.py`의 Judge 전용 mode로 구현했다. 실제 model turn을 만드는 SDK thread 경로는 추가하지 않았다.
- runtime J는 source commit의 Git object에서 byte-exact 추출하며 source/runtime file set과 hash, protected root identity를 결합한다. Judge probe와 property checker는 repository J source가 아니라 이 runtime J만 실행한다. 실행 전후 W/J/S tree와 fresh O residue를 다시 계산하며, loopback 연결 성공·보호 root mutation은 `CHALLENGE_INVALID`, 그 외 증명 결손은 `CHALLENGE_NOT_READY`로 닫는다.
- Judge source bundle에는 기존 표준 라이브러리 probe의 byte-exact 복사본 1개가 추가됐다. manifest 제외 32 files, payload aggregate SHA-256 `5bc46cd27b6e0ef9dae01920c9f5552905cbe6cfb1ea6cf0879e0a9734dee0ed`, bundle manifest SHA-256 `80e173d4ac75d55c7082b87408d701361e3ec422f7de19b101e80115e0ff6561`다. checker 내부 pytest 임시 파일은 fresh O 아래에서만 생성·정리되도록 고정했다.
- 표적 검증은 `19 passed, 1 skipped in 11.78s`다. skip은 현재 Windows 계정에서 test용 symlink 생성 권한이 없어 발생했다. 전체 Runner 회귀는 `309 passed, 1 skipped, 1 failed in 277.28s`였고, 유일한 실패는 기존 SDK Cell 테스트의 임시 `cell-state.json` 교체에서 발생한 Windows `WinError 5`였다. 실패 테스트만 재실행한 결과 `1 passed in 8.33s`로 통과해 Judge 변경과 무관한 일시적 파일 잠금으로 분리했다. 전체 회귀는 반복하지 않았다.
- 현재 코드는 `JUDGE_RUNTIME_BOUNDARY_CANDIDATE`를 실제로 만들 수 있는 실행 진입점까지 준비됐지만 아직 Git object로 동결되지 않았으므로 `codex sandbox` 경계 시험은 실행하지 않았다. 다음 순서는 이 변경분을 commit한 뒤 exact commit에서 W/J를 추출해 model-free Judge 시험을 1회 실행하는 것이다. 실제 Worker 실행, Phase E live, Phase F model turn과 `challenge_ready=true` 전환은 계속 `NO-GO`다.

## Phase D Profile R Judge 경계 실제 실행

- 작업일: 2026-08-11. 실행 가능성 수정분을 commit `3cbdcb47d34412abd6a7ecc75956610795ec0a52`로 동결한 뒤 새 one-shot root에서 Profile R Judge 경계를 1회 실행했다. run ID는 `profile-r-judge-candidate-20260811-3cbdcb4-1`, 최종 판정은 `CHALLENGE_INVALID`, model turn은 0이다.
- W/J read-only, fresh O read/write와 종료 뒤 empty, S 전면 access denied, W/J/S 무변경은 확인됐다. Probe는 exit 0으로 typed 결과를 반환했고 Checker도 pristine W의 등록 property 실패를 exit 1 canonical JSON으로 반환했다. 이 Checker 실패는 사전 등록 negative control과 일치한다.
- 실패 verification code는 `COMMON_PARENT_ENUMERATION_NOT_DENIED`, `DRIVE_ROOT_ENUMERATION_NOT_DENIED`, `LOOPBACK_CONNECTION_ACCEPTED`, `LOOPBACK_NOT_PERMISSION_DENIED`, `PARENT_CHILD_MATRIX_MISMATCH`, `SYMLINK_CREATE_NOT_SUCCESS` 여섯 개다. 특히 `network.enabled=false` profile에서도 parent·child가 Controller loopback listener에 접속해 accepted connection count가 2였다.
- 이 결과를 통과로 완화하거나 같은 조건에서 반복하지 않는다. 현재 Windows Codex 0.144.4 permission profile만으로 동결 명세의 no-network Judge 경계를 증명하지 못했으므로 Profile R은 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`, `challenge_ready=false`에 머문다. 실제 Worker, Phase E/F와 model turn은 계속 `NO-GO`다.
- 다음 관문은 loopback까지 차단하는 별도 OS 격리 경계를 채택할지, 아니면 Judge를 신뢰된 로컬 검사기로 재분류해 명세·주장 범위를 낮출지에 대한 사용자 결정이다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-judge-boundary-result.md`에 기록했다.

## Phase D Profile R Docker Judge 사전검증

- 작업일: 2026-08-11. Windows Codex sandbox의 loopback 차단 실패를 우회해 통과 처리하지 않고 별도 실행환경 후보인 Docker Desktop을 실제 확인했다. Docker Desktop `4.85.0`, Linux Engine `29.6.2`가 동작했고 `python:3.12-slim` image를 digest `sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`으로 고정했다.
- 실제 Profile R W/J를 read-only, 새 O를 read/write로 mount하고 S는 노출하지 않았다. `--network none`, read-only root filesystem, capability 전부 제거, no-new-privileges, 비root 사용자, PID·CPU·memory 제한을 적용했다. W/J/root write는 `EROFS`, O/tmp write는 성공했고 Windows Controller listener 연결은 `ENETUNREACH`, accepted connection은 0이었다.
- 같은 격리에서 현재 stdlib-only Checker가 Linux에서 실행됐다. pristine W는 exit 1 typed 결과로 `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE`를 실패 처리했고 총 property 8개, `workspace_mutated=false`였다. 기존 Windows 실행의 negative control과 의미상 일치한다.
- Docker CLI 설치 뒤 engine이 꺼져 있어 Desktop을 시작했다. 잘못된 W 경로 1회는 container 전에 중단됐고, inline Python quote가 제거된 1회는 checker 시작 전 문법 오류로 끝났다. 최종 시험은 stdin 전달과 새 root를 사용해 전 항목을 다시 수행했다. 실패 준비 시도는 통과 근거로 세지 않았다.
- 판정은 `DOCKER_JUDGE_PREFLIGHT_PASSED`다. 아직 Docker backend, image recipe, timeout·kill·seal·Runner 통합과 Windows 전용 검사 분리는 미구현이므로 `challenge_ready=false`, Phase E/F와 model turn `NO-GO`를 유지한다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-preflight.md`에 기록했다.

## Phase D Profile R Docker Judge backend와 결과 분류

- 작업일: 2026-08-11. 사전검증된 Docker 격리를 재사용하는 고정 실행 backend를 commit `8bb3418a6aea41c078252cf75f984fb85386fd92`로 구현했다. W/J read-only, O read/write, S 미노출, network none, read-only root, capability 제거, no-new-privileges, 비root 사용자, resource limit과 digest 고정 image를 manifest 및 verifier 계약으로 고정했다.
- Docker 시작 실패, timeout, 강제 cleanup 실패, 예상 밖 exit, checker payload 손상, 출력 제한, W/J 변경과 O 잔여를 별도 status/reason code로 분류하고 stdout·stderr·process·manifest·result를 보존한다. result verifier는 manifest binding, self hash와 판정을 독립 재계산한다.
- 단위시험은 `11 passed in 0.49s`, 기존 Judge 및 Phase D fixture와 합친 표적 회귀는 `33 passed, 1 skipped in 19.23s`, Python compile과 `git diff --check`는 통과했다. skip은 기존 Windows symlink 권한 제한이다.
- exact commit에서 만든 pristine W/J로 run `profile-r-judge-candidate-20260811-8bb3418-1`을 실제 실행했다. 컨테이너 exit 1을 runtime 장애가 아닌 `CHECKS_FAILED`로 회수했고, 실패 property는 사전 등록된 `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE`였다. W/J는 실행 전후 동일하고 O는 비었으며 `workspace_mutated=false`, timeout false, 종료 뒤 container 잔여 없음, model turn 0이다.
- 현재 Docker Judge 고정 실행과 결과 회수·분류는 구현됐지만 reference positive control과 negative mutation 8개를 Docker backend에서 전수 실행하지 않았다. 따라서 Profile R은 `challenge_ready=false`, Phase E/F와 model turn은 `NO-GO`를 유지한다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-backend-result.md`에 기록했다.

## Phase D Profile R Docker Judge 9종 qualification

- 작업일: 2026-08-11. reference 1개와 사전 등록 negative mutation 8개를 fresh W/J/O에서 순서대로 실행하고, 각 Docker manifest/result와 47개 evidence 파일을 batch seal로 묶는 matrix를 구현했다. 구현 회귀는 39 passed, 기존 Windows symlink 권한 제한 1 skipped다.
- 실제 실행에서 세 환경 결손을 순서대로 발견했다. base Python image에는 pytest·PyYAML·pydantic·jsonschema가 없어 R-P02가 실패했고, 첫 전용 image에는 git이 없어 R-P06이 실패했으며, 두 번째 image에는 UID 65532의 passwd home이 없어 최소 subprocess 환경에서 `Path.home()`이 실패했다. exact dependency lock, git, UID 65532 `/tmp` home을 Dockerfile에 고정하고 각 공통 실패를 단일 검사로 재현·교정했다.
- Windows AppData의 긴 경로는 260자 제한으로 patch 적용 전에 중단돼 fresh short root `C:\lao-r`를 사용했다. 잘못 입력한 full commit SHA 1회는 Git 추출 전에 중단됐다. 이 준비 실패와 r1~r3 `CHALLENGE_NOT_READY` 결과는 성공 근거에 합치지 않았다.
- 최종 source commit `5146ee0ba4ab9ff69f181ca9a13d20d7fb7e96a0`, Judge image digest `fc6b0d42...93fbf98`로 batch `profile-r-docker-matrix-r5`를 184.8초 실행했다. Reference는 8/8 pass, mutation 8개는 각 사전 등록 목표 실패 패턴과 일치해 9/9 matched, W/J 무변경, O empty, container 잔여 없음, model turn 0이었다.
- 독립 verifier 재실행 결과는 `CHALLENGE_READY True 9`다. manifest SHA-256은 `a58d9761...79f363`, result는 `b25c7ad4...546ce4`, seal은 `56c1d214...e553bb`다. 민감 경로를 제외한 projection은 `benchmarks/artifacts/profile-r-docker-judge-qualification-v1/qualification.json`에 보존했다.
- Profile R 상태를 `PROFILE_R_CHALLENGE_READY`, `challenge_ready=true`로 판정한다. 이는 challenge artifact의 실험 사용 가능성만 뜻하며 SS1/B1 우위는 아직 미검증이다. 실제 Worker·SDK·model turn은 0회이며 다음 Phase 실행에는 별도 계획과 사용자 승인이 필요하다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-qualification-result.md`에 기록했다.

## Profile R qualification 뒤 회사→집 작업 반환

- 작업일: 2026-08-11. 회사에서 완료한 Profile R W·J bundle, Windows Judge 경계 실패, Docker 우회와 최종 9종 qualification을 집의 기존 Codex 작업으로 넘기기 위해 `company-to-home-codex-handoff.md`를 revision 2 현재 정본으로 갱신했다.
- 전달 branch는 `codex/phase-d-artifacts`이며 최소 포함 qualification commit은 `0112c20e6c59b1555ac444836b608af1e773d936`이다. 집은 fetch 뒤 이 commit을 포함한 원격 latest tip과 exact tree로 맞춘다. 기존 `codex/runtime-boundary-p01`이나 main에 병합하지 않는다.
- Git에는 코드·Dockerfile·dependency lock·시험·익명화 qualification projection이 포함된다. 회사 raw root `C:\lao-r\profile-r-docker-matrix-r5`, local Docker image와 집 P001~P015 원본은 Git 비정본이므로 자동 동기화된다고 주장하지 않는다.
- 같은 집 Codex 작업에 전달할 시작 프롬프트는 dirty·stash·local-only·ignored raw 충돌을 먼저 확인하고, 정상 동기화 뒤 Profile R `SS1 → B1` 최초 pair 실행계획 후보만 작성하도록 갱신했다. 실제 Worker·SDK thread·model turn, Docker qualification 반복과 main 병합은 별도 사용자 승인 전 금지한다.

### P001~P015 원본 전달 지시 교정

- 최초 revision 2는 집 P001~P015를 보존만 하고 Git에 넣지 않도록 막아 Profile I source gate를 계속 차단하는 오류가 있었다. 사용자의 의도는 원본을 익명화해 숨기는 것이 아니라 Git 정본에 byte 그대로 올리고, Worker runtime에서 해당 source root를 제외해 시험 정보 경계를 지키는 것이었다.
- repository가 `PUBLIC`임을 확인했고 사용자는 SID·절대경로·thread ID·실행 metadata를 포함한 P001~P015 원본 공개 push를 명시적으로 승인했다. 실제 credential 후보가 발견될 때만 public push를 중단하며, raw를 임의 수정·익명화하지 않는다.
- revision 3은 clean-context 일회용 독립 AI가 원본을 읽기 전용으로 대조·copy·hash 검증하고, 현재 Codex는 raw 내용을 보지 않은 채 exact import root만 `git add -f`, commit, push하도록 고쳤다. raw import가 완료돼야 Profile I model-free artifact 작업을 재개한다.

## Profile I source gate와 Worker projection 완료

- 작업일: 2026-08-11. byte-exact import된 P001~P015 171개 raw file을 source index·files manifest와 다시 대조하고, P001~P014 실패 계보와 P015 candidate를 source commit·revision evidence·typed failure/result artifact에 결합했다. source gate 표적 시험은 6 passed다.
- 기준 commit의 Git object 10개, public requirement overlay 9개와 P001~P014 public observation projection 1개를 결합해 20-file W snapshot을 만들었다. W tree aggregate SHA-256은 `870e1f2eda2a047d59e8a7f736aa3c8f513113989758c71ca73d2b262a25df31`이다.
- I01~I08은 동결 dependency graph, 같은 public goal·criteria·input·scope와 보호 path를 사용한다. public Check는 Worker가 선택한 symbol·regression·changed path·evidence declaration만 확인하고 exact reference 구현 이름이나 hidden property를 요구하지 않는다.
- `worker-information-boundary.json`은 모든 W file·Task·Check·feedback surface의 hash/provenance/cap을 열거한다. leakage catalog는 source evidence와 final reference-only hash를 결합하며 W에서 P015, correction lineage, J/S raw, SID·절대경로·thread·sentinel과 reference identity를 발견하지 않았다.
- source gate와 Worker projection 결합 표적 시험은 `14 passed in 2.95s`다. pristine W의 I01~I08 public Check는 의도대로 8/8 nonzero이며 actual model turn은 0회다.
- 상태는 `ANONYMIZED_WORKER_TASK_PACK_CANDIDATE`, `WORKER_INFORMATION_BOUNDARY_VERIFIED`, `challenge_ready=false`다. 다음 관문은 Profile I J source bundle, reference replay, deterministic property checker와 negative mutation이며 Docker qualification, 실제 Worker와 Phase E/F model turn은 아직 열지 않는다.

## Profile I Worker 완료 뒤 집→회사 작업 반환

- 작업일: 2026-08-11. 집에서 완료한 P001~P015 byte-exact import, Profile I source gate와 20-file Worker snapshot을 회사 기존 clone으로 반환하기 위해 `home-to-company-codex-handoff.md`를 revision 4로 갱신했다.
- 전달 branch는 `codex/phase-d-artifacts`이며 반드시 포함할 작업 commit은 `a66386dea97681d68dc51975c28586ba9627a5a0`이다. 회사는 fetch 뒤 이 commit을 포함한 원격 latest tip과 exact tree로 ff-only 동기화한다.
- 새 회사 시작 프롬프트는 이미 통과한 raw import·source gate·W build를 반복하지 않고 Profile I versioned J source bundle, reference, property checker, negative mutation과 model-free Docker qualification부터 이어가도록 고정했다.
- 실제 SS1/B1 Worker, SDK thread, live Plan, Codex model turn과 main 병합은 여전히 금지한다. Profile I artifact가 준비돼도 별도 artifact 심사와 사용자 Phase E 승인 전에는 live 비교를 시작하지 않는다.

## Phase D Profile I J source bundle과 Docker qualification

- 작업일: 2026-08-12. P015 reference source를 Worker 익명화 규칙으로 투영하고 공개 원장·claim·Task 계약을 완성한 `reference.patch`, I-P01~I-P10 property catalog/DAG/checker, 10개 negative mutation과 evidence를 versioned J source bundle로 만들었다. reference 10/10 pass, pristine fail, mutation 10/10 목표 실패·의존 차단 일치로 `PROFILE_I_SOURCE_BUNDLE_VERIFIED`를 확인했다.
- 기존 `realistic_judge.py`의 Git-object W/J 추출과 보호 root 경계를 profile별 prefix 인자로 재사용하고, 기존 Docker Judge backend 위에 Profile I 11셀 matrix만 추가했다. 새 Controller·seal·live lifecycle을 만들지 않았고 실제 model·SDK·Codex thread는 0회다.
- 첫 r1은 11셀 결과가 일치했지만 보호 J의 임의 디렉터리를 고정 경로로 읽은 verifier 오류와 W/J까지 포함한 706-file 과대 봉인 때문에 최종 근거에서 제외했다. verifier를 exact-one protected J 탐색으로 바꾸고 봉인 범위를 batch 2 + 11×5 evidence = 57개로 제한했다.
- fresh r2 `profile-i-docker-matrix-r2`는 reference 10/10 pass, negative mutation 10개가 각각 사전 등록 목표 실패 패턴과 일치해 11/11 matched, `CHALLENGE_READY`가 됐다. manifest `69a5d27...f5b39`, result `6f4f322e...e03c2`, seal `4b70211b...3841f`, model turn 0이다.
- 최종 표적 회귀는 ASCII 임시 경로에서 `33 passed, 1 skipped`, 새 LF clone의 source gate·Worker byte 재현은 `14 passed`다. 회사 `core.autocrlf=true`가 만든 첫 byte 차이는 fixture `.gitattributes` LF 고정으로 닫았다.
- Profile I 상태를 `PROFILE_I_CHALLENGE_READY`로 판정한다. 이는 challenge artifact 준비 완료이지 B1 우위 증명이 아니다. Phase E/F live·model turn과 main 병합은 별도 승인 전 `NO-GO`다. 상세 결과는 `docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-docker-judge-qualification-result.md`에 기록했다.

## Phase E 0-turn 실행 후보 동결

- 작업일: 2026-08-12. 사용자 Phase E 승인에 따라 실제 Worker나 model turn을 열지 않고 Profile R·I의 SS1/B1 네 Cell 실행계획만 만들었다. 순서는 R SS1 → R B1 → I B1 → I SS1이며 한 번에 Cell 하나, Cell별 명시 승인, 자동 연속 실행·자동 재시도 금지다.
- 모델은 `gpt-5.6-sol`, reasoning effort `high`, ChatGPT 구독 인증, `openai-codex==0.144.4`로 고정했다. 최초 계획 32 turns, 전체 상한 40 turns이고 runtime contract v2의 `runtime-boundary-worker`, `deny_all`/`never`, legacy sandbox 인자 생략을 Plan에 결합했다.
- 첫 구현 시험에서 source binding과 candidate seal의 자동 기본값 `schema_version`·`kind`를 해시 입력에서 누락한 오류를 발견했다. commit `79f9100125e2d5f6cecb3fe00b93e461afe1cdfd`에서 기본값을 명시해 자기검증과 재현 검증을 통과시켰다.
- Codex sandbox OS 사용자는 실제 Windows 사용자의 CLI 로그인 저장소를 보지 못해 최초 preflight가 `requires auth`로 중단됐다. ChatGPT 로그인을 실제 사용자 경계에서 완료한 뒤 같은 경계에서 account/model-list만 조회했고, 후보 검증은 로그인 없는 일반 경계에서 다시 수행했다. API key 환경 변수 이름은 없었고 값은 조회하지 않았으며 actual model turn은 0회다.
- 후보 experiment는 `exp_20260812_77e111e8_1`, Plan fingerprint `77e111e868b03e5ff1267c736031cb2a5588e6bcaf420e4388724eb0e9aea57d`, candidate seal `1e93ef12f11f7f05902ba7f0e25708f72dc9ed2e65ccea74956938caa5e57fc7`다. exact file set·hash·source commit/tree·R/I qualification·P015 runtime-boundary 결합을 별도 verifier가 재계산했다.
- Phase E 표적 시험은 회사 checkout과 clean short clone에서 각각 `3 passed`다. 회사 checkout 전체 회귀는 `351 passed, 1 skipped, 2 failed`였고 실패 2건은 기존 Profile I source-intake의 CRLF working-tree bytes가 LF 정본과 달라진 동일 원인이다. clean clone 전체 회귀는 긴 경로로 인한 불완전 checkout 1회와, Git 비정본 frozen wheel 결손 및 저장소 내부 pytest state root 계약 위반 1회로 환경이 무효였으므로 코드 회귀 숫자에 합치지 않았다.
- 상태는 `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`이다. 네 Cell은 아직 전부 미실행이며 SS1/B1 우위·route·일반화·기본 채택 주장은 없다. Phase F는 계속 `NO-GO`이고 첫 R SS1 Cell도 별도 사용자 승인을 받아야 한다.

## Phase F one-Cell Controller model-free 구현

- 작업일: 2026-08-12. 사용자가 승인한 범위에 따라 Phase E candidate를 검증하고 한 호출에서 정확히 다음 Cell 하나만 backend로 넘기는 `realistic_phase_f.py`를 구현했다. 실제 SDK adapter는 넣지 않았고 model·Worker·Codex process 호출은 0회다.
- Controller는 외부 state root, byte-exact Plan/candidate seal 복사, self-hashed state, write-once dispatch claim, expected ordinal과 별도 Cell/model 승인, request/result identity, Cell당 10-turn 상한을 강제한다. claim 뒤 실패는 `FAILED`로 닫고 자동 재시도하지 않는다.
- Fake backend 시험에서 Profile R SS1 Cell 1만 정확히 1회 호출됐다. 반환 뒤 Cell 1은 `SEALED`, Cell 2~4는 `PLANNED`이며 Cell 2 dispatch claim은 존재하지 않았다. 잘못된 ordinal, Cell 승인 없음, live model 승인 없음은 backend 호출 전 거부됐다.
- 최초 시험은 UTC `datetime`의 `+00:00`과 Pydantic canonical JSON의 `Z` 표현 차이로 state self-hash가 불일치했다. hash 전 UTC 표현을 canonical `Z`로 정규화해 교정했다. 최종 Phase F 표적 시험은 `5 passed`, Python compile과 `git diff --check`는 통과했다.
- 상태는 `PHASE_F_ONE_CELL_CONTROLLER_MODEL_FREE_READY`다. 실제 Profile R SS1 실행에는 runtime contract v2 live backend 구현·Fake transport 계약 시험과 별도 사용자 model-usage 승인이 남아 있다.

## Phase F SDK runtime contract v2 model-free 구현

- 작업일: 2026-08-12. Phase E Plan의 runtime contract v2를 SS1 `SdkRuntime` 경계에 구현했다. 기존 legacy `workspace_write` runtime은 재사용하지 않고 `runtime-boundary-worker`, `deny_all`/wire `never`, `gpt-5.6-sol`, effort `high`, thread·turn legacy sandbox 인자 생략을 별도 계보로 고정했다.
- `CodexPhaseFAppServerPort`는 실제 `openai-codex==0.144.4` 저수준 client를 지연 생성하며 raw `permissionProfile/list`, `thread/start` response와 `thread/started` notification을 결합한다. import나 객체 생성만으로 app-server를 열지 않으며 실제 실행은 외부 호출자가 `open()`을 호출할 때만 가능하다.
- Fake app-server와 fake 저수준 Codex client로 exact parameter, persistent single thread, account/model/profile·thread binding fail-closed, API-key 이름 차단, 다섯 config override 계약을 시험했다. Phase F SDK 표적 시험은 `14 passed`다.
- Phase E/F·SS1·기존 SDK 영향 회귀는 `51 passed`였고 Phase E candidate 재생성 1건만 신규 untracked 파일 때문에 clean-source precondition에서 중단됐다. 실제 SDK thread·Codex process·model turn은 모두 0회다.
- 상태는 `PHASE_F_SDK_RUNTIME_V2_MODEL_FREE_READY`다. 아직 Profile R workspace 준비, SS1 backend 최종 조립, observer·Judge·Measurement·seal과 실제 Cell 1 model turn은 수행하지 않았다.

## Phase F Profile R SS1 backend model-free 수직 조립

- 작업일: 2026-08-12. 동결 Profile R Worker manifest의 130-file path/hash를 새 Git workspace로 복원하고, public R01~R08을 기존 `SS1PersistentAdapter`와 주입형 runtime에 연결하는 `realistic_phase_f_ss1.py`를 구현했다. model-free Fake는 한 persistent thread에서 8개 initial turn과 8개 passive boundary record를 만들었다.
- 통합 과정에서 R04 이후 일부 declared input은 앞 Task가 생성하므로 Cell 시작 시점에 존재하지 않는다는 문제를 확인했다. 기존 Task 의미와 순서는 유지하고 선택형 `task_resolver`가 각 Task initial turn 직전에 declared input·predecessor artifact 존재와 SHA-256을 다시 계산하도록 했다. Task ID를 바꾸면 실패한다.
- workspace observer는 turn 전후 file tree, changed/out-of-scope path, protected file hash와 공개 evidence를 계산한다. Fake clear telemetry는 model-free mode에서만 허용하며 live mode에는 사용할 수 없다. adapter outcome이 `completed`가 아니면 backend 성공 결과를 반환하지 않는다.
- 표적 시험은 `5 passed`, SS1·routing·Phase F Controller·runtime v2 결합 회귀는 `57 passed`, 최종 SS1 backend와 기존 adapter 재검증은 `24 passed`다. 실제 SDK thread·Codex process·model turn은 0회다.
- 상태는 `PHASE_F_PROFILE_R_SS1_BACKEND_MODEL_FREE_READY`다. Cell 1만 `SEALED`, Cell 2~4는 `PLANNED`, Cell 2 claim은 없다. 아직 live J/S telemetry, Docker Judge·Measurement·최종 Cell seal과 model-usage 승인이 남아 있어 실제 Cell 1은 실행하지 않았다.

## Phase F Profile R Cell finalizer model-free 수직 조립

- 작업일: 2026-08-12. 기존 Profile R SS1 backend 뒤에 주입형 Judge, 공통 `Measurement`, 최종 Cell seal과 독립 verifier를 연결하는 `realistic_phase_f_finalize.py`를 구현했다. 실제 Docker·SDK·Codex·model은 호출하지 않았다.
- Fake Judge는 manifest/result만 결정론적으로 생성하고 model turn과 Docker 실행을 모두 0으로 기록한다. finalizer는 SS1 adapter Evidence, Judge 파일, Measurement를 한 seal에 결합하며 외부 seal 파일 hash부터 모든 파일 path·size·SHA-256과 Measurement identity를 다시 계산한다.
- Fake 수직 시험에서 R01~R08 실행 뒤 Cell 1만 `SEALED`가 됐고 Cell 2~4는 `PLANNED`, Cell 2 claim은 없었다. Measurement에는 session 1, turn 8, Judge 성공과 자동 연속 실행 금지가 기록됐다. Judge result 사후 변조는 verifier가 거부했다.
- 표적 수직 시험은 `2 passed`, Phase F Controller·SDK runtime·SS1·finalizer·기존 SS1 결합 회귀는 `45 passed`, Python compile은 통과했다. actual model turn·실제 SDK thread·Codex process·Docker 실행은 모두 0회다.
- 상태는 `PHASE_F_PROFILE_R_CELL_FINALIZER_MODEL_FREE_READY`다. 다음은 변경된 Worker workspace를 기존 Docker property Judge에 전달하는 실제 Judge 포트를 model-free로 구현·검증하는 단계다. 그 뒤에만 사용자에게 실제 Cell 1 model 사용 승인을 다시 요청한다.

## Phase F Profile R Docker Judge 포트 model-free 구현

- 작업일: 2026-08-12. 기존 qualification Docker Judge 코드를 수정하지 않고, Phase F Worker가 수정한 workspace를 metadata-free W snapshot으로 복사해 기존 read-only W/J/O 경계에 전달하는 `realistic_phase_f_docker.py`를 추가했다.
- 실제 W에서 `.git`, `.pytest_cache`, `__pycache__`를 제외하고 regular file만 새 raw run root로 복사한다. 기존 `prepare_realistic_judge_roots()`가 보호 J/O/S를 만들며 Docker에는 W/J read-only, O write, S 미마운트, network none 계약이 그대로 전달된다.
- raw Docker manifest/result는 Git 밖에 남긴다. Cell evidence에는 host 경로를 제거한 public manifest/result와 raw 두 hash만 기록한다. 기존 `verify_docker_judge_result()`로 status를 재계산한 뒤에만 Phase F `JudgeObservation`을 만든다.
- Fake Docker backend로 성공과 property 실패, 명령 경계, 경로 비공개를 확인했다. 포트+finalizer 표적 시험은 `5 passed`, 기존 Docker Judge와 Phase F 관련 결합 회귀는 `59 passed`, Python compile과 diff check는 통과했다. 실제 Docker·SDK·Codex·model 호출은 0회다.
- Docker sandbox 밖 최초 smoke는 기존 pytest 공용 임시 상위 폴더의 ACL 접근 거부로 subject 시작 전에 실패했다. 코드나 Docker 실패로 합치지 않고 새 전용 `C:\lao-phase-f-smoke-r1-20260812` 경로와 cacheprovider 비활성화로 다시 실행했다.
- 실제 Docker reference smoke는 `1 passed in 27.65s`로 통과했다. client/server `29.6.2`, 고정 image digest 일치, container 17.843초, `CHECKS_PASSED`, reason code 없음, model turn 0이다. public manifest/result SHA-256은 각각 `5716516f...c126f`, `ed48d290...75157`, raw result self-hash는 `8d86e0ad...42208`이다.
- 상태는 `PHASE_F_PROFILE_R_DOCKER_JUDGE_SMOKE_PASSED`다. 다음은 live Worker의 J/S 접근 telemetry와 SDK runtime을 one-Cell finalizer에 model-free로 최종 조립하는 단계다. 그 뒤 실제 Cell 1 model 사용 승인을 다시 받는다.

## Phase F Profile R live stack 최종 dry-run과 0-turn preflight

- 작업일: 2026-08-12. Fake SS1 Worker→실제 고정 Docker Judge→Measurement→Cell seal 전체 경로를 저장소 밖 `C:\lao-phase-f-full-dry-run-r1-20260812`에서 실행해 `1 passed in 28.16s`를 확인했다. Fake의 최소 변경은 R-P02/R-P05 실패와 `scope_ok=false`였고, 시스템은 이를 `completed + independent_judge_failed`로 봉인했다. Cell 1만 `SEALED`, Cell 2~4는 `PLANNED`, model turn은 0이다.
- dry-run Measurement SHA-256은 `30102171...2765b`, Cell seal self-hash는 `1e283abc...1e068`, 외부 seal 파일 SHA-256은 `1457952c...689b5`다. 실패 결과가 Measurement와 seal을 관통하고 사라지지 않는 것을 확인했다.
- 실제 live 조립기 `realistic_phase_f_live.py`를 추가했다. runtime v2 permission profile은 root deny와 exact W write만 결합하고 network를 끈다. telemetry는 같은 policy hash에 묶인 W changed-file secret scan과 J/S 비노출 capability를 기록한다. 모든 OS open syscall을 관측했다고 과장하지 않는다.
- 이 과정에서 공통 API-key 이름 검사 함수가 임의 `Mapping`에서 값 조회를 시도할 수 있음을 발견했다. `source.keys()`만 순회하도록 바꾸고 값 접근 시 실패하는 회귀를 추가했다. 실제 preflight 직전 API-key 환경 변수 이름은 없었고 값은 읽지 않았다.
- 실제 사용자 인증 경계의 SDK 0-turn preflight를 `C:\lao-phase-f-sdk-preflight-r1-20260812`에서 실행해 `1 passed in 1.83s`를 확인했다. ChatGPT 인증, `gpt-5.6-sol`, `runtime-boundary-worker` allowed를 확인했고 thread/start·turn/start·model turn은 모두 0회다.
- 관련 최종 회귀는 `75 passed, 3 skipped`다. skip 3건은 opt-in 실제 실행이며 이번 작업에서 full Docker dry-run과 SDK preflight를 각각 별도 실행해 통과했다. 상태는 `PHASE_F_PROFILE_R_LIVE_STACK_PREFLIGHT_PASSED`이며 다음은 사용자 model-usage 승인 뒤 Profile R SS1 Cell 1 하나만 실제 실행하는 단계다.
## Phase F Profile R B1 Cell 2 최초 실행과 boundary hook 정정

- 작업일: 2026-08-12. 기존 Experiment `exp_20260812_77e111e8_1`에서 명시 승인된 Cell 2 `cell_phase-e_2_realistic-compat-migration-001_b1` 하나만 실행했다. ChatGPT 구독 인증, `gpt-5.6-sol`, reasoning effort `high`, SDK `0.144.4`, `runtime-boundary-worker`를 사용했고 API-key 환경 이름은 없었다. Cell 3은 자동 실행하지 않고 `PLANNED`로 남겼다.
- 실행 전 model-free 검증은 B1 전체 `74 passed`, Phase F 관련 `35 passed, 3 skipped`, 새 B1 관통 시험 `1 passed`였다. 실제 사용자 인증 경계의 B1 0-turn preflight도 session 0, model turn 0으로 통과했다.
- 최초 실제 Cell 2는 149.688초, model turn 1, token 합계 157,880에서 `blocked`로 봉인됐다. Worker는 R01의 두 공개 파일을 허용 범위 안에서 수정했지만 Check 실행 전 Controller boundary hook이 중단됐다. 독립 Docker Judge 결과는 `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE` 실패였다.
- 직접 원인은 새 boundary Evidence를 기존 SQLite 원장이 허용하지 않는 `kind=boundary_observation`, `producer=observer`로 등록한 것이다. 기존 동결 원장 Schema를 넓히지 않고 `kind=runtime_observation`, `producer=controller`를 재사용하도록 정정했고, 관통 시험에서 Attempt가 `RUNNING`으로 남지 않음을 추가 검증했다. 정정 뒤 B1 전체 `74 passed`, B1 Phase F 관통 `1 passed`, 구현 로그 `44 entries` 검사와 하네스 `10 tests`를 통과했다.
- 최초 실패 Cell 2와 seal은 삭제·수정·자동 재시도하지 않았다. 기록은 `DEV-20260812-001`에 남겼다. 정정 구현으로 실제 B1을 다시 측정하려면 one-shot 계약을 보존하는 별도 수동 revision을 먼저 정해야 한다.

## Phase F Profile R B1 수동 correction run과 검사 실행기 정정

- 작업일: 2026-08-12. 최초 Cell 2를 덮어쓰지 않고 동일한 sealed dispatch request로 로컬 correction root `C:\lao-phase-f-live-c36731c-r2`, `C:\lao-phase-f-live-c36731c-r3`를 각각 새로 만들었다. 두 실행 모두 Controller의 다음 Cell 자동 실행 경로를 사용하지 않았으므로 Cell 3은 실행되지 않았다.
- r2에서는 첫 Attempt Check 실패 뒤 두 번째 SDK thread를 열 때 concrete app-server port가 누적 transcript 전체의 `thread/started`를 세어 `DISPATCH_UNCERTAIN`으로 닫혔다. 요청 직전 transcript offset 이후의 새 frame만 검증하도록 수정했고, Phase F SDK/B1 표적 시험 `16 passed`와 실제 ChatGPT 인증 2-thread/0-turn preflight로 서로 다른 thread 2개와 model turn 0을 확인했다. 구현 인시던트는 `DEV-20260812-002`다.
- r3에서는 시스템 경계 오류 없이 B1이 새 session 2개, model turn 2개, Attempt 2개와 Check 재시도 1회를 실행했다. 총 217.344초, model active 194.162초, token 300,285였으며 R01에서 두 Check가 실패해 R02~R08은 실행하지 않았다. 최종 Cell seal은 `3169273c7e85333018a4e9bcda26f8cabcb6b64756c083a2592d9ef2574dd1c0`, Measurement hash는 `5ad90ced2e314402b52048afe396a93eaaf4978d6c2d018134ef001c7d1e68ce`다.
- r3의 두 Check stderr는 모두 `ModuleNotFoundError: No module named 'yaml'`이었다. Windows에서 bare `python` 실행 파일 검색이 자식에게 전달한 정제 PATH가 아니라 부모 검색 경로의 전역 Python을 선택한 것이 원인이었다. Check 실행 전에 bare `python`을 현재 B1의 `sys.executable`, bare `git`을 발견된 절대경로로 결합하고, Evidence에는 원래 선언 argv를 그대로 보존하도록 정정했다. 구현 인시던트는 `DEV-20260812-003`이다.
- 정정 뒤 B1 검증 표적 `7 passed`, B1 전체 `74 passed`를 통과했다. 실패한 r3 workspace 자체를 바꾸지 않고 같은 R01 Check만 model-free로 다시 실행해 exit 0과 `R01_PUBLIC_CONTRACT_OK`를 확인했다. 따라서 r3의 R01 Worker 결과는 공개 Check 기준으로 성공했지만 실행 당시 Controller 검사 환경 오류 때문에 실패로 기록된 것이다.
- r1·r2·r3는 모두 원본 상태로 보존한다. 다음 실제 model 실행은 새 correction root r4에서 해야 하며, 반복 비용과 one-shot 측정 계약 때문에 별도 사용자 승인을 받기 전에는 실행하지 않는다.

## Phase F Profile R B1 R4와 regular-file Artifact 계약 명시

- 작업일: 2026-08-12. 새 correction root `C:\lao-phase-f-live-c36731c-r4`에서 r1의 동일한 sealed Cell 2 request를 직접 실행했다. R01과 R02는 각각 첫 model turn과 공개 Check 2개를 통과해 `SUCCEEDED`로 닫혔다. R03은 initial+resume 2 turns 뒤 `artifact_corrupt`로 `BLOCKED`됐고 R04~R08은 실행하지 않았다.
- R4는 총 1,417.593초, model active 1,384.484초, session 3, turn 4, Attempt 3, token 3,028,785였다. Cell 3 자동 실행은 없었다. Measurement SHA-256은 `7a336fa7ba8a97e725ea9ded062f3bf61e139312d56f2784ea493b523b27a7cb`, Cell seal 파일 SHA-256은 `2e1e410f94f33faf2d51ce9a78db715a546f6d42222a35b5722e436498ca111b`다.
- R03 Worker는 허용 범위 안에 두 fixture tree와 manifest를 생성했지만 `ResultEnvelope.artifacts`에 두 directory path를 기록했다. B1 final verifier는 regular file만 hash할 수 있어 이를 missing Artifact로 분류했다. 봉인 뒤 동일 workspace에서 model turn 없이 `r03_contract`와 `git diff --check`를 다시 실행한 결과 둘 다 exit 0, `R03_PUBLIC_CONTRACT_OK`였다. 따라서 코드 결과와 보고 metadata 실패를 분리했다.
- 공개 Pydantic Schema의 `ResultArtifact.path` 설명과 Worker prompt에 “existing regular file만 허용하며 directory/glob은 금지, directory output은 concrete manifest/index file로 대표”를 명시했다. result parsing 직후 기존 directory를 발견하면 final blocking 전에 같은 session의 1회 resume로 정확한 교정 문구를 전달한다. missing path와 외부 경로에 대한 기존 final verifier는 유지했다.
- FakeRuntime 관통 시험은 첫 turn의 directory artifact가 `result_schema` 교정 feedback을 받고, 두 번째 turn의 실제 file artifact가 독립 Check를 통과해 동일 Attempt `resume_count=1`, Run `COMPLETED`로 끝나는 것을 확인했다. prompt·Schema·관통 표적은 `7 passed`, B1 전체는 `75 passed`다. 구현 인시던트는 `DEV-20260812-004`다.
- R4 원본과 seal은 수정하지 않는다. 다음 실제 실행은 별도 R5 root와 사용자 model-usage 승인 뒤에만 수행한다.

## Phase F Profile R B1 R5와 Python bytecode scope 정규화

- 작업일: 2026-08-12. 사용자 승인 뒤 새 correction root `C:\lao-phase-f-live-c36731c-r5`에서 동일한 sealed Cell 2 request 하나만 실행했다. 실행 전 실제 SDK 0-turn preflight는 `1 passed in 1.76s`였고 ChatGPT 인증만 사용했으며 API-key 환경 이름은 없었다. Cell 3은 자동 실행하지 않았다.
- R5는 총 1,154.484초, model active 1,118.530초, session 3, turn 3, Attempt 3, token 2,348,081이었다. R01과 R02는 첫 시도에 통과했고 R03에서 `scope_violation`으로 `BLOCKED`됐다. Measurement SHA-256은 `3a419164391ead7f718f96b9145ae19673ea1dd63bba137a3d014b5d93135588`, Cell seal 파일 SHA-256은 `9564a817233560c51d9c9d4cbb7a2c7bb9a0273e49316551035dceca0cba3643`다.
- R03 ResultEnvelope의 artifact 세 개는 모두 실제 regular file이었다. 따라서 R4에서 발견한 directory artifact 계약 오류는 해결된 상태로 관측됐다. 새 차단 원인은 Worker가 공개 checker를 Python으로 읽는 과정에서 자동 생성된 미추적 `benchmark_checks/__pycache__/check_profile_r.cpython-312.pyc` 하나를 B1이 허용 범위 밖 소스 변경으로 판정한 것이다.
- B1 scope 검사 전에 Git에 추적되지 않은 regular `__pycache__/*.pyc`만 삭제하고 changed paths를 다시 계산하도록 정정했다. tracked bytecode, symlink·junction을 통과하는 경로, 다른 확장자는 삭제하지 않는다. 같은 `__pycache__` 안의 `injected.txt`는 계속 scope 위반으로 차단한다.
- FakeRuntime 표적 시험은 자동 `.pyc` 정규화 성공과 일반 파일 차단을 각각 확인해 `2 passed`, B1 전체 회귀는 `77 passed`다. 정정 검증의 model·SDK·Codex·Docker·network 호출은 0회다. 구현 인시던트는 `DEV-20260812-005`다.
- R5 원본과 seal은 수정하지 않는다. 전체 R01~R08 완료 여부를 다시 측정하려면 새 R6 root와 별도 사용자 model-usage 승인이 필요하다.

## Phase F Profile R B1 R6와 R07 공개 회귀 실패

- 작업일: 2026-08-12. 사용자 승인 뒤 새 root `C:\lao-phase-f-live-c36731c-r6`에서 동일한 봉인 Cell 2 request 하나만 실행했다. 실행 전 실제 SDK 0-turn preflight는 `1 passed in 1.86s`였고 ChatGPT 구독 인증만 사용했으며 API-key 환경 이름은 없었다. Cell 3은 자동 실행하지 않았다.
- R6는 총 2,783.579초, model active 2,710.407초, session/turn/Attempt 8/8/8, token 11,136,599였다. R01~R06은 모두 첫 Attempt에 통과했다. R03도 첫 Attempt에 통과해 regular-file Artifact 계약과 `.pyc` 정규화가 실제 실행에서 작동함을 확인했다.
- R07은 공개 `r07_contract`가 두 Attempt 모두 exit 1을 반환해 첫 시도 `RETRYABLE_FAILED`, 두 번째 시도 `FAILED`로 닫혔다. R08과 Cell 3은 실행되지 않았다. Worker 실패 때문에 Docker Judge는 실행되지 않았고 최종 실패 Cell은 정상 봉인됐다. Measurement SHA-256은 `68887d828e085a0ea81de5a271a813c13793d8a3c1e7fed58c0881bdb7056921`, sealed artifact SHA-256은 `fd4a7222d36390172837641b39188b2e268f0a38cc1744c36a931c21bf76dbb4`다.
- 실패 workspace를 수정하지 않고 B1 전용 Python으로 R07 test file을 model-free 재실행한 결과 `3 passed, 1 failed`였다. 실패한 `test_s2_fake_four_cell_plan_judge_property_seal_export`는 S2 전용 manifest의 `stage_id`, `purpose`, `initial_cell_order`와 fixture `profile`을 extra field를 금지하는 구형 `FrozenManifest` 입력에 그대로 넣었다. 직접 원인은 Worker가 만든 test fixture 변환 오류이며 시스템 Python 의존성 부족으로 분류하지 않는다.
- 공개 checker가 내부 pytest 원인을 버리고 `R07_PUBLIC_CONTRACT_FAILED` 한 줄만 출력해 B1의 한 번짜리 재시도가 조치 가능한 이유를 받지 못한 문제도 관측했다. 다음 수정은 model-free로 manifest 입력 경계를 바로잡고, 숨은 Judge 정보를 노출하지 않는 public bounded feedback을 확인·교정한 뒤 회귀를 통과시키는 것이다. 실제 R7은 별도 사용자 승인 전 실행하지 않는다.

## R6 뒤 회사→집 exact-tree 인수인계

- 작업일: 2026-08-12. 최신 회사→집 정본을 `docs/operations/company-to-home-codex-handoff.md` revision 4로 갱신하고, 같은 집 Codex 작업에 전달할 시작 프롬프트를 `docs/prompts/benchmark-runner/home-codex-resume-after-company-phase-d-profile-r.md`에 교체했다.
- 집의 다음 필수 작업은 `codex/phase-d-artifacts` 최신 tip으로 ff-only 동기화한 뒤 R07 test fixture와 공개 Check feedback을 model-free로 최소 교정하고 표적·관련 회귀, 로그, commit·push까지 끝내는 것이다. P001~P015는 이미 tracked 정본이므로 다시 수집하지 않는다.
- 회사 R1~R6 raw root, `.venv`, Docker local image와 로그인 상태는 Git 동기화 대상이 아니다. R6 결과와 hash는 인수 문서와 이 로그에 보존했다. 실제 model/SDK turn, R7 재실행과 Cell 3은 계속 별도 사용자 승인 대상이다.

## Phase F Profile R B1 R07 공개 회귀와 재시도 피드백 교정

- 작업일: 2026-08-12. 집 저장소를 `codex/phase-d-artifacts` 원격 tip `010a4246ea86bad380a11357b3663ca2e837864d`로 ff-only 동기화한 뒤, 봉인된 R6 원본과 P001~P015 정본은 수정하지 않고 R07 문제만 model-free로 재현했다. strict Pydantic 입력은 fixture `profile`과 S2 전용 `stage_id`, `purpose`, `initial_cell_order` 네 종류를 `extra_forbidden`으로 거부했다.
- 기준 reference 시험은 이미 `FrozenManifest`와 `FrozenFixtureSpec`의 선언 필드만 사용한다. 실제 실패는 R6 Worker가 새로 만든 test helper의 변환 오류였다. 새 R07 공개 goal에 strict model 선언 필드만 사용하고 S2 stage/profile dict를 전달하지 말라는 경계를 명시했다. production Pydantic model과 R07의 네 필수 시험, assertion은 완화하지 않았다.
- 보호된 public checker는 알려진 pytest failure를 공개 정보만으로 분류해 `WORKER_FEEDBACK:` 한 줄을 최대 1,600자로 출력한다. B1은 이 명시 marker만 읽고 전체 UTF-8 2,048-byte로 자른 뒤 failed Attempt에 보존하며, 다음 Attempt의 첫 turn에 allowed write scope와 남은 criteria를 함께 전달한다. unmarked stdout/stderr와 Judge/reference/negative-mutation 정보는 전달하지 않는다.
- Windows subprocess의 비 UTF-8 출력 때문에 public checker reader가 중단되는 model-free 관통 오류도 발견했다. checker는 `errors="replace"`로 디코딩하고 누락 stream을 빈 값으로 취급하도록 fail-closed 교정했다. 새 short reference workspace에서 최종 `R07_PUBLIC_CONTRACT_OK`를 확인했다.
- Profile R source bundle의 기존 manifest가 LF Git blob 대신 과거 CRLF working bytes의 크기/hash를 보존한 불일치도 회귀에서 드러났다. 이 PC에서 끊어진 `.venv`의 Python 3.12 경로만 로컬 bundled 3.12로 복구하고 정본 builder를 재실행했다. 최초 의존성 없는 builder 결과 `CHALLENGE_NOT_READY`는 통과 근거에서 제외했으며, 최종 bundle은 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`, payload aggregate `4bb6e9f81bb67215eb28975dfeef236d09d76e6795b1f46a6c90acbd7df4fcd6`다.
- 최종 model-free 검증은 routing S2와 Profile R fixture `30 passed`, B1 전체 `79 passed`, Phase F B1/finalizer/live 관련 `8 passed, 2 skipped`다. Phase F의 최초 세 실패는 Windows 긴 temp path에서 `git add`가 거부된 환경 실패였고 fresh `C:\lao-tests` root에서 세 시험 모두 통과했다. 실제 model, SDK, Codex, Docker, network 호출은 0회다. 구현 incident는 `DEV-20260812-006`이다.
- R6 실패 seal은 그대로 유지한다. 이번 교정으로 Worker/Judge source hash가 과거 Phase E candidate와 Docker qualification의 바이트에서 달라졌으므로, 기존 후보를 새 R7 근거로 재사용하지 않는다. 새 source에 대한 필요한 qualification과 model-free Phase E candidate 재동결, 별도 사용자 model 승인 전 실제 R7과 Cell 3은 계속 `NO-GO`다.

## R07 교정 source의 Profile R Docker Judge 재자격

- 작업일: 2026-08-12. 과거 v1 qualification과 image 기록을 수정하지 않고, 집 PC의 동일 Dockerfile·dependency lock image를 새 digest `5610c2a6...6ad89`로 고정했다. image package 17개는 lock과 일치했고 Docker Engine은 `29.6.2`, Linux `x86_64`였다.
- source commit `fd3d146097fe8c0cd41fc1e4a98ac32dd84ab223`에서 fresh root `C:\lao-r07-q2-20260812`를 사용해 reference 1개와 negative mutation 8개를 210.8초 실행했다. reference R-P01~R-P08은 8/8 pass, mutation은 각 target failure와 정확히 일치해 matrix는 `CHALLENGE_READY`, model turn 0으로 닫혔다.
- 별도 process verifier가 9 cells와 47-file seal을 다시 계산했다. manifest self-hash는 `e16ab3d5...5aa27`, result는 `eac5a911...56f8a`, seal은 `9577dd5b...e6e1a`이며 잔여 container는 0개다. 공개 projection은 `profile-r-docker-judge-qualification-v2`에 보존하고 stage의 Profile R 입력을 v2로 전환한다.
- 첫 단위시험은 공용 pytest temp root의 `WinError 5` 때문에 11개 setup error가 났고 6개만 통과했다. fresh 전용 basetemp에서 같은 시험은 `17 passed`였다. 환경 실패를 qualification 성공에 합치지 않았다.
- 다음 관문은 이 v2 qualification과 기존 Profile I qualification을 결합한 새 model-free Phase E candidate 동결이다. 실제 R7, Cell 3, model turn은 여전히 별도 사용자 승인 전 `NO-GO`다.

## R07 교정 뒤 Phase E v2 0-turn 후보 동결

- 작업일: 2026-08-12. source commit `ca7cd1e29d52d71385e73b9c8607efad7fa87174`에서 Profile R qualification v2와 기존 Profile I qualification v1을 결합해 새 Phase E 후보를 만들었다. 4-Cell 순서 R SS1→R B1→I B1→I SS1, 모델·reasoning·budget·one-cell confirmation 계약은 유지했다.
- current checkout의 ignored pytest cache 경고를 후보 근거에서 배제하기 위해 fresh short worktree에서 생성했다. ChatGPT 구독, SDK `0.144.4`, `gpt-5.6-sol` 가시성을 0-turn으로 확인했고 API-key 환경 이름, thread/start, turn/start, model turn은 모두 0이었다.
- 최종 experiment는 `exp_20260812_bd0b7fe5_1`, Plan fingerprint는 `bd0b7fe5...57c02`, files manifest는 `50b74e9a...3fa04`, candidate seal은 `59d059aa...0efde`다. 별도 process verifier가 exact 6-file set과 source/qualification/runtime binding을 다시 계산해 같은 결과를 냈다.
- 직전 pytest temp가 남은 current checkout에서 처음 생성한 후보는 clean-source 근거로 사용하지 않고 삭제했다. 최종 후보만 `sdk-routing-realistic-high-difficulty-phase-e-v2`에 보존한다. checked-in v2 candidate verifier를 포함한 관련 회귀는 clean record commit에서 `22 passed`다.
- 상태는 `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`이다. 실제 R7 또는 Cell 3, model turn은 이번 작업에서 실행하지 않았고 별도 사용자 승인 전 계속 `NO-GO`다.

## Phase F Profile R B1 R7과 S2 project-pack fixture 결손

- 작업일: 2026-08-12. 사용자 승인 뒤 새 root `C:\lao-phase-f-live-bd0b7fe5-r7`에서 v2 Experiment의 Profile R B1 Cell 2 하나만 실행했다. 실제 SDK 0-turn preflight는 ChatGPT 구독, `gpt-5.6-sol`, SDK `0.144.4`, `runtime-boundary-worker`를 확인했고 API-key 환경 이름과 thread/model turn은 0이었다. Cell 3은 실행하지 않았다.
- R01~R06은 첫 Attempt에 성공했다. R07 첫 공개 Check 실패 뒤 새 feedback 경로로 test 이름이 전달돼 두 번째 Attempt가 실행됐지만 같은 test가 실패했다. R08은 미실행이다. 총 session/turn/Attempt는 8/8/8, 공개 Check는 12 pass/2 fail, token은 11,675,629, sealed total wall은 2,823.687초다.
- 봉인 뒤 같은 workspace의 실패 test 하나를 model-free로 재실행했다. 첫 S2 B1 Cell preflight가 구형 `.orchestrator/project.yaml` 때문에 중단됐다. fixture에는 현재 B1이 요구하는 `core_compat`, `repository_root`, `default_capability_profile`, `default_policy`가 없고 구형 `purpose`, `requirements`, `task_order`가 있어 strict `ProjectConfig`가 거부했다.
- 따라서 R7 실패는 R07 기능 구현의 직접 실패가 아니라 공개 S2 test helper의 B1 project-pack fixture 변환 결손이다. feedback 통로는 작동했지만 test 이름만 전달해 실제 validation 원인이 두 번째 Worker에게 가지 않은 문제도 남았다.
- Docker Judge는 R-P05/R-P06 실패를 검출했고 Measurement는 `failed`, `scope_ok=false`로 봉인됐다. Cell seal file SHA는 `a2d1a35e...ac3ee`, Measurement는 `442d0f47...ea86`, self seal은 `17f39aa1...5dbc`다. 독립 finalization verifier는 통과했고 잔여 container는 0이다.
- R7 raw와 seal은 수정·삭제·자동 재시도하지 않는다. 다음은 model-free fixture/helper와 bounded assertion feedback 최소 교정이다. 회귀와 qualification/candidate 영향 판단 전 R8 model 실행과 Cell 3은 `NO-GO`다.

## R7 뒤 집→회사 exact-tree 인수인계

- 작업일: 2026-08-12. 오늘 집 작업의 Git 정본은 `codex/phase-d-artifacts`의 R7 결과 commit `7894c7daf3eae72568e0992002e034a8160530e2`까지다. 현재 집→회사 정본을 `docs/operations/home-to-company-codex-handoff.md` revision 5로 교체했다.
- 인수 문서는 R07 공개 회귀와 bounded feedback 교정, 집 Docker Judge 재자격, Phase E v2 0-turn 후보, 실제 R7 한 번의 봉인 결과와 model-free 사후 진단을 하나의 계보로 묶는다. 집 Docker image와 raw qualification/R7 root는 로컬 전용이고 Git 동기화 대상이 아님을 분리했다.
- 회사의 다음 작업은 실제 model 실행이 아니라 공개 S2 test helper가 복사하는 legacy `.orchestrator/project.yaml`을 현재 B1 `ProjectConfig` 형식으로 canonicalize하고, `B1 run validate failed`의 공개 원인을 bounded feedback으로 전달하는 model-free 최소 수정이다. production validation과 필수 assertion은 완화하지 않는다.
- 관련 R07/S2, B1 전체, Phase F model-free 회귀와 incident/revision 기록, commit·push 뒤 멈춘다. source 변경으로 기존 qualification/candidate가 stale해지는지만 보고하며 Docker 재자격, 후보 재생성, R8, Cell 3과 다른 model turn은 별도 사용자 승인 전 `NO-GO`다.

## Phase F Profile R R07 legacy project-pack model-free 교정

- 작업일: 2026-08-13. 회사 clone을 `origin/codex/phase-d-artifacts`의 `ee877eb2e947e1d2af4d36f845166a358aad8927`로 ff-only 동기화했다. 시작 전 dirty file, stash, local-only commit과 incoming tracked path/ignored file 충돌은 없었고 local/remote tree `a96799f8b4f32046b162d9cd5ecf1018a0e12ce7`가 일치했다.
- R7 사후 진단의 exact gap을 model-free 회귀로 고정했다. S2 test helper는 legacy `project.yaml`의 `purpose`, `requirements`, `task_order`를 실제로 만든 뒤 fixture source를 commit하기 전에 공개 capabilities/policies에서 `default_capability_profile`과 `default_policy`를 선택하고 현재 strict `ProjectConfig`의 여섯 필드로 canonicalize한다. production `ProjectConfig`와 B1 preflight는 변경하거나 완화하지 않았다.
- 보호 checker는 정확히 `test_s2_fake_four_cell_plan_judge_property_seal_export`의 `b1 preflight failed: B1 run validate failed`가 관측된 경우에만 누락된 현재 필드와 금지된 legacy 필드를 bounded `WORKER_FEEDBACK`으로 반환한다. 전체 traceback, Judge, reference와 mutation 정보는 전달하지 않는다. R07 goal/criterion과 Worker snapshot 130-file manifest도 결정론적으로 갱신했다.
- exact 회귀 3개는 통과했다. B1 전체는 `79 passed`, Phase F B1/finalizer/live model-free 묶음은 `8 passed, 2 skipped`였다. skip 2개는 실제 Docker dry-run과 실제 SDK preflight opt-in이므로 실행하지 않았다. R07/S2·Profile R fixture 묶음은 `30 passed, 1 failed`였고, 유일한 실패는 기존 회사 checkout의 Judge bundle manifest LF 크기 1,485 bytes와 working-tree CRLF 1,537 bytes 불일치다. 이번 변경 파일이나 R07 동작 실패로 분류하지 않고 qualification/줄바꿈 정본을 자동 수정하지 않았다.
- 구현 인시던트는 `DEV-20260812-007`로 기록했다. 실제 model, SDK thread, Codex process, Docker와 network 호출은 모두 0회다. R7 raw/seal, P001~P015와 기존 qualification/candidate는 수정하지 않았다.
- Worker 공개 source와 snapshot hash가 바뀌었으므로 Profile R Docker qualification v2와 이를 참조하는 Phase E v2 candidate는 새 실행 근거로 사용할 수 없는 `stale` 상태다. Profile I qualification은 영향받지 않는다. Docker 재자격과 Phase E 후보 재생성, 실제 R8/Cell 3/model turn은 사용자 별도 승인 전 수행하지 않는다.

## 회사 PC Profile R Docker 재자격 v3와 Phase E v3 후보 동결

- 작업일은 2026-08-13이다. 사용자의 후속 승인으로 stale 상태였던 Profile R qualification과 Phase E 후보를 새 revision으로 다시 만들었다. 과거 v2 artifact와 R7 raw/seal은 수정하지 않았다.
- 집 PC image digest `5610c2a6...6ad89`는 회사 PC에 없고 원격 registry에서도 받을 수 없었다. 동일 Dockerfile, requirements lock, base image를 `--provenance=false`로 빌드한 회사 image digest `ba83a183...330ab`를 commit `0e6b87a`에서 고정했다.
- 첫 재자격 준비는 긴 `%LOCALAPPDATA%` root에서 Windows path-length 오류로 Docker 실행 전에 중단됐다. 짧은 `C:\lao-r07-q3-20260813`에서 실행한 9개는 기능 결과는 전부 예상과 일치했지만, 공개 checker 변경 때문에 사전등록 workspace hash가 옛값이라 `CHALLENGE_NOT_READY`였다. 봉인된 before/after hash만 evidence에 재결합하고 commit `f401110`으로 고정했다.
- 최종 `C:\lao-r07-q4-20260813` batch `profile-r-docker-matrix-r07-company-v4`는 reference 8/8 pass와 mutation 8개 목표 실패가 모두 일치해 `9/9 matched`, `CHALLENGE_READY`로 닫혔다. manifest는 `8f71be5e...2146e`, result는 `8e7b3711...3dbd8`, seal은 `22a81ac5...781`이며 model·SDK thread·Codex turn은 0이다. projection은 `profile-r-docker-judge-qualification-v3`에 보존했다.
- qualification v3와 stage binding을 commit `608044d`로 고정한 뒤 ChatGPT account와 `gpt-5.6-sol` 노출만 SDK `0.144.4`로 확인하고 Phase E v3 0-turn 후보를 만들었다. thread/start와 turn/start는 0회다. experiment는 `exp_20260812_4053943d_1`, Plan fingerprint는 `4053943d...ada2`, candidate seal은 `2c66604e...4538`이다.
- 기존 v2 qualification과 candidate는 과거 기록으로 보존된다. 새 실행 입력은 v3이며, 실제 Profile R B1 correction Cell은 사용자 별도 승인 전 실행하지 않는다. Cell 3 자동 진행은 계속 금지다.
- 재자격 첫 호출 하나는 존재하지 않는 수기 source hash를 넘겨 Git object 확인 단계에서 중단됐고 Docker는 실행되지 않았다. 다음 긴-root 호출도 patch precheck의 Windows path-length 오류로 Docker 전에 중단됐다. 원인 확인 뒤 source나 patch를 완화하지 않고 짧은 새 root를 사용했다.
- 최종 관련 model-free 회귀는 Docker Judge, Phase E, Phase F Docker/B1/finalizer/live 묶음에서 `34 passed, 3 skipped`다. skip은 명시적 opt-in이 필요한 Docker smoke, full Docker dry-run, SDK preflight이며 자동 실행하지 않았다.

## Phase F Profile R B1 R8 회사 v3 실제 실행

- 작업일은 2026-08-13이다. 사용자 승인 뒤 Phase E v3의 Profile R B1 Cell 2 하나만 fresh root `C:\lao-phase-f-live-4053943d-r8`에서 실행했다. 실행 전 SDK 0-turn preflight는 ChatGPT 구독, `gpt-5.6-sol`, SDK `0.144.4`, `runtime-boundary-worker`를 확인했고 API-key 환경 이름, thread와 model turn은 0이었다.
- R01~R06은 첫 Attempt에 성공했다. R07 첫 Attempt는 공개 test 두 개의 `ERROR`로 `check_failed`가 됐고 bounded `WORKER_FEEDBACK`을 받은 두 번째 Attempt도 같은 두 test에서 실패했다. R07은 `FAILED`, R08은 `PENDING`으로 끝났고 Cell 3은 실행하지 않았다.
- 총 session/turn/Attempt는 8/8/8, retry는 1, 공개 Check는 12 pass/2 fail이다. model active는 3,003.537초, B1 wall은 3,055.683초, sealed total wall은 3,076.000초다. token은 input 15,103,169, output 114,030, total 15,217,199로 측정됐다. 한 번의 실패 Cell 수치이므로 일반 효율이나 variant 우열로 확대하지 않는다.
- 독립 Docker Judge는 R-P01~R-P04를 통과시키고 R-P05-LIFECYCLE-REUSE와 R-P06-EXPORT-ROUNDTRIP을 실패로 판정했다. R-P07/R-P08은 선행 조건 때문에 blocked됐다. 최종 Measurement는 `failed / b1_failed / check_success=false`, integrity `scope_ok=true`로 봉인됐다.
- Cell seal file SHA는 `3f46bea3...fef`, Measurement는 `4cf05079...e9e`, Judge public result는 `0b7d50b6...69d`, adapter evidence는 `068432f9...523`이다. 독립 finalization verifier는 통과했고 Cell 3 경로와 잔여 Docker container는 0개였다.
- bounded feedback 통로는 동작했지만 이번에는 pytest node ID와 exit code만 전달했다. Worker Python에는 pytest와 project dependencies가 없어 setup error의 구체 원인을 자체 확인하지 못했다. 이 관측은 열린 incident `DEV-20260813-001`에 기록한다.
- R8 raw와 seal은 수정·삭제·재봉인·자동 재시도하지 않는다. 다음은 별도 사용자 승인 아래 R8 workspace와 공개 Check를 model-free로 분석하는 단계다. R9, Cell 3과 다른 model turn은 계속 `NO-GO`다.

## R8 R07 공개 시험의 Windows path·Fake effect 원인 교정

- 작업일은 2026-08-13이다. sealed R8 workspace와 raw/seal은 수정하지 않고 실패한 공개 pytest node 두 개를 Python 3.12에서 model-free로 다시 실행했다. 두 node 모두 `git show`의 `Filename too long`에서 먼저 실패했다. `core.longpaths=true`를 같은 subprocess에 강제하자 project-pack canonicalization node는 통과했다.
- 긴 경로 결손 뒤에는 별도 4-Cell fixture 문제가 드러났다. R8 Worker가 만든 Fake adapter가 Task별 golden 파일을 쓰지 않고 빈 effects와 completed envelope만 반환해 config C2와 두 B1 Cell이 실패했다. 현재 정본에 있던 `GOLDEN_ROOT/_golden_turns`와 explicit C2/B1 file effects를 R07 goal의 보존 조건으로 고정했다.
- `routing_suite._git`은 매 호출에 `-c core.longpaths=true`를 전달한다. 공개 feedback은 `Filename too long`과 Fake 결과 파일 미생성을 각각 bounded 공개 문구로 분류한다. production B1 validation, Judge, 필수 assertion과 reference/mutation 경계는 완화하지 않았다.
- 정본 builder로 Worker snapshot을 130 files, aggregate `5e87ebb4b762b5e0c0d988505dc1828c69f542dd94a3ed75d66e40aa422393b4`로 갱신했다. Profile R Judge source bundle도 32 files, aggregate `24baf48f6ecb1ceac21ad4adb8cd26809d6f89e3f94792121389cde14203201d`, `PROFILE_R_SOURCE_BUNDLE_VERIFIED`로 재생성했다.
- 최종 검증은 R07/S2·Profile R·legacy S1 `38 passed`, B1 전체 `79 passed`, Phase F B1/finalizer/live `8 passed, 2 skipped`다. skip은 명시적 Docker/SDK opt-in이고 실행하지 않았다. model, SDK thread, Codex, Docker, network 호출은 0회다. incident `DEV-20260813-001`을 resolved로 닫았다.
- source와 Worker/Judge bundle bytes가 바뀌어 Profile R qualification v3와 Phase E v3 candidate는 R9 입력으로 stale하다. 다음은 별도 승인 아래 새 qualification과 0-turn candidate를 만든 뒤 R9 Cell 2를 결정하는 것이다. Cell 3 자동 진행은 계속 금지다.

## Profile R Docker Judge 재자격 v4와 독립 감사 관문

- 작업일은 2026-08-13이다. source commit `dd84c9b4665940a63f64923485c8c55ed353b8ef`의 Profile R 공개 입력을 기존 회사 Docker image `ba83a183...330ab`에서 다시 검사했다.
- 공식 v5 batch는 reference 8/8 pass와 negative mutation 8개의 목표 실패가 모두 일치해 `9/9`, `CHALLENGE_READY`였다. manifest `7612c0b9...6984`, result `88c54498...ff8e`, seal `07377e76...4413`이며 별도 verifier가 같은 결과를 재계산했다.
- 첫 호출의 제어 도구 timeout 뒤 실제 process가 계속 실행 중인 것을 늦게 확인해 v6를 중복 실행했다. v6도 raw seal과 `9/9`를 완성했지만 v5가 먼저 projection을 생성해 v6의 projection 쓰기는 fresh-output 규칙으로 거부됐다. v6를 공식 qualification이나 추가 표본으로 사용하지 않고 두 raw root를 모두 보존했다.
- v4 projection을 새 artifact로 추가하고 stage의 Profile R qualification 경로를 v4로 전환했다. 기존 v1~v3 qualification과 Phase E 후보, R1~R8 raw/seal, Profile I 및 P001~P015는 수정하지 않았다.
- 이 시점까지 실제 model, SDK thread와 Codex turn은 0회다. R7·R8에서 시험환경 결손을 실제 model 실행 중에 발견한 절차상 문제를 인정하고, 다음 관문을 `현재 동결 환경의 독립 AI model-free end-to-end 감사 → 차단 오류 한 차례 교정 → 동일 범위 재감사 한 차례`로 고정했다. 새 기능·위협모델 확대나 반복 감사는 허용하지 않는다.

## Profile R R9 전 Daybreak Blue 독립 감사와 재감사

- qualification v4와 stage binding을 commit `44341acfded453ab71cbfa654bd7ad91a3ad46be`로 먼저 고정했다. 관련 Docker Judge/matrix/Phase E 표적 시험은 clean commit에서 `23 passed`였다.
- 첫 `gpt-daybreak-blue-latest` clean-room 감사자는 지정된 routing S2, Profile R fixture, Docker Judge/matrix, Phase E, Phase F B1/finalizer/live model-free 묶음을 실행해 `62 passed, 0 failed, 2 skipped` (`132.70s`)와 `GO`를 보고했다. 첫 120초 도구 대기 제한 중단은 같은 명령의 실패 출력 없이 발생했고, 600초 제한 최종 실행만 판정 근거로 사용했다.
- 첫 결과를 전달받지 않은 두 번째 Daybreak Blue 감사자도 같은 commit과 범위를 실행해 `62 passed, 0 failed, 2 skipped` (`130.05s`)와 `GO`를 냈다. 두 번 모두 시작·종료 tree는 clean이었다.
- 두 감사가 확인한 경로는 작업 준비·fixture/manifest, canonical ProjectConfig와 B1 preflight, Fake worker 결과, 공개 Check/Judge, Phase E 생성·검증, Phase F Measurement/seal/finalization이다. skip은 실제 Docker full dry-run과 실제 SDK zero-turn preflight opt-in이다.
- 재현 가능한 R9 차단 결함이 0건이므로 production 수정과 새 테스트 작성은 0건으로 종료했다. 실제 model, SDK thread/turn, Codex process/CLI, Docker와 network 호출도 0회다. 다음은 새 Phase E 0-turn 후보 동결이며 실제 R9 Cell 2는 별도 사용자 승인 전 실행하지 않는다.

## 독립 감사 통과 뒤 Phase E v4 0-turn 후보 동결

- clean source commit `5a6790a69891ec4e48326bcfbab82306496f9d99`에서 기존 v1~v3 후보를 덮지 않고 `sdk-routing-realistic-high-difficulty-phase-e-v4`를 새로 만들었다.
- API-key 환경 이름은 없었다. 로그인된 ChatGPT 구독과 SDK `0.144.4`, `gpt-5.6-sol` 노출을 account/model-list 사전점검으로 확인했다. thread/start, turn/start와 actual model turn은 0회다.
- experiment는 `exp_20260813_44b11b86_1`, Plan fingerprint는 `44b11b86...68c3c`, files manifest는 `9c531bd6...c524`, candidate seal은 `2fefd981...ce7d`다. 별도 verifier가 exact 6-file set, source commit/tree, stage, Profile R qualification v4와 Profile I qualification v1, runtime-boundary binding과 모든 payload hash를 재계산해 통과했다.
- 후보는 4-Cell 순서 R SS1→R B1→I B1→I SS1, initial/ceiling turn 32/40, one-cell confirmation과 automatic continuation 금지 계약을 유지한다.
- 이 작업은 실제 R9이나 Cell 3을 실행하지 않았다. 다음 관문은 별도 사용자 승인 아래 Profile R B1 Cell 2 하나를 R9으로 실행하고 성공·실패 뒤 실험 실행을 종료하는 것이다. 자동 R10 반복은 하지 않는다.

## Phase F Profile R B1 R9 회사 v4 실제 실행과 실험 종료

- 작업일은 2026-08-13이다. 사용자 승인 뒤 Phase E v4의 Profile R B1 Cell 2 하나를 fresh root `C:\lao-phase-f-live-44b11b86-r9`에서 exactly once로 실행했다. 실행 전 SDK 0-turn preflight는 ChatGPT 구독, `gpt-5.6-sol`, SDK `0.144.4`, `runtime-boundary-worker`를 확인했고 API-key 환경 이름, thread와 model turn은 0이었다. request SHA-256은 `942493968e37cb0d18362461bc83299fb8d9d1d1b3821156bb4c9975b7338075`이며 `automatic_continuation=false`였다.
- R01~R06은 첫 Attempt에 성공했다. R07 첫 Attempt는 공개 pytest node 두 개의 `ERROR`로 `RETRYABLE_FAILED`가 됐고 bounded feedback 뒤 두 번째 Attempt도 같은 node에서 실패했다. R07은 `FAILED`, R08은 `PENDING`으로 끝났다. 총 session/turn/Attempt는 8/8/8, retry는 1, 공개 Check는 12 pass/2 fail, token은 input 22,291,455, output 154,160, total 22,445,615였다. sealed total wall은 3,472.000초다.
- 독립 Docker Judge는 R-P01~P04, P06, P07을 통과시키고 R-P05 `DUPLICATE_OR_MISSING_LIFECYCLE`, R-P08 `OPERATOR_CONTRACT_DRIFT`를 실패로 판정했다. Measurement는 `failed / b1_failed / check_success=false`, `scope_ok=true`, Evidence hash 정상, secret finding 없음으로 봉인됐다. 공개 feedback에는 pytest traceback이 없으므로 두 `ERROR`의 더 좁은 예외 원인은 미확인으로 남긴다.
- Measurement SHA-256은 `4ed937aa2e9dc9fafc4946bdd18cca557b4e8d2d64ec3c49db146a6d6707a7de`, Cell seal file SHA-256은 `edad83081a80289e5c6eaf26b58094890c66f11f9ba0ee0e7edd216e740c90f8`다. 별도 Python 3.12 process의 finalization verifier가 통과했고 종료 뒤 Docker container는 0개, backend Cell 디렉터리는 Cell 2 하나였다. Cell 3은 실행하지 않았다.
- 사전 합의한 종료선에 따라 성공·실패와 무관하게 R9에서 실험 실행을 종료한다. R10과 Cell 3은 실행하지 않는다. R9 raw/seal은 수정·삭제·재봉인하지 않는다. 이 단일 실패를 B1의 일반 효용이나 다른 variant와의 우열로 확대하지 않는다.

## B1 Phase F 최종 판정과 개발 방향 전환

- R7~R9의 봉인 결과와 현실 난이도 비교 명세의 route 술어를 대조했다. B1의 Task 순차 실행, 독립 Check, bounded retry, 실패 뒤 downstream 차단, Judge·Measurement·seal·별도 verifier는 실제 작동했으므로 `B1_MECHANICS_VERIFIED`다.
- SS1 대조 Cell과 독립 두 번째 snapshot이 없고 해석 가능한 R9 B1도 성공하지 못했으므로 route 판정은 `ROUTING_INCONCLUSIVE`다. `ADOPT_B1`, `REJECT_B1_PROFILE`, `ROUTE_B1_PROVISIONAL`, `INSTANCE_SS1_ADVANTAGE_OBSERVED`를 발행하지 않는다.
- R7~R9의 실제 운영 합계는 model turn 24회, token 49,338,443, sealed wall 9,371.687초다. source revision과 환경 상태가 달라 성능 통계로 합치지 않지만, 같은 synthetic benchmark의 반복 교정 비용이 크다는 운영 경고로 보존한다.
- B1은 폐기하지 않고 검증된 안전 실행 기반으로 보존한다. 기본 route로는 채택하지 않으며 단순 실행을 fallback으로 둔다. Task 의존·독립 검사·실패 차단이 필요한 실제 작업에만 선택적으로 적용한다.
- R10과 Cell 3을 포함한 Phase F 추가 실행은 종료했다. 다음은 새 benchmark가 아니라 현재 branch를 정본에 통합할 범위와 실제 프로젝트 1개에서 자연 사용 telemetry를 수집할 최소 오케스트레이터 범위를 정하는 것이다. B2·B3는 B1의 검증·복구가 실제 최종 성공을 만든 자료가 생기기 전까지 보류한다.

## R9에서 확인된 B1 공개 Check 재시도 정보 전달 결함 교정

- R9의 R07 두 Check artifact를 다시 대조해, B1이 재시도 Worker에게 공개 pytest node 두 개와 exit code만 전달하고 traceback·예외 문장을 전달하지 않았음을 구현 결함으로 확정했다. R08 차단은 정상 동작이지만 자동 교정 경로는 검증되지 않은 상태로 재분류했다.
- B1은 `WORKER_FEEDBACK:`가 붙은 공개 진단만 통과시키는 경계를 유지하면서 한도를 16 KiB로 늘리고, 여러 줄과 들여쓰기, 전송 byte 수, 잘림 여부를 `resume_feedback`에 보존한다. Profile R 공개 checker는 재실행 명령, 공개 원인 힌트와 pytest stdout/stderr를 12 KiB head-tail 진단으로 내보낸다. 숨은 Judge 출력은 계속 전달하지 않는다.
- 검증 결과는 B1 표적 `31 passed`, Profile R fixture `13 passed`, B1 전체 `79 passed`, 관련 Phase F model-free `13 passed, 2 skipped`다. skip은 실제 Docker와 SDK opt-in이며 model·SDK·Codex·Docker 호출은 0회다. incident는 `DEV-20260813-002`에 기록했다.
- Worker 공개 overlay와 snapshot hash가 바뀌어 기존 Profile R qualification v4와 Phase E v4 candidate는 새 live 실행 입력으로 stale하다. R9 raw/seal은 과거 사실로 보존하며 자동 R10·Cell 3·재자격·후보 재생성은 하지 않았다.
- 공식 표현은 `B1_CONTROL_FLOW_VERIFIED / B1_REPAIR_UNVERIFIED / ROUTING_INCONCLUSIVE`로 좁힌다. B2·B3는 B1 우월성의 보상이 아니라 원래 목표인 병렬 실행과 Brain 합성을 별도로 검증할 후속 단계다.

## 현재 source의 SS1 → B1 model-free 연속 실행 점검

- 같은 Phase F 상태에서 Cell 1 SS1과 Cell 2 B1을 실제 model 없이 순서대로 실행하는 회귀를 추가했다. SS1은 Fake SDK thread 하나에서 R01~R08 여덟 Task를 처리하고, 별도 명시 dispatch 전에는 B1 artifact가 생성되지 않는다.
- 두 번째 명시 dispatch 뒤 B1이 실행되고 SS1과 B1 각각 Fake Judge·Measurement·Cell seal을 만든다. 종료 뒤 상태는 Cell 1·2 `SEALED`, Cell 3·4 `PLANNED`이며 Cell 3 claim과 artifact는 없다.
- 새 연결 시험은 `1 passed`, SS1·B1 관련 파일 묶음은 `7 passed`다. model, SDK, Codex, Docker 호출은 0회다. 이는 실행 통로 점검이며 SS1/B1의 품질·시간·비용 우열 근거가 아니다.

## B1 공개 traceback 변경 뒤 Profile R Docker 재자격 v5

- B1 공개 feedback 변경으로 Worker snapshot bytes가 달라졌지만 첫 qualification batch `profile-r-docker-matrix-r09-company-v7`은 변경 전 Judge workspace hash를 사용했다. 기능 판정은 reference pass와 8개 mutation target fail로 맞았으나 9개 모두 before/after hash mismatch가 되어 `CHALLENGE_NOT_READY`로 봉인됐다.
- 현재 snapshot에서 Profile R Judge source bundle을 다시 생성해 `32 files`, aggregate `79d1cf4f...58320`, `PROFILE_R_SOURCE_BUNDLE_VERIFIED`로 닫았고 표적 시험 `30 passed`를 확인했다. 이를 commit `2062def`로 고정했다.
- 공식 batch `profile-r-docker-matrix-r09-company-v8`은 기존 image `ba83a183...330ab`에서 reference 8/8 pass와 negative mutation 8개 목표 실패가 모두 일치해 `9/9`, `CHALLENGE_READY`였다.
- manifest `bd74f9d5...59a2`, result `5da28bc9...a941`, seal `48673955...7042`이며 별도 verifier가 같은 결과를 재계산했다. 잔여 container는 0개, model·SDK thread·Codex turn은 0회다.
- 공개 projection은 기존 v1~v4를 덮지 않고 `profile-r-docker-judge-qualification-v5`에 추가하고 stage의 Profile R 입력을 v5로 전환한다. 실패한 v7 raw는 보존하지만 qualification 표본으로 합산하지 않는다.

## Profile R qualification v5 기반 Phase E v5 0-turn 후보

- clean source commit `f4ee4b26e6bd2282099d521fa9426d1606ecf060`에서 기존 v1~v4 후보를 덮지 않고 `sdk-routing-realistic-high-difficulty-phase-e-v5`를 생성했다.
- API-key 환경 이름은 없었다. ChatGPT 구독 account/model-list로 SDK `0.144.4`와 `gpt-5.6-sol` 노출만 확인했으며 thread/start, turn/start와 actual model turn은 0회다.
- experiment는 `exp_20260813_a79e6015_1`, Plan fingerprint는 `a79e6015...1718d`, files manifest는 `b03610d5...eb3d`, candidate seal은 `9efcc97c...2c89`다. 별도 verifier가 exact 6-file set과 모든 binding을 재계산해 통과했다.
- 후보는 R SS1→R B1→I B1→I SS1, 32/40 turn 예산과 automatic continuation 금지를 유지한다. 실제 SS1/B1과 다른 model turn은 별도 사용자 승인 전 시작하지 않는다.

## Phase F Profile R SS1 v5 실제 실행

- 사용자 승인 뒤 Phase E v5의 Cell 1 SS1 하나를 fresh root `C:\lao-phase-f-live-a79e6015-pair-1`에서 실행했다. zero-turn preflight는 ChatGPT 구독, SDK `0.144.4`, `gpt-5.6-sol`을 확인했고 API-key 환경 이름은 없었다.
- 한 thread에서 R01~R08을 처리했고 R02·R03 자기검토 2회를 포함해 model turn 10회, session 1회, Attempt 1회였다. token은 input 17,433,659, output 124,194, total 17,557,853이며 model active 3,140.396초, sealed wall 3,170.578초다.
- Worker는 completed를 보고했지만 Docker Judge는 R-P02 `STAGE_DISCRIMINATOR_FAILED`와 R-P05 `DUPLICATE_OR_MISSING_LIFECYCLE`를 실패로 판정했다. Measurement는 `failed / independent_judge_failed`로 봉인됐다.
- Measurement hash는 `a120e193...b647`, Cell seal file hash는 `5fc0be74...3367`이며 별도 verifier가 통과했다. 잔여 container는 0개, Cell 2 B1과 Cell 3은 실행하지 않았고 automatic continuation은 false다.
- 다른 프로젝트가 같은 PC와 ChatGPT 계정에서 동시에 실행돼 wall time은 참고값이다. 현재 source의 B1 대조 Cell이 없으므로 `ROUTING_INCONCLUSIVE`를 유지한다.

## Phase F Profile R B1 v5 실행과 시험환경 결손 확인

- 같은 v5 experiment의 Cell 2 B1을 별도 승인으로 한 번 실행했다. R01~R06은 첫 Attempt에 성공했고 R07은 한 번 재시도한 뒤 `FAILED`, R08은 `PENDING`, Cell 3은 `PLANNED`로 끝났다. actual model turn은 8회다.
- B1 공개 feedback 수정은 실제로 작동했다. 첫 R07 실패에서 재실행 명령, traceback과 예외를 포함한 공개 진단 12,126 bytes가 잘리지 않고 재시도 Worker에게 전달됐다.
- 첫 실패 원인은 `pytest-of-unknown` TEMP 디렉터리 접근 거부였고, 재시도에서는 기능 검사 전에 legacy `project.yaml`의 CRLF/LF byte equality가 실패했다. 따라서 이번 Cell은 `TEST_ENVIRONMENT_CONTAMINATED`이며 repair와 variant 품질 비교에 사용하지 않는다. incident `DEV-20260813-003`을 열었다.
- 독립 Judge는 부분 workspace에서 R-P05와 R-P06을 실패로 판정했다. Measurement hash는 `7ee05a99...21ee`, Cell seal file hash는 `f49fca89...673`이며 별도 verifier가 통과했다. 잔여 Docker container와 Cell 3 실행은 0이다.
- token은 input 13,639,888, output 130,726, total 13,770,614, model active 3,785.305초, sealed wall 3,859.203초다. 다른 프로젝트가 동시에 실행돼 시간은 참고값이다.
- 공식 판정은 `B1_CONTROL_FLOW_VERIFIED / B1_FEEDBACK_DELIVERY_VERIFIED / B1_REPAIR_NOT_EVALUABLE / ROUTING_INCONCLUSIVE`다. 같은 환경으로 live를 반복하지 않고 TEMP 격리와 줄바꿈 독립 fixture 계약을 model-free로 고치기 전까지 추가 실행을 중단한다.
## 2026-08-13 B1 v5 시험환경 결손 구조 교정

- B1 v5의 R07 첫 Attempt는 호스트 `TEMP/TMP` 아래 pytest 디렉터리의 Windows 권한 충돌로, 두 번째 Attempt는 `core.autocrlf=true`가 `git archive` 복원 바이트를 LF에서 CRLF로 바꿔 기능 검사 전에 실패했다. 기존 clean-room 감사가 통과한 것은 model-free 정본 checkout에서 실행됐기 때문이며, 실제 B1 Worker의 임시 경로와 Git 환경을 그대로 관통하지 못했다.
- B1 Check는 이제 실제 Git metadata 아래에 매 Check마다 새 임시 디렉터리를 만들고 `TEMP`, `TMP`, `TMPDIR`을 그 위치로 고정한다. Run 시작·재개 전 같은 환경에서 안전한 Python 쓰기 probe를 통과해야 하며 실패하면 model dispatch 전에 중단한다.
- Check 자식 프로세스에는 Git environment override로 `core.autocrlf=false`를 강제하고, `FixtureRestorer`의 `git archive`에도 같은 설정을 적용했다. Profile R workspace 자체도 초기 commit 전에 `core.autocrlf=false`를 고정한다. exact-byte assertion이나 production ProjectConfig는 완화하지 않았다.
- B1 보고 어댑터가 재시도 뒤 미실행 후속 Task의 빈 Attempt 목록을 인덱싱하던 결함도 고쳐, 실제 실패가 별도 `IndexError`로 가려지지 않게 했다.
- 검증은 B1 전체 `80 passed`, 관련 Runner `76 passed, 2 opt-in skipped`, 실제 B1 v5 Worker 복사본의 R07 canonicalization 회귀 `1 passed`다. model·SDK·Codex·Docker 호출은 0회다. `DEV-20260813-003`은 `resolved`로 닫았다.
- source identity가 바뀌었으므로 Profile R qualification v5와 Phase E v5 candidate는 역사 기록으로만 보존하고 새 live 입력으로 사용하지 않는다. 다음 live 전에 새 qualification과 candidate가 필요하며, 자동 재실행은 승인하지 않았다.

## B1 v5 시험환경 교정 뒤 집 Profile R Docker 재자격 v6

- 작업일: 2026-08-13. 회사의 B1 시험환경 교정 source를 집에 ff-only로 인수한 뒤, 집에 존재하는 동일 Dockerfile·lock image `5610c2a6...6ad89`에 Judge runtime을 다시 결합했다. image binding 표적 시험은 `14 passed, 1 opt-in skipped`였고 source commit은 `3f79bb2f8e26bc8db34fa5380239dd95cdba8640`이다.
- 긴 raw 경로로 인한 patch precheck 중단, 회사 image 부재로 9개 Cell이 모두 runtime error가 된 `C:\q6`의 `CHALLENGE_NOT_READY`, 짧은 source hash 입력 거부는 성공 결과에서 제외했다. `C:\q6` 실패 raw/seal은 보존하고 재분류하지 않는다.
- 공식 fresh batch `C:\q8\profile-r-docker-matrix-q8`은 reference R-P01~R-P08 8/8 pass와 negative mutation 8개의 목표 실패가 모두 일치해 `9/9`, `CHALLENGE_READY`로 닫혔다. seal self-hash는 `167d8813...c04b`, projection SHA-256은 `acfc13f5...476c`이며 별도 process verifier는 `CHALLENGE_READY True 9 9 0`을 재계산했다. 잔여 container는 0개이고 model·SDK thread·Codex turn은 0회다.
- 새 projection은 기존 v1~v5를 덮지 않고 `profile-r-docker-judge-qualification-v6`에 추가했고 stage도 v6를 가리킨다. 다음 관문은 새 Phase E 0-turn 후보 생성이며 이번 승인 범위에서는 자동 생성하거나 실제 Worker/model을 실행하지 않는다.
- projection과 stage binding을 clean commit으로 고정한 뒤 Docker Judge·Phase F Docker port·Phase E binding 관련 회귀는 `22 passed, 1 opt-in skipped`로 통과했다. skip은 실제 Docker smoke opt-in이며 공식 9-cell matrix는 별도 Docker 실행으로 완료됐다.

## Profile R qualification v6 기반 Phase E v6 0-turn 후보

- 작업일: 2026-08-13. qualification v6와 stage binding을 포함한 clean source commit `b61994bc6ebb57370b59a03fa24543c4bf836354`에서 기존 v1~v5 후보를 덮지 않고 `sdk-routing-realistic-high-difficulty-phase-e-v6` 후보를 생성했다.
- API-key 환경 이름은 없었다. SDK account/model-list로 ChatGPT 구독, SDK `0.144.4`, `gpt-5.6-sol` 노출을 확인했으며 thread/start, turn/start와 actual model turn은 0회다. 별도 `codex login status` CLI는 WindowsApps 실행 권한 거부로 시작되지 않았지만 SDK account 확인은 정상 통과했다.
- experiment는 `exp_20260813_a686cd22_1`, Plan fingerprint는 `a686cd22...30ce`, files manifest는 `fffebb68...8918`, candidate seal은 `20f1d3d8...45d2`다. 별도 process verifier가 exact 6-file set과 source/qualification/stage/runtime binding을 다시 계산해 같은 결과를 확인했다.
- 후보는 Profile R SS1→B1, Profile I B1→SS1, 32/40 turn 예산과 automatic continuation 금지를 유지한다. 실제 Worker·SDK thread/turn·Codex model·Cell 3은 별도 사용자 승인 전 실행하지 않는다.
- 후보를 Git에 고정한 clean commit에서 checked-in verifier가 동일 seal을 재계산했고 Phase E model-free 회귀는 `8 passed`였다.
