"""Date checks for announcement-type news (power cuts, job fairs / interviews, camps, 'today' / 'tomorrow' items):
such a story is only worth posting while the date it announces has not passed. Pure functions, used by the poster and by the collector."""
import datetime, re

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
EN_M = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
# Malayalam month names (full, and the spellings papers use: മേയ്/മെയ്, ആഗസ്റ്റ്/ഓഗസ്റ്റ്) and the short forms
ML_FULL = {"ജനുവരി": 1, "ഫെബ്രുവരി": 2, "മാർച്ച്": 3, "ഏപ്രിൽ": 4, "മേയ്": 5, "മെയ്": 5, "ജൂൺ": 6, "ജൂലൈ": 7, "ആഗസ്റ്റ്": 8,
           "ഓഗസ്റ്റ്": 8, "സെപ്റ്റംബർ": 9, "ഒക്ടോബർ": 10, "നവംബർ": 11, "ഡിസംബർ": 12}
ML_ABB = {"ജനു": 1, "ഫെബ്ര": 2, "സെപ്റ്റ": 9, "ഒക്ടോ": 10, "നവം": 11, "ഡിസം": 12}
# old-style chillu letters (consonant + virama + ZWJ) are written as the atomic chillu, so one spelling matches both
_CHILLU = {"ര്\u200d": "ർ", "ല്\u200d": "ൽ", "ന്\u200d": "ൻ", "ള്\u200d": "ൾ", "ണ്\u200d": "ൺ", "ക്\u200d": "ൿ"}


def norm_ml(t):
    t = str(t or "")
    for a, b in _CHILLU.items():
        t = t.replace(a, b)
    return t.replace("\u200d", "").replace("\u200c", "")


POWER_ML = r"വൈദ്യുതി\s*(?:വിതരണം\s*)?(?:മുട|തടസ്സ|നിയന്ത്രണ)|പവർ\s*കട്ട്|ലോഡ്\s*ഷെഡ്ഡിങ്"
TRIGGER = re.compile(POWER_ML + r"|power\s?cut|shutdown|തൊഴിൽ\s*മേള|ജോബ്\s*ഫെയർ|job\s?fair|interview|ഇന്റർവ്യൂ|അഭിമുഖം|"
                     r"recruitment|camp\b|ക്യാമ്പ്|walk-?in|ഇന്ന്|ഇന്നത്തെ|നാളെ|നാളത്തെ|tonight|\btoday\b|\btomorrow\b", re.I)
SHUT = re.compile(POWER_ML + r"|power\s?cut|shutdown", re.I)
TODAY = re.compile(r"ഇന്ന്|ഇന്നത്തെ|\btoday\b|tonight", re.I)
TOMORROW = re.compile(r"നാളെ|നാളത്തെ|\btomorrow\b", re.I)


def _mon_en(t):
    return EN_M.get(t[:3].lower())


def dates_in(text, year):
    """explicit dates ('23 Oct', 'Oct 23', 'ഒക്ടോബർ 23', 'ഒക്ടോബർ 23ന്', '23 ഒക്ടോബർ') found in the text -> list of date objects"""
    text = norm_ml(text)
    out = []
    pats_en = [(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*", 1, 2),
               (r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b", 2, 1)]
    for p, di, mi in pats_en:
        for m in re.finditer(p, text, re.I):
            out.append((int(m.group(di)), _mon_en(m.group(mi))))
    ml_mon = "|".join(sorted(list(ML_FULL) + list(ML_ABB), key=len, reverse=True))
    mal = {**ML_ABB, **ML_FULL}
    for m in re.finditer(r"(?<!\d)(\d{1,2})\s*-?\s*(%s)\.?(?![\u0D00-\u0D7F])" % ml_mon, text):
        out.append((int(m.group(1)), mal[m.group(2)]))
    for m in re.finditer(r"(%s)\.?\s*-?\s*(\d{1,2})(?!\d)" % ml_mon, text):
        out.append((int(m.group(2)), mal[m.group(1)]))
    res = []
    for d, mo in out:
        try:
            res.append(datetime.date(year, mo, d))
        except (ValueError, TypeError):
            pass
    return res


def pub_date(s):
    """date of the 'published' cell: ISO or '21 Oct 2026, 05:24 IST'"""
    s = str(s or "")
    try:      # owner 29 Oct: an ISO time with a zone ('...T22:17:23Z' = 03:47 next morning in IST) is read in IST, not by its UTC date
        t = datetime.datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        if t.tzinfo is not None:
            return t.astimezone(IST).date()
    except ValueError:
        pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})", s)
    if m and _mon_en(m.group(2)):
        return datetime.date(int(m.group(3)), _mon_en(m.group(2)), int(m.group(1)))
    return None


def stale_reason(headline_ml, headline_en, category, published, today=None):
    """'' when the story is still current, else why it must not be posted"""
    today = today or datetime.datetime.now(IST).date()
    text = norm_ml(f"{headline_ml} {headline_en} {category}")
    price = bool(RECUR.search(text))
    if not TRIGGER.search(text) and not price:
        return ""
    pub = pub_date(published)
    ds = dates_in(f"{headline_ml} {headline_en}", today.year)
    ds = [d for d in ds if (d - today).days < 300]
    if ds:
        if max(ds) < today:
            return f"announced date {max(ds):%d %b} has passed"
        return ""
    if pub:
        if price and pub < today:           # a daily price is only news on the day it applies to
            return f"price news from {pub:%d %b}, not today"
        if TODAY.search(text) and pub < today:
            return f"says 'today' but was published {pub:%d %b}"
        if TOMORROW.search(text) and pub + datetime.timedelta(days=1) < today:
            return f"says 'tomorrow' but was published {pub:%d %b}"
        if SHUT.search(text) and pub < today and not TOMORROW.search(text):
            return f"power-cut notice from {pub:%d %b} with no date"
    return ""


def news_date(published, source_url="", filed=None):
    """the day the news was published: the 'published' cell, else the date in the newspaper's link (/2026/Oct/26/, 2026-10-26,
    /20261026/), else the day it was filed (never earlier than the real day, so it can only be lenient)"""
    d = pub_date(published)
    if d:
        return d
    u = str(source_url or "")
    m = re.search(r"/(20\d\d)/([A-Za-z]{3})[a-z]*/(\d{1,2})/", u)
    if m and _mon_en(m.group(2)):
        return datetime.date(int(m.group(1)), _mon_en(m.group(2)), int(m.group(3)))
    m = re.search(r"/(20\d\d)[/-](\d{2})[/-](\d{2})(?:/|\b)", u)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"/(20\d\d)(\d{2})(\d{2})/", u)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return filed.date() if filed else None


def power_cut_over(headline_ml, headline_en, published, now=None):
    """'' or why a power-cut notice is too late to post: the cut is today and its end time ('ഉച്ചയ്ക്ക് 2 വരെ', 'till 5 pm') is less
    than 1 hour away or past. Checked even for stories filed today (27 Oct: a 9-2 cut was about to go out at 1:40 pm as 'tomorrow')."""
    headline_ml = norm_ml(headline_ml)
    text = f"{headline_ml} {headline_en}"
    if not SHUT.search(text):
        return ""
    now = now or datetime.datetime.now(IST)
    today, pub = now.date(), pub_date(published)
    ds = [d for d in dates_in(text, today.year) if abs((d - today).days) < 300]
    day = max(ds) if ds else (pub + datetime.timedelta(days=1) if pub and TOMORROW.search(text) else pub)
    if day != today:
        return ""
    m = (re.search(r"(ഉച്ചയ്ക്ക്|ഉച്ചക്ക്|ഉച്ചകഴിഞ്ഞ്|ഉച്ചതിരിഞ്ഞ്|വൈകിട്ട്|വൈകീട്ട്|വൈകുന്നേരം|രാത്രി)?\s*(\d{1,2})(?:[.:](\d{2}))?\s*(?:മണി\s*)?വരെ", headline_ml or "")
         or re.search(r"(?:till|to|until)\s*(\d{1,2})(?:[.:](\d{2}))?\s*(pm|am)?", headline_en or "", re.I))
    if not m:
        return ""
    if m.re.pattern.startswith("(ഉച്ചയ്ക്ക്"):
        pm, h, mi = bool(m.group(1)) or int(m.group(2)) <= 7, int(m.group(2)), int(m.group(3) or 0)
    else:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        pm = (m.group(3) or "").lower() == "pm" or (not m.group(3) and h <= 7)
    if pm and h < 12:
        h += 12
    end = now.replace(hour=min(h, 23), minute=mi, second=0, microsecond=0)
    if now >= end - datetime.timedelta(minutes=60):
        return f"power cut ends today at {end:%H:%M} - too late to post"
    return ""


# ---- repeating topics (daily gold rate, rubber price, fuel price ...): the same headline every day is NEW news each day
_GOLD = r"സ്വർണ\s*(?:ം\s*)?വില|സ്വർണവില|gold\s*(?:rate|price)"
_RUBBER = r"റബ(?:ർ|റി)\s*(?:ന്റെ\s*)?വില|rubber\s*(?:price|rate)"
_FUEL = r"പെട്രോൾ\s*വില|ഡീസൽ\s*വില|ഇന്ധന\s*വില|petrol|diesel"
RECUR = re.compile("|".join([_GOLD, _RUBBER, _FUEL]), re.I)


def recurring(text):
    return bool(RECUR.search(norm_ml(text)))


RECUR_TOPICS = {"gold": re.compile(_GOLD, re.I), "rubber": re.compile(_RUBBER, re.I), "fuel": re.compile(_FUEL, re.I)}


def recur_topic(*texts):
    t = norm_ml(" ".join(x or "" for x in texts))
    return next((k for k, rx in RECUR_TOPICS.items() if rx.search(t)), "")


def same_day_recurring(old, new, today=None):
    """a daily price topic (gold rate, rubber price ...) is posted ONCE a day, whatever the headline words"""
    k = recur_topic(old.get("headline_ml"), old.get("headline_en"))
    if not k or k != recur_topic(new.get("headline_ml"), new.get("headline_en")):
        return ""
    d_old = pub_date(old.get("researched"))
    d_new = pub_date(new.get("researched")) or today or datetime.datetime.now(IST).date()
    return k if d_old and d_old == d_new else ""


def different_numbers(a, b):
    """both headlines give numbers and none of them match: a different event (8 arrested / Rs 1,47,000 is not 6 people / Rs 11,600)"""
    na = set(re.findall(r"\d+", (a or "").replace(",", "")))
    nb = set(re.findall(r"\d+", (b or "").replace(",", "")))
    return bool(na) and bool(nb) and not (na & nb)


POWER = re.compile(POWER_ML + r"|power\s*(cut|shut)", re.I)
_POWER_COMMON = ("വൈദ്യു", "മുട", "തടസ്സ", "വിതര", "നിയന്ത", "നാളെ", "നാളത്", "ഇന്ന്", "ഇന്നത്", "രാവിലെ", "ഉച്ച", "വൈകി",
                 "വൈകു", "വരെ", "മുതൽ", "പ്രദേശ", "ഭാഗങ്ങ", "സെക്ഷ", "സബ്", "സ്റ്റേഷ", "അറ്റകു", "പണി", "കാരണ", "അറിയി", "മണി",
                 "മലപ്പു", "ജില്ല", "ലൈൻ", "കെഎസ്", "പവർ", "കട്ട്", "power", "cut", "shut", "tomorr", "today", "areas", "mainte",
                 "substa", "malapp", "kseb", "from", "till", "will", "the")


def different_power_cut(a, b, other_filed=None, today=None):
    """two power-cut notices look alike ('നാളെ വൈദ്യുതി മുടങ്ങും ... 9 മുതൽ 2 വരെ'); they are the same news only when they name the
    same place and were filed within 3 days (a notice for another section must not be skipped as a 'duplicate' of an older one)"""
    a, b = norm_ml(a), norm_ml(b)
    if not (POWER.search(a or "") and POWER.search(b or "")):
        return False
    def places(t):
        return {w[:6] for w in re.findall(r"[\u0D00-\u0D7Fa-zA-Z]{4,}", t.lower()) if not w.startswith(_POWER_COMMON)}
    pa, pb = places(a), places(b)
    if pa and pb and not (pa & pb):
        return True
    d = pub_date(other_filed)
    today = today or datetime.datetime.now(IST).date()
    return bool(d and (today - d).days >= 3)


_GENERIC = ("മലപ്പു", "മഞ്ചേ", "ജില്ല", "malap", "manje", "സമീപ", "അടുത്ത്", "ഇന്ന്", "നാളെ", "ഇന്നലെ", "മരിച്ച", "മരണ",
            "തൊഴിലാ", "അറസ്റ്റ", "പിടിയി", "പ്രദേശ", "നടന്ന", "നൽകി", "വിതരണ")


def shares_words(a, b):
    """Malayalam headlines share many letters, so a letter match alone is weak (two different court stories from the same town
    look alike letter by letter). The same news also shares a third of its own words (place names and common words left out),
    or is almost letter-for-letter the same."""
    import difflib
    n = lambda t: norm_ml(t).lower()
    w = lambda t: {x[:4] for x in re.findall(r"[\u0D00-\u0D7Fa-z0-9]{3,}", n(t)) if not x.startswith(_GENERIC)}
    x, y = w(a), w(b)
    if x and y and len(x & y) / min(len(x), len(y)) >= 0.34:
        return True
    return difflib.SequenceMatcher(None, n(a), n(b)).ratio() >= 0.75


def similar(a, b, thr, other_filed=None, today=None):
    """True when headline a and b are the same news. A repeating-price topic (e.g. today's egg price) counts as the same
    only when the other story was filed the same day - tomorrow's price is a new post."""
    import difflib
    a, b = norm_ml(a), norm_ml(b)
    if (not a or not b or difflib.SequenceMatcher(None, a, b).ratio() <= thr or different_numbers(a, b)
            or different_power_cut(a, b, other_filed, today) or not shares_words(a, b)):
        return False
    if recurring(a) or recurring(b):
        today = today or datetime.datetime.now(IST).date()
        return pub_date(other_filed) == today
    return True


FOLLOW = re.compile(r"അറസ്റ്റ്|പിടിയിൽ|പിടികൂടി|ജയിൽ|റിമാൻഡ്|വിധി|ശിക്ഷ|രക്ഷപ്പെടുത്തി|രക്ഷിച്ചു|കണ്ടെടുത്തു|പിടിച്ചെടുത്തു|"
                    r"നഷ്ടപരിഹാരം|കുറ്റപത്രം|ജാമ്യം|കീഴടങ്ങി|മരിച്ചു|മരണം|"
                    r"arrest|held|nabbed|sentenc|verdict|convict|rescued|recovered|seized|compensation|bail|surrender|died|dead", re.I)


def follow_up(old, new, days=2):
    """('3 arrested for stealing laptops' must not be blocked as a duplicate of 'laptops stolen' 6 days earlier):
    a later report that brings a new development (arrest, verdict, rescue, seizure ...) about a story filed more than `days`
    days before is new news, not a duplicate"""
    o, n = pub_date(old.get("researched")), pub_date(new.get("researched"))
    if not o or not n or (n - o).days <= days:
        return False
    text = lambda r: norm_ml(r.get("headline_ml")) + " " + (r.get("headline_en") or "")
    return bool(FOLLOW.search(text(new))) and not FOLLOW.search(text(old))


# owner rule: a story that only says the article has no facts is NOT news and is never filed or posted.
# The writer sometimes "explains" a page it could not read (price in an image, wrong text scraped) instead of reporting news.
NO_NEWS_ML = ("ലേഖനത്തിൽ ഇല്ല", "ലേഖനത്തിൽ പറയുന്നില്ല", "ലേഖനത്തിൽ വ്യക്തമാക്കിയിട്ടില്ല", "ലേഖനത്തിൽ നൽകിയിട്ടില്ല", "ഈ ലേഖനത്തിൽ",
              "വാർത്തയിൽ പറയുന്നില്ല", "വിശദാംശങ്ങൾ ലഭ്യമല്ല", "വിവരങ്ങൾ ലഭ്യമല്ല", "വിവരം ലഭ്യമല്ല", "വിവരം അറിവായിട്ടില്ല",
              "വിവരങ്ങൾ അറിവായിട്ടില്ല", "കൂടുതൽ വിവരങ്ങൾ ലഭിക്കുമ്പോൾ", "വിവരം ലഭിക്കുന്ന മുറയ്ക്ക്", "ബന്ധപ്പെട്ടതല്ല", "ബന്ധമില്ലാത്ത")
NO_NEWS_EN = ("not in the article", "not mentioned in the article", "article does not", "article doesn't", "no details available",
              "details not available", "details are not available", "will be shared when", "not related to")


def _meta(sentence):
    low = sentence.lower()
    sentence = norm_ml(sentence)
    return [x for x in NO_NEWS_ML if x in sentence] + [x for x in NO_NEWS_EN if x in low]


def _sentences(text):
    import re as _re
    return [x.strip() for x in _re.split(r"(?<=[.!?\u0964])\s+|\n+", str(text or "")) if x.strip()]


def no_news(headline, reel_script="", caption=""):
    """'' = real news. Otherwise why the story is only about missing facts: the headline/hook says so, or at least
    40% of the reel script's news sentences (the follow line not counted) talk about details that are missing."""
    found = _meta(str(headline or ""))
    if found:
        return f"not news: the headline says the details are missing ({found[0]})"
    sents = [x for x in _sentences(reel_script) if "ഫോളോ ചെയ്യ" not in x and "കൂടുതൽ വാർത്തകൾക്ക്" not in norm_ml(x) and "follow" not in x.lower()]
    bad = [x for x in sents if _meta(x)]
    if sents and len(bad) / len(sents) >= 0.4:
        return f"not news: {len(bad)} of {len(sents)} sentences only say the article has no details"
    return ""


def strip_no_news(text):
    """remove the sentences/lines that only say a detail is missing from the article (the rest of a real story stays)"""
    import re as _re
    out = []
    for line in str(text or "").split("\n"):
        keep = [x for x in _re.split(r"(?<=[.!?\u0964])\s+", line) if not _meta(x)]
        if line.strip() and not "".join(keep).strip():
            continue
        out.append(" ".join(keep))
    return "\n".join(out)


# owner rule (an old wedding re-told in a new article): a story whose every dated fact is months old and that
# has no sign of anything happening now (today / yesterday / a weekday / "so far" / an arrest or verdict) is an old event.
RECENT_WORDS = ("ഇന്ന്", "ഇന്നത്തെ", "ഇന്നലെ", "മിനിഞ്ഞാന്ന്", "ഇന്ന് രാത്രി", "ഈ ആഴ്ച", "നാളെ", "ഇതുവരെ", "നിലവിൽ", "ഇപ്പോൾ",
                "ഇപ്പോഴും", "അടുത്തിടെ", "തിങ്കളാഴ്ച", "ചൊവ്വാഴ്ച", "ബുധനാഴ്ച", "വ്യാഴാഴ്ച", "വെള്ളിയാഴ്ച", "ശനിയാഴ്ച", "ഞായറാഴ്ച")


def old_event(text, today=None):
    t = norm_ml(text)
    today = today or datetime.datetime.now(IST).date()
    if any(w in t for w in RECENT_WORDS) or FOLLOW.search(t):
        return ""
    if any(abs((d - today).days) <= 7 for d in dates_in(t, today.year)):
        return ""
    mal = {**ML_ABB, **ML_FULL}
    mon = "|".join(sorted(mal, key=len, reverse=True))
    olds = []
    # '2025 ജൂലൈ 28' (Malayalam papers put the year first) and '28 ജൂലൈ 2025' / 'ജൂലൈ 2025'
    for m in re.finditer(r"(20\d\d)\s*(%s)\.?\s*(\d{1,2})?(?!\d)" % mon, t):
        try:
            olds.append(datetime.date(int(m.group(1)), mal[m.group(2)], int(m.group(3) or 1)))
        except (ValueError, KeyError):
            pass
    for m in re.finditer(r"(?<!\d)(\d{1,2})?\s*(%s)\.?\s*,?\s*(20\d\d)" % mon, t):
        try:
            olds.append(datetime.date(int(m.group(3)), mal[m.group(2)], int(m.group(1) or 1)))
        except (ValueError, KeyError):
            pass
    if olds and all((today - d).days >= 60 for d in olds):
        return f"old event: the story is about {max(olds):%d %b %Y}, nothing in it happened in the last days"
    return ""


# owner rule (the same bus fight / the same Collector order told by two papers): the same event reported by two outlets
# in different words. Compared on the DISTINCTIVE words of the two reel scripts (words that appear in few other stories: names,
# places, numbers), not on the headline wording.
def _event_stems(t):
    t = re.sub(r"കൂടുതൽ വാർത്തകൾക്ക്.*$", "", norm_ml(t))
    return {w[:5] for w in re.findall(r"[\u0D00-\u0D7F]{5,}", t)} | set(re.findall(r"\d{2,}", t))


def event_df(scripts):
    import collections
    df = collections.Counter()
    for s in scripts:
        df.update(_event_stems(s))
    return df, max(1, len(scripts))


def same_event(a, b, df_n):
    df, n = df_n
    rare = lambda t: {s for s in _event_stems(t) if df[s] <= max(2, n * 0.05)}
    x, y = rare(a), rare(b)
    if len(x) < 4 or len(y) < 4:
        return False
    shared = len(x & y)
    return shared >= 9 and shared / min(len(x), len(y)) >= 0.45
