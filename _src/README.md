# modubox.app 원고 폴더 (_src)

이 사이트는 **원고(_src) → build.py → docs/(GitHub Pages가 내보내는 폴더)** 로 만들어집니다.
docs/ 는 손으로 고치지 않습니다(빌드할 때마다 새로 만들어짐).

## 누가 무엇을 (2026-10-22 두 세션 합의)
| 폴더·파일 | 고치는 쪽 |
|---|---|
| `_src/build.py` · `apps.json` · `site.json` · `static/` · `README.md` | 수면앱 세션 |
| `_src/sleep/` | 수면앱 세션 |
| `_src/box/` | 모두박스 세션(Cowork 원고 → 모두박스 클로드 코드가 커밋·푸시) |
| `_src/<새 앱>/` | 그 앱 세션 |
| 빌드·`docs/` 커밋·배포 | 수면앱 세션(빌드 전 확인: 자기 폴더 밖 변경 없음 · 금지 문구 · 링크) |

작업 순서: `git pull` → **자기 폴더만** 수정 → `git status`로 다른 폴더 변경 0 확인 → 커밋·푸시 → 수면앱 세션에 "원고 올렸음" 알림.

## 앱 폴더 형식 `_src/<앱>/`
| 파일 | 만들어지는 곳 | 비어 있으면 |
|---|---|---|
| `page.md` | `/<앱>/` 소개 + 홈 카드 | (필수) |
| `help.md` | `/<앱>/help/` 도움말 | 페이지 안 만듦 |
| `faq.md` | `/<앱>/help/` 아래 '자주 묻는 질문' | 안 넣음 |
| `updates.md` | `/<앱>/updates/` | 안 만듦 |
| `privacy.md` | `/<앱>/privacy/` (apps.json `privacy_format: "md"`일 때) | — |
| `img/` | `/<앱>/img/` (화면 사진 등) | — |
| `static/` | `/<앱>/` 아래 그대로 복사(앱이 읽는 데이터: `static/radio/v1/` → `/box/radio/v1/`) | — |

주석(`<!-- … -->`)만 있는 파일은 비어 있는 것으로 봅니다.

### page.md
```
---
title: 브라우저 탭 제목
description: 검색 결과 설명(한 줄)
h1: 큰 제목
lead: 제목 아래 한두 문장
card: 회사 홈 카드에 나오는 한 문장
---
본문(마크다운). 문단, "- 목록", [링크](https://…). HTML 그대로 써도 됨(예: <p class="note">…</p>).

<!-- buttons -->   ← 이 자리에 '곧 출시합니다/Google Play에서 받기 · 도움말 · 개인정보처리방침' 버튼이 자동으로 들어감

버튼 아래 본문.
```
- 받기 버튼·도움말 버튼·처리방침 버튼은 쓰지 않습니다(apps.json의 status와 help.md 유무로 자동).
- 사업자 정보·머리·바닥도 쓰지 않습니다(build.py 한 곳).

### faq.md
```
### 질문
답변 문단
```
실제로 받은 문의·리뷰에서 나온 질문만 씁니다.

### updates.md
```
## 2026-11-01 · 버전 3.1
- 바뀐 점
```
최근 것을 위에.

## apps.json (앱 목록, 수면앱 세션 관리 — 바꿀 때 요청)
`slug · name_ko · name_en · package · status · langs · color · mail · privacy_format · privacy_revised`
- status: `preparing`(숨김) · `testing`(곧 출시합니다) · `live`(Google Play 받기 버튼, utm_source=site&utm_campaign=<앱>_hero) · `retired`(숨김)
- 새 앱 = 한 줄 추가 + `_src/<앱>/` 폴더. 메일 `<앱>@modubox.app`은 바로 받음(ImprovMX catch-all).

## 지킬 것
- 공통: 과장·순위(최고·1위·유일), 남의 로고, 확인 안 된 수치, 지어낸 후기·질문 금지. 추적 도구·쿠키·광고 넣지 않음.
- 앱별 금지는 그 앱 원고 안에서: 모두박스 — "광고 없음" 문장·방송사 로고·"전파를 잡는다"·가족 원격 미언급 / 수면앱 — 의료 효능 금지, 의료기기 아님 고지 유지.
- 유료 기능 이름은 모든 앱 **"PRO"**(대문자, 10/22 사장님 결정). "Pro"·"프로"로 쓰지 않음.
- 출시 전에는 "곧 출시합니다"(status=testing).
- `static/` 데이터는 버전 폴더(v1, v2 …)로만 늘리고 옛 버전을 지우지 않음.
- 루트 `_src/static/googledf0d111223ff9489.html`(Search Console 인증)·CNAME은 건드리지 않음.

## 빌드(수면앱 세션)
```
pip install markdown
python3 _src/build.py      # → docs/
```
같은 원고면 같은 결과(날짜는 apps.json `privacy_revised`만 씀).
