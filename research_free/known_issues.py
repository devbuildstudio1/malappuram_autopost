"""Known issues that must NEVER repeat (owner 29 Oct: "once an issue is found, the automatic creating and posting must not repeat it").

Every issue found in a posted reel gets ONE entry here: the pattern that catches it, the story it came from, a real bad example and a good
one. The SAME list is checked
  - when a story is written (research_free/validate.py -> the writer rewrites it), and
  - right before posting (poster/post.py skip_reason -> a story written before the fix is not posted).
tests/test_regressions.py runs every entry against its own examples, so an entry that stops catching its issue fails the tests.
To add an issue: add an entry with its bad and good example; nothing else needs changing."""
import json, re

# a card line that ends in a joining form (genitive -ന്റെ / -ുടെ, locative-adjective -ിലെ, participle -ആയ / -ുള്ള / -ന്ന) was cut before
# the word it belongs to ('ലോകത്തിലെ മികച്ച 3 സ്ഥാപനങ്ങളുടെ')
DANGLING = re.compile("(\u0D28\u0D4D\u0D31\u0D46|\u0D41\u0D1F\u0D46|\u0D3F\u0D32\u0D46|\u0D06\u0D2F|\u0D41\u0D33\u0D4D\u0D33|\u0D28\u0D4D\u0D28)$")
# letters of another script (Devanagari ... Kannada, Sinhala, CJK, Hangul, Cyrillic, Arabic) - Malayalam itself is U+0D00-U+0D7F
FOREIGN = re.compile("[\u0900-\u0CFF\u0D80-\u0DFF\u3000-\u9FFF\uAC00-\uD7AF\u0400-\u04FF\u0600-\u06FF]")
META = ["ലേഖനത്തിൽ", "ഈ ലേഖനം", "വാർത്തയിൽ പറയുന്നില്ല", "വിവരം ലഭ്യമല്ല", "വിവരങ്ങൾ ലഭ്യമല്ല", "വിശദാംശങ്ങൾ ലഭ്യമല്ല",
        "കൂടുതൽ വിവരങ്ങൾ ലഭിക്കുമ്പോൾ", "വിവരം ലഭിക്കുന്ന മുറയ്ക്ക്", "ബന്ധപ്പെട്ടതല്ല", "പരാമർശിച്ചിട്ടില്ല", "പരാമർശിക്കുന്നില്ല",
        "the article", "this article", "not mentioned in", "no information"]
ESSAY = "\u0D32\u0D47\u0D16\u0D28\\s*\u0D2E\u0D24\u0D4D\u0D38\u0D30"      # ലേഖന മത്സരം = an essay competition is real school news


def _norm(t):
    try:
        import allnews
        return allnews.norm(t)
    except Exception:
        return t or ""


def texts(story):
    """the words a viewer sees or hears, from a writer draft (malayalam_headline, slides_spec dict) or a Sheet row (headline_ml, slides_spec JSON)"""
    sp = story.get("slides_spec") or {}
    if isinstance(sp, str):
        try:
            sp = json.loads(sp)
        except Exception:
            sp = {}
    cards = [_norm(re.sub(r"<[^>]+>", "", str(ln))) for sl in (sp.get("slides") or []) for ln in (sl.get("lines") or [])]
    return {"headline": _norm(str(story.get("malayalam_headline") or story.get("headline_ml") or "")), "script": _norm(str(story.get("reel_script") or "")),
            "caption": _norm(str(story.get("caption") or "")), "cards": cards}


def _meta(t):
    for k in ("headline", "script", "caption"):
        s = re.sub(ESSAY, " ", t[k])      # an essay competition is real school news
        hit = next((w for w in META if w.lower() in s.lower()), "")
        if hit:
            return f"{k} talks about the article instead of the news ('{hit}')"
    return ""


def _foreign(t):
    for k in ("headline", "script", "caption"):
        bad = FOREIGN.findall(t[k])
        if bad:
            return f"{k} has letters of another script ({''.join(bad[:4])})"
    return next((f"card has letters of another script ({''.join(FOREIGN.findall(c)[:4])})" for c in t["cards"] if FOREIGN.search(c)), "")


def _english(t):
    eng = sorted(set(re.findall(r"[A-Za-z]{2,}", t["script"])))
    return f"voice script has English words the voice skips ({', '.join(eng[:4])})" if eng else ""


def _dangling(t):
    bad = next((c for c in t["cards"] if DANGLING.search(c.strip(" .,;:"))), "")
    return f"card cut off mid-phrase ('{bad[-24:]}')" if bad else ""


# normal Malayalam doubling ('പതുക്കെ പതുക്കെ' = slowly, 'വീണ്ടും വീണ്ടും' = again and again) is not a mistake
REDUP = {"പതുക്കെ", "മെല്ലെ", "വീണ്ടും", "തുടരെ", "പല", "ചില", "ഓരോ", "അങ്ങിങ്ങ്", "വേഗം", "പെട്ടെന്ന്", "ചെറിയ", "കുറേ", "നന്നായി",
         "ഓടി", "തനിച്ച്", "വീട്", "നാട്", "തെരുവ്", "ദിവസം"}


def _repeat(t):
    w = t["script"].split()
    rep = next((a for a, b in zip(w, w[1:]) if a == b and len(a) > 3 and a not in REDUP), "")      # 'എസ് എസ്' (a name) is fine
    if rep:
        return f"word said twice in a row ('{rep}')"
    # split only at a real sentence end ('. ' + next word) - '2.50', 'എച്ച്.പി.' and 'കി.മീ.' are not sentence ends
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t["script"]) if len(s.strip()) > 25]
    return "the same sentence is read twice" if len(sents) != len(set(sents)) else ""


# id, first seen, check, a real bad example, a good example
ISSUES = [
    ("meta_article", "carried over from the Namakkal pipeline (a reel that talked about 'the article')", _meta,
     {"headline_ml": "ഇന്നത്തെ സ്വർണവില", "reel_script": "സ്വർണവില ഈ ലേഖനത്തിൽ നൽകിയിട്ടില്ല. വിവരം ലഭിക്കുന്ന മുറയ്ക്ക് അറിയിക്കും."},
     {"headline_ml": "മഞ്ചേരിയിൽ ഗതാഗത നിയന്ത്രണം", "reel_script": "മഞ്ചേരി റോഡിൽ നാളെ ഗതാഗത നിയന്ത്രണം ഏർപ്പെടുത്തും. സ്കൂളിൽ ലേഖന മത്സരം നടന്നു."}),
    ("foreign_script", "carried over from the Namakkal pipeline (letters of other scripts inside words)", _foreign,
     {"headline_ml": "ജയില്\u0BAA\u0BA3\u0BBF ജീവനക്കാരുടെ 監獄 കുറവ്", "reel_script": "ജയിൽ ജീവനക്കാരുടെ കുറവ്."},
     {"headline_ml": "ജയിൽ ജീവനക്കാരുടെ കുറവ്", "reel_script": "ജയിൽ ജീവനക്കാരുടെ കുറവ്."}),
    ("english_in_voice", "carried over from the Namakkal pipeline (English words the voice skips)", _english,
     {"reel_script": "ജർമനിയിൽ FBN Global Summit നടന്നു."},
     {"reel_script": "ജർമനിയിൽ എഫ് ബി എൻ ആഗോള ഉച്ചകോടി നടന്നു."}),
    ("card_cut_mid_phrase", "carried over from the Namakkal pipeline (card line cut before its last word)", _dangling,
     {"slides_spec": {"slides": [{"lines": ["ലോകത്തിലെ മികച്ച 3 സ്ഥാപനങ്ങളുടെ"]}]}},
     {"slides_spec": {"slides": [{"lines": ["ലോകത്തിലെ മികച്ച 3 സ്ഥാപനങ്ങളിൽ ഒന്ന്"]}]}}),
    ("repeated_words", "carried over from the Namakkal pipeline (a word read twice)", _repeat,
     {"reel_script": "സ്കൂളിൽ പോകാതെ പോകാതെ ജന്മദിനം ആഘോഷിച്ചു."},
     {"reel_script": "സ്കൂളിൽ പോകാതെ ജന്മദിനം ആഘോഷിച്ചു. പതുക്കെ പതുക്കെ വെള്ളം ഉയർന്നു. എസ് എസ് കൺസ്ട്രക്ഷൻസാണ് പണി നടത്തുന്നത്. "
                     "5 എച്ച്.പി. മോട്ടോറിന് കണക്ഷൻ ചാർജ് 2.50 ലക്ഷം രൂപ. 15 എച്ച്.പി. മോട്ടോറിന് കണക്ഷൻ ചാർജ് 4 ലക്ഷം രൂപ."}),
]


def problems(story):
    """[(issue id, what is wrong)] for every known issue found in this draft or Sheet row"""
    t = texts(story)
    out = []
    for iid, _, check, _, _ in ISSUES:
        why = check(t)
        if why:
            out.append((iid, why))
    return out


def _sentences(t):
    return [x for x in re.split(r"(?<=[.!?])\s+", t.strip()) if x]


def repair(story):
    """owner 29 Oct: an issue that CAN be fixed is fixed, not a reason to lose the news. Returns a copy with: sentences about 'the article'
    removed, a word or sentence said twice said once, card lines cut mid-phrase trimmed to whole words. What cannot be fixed (letters of
    another script left after verify.clean_text, English words in the voice) is still caught by problems()."""
    out = dict(story)
    for k in ("reel_script", "caption"):
        t = str(out.get(k) or "")
        if not t:
            continue
        lines = []
        for line in t.split("\n"):
            keep, seen = [], set()
            for sent in _sentences(line) or [line]:
                low = re.sub(ESSAY, " ", _norm(sent)).lower()
                if any(w.lower() in low for w in META) and len(_sentences(t)) > 2:
                    continue      # a sentence that only talks about the article
                key = sent.strip()
                if len(key) > 15 and key in seen:
                    continue      # the same sentence again
                seen.add(key)
                w = sent.split()
                sent = " ".join(x for i, x in enumerate(w) if not (i and x == w[i - 1] and len(x) > 3 and x not in REDUP))
                keep.append(sent)
            lines.append(" ".join(keep))
        out[k] = "\n".join(lines)
    sp, as_text = out.get("slides_spec"), False
    if isinstance(sp, str):
        try:
            sp, as_text = json.loads(sp), True
        except Exception:
            sp = None
    if isinstance(sp, dict):
        sp = json.loads(json.dumps(sp, ensure_ascii=False))      # work on a copy - never change the caller's story
        for sl in sp.get("slides") or []:
            new = []
            for ln in sl.get("lines") or []:
                plain = re.sub(r"<[^>]+>", "", str(ln)).strip()
                if DANGLING.search(plain.strip(" .,;:")):
                    ws = plain.split()
                    while len(ws) > 1 and DANGLING.search(ws[-1].strip(" .,;:")):
                        ws.pop()
                    plain = " ".join(ws).rstrip(" ,;:-")
                    if DANGLING.search(plain) and len(sl.get("lines") or []) > 1:
                        continue      # nothing whole left: drop the line (the slide keeps its other lines)
                    ln = plain
                new.append(ln)
            sl["lines"] = new or sl.get("lines")
        out["slides_spec"] = json.dumps(sp, ensure_ascii=False) if as_text else sp
    return out

