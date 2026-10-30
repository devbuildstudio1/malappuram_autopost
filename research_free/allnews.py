"""Collect EVERY Malappuram-district news item from many outlets (the papers' Malappuram district pages + Google News + Bing News RSS,
any extra listing pages in sources.json), tag each one Manjeri ('R' = the town page) or rest-of-district ('N' = the district page), merge
duplicates reported by several outlets, and give the owner a full list to analyse. Nothing here writes posts; collect.py ranks and writes
the best ones. Every request is wrapped so one broken outlet never stops the others."""
import datetime, difflib, email.utils, html, json, re, time, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
import requests
import sources as district_list

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "ml-IN,ml;q=0.9,en;q=0.5"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
DISTRICT_KEY = "malappuram"      # the district as newspapers write it in their links (url_district)
ML = "\u0D00-\u0D7F"             # Malayalam letters

# ---------------------------------------------------------------- Malayalam spelling forms
# Many sites still type the old "chillu" letters as consonant + virama + ZWJ (ര + ് + ZWJ instead of ർ). Both spellings are made the same
# before any place word is matched.
_OLD_CHILLU = {"\u0D23\u0D4D\u200D": "\u0D7A", "\u0D28\u0D4D\u200D": "\u0D7B", "\u0D30\u0D4D\u200D": "\u0D7C", "\u0D32\u0D4D\u200D": "\u0D7D",
               "\u0D33\u0D4D\u200D": "\u0D7E", "\u0D15\u0D4D\u200D": "\u0D7F"}
_CHILLU_BASE = {"\u0D7A": "\u0D23", "\u0D7B": "\u0D28", "\u0D7C": "\u0D30", "\u0D7D": "\u0D32", "\u0D7E": "\u0D33", "\u0D7F": "\u0D15"}


def norm(text):
    """one spelling for the same Malayalam word: old chillu forms -> atomic chillu letters, no zero-width joiners"""
    t = text or ""
    for a, b in _OLD_CHILLU.items():
        t = t.replace(a, b)
    return re.sub("[\u200B\u200C\u200D\u2060\uFEFF\u00AD]", "", t)      # zero-width marks (Madhyamam puts one inside words)


def stem(w):
    """the part of a place name that stays the same before a Malayalam ending:
    മലപ്പുറം -> മലപ്പുറ (മലപ്പുറത്ത്, മലപ്പുറത്തെ), തിരൂർ -> തിരൂര (തിരൂരിൽ), കോട്ടക്കൽ -> കോട്ടക്കല (കോട്ടക്കലിൽ),
    അരീക്കോട് -> അരീക്കോട (അരീക്കോട്ട്), കോട്ടക്കുന്ന് -> കോട്ടക്കുന്ന (കോട്ടക്കുന്നിൽ). Names ending in a vowel stay whole
    (പെരിന്തൽമണ്ണ -> പെരിന്തൽമണ്ണയിൽ)."""
    w = norm(w)
    if len(w) <= 3 or w.isascii():
        return w
    if w[-1] in _CHILLU_BASE:
        return w[:-1] + _CHILLU_BASE[w[-1]]
    if w[-1] in ("ം", "്"):      # ം (anusvara) / ് (virama)
        return w[:-1]
    return w


# Manjeri town + the villages and panchayats around it -> posted on Manjeri 360 (Malappuram 360 invited as collaborator)
TOWN_AREA = ["മഞ്ചേരി", "പാണ്ടിക്കാട്", "എടവണ്ണ", "അരീക്കോട്", "കീഴുപറമ്പ്", "തൃക്കലങ്ങോട്", "ആനക്കയം", "പുൽപ്പറ്റ", "പയ്യനാട്",
             "നെല്ലിക്കുത്ത്", "കാവനൂർ", "ഏറനാട്", "എളങ്കൂർ", "ചെരണി", "ഊർങ്ങാട്ടിരി", "കുഴിമണ്ണ",
             "Manjeri", "Pandikkad", "Edavanna", "Areekode", "Eranad", "Ernad"]
# searches that cover the whole district (every taluk and big town)
QUERIES = ["മലപ്പുറം", "മഞ്ചേരി", "തിരൂർ", "പെരിന്തൽമണ്ണ", "പൊന്നാനി", "നിലമ്പൂർ", "കോട്ടക്കൽ", "കൊണ്ടോട്ടി", "തിരൂരങ്ങാടി",
           "വളാഞ്ചേരി", "താനൂർ", "പരപ്പനങ്ങാടി", "വേങ്ങര", "എടപ്പാൾ", "അരീക്കോട്", "വണ്ടൂർ", "കരിപ്പൂർ", "മലപ്പുറം ജില്ല",
           # KSEB / government notices: the papers carry the official notices every day
           "മലപ്പുറം വൈദ്യുതി മുടങ്ങും", "മഞ്ചേരി വൈദ്യുതി മുടങ്ങും", "തിരൂർ വൈദ്യുതി മുടങ്ങും", "പെരിന്തൽമണ്ണ വൈദ്യുതി മുടങ്ങും",
           "മലപ്പുറം കളക്ടർ", "മലപ്പുറം ജില്ലാ ഭരണകൂടം", "മലപ്പുറം തൊഴിൽ മേള", "മലപ്പുറം നിയമനം", "മലപ്പുറം അവധി",
           "Malappuram", "Manjeri", "Tirur", "Perinthalmanna", "Nilambur", "Ponnani", "Kondotty", "Malappuram collector",
           "Malappuram power outage"]
# every outlet is also searched on its own (so a channel like MediaOne or Twentyfour is never missed)
SITES = {"മാതൃഭൂമി": "mathrubhumi.com", "മനോരമ": "manoramaonline.com", "മാധ്യമം": "madhyamam.com", "ദേശാഭിമാനി": "deshabhimani.com",
         "കേരള കൗമുദി": "keralakaumudi.com", "സുപ്രഭാതം": "suprabhaatham.com", "ചന്ദ്രിക": "chandrikadaily.com", "സിറാജ്": "sirajlive.com",
         "ഏഷ്യാനെറ്റ് ന്യൂസ്": "asianetnews.com", "മീഡിയവൺ": "mediaoneonline.com", "ട്വന്റിഫോർ": "twentyfournews.com",
         "റിപ്പോർട്ടർ": "reporterlive.com", "ജനയുഗം": "janayugomonline.com", "സമകാലിക മലയാളം": "samakalikamalayalam.com",
         "ന്യൂസ്18 മലയാളം": "malayalam.news18.com", "സമയം മലയാളം": "malayalam.samayam.com", "വൺഇന്ത്യ മലയാളം": "malayalam.oneindia.com",
         "മംഗളം": "mangalam.com", "ദീപിക": "deepika.com", "കൈരളി": "kairalinewsonline.com",
         "The Hindu": "thehindu.com", "New Indian Express": "newindianexpress.com", "Times of India": "timesofindia.indiatimes.com",
         "Onmanorama": "onmanorama.com"}
SITE_QUERIES = ["മലപ്പുറം", "മഞ്ചേരി", "തിരൂർ", "Malappuram"]      # English for the English papers
OUTLET_WORDS = ["മാതൃഭൂമി", "മനോരമ", "മാധ്യമം", "ദേശാഭിമാനി", "കൗമുദി", "സുപ്രഭാതം", "ചന്ദ്രിക", "സിറാജ്", "ഏഷ്യാനെറ്റ്", "മീഡിയവൺ",
                "മീഡിയ വൺ", "ട്വന്റിഫോർ", "റിപ്പോർട്ടർ", "ജനയുഗം", "സമകാലിക മലയാളം", "ന്യൂസ്18", "ന്യൂസ് 18", "സമയം", "മംഗളം", "ദീപിക",
                "കൈരളി", "ദി ഹിന്ദു"]


def _get(url, timeout=40, headers=None):
    r = requests.get(url, headers=headers or UA, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r


# Malappuram district places (town / taluk / municipality / panchayat / well-known places). A story that names none of them AND names a
# state-wide or another district's place is not Malappuram district news (e.g. "rain alert in 9 districts", "Kozhikode yellow alert").
# Names shared with places in other districts (പള്ളിക്കൽ, കൊളത്തൂർ, പെരുമണ്ണ, കോട്ടപ്പടി, ഊരകം, കുറുവ ...) are left out on purpose.
DISTRICT_WORDS = ["മലപ്പുറം", "മഞ്ചേരി", "തിരൂർ", "പെരിന്തൽമണ്ണ", "പൊന്നാനി", "നിലമ്പൂർ", "കോട്ടക്കൽ", "വളാഞ്ചേരി", "താനൂർ",
                  "പരപ്പനങ്ങാടി", "തിരൂരങ്ങാടി", "കൊണ്ടോട്ടി", "കരിപ്പൂർ", "വേങ്ങര", "എടപ്പാൾ", "കുറ്റിപ്പുറം", "ചങ്ങരംകുളം", "മങ്കട",
                  "കാളികാവ്", "വഴിക്കടവ്", "എടക്കര", "വണ്ടൂർ", "അരീക്കോട്", "എടവണ്ണ", "പാണ്ടിക്കാട്", "കോട്ടക്കുന്ന്", "ചെമ്മാട്",
                  "കാടാമ്പുഴ", "തിരുനാവായ", "ഏറനാട്", "തേഞ്ഞിപ്പലം", "കാലിക്കറ്റ് സർവകലാശാല", "കീഴുപറമ്പ്", "തൃക്കലങ്ങോട്", "ആനക്കയം",
                  "പുൽപ്പറ്റ", "പയ്യനാട്", "നെല്ലിക്കുത്ത്", "കാവനൂർ", "കാരക്കുന്ന്", "കരുവാരക്കുണ്ട്", "മേലാറ്റൂർ", "പുലാമന്തോൾ",
                  "അങ്ങാടിപ്പുറം", "മക്കരപ്പറമ്പ്", "കൂട്ടിലങ്ങാടി", "കോഡൂർ", "പൂക്കോട്ടൂർ", "മൊറയൂർ", "ഒതുക്കുങ്ങൽ", "ഇരിമ്പിളിയം",
                  "ആതവനാട്", "തവനൂർ", "വട്ടംകുളം", "മാറഞ്ചേരി", "വെളിയങ്കോട്", "പെരുമ്പടപ്പ്", "പൂക്കോട്ടുംപാടം", "ചുങ്കത്തറ", "മമ്പാട്",
                  "കരുളായി", "മൂത്തേടം", "പോത്തുകല്ല്", "വള്ളിക്കുന്ന്", "ചേളാരി", "കൽപകഞ്ചേരി", "വളവന്നൂർ", "ആലത്തിയൂർ", "പുറത്തൂർ",
                  "കൂട്ടായി", "ഒഴൂർ", "നിറമരുതൂർ", "ചെറിയമുണ്ടം", "എടരിക്കോട്", "പറപ്പൂർ", "കണ്ണമംഗലം", "മൂന്നിയൂർ", "ചേലേമ്പ്ര",
                  "വാഴക്കാട്", "വാഴയൂർ", "ചീക്കോട്", "മുതുവല്ലൂർ", "പുളിക്കൽ", "ഊർങ്ങാട്ടിരി", "കുഴിമണ്ണ", "എടയൂർ", "മാറാക്കര", "പൊന്മള",
                  "അമരമ്പലം", "ചോക്കാട്", "തുവ്വൂർ", "തിരുവാലി", "എളങ്കൂർ", "ആലിപ്പറമ്പ്", "താഴേക്കോട്", "വെട്ടത്തൂർ", "കീഴാറ്റൂർ",
                  "ഏലംകുളം", "പാതായ്ക്കര", "പുഴക്കാട്ടിരി", "മൂർക്കനാട്", "ചെരണി", "ഉണ്യാൽ",
                  "Malappuram", "Manjeri", "Tirur", "Perinthalmanna", "Ponnani", "Nilambur", "Kottakkal", "Valanchery", "Tanur",
                  "Parappanangadi", "Tirurangadi", "Kondotty", "Karipur", "Vengara", "Edappal", "Kuttippuram", "Changaramkulam",
                  "Areekode", "Edavanna", "Wandoor", "Pandikkad", "Edakkara", "Vazhikkadavu", "Thenhipalam", "Calicut University",
                  "Calicut airport", "Eranad", "Ernad"]
OUTSIDE_WORDS = ["കേരളത്തിൽ", "സംസ്ഥാനത്ത്", "ജില്ലകളിൽ", "ജില്ലകൾക്ക്", "ജില്ലകളിലും", "കോഴിക്കോട്", "പാലക്കാട്", "തൃശൂർ", "വയനാട്",
                 "കണ്ണൂർ", "കാസർകോട്", "എറണാകുളം", "കൊച്ചി", "തിരുവനന്തപുരം", "കൊല്ലം", "ആലപ്പുഴ", "കോട്ടയം", "ഇടുക്കി", "പത്തനംതിട്ട",
                 "ഇന്ത്യ", "പ്രധാനമന്ത്രി", "മുഖ്യമന്ത്രി", "ഡൽഹി", "തമിഴ്നാട്", "കർണാടക", "ഗൾഫ്", "സൗദി", "യുഎഇ", "Kerala", "Kozhikode"]


# other districts and their towns (Malappuram's neighbours first): a headline that names one of these and no Malappuram place is not ours.
# "കോഴിക്കോട്" alone is listed, but Karipur airport ("കോഴിക്കോട് വിമാനത്താവളം") and Calicut University are Malappuram places
# (DISTRICT_WORDS), so a headline naming them is kept.
OTHER_PLACES = ["കോഴിക്കോട്", "ഫറോക്ക്", "രാമനാട്ടുകര", "മുക്കം", "കൊടുവള്ളി", "താമരശ്ശേരി", "വടകര", "കൊയിലാണ്ടി", "ബാലുശ്ശേരി",
                "പാലക്കാട്", "പട്ടാമ്പി", "ഷൊർണൂർ", "ഒറ്റപ്പാലം", "മണ്ണാർക്കാട്", "ചെർപ്പുളശ്ശേരി", "തൃത്താല", "കൂറ്റനാട്", "അട്ടപ്പാടി",
                "ആലത്തൂർ", "ചിറ്റൂർ", "തൃശൂർ", "ഗുരുവായൂർ", "കുന്നംകുളം", "ചാവക്കാട്", "ഇരിങ്ങാലക്കുട", "കൊടുങ്ങല്ലൂർ", "വയനാട്",
                "കൽപ്പറ്റ", "മാനന്തവാടി", "സുൽത്താൻ ബത്തേരി", "ഗൂഡല്ലൂർ", "നീലഗിരി", "ഊട്ടി", "കണ്ണൂർ", "തലശ്ശേരി", "കാസർകോട്",
                "എറണാകുളം", "കൊച്ചി", "ആലുവ", "ആലപ്പുഴ", "കോട്ടയം", "ഇടുക്കി", "പത്തനംതിട്ട", "ശബരിമല", "കൊല്ലം", "തിരുവനന്തപുരം",
                "ചെന്നൈ", "കോയമ്പത്തൂർ", "ബെംഗളൂരു", "മംഗളൂരു", "തമിഴ്നാട്", "കർണാടക", "ഡൽഹി", "മുംബൈ"]
STATE_WIDE = ["Kerala Rain", "Kerala rain", "കേരളം", "കേരളത്തിൽ", "സംസ്ഥാനത്ത്", "സംസ്ഥാനത്തെ", "ചുഴലിക്കാറ്റ്", "ന്യൂനമർദം", "ന്യൂനമർദ്ദം",
              "അറബിക്കടലിൽ", "ബംഗാൾ ഉൾക്കടലിൽ"]


def _forms(w):
    """a place name and the form it takes before a Malayalam ending: കോഴിക്കോട് -> കോഴിക്കോട്ട്, തൃശൂർ -> തൃശൂരിൽ, കേരളം -> കേരളത്തിൽ"""
    w = norm(w)
    out = [w]
    s = stem(w)
    if s != w:
        out.append(s)
    return out


OTHER_EN = ["kozhikode", "palakkad", "thrissur", "wayanad", "kannur", "kasaragod", "ernakulam", "kochi", "cochin", "alappuzha", "kottayam",
            "idukki", "pathanamthitta", "kollam", "thiruvananthapuram", "trivandrum", "nilgiris", "ooty", "gudalur", "coimbatore", "chennai",
            "bengaluru", "mangaluru", "shoranur", "pattambi", "guruvayur", "vadakara", "feroke"]

# district names as newspapers write them in their links
KERALA_DISTRICTS = {"malappuram", "kozhikode", "calicut", "palakkad", "thrissur", "wayanad", "kannur", "kasaragod", "kasargod", "ernakulam",
                    "kochi", "kottayam", "alappuzha", "idukki", "pathanamthitta", "kollam", "thiruvananthapuram", "trivandrum"}


def url_district(url):
    """the district a newspaper filed the article under, read from its link ('' when the link does not say)
    (mathrubhumi.com/malappuram/news/..., manoramaonline.com/district-news/malappuram/..., madhyamam.com/kerala/local-news/malappuram/...)"""
    u = (url or "").lower()
    for pat in (r"/district-news/([a-z]+)", r"/local-news/([a-z]+)", r"mathrubhumi\.com/([a-z]+)/news/", r"/local/([a-z]+)[-_/]",
                r"/districts?/([a-z]+)[-_/]", r"/news/district/([a-z]+)", r"/kerala/([a-z]+)/"):
        m = re.search(pat, u)
        if m and m.group(1) in KERALA_DISTRICTS:
            return m.group(1)
    return ""


NON_NEWS = ("weekly-supplements", "/cinema", "/movies", "/entertainment", "/lifestyle", "/recipe", "/food/", "/health/", "/technology", "/tech/",
            "/astrology", "/photogallery", "/videos/", "/video/", "/sports/", "/world/", "/national/", "/trending/", "/web-stories",
            "/gulf", "/pravasi", "/spirituality")


LISTING = re.compile(r"/(topic|topics|tag|tags|author|authors|search|category)/|/page-?\d+(/|$)|[?&]page=\d", re.I)


def is_listing(url):
    """a topic / tag / author / search page lists many stories from everywhere - it is not one news article"""
    return bool(LISTING.search(url or ""))


def local_ok(url, title):
    """the link and headline allow this to be Malappuram-district news: not filed under another district, not a supplement / cinema / recipe
    page, no other district or state-wide wording in the headline - unless the headline itself names a Malappuram-district place"""
    if is_listing(url):
        return False
    if other_district(title):
        return False
    if has_place(title):
        return True
    d = url_district(url)
    if d and d != DISTRICT_KEY:
        return False
    return not any(s in (url or "").lower() for s in NON_NEWS)


def other_district(title):
    """headline names another district / town / the whole state and no Malappuram-district place"""
    t = norm(title)
    low = t.lower()
    return not has_place(t) and (any(f in t for w in OTHER_PLACES for f in _forms(w)) or any(w in t for w in STATE_WIDE)
                                 or any(re.search(r"\b" + w + r"\b", low) for w in OTHER_EN))


# these headlines are never Malappuram-district news, even when Malappuram is one name in a long list
ALWAYS_OUTSIDE = ["ജില്ലകളിൽ", "ജില്ലകൾക്ക്", "ജില്ലകളിലും", "കേരളത്തിൽ", "സംസ്ഥാനത്തുടനീളം", "സംസ്ഥാന വ്യാപകമായി", "സംസ്ഥാനമൊട്ടാകെ",
                  "രാജ്യസഭ", "ലോക്സഭ", "പ്രധാനമന്ത്രി", "തിരഞ്ഞെടുപ്പ് കമ്മീഷൻ", "സുപ്രീം കോടതി",
                  # Gulf news about Malappuram natives / expat committees happens outside the district
                  "റിയാദ്", "ജിദ്ദ", "ദമ്മാം", "സൗദി", "ദുബായ്", "ദുബൈ", "അബുദാബി", "ഷാർജ", "ഖത്തർ", "കുവൈത്ത്", "ഒമാൻ", "ബഹ്റൈൻ"]
# weather forecasts / alerts are not local reporting (a Collector's holiday notice for the district IS local news and is not listed here)
WEATHER_FORECAST = ["മഴ മുന്നറിയിപ്പ്", "യെല്ലോ അലർട്ട്", "ഓറഞ്ച് അലർട്ട്", "റെഡ് അലർട്ട്", "മഞ്ഞ ജാഗ്രത", "ഓറഞ്ച് ജാഗ്രത", "ചുവപ്പ് ജാഗ്രത",
                    "കാലാവസ്ഥ", "മഴയ്ക്ക് സാധ്യത", "മഴ പെയ്യാൻ സാധ്യത", "ശക്തമായ മഴയ്ക്ക്", "കനത്ത മഴയ്ക്ക്", "ന്യൂനമർദ", "ചക്രവാതച്ചുഴി",
                    "ഇടിമിന്നലോടു കൂടിയ", "ചുഴലിക്കാറ്റ്"]


# places next to Manjeri: used for the Manjeri page only when Manjeri itself has less than a round's worth of news (env TOWN_NEAR=1)
TOWN_NEAR = ["വണ്ടൂർ", "കാരക്കുന്ന്", "മലപ്പുറം", "കൊണ്ടോട്ടി", "മങ്കട"]


# Malayalam joins a place name to its ending (മലപ്പുറം -> മലപ്പുറത്ത്, തിരൂർ -> തിരൂരിൽ), so match the stems too
PLACE_STEMS = sorted({f for w in DISTRICT_WORDS if not w.isascii() for f in _forms(w)} | {
    "മലപ്പുറത്ത", "കോട്ടക്കലി", "കോട്ടയ്ക്കൽ", "കോട്ടയ്ക്കല", "തിരൂരങ്ങാടിയി", "വേങ്ങരയി", "കാലിക്കറ്റ് സർവ്വകലാശാല",
    "കോഴിക്കോട് വിമാനത്താവള", "കരിപ്പൂര", "പെരിന്തൽമണ്ണ", "പെരിന്തല്മണ്ണ", "നിലമ്പൂര", "പൊന്നാനിയി"})


# no towns outside the district (the nearby-area lists stay empty)
NEAR_TOWN, NEAR_DISTRICT = [], []


def has_place(text):
    t = norm(text)
    low = t.lower()
    return (any(w in t for w in PLACE_STEMS) or any(w.lower() in low for w in DISTRICT_WORDS if w.isascii())
            or any(f in t for w in NEAR_TOWN + NEAR_DISTRICT for f in _forms(w)))


FOLLOW_SENTENCE = re.compile(r"(കൂടുതൽ വാർത്തകൾക്ക്|മേലും വാർത്തകൾക്ക്).*$")


def written_elsewhere(headline, script):
    """a written story whose headline names no Malappuram-district place and whose first two sentences name another district / town /
    the whole state is not Malappuram news"""
    if has_place(headline or ""):
        return ""
    body = FOLLOW_SENTENCE.sub("", norm(script))
    first2 = " ".join(re.split(r"(?<=[.!?])\s+", body.strip())[:2])
    if first2 and other_district(first2):
        return "not Malappuram district news (the story's first lines name another place and no Malappuram place)"
    return ""


def outside_district(text, via=""):
    """True when the headline is clearly NOT Malappuram-district news: state-wide / multi-district / national news, weather forecasts, or a
    headline that names another place and none of ours. A headline that names no place at all is KEPT (many local reports omit it) - the
    article itself is checked for a Malappuram place before anything is written (collect.py)."""
    text = norm(text)
    if any(w in text for w in ALWAYS_OUTSIDE) or any(w in text for w in WEATHER_FORECAST):
        return True
    if has_place(text):
        return False
    if via == "district-list":
        return False
    return any(w in text for w in OUTSIDE_WORDS)


def area_of(text, default="N"):
    """'R' (Manjeri 360) when the text names Manjeri or a place around it, else the default ('N' = Malappuram 360)"""
    t = norm(text)
    low = t.lower()
    return "R" if any(any(f in t for f in _forms(k)) if not k.isascii() else (k.lower() in low) for k in TOWN_AREA + NEAR_TOWN) else default


def area_of_story(title, lead):
    """Manjeri page when the HEADLINE names Manjeri or a place around it, or (headline names no place) the opening lines do.
    District-wide news ("മലപ്പുറം ജില്ലയിൽ ...") that only lists Manjeri among the towns stays on the Malappuram page."""
    if area_of(title or "") == "R":
        return "R"
    if "ജില്ല" in norm(title) or has_place(title or ""):
        return "N"
    return area_of((lead or "")[:250])


def _clean_title(t):
    t = html.unescape(t or "").strip()
    return re.sub(r"\s+[-|–]\s+[^-|–]{2,40}$", "", t).strip()      # drop the " - outlet" suffix of RSS titles


def _outlet(t, fallback=""):
    m = re.search(r"\s[-|–]\s+([^-|–]{2,40})$", html.unescape(t or ""))
    return (m.group(1).strip() if m else fallback) or fallback


def _parse_pub(s):
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(IST).isoformat()
    except Exception:
        return ""


def from_google(q):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:2d") + "&hl=ml&gl=IN&ceid=IN:ml"
    root = ET.fromstring(_get(url).content)
    out = []
    for it in root.iter("item"):
        title = it.findtext("title") or ""
        src = it.find("source")
        out.append({"key": it.findtext("guid") or it.findtext("link"), "url": it.findtext("link"), "title": _clean_title(title),
                    "source": (src.text if src is not None and src.text else _outlet(title, "Google News")), "published": _parse_pub(it.findtext("pubDate") or ""),
                    "via": "google", "query": q, "snippet": re.sub(r"<[^>]+>", " ", html.unescape(it.findtext("description") or ""))[:300]})
    return out


def from_bing(q):
    url = "https://www.bing.com/news/search?q=" + urllib.parse.quote(q) + "&format=rss&setmkt=en-IN&cc=IN&qft=sortbydate%3d%221%22"
    root = ET.fromstring(_get(url).content)
    out = []
    for it in root.iter("item"):
        link = it.findtext("link") or ""
        real = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url", [link])[0]
        title = it.findtext("title") or ""
        src = [e.text for e in it if e.tag.lower().endswith("source")]
        out.append({"key": real, "url": real, "title": _clean_title(title), "source": (src[0] if src else _outlet(title, "Bing News")),
                    "published": _parse_pub(it.findtext("pubDate") or ""), "via": "bing", "query": q,
                    "snippet": re.sub(r"<[^>]+>", " ", html.unescape(it.findtext("description") or ""))[:300]})
    return out


def from_district_list():
    """links from the papers' own Malappuram district pages (sources.py): trusted as district news"""
    out = []
    for u in district_list.candidate_links(60):
        name = next((n for n, page, _ in district_list.LIST_PAGES if urllib.parse.urlparse(page).netloc in u), "district list")
        out.append({"key": u, "url": u, "title": "", "source": name, "published": "", "via": "district-list", "query": "district list", "snippet": ""})
    return out


def from_listing(cfg):
    """extra outlet pages from sources.json: {"name","url","link_regex"} -> article links (the article page gives title/date/text)"""
    h = _get(cfg["url"]).text
    base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(cfg["url"]))
    seen, out = set(), []
    for m in re.finditer(cfg.get("link_regex", r'href="([^"#?]+/\d{5,}[^"]*)"'), h):
        u = urllib.parse.urljoin(base, m.group(1))
        if u not in seen:
            seen.add(u)
            out.append({"key": u, "url": u, "title": "", "source": cfg["name"], "published": "", "via": "listing", "query": cfg["url"], "snippet": ""})
    return out[: cfg.get("limit", 30)]


def collect(log):
    """every item from every source, merged. Returns a list of dicts (see keys above + area, mentions, outlets)."""
    items = []

    def add(fn, *a, label=""):
        try:
            got = fn(*a)
            log.append(f"source {label or fn.__name__}: {len(got)} items")
            items.extend(got)
        except Exception as e:
            log.append(f"source {label or fn.__name__} FAILED: {str(e)[:120]}")
    add(from_district_list, label="district list")
    for q in QUERIES:
        add(from_google, q, label=f"google '{q}'")
        add(from_bing, q, label=f"bing '{q}'")
    for name, dom in SITES.items():
        for q in SITE_QUERIES:
            add(from_google, f"{q} site:{dom}", label=f"google {name} '{q}'")
            add(from_bing, f"{q} site:{dom}", label=f"bing {name} '{q}'")
    try:
        for cfg in json.loads((HERE / "sources.json").read_text(encoding="utf-8")):
            add(from_listing, cfg, label=cfg["name"])
    except FileNotFoundError:
        pass
    # merge: same URL or very similar headline = one story reported by several outlets
    merged = []
    for it in items:
        if not it.get("key"):
            continue
        hit = None
        for m in merged:
            if m["key"] == it["key"] or m["url"] == it["url"]:
                hit = m
                break
            if it["title"] and m["title"] and difflib.SequenceMatcher(None, it["title"], m["title"]).ratio() > 0.62:
                hit = m
                break
        if hit:
            hit["outlets"].add(it["source"])
            hit["alts"].append(it["url"])
            if not hit["title"] and it["title"]:
                hit["title"] = it["title"]
            if not hit["published"] and it["published"]:
                hit["published"] = it["published"]
            if len(it.get("snippet", "")) > len(hit.get("snippet", "")):
                hit["snippet"] = it["snippet"]
            if it["via"] == "district-list" or (it["via"] == "bing" and hit["via"] == "google"):
                hit["url"] = it["url"]          # prefer a direct publisher link
                hit["via"] = it["via"]
        else:
            it = dict(it)
            it["outlets"] = {it["source"]}
            it["alts"] = [it["url"]]
            merged.append(it)
    for m in merged:
        m["mentions"] = len(m["outlets"])
        m["area"] = area_of(m["title"] + " " + m.get("snippet", ""))
        m["outlets"] = sorted(m["outlets"])
    log.append(f"all sources: {len(items)} items -> {len(merged)} different news ({sum(1 for m in merged if m['area'] == 'R')} Manjeri)")
    return merged


# ---------------------------------------------------------------- article text
def resolve(url):
    """Google News links are redirects; turn one into the publisher's page (needs the googlenewsdecoder package)."""
    if "news.google.com" not in url:
        return url
    err = ""
    for attempt in range(3):      # the decoder is rate-limited when many links come at once: pause and try again
        try:
            from googlenewsdecoder import gnewsdecoder
            r = gnewsdecoder(url, interval=2)
            if (r.get("success") or r.get("status")) and r.get("decoded_url"):      # 0.2.x answers "success", older versions "status"
                return r["decoded_url"]
            err = str(r.get("message") or "no decoded url")[:80]
        except Exception as e:
            err = f"decoder: {str(e)[:70]}"
        time.sleep(6 * (attempt + 1))
    try:
        final = _get(url, timeout=30).url
        if "news.google.com" not in final:
            return final
        raise RuntimeError("google page, not the article")
    except Exception as e:
        raise RuntimeError(f"google news link not decoded ({err}; {str(e)[:60]})")


# lines that start the page footer (comment policy, "read also" lists) - nothing after them belongs to the article
BOILERPLATE = ("അഭിപ്രായങ്ങൾ വായനക്കാരുടേത", "മംഗ്ലീഷ് ഒഴിവാക്കുക", "അഭിപ്രായം രേഖപ്പെടുത്തുന്നവർ", "ഇതുകൂടി വായിക്കാം", "കൂടുതൽ വായിക്കാം",
               "ഇവിടെ ക്ലിക്ക് ചെയ്യുക", "Also Read", "Disclaimer", "ഡൗൺലോഡ് ചെയ്യൂ", "ഫോളോ ചെയ്യൂ")


def article_any(url):
    """title / published / text from any outlet's article page (JSON-LD first, then page paragraphs)."""
    h = _get(url, timeout=40).text
    title = pub = body = ""
    for blk in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', h, flags=re.S):
        try:
            data = json.loads(blk)
        except Exception:
            continue
        for d in (data if isinstance(data, list) else [data]):
            for e in (d.get("@graph", [d]) if isinstance(d, dict) else []):
                if isinstance(e, dict) and "Article" in str(e.get("@type", "")):
                    title = title or e.get("headline", "")
                    pub = pub or e.get("datePublished", "")
                    body = body or e.get("articleBody", "")
    if not title:
        m = re.search(r'property="og:title"\s+content="([^"]+)"', h) or re.search(r"<title>([^<]+)</title>", h)
        title = html.unescape(m.group(1)).strip() if m else ""
    if not pub:
        m = re.search(r'property="article:published_time"\s+content="([^"]+)"', h)
        pub = m.group(1) if m else ""
    if len(body) < 200:
        h2 = re.sub(r"<(style|script|noscript|svg)[^>]*>.*?</\1>", " ", h, flags=re.S)
        paras = [re.sub(r"\s+", " ", html.unescape(x)).strip() for x in re.sub(r"<[^>]+>", "\n", h2).split("\n")]
        paras = [x for x in paras if len(x) > 60 and re.search(r"[\u0D00-\u0D7F]", x) and "{" not in x and "css-" not in x]
        seen, out = set(), []
        for x in paras:
            if any(b in norm(x) for b in BOILERPLATE):
                break      # the comment policy / "read also" block ends the article; the lines after it are other stories
            if x not in seen:
                seen.add(x)
                out.append(x)
        body = "\n".join(out)
    return {"url": url, "title": norm(html.unescape(title)).strip(), "published": pub, "text": norm(html.unescape(body)).strip()}
