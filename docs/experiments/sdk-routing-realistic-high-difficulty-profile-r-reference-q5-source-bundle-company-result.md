# Profile R canonical LF reference q5와 Judge source bundle 결과

- 실행일: 2026-09-02
- LF normalization source: `d525c060fc588da18315613ac96d7ca4b5956c43`
- Judge source commit: `4f0a993a4f834a6002e5b967a856a6d86df3ed05`
- Judge source tree: `fe77ea139ae89e97869c3809abf33c0af2be2322`
- 판정: `REFERENCE_CHAIN_REUSED / PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- model·SDK thread/turn·Docker workload: `0`

canonical LF Worker에서 reference repository를 다시 만들었으며 q4의 commit, tree, chain, seal과
bundle이 byte-identical임을 확인했다. q4 reference는 Git object 단계에서는 이미 LF였으므로
불필요하게 새 identity를 만들지 않았다.

Judge source bundle만 canonical Worker bytes에서 다시 생성했다.

- Worker manifest file SHA-256: `6e8701bf3958cedfc7a799999d83234eb450e4d0929513a4b965f452b9f80a18`
- Worker tree aggregate: `41c1b97b9b1546a814ec16cf0c4e339ddf9555f299b8ea4094d64edeb4cd1652`
- canonical runner SHA-256: `e59cdbb442739d92f93702cf76062091df4961eae1c80ab2bd29b00e67b913d6`
- reused reference chain file SHA-256: `4747d4855a7b585a4900527bf166cdb5a833c754a37580e7dcd81b565c6e3b87`
- reused reference chain seal: `e1e2bdf638a347e378b5812cd0f7127b60c49d3280c5723f1dbab1a5190c453a`
- Judge bundle manifest file SHA-256: `94043d66993b0c3d0135d667730ce459b4097e42fd963a1e7c050626d5585175`
- Judge source payload aggregate: `6180174d54925337978d08e7e8abec55aa53e1612a492271ea8b3ee1edc929db`
- expected reference workspace: `f1e35d6019502d3b23705dbb3fba061da3f782a542d82c1c143fde626f70c102`

expected reference workspace는 q23 Docker actual과 exact 일치한다. source bundle 47파일,
R11/R12 reference와 13개 public negative/hidden property 검증, 관련 회귀 33개가 통과했다.

다음 관문은 이 clean source의 fresh q24 Docker Judge qualification이다. q23을 재실행하지
않으며 Task Pack, candidate, acceptance와 Live는 `NO-GO`다.
