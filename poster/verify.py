"""Checks that must pass BEFORE anything is posted: Malayalam text, fonts, voice/reel audio, and news verification."""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "kit" / "node_modules" / "@fontsource"

# fonts the poster and reel really use (Malayalam + Latin subsets): NST noto-sans-malayalam, BT baloo-chettan-2, CT anek-malayalam
FONT_FILES = [("noto-sans-malayalam", "malayalam", (600, 700, 800)), ("noto-sans-malayalam", "latin", (600, 700, 800)),
              ("baloo-chettan-2", "malayalam", (700, 800)), ("baloo-chettan-2", "latin", (700, 800)),
              ("anek-malayalam", "malayalam", (700, 800)), ("anek-malayalam", "latin", (700, 800))]
HEAD_FONTS = ("noto-sans-malayalam", "baloo-chettan-2")      # every character must be in one of these or in the CT font
CT_FONT = "anek-malayalam"
_cov = None


def font_coverage():
    global _cov
    if _cov is None:
        try:
            from fontTools.ttLib import TTFont
        except ImportError:      # the story writer and the test runner have no fontTools: letters are still repaired, only the font check is skipped
            _cov = {}
            return _cov
        per = {}
        for pkg, sub, weights in FONT_FILES:
            for w in weights:
                f = FONTS / pkg / "files" / f"{pkg}-{sub}-{w}-normal.woff2"
                if f.exists():
                    per[(pkg, sub, w)] = set(TTFont(str(f)).getBestCmap().keys())
        _cov = per
    return _cov


def strip_tags(t):
    return re.sub(r"<[^>]+>", "", t or "")


def spec_texts(spec):
    out = [spec.get("hl1", ""), spec.get("hl2", ""), spec.get("cat", ""), spec.get("loc", ""), spec.get("date", "")]
    for s in spec.get("slides", []):
        out.append(s.get("title", ""))
        out += s.get("lines", [])
    return [strip_tags(x) for x in out if x]


ML_CONS = range(0x0D15, 0x0D3B)
SIGNS = set(range(0x0D3E, 0x0D4E)) | {0x0D57, 0x0D62, 0x0D63}      # vowel signs, virama, au length mark, vocalic l/ll signs
# two-part vowel signs: ൊ ോ ൌ may be typed as െ/േ followed by ാ or ൗ
_SPLIT_FIRST, _SPLIT_SECOND = (0x0D46, 0x0D47), (0x0D3E, 0x0D57)


def _sign_ok(prev, c):
    return prev is not None and (ord(prev) in ML_CONS or (ord(prev) in _SPLIT_FIRST and c in _SPLIT_SECOND))


def malayalam_sequence_problems(text):
    """Broken Malayalam: a vowel sign or virama with no consonant before it, doubled signs, replacement characters."""
    probs = []
    if "�" in text:
        probs.append("replacement character (broken text)")
    prev = None
    for i, ch in enumerate(text):
        c = ord(ch)
        if c in SIGNS and not _sign_ok(prev, c):
            probs.append(f"stray Malayalam sign '{ch}' after '{prev or ''}' in «{text[max(0, i - 6):i + 4]}»")
        if c not in (0x200C, 0x200D):      # ZWJ/ZWNJ (old chillu forms) do not break the consonant + sign pair
            prev = ch
    return probs


tamil_sequence_problems = malayalam_sequence_problems      # old name, still imported by research_free/validate.py


def check_fonts(texts):
    """Every character shown on a slide or in a reel caption must exist in the fonts (otherwise it prints as a box)."""
    cov = font_coverage()
    if not cov:
        return ["font files not found - cannot check Malayalam rendering"]
    probs = []
    for key_pkg in HEAD_FONTS:
        cps = set()
        for (pkg, sub, w), s in cov.items():
            if pkg == key_pkg:
                cps |= s
        cat = set()
        for (pkg, sub, w), s in cov.items():
            if pkg == CT_FONT:
                cat |= s
        missing = set()
        for t in texts:
            for ch in t:
                if ch.isspace() or ord(ch) in (0x200C, 0x200D):
                    continue
                if ord(ch) not in cps and ord(ch) not in cat:
                    missing.add(ch)
        if missing:
            probs.append(f"characters missing in font {key_pkg}: {' '.join(sorted(missing))}")
    return probs


def check_texts(spec, reel_captions):
    texts = spec_texts(spec) + list(reel_captions)
    probs = []
    for t in texts:
        probs += malayalam_sequence_problems(t)
    probs += check_fonts(texts)
    return probs


def check_news(row):
    v = (row.get("verification") or "").strip().lower()
    if not v:
        return ["news not marked as verified"]
    if re.search(r"unconfirmed|not verified|not confirmed|rumou?r|unverified|single source - unclear", v):
        return [f"news verification is weak: '{row.get('verification')}'"]
    return []


def ff_json(args):
    return json.loads(subprocess.run(args, capture_output=True, text=True, check=True).stdout)


def reel_duration(mp4):
    """length of a finished reel in seconds (0 if it cannot be read)"""
    try:
        return float(ff_json(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", str(mp4)])["format"].get("duration", 0))
    except Exception:
        return 0.0


def check_reel(mp4, spoken_lines):
    probs = []
    info = ff_json(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(mp4)])
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(info["format"].get("duration", 0))
    if not v or (v.get("width"), v.get("height")) != (1080, 1920):
        probs.append("reel is not 1080x1920")
    if not a:
        probs.append("reel has no audio (voice missing)")
    if not 10 <= dur <= 90:
        probs.append(f"reel length {dur:.1f}s is outside 10-90 seconds")
    if a:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "volumedetect", "-vn", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
        mx = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
        if not m or float(m.group(1)) < -40:
            probs.append("reel audio is silent or far too quiet")
        if mx and float(mx.group(1)) > -0.1:
            probs.append("reel audio is clipping (too loud)")
    # does the voice say everything that is written? (the voice model drops letters it cannot pronounce)
    sys.path.insert(0, str(ROOT / "reel"))
    try:
        import tts
        for line in spoken_lines:
            letters = [c for c in line if 0x0D00 <= ord(c) <= 0x0D7F]
            kept = [c for c in tts.clean(line) if 0x0D00 <= ord(c) <= 0x0D7F]
            if letters and (len(letters) - len(kept)) / len(letters) > 0.03:
                probs.append(f"the voice cannot pronounce part of: «{line[:40]}»")
    except Exception as e:
        probs.append(f"voice check could not run: {e}")
    return probs


INDIC_BASES = (0x0900, 0x0980, 0x0A00, 0x0A80, 0x0B00, 0x0B80, 0x0C00, 0x0C80)      # Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada
ML_OK = {c for c in range(0x0D00, 0x0D80) if __import__("unicodedata").name(chr(c), "")}
_TO_ML = {0x0BA9: 0x0D28}      # Tamil ன -> ന (Malayalam's old ഩ is missing in the fonts)
CJK_ETC = r"[\u3040-\u30FF\u3400-\u9FFF\uAC00-\uD7AF\u1100-\u11FF\u0E00-\u0E7F]"


def fix_scripts(t):
    """owner rule: the writer model sometimes types a letter of another script inside a Malayalam word (നির്ദേശം, പോലീस്,
    ജയിൽ탈출). The voice then misreads the word and the card shows a wrong letter. Indian scripts share Malayalam's letter
    order, so each such letter becomes the same Malayalam letter (द -> ദ, র -> ര, Tamil க -> ക); Chinese/Japanese/Korean/Thai
    letters are removed."""
    if not isinstance(t, str) or not t:
        return t
    import re as _re
    out = []
    for ch in t:
        c = ord(ch)
        base = next((b for b in INDIC_BASES if b <= c < b + 0x80), None)
        if base is None:
            out.append(ch)
            continue
        off = c - base
        cand = _TO_ML.get(c, 0x0D00 + off)                   # Malayalam has the aspirated/voiced letters: same place in the block
        if cand in ML_OK:
            out.append(chr(cand))
        elif off in (0x3C,):                                  # nukta: no Malayalam sign, drop
            continue
        # anything else without a Malayalam twin is dropped
    t = "".join(out)
    return _re.sub(CJK_ETC, "", t)


def clean_text(t):
    """owner rule: Malayalam text problems are FIXED, never a reason to skip a story. Removes broken characters, stray Malayalam
    vowel signs/virama (no consonant before them) and characters the fonts cannot draw."""
    if not isinstance(t, str) or not t:
        return t
    t = fix_scripts(t.replace("\ufffd", ""))
    out, prev = [], None
    for ch in t:
        c = ord(ch)
        if c in SIGNS and not _sign_ok(prev, c):
            continue      # stray sign: dropped
        out.append(ch)
        if c not in (0x200C, 0x200D):
            prev = ch
    t = "".join(out)
    cov = font_coverage() or {}
    cps = set()
    for (pkg, sub, w), s in cov.items():
        if pkg in HEAD_FONTS + (CT_FONT,):
            cps |= s
    if cps:
        t = "".join(ch for ch in t if not (0x0D00 <= ord(ch) <= 0x0D7F and ord(ch) not in cps and not ch.isspace()))
    return t


def clean_obj(o):
    """clean_text on every string inside a dict/list (used on the spec and the reel scenes before rendering)"""
    if isinstance(o, str):
        return clean_text(o)
    if isinstance(o, list):
        return [clean_obj(x) for x in o]
    if isinstance(o, dict):
        return {k: clean_obj(v) for k, v in o.items()}
    return o
