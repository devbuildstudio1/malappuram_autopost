"""Last Malayalam proofread before a reel is built: spelling, sandhi (സന്ധി), grammar and unclear sentences in everything that goes out
(headline, slide texts shown in the reel, the spoken script, the caption). Free models first, Claude only when they are not available.
Only exact, small corrections are applied; a correction that changes a number, or makes broken Malayalam, is ignored."""
import difflib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "research_free"))

PROOF = """You are a senior Malayalam news editor and proofreader. You get the texts of ONE Malayalam news post as JSON.
Find every real mistake: wrong spelling, wrong sandhi (സന്ധി, e.g. missing consonant doubling such as ക്ക/ച്ച/ത്ത/പ്പ), wrong chillu
(ർ ൽ ൻ ൾ ൺ) or a chillu written as consonant + virama, wrong case ending (വിഭക്തി), wrong verb form, a word that does not exist,
a broken or unclear sentence, a sentence that mixes two facts, spoken/colloquial forms in headline_ml and caption (ഉണ്ടാർന്നു -> ഉണ്ടായിരുന്നു),
dialect spellings anywhere (ഇണ്ട്, ഇങ്ങള്, പോയീന്). reel_script is DELIBERATELY friendly spoken Malayalam (പറഞ്ഞു, ഇടിച്ചു, പരിക്ക് പറ്റി,
വിളിക്കാം, കറന്റ്, ശ്രദ്ധിക്കണേ): that is correct there - never make it formal, only fix real spelling/grammar mistakes in it,
and English words written in English letters inside Malayalam text.
For each mistake give the EXACT wrong text as it appears (a few words, copied character by character) and the corrected text.
STRICT: never change a number, date, time, amount, name, place or fact; never add information; do not rewrite text that is already correct;
keep the closing follow line and hashtags as they are. If everything is correct, return an empty list.
Return ONLY JSON: {"fixes": [{"wrong": "exact text", "right": "corrected text", "why": "short reason"}]}"""

FIELDS = ("headline_ml", "reel_script", "caption")


def _texts(row):
    spec = json.loads(row.get("slides_spec") or "{}")
    slides = [{"title": s.get("title", ""), "lines": s.get("lines", [])} for s in spec.get("slides", [])]
    return {"headline_ml": row.get("headline_ml", ""), "hl1": spec.get("hl1", ""), "hl2": spec.get("hl2", ""), "slides": slides,
            "reel_script": row.get("reel_script", ""), "caption": (row.get("caption") or "").split("#")[0].strip()}


def _digits(t):
    return re.findall(r"\d+", t or "")


LASTS = ("കൂടുതൽ വാർത്തകൾക്ക് മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ.",
         "കൂടുതൽ വാർത്തകൾക്ക് മഞ്ചേരി ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ.")
LAST = LASTS[0]
KEEP = ("മലപ്പുറം", "മഞ്ചേരി", "ത്രീ", "സിക്സ്റ്റി", "ഫോളോ", "360")      # page names and the follow line are never "corrected"
NEG = ("ഇല്ല", "അല്ല", "ഇല്ലാത്ത", "ല്ല", "അരുത്", "വേണ്ട", "കൂടാതെ", "ആതെ", "ാതെ", "രഹിത")      # a fix that adds "not" flips the meaning
# ("ല്ല" catches negation written as a suffix: വരേണ്ട -> വരേണ്ടതില്ല, ബന്ധപ്പെട്ട -> ബന്ധപ്പെട്ടതല്ല)
ML = "\u0D00-\u0D7F\u200c\u200d\\w"


def _whole(w):
    return re.compile(f"(?<![{ML}]){re.escape(w)}(?![{ML}])")


def _repeats(t):
    """'X X' or 'X Y X' word runs (a proofreader once returned 'പോകാതെ പോയി പോകാതെ')"""
    w = re.findall(r"\S+", t or "")
    return {" ".join(w[i:i + 3]) for i in range(len(w) - 2) if w[i] == w[i + 2] and len(w[i]) > 3} | \
        {" ".join(w[i:i + 2]) for i in range(len(w) - 1) if w[i] == w[i + 1] and len(w[i]) > 3}


def _article(row):
    try:
        import allnews
        a = allnews.article_any((row.get("source") or "").strip())
        return (a.get("title", "") + " " + a.get("text", "")) if isinstance(a, dict) else str(a[-1] if isinstance(a, (tuple, list)) else a or "")
    except Exception:
        return ""


VERB_ENDS = ("ുന്നു", "ുന്ന", "ിച്ചു", "ിച്ച", "ും", "ാൻ", "പ്പെട്ടു", "പ്പെട്ട", "ുകയാണ്", "ുകയായിരുന്നു", "ിരുന്നു", "ിട്ടുണ്ട്")


def unsafe(w, ok, article=""):
    """why a proposed fix must NOT be applied ('' = safe). Proofreading models change place names, flip a 'must' into a
    'need not', delete facts and double words - only small spelling fixes go in."""
    if not w or not ok or w == ok or len(w) < 2:
        return "empty"
    if re.search(r"[A-Za-z]", w + ok):
        return "English text / follow line"
    if _digits(w) != _digits(ok):
        return "number changed"
    if any(k in w for k in KEEP):
        return "page or place name"
    if any(n in ok and n not in w for n in NEG):
        return "meaning flipped"
    abbr = r"[ഀ-ൿ]\.\s?[ഀ-ൿ]"
    if re.search(abbr, ok) and not re.search(abbr, w):      # a name shortened to initials (പെരിന്തൽമണ്ണ -> പി.മണ്ണ) is not a spelling fix
        return "name shortened"
    if abs(len(ok.split()) - len(w.split())) > 1 or difflib.SequenceMatcher(None, w, ok).ratio() < 0.6:
        return "rewrite, not a spelling fix"
    # a misspelt verb must not become a noun ('നിയന്ത്രിക്കുന്നു' -> 'നിയന്ത്രണം'): a fix must keep the word's grammatical ending
    lw, lo = w.split()[-1].strip(".,;:!?()\"'"), ok.split()[-1].strip(".,;:!?()\"'")
    if any(lw.endswith(e) and not lo.endswith(e) for e in VERB_ENDS):
        return "word form changed (verb into another word)"
    words = [x.strip(".,;:!?()\"'") for x in w.split()]
    if article and all(_whole(x).search(article) for x in words if x):
        return "the article itself writes it this way"
    import verify
    if verify.malayalam_sequence_problems(ok):
        return "broken Malayalam"
    return ""


def proofread(row, log=print, article=None):
    """corrects row in place; returns the number of corrections applied. Only whole-word, single-place, small spelling/sandhi
    fixes are applied; anything that could change a fact or the meaning is ignored."""
    import llm
    user = json.dumps(_texts(row), ensure_ascii=False)
    try:
        try:
            r, m = llm.ask_json(PROOF, user)
        except Exception:
            if not llm.claude_available():
                raise
            r, m = llm.ask_claude(PROOF, user, max_tokens=3000)
    except Exception as e:
        log("Malayalam proofread unavailable (posting goes on):", str(e)[:150])
        return 0
    fixes = (r or {}).get("fixes") if isinstance(r, dict) else None
    if not fixes:
        log(f"Malayalam proofread by {m}: no mistakes found")
        return 0
    if article is None:
        article = _article(row)
    spec = row.get("slides_spec") or ""
    done = 0
    for f in fixes[:25]:
        w, ok = str(f.get("wrong") or "").strip(), str(f.get("right") or "").strip()
        why = unsafe(w, ok, article)
        if why:
            log(f"proofread fix ignored ({why}):", w[:40], "->", ok[:40])
            continue
        hit = False
        for k in FIELDS:
            t = row.get(k) or ""
            if len(_whole(w).findall(t)) != 1:      # not there, or in several places: never replace blindly
                continue
            end = next((x for x in LASTS if t.rstrip().endswith(x)), "") if k == "reel_script" else ""
            body, last = (t.rstrip()[:-len(end)], end) if end else (t, "")
            new = _whole(w).sub(lambda _: ok, body, count=1) + last
            if _repeats(new) - _repeats(t):
                log("proofread fix ignored (would double words):", w[:40], "->", ok[:40])
                continue
            row[k], hit = new, True
        jw, jo = json.dumps(w, ensure_ascii=False)[1:-1], json.dumps(ok, ensure_ascii=False)[1:-1]
        if len(_whole(jw).findall(spec)) == 1:
            spec, hit = _whole(jw).sub(lambda _: jo, spec, count=1), True
        if hit:
            done += 1
            log(f"Malayalam fix: «{w}» -> «{ok}» ({str(f.get('why', ''))[:60]})")
    try:
        json.loads(spec)
        row["slides_spec"] = spec
    except Exception:
        log("proofread fixes in the slide texts skipped (would break the format)")
    log(f"Malayalam proofread by {m}: {done} of {len(fixes)} corrections applied")
    return done
