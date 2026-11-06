#!/usr/bin/env python3
"""Builds assets/banner.svg, the animated Bytebug arena header for the README.

    python banner/build_banner.py            # new random shuffle every run
    python banner/build_banner.py 42         # same seed -> same banner

What happens in the banner:
  * Lem walks around the arena carrying a blushing Bytebug in his arms.
  * The other Bytebugs wander in pairs, bump into each other and react with a
    random emotion each time.
  * Every 15 seconds a Bytebug runs over, bumps Lem's legs and begs to be carried
    (puppy eyes, crying, or a tsundere "hmph!"). Lem puts down the one he is
    holding, which is sad for a moment and then goes back to wandering, and
    picks up the new one.

A README image can't run code, so the whole story is planned here and baked
into CSS keyframes. It loops seamlessly: the order of carried Bytebugs is chosen
so everyone ends up back where they started.

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
BACK, MID, FRONT = 300, 392, 506            # ground lines of the three lanes


def lane_scale(gy):
    return .72 + (gy - BACK) / (FRONT - BACK) * .28


# Bug sprites (display px). Roaming bugs are anchored at their feet.
BUG = D['bug']
BU = BUG['scale']
FEET = 19 * BU                              # bug origin -> feet
IMG_X, IMG_Y = -BUG['ox'], -(BUG['oy'] + FEET)
# Lem: 2 display px per sprite px, anchored at the feet.
LEM = D['lem']
LK = LEM['k']
LEM_W, LEM_H = LEM['w'] * LK, LEM['h'] * LK
LEM_X, LEM_Y = -LEM['anchor'][0] * LK, -LEM['anchor'][1] * LK
CARRY_X = (LEM['carry']['x'] - LEM['anchor'][0]) * LK
CARRY_Y = (LEM['carry']['y'] - LEM['anchor'][1]) * LK
CARRY_S = LEM['carry']['unit'] * LK / BU    # carried bug size relative to a front-lane bug
CARRY_FEET = (CARRY_Y + FEET * CARRY_S) / CARRY_S   # hop height that lands a bug in Lem's arms

SWAP_EVERY = 15
FIRST_SWAP = 10
CARRY_SEATS = 4                             # seats whose bugs take turns being carried

EMOTIONS = {   # name: (face, bubble)
    'happy': ('happy', 'note'), 'angry': ('angry', 'anger'), 'excited': ('excited', 'bang2'),
    'love': ('love', 'heart'), 'shock': ('shock', 'bang'), 'sad': ('sad', 'drop'),
    'dizzy': ('dizzy', 'star'), 'smug': ('smug', 'sparkle'), 'flustered': ('blush3', 'slash'),
}
STORY = {'plead': ('plead', 'pls'), 'cry': ('cry', 'waah'), 'tsundere': ('tsundere', 'hmph')}
ICONS = {
    'heart':   ('#e8435f', ['01100110', '11111111', '11111111', '11111111', '01111110', '00111100', '00011000']),
    'anger':   ('#e25a4f', ['01100110', '11000011', '10000001', '00000000', '10000001', '11000011', '01100110']),
    'bang2':   ('#e0a93a', ['01100110', '01100110', '01100110', '01100110', '00000000', '01100110', '01100110']),
    'bang':    ('#f08a4b', ['00011000', '00011000', '00011000', '00011000', '00000000', '00011000', '00011000']),
    'note':    ('#4fb487', ['00011000', '00011100', '00010110', '00010010', '01110000', '11110000', '01100000']),
    'drop':    ('#4f9fd6', ['00010000', '00111000', '00111000', '01111100', '01111100', '01111100', '00111000']),
    'star':    ('#e0b93a', ['00010000', '00010000', '11111110', '01111100', '00111000', '01101100', '01000100']),
    'sparkle': ('#6f9fd0', ['00010000', '00010000', '00111000', '11111110', '00111000', '00010000', '00010000']),
    'slash':   ('#f08aa0', ['00100100', '01001001', '10010010', '00100100', '01001000', '00000000', '00000000']),
}
FONT = {  # 3x5 pixel font for the story bubbles
    'P': ['111', '101', '111', '100', '100'], 'L': ['100', '100', '100', '100', '111'],
    'S': ['111', '100', '111', '001', '111'], '?': ['111', '001', '011', '000', '010'],
    'W': ['10001', '10001', '10101', '10101', '01010'], 'A': ['010', '101', '111', '101', '101'],
    'H': ['101', '101', '111', '101', '101'], 'M': ['10001', '11011', '10101', '10001', '10001'],
    '!': ['1', '1', '1', '0', '1'], '.': ['0', '0', '0', '0', '1'],
}
TEXTS = {'pls': ('PLS?', '#e8435f'), 'waah': ('WAAH', '#4f9fd6'), 'hmph': ('HMPH!', '#e25a4f'), 'dots': ('...', '#6c7385')}

defs, css = [], []
images = {}
anim_count = [0]


def num(v, p=2):
    s = f'{v:.{p}f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def image(url, w, h):
    """Each PNG is stored once in <defs> and reused with <use>."""
    if url not in images:
        images[url] = f'i{len(images)}'
        defs.append(f'<image id="{images[url]}" width="{num(w)}" height="{num(h)}" href="{url}"/>')
    return images[url]


def anim(period, points, fmt, timing='linear', delay=0):
    """Inline style for a keyframe animation through (time, value) points."""
    anim_count[0] += 1
    name = f'a{anim_count[0]}'
    pts = sorted(points, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < period:
        pts.append((period, pts[-1][1]))
    frames, last = [], -1.0
    for t, v in pts:
        pct = max(0.0, min(100.0, t / period * 100))
        if pct <= last:
            pct = last + .001
        last = pct
        frames.append(f'{num(pct, 3)}%{{{fmt(v)}}}')
    css.append(f'@keyframes {name}{{{"".join(frames)}}}')
    d = f' -{num(delay)}s' if delay else ''
    return f'animation:{name} {num(period)}s {timing}{d} infinite'


def window(period, spans, delay=0):
    """Visible only inside the given (start, end) spans."""
    pts = [(0, 0)]
    for a, b in sorted(spans):
        pts += [(a, 1), (b, 0)]
    return anim(period, pts, lambda v: f'opacity:{v}', 'steps(1,end)', delay)


def merge(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def complement(spans, period):
    out, cur = [], 0
    for a, b in merge(spans):
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if cur < period:
        out.append((cur, period))
    return out


def tf(v):
    x, y, r = v
    return f'transform:translate({num(x)}px,{num(y)}px) rotate({num(r)}deg)'


# ---------------------------------------------------------------- actors

class Bug:
    def __init__(self, name):
        self.name = name
        self.hw = D['hw'][name] * BU
        self.pos = []        # (t, (x, gy, scale))
        self.mot = []        # (t, (dx, dy, rotate)) local body motion
        self.flip = []       # (t, 1 | -1)
        self.faces = {}      # face -> [(t0, t1)]
        self.bubbles = {}    # bubble -> [(t0, t1)]
        self.carried = []    # spans in Lem's arms (the walking sprite is hidden then)

    def at(self, t, x, gy, s=None):
        self.pos.append((t, (x, gy, lane_scale(gy) if s is None else s)))

    def move(self, t, dx=0, dy=0, r=0):
        self.mot.append((t, (dx, dy, r)))

    def face(self, f, t0, t1):
        self.faces.setdefault(f, []).append((t0, t1))

    def say(self, b, t0, t1):
        self.bubbles.setdefault(b, []).append((t0, t1))

    def turn(self, t, f):
        self.flip.append((t, f))


def emotion_motion(bug, kind, t0, length):
    m = bug.move
    m(t0)
    if kind == 'happy':
        for i in range(3):
            m(t0 + i * .5 + .15, dy=-7); m(t0 + i * .5 + .3)
    elif kind == 'excited':
        for i in range(4):
            m(t0 + i * .42 + .14, dy=-15); m(t0 + i * .42 + .28)
    elif kind in ('angry', 'cry'):
        for i in range(10):
            m(t0 + .1 + i * .07, dx=3 if i % 2 else -3)
        m(t0 + .9)
        if kind == 'angry':
            m(t0 + 1.4, dy=-5); m(t0 + 1.52)
    elif kind == 'love':
        m(t0 + .6, dy=-6); m(t0 + 1.2); m(t0 + 1.8, dy=-6); m(t0 + 2.2)
    elif kind == 'shock':
        m(t0 + .1, dy=-14); m(t0 + .26); m(t0 + .34, dy=-3); m(t0 + .42)
    elif kind == 'sad':
        m(t0 + .5, dy=2); m(t0 + length - .2, dy=2)
    elif kind == 'dizzy':
        for i in range(8):
            m(t0 + .1 + i * .25, r=9 if i % 2 else -9)
    elif kind == 'smug':
        m(t0 + .25, r=-7); m(t0 + length - .3, r=-7)
    elif kind == 'flustered':
        for i in range(8):
            m(t0 + .1 + i * .2, dx=2 if i % 2 else -2)
    elif kind == 'plead':
        for i in range(4):
            m(t0 + i * .6 + .15, dy=-5); m(t0 + i * .6 + .3)
    elif kind == 'tsundere':
        for i in range(3):
            m(t0 + i * .5 + .1, dy=-3); m(t0 + i * .5 + .2)
    m(t0 + length)


# ---------------------------------------------------------------- the story

names = list(D['bugs'])
bugs = {n: Bug(n) for n in names}
first_carried = 'Dark Boulder'
roamers = [n for n in names if n != first_carried]
rng.shuffle(roamers)

SLOTS = [(BACK, 40, 345), (BACK, 345, 655), (BACK, 655, 960),
         (MID, 24, 384), (MID, 616, 976),
         (FRONT, 24, 330), (FRONT, 670, 976)]
seats = [(i, side) for i in range(len(SLOTS)) for side in (0, 1)]
start_occupant = {seat: roamers[k] for k, seat in enumerate(seats)}
occupant = dict(start_occupant)


def home(seat, name):
    gy, left, right = SLOTS[seat[0]]
    hw = bugs[name].hw * lane_scale(gy)
    return (left + hw if seat[1] == 0 else right - hw), gy


for seat, n in occupant.items():
    bugs[n].at(0, *home(seat, n))
    bugs[n].turn(0, 1 if seat[1] == 0 else -1)

# Cycling through m seats m*(m+1) times puts every bug back where it started.
cycle = rng.sample(seats, CARRY_SEATS)
swaps = CARRY_SEATS * (CARRY_SEATS + 1)
swap_times = [FIRST_SWAP + SWAP_EVERY * k for k in range(swaps)]
T = swap_times[-1] + 16
lem_spots = [rng.uniform(430, 570) for _ in range(swaps)]
blocks = {i: [] for i in range(len(SLOTS))}
seat_changes = []         # (time, seat, new occupant)
lem_events = []           # (tb, x, side)
carrier, carry_start = first_carried, 0.0


def path_time(points, speed):
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** .5 for a, b in zip(points, points[1:])) / speed


def walk_path(bug, t, points, speed):
    """Walks through (x, gy) points starting at t; returns the arrival time."""
    bug.at(t, *points[0])
    for a, b in zip(points, points[1:]):
        if abs(b[0] - a[0]) > 1:
            bug.turn(t, 1 if b[0] > a[0] else -1)
        t += path_time([a, b], speed)
        bug.at(t, *b)
    return t


for k, tb in enumerate(swap_times):
    seat = cycle[k % CARRY_SEATS]
    lx = lem_spots[k]
    asker = bugs[occupant[seat]]
    hx, hgy = home(seat, asker.name)
    side = -1 if hx < lx else 1
    lem_events.append((tb, lx, side))

    # A Bytebug runs over to Lem's legs...
    near = (lx + side * 40, FRONT)
    route = [(hx, hgy)] + ([(lx + side * 150, (hgy + FRONT) / 2)] if hgy != FRONT else []) + [near]
    t_dep = tb - path_time(route, 85)
    walk_path(asker, t_dep, route, 85)
    asker.turn(tb - .01, -side)
    # ...bumps into them...
    asker.face('hit', tb, tb + .4)
    asker.move(tb); asker.move(tb + .1, dx=side * 8, dy=-4); asker.move(tb + .3, dx=side * 4); asker.move(tb + .4)
    # ...and begs to be carried.
    plea = rng.choice(list(STORY))
    face, bubble = STORY[plea]
    asker.face(face, tb + .4, tb + 3.0)
    asker.say(bubble, tb + .45, tb + 2.9)
    emotion_motion(asker, plea, tb + .4, 2.6)
    if plea == 'tsundere':           # turns away, then sneaks a look back
        asker.turn(tb + .4, side); asker.turn(tb + 2.1, -side)

    # Lem puts down the one he's carrying...
    old = bugs[carrier]
    old.carried.append((carry_start, tb + 3.05))
    drop = lx + side * 108
    old.at(tb + 3.05, lx + side * CARRY_X, FRONT, CARRY_S)
    old.at(tb + 3.5, drop, FRONT, 1)
    old.move(tb + 3.05, dy=CARRY_FEET); old.move(tb + 3.25, dy=CARRY_FEET - 18); old.move(tb + 3.5)
    old.turn(tb + 3.05, -side)
    old.face('shock', tb + 3.05, tb + 3.55)
    # ...it's sad for a moment...
    mood = rng.choice(['sad', 'cry'])
    old.face(mood, tb + 3.55, tb + 5.7)
    old.say('dots' if mood == 'sad' else 'waah', tb + 3.6, tb + 5.6)
    emotion_motion(old, mood, tb + 3.55, 2.15)
    # ...then takes the empty seat and goes back to wandering.
    nx, ngy = home(seat, old.name)
    back = [(drop, FRONT)] + ([(lx + side * 160, (ngy + FRONT) / 2)] if ngy != FRONT else []) + [(nx, ngy)]
    t_arr = walk_path(old, tb + 5.75, back, 62)
    old.turn(t_arr, 1 if seat[1] == 0 else -1)
    assert t_arr < T - .5, 'a Bytebug would still be walking when the loop restarts'

    # The new one hops into Lem's arms.
    asker.at(tb + 3.9, *near)
    asker.at(tb + 4.35, lx + side * CARRY_X, FRONT, CARRY_S)
    asker.move(tb + 3.9); asker.move(tb + 4.12, dy=CARRY_FEET - 25); asker.move(tb + 4.35, dy=CARRY_FEET)
    asker.face('happy', tb + 3.9, tb + 4.4)
    carrier, carry_start = asker.name, tb + 4.35

    blocks[seat[0]].append((t_dep - .3, t_arr + .3))
    seat_changes.append((tb, seat, old.name))
    occupant[seat] = old.name

# Whoever is carried at the end is carried at the start, so the loop is seamless.
assert carrier == first_carried and occupant == start_occupant
bugs[carrier].carried.append((carry_start, T))


def who(seat, t):
    n = start_occupant[seat]
    for tc, s, new in seat_changes:
        if s == seat and tc <= t:
            n = new
    return n


# ---------------------------------------------------------------- wandering pairs

flashes = {i: [] for i in range(len(SLOTS))}


def plan_round(slot, t0):
    """Plans one meet, bump, react, walk-home round. Nothing is applied yet."""
    gy, left, right = SLOTS[slot]
    s = lane_scale(gy)
    a, b = bugs[who((slot, 0), t0)], bugs[who((slot, 1), t0)]
    xa0, xb0 = home((slot, 0), a.name)[0], home((slot, 1), b.name)[0]
    meet = (left + right) / 2 + rng.uniform(-25, 25)
    xa1, xb1 = meet - a.hw * s * .82, meet + b.hw * s * .82
    speed = rng.uniform(42, 64) * s
    t1 = t0 + rng.uniform(.3, 1.6)
    t2 = t1 + max(xa1 - xa0, xb0 - xb1) / speed
    te0, te1 = t2 + .5, t2 + .5 + rng.uniform(2.2, 2.8)
    t4 = te1 + .1 + max(xa1 - xa0, xb0 - xb1) / (speed * rng.uniform(.85, 1.1))
    end = t4 + rng.uniform(.5, 1.6)
    feelings = []
    for _ in range(2):
        feel = rng.choice(list(EMOTIONS))
        face = rng.choice(['blush2', 'blush3']) if feel == 'flustered' else EMOTIONS[feel][0]
        feelings.append((feel, face))
    return dict(slot=slot, gy=gy, s=s, a=a, b=b, xa=(xa0, xa1), xb=(xb0, xb1), meet=meet,
                t=(t1, t2, te0, te1, t4, end), feelings=feelings)


def apply_round(p):
    gy, s = p['gy'], p['s']
    t1, t2, te0, te1, t4, end = p['t']
    knock = 11 * s
    for bug, (x0, x1), kd, facing, (feel, face) in ((p['a'], p['xa'], -1, 1, p['feelings'][0]),
                                                      (p['b'], p['xb'], 1, -1, p['feelings'][1])):
        bug.at(t1, x0, gy); bug.at(t2, x1, gy); bug.at(t2 + .16, x1 + kd * knock, gy)
        bug.at(te1 + .1, x1 + kd * knock, gy); bug.at(t4, x0, gy)
        bug.turn(t1, facing); bug.turn(te1 + .1, -facing); bug.turn(t4 + (end - t4) * .5, facing)
        bug.face('hit', t2, te0)
        bug.move(t2); bug.move(t2 + .08, dy=-5); bug.move(t2 + .2)
        bug.face(face, te0, te1)
        bug.say(EMOTIONS[feel][1], te0, te1 - .05)
        emotion_motion(bug, feel, te0, te1 - te0)
    flashes[p['slot']].append((p['meet'], t2))


for slot in range(len(SLOTS)):
    busy = merge(blocks[slot])
    t = rng.uniform(0, 4)
    while t < T:
        nxt = next(((a, b) for a, b in busy if b > t), None)
        if nxt and nxt[0] <= t:          # inside a block: wait it out
            t = nxt[1]
            continue
        p = plan_round(slot, t)
        limit = (nxt[0] if nxt else T) - .2
        if p['t'][-1] <= limit:
            apply_round(p)
            t = p['t'][-1]
        elif nxt:
            t = nxt[1]
        else:
            break

# ---------------------------------------------------------------- Lem's walk

lem_pos, lem_flip, lem_walk = [], [], []
x, t = lem_spots[-1], 0.0
lem_pos.append((0, x))
lem_flip.append((0, lem_events[-1][2]))
for tb, lx, side in lem_events:
    ready = tb - 1.0
    avail = ready - t - .3
    mid = rng.uniform(420, 580)
    if (abs(mid - x) + abs(lx - mid)) / 32 + 1.0 <= avail:
        legs = [(mid, 32), (lx, 32)]
    else:
        legs = [(lx, max(32, abs(lx - x) / max(avail, .5)))]
    t += .3
    for i, (gx, speed) in enumerate(legs):
        if abs(gx - x) > 2:
            lem_pos.append((t, x))
            lem_flip.append((t, 1 if gx > x else -1))
            dt = abs(gx - x) / speed
            lem_walk.append((t, t + dt))
            t += dt
            x = gx
            lem_pos.append((t, x))
        if i < len(legs) - 1:
            t += 1.0
    lem_flip.append((ready, side))
    t = tb + 4.6
lem_pos.append((T, x))

# ---------------------------------------------------------------- drawing


def bubble_def(key):
    """A speech bubble with a pixel icon or pixel text; tail tip at (0, 0)."""
    px = 1.75
    if key in ICONS:
        color, rows = ICONS[key]
        cells = [(i, j) for j, row in enumerate(rows) for i, c in enumerate(row) if c == '1']
        w, ox, oy = 8 * px, 4, -21.5
    else:
        text, color = TEXTS[key]
        cells, cx = [], 0
        for ch in text:
            g = FONT[ch]
            cells += [(cx + i, j) for j, row in enumerate(g) for i, c in enumerate(row) if c == '1']
            cx += len(g[0]) + 1
        w, ox, oy = (cx - 1) * px, 4, -19.5
    inner = w + 8
    rects = ''.join(f'<rect x="{num(ox + i * px)}" y="{num(oy + j * px)}" width="{px}" height="{px}"/>' for i, j in cells)
    return (f'<g id="b_{key}"><rect x="-2" y="-26" width="{num(inner + 4)}" height="22" rx="4" fill="#15161b"/>'
            f'<path d="M1 -6h7l-6 6z" fill="#15161b"/>'
            f'<rect x="0" y="-24" width="{num(inner)}" height="18" rx="2.5" fill="#f4f1ea"/>'
            f'<path d="M3 -7h4l-3 3z" fill="#f4f1ea"/><g fill="{color}">{rects}</g></g>')


def pop(spans):
    pts = [(0, 0)]
    for a, b in sorted(spans):
        pts += [(a - .001, 0), (a + .12, 1.25), (a + .24, 1), (b - .16, 1), (b, 0)]
    return anim(T, pts, lambda s: f'transform:translate(0px,{num((1 - min(s, 1)) * 6)}px) scale({num(s)})')


def face_use(bug, face, style=''):
    f = D['bugs'][bug]['faces'][face]
    i = image(f['url'], f['w'], f['h'])
    return f'<use href="#{i}" x="{num(f["x"] - BUG["ox"])}" y="{num(f["y"] - BUG["oy"])}" style="{style}"/>'


def roaming(bug):
    b = D['bugs'][bug.name]
    delay = rng.uniform(0, .4)
    walk = ''.join(f'<use href="#{image(u, BUG["w"], BUG["h"])}" x="{num(IMG_X)}" y="{num(IMG_Y)}" class="w{i}" style="animation-delay:-{num(delay)}s"/>'
                   for i, u in enumerate(b['walk']))
    # Faces are drawn relative to the bug's origin; shift them down to the feet anchor.
    faces = ''.join(f'<g transform="translate(0 {num(-FEET)})">{face_use(bug.name, f, window(T, spans))}</g>'
                    for f, spans in bug.faces.items())
    busy = [s for spans in bug.faces.values() for s in spans]
    blink = rng.uniform(0, 4)
    neutral = (f'<g transform="translate(0 {num(-FEET)})" style="{window(T, complement(busy, T))}">'
               f'{face_use(bug.name, "idle", f"animation:eo 4s steps(1,end) -{num(blink)}s infinite")}'
               f'{face_use(bug.name, "blink", f"animation:ec 4s steps(1,end) -{num(blink)}s infinite")}</g>')
    extra = ' class="kh"' if bug.name == 'Keycap Jumper' else ' class="gf"' if bug.name == '404 Ghost' else ''
    bubbles = ''.join(f'<use href="#b_{k}" style="{pop(spans)}"/>' for k, spans in bug.bubbles.items())
    pos = anim(T, bug.pos, lambda v: f'transform:translate({num(v[0])}px,{num(v[1])}px) scale({num(v[2], 3)})')
    shown = '' if not bug.carried else f' style="{window(T, complement(bug.carried, T))}"'
    return (f'<g data-bug="{bug.name}" style="{pos}"><g{shown}>'
            f'<ellipse rx="{num(bug.hw * .95)}" ry="6" fill="url(#shadow)"/>'
            f'<g style="{anim(T, bug.mot, tf)}"><g style="{anim(T, bug.flip, lambda f: f"transform:scale({f},1)", "steps(1,end)")}">'
            f'<g{extra}>{walk}{neutral}{faces}</g></g></g>'
            f'<g transform="translate(10 -70) scale(1.45)">{bubbles}</g>'
            f'</g></g>')


def carried(bug):
    """The copy of a bug that sits in Lem's arms, blushing and fidgeting."""
    b = D['bugs'][bug.name]
    body = image(b['walk'][0], BUG['w'], BUG['h'])
    seq = [('blush', 1.4), ('blush2', .9), ('blush', .5), ('blush3', 1.1), ('blush4', 1.3),
           ('blush2', .7), ('blush3', .5), ('blush', .9), ('blush4', .8)]
    total, t0, spans = sum(d for _, d in seq), 0, {}
    for f, d in seq:
        spans.setdefault(f, []).append((t0, t0 + d))
        t0 += d
    delay = rng.uniform(0, total)
    faces = ''.join(face_use(bug.name, f, window(total, s, delay)) for f, s in spans.items())
    return (f'<g style="{window(T, bug.carried)}"><g transform="translate({num(CARRY_X)} {num(CARRY_Y)}) scale({num(CARRY_S, 3)})">'
            f'<g class="wig"><use href="#{body}" x="{num(-BUG["ox"])}" y="{num(-BUG["oy"])}"/>{faces}</g></g></g>')


def lem():
    swaps_busy = [(tb + 3.0, tb + 3.8) for tb, _, _ in lem_events]
    walking = window(T, lem_walk)
    standing = window(T, complement(lem_walk + swaps_busy, T))
    slam = window(T, swaps_busy)
    def use(url, cls='', style=''):
        extra = (' class="%s"' % cls if cls else '') + (' style="%s"' % style if style else '')
        return f'<use href="#{image(url, LEM_W, LEM_H)}" x="{num(LEM_X)}" y="{num(LEM_Y)}"{extra}/>'

    stride = ''.join(use(u, f'l{i}') for i, u in enumerate(LEM['walk']))
    # Standing: breathe through frames 0-3, blink (frame 4) every 3.4s.
    breathe = {i: [] for i in range(5)}
    for step in range(17):
        breathe[step % 4].append((step * .2, step * .2 + .2))
    breathe[0][0] = (.13, .2)
    breathe[4].append((0, .13))
    stand = ''.join(use(u, style=window(3.4, breathe[i])) for i, u in enumerate(LEM['stand']))
    held = ''.join(carried(b) for b in bugs.values() if b.carried)
    hands = use(LEM['hands'], style=window(T, complement(swaps_busy, T)))
    hearts = ''
    for i, (hx, d) in enumerate(((-8, 0), (10, .8), (2, 1.6))):
        rise = anim(2.4, [(0, (0, 0, 0)), (2.4, (hx * .4, -40, 0))], tf, delay=d)
        fade = anim(2.4, [(0, 0), (.2, 1), (1.6, 1), (2.4, 0)], lambda v: f'opacity:{v}', delay=d)
        heart = ''.join(f'<rect x="{c * 2}" y="{r * 2}" width="2" height="2"/>'
                        for r, row in enumerate(['01010', '11111', '11111', '01110', '00100']) for c, v in enumerate(row) if v == '1')
        hearts += f'<g transform="translate({num(CARRY_X + hx - 5)} {num(CARRY_Y - 48)})"><g style="{rise}"><g style="{fade}" fill="#f08aa0">{heart}</g></g></g>'
    hearts_on = window(T, complement([(tb + 2.8, tb + 5.2) for tb, _, _ in lem_events], T))
    bang = f'<use href="#b_bang" style="{pop([(tb + .05, tb + 1.1) for tb, _, _ in lem_events])}"/>'
    pos = anim(T, lem_pos, lambda x: f'transform:translate({num(x)}px,{FRONT}px)')
    flip = anim(T, lem_flip, lambda f: f'transform:scale({f},1)', 'steps(1,end)')
    return (f'<g style="{pos}"><ellipse rx="48" ry="8" fill="url(#shadow)"/>'
            f'<g style="{flip}">'
            f'<g style="{walking}"><g class="bob">{stride}</g></g>'
            f'<g style="{standing}">{stand}</g>'
            f'<g style="{slam}">{use(LEM["slam"])}</g>'
            f'{held}{hands}</g>'
            f'<g style="{hearts_on}">{hearts}</g>'
            f'<g transform="translate(16 -196) scale(1.6)">{bang}</g></g>')


def impact_flashes():
    out = []
    for slot, items in flashes.items():
        if not items:
            continue
        gy = SLOTS[slot][0]
        s = lane_scale(gy)
        pts = [(0, (items[0][0], 0))]
        for x, t2 in items:
            pts += [(t2 - .01, (x, 0)), (t2 + .05, (x, 1.3)), (t2 + .3, (x, 0))]
        st = anim(T, pts, lambda v: f'transform:translate({num(v[0])}px,{num(gy - 26 * s)}px) scale({num(v[1] * s, 3)})')
        out.append(f'<g style="{st}" fill="#f6e7b0">'
                   '<rect x="-1.5" y="-12" width="3" height="7"/><rect x="-1.5" y="5" width="3" height="7"/>'
                   '<rect x="-12" y="-1.5" width="7" height="3"/><rect x="5" y="-1.5" width="7" height="3"/>'
                   '<rect x="-8" y="-8" width="3" height="3"/><rect x="5" y="-8" width="3" height="3"/>'
                   '<rect x="-8" y="5" width="3" height="3"/><rect x="5" y="5" width="3" height="3"/></g>')
    return out


def text(key, x, y, fill):
    t = D['text'][key]
    return f'<path transform="translate({num(x)} {y})" fill="{fill}" d="{t["d"]}"/>', t['w']


def heading():
    T_ = D['text']
    out = []
    words, gap = ['k_design', 'k_develop', 'k_deploy'], 26
    x = 500 - (sum(T_[w]['w'] for w in words) + gap * 2) / 2
    for i, w in enumerate(words):
        p, wd = text(w, x, 46, '#8f97a8')
        out.append(p)
        x += wd
        if i < 2:
            out.append(f'<path d="M{num(x + gap / 2)} 36l3 3-3 3-3-3z" fill="#5d6576"/>')
            x += gap
    out.append(text('name', 500 - T_['name']['w'] / 2, 124, '#f4f1ea')[0])
    out.append(text('role', 500 - T_['role']['w'] / 2, 166, 'url(#silver)')[0])
    stats, sp, sep = [('n1', 'l1'), ('n2', 'l2'), ('n3', 'l3')], 8, 34
    x = 500 - (sum(T_[n]['w'] + sp + T_[l]['w'] for n, l in stats) + sep * 2) / 2
    for i, (n, l) in enumerate(stats):
        out.append(text(n, x, 210, '#f2c46d')[0])
        x += T_[n]['w'] + sp
        out.append(text(l, x, 210, '#aab1bf')[0])
        x += T_[l]['w']
        if i < 2:
            out.append(f'<rect x="{num(x + sep / 2 - 2)}" y="201" width="4" height="4" fill="#5d6576"/>')
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


for key in list(ICONS) + list(TEXTS):
    defs.append(bubble_def(key))
scene = [lem()]
scene += [roaming(bugs[n]) for n in sorted(names, key=lambda n: bugs[n].pos[0][1][1])]
scene += impact_flashes()
head = heading()

style = (
    # bug walk cycle (4 frames) and blinking
    '.w0,.w1,.w2,.w3{opacity:0;animation:.44s steps(1,end) infinite}'
    '.w0{animation-name:w0}.w1{animation-name:w1}.w2{animation-name:w2}.w3{animation-name:w3}'
    '@keyframes w0{0%{opacity:1}25%{opacity:0}}@keyframes w1{0%{opacity:0}25%{opacity:1}50%{opacity:0}}'
    '@keyframes w2{0%{opacity:0}50%{opacity:1}75%{opacity:0}}@keyframes w3{0%{opacity:0}75%{opacity:1}}'
    '@keyframes eo{0%{opacity:1}96%{opacity:0}}@keyframes ec{0%{opacity:0}96%{opacity:1}}'
    # Keycap Jumper bounces, 404 Ghost flickers now and then
    '.kh{animation:kh .5s ease-in-out infinite}@keyframes kh{0%,100%{transform:translate(0,0)}50%{transform:translate(0,-5px)}}'
    '.gf{animation:gf 3.7s steps(1,end) infinite}@keyframes gf{0%{opacity:1}80%{opacity:.35}83%{opacity:1}90%{opacity:.35}92%{opacity:1}}'
    # Lem's stride and the carried bug's fidget
    '.l0,.l1,.l2,.l3{opacity:0;animation:.72s steps(1,end) infinite}'
    '.l0{animation-name:w0}.l1{animation-name:w1}.l2{animation-name:w2}.l3{animation-name:w3}'
    '.bob{animation:bob .36s steps(1,end) infinite}@keyframes bob{0%{transform:translate(0,0)}50%{transform:translate(0,-2px)}}'
    '.wig{animation:wig 1.6s ease-in-out infinite}@keyframes wig{0%,100%{transform:rotate(-3deg)}50%{transform:translate(0,-1px) rotate(3deg)}}'
    + ''.join(css))

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
    '<title id="title">Luis Mario Acovera — Full Stack Developer</title>',
    '<desc id="desc">Luis Mario Acovera, Full Stack Developer. In the Bytebug Battle arena below, Lem walks around carrying a '
    'blushing Bytebug. The other Bytebugs wander, bump into each other and react with random emotions, and every 15 seconds '
    'one of them begs Lem to carry it instead.</desc>',
    f'<style>{style}</style>',
    '<defs>',
    '<linearGradient id="wall" x2="0" y2="1"><stop stop-color="#0f1015"/><stop offset=".44" stop-color="#171920"/><stop offset="1" stop-color="#262932"/></linearGradient>',
    '<linearGradient id="ground" x2="0" y2="1"><stop stop-color="#1b1d24"/><stop offset="1" stop-color="#2a2d36"/></linearGradient>',
    '<linearGradient id="silver" x2="0" y2="1"><stop stop-color="#f1f3f6"/><stop offset=".55" stop-color="#c3c8d0"/><stop offset="1" stop-color="#9aa1ac"/></linearGradient>',
    '<pattern id="dots" x="14" y="18" width="21" height="21" patternUnits="userSpaceOnUse"><rect width="1.2" height="1.2" fill="#666b78"/></pattern>',
    f'<radialGradient id="spot" cx="500" cy="{FRONT}" r="300" gradientTransform="translate(0 {FRONT}) scale(1 .45) translate(0 -{FRONT})" gradientUnits="userSpaceOnUse"><stop stop-color="#b8d5ef" stop-opacity=".12"/><stop offset="1" stop-color="#b8d5ef" stop-opacity="0"/></radialGradient>',
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
print(f'wrote {os.path.relpath(OUT)} ({os.path.getsize(OUT) // 1024} KB, {len(images)} images, {num(T)}s loop)')
