#!/usr/bin/env python3
"""modubox.app 빌드 — 앱 목록(apps.json) 방식 (10/22 0단계 틀 개편)

사용: python3 _src/build.py          (저장소 루트에서. 결과 → docs/, GitHub Pages가 docs/를 내보냄)
필요: Python 3.9+, pip 패키지 markdown

원고 위치(각 앱 세션은 자기 폴더만): _src/<앱>/page.md · help.md · faq.md · updates.md · img/ · static/
공통 틀(이 파일·apps.json·site.json·CSS·머리/바닥)·빌드·배포 = 수면앱 세션. 자세한 규칙은 _src/README.md
같은 원고 → 같은 결과(날짜·시각을 넣지 않음). 날짜는 apps.json 값만 씀.
"""
import os, re, sys, json, html, shutil
import markdown
from types import SimpleNamespace

def ns(d):
    return SimpleNamespace(**d)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_src')
OUT = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'docs')
BASE = 'https://modubox.app'

APPS = json.load(open(os.path.join(SRC, 'apps.json'), encoding='utf-8'))
SITE = json.load(open(os.path.join(SRC, 'site.json'), encoding='utf-8'))
SHOWN = [a for a in APPS if a['status'] in ('testing', 'live')]   # 홈 카드·메뉴·sitemap에 나오는 앱

BIZ_KO = ('상호 모두박스랩스 (ModuBox Labs) · 대표 김영균 · 사업자등록번호 163-78-00746 · 통신판매업 신고 제2026-서울서대문-1097호<br>'
          '주소 서울특별시 서대문구 신촌로 163, 1803호 · 전화 070-8065-7440 · 이메일 <a href="mailto:support@modubox.app">support@modubox.app</a>')

MON_EN = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
          'September', 'October', 'November', 'December']
MON_ES = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
          'septiembre', 'octubre', 'noviembre', 'diciembre']

CSS = """:root{--ink:#1d1f27;--sub:#5d6170;--line:#e4e6ec;--bg:#fbfbfd;--card:#fff;--accent:#3b4cca}
@media (prefers-color-scheme:dark){:root{--ink:#eceef5;--sub:#a3a8b8;--line:#2a2d3a;--bg:#101219;--card:#171a24;--accent:#9aa6ff}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic","Hiragino Sans","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.7;word-break:keep-all}
a{color:var(--accent)}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header.top{border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;height:60px}
.brand{white-space:nowrap;font-weight:700;font-size:17px;color:var(--ink);text-decoration:none;letter-spacing:-.01em}
.brand span{color:var(--sub);font-weight:500;margin-left:6px;font-size:14px}
header.top nav{white-space:nowrap}
header.top nav a{margin-left:14px;font-size:14px;color:var(--sub);text-decoration:none}
main{padding:40px 0 56px}
h1{font-size:28px;line-height:1.3;margin:0 0 10px;letter-spacing:-.02em}
.lead{color:var(--sub);font-size:16px;margin:0 0 36px}
.apps{display:grid;gap:14px}
.app{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;text-decoration:none;color:var(--ink)}
.app h2{font-size:18px;margin:0 0 4px}
.app p{margin:0;color:var(--sub);font-size:14.5px}
.app .more{display:inline-block;margin-top:10px;font-size:14px;color:var(--accent)}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}
.btn{display:inline-block;padding:10px 16px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);text-decoration:none;font-size:14.5px}
.note{color:var(--sub);font-size:14px}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--sub);font-size:12.5px;line-height:1.8}
footer a{color:var(--sub)}
.doc h1{font-size:23px}
.doc h2{font-size:17px;margin-top:28px}
.doc .updated{color:var(--sub);font-size:13px;margin:0 0 24px}
.doc nav.lang a{margin-right:12px;font-size:14px}
.doc hr{margin:48px 0;border:0;border-top:1px solid var(--line)}
.doc ul{padding-left:20px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media (max-width:480px){.brand span{display:none}}
.doc .updated+.updated{margin-top:-18px}
.doc .sub{margin:2px 0 2px 18px;color:var(--sub)}
"""

def page(title, body, desc='', lang='ko', canonical=''):
    nav = ''.join(f'<a href="/{ns(a).slug}/">{ns(a).name_ko}</a>' for a in SHOWN)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{html.escape(desc)}">
{f'<link rel="canonical" href="{canonical}">' if canonical else ''}
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">ModuBox Labs<span>모두박스랩스</span></a>
<nav>{nav}</nav></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">{BIZ_KO}<br>© 2026 ModuBox Labs</div></footer>
</body>
</html>
"""

def w(rel, text):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8', newline='\n').write(text)

def read(*parts):
    p = os.path.join(SRC, *parts)
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''

def has_content(text):
    return bool(re.sub(r'<!--.*?-->', '', text, flags=re.S).strip())

def md(text):
    out = markdown.markdown(re.sub(r'<!--.*?-->', '', text, flags=re.S).strip(), extensions=['tables'])
    return re.sub(r'\n{2,}', '\n', out).strip()

def front(text):
    """--- key: value --- 머리말 + 본문"""
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)

def copytree(src, dst):
    if not os.path.isdir(src):
        return
    for d, _, files in os.walk(src):
        for f in files:
            if f == '.keep':
                continue
            s = os.path.join(d, f)
            t = os.path.join(OUT, dst, os.path.relpath(s, src))
            os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copy2(s, t)

def play_url(a):
    return (f"https://play.google.com/store/apps/details?id={ns(a).package}"
            f"&referrer=utm_source%3Dsite%26utm_campaign%3D{ns(a).slug}_hero")

# ---------- 앱별 처리방침(옛 형식 그대로 — 글자 바꾸지 않음) ----------
def privacy_sleep_legacy(a, Y, M, D):
    MON_EN_ = MON_EN[int(M)]; MON_ES_ = MON_ES[int(M)]
    old = open(os.path.join(SRC, 'sleep', 'privacy_source.html'), encoding='utf-8').read()
    body = re.search(r'<body>(.*)</body>', old, re.S).group(1)
    body = body.replace('mailto:modubox.app@gmail.com">modubox.app@gmail.com', 'mailto:sleep@modubox.app">sleep@modubox.app')
    body = body.replace('<nav>', '<nav class="lang">', 1)
    rev = {
     '시행일: 2026년 10월 14일 (이전 버전 시행일: 2026년 9월 27일)':
       f'시행일: 2026년 10월 14일 (이전 버전 시행일: 2026년 9월 27일)<br>개정: {Y}년 {int(M)}월 {int(D)}일 — 연락처 이메일 변경(modubox.app@gmail.com → sleep@modubox.app), 페이지 주소 변경. 수집·이용 내용은 바뀌지 않았습니다.',
     'Effective date: October 14, 2026 (previous version effective: September 27, 2026)':
       f'Effective date: October 14, 2026 (previous version effective: September 27, 2026)<br>Revised: {MON_EN_} {int(D)}, {Y} — contact email changed (modubox.app@gmail.com → sleep@modubox.app) and page address moved. What the App collects and how did not change.',
     '施行日：2026年10月14日（前バージョン施行日：2026年9月27日）':
       f'施行日：2026年10月14日（前バージョン施行日：2026年9月27日）<br>改定：{Y}年{int(M)}月{int(D)}日 — 連絡先メールアドレスの変更（modubox.app@gmail.com → sleep@modubox.app）およびページアドレスの移転。収集・利用の内容は変わっていません。',
     '生效日期：2026年10月14日（上一版本生效日期：2026年9月27日）':
       f'生效日期：2026年10月14日（上一版本生效日期：2026年9月27日）<br>修订：{Y}年{int(M)}月{int(D)}日 — 联系邮箱变更（modubox.app@gmail.com → sleep@modubox.app），页面地址迁移。收集与使用内容未发生变化。',
     'Fecha de entrada en vigor: 14 de octubre de 2026 (versión anterior: 27 de septiembre de 2026)':
       f'Fecha de entrada en vigor: 14 de octubre de 2026 (versión anterior: 27 de septiembre de 2026)<br>Revisión: {int(D)} de {MON_ES_} de {Y} — cambio del correo de contacto (modubox.app@gmail.com → sleep@modubox.app) y de la dirección de esta página. La información que se recopila y su uso no han cambiado.',
    }
    for a, b in rev.items():
        assert a in body, a
        body = body.replace(a, b)
    assert 'modubox.app@gmail.com">' not in body
    return page('개인정보처리방침 · Privacy Policy — 수면 사운드 (Sleep Sounds)',
      '<div class="doc">' + body.strip() + '</div>', '수면 사운드(Sleep Sounds) 개인정보처리방침',
      canonical='https://modubox.app/sleep/privacy/')


def privacy_box_legacy(a, Y, M, D):
    MON_EN_ = MON_EN[int(M)]
    src = open(os.path.join(SRC, 'box', 'privacy_source.txt'), encoding='utf-8').read()
    part = src.split('① https://modubox.app/box/privacy/ 본문')[1].split('② https://modubox.app/box/')[0]
    part = part.replace('2026년 10월 __일', f'{Y}년 {int(M)}월 {int(D)}일').replace('October __, 2026', f'{MON_EN_} {int(D)}, {Y}')
    assert '__' not in part
    lines = [l.rstrip() for l in part.splitlines()]
    lines = [l for l in lines if not set(l) <= set('═ ')]
    ko_end = next(i for i, l in enumerate(lines) if l.startswith('Privacy Policy — ModuBox'))
    def to_html(ls, first_h1=True):
        out, in_ul = [], False
        def close():
            nonlocal in_ul
            if in_ul: out.append('</ul>'); in_ul = False
        h1_done = False
        for l in ls:
            s = l.strip()
            if not s: close(); continue
            e = html.escape(s).replace('box@modubox.app', '<a href="mailto:box@modubox.app">box@modubox.app</a>')
            if not h1_done:
                out.append(f'<h1>{e}</h1>'); h1_done = True; continue
            if re.match(r'^(시행일|개정|Effective date|Revised):', s):
                close(); out.append(f'<p class="updated">{e}</p>'); continue
            m = re.match(r'^(\d{1,2})\. (.*)$', s)
            if m and (len(s) < 40 or ' — ' not in s):
                close(); out.append(f'<h2>{e}</h2>'); continue
            if m:  # 영문: "1. 제목 — 본문"
                close(); t, rest = s.split(' — ', 1)
                out.append(f'<h2>{html.escape(t)}</h2>'); out.append('<p><span class="sr">— </span>' + html.escape(rest).replace('box@modubox.app', '<a href="mailto:box@modubox.app">box@modubox.app</a>') + '</p>'); continue
            if s.startswith('- '):
                if not in_ul: out.append('<ul>'); in_ul = True
                out.append(f'<li>{e[2:]}</li>'); continue
            if s.startswith('·'):
                out.append(f'<p class="sub">{e}</p>'); continue
            close(); out.append(f'<p>{e}</p>')
        close()
        return '\n'.join(out)
    ko = to_html(lines[:ko_end]); en = to_html(lines[ko_end:])
    box_body = ('<div class="doc"><nav class="lang"><a href="#ko">한국어</a><a href="#en">English</a></nav>\n'
                f'<section id="ko" lang="ko">\n{ko}\n</section>\n<hr>\n<section id="en" lang="en">\n{en}\n</section></div>')
    return page('개인정보처리방침 · Privacy Policy — 모두박스 (ModuBox)', box_body,
      '모두박스(ModuBox) 개인정보처리방침', canonical='https://modubox.app/box/privacy/')


def privacy_md(a, Y, M, D):
    meta, body = front(read(a['slug'], 'privacy.md'))
    return page(meta.get('title', f"개인정보처리방침 — {ns(a).name_ko}"), '<div class="doc">' + md(body) + '</div>',
                meta.get('description', f"{ns(a).name_ko} 개인정보처리방침"), canonical=f"{BASE}/{ns(a).slug}/privacy/")

PRIVACY = {'sleep-html-legacy': privacy_sleep_legacy, 'box-txt-legacy': privacy_box_legacy, 'md': privacy_md}

# ---------- 시작 ----------
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
w('assets/site.css', CSS)
w('CNAME', 'modubox.app\n')
w('.nojekyll', '')
copytree(os.path.join(SRC, 'static'), '.')          # 루트 고정 파일(Search Console 인증 등)

urls = [BASE + '/']

# ---------- 회사 홈 ----------
cards = []
for a in SHOWN:
    meta, _ = front(read(a['slug'], 'page.md'))
    cards.append(f'<a class="app" href="/{ns(a).slug}/"><h2>{ns(a).name_ko} · {ns(a).name_en}</h2>\n'
                 '<p>' + meta.get('card', '') + f'</p>\n<span class="more">자세히 보기 →</span></a>')
home = (f"\n<h1>{SITE['h1']}</h1>\n<p class=\"lead\">{SITE['lead']}</p>\n<div class=\"apps\">\n" + '\n'.join(cards) +
        f"\n</div>\n<p class=\"note\" style=\"margin-top:28px\">문의: <a href=\"mailto:{SITE['mail']}\">{SITE['mail']}</a></p>\n")
w('index.html', page(SITE['title'], home, SITE['description'], canonical=BASE + '/'))

# ---------- 앱 칸 ----------
for a in APPS:
    s = a['slug']
    meta, body = front(read(s, 'page.md'))
    help_txt, faq_txt, upd_txt = read(s, 'help.md'), read(s, 'faq.md'), read(s, 'updates.md')
    has_help = has_content(help_txt) or has_content(faq_txt)
    btns = []
    if a['status'] == 'live':
        btns.append(f'<a class="btn" href="{html.escape(play_url(a))}">Google Play에서 받기</a>')
    else:
        btns.append('<span class="btn" aria-disabled="true">곧 출시합니다</span>')
    if has_help:
        btns.append(f'<a class="btn" href="/{s}/help/">도움말</a>')
    btns.append(f'<a class="btn" href="/{s}/privacy/">개인정보처리방침</a>')
    btn_html = '<div class="btns">\n' + '\n'.join(btns) + '\n</div>'
    before, _, after = body.partition('<!-- buttons -->')
    if not _:
        before, after = body, ''
    parts = [f"<h1>{meta.get('h1', a['name_ko'])}</h1>", f"<p class=\"lead\">{meta.get('lead', '')}</p>"]
    if md(before): parts.append(md(before))
    parts.append(btn_html)
    if md(after): parts.append(md(after))
    w(f'{s}/index.html', page(meta.get('title', a['name_ko']), '\n' + '\n'.join(parts) + '\n',
                               meta.get('description', ''), canonical=f'{BASE}/{s}/'))
    Y, M, D = a['privacy_revised'].split('-')
    w(f'{s}/privacy/index.html', PRIVACY[a['privacy_format']](a, Y, M, D))
    if a in SHOWN:
        urls += [f'{BASE}/{s}/', f'{BASE}/{s}/privacy/']
    if has_help:
        hb = f"\n<div class=\"doc\">\n<h1>도움말 — {ns(a).name_ko}</h1>\n" + (md(help_txt) if has_content(help_txt) else '')
        if has_content(faq_txt):
            hb += '\n<h2>자주 묻는 질문</h2>\n' + md(faq_txt)
        hb += f"\n<p class=\"note\">더 궁금한 점: <a href=\"mailto:{ns(a).mail}\">{ns(a).mail}</a></p>\n</div>\n"
        w(f'{s}/help/index.html', page(f"도움말 — {ns(a).name_ko} · ModuBox Labs", hb, f"{ns(a).name_ko} 도움말·자주 묻는 질문",
                                        canonical=f'{BASE}/{s}/help/'))
        if a in SHOWN: urls.append(f'{BASE}/{s}/help/')
    if has_content(upd_txt):
        ub = f"\n<div class=\"doc\">\n<h1>업데이트 소식 — {ns(a).name_ko}</h1>\n{md(upd_txt)}\n</div>\n"
        w(f'{s}/updates/index.html', page(f"업데이트 소식 — {ns(a).name_ko} · ModuBox Labs", ub, f"{ns(a).name_ko} 업데이트 소식",
                                           canonical=f'{BASE}/{s}/updates/'))
        if a in SHOWN: urls.append(f'{BASE}/{s}/updates/')
    copytree(os.path.join(SRC, s, 'img'), f'{s}/img')
    copytree(os.path.join(SRC, s, 'static'), s)       # 앱 데이터 등(예: box/static/radio/v1 → /box/radio/v1/)

# ---------- 404 · sitemap ----------
w('404.html', page('페이지를 찾을 수 없습니다 — ModuBox Labs',
  '<h1>페이지를 찾을 수 없습니다</h1><p class="lead">주소를 다시 확인해 주세요.</p><p><a href="/">처음으로</a></p>'))
w('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
print('built', OUT, len(urls), 'urls')
