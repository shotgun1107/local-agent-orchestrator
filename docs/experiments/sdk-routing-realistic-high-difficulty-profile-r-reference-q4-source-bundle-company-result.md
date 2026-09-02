# Profile R R01~R13 reference q4와 Judge source bundle 결과

- 실행일: 2026-09-02
- atomic retry source: `b74239e15744d63a4ef774bfa56cdee789b0d045`
- sealed artifact commit: `eb062d3ccd2046372589782c4072432e7b749145`
- sealed artifact tree: `a02700c4d7c2d0c0bdb0208b09b9056730906b5f`
- 판정: `REFERENCE_CHAIN_BUILT / PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- model·SDK thread/turn·Docker workload: `0`

Windows atomic replace bounded retry와 명시적 public infrastructure override를 포함한 새 Worker
snapshot에서 reference repository와 Judge source bundle을 다시 만들었다.

- Worker manifest file SHA-256: `3a0594bd1e50b0dd45989c3198a1c40a8a54a49a21ba759a8f5c20100245ce9a`
- Worker tree aggregate: `01bc5a541ed3722e598992904f8e43f2dd2a5670fb886a08eaf9019afbf276e7`
- reference base commit/tree: `b5b92a2594bad0d40cad0c63c2161a9d053e81b8` / `180d0e2de8ae2c4cfc17077e317babf638dca5e6`
- reference final commit/tree: `6ef6a812a177c35584a75b0a70a891dcbc4b769b` / `6b724bf793c8a2d2cd155ebdbf96e658bf5449d3`
- reference chain file SHA-256: `4747d4855a7b585a4900527bf166cdb5a833c754a37580e7dcd81b565c6e3b87`
- reference chain seal: `e1e2bdf638a347e378b5812cd0f7127b60c49d3280c5723f1dbab1a5190c453a`
- reference bundle SHA-256: `e4ddac6177324abdfdaad35fcc0c845f4661ff07667b03d789dff0601eee000a`
- reference manifest file SHA-256: `822e5d48ffdc408d19b21f43aedbe6162840b28ccd1107cb7204daf289007f31`
- Judge source bundle manifest SHA-256: `00e907641f36236c01fda341c248d37bcc8fb2e42c4a49a3634ad2f39a763147`
- Judge source payload aggregate: `6f50066fd8ba9a6811f7c191e7325058eb8ab47d73a899b68526e0f04641a735`

reference repository는 정확히 14개 commit, clean status, unreachable object 0, complete bundle과
recomputed seal equality를 통과했다. R11 known-bad는 public `PRODUCT_ASSERTION`, rejection true,
hidden R-P11 fail이다. reference·Worker·Judge source 회귀는 33 passed다.

기존 q22/q3/candidate v20과 두 실패 preflight는 역사 Evidence로만 보존한다. 다음 관문은 이
clean source를 고정한 fresh q23 Docker Judge qualification이다. Task Pack q4, 새 candidate,
acceptance와 Live는 `NO-GO`다.
