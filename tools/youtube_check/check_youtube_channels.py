"""'유튜브' 탭 채널 목록을 **매주 저절로 점검한다** (전달문 121의 2번).

사장님(11/7): 채널 목록을 사람이 수시로 점검하지 않게 **"완전 자동으로"**.

이 파일은 **회사 홈페이지 저장소**(`Yeongk-Kim/modubox-site`)에서 깃허브
액션이 돌린다. 보는 라디오 저장소의 `tools/build_youtube_channels.py` 가
하던 확인 ①~⑤를 **표준 라이브러리만으로** 옮긴 것이다 — 러너에 아무것도
설치하지 않는다.

| 확인하는 것 | 어떻게 |
|---|---|
| 채널 번호 `UC…` | 채널 쪽의 `canonical`(없으면 `externalId`) |
| 채널 이름 | `og:title` — **견주어 본다**(이름이 다르면 버린다) |
| 지난 영상 목록 | `feeds/videos.xml?channel_id=UC…` 가 200인지 |
| 한국어 채널인가 | 맨 위 영상 제목에 한글이 있는지(영어 채널은 끈다) |
| 아직 올리는가 | 맨 위 영상이 `freshDays` 안인지 |
| **앱 안 재생** | 맨 위 영상을 `oembed` 로 물어 200인지 |

⚠ **유튜브 Data API 를 쓰지 않는다** — 공개 쪽만 본다. **비밀값(키)이
하나도 필요 없다**(전달문 121의 2-f).

⚠ **검색으로 새 채널을 찾지 않는다.** 후보는 `candidates.json` 에 적힌
것뿐이고, 거기에 넣는 일은 **사람이 한다**.

## 점검 규칙 (전달문 121의 2번)

| | |
|---|---|
| a | 이미 목록에 있는 채널은 **2주 연속** 실패해야 뺀다(1주는 숫자만 올린다) |
| b | 이번 주 통과가 지난 목록의 **80% 밑이면 파일을 쓰지 않는다**(유튜브가 통째로 막힌 날) |
| c | 후보가 통과하면 넣는다 — **그 분야 끝**에. 분야는 다섯뿐이고 다른 값은 거부 |
| d | **바뀐 게 있을 때만** 커밋한다(이 파일은 `changed` 를 알려 주고, 커밋은 워크플로가 한다) |
| e | 바뀌었거나 · b 에 걸렸거나 · **2주 넘게 확인을 못 했으면** 이슈 하나를 연다 |
| f | 비밀값을 쓰지 않는다 |
| g | 이미 목록에 있는 채널이 **1년 넘게 새 영상이 없으면** 저절로 빼지 않고 |
|   | 이슈에 **'빼기 후보'** 로만 적는다(전달문 122의 2번) |
| h | 환경변수 **`YT_API_KEY`** 가 있으면 **공식 Data API** 로 확인하고, |
|   | 없으면 **지금 공개 쪽 그대로** 돈다(전달문 127) |

⚠ **앱은 그대로 키 없이 공개 RSS 를 쓴다** — 키는 **점검기만** 쓴다
(보는 라디오 25장의 '지키는 것'). 까닭과 쓰는 양은 아래 API 묶음 설명에
있다. ⚠ **키를 읽거나 적지 않는다** — 있는지만 보고 주소에 실어 보낸다.

⚠ **g 는 `freshDays`(30일)와 다른 자리다.** 30일 규칙은 **새 후보를 넣지
않으려는** 것이고, 이미 들어 있는 채널은 오래 멈췄다고 **빠지지 않는다** —
그 채널을 ☆ 로 담아 둔 사람의 목록이 깨지면 안 된다(전달문 120).

쓰는 법:
    python check_youtube_channels.py --out ../_src/visualradio/data/youtube_channels.json
    python check_youtube_channels.py --out … --dry     # 파일을 쓰지 않고 표만
    YT_API_KEY=… python check_youtube_channels.py --out …   # 공식 API 로
"""

import argparse
import datetime
import gzip
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ⚠ **`Accept-Encoding: gzip` 을 빼면 피드가 404 를 준다**(10/26 확인).
# 유튜브가 '여느 브라우저처럼 묻지 않는 쪽'을 막는다.
FEED_UA = "curl/8.0"

# ⚠ **쪽 주인의 번호는 `canonical` 에서 읽는다**(전달문 47).
# `"channelId":"…"` 를 먼저 집으면 **옆에 추천으로 붙은 남의 채널**이 잡힌다.
CANONICAL = re.compile(
    r'<link rel="canonical" href="https://www\.youtube\.com/channel/'
    r"(UC[A-Za-z0-9_-]{22})\""
)
EXTERNAL_ID = re.compile(r'"externalId":"(UC[A-Za-z0-9_-]{22})"')
TITLE = re.compile(r'<meta property="og:title" content="([^"]*)"')
HANGUL = re.compile(r"[가-힣]")

# 분야 다섯 — **이 차례로 보인다.** 다른 값은 거부한다(규칙 c).
CATEGORIES = ["news", "music", "show", "culture", "movie"]

# a. 이만큼 **연속으로** 실패해야 뺀다.
DROP_AFTER = 2

# b. 이번 주 통과가 지난 목록의 이 비율보다 적으면 파일을 쓰지 않는다.
KEEP_AT_LEAST = 0.8

# e. 이만큼 **확인을 못 하면** 이슈를 연다.
STALE_DAYS = 14

# g. 이미 목록에 있는 채널이 이만큼 새 영상이 없으면 **'빼기 후보'** 로
#    이슈에 적는다 — **저절로 빼지는 않는다**(전달문 122의 2번).
DORMANT_DAYS = 365


def plain(text):
    """띄어쓰기·대소문자를 지운 글 — 이름을 견주는 데 쓴다."""
    return re.sub(r"[\s·'’\-_.]", "", text).lower()


def fetch(url, timeout=25, agent=UA):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": agent,
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding", "") == "gzip":
            raw = gzip.decompress(raw)
        return response.status, raw


def channel_of(handle):
    """핸들(또는 `channel/UC…`)로 번호와 이름을 읽는다."""
    try:
        status, body = fetch("https://www.youtube.com/" + handle)
    except urllib.error.HTTPError as error:
        return None, "채널 쪽 HTTP %s" % error.code
    except Exception as error:  # noqa: BLE001 — 까닭을 표에 적기만 한다
        return None, "채널 쪽 %s" % type(error).__name__
    if status != 200:
        return None, "채널 쪽 HTTP %s" % status

    html = body.decode("utf-8", "replace")
    found = CANONICAL.search(html) or EXTERNAL_ID.search(html)
    if not found:
        return None, "채널 번호를 못 찾음"
    name = TITLE.search(html)
    # ⚠ `og:title` 은 **HTML 글자로** 온다(`it&#39;s Live`) — 풀지 않으면
    # 이름을 견줄 때 어긋난다(전달문 47).
    real = html_mod.unescape(name.group(1).strip()) if name else ""
    return (found.group(1), real), None


# ⚠ **유튜브 RSS 는 멀쩡한 목록에도 404·500 을 준다**(보는 라디오 16장).
# 그래서 **두 번 더** 물어본다 — 앱도 0.5초 쉬고 세 번까지 묻는다.
# 한 번만 묻고 포기하면 매주 '빠짐'이 들쭉날쭉해진다.
FEED_TRIES = 3
FEED_PAUSE = 1.5


def latest(channel_id):
    """공개 RSS 맨 위 영상 — (영상번호, 제목, 올린 날)."""
    url = "https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id
    why = "RSS 를 묻지 못함"
    body = None
    for turn in range(FEED_TRIES):
        if turn:
            time.sleep(FEED_PAUSE)
        try:
            status, got = fetch(url, agent=FEED_UA)
        except urllib.error.HTTPError as error:
            why = "RSS HTTP %s" % error.code
            continue
        except Exception as error:  # noqa: BLE001
            why = "RSS %s" % type(error).__name__
            continue
        if status != 200:
            why = "RSS HTTP %s" % status
            continue
        body = got
        break
    if body is None:
        return None, why

    xml = body.decode("utf-8", "replace")
    entry = xml[xml.find("<entry>") :]
    video = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", xml)
    title = re.search(r"<title>([^<]*)</title>", entry)
    when = re.search(r"<published>(\d{4}-\d{2}-\d{2})", entry)
    if not video:
        return None, "RSS 에 영상이 없음"
    return (
        video.group(1),
        html_mod.unescape(title.group(1)) if title else "",
        when.group(1) if when else "",
    ), None


def embeddable(video_id):
    """앱 안(우리 플레이어)에서 틀 수 있나 — `oembed` 가 200이면 된다."""
    url = (
        "https://www.youtube.com/oembed?format=json&url="
        "https%3A//www.youtube.com/watch%3Fv%3D" + video_id
    )
    try:
        status, _ = fetch(url, timeout=15)
    except urllib.error.HTTPError as error:
        return False, "oembed HTTP %s" % error.code
    except Exception as error:  # noqa: BLE001
        return False, "oembed %s" % type(error).__name__
    return status == 200, ""


def matches(expect, real_name):
    """채널 쪽 이름이 **기다리던 이름**인가.

    ⚠ `expect` 는 **여럿일 수 있다**(글 하나 또는 목록). 같은 채널인데도
    유튜브가 날에 따라 한국어 이름과 영어 이름을 번갈아 준다 —
    11/7에 '쇼박스 SHOWBOX' 가 'ShowBox' 로 왔다. 하나만 적어 두면
    멀쩡한 채널이 '이름이 다름'으로 떨어진다.
    """
    if not expect:
        return True
    wants = expect if isinstance(expect, list) else [expect]
    here = plain(real_name)
    return any(plain(want) in here for want in wants if want)


def inspect(candidate, fresh_days, today, known=False):
    """후보 하나를 확인한다.

    통과하면 `(채널, None, 멈춘 날수)`, 아니면 `(None, 까닭, None)`이다.

    `known` 이면 **이미 목록에 있는 채널**이다 — 오래 멈췄다고 떨어뜨리지
    않고, 1년을 넘으면 세 번째 값에 그 날수를 담아 **'빼기 후보'** 로만
    알린다(전달문 122의 2번).
    """
    got, why = channel_of(candidate["handle"])
    if got is None:
        return None, why, None
    channel_id, real_name = got

    expect = candidate.get("expect") or ""
    if not matches(expect, real_name):
        return None, "이름이 다름('%s')" % real_name[:20], None

    # ⚠ **번호로 쪽을 다시 열어 맞춰 본다**(전달문 47) — 핸들이 넘겨 준
    # 번호가 어긋날 수 있다.
    again, why = channel_of("channel/" + channel_id)
    if again is None:
        return None, "번호로 다시 열지 못함(%s)" % why, None
    if again[0] != channel_id:
        return None, "번호가 맞지 않음(%s → %s)" % (channel_id, again[0]), None
    real_name = again[1] or real_name
    if not matches(expect, real_name):
        return None, "이름이 다름('%s')" % real_name[:20], None

    got, why = latest(channel_id)
    if got is None:
        return None, why, None
    video_id, video_title, when = got

    if candidate.get("korean", True) and not HANGUL.search(video_title):
        return None, "한국어 채널이 아닌 듯('%s')" % video_title[:20], None

    dormant = None
    if when:
        days = (today - datetime.date.fromisoformat(when)).days
        if days > fresh_days:
            # 새 후보는 **넣지 않는다** — 늘 빈 채널이 된다.
            if not known:
                return None, "최근 영상이 %s일 전(기준 %s일)" % (
                    days,
                    fresh_days,
                ), None
            # g. ⚠ **이미 있는 채널은 빼지 않는다**(전달문 122의 2번) —
            #    1년을 넘으면 '빼기 후보'로만 적는다.
            if days > DORMANT_DAYS:
                dormant = days

    ok, embed_why = embeddable(video_id)
    if not ok:
        return None, "앱 안 재생 막힘(%s)" % embed_why, None

    return (
        {
            "id": channel_id,
            "name": candidate["name"],
            "realName": real_name,
            "category": candidate["category"],
        },
        None,
        dormant,
    )


# ─────────────────────────────────────────────────────────────────────
# 공식 **YouTube Data API v3** 길 (보는 라디오 전달문 127)
#
# 까닭(수면앱 세션 회신 11/7): 홈페이지 저장소의 Actions 첫 실행에서
# **통과 0/49** 였다 — RSS 가 404·500, 채널 쪽도 404, 이름이 엉뚱하게 왔다
# (`KBS News` → 'byung joo lee' · `MBCNEWS` → 'MBC الأخبار'). 데이터센터
# IP 를 유튜브가 막거나 다른 쪽을 준다. 안전장치 **b** 는 제대로 걸려
# 목록은 그대로였지만, **공개 쪽은 자동 점검에 쓸 수 없다.**
#
# | | |
# |---|---|
# | 키가 있으면(`YT_API_KEY`) | **API 로** 확인한다 |
# | 키가 없으면 | **지금 공개 쪽 그대로**다(한 줄도 바뀌지 않았다) |
#
# ⚠ **앱은 그대로 키 없이 공개 RSS 를 쓴다**(보는 라디오 25장의 '지키는
# 것'). 키는 **점검기만** 쓴다.
#
# ⚠ **키를 읽거나 적지 않는다** — 환경변수에서 **있는지만** 보고 주소에
# 실어 보낼 뿐이고, 로그·이슈·보고에 **값을 적지 않는다**.
#
# ## 쓰는 양 (하루 한도 10,000 단위)
#
# | 부르는 것 | 몇 번 | 한 번에 | 단위 |
# |---|---|---|---|
# | `channels.list`(id 50개씩) | 채널 ÷ 50 | 1 | ~2 |
# | `playlistItems.list`(업로드 목록) | 채널마다 1 | 1 | ~62 |
# | `videos.list`(id 50개씩) | 영상 ÷ 50 | 1 | ~2 |
#
# **한 번 돌 때 약 66단위**(채널 62개 기준)다 — 매주 한 번이니 한도의
# **0.7%** 다. 사람이 손으로 돌려 봐도 넉넉하다.

API = "https://www.googleapis.com/youtube/v3/"

# 한 번에 묻는 번호 수 — API 가 정한 한도다.
API_CHUNK = 50

# 최근 영상을 몇 개까지 보나(날짜만 쓴다).
API_RECENT = 5


def api_key():
    """`YT_API_KEY` 가 있으면 그것. ⚠ **값을 어디에도 적지 않는다.**"""
    return (os.environ.get("YT_API_KEY") or "").strip()


def api_get(what, params, key, timeout=25):
    """API 를 한 번 부른다 — `(dict, None)` 또는 `(None, 까닭)`.

    ⚠ 까닭에 **키를 담지 않는다.**
    """
    query = dict(params)
    query["key"] = key
    url = API + what + "?" + urllib.parse.urlencode(query, doseq=True)
    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "Accept-Encoding": "gzip"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8", "replace")), None
    except urllib.error.HTTPError as error:
        # 403 은 거의 한도 넘김이거나 키 제한이다.
        return None, "API %s HTTP %s" % (what, error.code)
    except Exception as error:  # noqa: BLE001
        return None, "API %s %s" % (what, type(error).__name__)


def api_pages(what, ids, params, key):
    """번호를 [API_CHUNK] 개씩 나눠 묻고 **번호 → 항목**으로 모은다."""
    got = {}
    why = None
    for at in range(0, len(ids), API_CHUNK):
        slice_ = ids[at : at + API_CHUNK]
        body, fail = api_get(
            what, dict(params, id=",".join(slice_)), key
        )
        if body is None:
            why = fail
            continue
        for item in body.get("items", []):
            if item.get("id"):
                got[item["id"]] = item
    return got, why


def api_channel_id(candidate, before_by_name):
    """그 후보의 **채널 번호**. 모르면 None.

    ⚠ **핸들로 찾지 않는다**(전달문 127의 1번) — 핸들은 날에 따라 엉뚱한
    채널로 풀린다(위 까닭). 번호는 둘 가운데서만 온다:

    | 어디서 | |
    |---|---|
    | 후보 명단의 `channel/UC…` | 사람이 적어 둔 번호다 |
    | **지금 목록에 있는 그 이름** | 전에 사람이 확인해 넣은 번호다 |
    """
    handle = candidate.get("handle") or ""
    found = re.search(r"(UC[A-Za-z0-9_-]{22})", handle)
    if found:
        return found.group(1)
    known = before_by_name.get(candidate["name"]) or {}
    got = known.get("id")
    return got if isinstance(got, str) and got.startswith("UC") else None


def inspect_by_api(candidates, before_by_name, fresh_days, today, key):
    """후보 전부를 **API 로** 확인한다.

    공개 쪽 길([inspect])과 **같은 것을 돌려준다** — `(passed, reasons,
    dormant)`. 그래서 이름 견주기·80%(b)·2주(a)·이슈(e)·빼기 후보(g)
    규칙은 **한 줄도 바뀌지 않는다.**
    """
    passed, reasons, dormant = {}, {}, {}

    # ① 번호를 모은다 — 모르는 후보는 그 자리에서 까닭을 적는다.
    ids, by_id = [], {}
    for candidate in candidates:
        channel_id = api_channel_id(candidate, before_by_name)
        if channel_id is None:
            reasons[candidate["name"]] = (
                "번호를 모름(후보 명단에 channel/UC… 로 적어 주십시오)"
            )
            continue
        if channel_id not in by_id:
            ids.append(channel_id)
        # 같은 번호를 두 후보가 가리키면 **둘 다** 본다.
        by_id.setdefault(channel_id, []).append(candidate)

    if not ids:
        return passed, reasons, dormant

    # ② channels.list — 있음 · 이름 · 업로드 목록 번호
    channels, why = api_pages(
        "channels",
        ids,
        {"part": "snippet,contentDetails,status"},
        key,
    )
    for channel_id in ids:
        if channel_id in channels:
            continue
        for candidate in by_id[channel_id]:
            reasons[candidate["name"]] = why or "API 에 그 채널이 없음"

    uploads = {}
    for channel_id, item in channels.items():
        snippet = item.get("snippet") or {}
        real = (snippet.get("title") or "").strip()
        playlist = (
            ((item.get("contentDetails") or {}).get("relatedPlaylists") or {})
        ).get("uploads")
        for candidate in by_id[channel_id]:
            if not matches(candidate.get("expect") or "", real):
                reasons[candidate["name"]] = "이름이 다름('%s')" % real[:20]
                continue
            if not playlist:
                reasons[candidate["name"]] = "업로드 목록이 없음"
                continue
            uploads[candidate["name"]] = (channel_id, real, playlist)

    # ③ playlistItems.list — 맨 위 영상의 제목과 올린 날
    tops = {}
    for name, (channel_id, real, playlist) in uploads.items():
        body, fail = api_get(
            "playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": playlist,
                "maxResults": API_RECENT,
            },
            key,
        )
        if body is None:
            reasons[name] = fail
            continue
        items = body.get("items") or []
        if not items:
            reasons[name] = "업로드 목록에 영상이 없음"
            continue
        first = items[0]
        snippet = first.get("snippet") or {}
        details = first.get("contentDetails") or {}
        video_id = (details.get("videoId") or "") or (
            (snippet.get("resourceId") or {}).get("videoId") or ""
        )
        title = (snippet.get("title") or "").strip()
        when = (
            details.get("videoPublishedAt") or snippet.get("publishedAt") or ""
        )[:10]
        if not video_id:
            reasons[name] = "영상 번호를 못 읽음"
            continue
        tops[name] = (channel_id, real, video_id, title, when)

    # ④ videos.list — **앱 안 재생**(embeddable)
    video_ids = [tops[name][2] for name in tops]
    videos, why = api_pages("videos", video_ids, {"part": "status"}, key)

    # ⑤ 규칙은 공개 쪽과 **같다** — 한국어 · 30일(새 후보만) · 1년(빼기 후보)
    for candidate in candidates:
        name = candidate["name"]
        if name not in tops or name in reasons:
            continue
        channel_id, real, video_id, title, when = tops[name]

        if candidate.get("korean", True) and not HANGUL.search(title):
            reasons[name] = "한국어 채널이 아닌 듯('%s')" % title[:20]
            continue

        asleep = None
        if when:
            try:
                days = (today - datetime.date.fromisoformat(when)).days
            except ValueError:
                days = 0
            if days > fresh_days:
                if name not in before_by_name:
                    reasons[name] = "최근 영상이 %s일 전(기준 %s일)" % (
                        days,
                        fresh_days,
                    )
                    continue
                if days > DORMANT_DAYS:
                    asleep = days

        status = (videos.get(video_id) or {}).get("status") or {}
        if video_id not in videos:
            reasons[name] = why or "API 에 그 영상이 없음"
            continue
        if status.get("embeddable") is False:
            reasons[name] = "앱 안 재생 막힘(embeddable=false)"
            continue

        passed[name] = {
            "id": channel_id,
            "name": name,
            "realName": real,
            "category": candidate["category"],
        }
        if asleep:
            dormant[name] = asleep

    return passed, reasons, dormant


def read_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:  # noqa: BLE001 — 처음 도는 날이면 없다
        return fallback


def write_json(path, document):
    folder = os.path.dirname(os.path.abspath(path))
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2) + "\n")


def tell(github_output, **values):
    """워크플로에 알려 준다(`GITHUB_OUTPUT`). 없으면 그냥 넘어간다."""
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in str(value):
                handle.write("%s<<VR_EOF\n%s\nVR_EOF\n" % (key, value))
            else:
                handle.write("%s=%s\n" % (key, value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="채널 목록 파일 자리")
    parser.add_argument("--candidates", default=os.path.join(HERE, "candidates.json"))
    parser.add_argument("--state", default=os.path.join(HERE, "state.json"))
    parser.add_argument("--dry", action="store_true", help="파일을 쓰지 않는다")
    parser.add_argument("--pause", type=float, default=0.4)
    args = parser.parse_args()

    today = datetime.date.today()
    book = read_json(args.candidates, None)
    if not book:
        print("후보 명단을 읽지 못했습니다:", args.candidates)
        return 2
    fresh_days = int(book.get("freshDays", 30))
    candidates = book.get("candidates", [])

    # c. 분야 다섯 밖의 값은 **거부한다**(앱의 `fromJson` 이 모르는 값을
    #    뉴스로 읽으므로, 애초에 들어가지 않게 여기서 막는다).
    unknown = sorted({c["category"] for c in candidates} - set(CATEGORIES))
    if unknown:
        print("모르는 분야가 후보 명단에 있습니다:", ", ".join(unknown))
        return 2

    before_doc = read_json(args.out, {})
    before = before_doc.get("channels", []) if isinstance(before_doc, dict) else []
    before_by_name = {item.get("name"): item for item in before}

    state = read_json(args.state, {})
    fails = dict(state.get("fails", {}))
    checked_on = state.get("checkedOn")

    # h. **키가 있으면 공식 API 로**(전달문 127) — 없으면 공개 쪽 그대로다.
    key = api_key()
    how = "공식 Data API" if key else "공개 쪽(RSS·채널 쪽)"
    print("확인하는 길: %s" % how)

    passed = {}
    reasons = {}
    # g. **오래 멈춘 기존 채널** — 빼지 않고 이슈에만 적는다(122의 2번).
    dormant = {}

    if key:
        passed, reasons, dormant = inspect_by_api(
            candidates, before_by_name, fresh_days, today, key
        )
        for candidate in candidates:
            name = candidate["name"]
            if name in passed:
                asleep = dormant.get(name)
                print("[o] %-16s %s  %s%s" % (
                    name,
                    passed[name]["id"],
                    passed[name]["realName"][:22],
                    "  (멈춘 지 %d일 — 빼기 후보)" % asleep if asleep else "",
                ))
            else:
                print("[x] %-16s %s" % (name, reasons.get(name, "확인 실패")))
    else:
        for candidate in candidates:
            known = candidate["name"] in before_by_name
            got, why, asleep = inspect(
                candidate, fresh_days, today, known=known
            )
            if got is None:
                reasons[candidate["name"]] = why
                print("[x] %-16s %s" % (candidate["name"], why))
            else:
                passed[candidate["name"]] = got
                if asleep:
                    dormant[candidate["name"]] = asleep
                print("[o] %-16s %s  %s%s" % (
                    candidate["name"],
                    got["id"],
                    got["realName"][:22],
                    "  (멈춘 지 %d일 — 빼기 후보)" % asleep if asleep else "",
                ))
            time.sleep(args.pause)

    print()
    print("통과 %d · 실패 %d (지난 목록 %d)" % (len(passed), len(reasons), len(before)))

    # b. **유튜브가 통째로 막힌 날에는 파일을 건드리지 않는다.**
    if before and len(passed) < len(before) * KEEP_AT_LEAST:
        note = "이번 주 통과 %d 개가 지난 목록 %d 개의 %d%% 밑이라 **파일을 쓰지 않았습니다**." % (
            len(passed),
            len(before),
            int(KEEP_AT_LEAST * 100),
        )
        print(note)
        body = note + "\n\n실패한 까닭:\n" + "\n".join(
            "- %s — %s" % (name, why) for name, why in sorted(reasons.items())
        )
        tell(
            os.environ.get("GITHUB_OUTPUT"),
            changed="false",
            issue="true",
            title="유튜브 채널 점검 — 통과가 너무 적어 건너뜀 (%s)" % today,
            body=body,
        )
        return 0

    # a. 이미 목록에 있는 채널은 **2주 연속** 실패해야 뺀다.
    kept_names = []
    dropped = []
    still_failing = []
    for item in before:
        name = item.get("name")
        if name in passed:
            fails.pop(name, None)
            kept_names.append(name)
            continue
        count = fails.get(name, 0) + 1
        fails[name] = count
        if count >= DROP_AFTER:
            dropped.append((name, reasons.get(name, "확인 실패")))
            fails.pop(name, None)
        else:
            kept_names.append(name)
            still_failing.append((name, reasons.get(name, "확인 실패"), count))

    # c. 후보가 통과하면 **그 분야 끝**에 넣는다.
    added = [
        name
        for name in passed
        if name not in before_by_name
    ]
    # 한 번도 목록에 없던 채널은 실패 횟수를 들고 있을 까닭이 없다.
    for name in list(fails):
        if name not in before_by_name:
            fails.pop(name, None)

    after = []
    for category in CATEGORIES:
        # ① 이미 있던 것은 **있던 차례 그대로**(사용자 차례가 흔들리지 않게).
        for name in kept_names:
            item = passed.get(name) or before_by_name.get(name)
            if item and item.get("category") == category:
                after.append(item)
        # ② 새로 들어온 것은 **그 분야 끝**에.
        for name in added:
            if passed[name]["category"] == category:
                after.append(passed[name])

    changed = [
        {k: v for k, v in item.items() if k in ("id", "name", "realName", "category")}
        for item in after
    ] != [
        {k: v for k, v in item.items() if k in ("id", "name", "realName", "category")}
        for item in before
    ]

    print("추가 %d · 빠짐 %d · 실패 중 %d · 빼기 후보 %d" % (
        len(added), len(dropped), len(still_failing), len(dormant)))
    for name in added:
        print("  추가: %s (%s)" % (name, passed[name]["category"]))
    for name, why in dropped:
        print("  빠짐: %s — %s (2주 연속)" % (name, why))
    for name, why, count in still_failing:
        print("  실패 중: %s — %s (%d주째, 2주째에 뺍니다)" % (name, why, count))
    for name, days in sorted(dormant.items()):
        print("  빼기 후보: %s — 새 영상이 %d일째 없습니다(저절로 빼지 않습니다)"
              % (name, days))

    document = {
        "_comment": before_doc.get(
            "_comment",
            "'유튜브' 탭의 공식 채널. 매주 깃허브 액션이 확인해서 만든다 — "
            "손으로 적지 않는다(전달문 121).",
        ),
        "fetchedOn": today.isoformat(),
        "channels": after,
    }

    # e. 2주 넘게 확인을 못 했으면 알린다.
    stale = False
    if checked_on:
        try:
            stale = (today - datetime.date.fromisoformat(checked_on)).days > STALE_DAYS
        except ValueError:
            stale = False

    if not args.dry:
        if changed:
            write_json(args.out, document)
        write_json(
            args.state,
            {
                "_comment": "채널마다 **연속 실패 횟수**(2주 규칙용)와 마지막 확인 날.",
                "checkedOn": today.isoformat(),
                "fails": fails,
            },
        )

    lines = []
    lines.append("확인하는 길: **%s**" % how)
    if added:
        lines.append("**추가** " + ", ".join(added))
    if dropped:
        lines.append("**빠짐** " + ", ".join("%s(%s)" % (n, w) for n, w in dropped))
    if still_failing:
        lines.append(
            "**실패 중** "
            + ", ".join("%s(%s · %d주째)" % (n, w, c) for n, w, c in still_failing)
        )
    if stale:
        lines.append("(!) 마지막 확인이 %s 입니다 — %d일이 넘었습니다." % (checked_on, STALE_DAYS))

    tell(
        os.environ.get("GITHUB_OUTPUT"),
        changed="true" if changed else "false",
        issue="true" if (changed or stale) else "false",
        title="유튜브 채널 점검 — 추가 %d · 빠짐 %d · 실패 중 %d (%s)"
        % (len(added), len(dropped), len(still_failing), today),
        body="\n".join(lines) or "바뀐 것이 없습니다.",
        summary="추가 %d · 빠짐 %d · 실패 중 %d" % (len(added), len(dropped), len(still_failing)),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
