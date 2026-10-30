"""Full place names and spoken forms. News sites use abbreviations (കെ.എസ്.ഇ.ബി., എസ്.ഐ., കി.മീ.) and English short forms (KSRTC,
MLA): a voice engine reads those badly or skips Latin letters. Everything we publish keeps the full place name; the reel voice also gets
spoken words for roles, units and abbreviations."""
import re

ML = "\u0D00-\u0D7F"

# (pattern, full name). The ending (-ിൽ, -ൽ, -ലെ ...) after the matched name is kept.
# Malayalam papers rarely shorten place names; only spellings that differ between papers are made the same here.
PLACES = [
    (r"കോട്ടയ്ക്കൽ", "കോട്ടക്കൽ"),
    (r"കോട്ടയ്ക്കല(?=[\u0D3E-\u0D4C\u0D4D])", "കോട്ടക്കല"),
    (r"പെരിന്തല്മണ്ണ", "പെരിന്തൽമണ്ണ"),
]

# only for the spoken reel script (the screen text may keep the short, well-known forms)
D = r"\s?\.\s?"      # the dot between the letters of a Malayalam abbreviation (എസ്.ഐ. / എസ് . ഐ)
NB = r"(?<![A-Za-z])"
NA = r"(?![A-Za-z])"
ROLES = [
    # longest first: എ.എസ്.ഐ. must not become എ.+എസ്.ഐ.
    (r"ഡിവൈ" + D + r"എസ്" + D + r"പി(?:\s?\.)?,?|" + NB + r"DYSP" + NA + "|" + NB + r"DySP" + NA, "ഡെപ്യൂട്ടി പോലീസ് സൂപ്രണ്ട്"),
    (r"(?<![" + ML + r".])എ" + D + r"എസ്" + D + r"ഐ(?:\s?\.)?,?|" + NB + r"ASI" + NA, "അസിസ്റ്റന്റ് സബ് ഇൻസ്പെക്ടർ"),
    (r"(?<![" + ML + r".])എസ്" + D + r"ഐ(?:\s?\.)?,?(?!\s?[" + ML + r"]{1,3}\s?\.)|" + NB + r"SI" + NA, "സബ് ഇൻസ്പെക്ടർ"),
    (r"(?<![" + ML + r".])സി" + D + r"ഐ(?:\s?\.)?,?(?!\s?[" + ML + r"]{1,3}\s?\.)|" + NB + r"CI" + NA, "സർക്കിൾ ഇൻസ്പെക്ടർ"),
    (r"എസ്" + D + r"എച്ച്" + D + r"ഒ(?:\s?\.)?,?|" + NB + r"SHO" + NA, "സ്റ്റേഷൻ ഹൗസ് ഓഫീസർ"),
    (NB + r"SP" + NA, "പോലീസ് സൂപ്രണ്ട്"),
    (r"(?<![" + ML + r".])എസ്" + D + r"പി(?:\s?\.)?,?(?!\s?[" + ML + r"]{1,3}\s?\.)", "പോലീസ് സൂപ്രണ്ട്"),
    (r"കെ" + D + r"എസ്" + D + r"ഇ" + D + r"ബി(?:\s?\.)?|" + NB + r"KSEB" + NA, "കെ എസ് ഇ ബി"),
    (r"കെ" + D + r"എസ്" + D + r"ആർ" + D + r"ടി" + D + r"സി(?:\s?\.)?|" + NB + r"KSRTC" + NA, "കെ എസ് ആർ ടി സി"),
    (r"എം" + D + r"എൽ" + D + r"എ(?:\s?\.)?|" + NB + r"MLA" + NA, "എം എൽ എ"),
    (NB + r"MP" + NA, "എം പി"),
    (NB + r"RDO" + NA, "ആർ ഡി ഒ"),
    (NB + r"DMO" + NA, "ജില്ലാ മെഡിക്കൽ ഓഫീസർ"),
    (NB + r"PWD" + NA, "പൊതുമരാമത്ത് വകുപ്പ്"),
    (NB + r"KWA" + NA, "ജല അതോറിറ്റി"),
    (NB + r"NH" + NA, "ദേശീയപാത"),
    (NB + r"NEET" + NA, "നീറ്റ്"),
    (NB + r"COVID" + NA, "കോവിഡ്"),
    (NB + r"PSC" + NA, "പി എസ് സി"),
    (NB + r"No\.\s?", "നമ്പർ "),
    (r"മി" + D + r"മീ(?:\s?\.)?,?", "മില്ലിമീറ്റർ"),
    (r"സെ" + D + r"മീ(?:\s?\.)?,?", "സെന്റിമീറ്റർ"),
    (r"കി" + D + r"മീ(?:\s?\.)?,?", "കിലോമീറ്റർ"),
    (r"കി" + D + r"ഗ്രാം(?:\s?\.)?,?|കി" + D + r"ഗ്രാ\s?\.", "കിലോഗ്രാം"),
    (r"(?<![" + ML + r"])ഡോ\s?\.\s?", "ഡോക്ടർ "),
    (r"(?<![" + ML + r"])ഒക്ടോ\s?\.", "ഒക്ടോബർ"),
    (r"(?<![" + ML + r"])നവം\s?\.", "നവംബർ"),
    (r"(?<![" + ML + r"])ഡിസം\s?\.", "ഡിസംബർ"),
    (r"(?<![" + ML + r"])ജനു\s?\.", "ജനുവരി"),
    (r"(?<![" + ML + r"])ഫെബ്രു\s?\.", "ഫെബ്രുവരി"),
    (r"(?<![" + ML + r"])സെപ്റ്റം\s?\.", "സെപ്റ്റംബർ"),
    (r"(?<![" + ML + r"])ആഗ\s?\.", "ആഗസ്റ്റ്"),
]


def _norm(text):
    """old chillu spellings and zero-width marks -> one spelling (same rule as the collector)"""
    try:
        import allnews
        return allnews.norm(text)
    except Exception:
        return text or ""


def full_places(text):
    text = _norm(text)
    for pat, full in PLACES:
        text = re.sub(pat, full, text or "")
    return ages(text)


MONTH_WORDS = ("ജനുവരി", "ഫെബ്രുവരി", "മാർച്ച്", "ഏപ്രിൽ", "മേയ്", "ജൂൺ", "ജൂലൈ", "ആഗസ്റ്റ്", "ഓഗസ്റ്റ്", "സെപ്റ്റംബർ", "ഒക്ടോബർ", "നവംബർ", "ഡിസംബർ")


def ages(text):
    """newspaper shorthand ages ('രാജു (47)' / 'രാജു, 47,') are said with the word വയസ്സ് - 'രാജു (47 വയസ്സ്)' - so a viewer hears
    it is an age, not a bare number"""
    W = r"(?<![" + ML + r"])([" + ML + r"]+)"
    keep = lambda f: lambda m: m.group(0) if m.group(1) in MONTH_WORDS else f(m)
    text = re.sub(W + r",\s?(\d{1,2}),(?!\s*\d)", keep(lambda m: f"{m.group(1)} ({m.group(2)} വയസ്സ്),"), text or "")
    return re.sub(W + r"\s?\((\d{1,2})\)", keep(lambda m: f"{m.group(1)} ({m.group(2)} വയസ്സ്)"), text)


# English letters as a Malayalam news reader says them (the voice model drops Latin letters completely)
LATIN = {"A": "എ", "B": "ബി", "C": "സി", "D": "ഡി", "E": "ഇ", "F": "എഫ്", "G": "ജി", "H": "എച്ച്", "I": "ഐ", "J": "ജെ", "K": "കെ", "L": "എൽ",
         "M": "എം", "N": "എൻ", "O": "ഒ", "P": "പി", "Q": "ക്യു", "R": "ആർ", "S": "എസ്", "T": "ടി", "U": "യു", "V": "വി", "W": "ഡബ്ല്യു",
         "X": "എക്സ്", "Y": "വൈ", "Z": "ഇസഡ്"}

# one spoken letter of a dotted abbreviation: എസ്, എം, എൽ, ഐ, കെ, ബി, ആർ, ടി, സി ...
L = r"[\u0D05-\u0D39](?:[\u0D3E-\u0D4C\u0D02]|[\u0D7A-\u0D7F]|[\u0D15-\u0D39]\u0D4D){0,2}"


def spoken(text):
    text = full_places(text)
    for pat, full in ROLES:
        text = re.sub(pat, full, text)
    # any other abbreviation is read letter by letter: UDF -> യു ഡി എഫ്, പി.കെ. -> പി കെ, എം.ഡി.എം.എ. -> എം ഡി എം എ
    text = re.sub(r"(?<![A-Za-z])[A-Z]{2,7}(?![A-Za-z])", lambda m: " ".join(LATIN[c] for c in m.group()), text)
    # letters joined by dots with no space between ('പി.കെ.', 'എം.ഡി.എം.എ'); two letters need the closing dot, so a sentence end
    # followed by a short word ('ഇത്. ഒരു') is never joined
    text = re.sub(r"(?<![" + ML + r".])((?:" + L + r"\.){2,}" + L + r"|(?:" + L + r"\.)+" + L + r"(?=\.))\.?",
                  lambda m: " ".join(x.strip() for x in m.group(1).split(".") if x.strip()), text)
    return re.sub(r"[ \t]{2,}", " ", text)
