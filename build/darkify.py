# Convert a light stylesheet to a matte dark one. Usage: python3 -I darkify.py <file.html> [more files]
# Rules (property-aware):
#  - neutral colours are inverted into a warm matte range (white surfaces -> near-black, dark ink -> light grey)
#  - blue accents become amber/gold (the brand accent of the dark theme); light blue tints become dark amber tints
#  - other hues keep their hue: light tints become dark tints, dark text colours get lighter
#  - shadows stay dark (they are depth, not paint)
import re, sys, colorsys

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))

def parse(c):
    c = c.strip().lower()
    if c.startswith('#'):
        h = c[1:]
        if len(h) in (3, 4): h = ''.join(ch * 2 for ch in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        a = int(h[6:8], 16) / 255 if len(h) == 8 else None
        return r / 255, g / 255, b / 255, a
    m = re.match(r'rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+%?)\s*)?\)', c)
    if m:
        a = m.group(4)
        if a is not None: a = float(a[:-1]) / 100 if a.endswith('%') else float(a)
        return float(m.group(1)) / 255, float(m.group(2)) / 255, float(m.group(3)) / 255, a
    return None

def fmt(r, g, b, a):
    R, G, B = (int(round(clamp(v) * 255)) for v in (r, g, b))
    if a is None: return '#%02x%02x%02x' % (R, G, B)
    return 'rgba(%d,%d,%d,%s)' % (R, G, B, ('%.3f' % a).rstrip('0').rstrip('.') or '0')

def from_hls(h, l, s): return colorsys.hls_to_rgb(h % 1, clamp(l), clamp(s))

def inv_l(l): return 0.043 + 0.877 * (1 - l)   # white -> ~#0b0b0b, near-black ink -> ~#e2e2e2

def convert(col, shadow=False):
    p = parse(col)
    if not p: return col
    r, g, b, a = p
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if shadow:
        if s < 0.25 or l < 0.2:   # neutral shadow: keep it a dark shadow
            aa = 0.5 if a is None else min(0.75, a * 1.7 + 0.05)
            return fmt(0, 0, 0, aa)
        if 190 <= hue <= 255: h = 38 / 360
        return fmt(*from_hls(h, l, s), a)
    if s < 0.22 or (l < 0.16 and s < 0.5):            # neutral (incl. navy-black ink)
        nl = inv_l(l)
        warm_s = 0.06 if nl < 0.5 else 0.035
        return fmt(*from_hls(36 / 360, nl, warm_s), a)
    if 185 <= hue <= 255:                              # blue accent -> amber
        H = 38 / 360
        if l > 0.8: return fmt(*from_hls(H, inv_l(l) + 0.02, min(0.45, s * 0.5)), a)
        if l < 0.3: return fmt(*from_hls(H, 0.72, 0.6), a)
        return fmt(*from_hls(H, max(0.56, l), min(0.82, max(0.65, s))), a)
    # other hues: keep hue
    if l > 0.82: return fmt(*from_hls(h, inv_l(l) + 0.03, min(0.5, s * 0.6)), a)
    if l < 0.38: return fmt(*from_hls(h, 0.62, min(0.7, s)), a)
    return fmt(r, g, b, a)

COL = re.compile(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^()]*\)')
SHADOW_PROPS = ('box-shadow', 'text-shadow')
NAMED = {'white': '#ffffff', 'black': '#000000'}

def conv_value(prop, val):
    prop = prop.strip().lower()
    if prop.startswith('--'):
        shadow = 'shadow' in prop
    else:
        shadow = prop in SHADOW_PROPS
    def rep(m): return convert(m.group(0), shadow)
    out = val
    # drop-shadow() inside filter: keep shadows dark
    if 'drop-shadow' in out:
        out = re.sub(r'drop-shadow\(([^()]*(?:\([^()]*\))?[^()]*)\)', lambda m: 'drop-shadow(' + COL.sub(lambda k: convert(k.group(0), True), m.group(1)) + ')', out)
        if prop == 'filter' or prop.startswith('--'):
            return out
    out = COL.sub(rep, out)
    if prop in ('color', 'background', 'background-color', 'border-color', 'fill', 'stroke', 'outline-color', 'caret-color') or prop.startswith('border'):
        out = re.sub(r'(?<![\w-])(white|black)(?![\w-])', lambda m: convert(NAMED[m.group(1)], False), out)
    return out

SKIP = re.compile(r'\.scan-card|\.hv-(fig|ph|scan|l|pt|ch)\b|\.hz\b|\.hz-|\.hero-vid|\.hero-img')
DECL = re.compile(r'([a-zA-Z-]+|--[\w-]+)(\s*:\s*)([^;{}]+)(?=[;}]|$)')

def conv_css(css):
    urls = []
    def keep(m): urls.append(m.group(0)); return '\x00%d\x00' % (len(urls) - 1)
    css = re.sub(r'url\((?:[^()]|\([^()]*\))*\)', keep, css)
    def rule(m):
        sel, body = m.group(1), m.group(2)
        parts = [x.strip() for x in sel.split('*/')[-1].split(',') if x.strip()]
        if parts and all(SKIP.search(x) for x in parts):   # paint on top of photos: keep as designed
            return m.group(0)
        return sel + '{' + DECL.sub(lambda d: d.group(1) + d.group(2) + conv_value(d.group(1), d.group(3)), body) + '}'
    css = re.sub(r'([^{}]*)\{([^{}]*)\}', rule, css)
    return re.sub(r'\x00(\d+)\x00', lambda m: urls[int(m.group(1))], css)

if __name__ == '__main__':
    for path in sys.argv[1:]:
        s = open(path, encoding='utf-8').read()
        out, pos, n = [], 0, 0
        for m in re.finditer(r'<style[^>]*>(.*?)</style>', s, re.S):
            out.append(s[pos:m.start(1)]); out.append(conv_css(m.group(1))); pos = m.end(1); n += 1
        out.append(s[pos:])
        open(path, 'w', encoding='utf-8').write(''.join(out))
        print(path, 'style blocks converted:', n)
