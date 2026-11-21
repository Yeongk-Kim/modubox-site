# -*- coding: utf-8 -*-
"""유튜브 채널이 **어느 나라에서 되는지**를 공식 API 로 읽어 표로 남긴다
(보는 라디오 전달문 177의 2 — 사장님 결정 11/21 06:57 · 안1).

```
YT_API_KEY=… python check_region.py          # 표를 만든다
python check_region.py --selftest            # 셈만 시험한다(바깥 연결 0)
```

## 왜

교민(미국 · 캐나다 · 일본 · 호주)이 우리 앱에서 **영상**을 볼 수 있는지
한국에서는 알 수 없다. 그런데 유튜브는 **업로더가 걸어 둔 설정**을 API 로
그대로 알려 준다 — 재생해 보지 않아도 **근거 있는 표**를 만들 수 있다.

| 읽는 값 | 뜻 |
|---|---|
| `contentDetails.regionRestriction.allowed` | **거기 든 나라만** 된다 |
| `contentDetails.regionRestriction.blocked` | **거기 든 나라는** 안 된다 |
| 둘 다 없음 | **모든 나라** 된다 |
| `status.embeddable` | 거짓이면 **앱 안에서 안 나온다**(나라와 무관) |
| `snippet.liveBroadcastContent` | `live` · `upcoming` · `none` |

⚠ **재생을 흉내 내지 않는다** — 러너 IP 로는 유튜브 재생이 막힌다
(전달문 127에서 통과 0/49). 여기서 읽는 것은 **설정 값뿐**이다.

⚠ **이 표가 '된다'를 보증하지는 않는다** — 업로더 설정 밖의 막힘(음악
권리 · 방송사 자체 차단 · 그 나라 망)은 알 수 없다. 교민 베타 한 분
('가')이 폰에서 보는 것과 **함께** 읽는다.

## 지키는 것

| | |
|---|---|
| **키는 비밀값으로만** | `YT_API_KEY`. ⚠ 값을 로그·표·이슈 어디에도 적지 않는다 |
| **키가 없으면 아무것도 하지 않는다** | 표를 건드리지 않고 그대로 끝난다(공개 쪽으로 흉내 내지 않는다 — 전달문 127) |
| **`search.list` 를 쓰지 않는다** | 한 번에 100단위다. 쓰는 것은 `channels`·`playlistItems`·`videos` 셋뿐이다 |
| **표준 라이브러리만** | 러너에 설치하는 것이 없다 |
| **사용자 정보 0** | 보내는 값은 채널 번호·영상 번호뿐이다 |
| ⚠ **지어내지 않는다** | 못 받은 채널은 '못 받음'이고, 지난 표의 그 줄을 그대로 둔다 |

## 쓰는 양 (하루 한도 10,000 단위)

| 부르는 것 | 몇 번 | 단위 |
|---|---|---|
| `channels.list`(업로드 목록 번호 · 50개씩) | 채널 ÷ 50 | 2 |
| `playlistItems.list`(채널마다 최근 5편) | 채널 수 | 96 |
| `videos.list`(50개씩) | 영상 ÷ 50 | 10 |

채널 96 기준 **한 번 돌 때 ≈108 단위**다. **주 1회**이므로 하루 한도의
**1.1%** 이고, 채널 점검(주 1회 ≈64)·영상 목록(하루 ≈270)과 더해도
넉넉하다.
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 — 옛 파이썬이면 그냥 넘어간다
    pass

# 부르는 길은 **점검기와 한 군데**를 쓴다(두 벌로 두지 않는다).
from check_youtube_channels import (  # noqa: E402
    API_CHUNK,
    api_get,
    api_key,
    api_pages,
    read_json,
    tell,
    write_json,
)

# 재어 보는 나라 — 사장님이 물으신 넷 + **대조용 한국**.
COUNTRIES = [("US", "미"), ("CA", "캐"), ("JP", "일"), ("AU", "호"),
             ("KR", "한")]

# 채널마다 최근 몇 편을 보나.
RECENT = 5


def allows(restriction, country):
    """그 영상이 그 나라에서 **되는가** — 유튜브 문서 그대로.

    | 걸려 있는 것 | |
    |---|---|
    | `allowed` | **거기 든 나라만** 된다 |
    | `blocked` | **거기 든 나라는** 안 된다 |
    | 둘 다 없음 | 모든 나라 된다 |
    """
    restriction = restriction or {}
    allowed = restriction.get("allowed")
    blocked = restriction.get("blocked")
    if allowed is not None:
        return country in allowed
    if blocked is not None:
        return country not in blocked
    return True


def uploads_of(channel_ids, key):
    """채널마다 **업로드 목록 번호**. 못 받은 채널은 빠진다."""
    got, why = api_pages(
        "channels", channel_ids, {"part": "contentDetails"}, key)
    out = {}
    for channel_id, item in got.items():
        playlist = (
            (item.get("contentDetails") or {}).get("relatedPlaylists") or {}
        ).get("uploads")
        if playlist:
            out[channel_id] = playlist
    return out, why


def listed(playlist, key):
    """그 업로드 목록의 맨 위 [RECENT] 개 — 영상 번호만."""
    body, why = api_get(
        "playlistItems",
        {"part": "contentDetails", "playlistId": playlist,
         "maxResults": RECENT},
        key,
    )
    if body is None:
        return [], why
    out = []
    for item in body.get("items", []):
        video = (item.get("contentDetails") or {}).get("videoId")
        if video:
            out.append(video)
    return out, None


def look_at(video_ids, key):
    """영상마다 **나라 제한 · 삽입 허용 · 생방송인가**."""
    got, why = api_pages(
        "videos", video_ids,
        {"part": "contentDetails,status,snippet"}, key)
    out = {}
    for video_id, item in got.items():
        content = item.get("contentDetails") or {}
        status = item.get("status") or {}
        snippet = item.get("snippet") or {}
        out[video_id] = {
            "title": snippet.get("title") or "",
            "live": snippet.get("liveBroadcastContent") or "none",
            "embeddable": bool(status.get("embeddable")),
            "restriction": content.get("regionRestriction") or None,
        }
    return out, why


def judge(rows):
    """채널마다 나라별 '됨' 수 · 삽입 불허 수 · 막힌 영상 보기 하나."""
    out = []
    for row in rows:
        videos = row["videos"]
        counts = {}
        for code, _word in COUNTRIES:
            counts[code] = sum(1 for v in videos if allows(v["restriction"],
                                                           code))
        no_embed = sum(1 for v in videos if not v["embeddable"])
        example = None
        for video in videos:
            if video["restriction"]:
                example = video
                break
        out.append(dict(row, counts=counts, noEmbed=no_embed,
                        example=example))
    return out


GROUP_WORD = {"domestic": "국내", "overseas": "해외"}


def cell(text):
    """⚠ 표 칸에 `|` 가 들어가면 표가 깨진다 — 바꿔 적는다."""
    return (text or "").replace("|", "¦")


def report_text(today, rows, missed, units):
    seen = [row for row in rows if row["videos"]]
    lines = [
        "# 유튜브 **나라별 막힘** 표 (주 1회)",
        "",
        "보는 라디오 전달문 177의 2(안1 · 사장님 결정 11/21 06:57).",
        "**공식 Data API 로 업로더가 걸어 둔 설정만** 읽는다 — 재생을",
        "흉내 내지 않는다(러너 IP 로는 유튜브 재생이 막힌다 · 전달문 127).",
        "",
        "| 잰 날 | 채널 | 영상을 본 채널 | 쓴 쿼터 |",
        "|---|---|---|---|",
        "| %s | %d | %d | 약 %d 단위 |" % (today, len(rows), len(seen), units),
        "",
        "| 카드 | 채널 | 미 | 캐 | 일 | 호 | (한) | 삽입 불허 | 막힌 영상 보기 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        total = len(row["videos"])
        if not total:
            lines.append("| `%s` | %s | — | — | — | — | — | — | %s |" % (
                row["key"], cell(row["name"]),
                cell(row.get("why")) or "못 받음"))
            continue
        cells = ["%d/%d" % (row["counts"][code], total)
                 for code, _word in COUNTRIES]
        example = row["example"]
        note = ""
        if example:
            restriction = example["restriction"]
            where = ("allowed=%s" % ",".join(restriction.get("allowed") or [])
                     if restriction.get("allowed") is not None
                     else "blocked=%s"
                          % ",".join(restriction.get("blocked") or []))
            # ⚠ 제목에 `|` 가 들어 있으면 **표가 깨진다** — 바꿔 적는다.
            note = "%s — %s" % (cell(example["title"])[:40], where)
        lines.append("| `%s` | %s | %s | %d | %s |" % (
            row["key"], cell(row["name"]), " | ".join(cells),
            row["noEmbed"], note or "—"))
    lines += [
        "",
        "## 읽는 법",
        "",
        "- 칸은 **최근 %d편 가운데 그 나라에서 되는 수**다(`5/5` 면 다 된다)." % RECENT,
        "- **삽입 불허**는 `status.embeddable == false` 인 영상 수다 —",
        "  **나라와 무관**하게 우리 앱 안에서 안 나온다(보는 라디오 25장).",
        "- **(한)** 은 대조용이다. 한국도 `5/5` 가 아니면 나라 막힘이 아니라",
        "  그 영상 자체의 설정이다.",
        "- 판정은 유튜브 문서 그대로다 — `allowed` 가 있으면 **거기 든 나라만**,",
        "  `blocked` 가 있으면 **거기 든 나라는 안 됨**, 둘 다 없으면 **모든 나라**.",
        "",
        "## ⚠ 이 표가 보증하지 않는 것",
        "",
        "- 업로더 설정 **밖의 막힘**(음악 권리 · 방송사 자체 차단 · 그 나라 망)은",
        "  알 수 없다. 교민 베타 한 분('가')이 폰에서 보는 것과 **함께** 읽는다.",
        "- 생방송은 **그때그때 다른 영상**이다 — 이 표는 최근 올린 영상의",
        "  설정이고, 지금 하는 생방송의 설정은 아닐 수 있다.",
        "- 못 받은 채널은 **'못 받음'** 이다(지어내지 않는다).",
    ]
    if missed:
        lines += ["", "## 못 받은 까닭", ""]
        for why in sorted(set(missed)):
            lines.append("- %s" % why)
    return "\n".join(lines) + "\n"


def selftest():
    """셈만 시험한다 — **바깥에 연결하지 않는다.**"""
    bad = [0]

    def same(what, got, want):
        if got != want:
            bad[0] += 1
            print("   %s -> %r (바라던 것 %r)" % (what, got, want))

    # 판정 — 유튜브 문서 그대로(allowed / blocked / 둘 다 없음).
    same("제한 없음(None)", allows(None, "US"), True)
    same("제한 없음({})", allows({}, "JP"), True)
    same("allowed 안", allows({"allowed": ["KR", "US"]}, "US"), True)
    same("allowed 밖", allows({"allowed": ["KR"]}, "US"), False)
    same("blocked 안", allows({"blocked": ["US", "CA"]}, "CA"), False)
    same("blocked 밖", allows({"blocked": ["US"]}, "JP"), True)
    # ⚠ 둘 다 오면 **allowed 가 먼저다**(allowed 가 더 좁은 말이다).
    same("둘 다 — allowed 먼저",
         allows({"allowed": ["KR"], "blocked": ["JP"]}, "JP"), False)
    same("빈 allowed", allows({"allowed": []}, "KR"), False)
    same("빈 blocked", allows({"blocked": []}, "KR"), True)

    rows = judge([{
        "key": "x", "name": "x", "kind": "card", "group": "domestic",
        "videos": [
            {"title": "a", "live": "none", "embeddable": True,
             "restriction": None},
            {"title": "b", "live": "none", "embeddable": False,
             "restriction": {"blocked": ["US", "CA"]}},
            {"title": "c", "live": "live", "embeddable": True,
             "restriction": {"allowed": ["KR"]}},
        ],
    }])
    same("미국 됨 수", rows[0]["counts"]["US"], 1)
    same("한국 됨 수", rows[0]["counts"]["KR"], 3)
    same("일본 됨 수", rows[0]["counts"]["JP"], 2)
    same("삽입 불허 수", rows[0]["noEmbed"], 1)
    same("막힌 영상 보기", rows[0]["example"]["title"], "b")

    empty = judge([{"key": "y", "name": "y", "kind": "tab", "group": "news",
                    "videos": []}])
    same("영상 0편 — 보기 없음", empty[0]["example"], None)
    same("영상 0편 — 됨 수 0", empty[0]["counts"]["US"], 0)

    # ⚠ 표에 **키가 적히지 않는다**(비밀값 0).
    text = report_text("2026-11-21", rows, ["API videos HTTP 403"], 108)
    same("표에 키 없음", "key=" in text, False)
    same("표에 못 받은 까닭", "API videos HTTP 403" in text, True)

    print("셈 시험 — %s" % ("모두 통과" if not bad[0]
                           else "**%d 개 어긋남**" % bad[0]))
    return 1 if bad[0] else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", default=os.path.join(HERE, "cards.json"))
    parser.add_argument("--report",
                        default=os.path.join(HERE, "region_report.md"))
    parser.add_argument("--state",
                        default=os.path.join(HERE, "region_state.json"))
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--dry", action="store_true", help="파일을 쓰지 않는다")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    book = read_json(args.cards, None)
    if not book or not book.get("cards"):
        print("채널 목록을 읽지 못했습니다:", args.cards)
        return 2
    cards = book["cards"]

    # ⚠ **키가 없으면 아무것도 하지 않는다** — 표를 건드리지 않는다.
    key = api_key()
    if not key:
        print("키 없음(YT_API_KEY) — 아무것도 하지 않고 끝냅니다.")
        tell(os.environ.get("GITHUB_OUTPUT"), changed="false",
             summary="키 없음")
        return 0

    today = datetime.date.today().isoformat()
    channel_ids = [row["channelId"] for row in cards]
    units = 0

    uploads, why = uploads_of(channel_ids, key)
    units += (len(channel_ids) + API_CHUNK - 1) // API_CHUNK
    missed = [why] if why else []

    picked = {}
    for row in cards:
        playlist = uploads.get(row["channelId"])
        if not playlist:
            picked[row["key"]] = ([], "업로드 목록을 못 받음")
            continue
        videos, fail = listed(playlist, key)
        units += 1
        picked[row["key"]] = (videos, fail)
        if fail:
            missed.append(fail)

    every = [v for videos, _why in picked.values() for v in videos]
    looked, why = look_at(every, key) if every else ({}, None)
    units += (len(every) + API_CHUNK - 1) // API_CHUNK
    if why:
        missed.append(why)

    rows = []
    for row in cards:
        videos, fail = picked[row["key"]]
        rows.append(dict(
            row,
            videos=[looked[v] for v in videos if v in looked],
            why=fail,
        ))
    rows = judge(rows)

    text = report_text(today, rows, missed, units)
    before = ""
    if os.path.exists(args.report):
        with open(args.report, encoding="utf-8") as handle:
            before = handle.read()

    # ⚠ **잰 날 줄만 다른 것은 '바뀜'으로 세지 않는다** — 그러면 주마다
    #   커밋이 쌓인다. 결과가 달라진 날에만 적는다.
    def body_of(blob):
        return "\n".join(line for line in blob.splitlines()
                         if not line.startswith("| 20"))

    changed = body_of(text) != body_of(before)

    blocked = [row for row in rows
               if row["videos"] and any(row["counts"][code] < len(row["videos"])
                                        for code, _w in COUNTRIES[:4])]
    seen = [row for row in rows if row["videos"]]
    summary = "채널 %d · 영상 본 채널 %d · 나라 막힘 있는 채널 %d" % (
        len(rows), len(seen), len(blocked))
    print("%s (쿼터 약 %d 단위)" % (summary, units))
    for row in blocked:
        print("  %-10s %-28s 미 %s · 캐 %s · 일 %s · 호 %s / %d"
              % (row["kind"], row["key"], row["counts"]["US"],
                 row["counts"]["CA"], row["counts"]["JP"],
                 row["counts"]["AU"], len(row["videos"])))

    if args.dry:
        print("\n--dry — 파일을 쓰지 않았습니다.")
        return 0

    with open(args.report, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    write_json(args.state, {
        "_comment": "유튜브 나라별 막힘 점검이 스스로 적는다 — 손으로 "
                    "고치지 않는다.",
        "checkedOn": today,
        "channels": len(rows),
        "sawVideos": len(seen),
        "blocked": sorted(row["key"] for row in blocked),
    })

    tell(os.environ.get("GITHUB_OUTPUT"),
         changed="true" if changed else "false",
         summary=summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
