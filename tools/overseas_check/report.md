# 라디오 소리 주소 점검 (주 1회)

보는 라디오 보고_162 의 판단 ⑤ '나' + 전달문 177(안1). **미국
러너에서** 소리 주소를 열어 보고 적는다 — 유튜브(영상)는 여기서
재지 않는다(`../youtube_check/region_report.md` 가 **API 로 설정
값만** 읽는다).

| 잰 날 | 러너 자리 | 열림 | 받은 양 |
|---|---|---|---|
| 2026-11-23 | github-hosted ubuntu (미국) | 27 / 40 | 260KB |

| 카드 | 이름 | 묶음 | 방식 | 결과 | 응답 코드 | 첫 소리까지 |
|---|---|---|---|---|---|---|
| `bbs-radio` | BBS 불교방송 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 9.4초 |
| `cbs-musicfm` | CBS 음악FM | 국내 | 고정 | **열림** | HTTP/1.1 200 | 5.3초 |
| `cbs-standardfm` | CBS 표준FM | 국내 | 고정 | **열림** | HTTP/1.1 200 | 4.2초 |
| `cpbc-radio` | cpbc 라디오 | 국내 | 조회 | **조회 거절** | 조회 200 | onair.source.mediasource.mediaurl 자리가 비었다 |
| `ebs-fm` | EBS FM | 국내 | 고정 | **열림** | HTTP/1.1 200 | 3.8초 |
| `febc-daejeon` | 극동방송 대전 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 4.8초 |
| `febc-seoul` | 극동방송 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 5.4초 |
| `gugak-fm` | 국악방송 라디오 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 9.9초 |
| `ifm-radio` | 경인방송 iFM | 국내 | 고정 | **열림** | HTTP/1.1 200 | 4.6초 |
| `kbs-1radio` | KBS 1라디오 | 국내 | 조회 | **열림** | HTTP/1.1 200 | 1.5초 |
| `kbs-classicfm` | KBS 클래식FM | 국내 | 조회 | **열림** | HTTP/1.1 200 | 1.3초 |
| `kbs-coolfm` | KBS 쿨FM | 국내 | 조회 | **열림** | HTTP/1.1 200 | 1.4초 |
| `kbs-daegu-radio` | KBS대구 라디오 | 국내 | 조회 | **조회 거절** | 조회 200 | 주소가 아니다 |
| `kbs-daejeon-radio` | KBS대전 라디오 | 국내 | 조회 | **조회 거절** | 조회 200 | 주소가 아니다 |
| `kbs-happyfm` | KBS 2라디오 해피FM | 국내 | 조회 | **열림** | HTTP/1.1 200 | 1.2초 |
| `kbs-suncheon` | KBS순천 | 국내 | 조회 | **조회 거절** | 조회 200 | 주소가 아니다 |
| `kfn-radio` | 국방FM (KFN) | 국내 | 고정 | **열림** | HTTP/1.0 200 | 2.9초 |
| `mbc-fm4u` | MBC FM4U | 국내 | 조회 | **열림** | HTTP/1.1 200 | 5.1초 |
| `mbc-sfm` | MBC 표준FM | 국내 | 조회 | **열림** | HTTP/1.1 200 | 5.9초 |
| `mbc-trot` | MBC 트로트라디오 | 국내 | 조회 | **열림** | HTTP/1.1 200 | 5.9초 |
| `obs-radio` | OBS 라디오 FM99.9 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 9.6초 |
| `sbs-gorealram` | SBS 고릴라M | 국내 | 조회 | **조회 거절** | 조회 200 | onair.source.mediasource.mediaurl 자리가 비었다 |
| `sbs-lovefm` | SBS 러브FM | 국내 | 조회 | **조회 거절** | 조회 200 | onair.source.mediasource.mediaurl 자리가 비었다 |
| `sbs-powerfm` | SBS 파워FM | 국내 | 조회 | **조회 거절** | 조회 200 | onair.source.mediasource.mediaurl 자리가 비었다 |
| `tbn-busan` | tbn 부산교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbn-chungbuk` | tbn 충북교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbn-daegu` | tbn 대구교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbn-daejeon` | tbn 대전교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbn-gyeongin` | tbn 경인교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbn-ulsan` | tbn 울산교통방송 | 국내 | 고정 | **소리 거절** | — | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: certificate has expired (_ssl.c:1011)> |
| `tbs-efm` | TBS eFM (영어) | 국내 | 고정 | **열림** | HTTP/1.1 200 | 5.3초 |
| `tbs-fm` | TBS 시민의방송 | 국내 | 고정 | **열림** | HTTP/1.1 200 | 4.4초 |
| `ubc-radio` | ubc 울산방송 라디오 | 국내 | 고정 | **열림** | HTTP/1.0 200 | 3.4초 |
| `wbs-radio` | WBS 원음방송 | 국내 | 고정 | **열림** | HTTP/1.1 200 | 1.2초 |
| `ytn-radio` | YTN 라디오 | 국내 | 고정 | **열림** | HTTP/1.1 200 | 4.6초 |
| `kradio-ny-1660` | K-Radio AM1660 (뉴욕) | 해외 | 고정 | **열림** | HTTP/1.0 200 | 0.7초 |
| `radio-korea-atlanta` | 애틀랜타 라디오코리아 AM790 | 해외 | 고정 | **열림** | HTTP/1.0 200 | 0.8초 |
| `radio-korea-la` | Radio Korea (LA, AM 1540) | 해외 | 고정 | **열림** | ICY 200 | 0.4초 |
| `radio-seoul-la` | 라디오 서울 AM1650 (LA) | 해외 | 고정 | **열림** | HTTP/1.1 200 | 0.6초 |
| `rain-fm-la` | RAIN FM (LA, K-POP) | 해외 | 고정 | **열림** | HTTP/1.1 200 | 0.6초 |

## 결과 네 가지

| | 뜻 |
|---|---|
| **열림** | 소리가 512바이트 넘게 흘렀다 |
| **조회 거절** | ① 방송사 **조회 API** 가 막았다(해외 막힘이면 여기다) |
| **소리 거절** | ② 조회는 됐는데 **그 소리 주소**가 막혔다 |
| **시간 초과** | 8초 안에 답이 없었다 |

- ⚠ **'열림이 아니다'가 곧 '해외에서 안 된다'는 뜻은 아니다** —
  그 주소가 그 시각에 응답하지 않았다는 뜻이다. 두 주 잇달아
  그러면 사람이 본다.
- ⚠ **러너는 데이터센터 IP 다** — 가정용 망과 다를 수 있다.
  교민 베타 한 분('가')이 폰에서 보는 것과 **함께** 읽는다.
- ⚠ 이 표로 `assets/SOURCES.md` 의 `overseas` 칸을 **곧바로**
  채우지 않는다 — 그 칸은 **영상까지** 되는지를 말한다.
- ⚠ 소리 번호를 **나눠 쓰는 카드**가 있다(`mbc-trot` 과 `mbc-sfm`).
  그런 카드는 줄이 둘이지만 **한 번만** 열어 본다.
