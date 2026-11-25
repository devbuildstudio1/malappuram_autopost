"""What Instagram insights taught us (written by poster/insights.py into learned.json). Used ONLY to order candidate stories and to give the
writer style hints. It never relaxes a fact / quality check."""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
TOPICS = {
    "weather": ["മഴ", "വെയിൽ", "കാലാവസ്ഥ", "മുന്നറിയിപ്പ്", "അലർട്ട്", "വെള്ളപ്പൊക്ക", "ഉരുൾപൊട്ട", "കാറ്റ്", "അവധി"],
    "crime": ["കൊല", "അറസ്റ്റ്", "പിടിയിൽ", "മോഷ", "പോലീസ്", "കേസ്", "തട്ടിപ്പ്", "ആത്മഹത്യ", "കവർച്ച", "എംഡിഎംഎ", "കഞ്ചാവ്", "ഹവാല", "മയക്കുമരുന്ന", "ലഹരി", "പിടികൂടി",
              "കവർന്ന", "ആക്രമിച്ച", "അപമാനിച്ച", "പീഡന", "എൻഫോഴ്സ്മെന്റ്",
              "പീഡിപ്പി", "പ്രായപൂർത്തിയാകാത്ത", "പോക്സോ", "കാപ്പ"],
    "accident": ["അപകട", "മരിച്ചു", "മരണം", "തീപിടിത്ത", "കൂട്ടിയിടിച്ച്", "മറിഞ്ഞ്", "ഇടിച്ച്", "പരിക്ക്", "മുങ്ങി"],
    "temple": ["ക്ഷേത്ര", "ഉത്സവ", "നേർച്ച", "പള്ളി", "പെരുന്നാൾ", "പൂജ", "ഉറൂസ്", "തിരുനാൾ"],
    "politics": ["മുഖ്യമന്ത്രി", "മന്ത്രി", "എംഎൽഎ", "എം.എൽ.എ", "തിരഞ്ഞെടുപ്പ്", "യുഡിഎഫ്", "എൽഡിഎഫ്", "ലീഗ്", "സിപിഎം", "കോൺഗ്രസ്", "ബിജെപി", "പാർട്ടി"],
    "poultry_agri": ["കൃഷി", "കർഷക", "വില", "വിപണി", "നെല്ല്", "തെങ്ങ്", "റബ്ബർ", "വാഴ", "മത്സ്യ", "കോഴി"],
    "education": ["വിദ്യാർഥി", "സ്കൂൾ", "കോളേജ്", "പരീക്ഷ", "സർവകലാശാല", "പ്ലസ് ടു", "എസ്എസ്എൽസി", "കോളജ", "കോളേജ"],
    "health": ["ആശുപത്രി", "ചികിത്സ", "ഡോക്ടർ", "രോഗി", "മെഡിക്കൽ കോളജ്", "ഷിഗെല്ല", "മഞ്ഞപ്പിത്ത", "പനി"],
    "obituary": ["അന്തരിച്ചു", "നിര്യാതനായി", "നിര്യാതയായി", "വിടവാങ്ങി", "ഖബറടക്കം"],
    "felicitation": ["ആദരി", "യാത്രയയപ്പ്", "സേവനത്തിന് ശേഷം", "അനുമോദി", "ഉദ്ഘാടനം", "ക്യാമ്പ്", "ഫെസ്റ്റ്", "സെമിനാർ", "ശിൽപശാല"],
    "civic": ["കുടിവെള്ള", "റോഡ്", "ബസ്", "നഗരസഭ", "പഞ്ചായത്ത്", "മാലിന്യ", "ദേശീയപാത", "ഗതാഗത", "പാലം", "ട്രാഫിക്", "റെയിൽവേ", "കനാൽ", "കളിസ്ഥല", "സ്ഥലമില്ല"],
    "sports_culture": ["മത്സരം", "ഫുട്ബോൾ", "സെവൻസ്", "കായിക", "കലോത്സവ", "സിനിമ", "പുരസ്കാര"],
}


# power cuts and jobs are their own topics and win over any other topic word in the headline ('റോഡ്' in a power-cut notice is still a
# power cut); on the Namakkal pages they were the most watched news.
FIRST = {
    "power_cut": ["വൈദ്യുതി മുടങ്ങും", "വൈദ്യുതി മുടക്കം", "വൈദ്യുതി മുടങ്ങി", "വൈദ്യുതി തടസ്സ", "വൈദ്യുതി വിതരണം തടസ്സ", "പവർകട്ട്",
                  "ലോഡ് ഷെഡ്ഡിങ്", "power cut", "power outage", "power shutdown"],
    # owner 20 Nov: the hartal notice (15 Nov) was our most liked reel by far and brought the biggest follower jump; news that changes
    # everyone's day (hartal, strike, road / water closure, school holiday) gets its own topic so it is measured and never skipped.
    "public_alert": ["ഹർത്താൽ", "പണിമുടക്ക്", "ബസ് സമരം", "ഗതാഗതം നിരോധി", "ഗതാഗത നിയന്ത്രണ", "വഴിതിരിച്ചു", "കുടിവെള്ളം മുടങ്ങ",
                     "ജലവിതരണം മുടങ്ങ", "ജലവിതരണം തടസ്സ", "സ്കൂളുകൾക്ക് അവധി", "വിദ്യാഭ്യാസ സ്ഥാപനങ്ങൾക്ക് അവധി", "അവധി പ്രഖ്യാപി"],
    # owner 20 Nov: one gold-rate reel a day ('വില' alone put it in poultry_agri, a skipped topic, so it never went out)
    "gold_price": ["സ്വർണവില", "സ്വർണ വില", "സ്വർണം വില", "gold rate", "gold price"],
    "jobs": ["തൊഴിൽ മേള", "ജോലി ഒഴിവ്", "ഒഴിവുകൾ", "ഒഴിവ്", "നിയമനം", "അഭിമുഖം", "റിക്രൂട്ട്", "job fair", "recruitment", "vacanc"],
}
# starting weight until insights has measured MIN_PER_TOPIC posts of the topic (then the measured weight is used)
PRIOR = {"power_cut": 1.0, "jobs": 1.0, "public_alert": 1.5, "gold_price": 1.5}


def headline(caption):
    """the headline of a posted caption (its first line). Topics are judged on the headline only: the collector and the poster only ever
    see the headline, and the body's background words ('വില' in a gold-smuggling story, 'മന്ത്രി' quoted in a road story) put 60 of
    157 measured reels in the wrong topic, so the hartal reel counted as poultry_agri and politics was skipped (20 Nov)."""
    return (caption or "").strip().split("\n")[0]


def topic(text):
    try:
        import allnews
        t = allnews.norm(text)
    except Exception:
        t = text or ""
    low = t.lower()
    for k, words in FIRST.items():
        if any(w.lower() in low for w in words):
            return k
    best, n = "other", 0
    for k, words in TOPICS.items():
        c = sum(1 for w in words if w in t)
        if c > n:
            best, n = k, c
    return best


def load():
    try:
        return json.loads((HERE / "learned.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def boost(text):
    """score adjustment for a candidate headline from its topic's measured performance (weights are already clamped by insights.py),
    plus +0.5 for each word it shares with our viral reels (viral_hits, at most +1.5)"""
    t = topic(text)
    w = (load().get("topic_weight") or {}).get(t)
    base = float(w) if w is not None else PRIOR.get(t, 0.0)
    return base + min(1.5, 0.5 * viral_hits(text))


# ---- owner 25 Nov 'post reels similar to the ones that went viral'. The viral reels of 16-24 Nov (185, 141, 138, 98, 95, 91 likes
# against a page median of 1) were police / crime drama about YOUNG people: '18കാരൻ പിടിയിൽ', students' brawl, youths' deaths,
# '19 വയസ്സുകാരൻ അറസ്റ്റ്', theft of lakhs. insights.py finds the headline words that are far more common in our viral reels (5x the page
# median or more) than in the rest and stores them in learned.json viral_words; stories using them are written and posted first.
VIRAL_REL, VIRAL_LIFT, VIRAL_MIN_TOP, VIRAL_MIN_ALL, VIRAL_MAX = 5.0, 2.0, 3, 4, 20
# grammar / filler stems and words in nearly every headline: never a 'viral word'
VIRAL_STOP = {"ചെയ്ത", "ചെയ്യ", "നിന്ന", "കൊണ്ട", "മാറ്റ", "നടന്ന", "നൽകി", "നൽകിയ", "എന്ന്", "ഇന്ന്", "നാളെ", "പൂർണ", "വിവരം",
              "മലപ്പ", "ജില്ല", "സംസ്ഥ", "കേരള", "മഞ്ചേ", "രൂപയു"}


def stems(text):
    try:
        import allnews
        t = allnews.norm(text or "")
    except Exception:
        t = text or ""
    return {w[:5] for w in re.findall(r"[\u0D00-\u0D7F]{4,}", t)}


def _place_stems():
    try:
        import allnews
        return {s for w in allnews.DISTRICT_WORDS for s in stems(w)}
    except Exception:
        return set()


def viral_words(rows):
    """rows = measured reels with 'caption' and 'rel' (score / page median). The headline stems with the highest lift in viral reels."""
    import collections
    top = [h for h in rows if h.get("rel", 0) >= VIRAL_REL]
    if len(top) < 5:
        return []
    skip = VIRAL_STOP | _place_stems()
    ct, ca = collections.Counter(), collections.Counter()
    for h in rows:
        s = stems(headline(h.get("caption")))
        ca.update(s)
        if h.get("rel", 0) >= VIRAL_REL:
            ct.update(s)
    lift = {s: (ct[s] / len(top)) / (n / len(rows)) for s, n in ca.items()
            if n >= VIRAL_MIN_ALL and ct[s] >= VIRAL_MIN_TOP and s not in skip}
    return [s for s, l in sorted(lift.items(), key=lambda kv: -kv[1]) if l >= VIRAL_LIFT][:VIRAL_MAX]


def viral_hits(text):
    vw = set(load().get("viral_words") or [])
    return len(stems(text) & vw) if vw else 0


def viral_like(text):
    """2+ viral words: a story like our viral reels, written and posted even when its topic is in skip_topics"""
    return viral_hits(text) >= 2


def hints():
    """short style guidance for the writer prompt; '' until enough posts have been measured"""
    d = load()
    out = []
    if d.get("avg_watch_s"):
        out.append(f"Viewers leave after about {d['avg_watch_s']} seconds on average: the FIRST sentence of reel_script must carry the most surprising fact (a number, place or consequence), never a greeting or background.")
    if d.get("top_openings"):
        out.append("Openings of our best-performing reels (style reference only, never copy facts): " + " | ".join(d["top_openings"][:4]))
    return "\n".join(out)
