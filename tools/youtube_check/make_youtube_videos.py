"""'유튜브' 탭 **영상 목록을 공식 API 로 만들어 올린다** (보는 라디오
전달문 130의 1번).

사장님(11/7): *"아까 차단된 유튜브는 고치고 마무리 하자."*

## 까닭

공식 채널이 맞는데 **공개 RSS(`feeds/videos.xml`)가 비거나 404·500 을
주는 채널**이 있다 — TVCHOSUN MUSIC · KBS 레전드 케이팝 · SBS Biz 가
그랬다(보는 라디오 보고_120·122·130). 깃허브 러너(데이터센터 IP)에서는
**채널을 가리지 않고** 그랬다(보고_127: 통과 0/49).

앱은 RSS 가 아무것도 주지 않으면 **기기에 둔 마지막 목록 → 씨앗**으로
버티는데, 그 둘도 없는 채널은 **늘 빈 카드**였다. 그래서 홈페이지가
**공식 Data API** 로 목록을 만들어 올리고, 앱은 그 **글 파일 하나**를
받아 쓴다.

⚠ **앱에는 키를 넣지 않는다**(보는 라디오 25장) — 키는 이 저장소의
`YT_API_KEY` 하나뿐이다.

⚠ **영상을 받는 것이 아니다** — 영상 번호·제목·올린 때뿐이다(유튜브
개발자 정책 III.E.1). 썸네일 그림도 담지 않는다.

## 무엇을 빼나 (앱과 같은 규칙)

| 빼는 것 | 어떻게 보나 | 왜 |
|---|---|---|
| **비공개·삭제** | `videos.list` 에 아예 안 온다 | 누르면 '비공개 동영상'(129) |
| **삽입 막힘** | `status.embeddable == false` | 앱 안에서 안 나온다 |
| **예정 생방송** | `snippet.liveBroadcastContent == 'upcoming'` | 눌러도 '생방송 오프라인'(26의 2번) |
| **숏츠** | 제목에 `#Shorts` · `#shorts` | 보는 라디오 16장 |

## 쓰는 양 (하루 한도 10,000 단위)

| 부르는 것 | 몇 번 | 단위 |
|---|---|---|
| `playlistItems.list`(채널마다) | 채널 수 | ≈50 |
| `channels.list`(업로드 목록 번호 · 50개씩) | 채널 ÷ 50 | ≈2 |
| `videos.list`(50개씩) | 영상 ÷ 50 | ≈15 |

**한 번 돌 때 약 채널 수 + 17단위**(채널 50 → ≈67)이고 **하루 네 번**이면
**≈270** 이다 — 한도의 **2.7%** 다. 채널 점검(주 1회 ≈64)과 따로 돈다.

## 쓰는 법

    YT_API_KEY=… python make_youtube_videos.py \
        --channels ../_src/visualradio/data/youtube_channels.json \
        --out      ../_src/visualradio/data/youtube_videos.json

⚠ **키가 없으면 아무것도 하지 않는다** — 파일을 건드리지 않고 그대로
돌아간다(공개 쪽으로 만들지 않는다. 그것이 믿을 수 없어 이것을 만들었다).

⚠ **받지 못한 채널은 지난 파일 값 그대로 둔다** — 빈 채로 덮지 않는다.
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ⚠ **적는 글을 UTF-8 로 못 박는다** — 윈도 콘솔(cp949)에서 '—' 하나에
# 터진다(깃허브 러너는 UTF-8 이라 거기서는 탈이 없다).
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
    write_json,
)

# 채널마다 몇 개까지 담나 — 앱이 RSS 로 받는 수(15)와 같다.
RECENT = 15

# 앱의 `RecentVideos.parse` 와 같은 규칙(보는 라디오 16장).
SHORTS = ("#shorts", "#Shorts", "#SHORTS")


def is_short(title):
    """숏츠인가 — 제목에 그 꼬리표가 붙어 온다."""
    return any(mark.lower() in (title or "").lower() for mark in SHORTS)


def uploads_of(channel_ids, key):
    """채널마다 **업로드 목록 번호**. 못 받은 채널은 빠진다."""
    got, _why = api_pages(
        "channels", channel_ids, {"part": "contentDetails"}, key
    )
    out = {}
    for channel_id, item in got.items():
        playlist = (
            (item.get("contentDetails") or {}).get("relatedPlaylists") or {}
        ).get("uploads")
        if playlist:
            out[channel_id] = playlist
    return out


def listed(playlist, key):
    """그 업로드 목록의 맨 위 [RECENT] 개 — `(번호, 제목, 올린 때)`."""
    body, why = api_get(
        "playlistItems",
        {
            "part": "snippet,contentDetails",
            "playlistId": playlist,
            "maxResults": RECENT,
        },
        key,
    )
    if body is None:
        return None, why
    out = []
    for item in body.get("items", []):
        snippet = item.get("snippet") or {}
        details = item.get("contentDetails") or {}
        video_id = details.get("videoId") or (
            (snippet.get("resourceId") or {}).get("videoId")
        )
        if not video_id:
            continue
        out.append(
            (
                video_id,
                (snippet.get("title") or "").strip(),
                details.get("videoPublishedAt")
                or snippet.get("publishedAt")
                or "",
            )
        )
    return out, None


def playable(video_ids, key):
    """**앱 안에서 틀 수 있는 영상**만 돌려준다(번호 모음).

    `videos.list` 에 **아예 안 오는 번호는 비공개·삭제**다(129의 그것).
    """
    ok = set()
    for at in range(0, len(video_ids), API_CHUNK):
        slice_ = video_ids[at : at + API_CHUNK]
        body, _why = api_get(
            "videos",
            {"part": "status,snippet", "id": ",".join(slice_)},
            key,
        )
        if body is None:
            # 못 물어봤으면 **아무것도 빼지 않는다** — 모르는 것을 지우지
            # 않는다(0장). 그 묶음은 그대로 통과시킨다.
            ok.update(slice_)
            continue
        for item in body.get("items", []):
            status = item.get("status") or {}
            snippet = item.get("snippet") or {}
            if status.get("embeddable") is False:
                continue
            if snippet.get("liveBroadcastContent") == "upcoming":
                continue
            ok.add(item.get("id"))
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--channels",
        required=True,
        help="채널 목록 파일(youtube_channels.json)",
    )
    parser.add_argument("--out", required=True, help="영상 목록 파일 자리")
    parser.add_argument("--dry", action="store_true", help="파일을 쓰지 않는다")
    args = parser.parse_args()

    key = api_key()
    if not key:
        # ⚠ **공개 쪽으로 만들지 않는다** — 믿을 수 없어 이것을 만들었다.
        print("YT_API_KEY 가 없습니다 — 영상 목록을 건드리지 않았습니다.")
        return 0

    book = read_json(args.channels, None)
    channels = (book or {}).get("channels") or []
    if not channels:
        print("채널 목록을 읽지 못했습니다:", args.channels)
        return 2
    channel_ids = [
        item["id"] for item in channels if str(item.get("id", "")).startswith("UC")
    ]
    print("채널 %d개" % len(channel_ids))

    before = read_json(args.out, {}) or {}
    kept = before.get("lists") or {}

    uploads = uploads_of(channel_ids, key)
    print("업로드 목록을 받은 채널 %d개" % len(uploads))

    # ① 채널마다 맨 위 몇 개
    rows = {}
    missed = []
    for channel_id in channel_ids:
        playlist = uploads.get(channel_id)
        if not playlist:
            missed.append(channel_id)
            continue
        got, why = listed(playlist, key)
        if got is None:
            print("[x] %s %s" % (channel_id, why))
            missed.append(channel_id)
            continue
        rows[channel_id] = got

    # ② 틀 수 있는 것만 — 비공개·삭제·삽입 막힘·예정 생방송을 뺀다
    every = [video[0] for got in rows.values() for video in got]
    ok = playable(every, key) if every else set()

    lists = {}
    for channel_id, got in rows.items():
        videos = [
            {"videoId": vid, "title": title, "published": when}
            for (vid, title, when) in got
            if vid in ok and not is_short(title)
        ]
        if not videos:
            missed.append(channel_id)
            continue
        lists["yt-" + channel_id] = videos[:RECENT]

    # ③ **받지 못한 채널은 지난 값 그대로** — 빈 채로 덮지 않는다.
    held = 0
    for channel_id in missed:
        key_name = "yt-" + channel_id
        had = kept.get(key_name)
        if had:
            lists[key_name] = had
            held += 1

    today = datetime.date.today().isoformat()
    document = {
        "_comment": (
            "'유튜브' 탭 영상 목록. 공식 YouTube Data API v3 로 6시간마다 "
            "만든다 — 손으로 적지 않는다(보는 라디오 전달문 130). "
            "영상 번호·제목·올린 때뿐이고 영상도 썸네일 그림도 담지 않는다."
        ),
        "fetchedOn": today,
        "lists": lists,
    }

    size = len(json.dumps(document, ensure_ascii=False))
    print(
        "채널 %d개 · 영상 %d개 · %d bytes (%d KB)"
        % (
            len(lists),
            sum(len(v) for v in lists.values()),
            size,
            size // 1024,
        )
    )
    print("새로 받음 %d · 지난 값 그대로 %d" % (len(lists) - held, held))

    # ⚠ **아무것도 얻지 못했으면 적지 않는다**(안전줄) — 키가 막히거나
    # 한도를 넘긴 날 멀쩡한 파일을 빈 것으로 덮지 않는다. 지난 값이
    # 있으면 ③에서 그대로 들고 오므로 여기까지 오는 것은 '정말 아무것도
    # 없는' 날뿐이다.
    if not lists:
        print("얻은 것이 없어 **파일을 쓰지 않았습니다**.")
        return 0

    if not args.dry:
        write_json(args.out, document)
        print("적었습니다:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
