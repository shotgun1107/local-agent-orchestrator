# Profile R R01~R13 회사 Docker Judge q20 결과

- 실행일: 2026-09-01
- source: `af7f50055a07b1c31b4aa4c972d2c9f3f3d912fb`
- batch: `profile-r-docker-matrix-q20-company-r01-r13`
- raw: `C:\q20\profile-r-docker-matrix-q20-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v17/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_NOT_READY`, expectation match `0/14`, model turn `0`

public checker 교정으로 바뀐 Worker baseline과 새 reference chain을 exact source에 고정한 뒤
reference 1개와 전용 known-bad mutation 13개를 같은 Docker Judge 경계로 순차 실행했다.
Judge의 property 판정 자체는 모두 기대와 같았다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- prerequisite blocking: `0`
- Judge outcome expectation: `14/14` 일치
- residual Profile R container: `0`

그러나 14개 셀 모두 `WORKSPACE_BEFORE_MISMATCH`와 `WORKSPACE_AFTER_MISMATCH`를 기록했다.
reference의 protected expected workspace는
`45e695c72b16805776d684aa07ef2e748c5482ef0bd8515c3957919808f091b8`였고 실제 새 baseline의
reference workspace는
`744f5ede0695562221bf560577d82e804564aa77e38339076dd18fd101f7693e`였다. reference chain만
재생성하고 protected Judge source의 reference/mutation Evidence를 다시 만들지 않은 것이
직접 원인이다. q20은 이를 fail-closed로 거부했고 같은 batch를 재실행하지 않았다.

주요 SHA-256:

- manifest file: `85e42aea5ddfb14bce1bc7e4fcdf81f6d94840dca56fc062c3516de0add3974a`
- result file: `dec0e95d77c23b9594e16fb9a69e3654e3f42b9f7e38bdd3f871bcbb9fb780b9`
- seal file: `f113ca462105e310e5492620560514197849375242688cd4e77d62d7df08faf1`
- files manifest file: `15c531303fef85d9b2f787b791766dae1c5d2477c98853c0e0d61854192459da`
- manifest self: `16ca172c5817ff1fbe32ec73c91ecbd2a9d904200aa82e86140ae2f5fcb85298`
- result self: `4aa899b1358f81fca76cd0234396741e8fc9d785fc4fd739d551307e903e2a95`
- seal self: `f55996ab8df68fd3e6d57ef4bf2b567a3005fa0d043e7269a0ae084cc12685ba`
- payload aggregate: `58de8fb278da23b98e016be8ab6e6084b7fbbebae344dd2f633a9ff873932201`
- projection file: `90b4dfb86e11a94d0ac8bcd3b91a24a4e0c0e4b2707535add15725f1bf4ceae7`
- Docker environment file: `489eb91c8b6a699727f1b2924e48744d8445b7520eeee1136e646358aaca8ff7`

q20 raw·seal·projection은 실패 진단 Evidence로 보존한다. Judge source bundle을 새 baseline에서
model-free 재생성한 결과 14개 protected workspace hash가 q20 실제 관측값과 모두 exact
일치했고 source bundle은 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`, 47파일, aggregate
`ee01f8c515e62b34c14441087ee07fdddc2c0ff38546324ae64dc7ddc49463ff`가 됐다. 관련 회귀는
`36 passed`다.

다음 관문은 이 교정 source를 새 commit으로 고정한 뒤 fresh q21을 실행하는 것이다. q20을
성공으로 재분류하지 않으며 Task Pack q2, candidate, acceptance와 Live는 아직 `NO-GO`다.
