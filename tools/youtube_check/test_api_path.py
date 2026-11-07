"""**공식 Data API 길**을 가짜 응답으로 시험한다 (보는 라디오 전달문 127).

⚠ **진짜 키로는 돌리지 않는다.** 키를 읽지도 적지도 않는다 — `api_get` 을
갈아 끼워 **우리가 만든 응답**만 돌려준다.

쓰는 법(표준 라이브러리만 쓴다 — 설치할 것이 없다):

    python -m unittest test_api_path -v
    python test_api_path.py
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_youtube_channels as checker  # noqa: E402

TODAY = datetime.date(2026, 11, 7)

# 후보 넷 — 번호로 적은 것 둘, 핸들만 적은 것 하나, 목록에 있는 것 하나.
CANDIDATES = [
    {
        "category": "news",
        "name": "번호로",
        "handle": "channel/UCaaaaaaaaaaaaaaaaaaaaaa",
        "expect": "가 뉴스",
        "korean": True,
    },
    {
        "category": "music",
        "name": "목록에 있는",
        "handle": "@onlyhandle",
        "expect": "나 음악",
        "korean": True,
    },
    {
        "category": "show",
        "name": "핸들만",
        "handle": "@nowhere",
        "expect": "다 예능",
        "korean": True,
    },
]

BEFORE = {
    "목록에 있는": {
        "id": "UCbbbbbbbbbbbbbbbbbbbbbb",
        "name": "목록에 있는",
        "realName": "나 음악",
        "category": "music",
    },
}


def _channel(channel_id, title, uploads="UU" + "x" * 22):
    return {
        "id": channel_id,
        "snippet": {"title": title},
        "contentDetails": {"relatedPlaylists": {"uploads": uploads}},
        "status": {"privacyStatus": "public"},
    }


def _item(video_id, title, when):
    return {
        "snippet": {
            "title": title,
            "publishedAt": when + "T00:00:00Z",
            "resourceId": {"videoId": video_id},
        },
        "contentDetails": {"videoId": video_id, "videoPublishedAt": when + "T00:00:00Z"},
    }


class FakeApi:
    """`api_get` 을 갈아 끼운다 — **망에 나가지 않는다.**"""

    def __init__(self, channels, items, videos, fail=None):
        self.channels = channels
        self.items = items
        self.videos = videos
        self.fail = fail or {}
        # 부른 횟수 — '쓰는 양'을 보고에 적으려고 센다.
        self.calls = {"channels": 0, "playlistItems": 0, "videos": 0}
        self.keys_seen = []

    def __call__(self, what, params, key, timeout=25):
        self.calls[what] = self.calls.get(what, 0) + 1
        self.keys_seen.append(key)
        if what in self.fail:
            return None, self.fail[what]
        if what == "channels":
            ids = params["id"].split(",")
            return {
                "items": [self.channels[i] for i in ids if i in self.channels]
            }, None
        if what == "playlistItems":
            got = self.items.get(params["playlistId"])
            return {"items": got or []}, None
        if what == "videos":
            ids = params["id"].split(",")
            return {
                "items": [
                    {"id": i, "status": {"embeddable": self.videos.get(i, True)}}
                    for i in ids
                    if i in self.videos
                ]
            }, None
        raise AssertionError("모르는 부름: %s" % what)


class ApiPathTest(unittest.TestCase):
    def setUp(self):
        self.real = checker.api_get
        self.addCleanup(lambda: setattr(checker, "api_get", self.real))

    def run_with(self, fake, candidates=None, before=None, fresh_days=30):
        checker.api_get = fake
        return checker.inspect_by_api(
            candidates if candidates is not None else CANDIDATES,
            BEFORE if before is None else before,
            fresh_days,
            TODAY,
            "가짜키",
        )

    # ─────────────────────────── ① 번호 ───────────────────────────

    def test_번호는_명단이나_지금_목록에서만_온다(self):
        """⚠ **핸들로 찾지 않는다** — 날에 따라 엉뚱한 채널로 풀린다."""
        self.assertEqual(
            checker.api_channel_id(CANDIDATES[0], BEFORE),
            "UCaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.assertEqual(
            checker.api_channel_id(CANDIDATES[1], BEFORE),
            "UCbbbbbbbbbbbbbbbbbbbbbb",
        )
        self.assertIsNone(checker.api_channel_id(CANDIDATES[2], BEFORE))

    def test_번호를_모르면_까닭을_적고_넘어간다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "가 뉴스", "UUa"
                ),
                "UCbbbbbbbbbbbbbbbbbbbbbb": _channel(
                    "UCbbbbbbbbbbbbbbbbbbbbbb", "나 음악", "UUb"
                ),
            },
            {
                "UUa": [_item("v1", "가 뉴스 오늘", "2026-11-06")],
                "UUb": [_item("v2", "나 음악 오늘", "2026-11-05")],
            },
            {"v1": True, "v2": True},
        )
        passed, reasons, dormant = self.run_with(fake)
        self.assertEqual(sorted(passed), ["목록에 있는", "번호로"])
        self.assertIn("핸들만", reasons)
        self.assertIn("번호를 모름", reasons["핸들만"])
        self.assertEqual(dormant, {})

    # ────────────────────── ② 규칙은 그대로다 ──────────────────────

    def test_이름이_다르면_버린다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "byung joo lee", "UUa"
                ),
            },
            {"UUa": [_item("v1", "가 뉴스 오늘", "2026-11-06")]},
            {"v1": True},
        )
        passed, reasons, _ = self.run_with(fake, candidates=[CANDIDATES[0]])
        self.assertEqual(passed, {})
        self.assertIn("이름이 다름", reasons["번호로"])

    def test_이름은_목록으로도_적을_수_있다(self):
        """⚠ 유튜브가 날에 따라 한국어·영어 이름을 번갈아 준다."""
        candidate = dict(CANDIDATES[0], expect=["가 뉴스", "GA NEWS"])
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "GA NEWS", "UUa"
                ),
            },
            {"UUa": [_item("v1", "가 뉴스 오늘", "2026-11-06")]},
            {"v1": True},
        )
        passed, _, _ = self.run_with(fake, candidates=[candidate])
        self.assertIn("번호로", passed)

    def test_한국어가_아니면_버린다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "가 뉴스", "UUa"
                ),
            },
            {"UUa": [_item("v1", "MBC news in Arabic", "2026-11-06")]},
            {"v1": True},
        )
        passed, reasons, _ = self.run_with(fake, candidates=[CANDIDATES[0]])
        self.assertEqual(passed, {})
        self.assertIn("한국어", reasons["번호로"])

    def test_앱_안_재생이_막히면_버린다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "가 뉴스", "UUa"
                ),
            },
            {"UUa": [_item("v1", "가 뉴스 오늘", "2026-11-06")]},
            {"v1": False},
        )
        passed, reasons, _ = self.run_with(fake, candidates=[CANDIDATES[0]])
        self.assertEqual(passed, {})
        self.assertIn("앱 안 재생 막힘", reasons["번호로"])

    def test_새_후보는_30일_넘으면_넣지_않는다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "가 뉴스", "UUa"
                ),
            },
            {"UUa": [_item("v1", "가 뉴스 옛것", "2026-01-01")]},
            {"v1": True},
        )
        passed, reasons, _ = self.run_with(fake, candidates=[CANDIDATES[0]])
        self.assertEqual(passed, {})
        self.assertIn("최근 영상이", reasons["번호로"])

    def test_이미_있는_채널은_오래_멈춰도_빼지_않고_후보로만_적는다(self):
        """g 규칙 — 1년을 넘으면 '빼기 후보' 이슈에만 적는다(122의 2번)."""
        fake = FakeApi(
            {
                "UCbbbbbbbbbbbbbbbbbbbbbb": _channel(
                    "UCbbbbbbbbbbbbbbbbbbbbbb", "나 음악", "UUb"
                ),
            },
            {"UUb": [_item("v2", "나 음악 아주 옛것", "2016-01-01")]},
            {"v2": True},
        )
        passed, reasons, dormant = self.run_with(
            fake, candidates=[CANDIDATES[1]]
        )
        self.assertIn("목록에 있는", passed)
        self.assertNotIn("목록에 있는", reasons)
        self.assertGreater(dormant["목록에 있는"], checker.DORMANT_DAYS)

    def test_이미_있는_채널은_30일과_1년_사이면_조용하다(self):
        fake = FakeApi(
            {
                "UCbbbbbbbbbbbbbbbbbbbbbb": _channel(
                    "UCbbbbbbbbbbbbbbbbbbbbbb", "나 음악", "UUb"
                ),
            },
            {"UUb": [_item("v2", "나 음악 두 달 전", "2026-09-01")]},
            {"v2": True},
        )
        passed, _, dormant = self.run_with(fake, candidates=[CANDIDATES[1]])
        self.assertIn("목록에 있는", passed)
        self.assertEqual(dormant, {})

    # ───────────────────── ③ 못 받았을 때 ─────────────────────

    def test_channels가_엎어지면_까닭을_그대로_적는다(self):
        fake = FakeApi({}, {}, {}, fail={"channels": "API channels HTTP 403"})
        passed, reasons, _ = self.run_with(fake)
        self.assertEqual(passed, {})
        self.assertIn("HTTP 403", reasons["번호로"])
        # ⚠ **까닭에 키가 섞이지 않는다.**
        for why in reasons.values():
            self.assertNotIn("가짜키", why)

    def test_업로드_목록이_비면_넣지_않는다(self):
        fake = FakeApi(
            {
                "UCaaaaaaaaaaaaaaaaaaaaaa": _channel(
                    "UCaaaaaaaaaaaaaaaaaaaaaa", "가 뉴스", "UUa"
                ),
            },
            {"UUa": []},
            {},
        )
        passed, reasons, _ = self.run_with(fake, candidates=[CANDIDATES[0]])
        self.assertEqual(passed, {})
        self.assertIn("영상이 없음", reasons["번호로"])

    # ───────────────────── ④ 쓰는 양 ─────────────────────

    def test_쓰는_양은_채널마다_하나에_묶음_둘이다(self):
        """channels 1 + playlistItems N + videos 1 (채널 50개까지)."""
        channels, items, videos, many = {}, {}, {}, []
        for i in range(60):
            cid = "UC%022d" % i
            channels[cid] = _channel(cid, "가 뉴스 %d" % i, "UU%d" % i)
            items["UU%d" % i] = [_item("v%d" % i, "가 뉴스 오늘", "2026-11-06")]
            videos["v%d" % i] = True
            many.append(
                {
                    "category": "news",
                    "name": "채널 %d" % i,
                    "handle": "channel/" + cid,
                    "expect": "가 뉴스",
                    "korean": True,
                }
            )
        fake = FakeApi(channels, items, videos)
        passed, reasons, _ = self.run_with(fake, candidates=many, before={})
        self.assertEqual(len(passed), 60)
        self.assertEqual(reasons, {})
        # 60개면 channels 2 묶음 · playlistItems 60번 · videos 2 묶음 = 64단위.
        self.assertEqual(fake.calls["channels"], 2)
        self.assertEqual(fake.calls["playlistItems"], 60)
        self.assertEqual(fake.calls["videos"], 2)
        self.assertEqual(
            fake.calls["channels"]
            + fake.calls["playlistItems"]
            + fake.calls["videos"],
            64,
        )

    # ───────────────────── ⑤ 키가 없으면 ─────────────────────

    def test_키가_없으면_빈_글이다(self):
        was = os.environ.pop("YT_API_KEY", None)
        self.addCleanup(
            lambda: os.environ.__setitem__("YT_API_KEY", was)
            if was is not None
            else None
        )
        self.assertEqual(checker.api_key(), "")
        os.environ["YT_API_KEY"] = "  "
        self.assertEqual(checker.api_key(), "")
        os.environ["YT_API_KEY"] = " abc "
        self.assertEqual(checker.api_key(), "abc")

    def test_공개_쪽_길은_그대로_있다(self):
        """⚠ 키가 없으면 **지금 공개 쪽 그대로** 돈다."""
        self.assertTrue(callable(checker.inspect))
        self.assertTrue(callable(checker.latest))
        self.assertTrue(callable(checker.channel_of))
        self.assertTrue(callable(checker.embeddable))
        # 규칙 값도 그대로다.
        self.assertEqual(checker.DROP_AFTER, 2)
        self.assertEqual(checker.KEEP_AT_LEAST, 0.8)
        self.assertEqual(checker.STALE_DAYS, 14)
        self.assertEqual(checker.DORMANT_DAYS, 365)
        self.assertEqual(checker.CATEGORIES, ["news", "music", "show", "culture", "movie"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
