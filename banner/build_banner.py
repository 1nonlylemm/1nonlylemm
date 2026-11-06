#!/usr/bin/env python3
"""Builds assets/banner.svg, the animated Bytebug arena header for the README.

    python banner/build_banner.py            # new random shuffle every run
    python banner/build_banner.py 42         # same seed -> same banner

Each run picks new Bytebug pairs, lanes, walking speeds and a random emotion for
every bump. Within one banner each pair cycles through several bumps with
different emotions, so the loop doesn't feel repetitive.

data.json holds the sprite frames (rendered from the portfolio's Bytebug Battle
canvas code) and the Syne / DM Sans text already converted to outlines.
"""
import json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'banner.svg')
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf8'))
rng = random.Random(sys.argv[1] if len(sys.argv) > 1 else None)

W, H = 1000, 540
HORIZON = 238
BACK, MID, FRONT = (312, .74), (394, .87), (506, 1.0)
BU = D['bug']['scale']                     # display px per bug unit
BUG_W, BUG_H = 80 * BU, 64 * BU
BUG_X, BUG_Y = -40 * BU, -56 * BU          # sprite origin -> feet on the ground
LOOPS = 4                                  # bumps per pair before the pattern repeats

EMOTIONS = {
    # name: (face frame, bubble icon, icon color)
    'happy':     ('happy',   'note',    '#7fd1a8'),
    'angry':     ('angry',   'anger',   '#e25a4f'),
    'excited':   ('excited', 'bang2',   '#f2c46d'),
    'love':      ('love',    'heart',   '#e8435f'),
    'shock':     ('shock',   'bang',    '#f08a4b'),
    'sad':       ('sad',     'drop',    '#7fc4f0'),
    'dizzy':     ('dizzy',   'star',    '#f2e3a8'),
    'smug':      ('smug',    'sparkle', '#b8d5ef'),
    'flustered': ('blush3',  'slash',   '#f08aa0'),
}
ICONS = {
    'heart':   ['01100110', '11111111', '11111111', '11111111', '01111110', '00111100', '00011000', '00000000'],
    'anger':   ['01100110', '11000011', '10000001', '00000000', '00000000', '10000001', '11000011', '01100110'],
    'bang2':   ['01100110', '01100110', '01100110', '01100110', '01100110', '00000000', '01100110', '01100110'],
    'bang':    ['00011000', '00011000', '00011000', '00011000', '00011000', '00000000', '00011000', '00011000'],
    'note':    ['00011000', '00011100', '00010110', '00010010', '00010000', '01110000', '11110000', '01100000'],
    'drop':    ['00010000', '00111000', '00111000', '01111100', '01111100', '01111100', '00111000', '00000000'],
    'star':    ['00010000', '00010000', '11111110', '01111100', '00111000', '01101100', '01000100', '00000000'],
    'sparkle': ['00010000', '00010000', '00111000', '11111110', '00111000', '00010000', '00010000', '00000000'],
    'slash':   ['00000000', '00100100', '01001001', '10010010', '00100100', '01001000', '00000000', '00000000'],
}

defs, css, body = [], [], []
images, anim_count = {}, [0]
start_offset = [0.0]   # each pair starts at a random point so bumps don't all happen at once


def num(v):
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def image(url, w, h):
    """Each PNG is stored once in <defs> and reused with <use>."""
    if url not in images:
        images[url] = f'i{len(images)}'
        defs.append(f'<image id="{images[url]}" width="{num(w)}" height="{num(h)}" href="{url}"/>')
    return images[url]


def anim(period, points, value, timing='linear'):
    """Returns an inline style for a keyframe animation through (time, value) points."""
    anim_count[0] += 1
    name = f'a{anim_count[0]}'
    pts = sorted(points, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < period:
        pts.append((period, pts[-1][1]))
    frames, seen = [], set()
    for t, v in pts:
        pct = num(max(0, min(100, t / period * 100)))
        if pct in seen:
            pct = num(float(pct) + .01)
        seen.add(pct)
        frames.append(f'{pct}%{{{value(v)}}}')
    css.append(f'@keyframes {name}{{{"".join(frames)}}}')
    return f'animation:{name} {num(period)}s {timing} -{num(start_offset[0])}s infinite'


def window(period, spans):
    """Visible only inside the given (start, end) spans."""
    pts = [(0, 0)]
    for a, b in spans:
        pts += [(a, 1), (b, 0)]
    return anim(period, pts, lambda v: f'opacity:{v}', 'steps(1,end)')


def move(t, x=0, y=0, r=0):
    return (t, (x, y, r))


def tf(v):
    x, y, r = v
    return f'transform:translate({num(x)}px,{num(y)}px) rotate({num(r)}deg)'


def emotion_motion(kind, t0, length):
    """Body motion while an emotion plays, as (time, (x, y, rotate)) points."""
    p = [move(t0)]
    if kind == 'happy':
        for i in range(3):
            p += [move(t0 + i * .5 + .15, y=-7), move(t0 + i * .5 + .3)]
    elif kind == 'excited':
        for i in range(4):
            p += [move(t0 + i * .42 + .14, y=-15), move(t0 + i * .42 + .28)]
    elif kind == 'angry':
        for i in range(16):
            p.append(move(t0 + .1 + i * .06, x=3 if i % 2 else -3))
        p.append(move(t0 + 1.1))
        p += [move(t0 + 1.5, y=-5), move(t0 + 1.62)]
    elif kind == 'love':
        p += [move(t0 + .6, y=-6), move(t0 + 1.2), move(t0 + 1.8, y=-6), move(t0 + 2.3)]
    elif kind == 'shock':
        p += [move(t0 + .1, y=-14), move(t0 + .26), move(t0 + .34, y=-3), move(t0 + .42)]
    elif kind == 'sad':
        p += [move(t0 + .5, y=2), move(t0 + length - .2, y=2)]
    elif kind == 'dizzy':
        for i in range(8):
            p.append(move(t0 + .1 + i * .25, r=9 if i % 2 else -9))
    elif kind == 'smug':
        p += [move(t0 + .25, r=-7), move(t0 + length - .3, r=-7)]
    elif kind == 'flustered':
        for i in range(10):
            p.append(move(t0 + .1 + i * .18, x=2 if i % 2 else -2))
    p.append(move(t0 + length))
    return p


def bubble(icon, color, period, t0, t1):
    rows = ICONS[icon]
    px = ''.join(f'<rect x="{num(4 + i * 1.75)}" y="{num(-22 + j * 1.75)}" width="1.75" height="1.75"/>'
                 for j, row in enumerate(rows) for i, c in enumerate(row) if c == '1')
    pop = anim(period, [(0, 0), (t0, 0), (t0 + .12, 1.25), (t0 + .24, 1), (t1 - .16, 1), (t1, 0)],
               lambda s: f'transform:translate(0px,{num((1 - min(s, 1)) * 6)}px) scale({num(s)})')
    return (f'<g style="{pop}">'
            f'<rect x="-2" y="-26" width="26" height="22" rx="4" fill="#15161b"/>'
            f'<path d="M1 -6h7l-6 6z" fill="#15161b"/>'
            f'<rect x="0" y="-24" width="22" height="18" rx="2.5" fill="#f4f1ea"/>'
            f'<path d="M3 -7h4l-3 3z" fill="#f4f1ea"/>'
            f'<g fill="{color}">{px}</g></g>')


def bug_pair(a, b, lane, left, right):
    ground, s = lane
    hw = {n: D['hw'][n] * BU * s for n in (a, b)}
    xa0, xb0 = left + hw[a], right - hw[b]
    meet = (left + right) / 2 + rng.uniform(-25, 25)
    xa1, xb1 = meet - hw[a] * .82, meet + hw[b] * .82
    speed = rng.uniform(42, 64) * s
    knock = 11 * s
    t1 = rng.uniform(.3, 1.6)
    t2 = t1 + max(xa1 - xa0, xb0 - xb1) / speed
    te0 = t2 + .5
    te1 = te0 + rng.uniform(2.2, 2.8)
    t3 = te1 + .1
    t4 = t3 + max(xa1 - xa0, xb0 - xb1) / (speed * rng.uniform(.85, 1.1))
    rest = rng.uniform(.5, 1.6)
    period = t4 + rest
    long_period = period * LOOPS
    start_offset[0] = rng.uniform(0, long_period)

    # Random emotion per bug per bump, never the same twice in a row.
    feelings = {}
    for n in (a, b):
        seq = []
        for _ in range(LOOPS):
            seq.append(rng.choice([e for e in EMOTIONS if not seq or e != seq[-1]]))
        feelings[n] = seq

    out = []
    for n, x0, x1, kdir, facing in ((a, xa0, xa1, -1, 1), (b, xb0, xb1, 1, -1)):
        frames = D['bugs'][n]
        go = anim(period, [(0, x0), (t1, x0), (t2, x1), (t2 + .16, x1 + kdir * knock), (t3, x1 + kdir * knock), (t4, x0)],
                  lambda x: f'transform:translate({num(x)}px,0px)')
        if n == 'Keycap Jumper':   # its ESC label would read backwards
            facing = 0
        flip = anim(period, [(0, facing or 1), (t3, -facing or 1), (t4 + rest * .5, facing or 1)],
                    lambda f: f'transform:scale({f},1)', 'steps(1,end)')
        hop_pts, hits, emos, bubbles = [], [], [], []
        delay = rng.uniform(0, .3)
        for k, feel in enumerate(feelings[n]):
            o = k * period
            hop_pts += [move(o + t2), move(o + t2 + .08, y=-5), move(o + t2 + .2)]
            hop_pts += emotion_motion(feel, o + te0, te1 - te0)
            hits.append((o + t2, o + te0))
            face, icon, color = EMOTIONS[feel]
            if feel == 'flustered':
                face = rng.choice(['blush2', 'blush3'])
            emos.append((face, o + te0, o + te1))
            bubbles.append(bubble(icon, color, long_period, o + te0, o + te1 - .05))
        hop = anim(long_period, hop_pts, tf)
        # Walking frames hide while the bump + emotion faces are showing.
        vis, cur = [], 0
        for s0, s1 in ((k * period + t2, k * period + te1) for k in range(LOOPS)):
            vis.append((cur, s0))
            cur = s1
        vis.append((cur, long_period))
        walk_vis = window(long_period, vis)
        wa, wb = image(frames['walkA'], BUG_W, BUG_H), image(frames['walkB'], BUG_W, BUG_H)
        hit_id = image(frames['hit'], BUG_W, BUG_H)
        faces = ''.join(
            f'<use href="#{image(frames[f], BUG_W, BUG_H)}" x="{num(BUG_X)}" y="{num(BUG_Y)}" style="{window(long_period, [(e0, e1)])}"/>'
            for f, e0, e1 in emos)
        shadow_w = D['hw'][n] * BU * s * .95
        out.append(
            f'<g transform="translate(0 {ground})"><g style="{go}">'
            f'<ellipse rx="{num(shadow_w)}" ry="{num(6 * s)}" fill="url(#shadow)"/>'
            f'<g transform="scale({s})"><g style="{hop}"><g style="{flip}">'
            f'<g style="{walk_vis}">'
            f'<use href="#{wa}" x="{num(BUG_X)}" y="{num(BUG_Y)}" class="fa" style="animation-delay:-{num(delay)}s"/>'
            f'<use href="#{wb}" x="{num(BUG_X)}" y="{num(BUG_Y)}" class="fb" style="animation-delay:-{num(delay)}s"/></g>'
            f'<use href="#{hit_id}" x="{num(BUG_X)}" y="{num(BUG_Y)}" style="{window(long_period, hits)}"/>'
            f'{faces}</g></g>'
            f'<g transform="translate(6 -62) scale(1.6)">{"".join(bubbles)}</g>'
            f'</g></g></g>')

    # Little impact flash where they bump.
    bang = anim(period, [(0, 0), (t2 - .01, 0), (t2 + .05, 1.3), (t2 + .3, 0)],
                lambda v: f'transform:scale({num(v)});opacity:{num(min(1, v))}')
    out.append(
        f'<g transform="translate({num(meet)} {ground - 26 * s}) scale({s})"><g style="{bang}" fill="#f6e7b0">'
        f'<rect x="-1.5" y="-12" width="3" height="7"/><rect x="-1.5" y="5" width="3" height="7"/>'
        f'<rect x="-12" y="-1.5" width="7" height="3"/><rect x="5" y="-1.5" width="7" height="3"/>'
        f'<rect x="-8" y="-8" width="3" height="3"/><rect x="5" y="-8" width="3" height="3"/>'
        f'<rect x="-8" y="5" width="3" height="3"/><rect x="5" y="5" width="3" height="3"/></g></g>')
    return out


def lem():
    start_offset[0] = 0
    L = D['lem']
    k = L['k']
    iw, ih = L['w'] * k, L['h'] * k
    ix, iy = -(L['ox'] + 32) * k, -(L['oy'] + 92) * k
    ground = FRONT[0]
    x0, x1, speed = 432, 568, 30
    t1 = 1.4
    t2 = t1 + (x1 - x0) / speed
    t3 = t2 + 2.2
    t4 = t3 + (x1 - x0) / speed
    period = t4 + 1.0
    go = anim(period, [(0, x0), (t1, x0), (t2, x1), (t3, x1), (t4, x0)], lambda x: f'transform:translate({num(x)}px,0px)')
    flip = anim(period, [(0, 1), (t2 + 1.1, -1), (t4 + .5, 1)], lambda f: f'transform:scale({f},1)', 'steps(1,end)')
    walking = window(period, [(t1, t2), (t3, t4)])
    standing = window(period, [(0, t1), (t2, t3), (t4, period)])

    # Dark Boulder in Lem's arms: flustered, blushing, never quite still.
    seq = [('blush', 1.4), ('blush2', .9), ('blush', .5), ('blush3', 1.1), ('blush4', 1.3),
           ('blush2', .7), ('blush3', .5), ('blush', .9), ('blush4', .8)]
    total = sum(d for _, d in seq)
    t, face_spans = 0, {}
    for f, d in seq:
        face_spans.setdefault(f, []).append((t, t + d))
        t += d
    faces = ''.join(
        f'<use href="#{image(L["boulder"][f], iw, ih)}" x="{num(ix)}" y="{num(iy)}" style="{window(total, spans)}"/>'
        for f, spans in face_spans.items())
    bx, by = ix + (L['ox'] + 67 / 1.8125) * k, iy + (L['oy'] + 72 / 1.8125) * k
    wiggle = anim(1.6, [(0, (0, 0, -3)), (.4, (0, -1, 3)), (.8, (0, 0, -3)), (1.2, (0, -1, 3)), (1.6, (0, 0, -3))], tf, 'ease-in-out')
    hearts = ''
    for i, (hx, delay) in enumerate(((-8, 0), (10, .8), (2, 1.6))):
        rise = anim(2.4, [(0, (0, 0, 0)), (2.4, (hx * .4, -40, 0))], tf)
        fade = anim(2.4, [(0, 0), (.2, 1), (1.6, 1), (2.4, 0)], lambda v: f'opacity:{v}')
        heart = ''.join(f'<rect x="{i2 * 2}" y="{j * 2}" width="2" height="2"/>'
                        for j, row in enumerate(['01010', '11111', '11111', '01110', '00100']) for i2, c in enumerate(row) if c == '1')
        hearts += (f'<g transform="translate({num(bx + hx - 5)} {num(by - 40)})"><g style="{rise};animation-delay:-{delay}s">'
                   f'<g style="{fade};animation-delay:-{delay}s" fill="#f08aa0">{heart}</g></g></g>')
    boulder = (f'<g transform="translate({num(bx)} {num(by)})"><g style="{wiggle}">'
               f'<g transform="translate({num(-bx)} {num(-by)})">{faces}</g></g></g>')
    hands = f'<use href="#{image(L["hands"], iw, ih)}" x="{num(ix)}" y="{num(iy)}"/>'
    stride = ''.join(f'<use href="#{image(L["frames"][f], iw, ih)}" x="{num(ix)}" y="{num(iy + dy)}" class="l{i}"/>'
                     for i, (f, dy) in enumerate((('s0', 0), ('s2', 1), ('s0', 0), ('s-1', -1))))
    stand = f'<use href="#{image(L["frames"]["s0"], iw, ih)}" x="{num(ix)}" y="{num(iy)}"/>'
    return (f'<g transform="translate(0 {ground})"><g style="{go}">'
            f'<ellipse rx="46" ry="8" fill="url(#shadow)"/>'
            f'<g style="{flip}">'
            f'<g style="{walking}"><g class="bob">{stride}{boulder}{hands}</g></g>'
            f'<g style="{standing}">{stand}{boulder}{hands}</g>'
            f'</g>{hearts}</g></g>')


def text(key, x, y, fill):
    t = D['text'][key]
    return f'<path transform="translate({num(x)} {y})" fill="{fill}" d="{t["d"]}"/>', t['w']


def heading():
    T = D['text']
    out = []
    # design ◆ develop ◆ deploy
    words, gap = ['k_design', 'k_develop', 'k_deploy'], 26
    total = sum(T[w]['w'] for w in words) + gap * 2
    x = 500 - total / 2
    for i, w in enumerate(words):
        p, wd = text(w, x, 46, '#8f97a8')
        out.append(p)
        x += wd
        if i < 2:
            out.append(f'<path d="M{num(x + gap / 2)} 36l3 3-3 3-3-3z" fill="#5d6576"/>')
            x += gap
    out.append(text('name', 500 - T['name']['w'] / 2, 124, '#f4f1ea')[0])
    out.append(text('role', 500 - T['role']['w'] / 2, 166, 'url(#silver)')[0])
    stats, sp, sep = [('n1', 'l1'), ('n2', 'l2'), ('n3', 'l3')], 8, 34
    total = sum(T[n]['w'] + sp + T[l]['w'] for n, l in stats) + sep * 2
    x = 500 - total / 2
    for i, (n, l) in enumerate(stats):
        out.append(text(n, x, 210, '#f2c46d')[0])
        x += T[n]['w'] + sp
        out.append(text(l, x, 210, '#aab1bf')[0])
        x += T[l]['w']
        if i < 2:
            cx = x + sep / 2
            out.append(f'<rect x="{num(cx - 2)}" y="201" width="4" height="4" fill="#5d6576"/>')
            x += sep
    return out


def floor():
    d = [f'M500 {HORIZON}L{x} {H}' for x in range(-800, W + 880, 84)]
    y, step = HORIZON, 5.0
    while y < H:
        d.append(f'M0 {num(y)}H{W}')
        y += step
        step *= 1.3
    return [f'<rect width="{W}" height="{H}" fill="url(#wall)"/>',
            f'<rect width="{W}" height="{HORIZON}" fill="url(#dots)" opacity=".7"/>',
            f'<rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#ground)"/>',
            f'<path d="{"".join(d)}" stroke="#3d414c" fill="none" clip-path="url(#below)"/>',
            f'<rect y="{HORIZON}" width="{W}" height="2" fill="#4c515e" opacity=".7"/>',
            f'<rect width="{W}" height="{H}" fill="url(#spot)"/>']


# Roster: Dark Boulder rides with Lem, the other 14 split into random pairs.
roster = [n for n in D['bugs'] if n != 'Dark Boulder']
rng.shuffle(roster)
pairs = [roster[i:i + 2] for i in range(0, 14, 2)]
slots = [(BACK, 40, 345), (BACK, 345, 655), (BACK, 655, 960),
         (MID, 24, 384), (MID, 616, 976),
         (FRONT, 24, 350), (FRONT, 650, 976)]
actors = [bug_pair(a, b, *slot) for (a, b), slot in zip(pairs, slots)]

scene = []
for i in range(5):
    scene += actors[i]
scene.append(lem())
for i in range(5, 7):
    scene += actors[i]

head = heading()
style = ('.fa{animation:fa .34s steps(1,end) infinite}.fb{animation:fb .34s steps(1,end) infinite}'
         '@keyframes fa{0%{opacity:1}50%{opacity:0}}@keyframes fb{0%{opacity:0}50%{opacity:1}}'
         '.l0,.l1,.l2,.l3{opacity:0;animation:.72s steps(1,end) infinite}'
         '.l0{animation-name:l0}.l1{animation-name:l1}.l2{animation-name:l2}.l3{animation-name:l3}'
         '@keyframes l0{0%{opacity:1}25%{opacity:0}}@keyframes l1{0%{opacity:0}25%{opacity:1}50%{opacity:0}}'
         '@keyframes l2{0%{opacity:0}50%{opacity:1}75%{opacity:0}}@keyframes l3{0%{opacity:0}75%{opacity:1}}'
         '.bob{animation:bob .36s steps(1,end) infinite}@keyframes bob{0%{transform:translate(0,0)}50%{transform:translate(0,-2px)}}'
         + ''.join(css))
svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
    '<title id="title">Luis Mario Acovera — Full Stack Developer</title>',
    '<desc id="desc">Luis Mario Acovera, Full Stack Developer. In the Bytebug Battle arena below, Lem walks around carrying a '
    'blushing Dark Boulder while the other fourteen Bytebugs wander, bump into each other and react with random emotions.</desc>',
    f'<style>{style}</style>',
    '<defs>',
    '<linearGradient id="wall" x2="0" y2="1"><stop stop-color="#0f1015"/><stop offset=".44" stop-color="#171920"/><stop offset="1" stop-color="#262932"/></linearGradient>',
    f'<linearGradient id="ground" x2="0" y2="1"><stop stop-color="#1b1d24"/><stop offset="1" stop-color="#2a2d36"/></linearGradient>',
    '<pattern id="dots" x="14" y="18" width="21" height="21" patternUnits="userSpaceOnUse"><rect width="1.2" height="1.2" fill="#666b78"/></pattern>',
    f'<radialGradient id="spot" cx="500" cy="{FRONT[0]}" r="300" gradientTransform="translate(0 {FRONT[0]}) scale(1 .45) translate(0 -{FRONT[0]})" gradientUnits="userSpaceOnUse"><stop stop-color="#b8d5ef" stop-opacity=".12"/><stop offset="1" stop-color="#b8d5ef" stop-opacity="0"/></radialGradient>',
    '<linearGradient id="silver" x2="0" y2="1"><stop stop-color="#f1f3f6"/><stop offset=".55" stop-color="#c3c8d0"/><stop offset="1" stop-color="#9aa1ac"/></linearGradient>',
    '<radialGradient id="shadow"><stop stop-color="#000" stop-opacity=".5"/><stop offset=".6" stop-color="#000" stop-opacity=".3"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>',
    f'<clipPath id="below"><rect y="{HORIZON}" width="{W}" height="{H - HORIZON}"/></clipPath>',
    f'<clipPath id="edge"><rect width="{W}" height="{H}" rx="16"/></clipPath>',
    *defs,
    '</defs>',
    '<g clip-path="url(#edge)">',
    *floor(), *head, *scene,
    '</g>',
    f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="#353945"/>',
    '</svg>',
]
open(OUT, 'w', encoding='utf8').write('\n'.join(svg))
print(f'wrote {os.path.relpath(OUT)} ({os.path.getsize(OUT) // 1024} KB, {len(images)} images)')
