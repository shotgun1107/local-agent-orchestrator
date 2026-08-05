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
