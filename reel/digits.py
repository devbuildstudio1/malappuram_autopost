"""Display-only helper: the voice needs numbers written as Malayalam words, but the on-screen text should show digits
(10 മണി, not പത്ത് മണി) and 360 (not ത്രീ സിക്സ്റ്റി). Never used for the spoken text."""
import re

UNITS = {"ഒന്ന്": 1, "ഒന്നാം": 1, "രണ്ട്": 2, "രണ്ടു": 2, "രണ്ടാം": 2, "മൂന്ന്": 3, "മൂന്നു": 3, "മൂന്നാം": 3,
         "നാല്": 4, "നാലു": 4, "നാലാം": 4, "അഞ്ച്": 5, "അഞ്ചു": 5, "അഞ്ചാം": 5, "ആറ്": 6, "ആറു": 6, "ആറാം": 6, "ഏഴ്": 7, "ഏഴു": 7, "ഏഴാം": 7,
         "എട്ട്": 8, "എട്ടു": 8, "എട്ടാം": 8, "ഒമ്പത്": 9, "ഒൻപത്": 9, "ഒമ്പതാം": 9}
TENS_PREFIX = {"ഇരുപത്തി": 20, "ഇരുപത്തിയൊന്ന്": None, "മുപ്പത്തി": 30, "നാൽപത്തി": 40, "നാല്പത്തി": 40, "അമ്പത്തി": 50, "അൻപത്തി": 50,
               "അറുപത്തി": 60, "എഴുപത്തി": 70, "എൺപത്തി": 80, "തൊണ്ണൂറ്റി": 90}
TENS_PREFIX = {k: v for k, v in TENS_PREFIX.items() if v}
SINGLE = {"പത്ത്": 10, "പതിനൊന്ന്": 11, "പന്ത്രണ്ട്": 12, "പതിമൂന്ന്": 13, "പതിനാല്": 14, "പതിനഞ്ച്": 15,
          "പതിനാറ്": 16, "പതിനേഴ്": 17, "പതിനെട്ട്": 18, "പത്തൊമ്പത്": 19, "ഇരുപത്": 20, "മുപ്പത്": 30, "നാൽപത്": 40, "അമ്പത്": 50,
          "അറുപത്": 60, "എഴുപത്": 70, "എൺപത്": 80, "തൊണ്ണൂറ്": 90, "നൂറ്": 100, "പത്താം": 10, "പതിനൊന്നാം": 11, "പന്ത്രണ്ടാം": 12,
          "പതിമൂന്നാം": 13, "പതിനാലാം": 14, "പതിനഞ്ചാം": 15, "പതിനാറാം": 16, "പതിനേഴാം": 17, "പതിനെട്ടാം": 18, "പത്തൊമ്പതാം": 19,
          "ഇരുപതാം": 20, "മുപ്പതാം": 30, "നാൽപതാം": 40}
UNIT_SKIP = {"ഒരു"}


def _ord(w):
    return "-ാം" if w.endswith("ാം") else ""


def to_digits(text):
    text = re.sub(r"ത്രീ\s+സിക്സ്റ്റി", "360", text)
    words = text.split(" ")
    out, i = [], 0
    while i < len(words):
        w = words[i]
        core = w.rstrip(".,!?:;")
        tail = w[len(core):]
        if core in TENS_PREFIX:
            n = TENS_PREFIX[core]
            nxt = words[i + 1].rstrip(".,!?:;") if i + 1 < len(words) else ""
            if nxt in UNITS:
                tail2 = words[i + 1][len(nxt):]
                out.append(str(n + UNITS[nxt]) + _ord(nxt) + tail2)
                i += 2
                continue
            out.append(str(n) + tail)
        elif core in SINGLE:
            out.append(str(SINGLE[core]) + _ord(core) + tail)
        elif core in UNITS and core not in UNIT_SKIP and core not in ("ഒന്ന്",):
            out.append(str(UNITS[core]) + _ord(core) + tail)
        else:
            out.append(w)
        i += 1
    return " ".join(out)


if __name__ == "__main__":
    for t in ["രാവിലെ പത്ത് മണി മുതൽ വൈകിട്ട് അഞ്ച് മണി വരെ", "ഒക്ടോബർ ഇരുപത്തി ഒന്നാം തീയതി", "മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ്", "ഒരു മണിക്കൂർ", "ഏഴ് പേർക്ക് പരിക്ക്."]:
        print(to_digits(t))
