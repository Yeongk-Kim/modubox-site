# -*- coding: utf-8 -*-
"""해외(미국) 러너에서 **라디오 소리 주소가 열리는지** 주 1회 재어 본다.

보고_162 의 판단 ⑤ '나' — 사장님 결정(11/16 13:11):
*"해외 확인은 가(교민 베타 1명)+나(주 1회 소리 점검 액션), unknown 유지."*
대상을 **소리가 있는 카드 전부**(국내 35 + 해외 5)로 넓힌 것은 사장님
결정(11/21 06:57 · 안1 · 보는 라디오 전달문 177)이다.

```
python check_overseas_sound.py                      # 지금 자리에서 그대로
python check_overseas_sound.py --selftest           # 셈만 시험한다(바깥 연결 0)
```

| 지키는 것 | |
|---|---|
| **비밀값 0** | 키도 토큰도 쓰지 않는다(이슈를 여는 `GITHUB_TOKEN` 은 액션이 준다) |
| **표준 라이브러리만** | 러너에 설치하는 것이 없다 |
| **받는 양** | 소리는 **2KB 까지**(`MAX_BODY`) · 조회·재생목록은 **64KB 까지** · 한 걸음 8초 |
| **보내는 값 0** | 주소만 열어 본다 — 사용자 정보도 식별 값도 싣지 않는다 |
| ⚠ **값을 지어내지 않는다** | 열렸는지 모르면 `unknown` 이다(`assets/SOURCES.md` 의 그 칸도 그대로 둔다) |
| ⚠ **유튜브는 재지 않는다** | 러너 IP 가 막힌다(전달문 127에서 통과 0/49) — 영상 쪽은 `../youtube_check/check_region.py` 가 **API 로 설정 값만** 읽는다 |

## 두 걸음이다 — 조회 → 재생 (전달문 177의 1-2)

국내 방송사 넷(KBS · MBC · SBS · cpbc)은 **지금 재생 주소를 한 번 더
물어본다**. 앱 부품 `StreamResolver` 와 **같은 뜻**으로 푼다:

| `streamLookup` | 푸는 법 |
|---|---|
| `{"kind":"json","path":"channel_item.0.service_url"}` | KBS — JSON 의 그 자리 |
| `{"kind":"json","path":"onair.source.mediasource.mediaurl"}` | SBS · cpbc — 같은 길, 자리만 다르다 |
| `{"kind":"text"}` | MBC — 몸통이 곧 주소다(sredirect) |
| 없음 | `streamUrl` 이 **바로 재생 주소**다 |

⚠ **그래서 결과를 두 단계로 가른다** — `조회 거절`(① 방송사 API 가
막았다)과 `소리 거절`(② 조회는 됐는데 그 주소가 막혔다)은 **다른
일**이다. 해외에서 막힌 것인지 그냥 죽은 주소인지는 이 구분이 있어야
가릴 수 있다.

⚠ **`http://` 로 온 주소는 `https://` 로 바꿔 연다** — 앱과 같다
(보는 라디오 CLAUDE.md 23장 · cpbc 가 평문으로 준다).

## HLS(.m3u8)는 **첫 조각 하나까지** 간다

재생목록은 글이라 그것만 받아서는 '소리가 흘렀다'고 할 수 없다. 그래서
재생목록 → (여러 품질이면) 첫 갈래 → **첫 조각**을 받아 본다(그 조각도
2KB 까지다).

⚠ **`ICY 200 OK` 를 받아야 한다** — Radio Korea LA(SHOUTcast)는 첫 줄이
보통 HTTP 가 아니라서 `urllib`·`http.client` 가 통째로 터진다(`curl` 도
`--http0.9` 없이는 못 받는다 · `assets/SOURCES.md`). 그래서 **소리를 받는
자리**는 생 소켓 + TLS 로 직접 한 줄을 읽는다(조회·재생목록은 보통
HTTP 라 `urllib` 그대로다).

⚠ **목록을 손으로 적지 않는다** — `streams.json` 은 보는 라디오 저장소의
`python tools/build_overseas_check.py` 가 `assets/audio_streams.json` 과
`assets/channels.json` 에서 만든다. 카드가 늘면 그 도구를 한 번 돌려
이 폴더의 파일을 바꿔 넣는다(사람이 고치는 자리가 아니다).
"""

import argparse
import datetime
import io
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TIMEOUT = 8.0          # 한 걸음에 쓰는 시간
MAX_BODY = 2048        # 소리는 2KB 만 받아 본다
MAX_TEXT = 65536       # 조회 응답·재생목록은 글이라 조금 넉넉히
SOUND_LEAST = 512      # 이만큼 받으면 '소리가 흐른다'로 본다
AGENT = "ModuBoxVisualRadioCheck/1.0 (+https://modubox.app)"

# 결과 네 가지 — 표와 state 가 **같은 말**을 쓴다.
OPEN = "열림"
LOOKUP_NO = "조회 거절"
SOUND_NO = "소리 거절"
SLOW = "시간 초과"

GROUP_WORD = {"domestic": "국내", "overseas": "해외"}


def secure(url):
    """⚠ `http://` 는 `https://` 로 바꿔 연다 — 앱과 같다(23장)."""
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def looks_slow(why):
    """그 까닭이 '시간 초과' 인가 — 번호가 아니라 말로 온다."""
    return "timeout" in (why or "").lower() or "timed out" in (why or "").lower()


def status_of(first_line):
    """첫 줄에서 번호를 읽는다 — `HTTP/1.1 200 OK` 와 `ICY 200 OK` 둘 다."""
    parts = first_line.strip().split()
    if len(parts) < 2:
        return None, first_line.strip()
    try:
        return int(parts[1]), parts[0]
    except ValueError:
        return None, parts[0]


def headers_of(blob):
    """머리글을 소문자 이름으로 모은다(값은 그대로)."""
    out = {}
    for line in blob.split("\r\n")[1:]:
        if not line or ":" not in line:
            continue
        name, _, value = line.partition(":")
        out[name.strip().lower()] = value.strip()
    return out


def pick_path(body, path):
    """`channel_item.0.service_url` 처럼 점으로 끊은 자리를 따라 들어간다.

    부품 `StreamResolver.pickPath` 와 **같은 셈**이다(두 벌로 두지 않는다).
    """
    if not path:
        return None, "json 인데 path 가 없다"
    try:
        node = json.loads(body)
    except Exception as error:          # noqa: BLE001
        return None, "JSON 이 아니다: %s" % type(error).__name__
    for part in path.split("."):
        if isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            node = None
        if node is None:
            return None, "%s 자리가 비었다" % path
    if not isinstance(node, str):
        return None, "%s 가 글자가 아니다" % path
    return node, None


def first_uri(text):
    """재생목록에서 **첫 주소 한 줄**과 '여러 품질인가'를 돌려준다."""
    master = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith("#EXT-X-STREAM-INF"):
                master = True
            continue
        return line, master
    return None, master


def looks_m3u8(url):
    """주소 끝이 `.m3u8` 인가(물음표 뒤는 보지 않는다)."""
    return urllib.parse.urlparse(url).path.lower().endswith(".m3u8")


def is_playlist(url, got):
    """그 응답이 HLS 재생목록인가 — 주소 끝과 종류를 함께 본다."""
    if looks_m3u8(url):
        return True
    kind = (got.get("type") or "").lower()
    return "mpegurl" in kind or "m3u8" in kind


def fetch_text(url, timeout=TIMEOUT):
    """조회 주소·재생목록을 받는다 — 보통 HTTP 라 `urllib` 그대로다."""
    url = secure(url)
    request = urllib.request.Request(
        url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_TEXT)
            return {"status": response.getcode(), "bytes": len(raw),
                    "text": raw.decode("utf-8", "replace"), "why": None,
                    "url": url}
    except urllib.error.HTTPError as error:
        return {"status": error.code, "bytes": 0, "text": "",
                "why": "번호 %s" % error.code, "url": url}
    except Exception as error:          # noqa: BLE001 — 까닭을 그대로 적는다
        return {"status": None, "bytes": 0, "text": "",
                "why": "%s: %s" % (type(error).__name__, error), "url": url}


def listen(url, timeout=TIMEOUT):
    """주소를 열어 **첫 줄 · 머리글 · 받은 소리**를 돌려준다.

    ⚠ 생 소켓 + TLS 다 — `ICY 200 OK`(SHOUTcast) 때문이다(맨 위 ⚠).
    """
    url = secure(url)
    if not url.startswith("https://"):
        return {"ok": False, "why": "https 가 아니다", "status": None,
                "bytes": 0, "got": 0, "raw": b""}

    rest = url[len("https://"):]
    host_port, _, path = rest.partition("/")
    host, _, port = host_port.partition(":")
    port = int(port) if port else 443
    request = (
        "GET /%s HTTP/1.0\r\nHost: %s\r\nUser-Agent: %s\r\n"
        "Icy-MetaData: 1\r\nAccept: */*\r\nConnection: close\r\n\r\n"
        % (path, host_port, AGENT)
    )

    raw = b""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                tls.sendall(request.encode("ascii"))
                while len(raw) < MAX_BODY + 4096:
                    try:
                        chunk = tls.recv(4096)
                    except (socket.timeout, ssl.SSLError):
                        break               # 소리는 끝없이 온다 — 끊는 것이 정상이다
                    if not chunk:
                        break
                    raw += chunk
    except Exception as error:              # noqa: BLE001 — 까닭을 그대로 적는다
        return {"ok": False, "why": "%s: %s" % (type(error).__name__, error),
                "status": None, "bytes": 0, "got": 0, "raw": b""}

    split = raw.find(b"\r\n\r\n")
    head = raw[:split if split >= 0 else len(raw)].decode("latin-1")
    body = raw[split + 4:] if split >= 0 else b""
    status, kind = status_of(head.split("\r\n")[0])
    fields = headers_of(head)
    return {
        "ok": status == 200 and len(body) >= SOUND_LEAST,
        "status": status,
        "kind": kind,                        # `HTTP/1.1` 또는 `ICY`
        "type": fields.get("content-type"),
        "icyName": fields.get("icy-name"),
        "bytes": len(body),
        "got": len(raw),                     # 머리글까지 **받은 총량**
        "raw": body,
        "why": None if status == 200 else "번호 %s" % status,
    }


def sound_of(url, budget):
    """그 주소에서 **소리가 흘렀나**. HLS 면 첫 조각까지 따라간다.

    `budget` 은 받은 바이트를 적어 두는 그릇이다(한 주 양을 세려고).
    """
    here = secure(url)

    # ① 재생목록이라고 **주소에 적혀 있으면** 글로 받는다(소리가 아니다).
    text = None
    if looks_m3u8(here):
        step = fetch_text(here)
        budget["bytes"] += step["bytes"]
        if step["status"] != 200:
            return ({"ok": False, "status": step["status"], "kind": "HTTP",
                     "type": None, "bytes": 0, "got": step["bytes"],
                     "raw": b"",
                     "why": step["why"] or "재생목록 번호 %s" % step["status"]},
                    here)
        text = step["text"]
    else:
        got = listen(here)
        budget["bytes"] += got.get("got", 0)
        if not is_playlist(here, got):
            return got, here                 # 보통 스트림이다 — 여기서 끝
        if got.get("status") != 200:
            return got, here
        text = got["raw"].decode("utf-8", "replace")

    # ② 재생목록을 따라 **첫 조각**까지 간다(여러 품질이면 한 번 더).
    for _step in range(2):
        uri, _master = first_uri(text or "")
        if not uri:
            return ({"ok": False, "status": 200, "kind": "HTTP", "type": None,
                     "bytes": 0, "got": 0, "raw": b"",
                     "why": "재생목록이 비었다"}, here)
        here = urllib.parse.urljoin(here, uri)
        if looks_m3u8(here):
            step = fetch_text(here)
            budget["bytes"] += step["bytes"]
            if step["status"] != 200:
                return ({"ok": False, "status": step["status"], "kind": "HTTP",
                         "type": None, "bytes": 0, "got": step["bytes"],
                         "raw": b"",
                         "why": step["why"] or "재생목록 번호 %s"
                                % step["status"]}, here)
            text = step["text"]
            continue
        got = listen(here)                   # 이것이 조각이다 — 소리를 받는다
        budget["bytes"] += got.get("got", 0)
        return got, here

    return ({"ok": False, "status": None, "kind": "HTTP", "type": None,
             "bytes": 0, "got": 0, "raw": b"",
             "why": "재생목록이 너무 깊다"}, here)


def probe(item, budget):
    """카드 하나를 잰다 — 조회(있으면) → 재생. 결과 한 꾸러미."""
    started = time.time()
    lookup = item.get("lookup")
    play = item["url"]
    out = {"how": "고정", "lookupStatus": None, "lookupWhy": None}

    if lookup:
        out["how"] = "조회"
        asked = fetch_text(item["url"])
        budget["bytes"] += asked["bytes"]
        out["lookupStatus"] = asked["status"]
        if asked["status"] != 200:
            out.update(result=SLOW if looks_slow(asked["why"]) else LOOKUP_NO,
                       lookupWhy=asked["why"], status=asked["status"],
                       bytes=0, took=time.time() - started, url=item["url"])
            return out
        if lookup.get("kind") == "text":
            found = asked["text"].strip()
            why = None if found else "몸통이 비었다"
            found = found or None
        else:
            found, why = pick_path(asked["text"], lookup.get("path"))
        if found is None or "://" not in found:
            out.update(result=LOOKUP_NO, lookupWhy=why or "주소가 아니다",
                       status=asked["status"], bytes=0,
                       took=time.time() - started, url=item["url"])
            return out
        play = found

    got, where = sound_of(play, budget)
    if got["ok"]:
        result = OPEN
    elif looks_slow(got.get("why")):
        result = SLOW
    else:
        result = SOUND_NO
    out.update(result=result, status=got.get("status"),
               kind=got.get("kind"), type=got.get("type"),
               icyName=got.get("icyName"), bytes=got.get("bytes", 0),
               why=got.get("why"), took=time.time() - started,
               url=where or play)
    return out


def tell(github_output, **values):
    """워크플로에 알려 준다(`GITHUB_OUTPUT`). 없으면 그냥 넘어간다."""
    if not github_output:
        return
    with io.open(github_output, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in str(value):
                handle.write("%s<<VR_EOF\n%s\nVR_EOF\n" % (key, value))
            else:
                handle.write("%s=%s\n" % (key, value))


def report_text(today, where, rows, kilobytes):
    opened = sum(1 for row in rows if row["got"]["result"] == OPEN)
    lines = [
        "# 라디오 소리 주소 점검 (주 1회)",
        "",
        "보는 라디오 보고_162 의 판단 ⑤ '나' + 전달문 177(안1). **미국",
        "러너에서** 소리 주소를 열어 보고 적는다 — 유튜브(영상)는 여기서",
        "재지 않는다(`../youtube_check/region_report.md` 가 **API 로 설정",
        "값만** 읽는다).",
        "",
        "| 잰 날 | 러너 자리 | 열림 | 받은 양 |",
        "|---|---|---|---|",
        "| %s | %s | %d / %d | %.0fKB |" % (today, where, opened, len(rows),
                                            kilobytes),
        "",
        "| 카드 | 이름 | 묶음 | 방식 | 결과 | 응답 코드 | 첫 소리까지 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        got = row["got"]
        if got["result"] == LOOKUP_NO:
            code = "조회 %s" % (got.get("lookupStatus") or "—")
        elif got.get("status"):
            code = "%s %s" % (got.get("kind") or "HTTP", got["status"])
        else:
            code = "—"
        last = ("%.1f초" % got["took"]) if got["result"] == OPEN else (
            got.get("lookupWhy") or got.get("why") or "—")
        lines.append("| `%s` | %s | %s | %s | **%s** | %s | %s |" % (
            row["card"], row["cardName"],
            GROUP_WORD.get(row["group"], row["group"]),
            got["how"], got["result"], code, last))
    lines += [
        "",
        "## 결과 네 가지",
        "",
        "| | 뜻 |",
        "|---|---|",
        "| **열림** | 소리가 %d바이트 넘게 흘렀다 |" % SOUND_LEAST,
        "| **조회 거절** | ① 방송사 **조회 API** 가 막았다(해외 막힘이면 여기다) |",
        "| **소리 거절** | ② 조회는 됐는데 **그 소리 주소**가 막혔다 |",
        "| **시간 초과** | %d초 안에 답이 없었다 |" % int(TIMEOUT),
        "",
        "- ⚠ **'열림이 아니다'가 곧 '해외에서 안 된다'는 뜻은 아니다** —",
        "  그 주소가 그 시각에 응답하지 않았다는 뜻이다. 두 주 잇달아",
        "  그러면 사람이 본다.",
        "- ⚠ **러너는 데이터센터 IP 다** — 가정용 망과 다를 수 있다.",
        "  교민 베타 한 분('가')이 폰에서 보는 것과 **함께** 읽는다.",
        "- ⚠ 이 표로 `assets/SOURCES.md` 의 `overseas` 칸을 **곧바로**",
        "  채우지 않는다 — 그 칸은 **영상까지** 되는지를 말한다.",
        "- ⚠ 소리 번호를 **나눠 쓰는 카드**가 있다(`mbc-trot` 과 `mbc-sfm`).",
        "  그런 카드는 줄이 둘이지만 **한 번만** 열어 본다.",
    ]
    return "\n".join(lines) + "\n"


def selftest():
    """셈만 시험한다 — **바깥에 연결하지 않는다.**"""
    bad = [0]

    def same(what, got, want):
        if got != want:
            bad[0] += 1
            print("   %s -> %r (바라던 것 %r)" % (what, got, want))

    for line, want in [
        ("HTTP/1.1 200 OK", (200, "HTTP/1.1")),
        ("ICY 200 OK", (200, "ICY")),          # ⚠ Radio Korea LA 가 이것이다
        ("HTTP/1.1 403 Forbidden", (403, "HTTP/1.1")),
        ("HTTP/1.0 404 Not Found", (404, "HTTP/1.0")),
        ("쓰레기", (None, "쓰레기")),
    ]:
        same("첫 줄 '%s'" % line, status_of(line), want)

    head = "ICY 200 OK\r\nicy-name: rainfm\r\nContent-Type: audio/mpeg\r\n"
    fields = headers_of(head)
    same("머리글 icy-name", fields.get("icy-name"), "rainfm")
    same("머리글 content-type", fields.get("content-type"), "audio/mpeg")

    # 조회 — 앱 부품 `StreamResolver` 와 같은 뜻인가(전달문 177의 1-2).
    kbs = '{"channel_item":[{"service_url":"https://a/b.m3u8"}]}'
    same("KBS 길", pick_path(kbs, "channel_item.0.service_url"),
         ("https://a/b.m3u8", None))
    sbs = '{"onair":{"source":{"mediasource":{"mediaurl":"http://c/d"}}}}'
    same("SBS·cpbc 길", pick_path(sbs, "onair.source.mediasource.mediaurl"),
         ("http://c/d", None))
    same("빈 자리", pick_path('{"onair":{}}', "onair.source.x")[0], None)
    same("JSON 이 아님", pick_path("<html>", "a.b")[0], None)
    same("path 없음", pick_path("{}", None)[0], None)

    # ⚠ http -> https (앱과 같다 · 23장)
    same("평문 바꾸기", secure("http://c/d"), "https://c/d")
    same("https 그대로", secure("https://c/d"), "https://c/d")

    # HLS — 여러 품질(master)과 조각 목록을 가린다.
    master = ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=64000\nlow.m3u8\n"
              "#EXT-X-STREAM-INF:BANDWIDTH=128000\nhigh.m3u8\n")
    same("여러 품질", first_uri(master), ("low.m3u8", True))
    media = "#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nseg1.aac\n"
    same("조각 목록", first_uri(media), ("seg1.aac", False))
    same("빈 목록", first_uri("#EXTM3U\n"), (None, False))
    same("이어 붙이기",
         urllib.parse.urljoin("https://a/x/y.m3u8", "seg1.aac"),
         "https://a/x/seg1.aac")
    same("재생목록인가(끝)", is_playlist("https://a/b.m3u8?t=1", {}), True)
    same("재생목록인가(종류)",
         is_playlist("https://a/b", {"type": "application/vnd.apple.mpegurl"}),
         True)
    same("소리다", is_playlist("https://a/b.aac", {"type": "audio/aac"}), False)

    same("시간 초과 가리기", looks_slow("TimeoutError: timed out"), True)
    same("시간 초과 아님", looks_slow("번호 403"), False)

    if listen("ftp://example.com/x")["ok"]:
        bad[0] += 1
        print("   https 가 아닌 주소를 열었다고 했다")

    print("셈 시험 — %s" % ("모두 통과" if not bad[0]
                           else "**%d 개 어긋남**" % bad[0]))
    return 1 if bad[0] else 0


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--list", default=os.path.join(here, "streams.json"))
    parser.add_argument("--state", default=os.path.join(here, "state.json"))
    parser.add_argument("--report", default=os.path.join(here, "report.md"))
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    with io.open(args.list, encoding="utf-8") as handle:
        wanted = json.load(handle)["streams"]
    state = {}
    if os.path.exists(args.state):
        with io.open(args.state, encoding="utf-8") as handle:
            state = json.load(handle)

    today = datetime.date.today().isoformat()
    # ⚠ **러너가 어느 나라인지 지어내지 않는다**(0장) — 액션이 적어 준
    #   값을 그대로 쓰고, 없으면 '모름' 이다(이 PC 에서 돌려 볼 때가 그렇다).
    where = os.environ.get("VR_RUNNER_PLACE", "모름(액션 밖에서 돌렸다)")

    budget = {"bytes": 0}
    rows = []
    seen = {}                       # ⚠ **같은 소리 번호는 한 번만 연다**
    for item in wanted:
        got = seen.get(item["id"])
        if got is None:
            got = probe(item, budget)
            seen[item["id"]] = got
        rows.append(dict(item, got=got))
        print("%-4s %-22s %-26s %-9s %s"
              % (GROUP_WORD.get(item["group"], item["group"]), item["card"],
                 item["id"], got["result"],
                 got.get("lookupWhy") or got.get("why") or ""))

    for stream_id, got in seen.items():
        was = state.get(stream_id, {})
        fails = 0 if got["result"] == OPEN else int(was.get("fails", 0)) + 1
        state[stream_id] = {
            "lastCheckedOn": today,
            "ok": got["result"] == OPEN,
            "result": got["result"],
            "fails": fails,
            "status": got.get("status"),
        }

    kilobytes = budget["bytes"] / 1024.0
    text = report_text(today, where, rows, kilobytes)
    before = ""
    if os.path.exists(args.report):
        before = io.open(args.report, encoding="utf-8").read()

    # ⚠ **잰 날·받은 양·걸린 시간만 다른 것은 '바뀜'으로 세지 않는다** —
    #   그러면 주마다 커밋이 쌓인다. 결과가 달라진 날에만 적는다.
    def body_of(blob):
        out = []
        for line in blob.splitlines():
            if line.startswith("| 20"):
                continue
            if line.startswith("| `"):
                line = "|".join(line.split("|")[:6])   # '첫 소리까지' 를 뺀다
            out.append(line)
        return "\n".join(out)

    changed = body_of(text) != body_of(before)

    with io.open(args.report, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(args.state, "w", encoding="utf-8", newline="") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")

    failing = [row for row in rows if row["got"]["result"] != OPEN]
    twice = [row for row in rows
             if int(state[row["id"]].get("fails", 0)) >= 2]
    lines = ["라디오 소리 주소 점검 — %s (%s)" % (today, where), ""]
    if failing:
        lines.append("## 열리지 않은 주소")
        for row in failing:
            got = row["got"]
            lines.append("- `%s` %s (%s) — **%s** %s" % (
                row["card"], row["cardName"],
                GROUP_WORD.get(row["group"], row["group"]), got["result"],
                got.get("lookupWhy") or got.get("why") or "까닭을 모름"))
    if twice:
        lines += ["", "## **두 주 잇달아** 열리지 않음 — 사람이 볼 것"]
        for row in twice:
            lines.append("- `%s` %s (%d 주)" % (
                row["card"], row["cardName"], state[row["id"]]["fails"]))
    if not failing:
        lines.append("모두 열렸습니다.")
    lines += ["", "표: `tools/overseas_check/report.md`",
              "받은 양: 약 %.0fKB" % kilobytes]

    print("\n%s" % "\n".join(lines))
    tell(
        os.environ.get("GITHUB_OUTPUT"),
        changed="true" if changed else "false",
        issue="true" if failing else "false",
        title="라디오 소리 점검 — 열림 %d / %d (%s)"
              % (len(rows) - len(failing), len(rows), today),
        body="\n".join(lines),
        summary="열림 %d / %d" % (len(rows) - len(failing), len(rows)),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
