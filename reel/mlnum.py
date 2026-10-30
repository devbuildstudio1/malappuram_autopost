"""Numbers -> Malayalam words for the voice ("56" -> "അമ്പത്തി ആറ്", not digit by digit).
Malayalam glues case endings to digits ("26ന്", "12-ാം", "5ഓടെ"); the ending is joined to the number word with the usual sandhi
("ഇരുപത്തി ആറിന്", "പന്ത്രണ്ടാം", "അഞ്ചോടെ")."""
import datetime
import re

ONES = ["", "ഒന്ന്", "രണ്ട്", "മൂന്ന്", "നാല്", "അഞ്ച്", "ആറ്", "ഏഴ്", "എട്ട്", "ഒമ്പത്"]
TEENS = {10: "പത്ത്", 11: "പതിനൊന്ന്", 12: "പന്ത്രണ്ട്", 13: "പതിമൂന്ന്", 14: "പതിനാല്", 15: "പതിനഞ്ച്", 16: "പതിനാറ്",
         17: "പതിനേഴ്", 18: "പതിനെട്ട്", 19: "പത്തൊമ്പത്"}
TENS = {2: "ഇരുപത്", 3: "മുപ്പത്", 4: "നാൽപത്", 5: "അമ്പത്", 6: "അറുപത്", 7: "എഴുപത്", 8: "എൺപത്", 9: "തൊണ്ണൂറ്"}
TENS_JOIN = {2: "ഇരുപത്തി", 3: "മുപ്പത്തി", 4: "നാൽപത്തി", 5: "അമ്പത്തി", 6: "അറുപത്തി", 7: "എഴുപത്തി", 8: "എൺപത്തി", 9: "തൊണ്ണൂറ്റി"}
HUND = {1: "നൂറ്", 2: "ഇരുനൂറ്", 3: "മുന്നൂറ്", 4: "നാനൂറ്", 5: "അഞ്ഞൂറ്", 6: "അറുനൂറ്", 7: "എഴുനൂറ്", 8: "എണ്ണൂറ്", 9: "തൊള്ളായിരം"}
HUND_JOIN = {1: "നൂറ്റി", 2: "ഇരുനൂറ്റി", 3: "മുന്നൂറ്റി", 4: "നാനൂറ്റി", 5: "അഞ്ഞൂറ്റി", 6: "അറുനൂറ്റി", 7: "എഴുനൂറ്റി", 8: "എണ്ണൂറ്റി", 9: "തൊള്ളായിരത്തി"}
ZERO = "പൂജ്യം"
VIRAMA = "്"      # ്
# independent vowel -> vowel sign (for joining an ending such as "ഓടെ" to a number word)
SIGN = {"അ": "", "ആ": "ാ", "ഇ": "ി", "ഈ": "ീ", "ഉ": "ു", "ഊ": "ൂ", "എ": "െ", "ഏ": "േ", "ഐ": "ൈ", "ഒ": "ൊ", "ഓ": "ോ", "ഔ": "ൌ"}
SIGNS = set("ാിീുൂൃെേൈൊോൌൗ")
ML = r"ഀ-ൿ"


def _below_100(n):
    if n < 10:
        return ONES[n]
    if n < 20:
        return TEENS[n]
    t, o = divmod(n, 10)
    return TENS[t] if o == 0 else TENS_JOIN[t] + " " + ONES[o]


def _below_1000(n):
    h, r = divmod(n, 100)
    if h == 0:
        return _below_100(r)
    if r == 0:
        return HUND[h]
    return HUND_JOIN[h] + " " + _below_100(r)


def _mult(w):
    """number before ലക്ഷം/കോടി: ഒന്ന് -> ഒരു"""
    return "ഒരു" if w == "ഒന്ന്" else w


_THOU_SPECIAL = {"മൂന്ന്": "മൂവായിരം", "അഞ്ച്": "അയ്യായിരം", "എട്ട്": "എണ്ണായിരം", "ഒമ്പത്": "ഒമ്പതിനായിരം", "പത്ത്": "പതിനായിരം"}


def _thousand(w):
    """രണ്ട് -> രണ്ടായിരം, മൂന്ന് -> മൂവായിരം, ഇരുപത് -> ഇരുപതിനായിരം (only the last word changes)"""
    head, _, last = w.rpartition(" ")
    if last in _THOU_SPECIAL:
        x = _THOU_SPECIAL[last]
    elif last.endswith("ത്ത്"):
        x = last[:-4] + "തിനായിരം"
    elif last.endswith("ത്"):
        x = last[:-2] + "തിനായിരം"
    elif last.endswith(VIRAMA):
        x = last[:-1] + "ായിരം"
    elif last.endswith("ം"):
        x = last[:-1] + "ത്തി ആയിരം"
    else:
        x = last + " ആയിരം"
    return (head + " " + x).strip()


def words(n):
    """0 .. 99,99,99,999"""
    if n == 0:
        return ZERO
    parts = []
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thou, n = divmod(n, 1000)
    if crore:
        parts.append(_mult(_below_1000(crore)) + " കോടി")
    if lakh:
        parts.append(_mult(_below_1000(lakh)) + (" ലക്ഷത്തി" if (thou or n) else " ലക്ഷം"))
    if thou:
        w = "ആയിരം" if thou == 1 else _thousand(_below_1000(thou))
        parts.append(w[:-1] + "ത്തി" if n else w)      # ആയിരം -> ആയിരത്തി when more follows
    if n:
        parts.append(_below_1000(n))
    return " ".join(p for p in parts if p).strip()


def join(w, suffix):
    """number word + glued ending: ആറ് + ന് -> ആറിന്, പന്ത്രണ്ട് + ാം -> പന്ത്രണ്ടാം, ആയിരം + ന് -> ആയിരത്തിന്"""
    if not suffix:
        return w
    if suffix[0] in SIGN:                       # independent vowel at the start of the ending
        suffix = SIGN[suffix[0]] + suffix[1:]
        if not suffix:
            return w
    starts_sign = suffix[0] in SIGNS
    if w.endswith(VIRAMA):
        return w[:-1] + suffix if starts_sign else w[:-1] + "ി" + suffix
    if w.endswith("ം"):
        if suffix.startswith("ത്ത"):              # writer already joined it: 1000ത്തിലധികം
            return w[:-1] + suffix
        return w[:-1] + "ത്ത" + suffix if starts_sign else w[:-1] + "ത്തി" + suffix
    if w[-1] in SIGNS or not starts_sign:       # കോടി + ന് -> കോടിക്ക് is idiomatic, but rare: keep it simple
        return w + ("യ" + suffix if starts_sign else suffix)
    return w + suffix


def half(n):
    """2.5 -> രണ്ടര, 10.5 -> പത്തര"""
    w = words(n)
    return w[:-1] + "ര" if w.endswith(VIRAMA) else w + " അര"


def _time(h, mm):
    h, mm = int(h), int(mm)
    if mm == 0:
        return words(h)
    if mm == 30:
        return half(h)
    return words(h) + " " + words(mm)


MONTHS = ["ജനുവരി", "ഫെബ്രുവരി", "മാർച്ച്", "ഏപ്രിൽ", "മേയ്", "ജൂൺ", "ജൂലൈ", "ഓഗസ്റ്റ്", "സെപ്റ്റംബർ", "ഒക്ടോബർ", "നവംബർ", "ഡിസംബർ"]
DAYPART = r"(രാവിലെ|വൈകിട്ട്|വൈകീട്ട്|വൈകുന്നേരം|രാത്രി|ഉച്ചയ്ക്ക്|ഉച്ചകഴിഞ്ഞ്|ഉച്ചയ്ക്കു|പുലർച്ചെ|അർധരാത്രി|ഉച്ചക്ക്)"
NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)(?:\s*-\s*(?=[" + ML + r"]))?([" + ML + r"]*)")
UNIT_WORDS = r"(?:ലക്ഷം|ആയിരം|കോടി)"


def _num_word(s):
    s = s.replace(",", "")
    if "." in s:
        a, b = s.split(".", 1)
        if b.rstrip("0") == "5":
            return half(int(a))
        if b.rstrip("0") == "":
            return words(int(a))
        return words(int(a)) + " പോയിന്റ് " + " ".join(ONES[int(c)] or ZERO for c in b)
    if len(s) > 9:
        return " ".join(ONES[int(c)] or ZERO for c in s)
    return words(int(s))


def speak_numbers(t):
    """replace every number in a Malayalam sentence by its Malayalam words (26ന് -> ഇരുപത്തി ആറിന്, 1,200 -> ആയിരത്തി ഇരുനൂറ്)"""
    t = re.sub(r"<[^>]+>", "", t)                       # stray html (<b>56</b>)

    # dates 26.10.2026 / 26/10/2026 / 26-10-2026 -> ഒക്ടോബർ 26-ാം തീയതി (2026)
    def _date(m):
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if not (1 <= d <= 31 and 1 <= mo <= 12):
            return m.group()
        y = ("20" + y) if len(y) == 2 else y
        year = "" if y == str(datetime.date.today().year) else f" {y}"      # the current year is not read out
        return f"{MONTHS[mo - 1]} {d}-ാം തീയതി{year} "
    t = re.sub(r"(?<![\d.])(\d{1,2})[./-](\d{1,2})[./-](\d{4}|\d{2})(?![\d.])\s*(?:തീയതി)?", _date, t)

    # times: രാവിലെ 10.30ന് / 4:30 മണിക്ക് -> പത്തര മണിക്ക് / നാലര മണിക്ക്
    def _t(h, mm, suf):
        w = _time(h, mm)
        if suf in ("ന്", "നു", "ന"):
            return w + " മണിക്ക്"
        return join(w, suf)
    t = re.sub(r"(?<![\d.])(\d{1,2})[.:](\d{2})(?=\s*(?:മണി|hrs))", lambda m: _time(m.group(1), m.group(2)), t)
    t = re.sub(DAYPART + r"\s*(\d{1,2})[.:](\d{2})(?![\d])\s*-?\s*([" + ML + r"]*)",
               lambda m: m.group(1) + " " + _t(m.group(2), m.group(3), m.group(4)), t)

    # money with paise: ₹5.70 -> 5 രൂപ 70 പൈസ
    def _paise(m):
        rs, ps = m.group(1), (m.group(2) + "0")[:2]
        return f"{rs} രൂപ" + ("" if int(ps) == 0 else f" {int(ps)} പൈസ")
    t = re.sub(r"(?:₹|Rs\.?|രൂ\.)\s*(\d[\d,]*)\.(\d{1,2})(?![\d])(?!\s*" + UNIT_WORDS + ")", _paise, t)
    # ranges: 10-12 -> 10 മുതൽ 12; a year range 2025-26 is read as two numbers
    t = re.sub(r"(?<![\d.])(\d{4})\s*[-–]\s*(\d{2})(?![\d])", r"\1 \2", t)
    t = re.sub(r"(?<![\d.])(\d[\d,]*)\s*[-–]\s*(\d[\d,]*)(?![\d.])", r"\1 മുതൽ \2", t)
    t = re.sub(r"(?:₹|Rs\.?|രൂ\.)\s*(\d[\d,]*(?:\.\d+)?)\s*(" + UNIT_WORDS + ")", r"\1 \2 രൂപ", t)      # ₹9 ലക്ഷം -> 9 ലക്ഷം രൂപ
    t = re.sub(r"(?:₹|Rs\.?|രൂ\.)\s*(\d[\d,]*(?:\.\d+)?)", r"\1 രൂപ", t)      # ₹11,600 -> 11,600 രൂപ
    t = t.replace("%", " ശതമാനം")

    t = NUM.sub(lambda m: join(_num_word(m.group(1)), m.group(2)) + ("" if m.group(2) else " "), t)
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    for s in ["56 തെങ്ങുകൾ", "₹11,600 പിടിച്ചെടുത്തു", "1,200 വോട്ടർമാർ", "12-ാം തീയതി 20ാം തീയതി", "2,600 ടൺ", "ഒക്ടോബർ 26ന്",
              "<b>200</b> പേർ", "24 ഏക്കർ", "45%", "3.5 കോടി", "105 പേർ", "2026", "₹1,25,000", "രാവിലെ 10.30ന്", "4:30 മണിക്ക്",
              "26.10.2026 തീയതി", "₹5.70", "10-12 ക്ലാസ്", "5ഓടെ", "1000ത്തിലധികം", "25,000", "₹9 ലക്ഷം", "2025-26"]:
        print(s, "->", speak_numbers(s))
