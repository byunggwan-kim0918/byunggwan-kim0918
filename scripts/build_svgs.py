"""프로필 README용 SVG 생성기 — "달과 별" 테마 (자체 제작, 외부 위젯 없음).

    python scripts/build_svgs.py

생성물 (assets/):
  header-{day,night}.svg     밤하늘(다크) / 새벽하늘(라이트) 카드 + 졸린 초승달 + 별·별자리·별똥별 + 이름
  stack-{day,night}.svg      분야별 아이콘 칩
  project-<name>-{day,night}.svg
  activity-{day,night}.svg   최근 1년 기여 요약 (매일 갱신)
  footer-{day,night}.svg     행성 지평선을 걸어가는 아이
GitHub 라이트/다크 테마에 따라 day/night 가 자동으로 바뀝니다.

아이콘: scripts/icons.json (Simple Icons, CC0). 기여 데이터: GITHUB_TOKEN 이 있으면 GraphQL, 없으면 공개 프로필.
"""
import json
import math
import os
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
ICONS = json.loads((ROOT / "scripts" / "icons.json").read_text())
USERNAME = os.environ.get("GH_USERNAME") or "byunggwan-kim0918"

# ---------------------------------------------------------------- DATA
NAME_KO = "김병관"
SUBTITLE = "Byunggwan Kim · Full-stack Developer"

# (label, color key, [(name, simple-icons slug or None)])
STACK = [
    ("BACKEND", "gold", [("Java 21", "openjdk"), ("Spring Boot", "springboot"), ("JPA", "hibernate"),
                         ("Spring Security", "springsecurity"), ("Flyway", "flyway")]),
    ("FRONTEND", "lilac", [("TypeScript", "typescript"), ("Next.js", "nextdotjs"), ("React", "react"),
                           ("Tailwind CSS", "tailwindcss"), ("Zustand", None)]),
    ("DATA", "sky", [("PostgreSQL", "postgresql"), ("Redis", "redis"), ("MapLibre", "maplibre")]),
    ("INFRA", "pink", [("Docker", "docker"), ("AWS", "amazonwebservices"), ("Terraform", "terraform"),
                       ("GitHub Actions", "githubactions")]),
    ("TEST", "mint", [("Playwright", None), ("JaCoCo", None)]),
]

PROJECTS = [  # (repo name, 설명, 기술, 그림, 색)
    ("shg-trip", "여행 일정 관리 서비스", "Spring Boot · Next.js · AWS", "constellation", "gold"),
    ("ui-tells", "UI 디자인 리뷰 도구", "Shell", "telescope", "lilac"),
]

# ---------------------------------------------------------------- PALETTE
COLORS = {  # (day, night)
    "gold": ("#C98A0B", "#FFD66B"), "lilac": ("#7B61E0", "#B9A8FF"), "sky": ("#3D8FD9", "#8CCBFF"),
    "pink": ("#D9577F", "#FFA9C2"), "mint": ("#1F9C80", "#8FE3CF"),
}
THEMES = {
    # 라이트: 연보라~복숭아 새벽하늘
    "day": dict(night=False, ink="#2A2550", muted="#6E6A8F", chip_bg="#FFFFFF", card="#FFFFFF", line="#E4E0F2",
                sky_top="#E9E4FF", sky_bot="#FFE9E4", moon="#FFC94D", moon_glow="#FFE7A3", star="#8F7FE8",
                cloud="#FFFFFF", cloud_op=".75",
                levels=["#F1EEFA", "#DAD2FB", "#B7A8F5", "#8F7AE8", "#6A4FD6"]),
    # 다크: 남색 밤하늘
    "night": dict(night=True, ink="#F5F3FF", muted="#A7A3C7", chip_bg="#12142A", card="#11132A", line="#2A2D52",
                  sky_top="#0B0E26", sky_bot="#241E4E", moon="#FFE19A", moon_glow="#FFD66B", star="#FFF6D6",
                  cloud="#3A3470", cloud_op=".45",
                  levels=["#1B1E3A", "#3A3474", "#5B4FB0", "#8F7FF0", "#FFD66B"]),
}
SANS = "'Pretendard','Inter','Segoe UI','Apple SD Gothic Neo','Noto Sans KR',system-ui,sans-serif"
SERIF = "'Gowun Batang','Nanum Myeongjo','AppleMyungjo','Batang',Georgia,serif"
MONO = "'JetBrains Mono','SF Mono','Cascadia Code',Consolas,Menlo,monospace"
W = 900


def c(key, t):
    return COLORS[key][1 if t["night"] else 0]


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">\n'
            f'<style>.s{{font-family:{SANS}}}.m{{font-family:{MONO}}}.r{{font-family:{SERIF}}}</style>\n{body}\n</svg>\n')


# ---------------------------------------------------------------- CELESTIAL PARTS
def sparkle(x, y, r, color, dur=None, delay=0):
    """네 갈래 반짝이 별."""
    k = r * 0.28
    d = (f"M{x},{y-r} Q{x+k},{y-k} {x+r},{y} Q{x+k},{y+k} {x},{y+r} "
         f"Q{x-k},{y+k} {x-r},{y} Q{x-k},{y-k} {x},{y-r}Z")
    anim = (f'<animate attributeName="opacity" values="1;.3;1" dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/>'
            if dur else "")
    return f'<path d="{d}" fill="{color}">{anim}</path>'


def dot_star(x, y, r, color, dur, delay=0):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"><animate attributeName="opacity" values="1;.2;1" '
            f'dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/></circle>')


def sleepy_moon(cx, cy, r, t, uid):
    """볼이 발그레한 졸린 초승달."""
    blush = c("pink", t)
    ink = "#7A5B2E"
    return f"""<defs><mask id="moon{uid}"><rect x="{cx-r*2}" y="{cy-r*2}" width="{r*4}" height="{r*4}" fill="#fff"/>
<circle cx="{cx+r*0.55:.1f}" cy="{cy-r*0.3:.1f}" r="{r*0.9:.1f}" fill="#000"/></mask>
<radialGradient id="glow{uid}"><stop offset="0" stop-color="{t['moon_glow']}" stop-opacity=".55"/><stop offset="1" stop-color="{t['moon_glow']}" stop-opacity="0"/></radialGradient></defs>
<circle cx="{cx}" cy="{cy}" r="{r*2.1:.1f}" fill="url(#glow{uid})"><animate attributeName="r" values="{r*1.9:.1f};{r*2.3:.1f};{r*1.9:.1f}" dur="5s" repeatCount="indefinite"/></circle>
<g><animateTransform attributeName="transform" type="rotate" values="-4 {cx} {cy};4 {cx} {cy};-4 {cx} {cy}" dur="7s" repeatCount="indefinite"/>
<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t['moon']}" mask="url(#moon{uid})"/>
<path d="M{cx-r*0.62:.1f},{cy+r*0.02:.1f} q{r*0.09:.1f},{r*0.1:.1f} {r*0.18:.1f},0" stroke="{ink}" stroke-width="{max(1.5, r*0.045):.1f}" stroke-linecap="round" fill="none"/>
<path d="M{cx-r*0.3:.1f},{cy+r*0.3:.1f} q{r*0.09:.1f},{r*0.1:.1f} {r*0.18:.1f},0" stroke="{ink}" stroke-width="{max(1.5, r*0.045):.1f}" stroke-linecap="round" fill="none"/>
<ellipse cx="{cx-r*0.68:.1f}" cy="{cy+r*0.22:.1f}" rx="{r*0.1:.1f}" ry="{r*0.06:.1f}" fill="{blush}" opacity=".7"/>
<ellipse cx="{cx-r*0.28:.1f}" cy="{cy+r*0.52:.1f}" rx="{r*0.1:.1f}" ry="{r*0.06:.1f}" fill="{blush}" opacity=".7"/>
</g>"""


def zzz(x, y, t):
    col = t["muted"]
    out = []
    for i, (dx, dy, s) in enumerate([(0, 0, 13), (14, -16, 16), (32, -36, 19)]):
        out.append(f'<text class="s" x="{x+dx}" y="{y+dy}" font-size="{s}" font-weight="700" fill="{col}" opacity="0">z'
                   f'<animate attributeName="opacity" values="0;1;0" dur="3s" begin="{i*0.6}s" repeatCount="indefinite"/></text>')
    return "".join(out)


def shooting_star(x1, y1, length, t, uid, delay=0):
    col = t["star"]
    return f"""<defs><linearGradient id="ss{uid}" x1="0" x2="1"><stop offset="0" stop-color="{col}" stop-opacity="0"/><stop offset="1" stop-color="{col}"/></linearGradient></defs>
<g opacity="0"><animate attributeName="opacity" values="0;1;0;0" keyTimes="0;.08;.18;1" dur="7s" begin="{delay}s" repeatCount="indefinite"/>
<animateTransform attributeName="transform" type="translate" values="0 0;{length} {length*0.45:.0f};{length} {length*0.45:.0f}" keyTimes="0;.18;1" dur="7s" begin="{delay}s" repeatCount="indefinite"/>
<line x1="{x1-90}" y1="{y1-40}" x2="{x1}" y2="{y1}" stroke="url(#ss{uid})" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="{x1}" cy="{y1}" r="2.6" fill="{col}"/></g>"""


def constellation(points, edges, t, r=3.2, line_op=".5"):
    col = t["star"]
    s = [f'<line x1="{points[a][0]}" y1="{points[a][1]}" x2="{points[b][0]}" y2="{points[b][1]}" stroke="{col}" '
         f'stroke-width="1.3" stroke-dasharray="3 4" opacity="{line_op}"/>' for a, b in edges]
    s += [sparkle(x, y, r * 2.2 if i % 2 == 0 else r * 1.6, col, dur=2.5 + i * 0.4, delay=i * 0.3)
          for i, (x, y) in enumerate(points)]
    return "\n".join(s)


def soft_cloud(x, y, s, t, drift=14, dur="16s"):
    return f"""<g transform="translate({x},{y}) scale({s})" opacity="{t['cloud_op']}">
<g><animateTransform attributeName="transform" type="translate" values="0 0;{drift} 0;0 0" dur="{dur}" repeatCount="indefinite"/>
<path d="M-40,12 C-52,12 -52,-2 -40,-4 C-40,-16 -22,-20 -14,-10 C-8,-22 14,-22 18,-8 C30,-12 40,0 32,10 C32,12 30,12 28,12Z" fill="{t['cloud']}"/>
</g></g>"""


# ---------------------------------------------------------------- HEADER (동화풍, 가운데 타이틀 + 양쪽 작은 행성)
TITLE = "Byunggwan Kim"
TAGLINE = "Full-stack Developer  ·  Spring Boot & Next.js"
MOTTO = "building little things on a little planet"
SCENE = {  # 장면 전용 색 (day = 해 질 녘 수채화, night = 깊은 밤)
    "day": dict(sky=["#F7E9D7", "#F3D5CF", "#D8D0F0"], planet="#E9C9A6", crater="#D2A57E",
                grass="#8DB596", coat="#4A6FA5", scarf="#E76F51", skin="#F6DCC4", hair="#5B4636",
                dome="#FFFFFF", rose="#D9466B", stem="#4F8A5B", lamp="#4A4A68", light="#FFC94D",
                ink="#3B2F4A", muted="#7A6A7E", star="#B49BE0", moon="#F4B942", accent="#E76F51"),
    "night": dict(sky=["#141A3C", "#232B5C", "#4A3F78"], planet="#C9A37E", crater="#9A7552",
                  grass="#5E8C6A", coat="#5B7FC0", scarf="#F4A261", skin="#F6DCC4", hair="#4A3A2C",
                  dome="#FFFFFF", rose="#FF6B8B", stem="#6FAF7D", lamp="#2B2B44", light="#FFD66B",
                  ink="#FBF6EE", muted="#C8C0DA", star="#FFF6D6", moon="#FFE19A", accent="#F4A261"),
}


def on_planet(x, px, py, pr):
    return py - math.sqrt(max(pr * pr - (x - px) ** 2, 0))


def planet(px, py, pr, k, uid, craters=()):
    s = [f'<radialGradient id="pl{uid}" cx=".35" cy=".1" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".28"/>'
         f'<stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></radialGradient>',
         f'<circle cx="{px}" cy="{py}" r="{pr}" fill="{k["planet"]}"/><circle cx="{px}" cy="{py}" r="{pr}" fill="url(#pl{uid})"/>']
    for dx, dy, w in craters:
        s.append(f'<ellipse cx="{px+dx}" cy="{on_planet(px+dx, px, py, pr)+dy:.1f}" rx="{w}" ry="{w*0.36:.1f}" fill="{k["crater"]}"/>')
    return "".join(s)


def grass(x, y, k):
    return f'<path d="M{x-5},{y+2:.1f} q2,-9 4,-1 q1,-11 3,0 q3,-8 4,1" stroke="{k["grass"]}" stroke-width="2" stroke-linecap="round" fill="none"/>'


def lamp(lx, ly, k, uid):
    return (f'<radialGradient id="lg{uid}"><stop offset="0" stop-color="{k["light"]}" stop-opacity=".75"/><stop offset="1" stop-color="{k["light"]}" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{lx}" cy="{ly-63:.1f}" r="34" fill="url(#lg{uid})"><animate attributeName="opacity" values="1;.55;1;.8;1" dur="4s" repeatCount="indefinite"/></circle>'
            f'<line x1="{lx}" y1="{ly:.1f}" x2="{lx}" y2="{ly-56:.1f}" stroke="{k["lamp"]}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<path d="M{lx-9},{ly-56:.1f} L{lx+9},{ly-56:.1f} L{lx+6},{ly-70:.1f} L{lx-6},{ly-70:.1f}Z" fill="{k["lamp"]}"/>'
            f'<rect x="{lx-5}" y="{ly-68:.1f}" width="10" height="10" rx="2" fill="{k["light"]}"/>'
            f'<path d="M{lx-8},{ly-70:.1f} L{lx},{ly-78:.1f} L{lx+8},{ly-70:.1f}Z" fill="{k["lamp"]}"/>')


def rose_dome(x, y, k):
    return (f'<g transform="translate({x},{y:.1f})">'
            f'<path d="M0,0 L0,-22" stroke="{k["stem"]}" stroke-width="2.2" stroke-linecap="round"/>'
            f'<path d="M0,-10 q-8,-2 -9,-8 q7,0 9,6Z" fill="{k["stem"]}"/>'
            f'<path d="M-6,-26 q6,-10 12,0 q-1,7 -6,7 q-5,0 -6,-7Z" fill="{k["rose"]}"/>'
            f'<path d="M-3,-27 q3,-5 6,0" stroke="#fff" stroke-width="1" opacity=".5" fill="none"/>'
            f'<path d="M-15,2 L-15,-26 A15,15 0 0 1 15,-26 L15,2Z" fill="{k["dome"]}" fill-opacity=".14" stroke="{k["dome"]}" stroke-opacity=".7" stroke-width="1.6"/>'
            f'<path d="M-9,-30 A10,10 0 0 1 -2,-38" stroke="#fff" stroke-width="1.6" stroke-linecap="round" opacity=".8"/>'
            f'<rect x="-18" y="0" width="36" height="4" rx="2" fill="{k["lamp"]}" opacity=".5"/></g>')


def kid_sitting(cx, cy, k, t, s=1.55):
    """무릎을 안고 앉아 오른쪽 위(달)를 올려다보는 아이 (오리지널 캐릭터)."""
    return f"""<g transform="translate({cx:.1f},{cy:.1f}) scale({s})">
<path stroke="{k['scarf']}" stroke-width="4.5" stroke-linecap="round" fill="none" d="M-6,-29 C-18,-31 -26,-24 -40,-30">
  <animate attributeName="d" dur="2.8s" repeatCount="indefinite" values="M-6,-29 C-18,-31 -26,-24 -40,-30;M-6,-29 C-18,-26 -28,-33 -41,-26;M-6,-29 C-18,-31 -26,-24 -40,-30"/></path>
<path stroke="{k['scarf']}" stroke-width="3.5" stroke-linecap="round" fill="none" opacity=".85" d="M-6,-27 C-14,-25 -20,-20 -30,-22">
  <animate attributeName="d" dur="2.2s" repeatCount="indefinite" values="M-6,-27 C-14,-25 -20,-20 -30,-22;M-6,-27 C-14,-23 -22,-25 -31,-19;M-6,-27 C-14,-25 -20,-20 -30,-22"/></path>
<path d="M-12,0 C-14,-12 -12,-24 -4,-28 C4,-30 10,-24 12,-14 L14,0Z" fill="{k['coat']}"/>
<path d="M6,-3 L18,-14 L29,-2" stroke="{k['coat']}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
<ellipse cx="31" cy="-1.5" rx="5" ry="3" fill="{k['hair']}"/>
<path d="M0,-22 C6,-18 12,-15 17,-13" stroke="{k['coat']}" stroke-width="5" stroke-linecap="round" fill="none" opacity=".95"/>
<circle cx="17" cy="-13" r="2.6" fill="{k['skin']}"/>
<path d="M-11,-29 C-6,-33 2,-33 6,-28" stroke="{k['scarf']}" stroke-width="6" stroke-linecap="round" fill="none"/>
<g transform="rotate(-22 -1 -40)">
<circle cx="-1" cy="-40" r="11" fill="{k['skin']}"/>
<path d="M-12,-41 C-13,-54 9,-56 11,-44 C8,-47 3,-49 -1,-47 C-4,-50 -9,-48 -12,-41Z" fill="{k['hair']}"/>
<path d="M-3,-50 l-2,-5 M1,-50 l2,-5" stroke="{k['hair']}" stroke-width="2" stroke-linecap="round"/>
<path d="M4,-41 q1.6,-1.6 3.2,0" stroke="{k['hair']}" stroke-width="1.3" stroke-linecap="round" fill="none"/>
<ellipse cx="5.5" cy="-36.5" rx="2.4" ry="1.4" fill="{c('pink', t)}" opacity=".6"/>
</g></g>"""


def header(t):
    H = 320
    k = SCENE["night" if t["night"] else "day"]
    p = [f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{k['sky'][0]}"/><stop offset=".6" stop-color="{k['sky'][1]}"/><stop offset="1" stop-color="{k['sky'][2]}"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>
<filter id="paper" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/>
<feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.45  0 0 0 0 0.4  0 0 0 .09 0"/></filter>
<radialGradient id="moonglow"><stop offset="0" stop-color="{k['moon']}" stop-opacity=".45"/><stop offset="1" stop-color="{k['moon']}" stop-opacity="0"/></radialGradient>
<mask id="cres"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="{812+13}" cy="{62-7}" r="24" fill="#000"/></mask>
</defs>
<rect width="{W}" height="{H}" rx="28" fill="url(#sky)"/>
<g clip-path="url(#card)">"""]
    # 별
    pts = [(40, 36), (98, 120), (170, 30), (250, 92), (330, 34), (300, 230), (380, 70), (520, 64), (600, 30),
           (660, 110), (720, 40), (880, 140), (860, 30), (60, 200), (430, 250), (470, 30), (600, 240), (240, 160),
           (690, 180), (560, 120), (350, 120)]
    for i, (x, y) in enumerate(pts):
        p.append(dot_star(x, y, 1.3 if i % 3 else 2, k["star"], 2.2 + (i % 5) * .6, (i % 7) * .4))
    p.append(sparkle(300, 76, 6, k["star"], 3) + sparkle(640, 70, 5, k["star"], 2.6, .9)
             + sparkle(200, 130, 4, k["star"], 3.4, 1.6) + sparkle(700, 140, 4, k["star"], 3, 2.1))
    p.append(shooting_star(560, 24, 180, dict(t, star=k["star"]), "a", delay=2))
    # 달 (오른쪽 위)
    p.append(f'<circle cx="812" cy="62" r="56" fill="url(#moonglow)"><animate attributeName="r" values="50;62;50" dur="6s" repeatCount="indefinite"/></circle>'
             f'<circle cx="812" cy="62" r="24" fill="{k["moon"]}" mask="url(#cres)"/>')
    # 고리 행성 (왼쪽 위)
    p.append(f'<g transform="translate(92,68) rotate(-18)"><circle r="12" fill="{c("lilac", t)}" opacity=".85"/>'
             f'<ellipse rx="22" ry="5.5" stroke="{c("gold", t)}" stroke-width="2" opacity=".8"/></g>')
    # 왼쪽 행성 + 앉은 아이
    lpx, lpy, lpr = 140, 430, 175
    p.append(planet(lpx, lpy, lpr, k, "L", craters=[(-70, 26, 13), (52, 18, 9)]))
    for gx in (60, 100, 205, 240):
        p.append(grass(gx, on_planet(gx, lpx, lpy, lpr), k))
    p.append(kid_sitting(lpx - 8, on_planet(lpx - 8, lpx, lpy, lpr) + 3, k, t))
    # 오른쪽 행성 + 가로등 + 장미
    rpx, rpy, rpr = 770, 440, 170
    p.append(planet(rpx, rpy, rpr, k, "R", craters=[(-60, 22, 11), (70, 30, 14)]))
    for gx in (680, 720, 830, 870):
        p.append(grass(gx, on_planet(gx, rpx, rpy, rpr), k))
    p.append(lamp(810, on_planet(810, rpx, rpy, rpr) + 4, k, "R"))
    p.append(rose_dome(740, on_planet(740, rpx, rpy, rpr) + 3, k))
    # 종이 질감
    p.append(f'<rect width="{W}" height="{H}" filter="url(#paper)"/>')
    # 가운데 타이틀
    cx = W / 2
    p.append(f'<text class="r" x="{cx}" y="140" font-size="36" font-style="italic" font-weight="700" letter-spacing=".5" '
             f'fill="{k["ink"]}" text-anchor="middle">{TITLE}</text>')
    p.append(sparkle(cx - 186, 170, 4, k["accent"]) + sparkle(cx + 186, 170, 4, k["accent"]))
    p.append(f'<text class="r" x="{cx}" y="175" font-size="13.5" letter-spacing="1.2" fill="{k["muted"]}" text-anchor="middle">{escape(TAGLINE)}</text>')
    p.append(f'<text class="m" x="{cx}" y="202" font-size="10" letter-spacing="2.6" fill="{k["muted"]}" text-anchor="middle" opacity=".85">— {MOTTO.upper()} —</text>')
    p.append("</g>")
    return svg(W, H, "\n".join(p))


# ---------------------------------------------------------------- FOOTER (지평선을 걸어가는 아이)
def walker(k, t):
    """오른쪽을 보고 걷는 아이. 원점 = 발 밑."""
    leg = lambda dx, phase: (
        f'<g transform="translate({dx},-14)"><line x1="0" y1="0" x2="0" y2="13" stroke="{k["coat"]}" stroke-width="4.5" stroke-linecap="round"/>'
        f'<ellipse cx="2" cy="13.5" rx="3.6" ry="2" fill="{k["hair"]}"/>'
        f'<animateTransform attributeName="transform" type="rotate" additive="sum" values="{phase};{-phase};{phase}" dur=".9s" repeatCount="indefinite"/></g>')
    arm = lambda phase, op: (
        f'<g transform="translate(0,-31)" opacity="{op}"><line x1="0" y1="0" x2="0" y2="12" stroke="{k["coat"]}" stroke-width="4" stroke-linecap="round"/>'
        f'<circle cx="0" cy="13" r="2.2" fill="{k["skin"]}"/>'
        f'<animateTransform attributeName="transform" type="rotate" additive="sum" values="{phase};{-phase};{phase}" dur=".9s" repeatCount="indefinite"/></g>')
    return f"""<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -1.6;0 0" dur=".45s" repeatCount="indefinite"/>
{arm(-24, ".7")}
{leg(-3, 22)}{leg(3, -22)}
<path d="M-8,-14 C-9,-24 -6,-34 0,-35 C6,-34 9,-24 8,-14Z" fill="{k['coat']}"/>
{arm(24, "1")}
<path stroke="{k['scarf']}" stroke-width="4" stroke-linecap="round" fill="none" d="M-2,-34 C-12,-36 -20,-30 -30,-35">
  <animate attributeName="d" dur="1.6s" repeatCount="indefinite" values="M-2,-34 C-12,-36 -20,-30 -30,-35;M-2,-34 C-12,-31 -21,-38 -31,-31;M-2,-34 C-12,-36 -20,-30 -30,-35"/></path>
<path d="M-6,-35 h11" stroke="{k['scarf']}" stroke-width="5" stroke-linecap="round"/>
<circle cx="1" cy="-45" r="9.5" fill="{k['skin']}"/>
<path d="M-9,-46 C-10,-57 9,-58 10,-48 C6,-51 1,-52 -2,-50 C-5,-52 -8,-50 -9,-46Z" fill="{k['hair']}"/>
<path d="M-2,-53 l-2,-4 M2,-53 l2,-4" stroke="{k['hair']}" stroke-width="1.8" stroke-linecap="round"/>
<circle cx="6" cy="-45" r="1.2" fill="{k['hair']}"/>
<ellipse cx="6" cy="-41" rx="2.1" ry="1.2" fill="{c('pink', t)}" opacity=".6"/>
</g>"""


def footer(t):
    H = 170
    k = SCENE["night" if t["night"] else "day"]
    ground = "M0,138 Q450,108 900,138"
    p = []
    # 별
    for i, (x, y) in enumerate([(60, 30), (150, 70), (260, 24), (370, 58), (500, 20), (590, 64), (700, 30), (820, 56),
                                 (870, 18), (420, 90), (120, 100), (760, 96)]):
        p.append(dot_star(x, y, 1.3 if i % 3 else 2, k["star"], 2.2 + (i % 5) * .6, (i % 7) * .4))
    p.append(sparkle(310, 40, 5, k["star"], 3) + sparkle(640, 46, 4, k["star"], 2.6, 1))
    p.append(shooting_star(560, 20, 150, dict(t, star=k["star"]), "f", delay=3))
    # 지평선 (행성 표면)
    p.append(f'<defs><linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{k["planet"]}"/>'
             f'<stop offset="1" stop-color="{k["crater"]}"/></linearGradient></defs>')
    p.append(f'<path d="{ground} L900,{H} L0,{H}Z" fill="url(#gr)"/>')
    for x, w in [(120, 14), (330, 10), (600, 16), (790, 11)]:
        y = 138 - 30 * (1 - ((x - 450) / 450) ** 2) + 12
        p.append(f'<ellipse cx="{x}" cy="{y:.1f}" rx="{w}" ry="{w*0.35:.1f}" fill="{k["crater"]}" opacity=".8"/>')

    def surf(x):  # 지평선 곡선 위 y
        return 138 - 30 * (1 - ((x - 450) / 450) ** 2)

    for gx in (70, 190, 260, 410, 520, 650, 720, 860):
        gy = surf(gx)
        p.append(f'<path d="M{gx-5},{gy+2:.1f} q2,-9 4,-1 q1,-11 3,0 q3,-8 4,1" stroke="{k["grass"]}" stroke-width="2" stroke-linecap="round" fill="none"/>')
    # 장미 (작게)
    rx_ = 560
    p.append(f'<g transform="translate({rx_},{surf(rx_)+2:.1f}) scale(.8)">'
             f'<path d="M0,0 L0,-20" stroke="{k["stem"]}" stroke-width="2.2" stroke-linecap="round"/>'
             f'<path d="M0,-9 q-8,-2 -9,-8 q7,0 9,6Z" fill="{k["stem"]}"/>'
             f'<path d="M-6,-24 q6,-10 12,0 q-1,7 -6,7 q-5,0 -6,-7Z" fill="{k["rose"]}"/></g>')
    # 가로등
    lx = 770
    ly = surf(lx) + 3
    p.append(f'<defs><radialGradient id="lg2"><stop offset="0" stop-color="{k["light"]}" stop-opacity=".7"/><stop offset="1" stop-color="{k["light"]}" stop-opacity="0"/></radialGradient></defs>'
             f'<circle cx="{lx}" cy="{ly-60:.1f}" r="30" fill="url(#lg2)"><animate attributeName="opacity" values="1;.55;1;.8;1" dur="4s" repeatCount="indefinite"/></circle>'
             f'<line x1="{lx}" y1="{ly:.1f}" x2="{lx}" y2="{ly-54:.1f}" stroke="{k["lamp"]}" stroke-width="3.2" stroke-linecap="round"/>'
             f'<path d="M{lx-8},{ly-54:.1f} L{lx+8},{ly-54:.1f} L{lx+5},{ly-66:.1f} L{lx-5},{ly-66:.1f}Z" fill="{k["lamp"]}"/>'
             f'<rect x="{lx-4}" y="{ly-64:.1f}" width="8" height="8" rx="2" fill="{k["light"]}"/>'
             f'<path d="M{lx-7},{ly-66:.1f} L{lx},{ly-73:.1f} L{lx+7},{ly-66:.1f}Z" fill="{k["lamp"]}"/>')
    # 걷는 아이: 지평선 곡선을 따라 왼쪽 → 오른쪽
    p.append(f'<g>{walker(k, t)}<animateMotion dur="26s" repeatCount="indefinite" path="M-40,{surf(-40)+1:.1f} Q450,{108+1} 940,{surf(940)+1:.1f}"/></g>')
    return svg(W, H, "\n".join(p))


# ---------------------------------------------------------------- STACK CHIPS
def text_w(s, size):
    return sum(size * (0.62 if ch.isupper() else 0.56 if ch.isalnum() else 0.4) for ch in s)


def icon(slug, x, y, size, color):
    if slug and slug in ICONS:
        return f'<path transform="translate({x},{y}) scale({size/24:.4f})" d="{ICONS[slug]}" fill="{color}"/>'
    m = size / 2
    return sparkle(x + m, y + m, m - 0.5, color)  # 아이콘이 없으면 작은 별


def label_glyph(i, x, y, col, t):
    """분야 라벨 앞 아이콘: 달 / 별 / 행성 / 혜성 / 반짝이."""
    cx, cy = x + 10, y + 11
    bg = t["chip_bg"] if t["night"] else "#FFFFFF"
    g = [
        f'<circle cx="{cx}" cy="{cy}" r="9" fill="{col}"/><circle cx="{cx+5}" cy="{cy-3}" r="8" fill="{bg}"/>',
        sparkle(cx, cy, 10, col),
        f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="{col}"/><ellipse cx="{cx}" cy="{cy}" rx="11" ry="3.5" stroke="{col}" stroke-width="1.8" transform="rotate(-20 {cx} {cy})"/>',
        f'<path d="M{cx-11},{cy-7} L{cx+2},{cy+1}" stroke="{col}" stroke-width="2" stroke-linecap="round" opacity=".6"/><path d="M{cx-8},{cy-11} L{cx+1},{cy-3}" stroke="{col}" stroke-width="1.5" stroke-linecap="round" opacity=".4"/><circle cx="{cx+4}" cy="{cy+3}" r="5.5" fill="{col}"/>',
        sparkle(cx - 3, cy + 2, 7, col) + sparkle(cx + 6, cy - 5, 4, col),
    ]
    return g[i % len(g)]


def stack(t):
    size, h, gap, rowh = 16, 38, 9, 54
    rows_svg, y = [], 12
    for i, (label, ck, items) in enumerate(STACK):
        col = c(ck, t)
        lw = 30 + text_w(label, 14) * 1.25 + 14
        chips = [(n, s, 12 + 20 + 8 + text_w(n, size) + 14) for n, s in items]
        total = lw + sum(w for *_, w in chips) + gap * len(chips)
        x = (W - total) / 2
        part = [label_glyph(i, x, y + 8, col, t),
                f'<text class="m" x="{x+30}" y="{y+25}" font-size="14" letter-spacing="2" font-weight="600" fill="{t["muted"]}">{label}</text>']
        x += lw
        for n, s, w in chips:
            part.append(f'<rect x="{x+1:.1f}" y="{y+1}" width="{w-2:.1f}" height="{h-2}" rx="{h/2}" fill="{t["chip_bg"]}" '
                        f'stroke="{col}" stroke-width="2"/>')
            part.append(icon(s, x + 13, y + 11, 16, col))
            part.append(f'<text class="s" x="{x+38:.1f}" y="{y+24.5}" font-size="{size}" font-weight="600" fill="{col}">{escape(n)}</text>')
            x += w + gap
        rows_svg.append("\n".join(part))
        y += rowh
    return svg(W, y - rowh + h + 16, "\n".join(rows_svg))


# ---------------------------------------------------------------- PROJECT CARDS
def telescope(x, y, t):
    col, st = c("lilac", t), c("gold", t)
    return f"""<g transform="translate({x},{y})">
{sparkle(30, -48, 9, st, 2.4)}{sparkle(52, -22, 5, st, 3, .6)}{sparkle(8, -62, 4, st, 2.8, 1.1)}
<g transform="rotate(-28)"><rect x="-44" y="-9" width="62" height="18" rx="6" fill="{col}"/>
<rect x="16" y="-12" width="12" height="24" rx="4" fill="{col}"/><rect x="-52" y="-6" width="10" height="12" rx="3" fill="{col}" opacity=".7"/></g>
<line x1="-10" y1="8" x2="-28" y2="44" stroke="{t['muted']}" stroke-width="3" stroke-linecap="round"/>
<line x1="-10" y1="8" x2="6" y2="44" stroke="{t['muted']}" stroke-width="3" stroke-linecap="round"/>
<line x1="-10" y1="8" x2="-10" y2="46" stroke="{t['muted']}" stroke-width="3" stroke-linecap="round"/></g>"""


def project(name, desc, tech, art, ck, t):
    PW, PH = 440, 170
    col = c(ck, t)
    if art == "constellation":
        deco = constellation([(318, 120), (346, 82), (384, 98), (404, 54), (366, 38)],
                             [(0, 1), (1, 2), (2, 3), (3, 4)], dict(t, star=col), r=3.4, line_op=".7")
    else:
        deco = telescope(372, 104, t)
    body = f"""<rect x="1.5" y="1.5" width="{PW-3}" height="{PH-3}" rx="22" fill="{t['card']}" stroke="{t['line']}" stroke-width="2"/>
{deco}
<text class="m" x="28" y="42" font-size="13" letter-spacing="2" fill="{t['muted']}">PROJECT</text>
<text class="s" x="26" y="88" font-size="32" font-weight="800" letter-spacing="-.5" fill="{t['ink']}">{name}</text>
<text class="s" x="28" y="116" font-size="16" fill="{t['muted']}">{escape(desc)}</text>
<rect x="28" y="130" width="{text_w(tech, 13) + 24:.0f}" height="24" rx="12" fill="{col}" fill-opacity=".16"/>
<text class="s" x="40" y="146.5" font-size="13" font-weight="600" fill="{col}">{escape(tech)}</text>"""
    return svg(PW, PH, body)


# ---------------------------------------------------------------- ACTIVITY
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch_contributions(user):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        q = ('query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{'
             'weeks{contributionDays{date contributionCount contributionLevel}}}}}}')
        req = urllib.request.Request("https://api.github.com/graphql",
                                     data=json.dumps({"query": q, "variables": {"u": user}}).encode(),
                                     headers={"Authorization": f"bearer {token}", "User-Agent": "profile-svg"})
        weeks = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [(date.fromisoformat(d["date"]), d["contributionCount"], LEVEL[d["contributionLevel"]])
                for w in weeks for d in w["contributionDays"]]
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "profile-svg"})
    html = urllib.request.urlopen(req).read().decode()
    cells = re.findall(r'<td[^>]*data-date="([\d-]+)"[^>]*id="([\w-]+)"[^>]*data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([\w-]+)"[^>]*>([^<]*)</tool-tip>', html))
    out = []
    for d, cid, lv in cells:
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        out.append((date.fromisoformat(d), int(m.group(1)) if m else 0, int(lv)))
    return sorted(out)


def streaks(days):
    counts = {d: n for d, n, _ in days}
    longest = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    cur, d = 0, days[-1][0]
    if not counts.get(d):
        d -= timedelta(days=1)
    while counts.get(d):
        cur, d = cur + 1, d - timedelta(days=1)
    return cur, longest


def activity(t, days):
    total = sum(n for _, n, _ in days)
    cur, longest = streaks(days)
    stats = [(f"{total:,}", "contributions", "lilac"), (f"{cur}", "day streak", "gold"), (f"{longest}", "longest streak", "sky")]
    p = [f'<rect x="1.5" y="1.5" width="{W-3}" height="__H__" rx="24" fill="{t["card"]}" stroke="{t["line"]}" stroke-width="2"/>']
    for i, (num, cap, ck) in enumerate(stats):
        cx = W / 6 + i * W / 3
        p.append(f'<text class="s" x="{cx}" y="74" font-size="40" font-weight="800" fill="{c(ck, t)}" text-anchor="middle">{num}</text>')
        p.append(f'<text class="m" x="{cx}" y="100" font-size="13" letter-spacing="1" fill="{t["muted"]}" text-anchor="middle">{cap}</text>')
        if i:
            p.append(f'<line x1="{i*W/3}" y1="44" x2="{i*W/3}" y2="104" stroke="{t["line"]}" stroke-width="1.5"/>')
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    weeks = (days[-1][0] - start).days // 7 + 1
    step = (W - 64) / weeks
    cell = step - 3
    gx, gy, last = 32, 150, None
    for d, n, lv in days:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        x = gx + col * step
        if d.day <= 7 and row == 0 and d.month != last and col < weeks - 2:
            p.append(f'<text class="m" x="{x:.1f}" y="{gy-10}" font-size="11" fill="{t["muted"]}">{d:%b}</text>')
            last = d.month
        if lv == 4:  # 가장 많이 한 날은 별로
            p.append(sparkle(x + cell / 2, gy + row * step + cell / 2, cell / 2 + 1.5, t["levels"][4], 2.4, (col % 5) * .3))
        else:
            p.append(f'<rect x="{x:.1f}" y="{gy + row*step:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3" fill="{t["levels"][lv]}"/>')
    end = gy + 7 * step
    p.append(f'<text class="m" x="32" y="{end+28:.0f}" font-size="12" fill="{t["muted"]}">last 12 months · updated {days[-1][0]:%Y-%m-%d}</text>')
    lx = W - 32 - 5 * 15 - 34
    p.append(f'<text class="m" x="{lx-8}" y="{end+28:.0f}" font-size="12" fill="{t["muted"]}" text-anchor="end">less</text>')
    for i in range(4):
        p.append(f'<rect x="{lx + i*15}" y="{end+18:.0f}" width="11" height="11" rx="2.5" fill="{t["levels"][i]}"/>')
    p.append(sparkle(lx + 4 * 15 + 5.5, end + 23.5, 7, t["levels"][4]))
    p.append(f'<text class="m" x="{lx + 5*15 + 4}" y="{end+28:.0f}" font-size="12" fill="{t["muted"]}">more</text>')
    H = end + 50
    return svg(W, H, "\n".join(p).replace("__H__", f"{H-3:.0f}"))


def main():
    days = fetch_contributions(USERNAME)
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.svg"):
        f.unlink()
    for mode, t in THEMES.items():
        (OUT / f"header-{mode}.svg").write_text(header(t), encoding="utf-8")
        (OUT / f"stack-{mode}.svg").write_text(stack(t), encoding="utf-8")
        (OUT / f"footer-{mode}.svg").write_text(footer(t), encoding="utf-8")
        (OUT / f"activity-{mode}.svg").write_text(activity(t, days), encoding="utf-8")
        for name, desc, tech, art, ck in PROJECTS:
            (OUT / f"project-{name}-{mode}.svg").write_text(project(name, desc, tech, art, ck, t), encoding="utf-8")
    print(f"{len(days)} days, total {sum(n for _, n, _ in days)} ->", sorted(f.name for f in OUT.glob('*.svg')))


if __name__ == "__main__":
    main()
