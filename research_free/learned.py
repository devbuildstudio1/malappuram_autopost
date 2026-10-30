"""What Instagram insights taught us (written by poster/insights.py into learned.json). Used ONLY to order candidate stories and to give the
writer style hints. It never relaxes a fact / quality check."""
import json, pathlib

HERE = pathlib.Path(__file__).parent
TOPICS = {
    "weather": ["മഴ", "വെയിൽ", "കാലാവസ്ഥ", "മുന്നറിയിപ്പ്", "അലർട്ട്", "വെള്ളപ്പൊക്ക", "ഉരുൾപൊട്ട", "കാറ്റ്", "അവധി"],
    "crime": ["കൊല", "അറസ്റ്റ്", "പിടിയിൽ", "മോഷ", "പോലീസ്", "കേസ്", "തട്ടിപ്പ്", "ആത്മഹത്യ", "കവർച്ച", "എംഡിഎംഎ", "കഞ്ചാവ്", "ഹവാല"],
    "accident": ["അപകട", "മരിച്ചു", "മരണം", "തീപിടിത്ത", "കൂട്ടിയിടിച്ച്", "മറിഞ്ഞ്", "ഇടിച്ച്", "പരിക്ക്", "മുങ്ങി"],
    "temple": ["ക്ഷേത്ര", "ഉത്സവ", "നേർച്ച", "പള്ളി", "പെരുന്നാൾ", "പൂജ", "ഉറൂസ്", "തിരുനാൾ"],
    "politics": ["മുഖ്യമന്ത്രി", "മന്ത്രി", "എംഎൽഎ", "എം.എൽ.എ", "തിരഞ്ഞെടുപ്പ്", "യുഡിഎഫ്", "എൽഡിഎഫ്", "ലീഗ്", "സിപിഎം", "കോൺഗ്രസ്", "ബിജെപി", "പാർട്ടി"],
    "poultry_agri": ["കൃഷി", "കർഷക", "വില", "വിപണി", "നെല്ല്", "തെങ്ങ്", "റബ്ബർ", "വാഴ", "മത്സ്യ", "കോഴി"],
    "education": ["വിദ്യാർഥി", "സ്കൂൾ", "കോളേജ്", "പരീക്ഷ", "സർവകലാശാല", "പ്ലസ് ടു", "എസ്എസ്എൽസി"],
    "civic": ["കുടിവെള്ള", "റോഡ്", "ബസ്", "നഗരസഭ", "പഞ്ചായത്ത്", "മാലിന്യ", "ദേശീയപാത", "ഗതാഗത", "പാലം"],
    "sports_culture": ["മത്സരം", "ഫുട്ബോൾ", "സെവൻസ്", "കായിക", "കലോത്സവ", "സിനിമ", "പുരസ്കാര"],
}


# power cuts and jobs are their own topics and win over any other topic word in the headline ('റോഡ്' in a power-cut notice is still a
# power cut); on the Namakkal pages they were the most watched news.
FIRST = {
    "power_cut": ["വൈദ്യുതി മുടങ്ങും", "വൈദ്യുതി മുടക്കം", "വൈദ്യുതി മുടങ്ങി", "വൈദ്യുതി തടസ്സ", "വൈദ്യുതി വിതരണം തടസ്സ", "പവർകട്ട്",
                  "ലോഡ് ഷെഡ്ഡിങ്", "power cut", "power outage", "power shutdown"],
    "jobs": ["തൊഴിൽ മേള", "ജോലി ഒഴിവ്", "ഒഴിവുകൾ", "ഒഴിവ്", "നിയമനം", "അഭിമുഖം", "റിക്രൂട്ട്", "job fair", "recruitment", "vacanc"],
}
# starting weight until insights has measured MIN_PER_TOPIC posts of the topic (then the measured weight is used)
PRIOR = {"power_cut": 1.0, "jobs": 1.0}


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
    """score adjustment for a candidate headline from its topic's measured performance (weights are already clamped by insights.py)"""
    t = topic(text)
    w = (load().get("topic_weight") or {}).get(t)
    return float(w) if w is not None else PRIOR.get(t, 0.0)


def hints():
    """short style guidance for the writer prompt; '' until enough posts have been measured"""
    d = load()
    out = []
    if d.get("avg_watch_s"):
        out.append(f"Viewers leave after about {d['avg_watch_s']} seconds on average: the FIRST sentence of reel_script must carry the most surprising fact (a number, place or consequence), never a greeting or background.")
    if d.get("top_openings"):
        out.append("Openings of our best-performing reels (style reference only, never copy facts): " + " | ".join(d["top_openings"][:4]))
    return "\n".join(out)
