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
          '주소 서울특별시 서대문구 신촌로 163 (대현동) · 전화 <a href="tel:07080657440">070-8065-7440</a> · 이메일 <a class="mail" href="mailto:support@modubox.app">support@modubox.app</a>')

MON_EN = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
          'September', 'October', 'November', 'December']
MON_ES = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
          'septiembre', 'octubre', 'noviembre', 'diciembre']

CSS = open(os.path.join(SRC, "site", "site.css"), encoding="utf-8").read()
import hashlib
CSS_VER = hashlib.sha256(CSS.encode()).hexdigest()[:10]   # 옛 site.css 캐시 때문에 깨져 보이지 않게(11/11)   # 11/11 새 디자인 v5(본부 홍보팀) — 흰 바탕 고정

def og_tags(title, desc, url, og):
    """카톡·문자 링크 미리보기(오픈 그래프) — og = (제목, 그림 주소) 있을 때만. 10/28 수면앱 공유 미리보기"""
    if not og:
        return ''
    t, img = og
    e = html.escape
    return ('\n' + f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="ModuBox Labs">\n'
            f'<meta property="og:title" content="{e(t)}">\n<meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="{e(url)}">\n<meta property="og:image" content="{e(img)}">\n'
            f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:card" content="summary_large_image">')

# ---------- 11/11 새 디자인 v5: 아이콘·자리표시 ----------
ICON = {
 'radio': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#f25b40"/><path d="m37 32 49-13" stroke="#27221f" stroke-width="5" stroke-linecap="round"/><rect x="23" y="34" width="82" height="65" rx="13" fill="#fff2d8"/><circle cx="47" cy="67" r="15" fill="none" stroke="#27221f" stroke-width="5"/><path d="M76 54h15M76 65h15M76 76h15" stroke="#27221f" stroke-width="4" stroke-linecap="round"/><circle cx="86" cy="88" r="3" fill="#27221f"/></svg>',
 'podcast': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#efa8c8"/><rect x="51" y="24" width="26" height="52" rx="13" fill="#622743"/><path d="M39 61a25 25 0 0 0 50 0M64 87v17M51 105h26" fill="none" stroke="#622743" stroke-width="7" stroke-linecap="round"/></svg>',
 'music': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#a9b5fa"/><path d="M54 81V38l41-8v45M54 50l41-8" fill="none" stroke="#24204e" stroke-width="8" stroke-linejoin="round"/><ellipse cx="41" cy="84" rx="17" ry="12" transform="rotate(-18 41 84)" fill="#24204e"/><ellipse cx="82" cy="78" rx="17" ry="12" transform="rotate(-18 82 78)" fill="#24204e"/></svg>',
 'bookmark': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#c4e87b"/><path d="M40 28h48a6 6 0 0 1 6 6v68L64 83l-30 19V34a6 6 0 0 1 6-6Z" fill="#28532f"/><path d="m53 51 8 8 15-16" fill="none" stroke="#eaf6d3" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 'headphones': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#f4c854"/><path d="M32 70V59a32 32 0 0 1 64 0v11" fill="none" stroke="#492f24" stroke-width="9"/><rect x="25" y="61" width="20" height="34" rx="10" fill="#492f24"/><rect x="83" y="61" width="20" height="34" rx="10" fill="#492f24"/><path d="M89 94c0 10-13 13-24 13" fill="none" stroke="#492f24" stroke-width="5" stroke-linecap="round"/></svg>',
 'moon': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#5474d0"/><path d="M84 25a40 40 0 1 0 21 66A39 39 0 0 1 84 25Z" fill="#fff0bc"/><path d="m92 39 3 7 7 3-7 3-3 7-3-7-7-3 7-3Z" fill="#fff0bc"/></svg>',
 'tv': '<svg viewBox="0 0 128 128" aria-hidden="true"><rect width="128" height="128" rx="29" fill="#b9a6f5"/><rect x="22" y="36" width="84" height="58" rx="12" fill="#2a1a63"/><path d="M56 52v26l22-13Z" fill="#efe8ff"/><path d="m50 22 14 13 14-13" fill="none" stroke="#2a1a63" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M46 104h36" stroke="#2a1a63" stroke-width="6" stroke-linecap="round"/></svg>',
}
WAVE = '<svg class="wave" viewBox="0 0 22 12" aria-hidden="true"><path d="M1 5v2M5 2v8M9 4v4M13 0v12M17 3v6M21 5v2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
LOGO = '<svg class="mark" viewBox="0 0 22 20" aria-hidden="true"><path d="M2 5v10M7 1v18M12 4v12M17 7v6" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>'
NAV = [('home', '홈', '/'), ('box', '모두박스', '/box/'), ('sleep', '수면 사운드', '/sleep/'), ('about', '소개', '/about/')]
# 보는 라디오: 11/11 사장님 결정으로 메뉴·홈 카드 숨김(apps.json preparing). /visualradio/·처리방침 주소는 유지
TOP_JS = ("<script>try{history.scrollRestoration='manual'}catch(e){}function _top(){if(!location.hash){window.scrollTo({top:0,left:0,behavior:'instant'})}}"
          "_top();addEventListener('pageshow',_top);</script>")

def bars(n=22, k=1.7):
    import math
    return '<span class="bars" aria-hidden="true">' + ''.join(f'<i style="height:{int(6+16*abs(math.sin(i*k)))}px"></i>' for i in range(n)) + '</span>'

def app_by(slug):
    return next(a for a in APPS if a['slug'] == slug)

def v5_play(slug, label='Google Play에서 받기', cls='btn'):
    slug, _, pos = slug.partition('@')          # {{play:앱@bottom}} → utm_campaign=<앱>_bottom (11/11 홍보팀: 위 hero · 아래 bottom)
    a = app_by(slug)
    if a['status'] != 'live':
        return f'<span class="{cls} soon">곧 출시합니다</span>'
    return f'<a class="{cls}" href="{html.escape(play_url(a, pos or 'hero'))}" target="_blank" rel="noopener">{label} {WAVE}</a>'

def fill(text):
    """원고 HTML의 자리표시 채우기: {{icon:x}} {{wave}} {{bars}} {{bars:k}} {{play:앱}} {{play:앱@bottom}} {{play:앱:글자:class}}"""
    def rep(m):
        parts = m.group(1).split(':')
        if parts[0] == 'icon': return ICON[parts[1]]
        if parts[0] == 'wave': return WAVE
        if parts[0] == 'bars': return bars(22, float(parts[1])) if len(parts) > 1 else bars()
        if parts[0] == 'play': return v5_play(parts[1], *(parts[2:4]))
        raise KeyError(m.group(0))
    return re.sub(r'\{\{([^{}]+)\}\}', rep, text)

def page(title, body, desc='', lang='ko', canonical='', og=None, cur='', cta=None, doc=False, noindex=False):
    cur_attr = ' aria-current="page"'
    nav = ''.join(f'<a href="{h}"{cur_attr if s == cur else ""}>{n}</a>' for s, n, h in NAV)
    if cta is None:
        cta = f'<a class="btn" href="/#apps">앱 받기 {WAVE}</a>'
    main = f'<div class="wrap"><div class="docpage">\n{body}\n</div></div>' if doc else body
    links = ''.join(f'<a href="/{s}/privacy/">{n} 개인정보처리방침</a>' for s, n in
                    [('box', '모두박스'), ('sleep', '수면 사운드'), ('visualradio', '보는 라디오')])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<title>{title}</title>
<meta name="description" content="{html.escape(desc)}">
{'<meta name="robots" content="noindex">' if noindex else ''}{f'<link rel="canonical" href="{canonical}">' if canonical else ''}{og_tags(title, desc, canonical, og)}
<link rel="stylesheet" href="/assets/fonts/pretendard.css">
<link rel="stylesheet" href="/assets/site.css?v={CSS_VER}">
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="/">{LOGO}모두박스<small>Labs</small></a><nav class="nav" aria-label="사이트">{nav}</nav>{cta}</div></header>
<main>
{main}
</main>
<footer><div class="wrap"><div class="links">{links}<a href="/about/">회사 소개</a></div>{BIZ_KO}<br>© 2026 ModuBox Labs</div></footer>
{TOP_JS}
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

def play_url(a, pos='hero'):
    return (f"https://play.google.com/store/apps/details?id={ns(a).package}"
            f"&referrer=utm_source%3Dsite%26utm_campaign%3D{ns(a).slug}_{pos}")

def app_cta(a):
    """머리 오른쪽 단추: 출시 앱 = '앱 받기'(Play), 준비 중 = '곧 출시'"""
    return v5_play(a['slug'], '앱 받기') if a['status'] == 'live' else '<span class="btn soon">곧 출시</span>'

PLAY_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.5v15a1 1 0 0 0 1.5.86l12.4-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>'
def play_btn(a, pos='hero'):
    return (f'<a class="btn play" style="--app:{html.escape(a.get("color", "#1A3270"))}" '
            f'href="{html.escape(play_url(a, pos))}">{PLAY_SVG}Google Play에서 받기</a>')

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
    for k_, v_ in rev.items():
        assert k_ in body, k_
        body = body.replace(k_, v_)
    assert 'modubox.app@gmail.com">' not in body
    return page('개인정보처리방침 · Privacy Policy — 수면 사운드 (Sleep Sounds)',
      '<div class="doc">' + body.strip() + '</div>', '수면 사운드(Sleep Sounds) 개인정보처리방침',
      canonical='https://modubox.app/sleep/privacy/', doc=True, cur='sleep', cta=app_cta(a))


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
      '모두박스(ModuBox) 개인정보처리방침', canonical='https://modubox.app/box/privacy/', doc=True, cur='box', cta=app_cta(a))


def privacy_md(a, Y, M, D):
    meta, body = front(read(a['slug'], 'privacy.md'))
    return page(meta.get('title', f"개인정보처리방침 — {ns(a).name_ko}"), '<div class="doc">' + md(body) + '</div>',
                meta.get('description', f"{ns(a).name_ko} 개인정보처리방침"), canonical=f"{BASE}/{ns(a).slug}/privacy/", doc=True, cur=a["slug"], cta=app_cta(a))

RESERVED = {'page', 'help', 'faq', 'updates', 'privacy', 'README'}   # 그 밖의 <이름>.md → /<앱>/<이름>/ (예: box/rights.md → /box/rights/)

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

# ---------- 회사 홈 · 소개 (11/11 v5, 원고 _src/site/home.html · about.html — 홍보팀 관장) ----------
w('index.html', page(SITE['title'], fill(read('site', 'home.html')), SITE['description'], canonical=BASE + '/', cur='home'))
w('about/index.html', page('모두박스랩스 소개', fill(read('site', 'about.html')), '모두박스랩스가 앱을 만드는 이야기와 원칙',
                           canonical=BASE + '/about/', cur='about', cta=f'<a class="btn" href="/#apps">앱 받기 {WAVE}</a>'))
urls.append(BASE + '/about/')

def legacy_app_page(a, meta, body, has_help, og):
    """옛 형식 page.md(머리말 h1·lead + 마크다운 본문 + <!-- buttons -->) — 새 틀 안에 문서 쪽 모양으로"""
    s = a['slug']
    btns = [v5_play(s)]
    if has_help:
        btns.append(f'<a class="btn ghost" href="/{s}/help/">도움말</a>')
    btns.append(f'<a class="btn ghost" href="/{s}/privacy/">개인정보처리방침</a>')
    btn_html = '<div class="cta" style="display:flex;gap:10px;flex-wrap:wrap;margin:22px 0">\n' + '\n'.join(btns) + '\n</div>'
    before, _, after = body.partition('<!-- buttons -->')
    if not _:
        before, after = body, ''
    parts = [f"<h1>{meta.get('h1', a['name_ko'])}</h1>", f"<p class=\"lead\" style=\"margin:0 0 8px\">{meta.get('lead', '')}</p>"]
    if md(before): parts.append(md(before))
    parts.append(btn_html)
    if md(after): parts.append(md(after))
    w(f'{s}/index.html', page(meta.get('title', a['name_ko']), '<div class="doc">' + '\n'.join(parts) + '</div>',
                               meta.get('description', ''), canonical=f'{BASE}/{s}/', og=og, cur=s, cta=app_cta(a),
                               doc=True, noindex=a['status'] == 'preparing'))

# ---------- 앱 칸 ----------
for a in APPS:
    s = a['slug']
    meta, body = front(read(s, 'page.md'))
    help_txt, faq_txt, upd_txt = read(s, 'help.md'), read(s, 'faq.md'), read(s, 'updates.md')
    has_help = has_content(help_txt) or has_content(faq_txt)
    og = ((meta.get('og_title', meta.get('title', a['name_ko'])), f'{BASE}/{s}/img/og.png')
          if os.path.exists(os.path.join(SRC, s, 'img', 'og.png')) else None)
    if meta.get('layout') == 'full':      # 11/11 v5: 본문 HTML 그대로(자리표시만 채움)
        w(f'{s}/index.html', page(meta.get('title', a['name_ko']), fill(re.sub(r'<!--.*?-->', '', body, flags=re.S)).strip(),
                                   meta.get('description', ''), canonical=f'{BASE}/{s}/', og=og, cur=s, cta=app_cta(a),
                                   noindex=a['status'] == 'preparing'))
    else:
        legacy_app_page(a, meta, body, has_help, og)
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
                                        canonical=f'{BASE}/{s}/help/', doc=True, cur=s, cta=app_cta(a)))
        if a in SHOWN: urls.append(f'{BASE}/{s}/help/')
    if has_content(upd_txt):
        ub = f"\n<div class=\"doc\">\n<h1>업데이트 소식 — {ns(a).name_ko}</h1>\n{md(upd_txt)}\n</div>\n"
        w(f'{s}/updates/index.html', page(f"업데이트 소식 — {ns(a).name_ko} · ModuBox Labs", ub, f"{ns(a).name_ko} 업데이트 소식",
                                           canonical=f'{BASE}/{s}/updates/', doc=True, cur=s, cta=app_cta(a)))
        if a in SHOWN: urls.append(f'{BASE}/{s}/updates/')
    for fn in sorted(os.listdir(os.path.join(SRC, s))):
        nm, ext = os.path.splitext(fn)
        if ext != '.md' or nm in RESERVED:
            continue
        txt = read(s, fn)
        if not has_content(txt):
            continue
        em, eb = front(txt)
        title = em.get('title', nm)
        xb = f"\n<div class=\"doc\">\n<h1>{em.get('h1', title)}</h1>\n{md(eb)}\n</div>\n"
        w(f'{s}/{nm}/index.html', page(f"{title} · ModuBox Labs", xb, em.get('description', ''), canonical=f'{BASE}/{s}/{nm}/', doc=True, cur=s, cta=app_cta(a)))
        if a in SHOWN: urls.append(f'{BASE}/{s}/{nm}/')
    copytree(os.path.join(SRC, s, 'img'), f'{s}/img')
    copytree(os.path.join(SRC, s, 'static'), s)       # 앱 데이터 등(예: box/static/radio/v1 → /box/radio/v1/)

# ---------- 404 · sitemap ----------
w('404.html', page('페이지를 찾을 수 없습니다 — ModuBox Labs',
  '<div class="doc"><h1>페이지를 찾을 수 없습니다</h1><p>주소를 다시 확인해 주세요.</p><p><a href="/">처음으로</a></p></div>', doc=True))
w('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
  ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
# robots.txt: 앱 데이터 폴더(static/ 아래 폴더)는 검색 제외, sitemap 위치 안내
dis = []
for a in APPS:
    sd = os.path.join(SRC, a['slug'], 'static')
    if os.path.isdir(sd):
        dis += [f"/{a['slug']}/{d}/" for d in sorted(os.listdir(sd)) if os.path.isdir(os.path.join(sd, d))]
w('robots.txt', 'User-agent: *\n' + ''.join(f'Disallow: {d}\n' for d in dis) + f'\nSitemap: {BASE}/sitemap.xml\n')
print('built', OUT, len(urls), 'urls')
