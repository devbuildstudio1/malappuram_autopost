"""Regression tests built from real cases the pipeline got wrong. Run before every push:

    python3 -m unittest discover -s tests -v

The cases were first found on the Namakkal (Tamil) pages and are kept here as Malappuram / Malayalam equivalents that run the
same code paths; each test says which old problem it guards against, so a failure says which problem has come back."""
import ast, datetime, json, os, re, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for d in ("poster", "research_free", "reel"):
    sys.path.insert(0, str(ROOT / d))

import freshness as fr          # noqa: E402
import allnews                  # noqa: E402
import collect                  # noqa: E402
import post                     # noqa: E402

IST = fr.IST
TODAY = datetime.datetime.now(IST).date()
LAST = "കൂടുതൽ വാർത്തകൾക്ക് മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ."


def from_file(path, names, extra=None):
    """load only some top-level functions/assignments of a file (reel4.py needs a browser library to import as a whole)"""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    body = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names)
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in names)]
    ns = {"os": os, "sys": sys, "json": json, "re": re, "Path": Path, "__file__": str(path), "html": __import__("html")}
    ns.update(extra or {})
    exec(compile(ast.Module(body, []), str(path), "exec"), ns)
    return ns


def example(i):
    return dict(json.loads((ROOT / "research_free" / "examples.json").read_text(encoding="utf-8"))[i]["output"])


class DuplicateCheck(unittest.TestCase):
    def test_prisoner_is_not_the_rss_march(self):      # an escaped-prisoner story was skipped as a 'duplicate' of a march
        self.assertFalse(fr.similar("മലപ്പുറത്ത് കോടതി ഉത്തരവ് പ്രകാരം ആർഎസ്എസ് പഥസഞ്ചലനം",
                                    "മലപ്പുറം കോടതിയിൽ നിന്ന് രക്ഷപ്പെട്ട പ്രതി പിടിയിൽ", 0.55))

    def test_bus_death_is_not_roof_fall(self):
        self.assertFalse(fr.similar("വേങ്ങരയിൽ സ്വകാര്യ ബസ് ഇടിച്ച് തൊഴിലാളി മരിച്ചു",
                                    "വീടിന്റെ മേൽക്കൂരയിൽ നിന്ന് വീണ് തൊഴിലാളി മരിച്ചു", 0.55))

    def test_same_news_other_words_still_duplicate(self):
        self.assertTrue(fr.similar("100 വർഷം പഴക്കമുള്ള പുളിമരം റോഡിന് കുറുകെ വീണു",
                                   "മങ്കടയിൽ 100 വർഷം പഴക്കമുള്ള പുളിമരം റോഡിലേക്ക് വീണു", 0.55))
        self.assertTrue(fr.similar("മലപ്പുറത്ത് കോടതി ഉത്തരവ് പ്രകാരം ആർഎസ്എസ് പഥസഞ്ചലനം",
                                   "മലപ്പുറത്ത് ആര്‍എസ്എസ് പഥസഞ്ചലനം", 0.55))      # old chillu form ര്+ZWJ = ർ

    def test_different_numbers_are_different_events(self):
        self.assertTrue(fr.different_numbers("ചീട്ടുകളി: 8 പേർ അറസ്റ്റിൽ", "ചീട്ടുകളി: 6 പേർ അറസ്റ്റിൽ"))

    def test_power_cut_other_place_not_duplicate(self):      # a power cut for another section was skipped as a 'duplicate'
        a = "കോട്ടക്കൽ സബ്സ്റ്റേഷനിൽ അറ്റകുറ്റപ്പണി: നാളെ രാവിലെ 9 മുതൽ ഉച്ചയ്ക്ക് 2 വരെ വൈദ്യുതി മുടങ്ങും"
        b = "വളാഞ്ചേരി സബ്സ്റ്റേഷനിൽ അറ്റകുറ്റപ്പണി: നാളെ രാവിലെ 9 മുതൽ ഉച്ചയ്ക്ക് 2 വരെ വൈദ്യുതി മുടങ്ങും"
        self.assertFalse(fr.similar(b, a, 0.62, f"{TODAY:%d %b %Y}, 02:00"))
        self.assertTrue(fr.similar(a, a, 0.62, f"{TODAY:%d %b %Y}, 02:00"))
        old = TODAY - datetime.timedelta(days=15)
        self.assertFalse(fr.similar(a, a, 0.62, f"{old:%d %b %Y}, 10:00"))      # same substation, an older notice

    def test_writer_same_news(self):
        self.assertTrue(collect.same_news("മഴയിൽ മലപ്പുറം കളക്ടറുടെ വസതിയുടെ മതിൽ ഇടിഞ്ഞു",
                                          "കനത്ത മഴ: മലപ്പുറം കളക്ടറുടെ ബംഗ്ലാവിന്റെ മതിൽ തകർന്നു"))

    def test_writer_other_news_not_duplicate(self):      # three new stories were skipped as 'similar to a filed story'
        now = f"{TODAY:%d %b %Y}, 06:00"
        old = f"{TODAY - datetime.timedelta(days=6):%d %b %Y}, 06:00"
        self.assertFalse(collect.same_news("മലപ്പുറത്ത് മരച്ചീനി കർഷകരുടെ പ്രശ്നം: ഒക്ടോബർ 30ന് ത്രികക്ഷി യോഗം",
                                           "30ന് കർഷക പരാതി പരിഹാര യോഗം", now))      # two shared words only
        self.assertFalse(collect.same_news("🗑️ മാലിന്യം നിറഞ്ഞ മഴവെള്ളം കെട്ടിക്കിടക്കുന്നു – ആരോഗ്യ ഭീഷണി",
                                           "സർവീസ് റോഡിൽ കൂട്ടിയിട്ട മാലിന്യം ആരോഗ്യ ഭീഷണി", old))      # days older
        self.assertTrue(collect.same_news("കളക്ടറേറ്റിൽ വയോധികൻ ആത്മഹത്യക്ക് ശ്രമിച്ചു: ഭൂമി തർക്കം",
                                          "വയോധികൻ ആത്മഹത്യക്ക് ശ്രമിച്ചു കളക്ടറേറ്റിൽ സംഘർഷം", now))      # real repeat


class LearnedPriority(unittest.TestCase):
    """power cuts and jobs (the most watched news) were scored -0.5 as 'civic' / 'education_jobs'"""

    def test_power_cut_and_jobs_have_own_topic(self):
        import learned
        self.assertEqual("power_cut", learned.topic("നാളെ കോട്ടക്കൽ ഉൾപ്പെടെ 9 പ്രദേശങ്ങളിൽ വൈദ്യുതി മുടങ്ങും: റോഡ് പണി"))
        self.assertEqual("jobs", learned.topic("മലപ്പുറത്ത് 23ന് സ്വകാര്യ തൊഴിൽ മേള"))
        self.assertEqual("education", learned.topic("എസ്എസ്എൽസി പരീക്ഷയ്ക്ക് സൗജന്യ പരിശീലനം"))
        real = learned.load
        learned.load = lambda: {"topic_weight": {"civic": -0.5, "education": -0.5}}      # not measured yet: the starting weight is used
        try:
            self.assertGreater(learned.boost("നാളെ 9 പ്രദേശങ്ങളിൽ വൈദ്യുതി മുടങ്ങും"), 0)
            self.assertGreater(learned.boost("സ്വകാര്യ തൊഴിൽ മേള"), 0)
        finally:
            learned.load = real


class PowerCutTiming(unittest.TestCase):
    A = "കോട്ടക്കൽ സബ്സ്റ്റേഷനിൽ അറ്റകുറ്റപ്പണി: നാളെ രാവിലെ 9 മുതൽ ഉച്ചയ്ക്ക് 2 വരെ വൈദ്യുതി മുടങ്ങും"

    def at(self, h, m=0):
        return datetime.datetime.combine(TODAY, datetime.time(h, m), IST)

    def test_late_notice_not_posted(self):      # a cut until 2 pm went out at 13:42
        y = TODAY - datetime.timedelta(days=1)
        self.assertIn("too late", fr.power_cut_over(self.A, "", f"{y} 18:33", self.at(13, 35)))
        self.assertEqual("", fr.power_cut_over(self.A, "", f"{y} 18:33", self.at(10, 0)))

    def test_tomorrow_cut_posted_today(self):
        self.assertEqual("", fr.power_cut_over(self.A, "", f"{TODAY} 18:33", self.at(21, 0)))

    def test_english_and_evening_end(self):
        y = TODAY - datetime.timedelta(days=1)
        self.assertIn("14:00", fr.power_cut_over("Power cut in Manjeri tomorrow", "Power cut from 9 am to 2 pm", f"{y}", self.at(13, 45)))
        self.assertIn("17:00", fr.power_cut_over("മലപ്പുറത്ത് ഇന്ന് രാവിലെ 9 മുതൽ വൈകിട്ട് 5 വരെ വൈദ്യുതി മുടക്കം", "", f"{TODAY}", self.at(16, 45)))


class NewsDate(unittest.TestCase):
    def test_date_from_link(self):      # the Sheet had no publish date for a story
        self.assertEqual(datetime.date(2026, 10, 26), fr.news_date("", "https://www.manoramaonline.com/district-news/malappuram/2026/10/26/x.html"))
        self.assertEqual(datetime.date(2026, 10, 23), fr.news_date("", "https://www.example-news.com/kerala/malappuram/20261023/x"))
        self.assertEqual(datetime.date(2026, 10, 25), fr.news_date("2026-10-25T09:00:00Z", ""))


class PostingGate(unittest.TestCase):
    def setUp(self):
        post.ALL_ROWS = []

    def row(self, **k):
        r = {"story_id": "MP-T1", "headline_ml": "കോട്ടക്കലിൽ നിരോധിത പുകയില ഉൽപന്നങ്ങൾ വിറ്റ 2 പേർ അറസ്റ്റിൽ",
             "headline_en": "Two held for selling banned tobacco in Kottakkal", "category": "Crime & Safety", "location": "കോട്ടക്കൽ, മലപ്പുറം",
             "caption": "കോട്ടക്കലിൽ പുകയില വിറ്റ രണ്ടുപേർ അറസ്റ്റിൽ", "published": f"{TODAY}",
             "source": f"https://www.manoramaonline.com/district-news/malappuram/{TODAY:%Y/%m/%d}/tobacco-arrest.html",
             "researched": f"{TODAY:%d %b %Y}, 06:25", "post_status": "", "notes": "", "batch": "", "review": "Auto"}
        r.update(k)
        return r

    def test_today_news_posts(self):
        self.assertEqual("", post.skip_reason(self.row()))

    def test_two_day_old_news_not_posted(self):      # a story went out two days late
        old = TODAY - datetime.timedelta(days=2)
        self.assertIn("older than yesterday", post.skip_reason(self.row(published=f"{old}", researched=f"{old:%d %b %Y}, 01:50")))

    def test_old_news_by_link_date(self):
        old = TODAY - datetime.timedelta(days=3)
        self.assertIn("older than yesterday", post.skip_reason(self.row(
            published="", source=f"https://www.manoramaonline.com/district-news/malappuram/{old:%Y/%m/%d}/x.html")))

    def test_other_district_not_posted(self):      # neighbouring-district stories slipped through
        self.assertTrue(post.skip_reason(self.row(headline_ml="കോഴിക്കോട് ബസ് അപകടം: 5 പേർക്ക് പരിക്ക്", location="കോഴിക്കോട്",
                                                  caption="കോഴിക്കോടിന് സമീപം അപകടം", source="https://www.example.com/news/x")))


class DistrictFilter(unittest.TestCase):
    def test_link_district(self):
        self.assertEqual("malappuram", allnews.url_district("https://www.manoramaonline.com/district-news/malappuram/2026/10/26/x.html"))
        self.assertEqual("malappuram", allnews.url_district("https://www.mathrubhumi.com/malappuram/news/youth-arrested-1.12345"))
        self.assertEqual("kozhikode", allnews.url_district("https://www.mathrubhumi.com/kozhikode/news/x-1.12345"))

    def test_places(self):
        for t in ("മഞ്ചേരിയിൽ", "വളാഞ്ചേരിയിൽ തീപിടിത്തം", "Nilambur rain", "കോട്ടക്കലിൽ", "മലപ്പുറത്ത്"):
            self.assertTrue(allnews.has_place(t), t)
        self.assertTrue(allnews.other_district("കോഴിക്കോട് കനത്ത മഴ"))


class Recheck(unittest.TestCase):
    URL = "https://www.manoramaonline.com/district-news/malappuram/2026/10/27/median-crowd.html"

    def test_rejected_district_page_story_checked_again_once(self):      # stories on the paper's district page stayed 'checked earlier'
        st = {"s": "notdistrict", "n": 0}
        self.assertTrue(collect.recheck_once(st, self.URL))
        self.assertNotIn("s", st)      # the writer must not see the old verdict
        st["s"] = "notdistrict"
        self.assertFalse(collect.recheck_once(st, self.URL))      # only once

    def test_old_duplicate_checked_again(self):      # the escaped-prisoner news
        st = {"s": "dup", "n": 0}
        self.assertTrue(collect.recheck_once(st, "https://news.google.com/x"))

    def test_other_district_not_rechecked(self):
        self.assertFalse(collect.recheck_once({"s": "notdistrict"}, "https://www.mathrubhumi.com/kozhikode/news/x-1.12345"))


class DistrictListPages(unittest.TestCase):
    def test_reads_whole_list(self):      # only the first 8 stories of a district page were read; a big rain report was missed
        import sources
        page = "".join(f'<a href="/district-news/malappuram/2026/10/27/story-{i}.html">x</a>' for i in range(12))
        page += "".join(f'<a href="https://www.mathrubhumi.com/malappuram/news/rain-{i}-1.1000{i}">x</a>' for i in range(3))
        page += '<a href="/district-news/malappuram/2026/10/27/story-0.html">again</a>'      # the same link twice is read once
        old = sources._get
        sources._get = lambda u: page
        try:
            links = sources.candidate_links(60)
        finally:
            sources._get = old
        self.assertEqual(15, len(links))
        self.assertIn("https://www.manoramaonline.com/district-news/malappuram/2026/10/27/story-11.html", links)
        self.assertTrue(any("mathrubhumi.com/malappuram/news/rain-2" in l for l in links))


class Reel(unittest.TestCase):
    def test_no_b_tags_on_screen(self):      # '<b>90,703</b>' showed in a reel
        E = from_file(ROOT / "reel" / "reel4.py", {"E"})["E"]
        self.assertEqual("90,703", E("<b>90,703</b>"))
        self.assertEqual("5 &lt; 7", E("5 < 7"))

    def test_google_voice_free_only(self):      # owner: Google voice only inside the free allowance, else the edge-tts voice
        ns = from_file(ROOT / "reel" / "reel4.py", {"voice_setting", "pick_voice", "google_used_this_month", "google_record", "_gv_dir", "_GV"})
        with tempfile.TemporaryDirectory() as tmp:
            ns["_gv_dir"] = lambda: Path(tmp)
            os.environ["GOOGLE_TTS_API_KEY"] = "test"
            try:
                spec = {"story": "MP-142", "sentences": [{"say": "അ" * 1300}]}
                self.assertEqual("google", ns["pick_voice"](spec)[0].get("engine"))
                self.assertEqual("google", ns["pick_voice"]({"story": "MP-143", "sentences": spec["sentences"]})[0].get("engine"))      # every reel, odd numbers too
                month = datetime.datetime.now(IST).strftime("%Y-%m")
                (Path(tmp) / f"MP-2_gvoice_{month}.json").write_text(json.dumps({"chars": 699500}))
                self.assertEqual("edge", ns["pick_voice"]({"story": "MP-144", "sentences": spec["sentences"]})[0].get("engine"))
                cfg = json.loads((ROOT / "poster" / "config.json").read_text())
                self.assertLessEqual(cfg["reel_voice_alt"]["free_chars_per_month"], 1000000, "never above Google's free tier")
            finally:
                os.environ.pop("GOOGLE_TTS_API_KEY", None)
        os.environ.pop("GOOGLE_TTS_API_KEY", None)
        self.assertEqual("edge", ns["pick_voice"]({"story": "MP-146", "sentences": [{"say": "അ"}]})[0].get("engine"))      # no key -> edge voice

    def test_malayalam_voices(self):      # the port: the reel is read in Malayalam, never by a Tamil voice
        cfg = json.loads((ROOT / "poster" / "config.json").read_text())
        self.assertTrue(cfg["reel_voice"]["voice"].startswith("ml-IN-"))
        self.assertTrue(cfg["reel_voice_alt"]["voice"].startswith("ml-IN-"))


class Images(unittest.TestCase):
    def test_cover_dev_scenes_schnell(self):      # owner: cost saving, every picture still made for this news
        import imagegen
        calls = []
        old_fal, old_size, old_key = imagegen._fal, imagegen.to_story_size, os.environ.get("FAL_KEY")
        imagegen._fal = lambda p, s, k, model=None: calls.append(model) or b"img"
        imagegen.to_story_size = lambda b: b
        os.environ["FAL_KEY"] = "test"
        try:
            imagegen.generate("p", 1); imagegen.generate("p", 1, cheap=True)
        finally:
            imagegen._fal, imagegen.to_story_size = old_fal, old_size
            if old_key is None:
                os.environ.pop("FAL_KEY", None)
            else:
                os.environ["FAL_KEY"] = old_key
        self.assertEqual(["fal-ai/flux/dev", "fal-ai/flux/schnell"], calls)
        self.assertNotEqual("1", os.environ.get("REUSE_IMAGES"), "older pictures are never reused")


class PrimeTime(unittest.TestCase):
    """owner: non-urgent reels wait for 9-12 / 18-21:30; urgent news never waits; nothing is ever dropped"""
    FESTIVAL = "ക്ഷേത്രോത്സവത്തിന് കൊടിയേറി"

    def at(self, h, m=0):
        return datetime.datetime.combine(TODAY, datetime.time(h, m), IST)

    def row(self, title, filed_h_ago=1):
        t = datetime.datetime.now(IST) - datetime.timedelta(hours=filed_h_ago)
        return {"story_id": "MP-T", "headline_ml": title, "headline_en": "", "category": "", "researched": t.strftime("%d %b %Y, %H:%M")}

    def test_urgent_never_waits(self):
        for title in ("കോട്ടക്കൽ ഭാഗത്ത് നാളെ വൈദ്യുതി മുടങ്ങും", "സ്വകാര്യ ബസ് ഇടിച്ച് തൊഴിലാളി മരിച്ചു",
                      "മലപ്പുറം ജില്ലയിൽ കനത്ത മഴ മുന്നറിയിപ്പ്", "കളക്ടറുടെ അറിയിപ്പ്: പ്രത്യേക ക്യാമ്പ്"):
            self.assertEqual("", post.prime_wait(self.row(title), self.at(14)), title)

    def test_other_news_waits_outside_prime_time(self):
        self.assertIn("prime time", post.prime_wait(self.row(self.FESTIVAL), self.at(14)))
        self.assertIn("18:00", post.prime_wait(self.row(self.FESTIVAL), self.at(14)))
        self.assertIn("09:00", post.prime_wait(self.row(self.FESTIVAL), self.at(23)))

    def test_posts_inside_prime_time(self):
        self.assertEqual("", post.prime_wait(self.row(self.FESTIVAL), self.at(10)))
        self.assertEqual("", post.prime_wait(self.row(self.FESTIVAL), self.at(19, 30)))

    def test_never_dropped_after_long_wait(self):      # a reel that has waited 12 hours goes out whatever the hour
        self.assertEqual("", post.prime_wait(self.row(self.FESTIVAL, filed_h_ago=13), self.at(3)))


class ReelOpening(unittest.TestCase):
    """owner (change 1): the most striking fact is spoken first"""
    def test_punch_line(self):
        ns = from_file(ROOT / "reel" / "reel4.py", {"punch_line", "punch_on"})
        self.assertEqual("90,703 കുട്ടികൾക്ക് വിറ്റാമിൻ എ ക്യാമ്പ്!", ns["punch_line"]({"hook": ["കുട്ടികൾക്ക് വിറ്റാമിൻ എ ക്യാമ്പ്", "<b>90,703</b>"]}))
        self.assertEqual("നാളെ വൈദ്യുതി മുടങ്ങും!", ns["punch_line"]({"hook": ["നാളെ വൈദ്യുതി മുടങ്ങും", "9 പ്രദേശങ്ങളിൽ വൈദ്യുതി മുടക്കം - പൂർണ പട്ടിക താഴെ"]}))
        self.assertEqual("എഴുത്തുകാരൻ നികുതി", ns["punch_line"]({"punch": "<b>എഴുത്തുകാരൻ</b> നികുതി", "hook": ["x", "1"]}))
        # owner: the reel opens with the one-line story itself (first 2-3 s), not a separate punch line
        self.assertFalse(json.loads((ROOT / "poster" / "config.json").read_text()).get("reel_punch"))


class ReelWords(unittest.TestCase):
    """owner: no double reading, full dates, everyday Kerala words in voice, subtitles and cards"""
    ns = None

    @classmethod
    def setUpClass(cls):
        cls.ns = from_file(ROOT / "reel" / "reel4.py", {"everyday", "everyday_on", "EVERYDAY", "fix_dates", "MONTHS_ML", "repeats", "_words", "punch_line"})

    def test_everyday_words(self):
        e = self.ns["everyday"]
        self.assertEqual("സ്വകാര്യ ബസ് ഇടിച്ച് ബൈക്കിൽ സഞ്ചരിച്ച", e("സ്വകാര്യ ബസ്സ് ഇടിച്ച് ഇരുചക്ര വാഹനത്തിൽ സഞ്ചരിച്ച"))
        self.assertEqual("ജില്ലാ കളക്ടർ, കളക്ടർക്ക് നിവേദനം", e("ജില്ലാ കലക്ടർ, കലക്ടർക്ക് നിവേദനം"))
        self.assertEqual("പോലീസ് അന്വേഷണം", e("പൊലീസ് അന്വേഷണം"))
        self.assertEqual("കെഎസ്ആർടിസി ബസ്സിൽ", e("കെഎസ്ആർടിസി ബസ്സിൽ"))      # a correct word that only starts like a formal word stays

    def test_full_dates(self):
        f, T = self.ns["fix_dates"], datetime.date(2026, 10, 27)
        self.assertEqual("ക്യാമ്പ് ഒക്ടോബർ 30-ാം തീയതി വരെ നടക്കും.", f("ക്യാമ്പ് <b>30</b> വരെ നടക്കും.", T))
        self.assertEqual("ഒക്ടോബർ 22-ാം തീയതി മലപ്പുറത്ത്", f("22-ാം തീയതി മലപ്പുറത്ത്", T))
        self.assertEqual("യോഗം ഒക്ടോബർ 29ന് നടക്കും", f("യോഗം 29ന് നടക്കും", T))
        for keep in ("ഒക്ടോബർ 28ന്", "വൈകിട്ട് 4.30 വരെ", "10.30 വരെ", "5 വയസ്സ് വരെയുള്ള", "രാവിലെ 10ന്"):
            self.assertEqual(keep, f(keep, T))

    def test_no_double_reading(self):
        self.assertTrue(self.ns["repeats"]("സ്വകാര്യ ബസ് ഇടിച്ച് തൊഴിലാളി മരിച്ചു!", "വേങ്ങരയ്ക്ക് സമീപം സ്വകാര്യ ബസ് ഇടിച്ച് ഒരു തൊഴിലാളി മരിച്ചു."))
        self.assertFalse(self.ns["repeats"]("നാളെ വൈദ്യുതി മുടങ്ങും!", "മഞ്ചേരി സബ്സ്റ്റേഷനിൽ അറ്റകുറ്റപ്പണി നടക്കുന്നു."))
        self.assertEqual("സ്വകാര്യ ബസ് ഇടിച്ച് തൊഴിലാളി മരിച്ചു!", self.ns["punch_line"]({"hook": ["സ്വകാര്യ ബസ് ഇടിച്ച് തൊഴിലാളി മരിച്ചു", "22 അപകടം, ഞായർ"]}))


class Website(unittest.TestCase):
    """owner: every posted story goes to the website with all its details; a website problem never stops posting"""
    def test_payload_has_everything(self):
        import website
        row = {"story_id": "MP-140", "researched": "27 Oct 2026, 10:14", "published": "2026-10-27", "headline_ml": "മരച്ചീനി കർഷക യോഗം",
               "headline_en": "Tapioca meeting", "category": "Government & Services", "location": "മലപ്പുറം", "source": "https://www.manoramaonline.com/x/1",
               "caption": "📰 പൂർണ വിവരം:\n🕘 സമയം: വൈകിട്ട് 4.30", "reel_script": "യോഗം നടക്കും.",
               "images": '["https://res.cloudinary.com/a.jpg", "NOIMAGE", "http://insecure.jpg"]', "reel_link": "മലപ്പുറം 360: https://www.instagram.com/reel/De_Cu6Pj3zR/"}
        p = website.payload(row, "", {"title_en": "Collector calls meeting", "story_en": "A meeting will be held."})
        self.assertEqual("2026-10-27T10:14:00+05:30", p["filed_at"])      # exact India time, not 12:00
        self.assertEqual(["https://res.cloudinary.com/a.jpg"], p["images"])
        self.assertEqual("Collector calls meeting", p["headline_en"])
        self.assertEqual("മരച്ചീനി കർഷക യോഗം", p["headline_ml"])
        self.assertIn("instagram.com/reel/", p["reel_link"])
        for k in ("location", "category", "source", "caption", "reel_script"):
            self.assertTrue(p[k], k)

    def test_never_raises_without_key(self):
        import website
        os.environ.pop("WEBSITE_INGEST_KEY", None)
        self.assertFalse(website.send({"story_id": "MP-1", "headline_ml": "x", "_en": {"title_en": "x", "story_en": "y" * 50}}, ""))


class FullDetail(unittest.TestCase):
    """reels were much shorter than the source article; owner: full detail, at most 60 seconds"""

    def length_problems(self, words, article_words):
        import validate
        d = example(1)
        d["reel_script"] = " ".join(["വിവരം"] * words) + " " + validate.LAST
        art = " ".join(f"വാക്ക്{i}" for i in range(article_words))
        return [x for x in validate.validate(d, art) if x.startswith("reel_script has")]

    def test_short_reel_of_long_article_is_rewritten(self):
        self.assertTrue(self.length_problems(70, 300))
        self.assertFalse(self.length_problems(95, 300))      # owner: at most 60 s / 105 words; the caption keeps the rest

    def test_short_article_keeps_a_short_reel(self):
        self.assertFalse(self.length_problems(70, 80))

    def test_never_more_words_than_60_seconds(self):
        self.assertTrue(self.length_problems(130, 400))

    def test_examples_are_full_detail(self):      # rules.md asks for 70-105 Malayalam words (Malayalam words are longer than Tamil ones)
        for e in json.loads((ROOT / "research_free" / "examples.json").read_text(encoding="utf-8")):
            self.assertGreaterEqual(len(e["output"]["reel_script"].split()), 70)

    def test_reel_max_seconds(self):
        self.assertEqual(json.loads((ROOT / "poster" / "config.json").read_text())["reel_max_seconds"], 60)
        self.assertIn("fit_max(work, len(texts), lead, gap)", (ROOT / "reel" / "reel4.py").read_text(encoding="utf-8"))


class Proofread(unittest.TestCase):
    """the last proofread damaged posted reels: a word doubled inside a sentence, the place name misspelt, 'must come' turned into
    'need not come', a verb turned into a noun, the follow line 'ത്രീ സിക്സ്റ്റി' translated"""

    def setUp(self):
        import mlcheck
        self.T = mlcheck

    def test_bad_fixes_are_refused(self):
        art = "പട്ടയം ആവശ്യപ്പെട്ട് നിവേദനം. കുട്ടികളെ രക്ഷപ്പെടുത്തി."
        for w, ok in [("മലപ്പുറം", "മലപ്പുരം"), ("വരേണ്ട", "വരേണ്ടതില്ല"), ("ത്രീ സിക്സ്റ്റി", "മൂന്ന് അറുപത്"),
                      ("Follow", "ഫോളോ ചെയ്യൂ"), ("കർശനമായി", ""), ("പോകാതെ", "പോകാതെ പോയി പോകാതെ"),
                      ("രക്ഷപ്പെടുത്തി.", "രക്ഷപ്പെടുത്തീ."), ("പട്ടയം", "പട്ടായം"), ("പെരിന്തൽമണ്ണ", "പി.മണ്ണ"),
                      ("തിരൂരങ്ങാടി താലൂക്ക്", "തി.താലൂക്ക്"), ("വരേണ്ട", "വരേണ്ടതല്ല")]:
            self.assertTrue(self.T.unsafe(w, ok, art), f"{w} -> {ok} must be refused")

    def test_verb_not_turned_into_noun(self):      # 'നിയന്ത്രിക്കുന്നു' -> 'നിയന്ത്രണം'
        self.assertTrue(self.T.unsafe("സർക്കാർ നിയന്ത്രിക്കുന്നു", "സർക്കാർ നിയന്ത്രണം", ""))
        self.assertEqual(self.T.unsafe("സർക്കാർ നിയന്തിക്കുന്നു", "സർക്കാർ നിയന്ത്രിക്കുന്നു", ""), "")      # the real spelling fix still goes in

    def test_real_spelling_fixes_still_go_in(self):
        for w, ok in [("പ്രസിദ്ധീകരിച്ചിട്ടുുണ്ട്.", "പ്രസിദ്ധീകരിച്ചിട്ടുണ്ട്."), ("പഞ്ചയത്ത്", "പഞ്ചായത്ത്"), ("അദ്ധ്യാപകർ", "അധ്യാപകർ")]:
            self.assertEqual(self.T.unsafe(w, ok, ""), "", f"{w} -> {ok}")

    def test_no_word_inside_a_word(self):      # a fix for a short word was applied inside a longer word
        import llm
        row = {"headline_ml": "x", "caption": "സ്കൂളിൽ പോകാതെ", "slides_spec": "{}",
               "reel_script": "സ്കൂളിൽ പോകാതെ ജന്മദിനം. രാജു സ്കൂളിൽ പോയില്ല. " + self.T.LAST}
        before = dict(row)
        old = llm.ask_json
        llm.ask_json = lambda *a, **k: ({"fixes": [{"wrong": "പോക", "right": "പോകു"}]}, "test")
        try:
            self.T.proofread(row, log=lambda *a: None, article="")
        finally:
            llm.ask_json = old
        self.assertEqual(row, before)

    def test_age_shorthand_sent_back(self):
        import validate
        d = example(1)
        d["reel_script"] = "വീരൻ തന്റെ മകൻ രാജു, 12, സ്കൂളിൽ പോയില്ല. " + validate.LAST
        self.assertTrue([p for p in validate.validate(d, "") if "ages" in p])


class ClearReading(unittest.TestCase):
    """owner: one-line story in the first 2-3 seconds; every number heard with its meaning (age, count, date with month)"""

    def problems(self, script):
        import validate
        d = example(0)
        d["reel_script"] = script + " " + validate.LAST
        return validate.validate(d, "")

    def test_long_opening_sent_back(self):
        self.assertTrue([p for p in self.problems("സ്കൂളിൽ പോകാതെ ജന്മദിനം ആഘോഷിക്കാൻ പോയ മൂന്ന് വിദ്യാർഥികളെ കോട്ടക്കൽ ബസ് സ്റ്റാൻഡിൽ നിന്ന് പോലീസ് കണ്ടെത്തി രക്ഷിതാക്കൾക്ക് കൈമാറി.") if p.startswith("sentence 1")])
        self.assertFalse([p for p in self.problems("കോട്ടക്കലിൽ മൂന്ന് വിദ്യാർഥികളെ കണ്ടെത്തി.") if p.startswith("sentence 1")])

    def test_bare_numbers_sent_back(self):
        self.assertTrue([p for p in self.problems("വിദ്യാർഥികളെ കണ്ടെത്തി. കൗശിക്, 14, ശ്രീധർ, 15, കാണാതായിരുന്നു.") if "without their meaning" in p])
        for ok in ("വിദ്യാർഥികളെ കണ്ടെത്തി. 14 വയസ്സുള്ള കൗശിക്കിനെ കാണാതായി.", "വിദ്യാർഥികളെ കണ്ടെത്തി. ഒക്ടോബർ 28, 2026ന് യോഗം.",
                   "വിദ്യാർഥികളെ കണ്ടെത്തി. 30 കുപ്പികളും 5,000 രൂപയും പിടിച്ചെടുത്തു.", "വിദ്യാർഥികളെ കണ്ടെത്തി. വില 5.70 രൂപ."):
            self.assertFalse([p for p in self.problems(ok) if "without their meaning" in p], ok)


class FollowUpAndPage(unittest.TestCase):
    """'3 arrested for the laptop theft' was blocked as a duplicate of the theft 6 days earlier; the district Collector's notice on
    the paper's own district page was blocked as not district news"""

    def test_arrest_after_the_theft_is_new_news(self):
        old = {"story_id": "MP-42", "researched": "22 Oct 2026, 10:26", "headline_en": "Four laptops and a phone stolen from students' room near Tirur",
               "headline_ml": "വിദ്യാർഥികളുടെ മുറിയിൽ നിന്ന് 4 ലാപ്ടോപ്പും മൊബൈൽ ഫോണും മോഷണം പോയി"}
        new = {"story_id": "MP-159", "researched": "28 Oct 2026, 06:39", "headline_en": "Three arrested for stealing laptops and mobile phones from student rooms near Tirur",
               "headline_ml": "തിരൂരിൽ ലാപ്ടോപ്പ്, മൊബൈൽ ഫോൺ മോഷണം: 3 പേർ അറസ്റ്റിൽ"}
        self.assertTrue(fr.follow_up(old, new))

    def test_same_day_report_stays_a_duplicate(self):
        a = {"researched": "27 Oct 2026, 17:10", "headline_ml": "കാണാതായ 4 സ്കൂൾ കുട്ടികളെ കോട്ടക്കലിൽ കണ്ടെത്തി"}
        b = {"researched": "28 Oct 2026, 05:46", "headline_ml": "സ്കൂളിൽ പോകാതെ ജന്മദിനം ആഘോഷിച്ച 3 വിദ്യാർഥികളെ കോട്ടക്കലിൽ കണ്ടെത്തി"}
        self.assertFalse(fr.follow_up(a, b))

    def test_paper_district_page_is_district_news(self):
        row = {"source": "https://www.manoramaonline.com/district-news/malappuram/2026/10/27/diwali-sweets-licence.html",
               "headline_ml": "ദീപാവലി മധുരപലഹാര വിൽപനയ്ക്ക് ലൈസൻസ് നിർബന്ധം", "caption": "ലൈസൻസ് നിർബന്ധം", "location": "Kerala"}
        self.assertEqual(post.not_in_district(row), "")
        row["headline_ml"] = "കോഴിക്കോട് മധുരപലഹാര വിൽപനയ്ക്ക് ലൈസൻസ് നിർബന്ധം"
        self.assertTrue(post.not_in_district(row))


class Ages(unittest.TestCase):
    """'രാജു, 47,' / 'രാജു (47)' was heard as a bare number - the age is said with വയസ്സ്, also for stories written earlier"""

    def test_newspaper_ages(self):
        import names
        self.assertEqual(names.ages("താമസിക്കുന്ന രാജു, 47, ധനസഹായം"), "താമസിക്കുന്ന രാജു (47 വയസ്സ്), ധനസഹായം")
        self.assertEqual(names.ages("ഉടമ രാജു (47), ചൊവ്വാഴ്ച"), "ഉടമ രാജു (47 വയസ്സ്), ചൊവ്വാഴ്ച")
        self.assertEqual(names.ages("കൗശിക്, 14, ശ്രീധർ, 15, എന്നിവരും"), "കൗശിക് (14 വയസ്സ്), ശ്രീധർ (15 വയസ്സ്), എന്നിവരും")
        for same in ("ഒക്ടോബർ 13, 14, 15 തീയതികളിൽ", "ഒക്ടോബർ, 12, യോഗം", "രാജു (47 വയസ്സ്) എത്തി", "5,000 രൂപ പിഴ"):
            self.assertEqual(names.ages(same), same)
        self.assertIn("(47 വയസ്സ്)", names.spoken("താമസിക്കുന്ന രാജു, 47, ധനസഹായം"))


class ReelTooLong(unittest.TestCase):
    """owner: a reel over the time limit is shortened automatically, never held"""
    SCRIPT = ("വണ്ടൂർ ചന്തയിൽ രണ്ടാഴ്ചയായി തേങ്ങ ലേലം നടക്കുന്നില്ല. കർഷകർ ദുരിതത്തിലാണ്. "
              "എല്ലാ ചൊവ്വാഴ്ചയും വ്യാഴാഴ്ചയും ആണ് ലേലം നടക്കാറുള്ളത്. പല നാടുകളിൽ നിന്നുള്ള കർഷകർ ഇവിടെ എത്താറുണ്ട്. "
              "വ്യാപാരികൾ ലേലത്തിൽ പങ്കെടുക്കാൻ വിസമ്മതിച്ചു. പുറത്തെ ചന്തകളിൽ കുറഞ്ഞ വില മാത്രമേ ലഭിക്കൂ. " + LAST)

    def test_shorter_keeps_first_and_follow_line(self):
        out = post.shorten_script(self.SCRIPT, 0.5)
        self.assertLess(len(out), len(self.SCRIPT))
        self.assertTrue(out.startswith("വണ്ടൂർ ചന്തയിൽ"))
        self.assertTrue(out.endswith("ഫോളോ ചെയ്യൂ."))
        self.assertGreaterEqual(len(re.split(r"(?<=[.!?])\s+", out)), 3)

    def test_short_script_unchanged(self):
        s = "ഒന്ന്. രണ്ട്. കൂടുതൽ വാർത്തകൾക്ക് ഫോളോ ചെയ്യൂ."
        self.assertEqual(post.shorten_script(s, 0.5), s)


class NotNews(unittest.TestCase):
    """a story that only says the article has no details (a daily price page whose price was in an image) is never filed or posted;
    a real story with one such sentence keeps its facts and loses only that sentence"""
    EMPTY = ("ഇന്നത്തെ സ്വർണവില സംബന്ധിച്ച വിവരം ഈ ലേഖനത്തിൽ നൽകിയിട്ടില്ല. സ്വർണവില എത്രയെന്ന കണക്കിന്റെ വിവരങ്ങൾ ലഭ്യമല്ല. "
             "മറ്റൊരു വാർത്തയാണ് പേജിലുള്ളത്. ആ വാർത്ത സ്വർണവിലയുമായി ബന്ധപ്പെട്ടതല്ല. കൂടുതൽ വിവരങ്ങൾ ലഭിക്കുമ്പോൾ അറിയിക്കും. " + LAST)
    REAL = ("മലപ്പുറത്ത് പെൻഷൻകാരുടെ സംഘടനയുടെ യോഗം നടന്നു. ക്ഷാമബത്ത സഹിതം പെൻഷൻ നൽകണമെന്ന് യോഗം ആവശ്യപ്പെട്ടു. "
            "ജില്ലാ പ്രസിഡന്റ് അധ്യക്ഷത വഹിച്ചു. 2013ന് ശേഷം ജോലിയിൽ പ്രവേശിച്ചവർ ഈ ആവശ്യത്തിന്റെ പരിധിയിൽ വരും. "
            "ആകെ ആനുകൂല്യങ്ങളെക്കുറിച്ചുള്ള പൂർണ വിവരം അറിവായിട്ടില്ല. " + LAST)

    def test_empty_story_rejected(self):
        self.assertTrue(fr.no_news("ഇന്നത്തെ സ്വർണവില", self.EMPTY, "").startswith("not news"))

    def test_headline_saying_no_detail_rejected(self):
        self.assertTrue(fr.no_news("സ്വർണവില - വിവരം ലഭ്യമല്ല", "", ""))

    def test_real_story_kept_and_cleaned(self):
        self.assertEqual(fr.no_news("പെൻഷൻകാരുടെ സംഘടനാ യോഗം", self.REAL, ""), "")
        out = fr.strip_no_news(self.REAL)
        self.assertNotIn("അറിവായിട്ടില്ല", out)
        self.assertIn("ക്ഷാമബത്ത", out)
        self.assertTrue(out.endswith("ഫോളോ ചെയ്യൂ."))

    def test_posting_gate_blocks_it(self):
        row = {"story_id": "MP-189", "headline_ml": "ഇന്നത്തെ സ്വർണവില", "headline_en": "Gold rate update", "category": "Business & Prices",
               "published": post.datetime.now(post.IST).isoformat(), "researched": post.datetime.now(post.IST).strftime("%d %b %Y, %H:%M"),
               "reel_script": self.EMPTY, "caption": "", "slides_spec": "{}"}
        self.assertTrue(post.skip_reason(row).startswith(("not news", "known issue meta_article")))      # blocked either way


class OwnerFixes(unittest.TestCase):
    """a reel (deleted by the owner) talked about the article; two posts of the same day's daily price; Claude backup model id"""

    def test_script_about_the_article_refused(self):
        import validate
        d = example(0)
        d["reel_script"] = ("ഇന്നത്തെ സ്വർണവില സംബന്ധിച്ച വിവരം ഈ ലേഖനത്തിൽ നൽകിയിട്ടില്ല. "
                            "വിവരം ലഭിക്കുന്ന മുറയ്ക്ക് അറിയിക്കും. " + validate.LAST)
        self.assertTrue([x for x in validate.validate(d, "") if "talks about the article" in x])
        self.assertFalse([x for x in validate.validate(example(0), "") if "talks about the article" in x])

    def test_one_daily_price_a_day(self):      # the Tamil pages' egg price is the gold rate here
        now = f"{TODAY:%d %b %Y}, 06:40"
        a = {"story_id": "MP-188", "researched": now, "headline_ml": "മലപ്പുറത്ത് സ്വർണവില പവന് 58,000 രൂപ", "headline_en": "Gold rate steady"}
        b = {"story_id": "MP-189", "researched": now, "headline_ml": "ഇന്നത്തെ സ്വർണവില", "headline_en": ""}
        self.assertEqual("gold", fr.same_day_recurring(a, b))
        y = dict(a, researched=f"{TODAY - datetime.timedelta(days=1):%d %b %Y}, 06:40")
        self.assertEqual("", fr.same_day_recurring(y, b))      # tomorrow's price is a new post
        self.assertEqual("", fr.same_day_recurring(a, {"researched": now, "headline_ml": "മഞ്ചേരിയിൽ ബൈക്ക് മോഷണം"}))
        post.ALL_ROWS = [dict(a, post_status="Posted")]
        try:
            self.assertIn("one gold price post a day", post.skip_reason(dict(b, source="", category="", published=f"{TODAY}", notes="", batch="", review="Auto")))
        finally:
            post.ALL_ROWS = []

    def test_claude_model_exists(self):
        # owner: the newest Haiku by default, with the older one only as an automatic fallback if the name is refused
        src = (ROOT / "research_free" / "llm.py").read_text()
        self.assertIn('os.environ.get("ANTHROPIC_MODEL") or "claude-haiku-5-5"', src)
        self.assertIn('model = body["model"] = "claude-haiku-4-5"', src)


class FreeImagesFirst(unittest.TestCase):
    """owner: Cloudflare and NVIDIA (free) first; FAL only when they fail (cover dev, scenes schnell)"""

    def order(self, fail, cheap=False):
        import imagegen
        calls = []
        def src(name):
            def f(*a, **k):
                calls.append(name)
                if name in fail:
                    raise RuntimeError(name + " 429: daily free allocation used")
                return b"img"
            return f
        saved = {k: getattr(imagegen, k) for k in ("_cf", "generate_nvidia", "_fal", "to_story_size")}
        env = {k: os.environ.get(k) for k in ("FAL_KEY", "NVIDIA_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")}
        imagegen._cf, imagegen.generate_nvidia, imagegen.to_story_size = src("cloudflare"), src("nvidia"), (lambda b: b)
        imagegen._fal = lambda p, s, k, model=None: src(model)()
        os.environ.update({k: "test" for k in env})
        imagegen.DEAD.clear()
        try:
            imagegen.generate("p", 1, cheap=cheap)
        finally:
            for k, v in saved.items():
                setattr(imagegen, k, v)
            for k, v in env.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
            imagegen.DEAD.clear()
        return calls

    def test_free_first_then_fal(self):
        self.assertEqual(["cloudflare"], self.order(set()))
        self.assertEqual(["cloudflare", "nvidia"], self.order({"cloudflare"}))
        self.assertEqual(["cloudflare", "nvidia", "fal-ai/flux/dev"], self.order({"cloudflare", "nvidia"}))      # cover
        self.assertEqual(["cloudflare", "nvidia", "fal-ai/flux/schnell"], self.order({"cloudflare", "nvidia"}, cheap=True))      # scenes 2-3


class NewsImagePrompt(unittest.TestCase):
    """owner: a clean, detailed prompt so the picture shows THIS news - the scene first, generic covers sent back"""
    GOOD = ("Two police constables in khaki unload seized liquor bottles from a white mini lorry onto a long table outside the Kottakkal "
            "police station while four men in shirts and mundu stand in a line nearby; the bottles are stacked in cartons, a police jeep is "
            "parked behind, coconut palms shade the station compound, late morning sunlight, light clouds, eye-level 35 mm wide shot showing the "
            "table, the lorry and the station gate.")

    def test_scene_first(self):
        p = collect.IMG_TEMPLATE.format(scene=self.GOOD)
        self.assertTrue(p.startswith("Two police constables"))
        self.assertIn("No text", p)
        self.assertIn("Kerala", p)

    def test_generic_cover_sent_back(self):
        head = "Police seize 120 liquor bottles from a mini lorry near Kottakkal"
        self.assertTrue(collect.scene_ok(self.GOOD, head))
        self.assertFalse(collect.scene_ok("A quiet village road in Kerala with trees and houses in daylight. " * 4, head))
        self.assertFalse(collect.scene_ok("Police seize liquor bottles from a lorry.", head))      # too short


class HeadlineOnlyAndMadeUp(unittest.TestCase):
    """a page that is only a headline is not written (the writer invented the rest), and a draft whose words mostly do not come
    from a Malayalam article is not filed. Short real briefs still pass."""
    def test_headline_only_page_has_no_body(self):
        a = {"title": "ED Raid| അപ്രതീക്ഷിത ട്വിസ്റ്റ്: കോഴിക്കോട്ടും റെയ്ഡ്.. ഞെട്ടി നഗരം",
             "text": "ED Raid| അപ്രതീക്ഷിത ട്വിസ്റ്റ്: കോഴിക്കോട്ടും റെയ്ഡ്.. ഞെട്ടി നഗരം അപ്രതീക്ഷിത ട്വിസ്റ്റ് കോഴിക്കോട്ടും"}
        self.assertLess(len(collect.body_words(a)), collect.HEADLINE_ONLY_MIN)

    def test_short_real_brief_passes(self):
        a = {"title": "ചീട്ടുകളി: 6 പേർ പിടിയിൽ",
             "text": "ചീട്ടുകളി: 6 പേർ പിടിയിൽ. പെരിന്തൽമണ്ണ പോലീസ് പട്രോളിങ്ങിനിടെ പണം വെച്ച് ചീട്ടുകളിച്ച ആറുപേരെ അറസ്റ്റ് ചെയ്തു, 11,600 രൂപ പിടിച്ചെടുത്തു. എല്ലാവരെയും ജാമ്യത്തിൽ വിട്ടു."}
        self.assertGreaterEqual(len(collect.body_words(a)), collect.HEADLINE_ONLY_MIN)

    def test_made_up_draft_rejected(self):
        art = {"url": "https://example.com/a", "title": "t", "published": collect.datetime.datetime.now(collect.IST).isoformat(),
               "text": " ".join(["മലപ്പുറത്ത്", "പോലീസ്", "അന്വേഷണം", "നടത്തി", "നാട്ടുകാരുടെ", "ആവശ്യം"] * 15)}
        d = {"malayalam_headline": "മലപ്പുറം വാർത്ത", "english_headline": "x", "category": "c", "location": "l", "scenes": ["s"],
             "reel_script": "", "caption": "", "slides_spec": {}}
        story, why = collect.file_story(art, (d, "test", ["not grounded: only 37% of the words come from the article"], 1), [], [])
        self.assertIsNone(story)
        self.assertIn("likely made up", why)


class OtherScriptLetters(unittest.TestCase):
    """letters of another script inside Malayalam words are repaired, so the voice reads the word and the card shows Malayalam
    letters; Chinese/Korean letters are removed"""
    def test_indic_letters_become_malayalam(self):
        import verify
        self.assertEqual(verify.fix_scripts("മലப்പുറം"), "മലപ്പുറം")      # Tamil ப் -> പ്
        self.assertEqual(verify.clean_text("പോലീस् സ്റ്റേഷനിൽ"), "പോലീസ് സ്റ്റേഷനിൽ")      # Devanagari स् -> സ്
        self.assertEqual(verify.clean_text("ജযিൽ"), "ജയിൽ")      # Bengali য ি -> യ ി

    def test_cjk_removed_and_malayalam_untouched(self):
        import verify
        self.assertNotRegex(verify.clean_text("ജയിൽ탈출 ചാട്ടം"), "[가-힯]")
        s = "സാധാരണ മലയാളം വാക്യം: 1,109 രൂപ ഫീസ്, ഒക്ടോബർ 26ന്."
        self.assertEqual(verify.clean_text(s), s)


class MalayalamSourcesOnly(unittest.TestCase):
    """owner: news only from Malayalam-language articles; English pages are skipped (a hand-given link still goes)"""
    def test_english_article_skipped(self):
        a = {"title": "Malappuram court sentences six to 10 years in prison in 2015 child trafficking case",
             "text": "A Malappuram court on Wednesday sentenced six people to ten years in prison in a 2015 case of selling a one-year-old girl. " * 4}
        self.assertFalse(collect.malayalam_source(a))

    def test_malayalam_article_kept(self):
        a = {"title": "വിളക്ക് കൊളുത്തുന്നതിനിടെ സാരിക്ക് തീപിടിച്ച് വയോധിക മരിച്ചു",
             "text": "കോട്ടക്കൽ പുത്തൂർ ഏഴാം വാർഡിൽ താമസിക്കുന്ന ലക്ഷ്മി പൂജാമുറിയിൽ വിളക്ക് കൊളുത്തുന്നതിനിടെ സാരിയിൽ തീ പടർന്നു. Kottakkal."}
        self.assertTrue(collect.malayalam_source(a))


class OldEventAndSameEvent(unittest.TestCase):
    """an old event re-told in a new article (a wedding from last December) is not posted; the same event from another outlet
    in other words (a bus crew fight) is not posted twice"""
    def test_old_event(self):
        t = "പ്രശസ്ത സിനിമാ താരവും സംവിധായകനും വിവാഹിതരായി. 2025 ഡിസംബർ 1ന് ക്ഷേത്രത്തിൽ വച്ചായിരുന്നു വിവാഹം."
        self.assertTrue(fr.old_event(t, datetime.date(2026, 10, 29)))
        self.assertEqual(fr.old_event("2015 ജൂലൈ 28ലെ കുട്ടിക്കടത്ത് കേസിൽ ബുധനാഴ്ച വിധി: 6 പേർക്ക് തടവ്", datetime.date(2026, 10, 29)), "")
        self.assertEqual(fr.old_event("വളാഞ്ചേരിയിൽ തെരുവുനായ ശല്യം രൂക്ഷം, നാട്ടുകാരുടെ പരാതി", datetime.date(2026, 10, 29)), "")

    def test_same_event_other_words(self):
        a = ("മലപ്പുറത്ത് ബസ് ജീവനക്കാർ നടുറോഡിൽ ഏറ്റുമുട്ടിയ സംഭവം വൈറൽ. രണ്ട് സ്വകാര്യ ബസുകളുടെ ഡ്രൈവർമാരും കണ്ടക്ടർമാരും "
             "യാത്രക്കാരെ കയറ്റുന്നതിനെ ചൊല്ലിയുള്ള തർക്കത്തെ തുടർന്ന് നടുറോഡിൽ തമ്മിലടിച്ചു. വീഡിയോ സമൂഹമാധ്യമങ്ങളിൽ പ്രചരിച്ചു. "
             "കുന്നുമ്മൽ ഭാഗത്ത് ഗതാഗതം തടസ്സപ്പെട്ടു.")
        b = ("കുന്നുമ്മലിൽ രണ്ട് ബസ് ജീവനക്കാർ നടുറോഡിൽ തമ്മിലടിച്ചു. സ്വകാര്യ ബസുകളുടെ ഡ്രൈവർമാരും കണ്ടക്ടർമാരും യാത്രക്കാരെ "
             "കയറ്റുന്നതിനെ ചൊല്ലി തർക്കം. നടുറോഡിൽ പരസ്പരം മർദിച്ചു. ദൃശ്യങ്ങൾ സമൂഹമാധ്യമങ്ങളിൽ പ്രചരിച്ചു. കുന്നുമ്മൽ ഭാഗത്ത് ഗതാഗതം തടസ്സപ്പെട്ടു.")
        other = ["എടവണ്ണയിൽ മാലിന്യം കത്തിക്കുന്നതിനിടെ തീപിടിത്തം", "മലപ്പുറത്ത് സ്വർണവില പവന് 58,000 രൂപ", "തിരൂരിൽ മണൽക്കടത്ത് പിടികൂടി"] * 10
        df = fr.event_df([a, b] + other)
        self.assertTrue(fr.same_event(a, b, df))
        self.assertFalse(fr.same_event(a, other[0] * 3, df))


class SameEventAtWriteTime(unittest.TestCase):
    """an online cracker scam (already posted) was written again from another outlet, because the headlines differ by one number
    ('2 ദിവസത്തിനിടെ') - the article text is now checked against filed reel scripts"""
    MP168 = ("ഓൺലൈനിൽ കുറഞ്ഞ വിലയ്ക്ക് പടക്കം എന്ന വ്യാജ പരസ്യങ്ങൾ വിശ്വസിച്ച് മലപ്പുറം ജില്ലയിൽ 25 പേർ തട്ടിപ്പിനിരയായി. 2 ദിവസത്തിനിടെ "
             "ഇവർക്ക് ആകെ 1.50 ലക്ഷം രൂപ നഷ്ടപ്പെട്ടു. ദീപാവലി നവംബർ 8ന് ആഘോഷിക്കും. ഇതോടനുബന്ധിച്ച് ആളുകൾ ഓൺലൈനായി പടക്കം ഓർഡർ ചെയ്യുന്നു. "
             "ഇത് മുതലെടുത്ത് തട്ടിപ്പുസംഘങ്ങൾ വ്യാജ വെബ്സൈറ്റുകളിലും സമൂഹമാധ്യമങ്ങളിലും പരസ്യം നൽകുന്നു. ശിവകാശി പടക്കങ്ങൾക്ക് 75 മുതൽ 80 ശതമാനം "
             "വരെ കിഴിവ് എന്ന് പറഞ്ഞാണ് കബളിപ്പിക്കുന്നത്. നിക്ഷേപിച്ചാൽ ഇരട്ടി പണം ലഭിക്കുമെന്നും മോഹിപ്പിക്കുന്നു. മലപ്പുറം ജില്ലാ സൈബർ ക്രൈം "
             "പോലീസ് അഡീഷണൽ എസ്പി വിജയരാഘവൻ, പടക്കം ഓർഡർ ചെയ്യുന്നതിന് മുമ്പ് വെബ്സൈറ്റിന്റെയോ സ്ഥാപനത്തിന്റെയോ വിശ്വാസ്യത ഉറപ്പാക്കണമെന്ന് നിർദേശിച്ചു.")
    ART = ("ഓൺലൈൻ പടക്ക പരസ്യം വിശ്വസിച്ച് മലപ്പുറം ജില്ലയിൽ 25 പേർക്ക് 1.50 ലക്ഷം രൂപ നഷ്ടമായ സംഭവം വലിയ ചർച്ചയായി. നവംബർ 8ന് ദീപാവലി "
           "ആഘോഷിക്കാനിരിക്കെ, ശിവകാശിയിൽ നിന്ന് ഓൺലൈൻ വഴി ആളുകൾ പടക്കങ്ങൾ തിരഞ്ഞെടുത്ത് ഓർഡർ ചെയ്തുവരികയാണ്. ഇത് മുതലെടുക്കുന്ന "
           "തട്ടിപ്പുസംഘങ്ങൾ വ്യാജ വെബ്സൈറ്റുകൾ വഴിയും സമൂഹമാധ്യമങ്ങൾ വഴിയും പരസ്യം നൽകി ആളുകളെ കബളിപ്പിക്കുന്നു. പ്രത്യേകിച്ച് ശിവകാശി "
           "പടക്കങ്ങൾക്ക് 75 മുതൽ 80 ശതമാനം വരെ കിഴിവ് നൽകുമെന്ന് പറഞ്ഞുള്ള വ്യാജ പരസ്യങ്ങൾ വഴിയാണ് പണം തട്ടുന്നത്. ഇതുസംബന്ധിച്ച് "
           "മുന്നറിയിപ്പ് നൽകിയ മലപ്പുറം ജില്ലാ സൈബർ ക്രൈം പോലീസ് അഡീഷണൽ എസ്പി വിജയരാഘവൻ, പടക്കം ഓർഡർ ചെയ്യുന്നതിന് മുമ്പ് "
           "വെബ്സൈറ്റിന്റെ വിശ്വാസ്യത ഉറപ്പാക്കണമെന്ന് അറിയിച്ചു.")
    OTHER = [("MP-%d" % i, "മലപ്പുറം %s റോഡ് പണിക്ക് %d കോടി രൂപ അനുവദിച്ച് പ്രവൃത്തി തുടങ്ങിയതായി പഞ്ചായത്ത് പ്രസിഡന്റ് അറിയിച്ചു" % (w, i))
             for i, w in enumerate(["വേങ്ങര", "മങ്കട", "എടക്കര", "നിലമ്പൂർ", "പൊന്നാനി", "താനൂർ"], 1)]

    def recent(self, when):
        rows = [{"story_id": "MP-168", "researched": when, "reel_script": self.MP168}]
        rows += [{"story_id": s, "researched": when, "reel_script": t} for s, t in self.OTHER]
        return rows

    def test_same_event_other_outlet_is_not_written(self):
        art = {"title": "ഓൺലൈൻ പടക്ക കെണി: മലപ്പുറത്ത് 2 ദിവസത്തിനിടെ 25 പേർക്ക് 1.50 ലക്ഷം രൂപ നഷ്ടം", "text": self.ART,
               "published": TODAY.isoformat()}
        y = (TODAY - datetime.timedelta(days=1)).strftime("%d %b %Y, 22:32")
        self.assertEqual(collect.same_event_filed(art, self.recent(y)), "MP-168")

    def test_old_story_or_other_news_is_not_a_duplicate(self):
        art = {"title": "x", "text": self.ART, "published": TODAY.isoformat()}
        old = (TODAY - datetime.timedelta(days=5)).strftime("%d %b %Y, 22:32")
        self.assertEqual(collect.same_event_filed(art, self.recent(old)), "")
        other = {"title": "മഞ്ചേരി കുളത്തിൽ മലിനജലം", "text": self.OTHER[0][1], "published": TODAY.isoformat()}
        rows = [r for r in self.recent(TODAY.strftime("%d %b %Y, 10:00")) if r["story_id"] != "MP-1"]
        self.assertEqual(collect.same_event_filed(other, rows), "")


class ListingPagesAreNotArticles(unittest.TestCase):
    """a topic page (a list of stories from all districts) was written as one story"""
    def test_listing_urls(self):
        for u in ("https://www.asianetnews.com/topic/missing-girl/page-2/amp", "https://www.example.com/tag/malappuram",
                  "https://malayalam.news18.com/author/x/", "https://site.in/news?page=3"):
            self.assertTrue(allnews.is_listing(u), u)
            self.assertFalse(allnews.local_ok(u, "മലപ്പുറത്ത് പെൺകുട്ടിയെ കണ്ടെത്തി"), u)
        for u in ("https://www.manoramaonline.com/district-news/malappuram/2026/10/29/x.html",
                  "https://www.mathrubhumi.com/malappuram/news/farmers-worried-1.12345"):
            self.assertFalse(allnews.is_listing(u), u)


class WrittenForAnotherDistrict(unittest.TestCase):
    """onion prices from a neighbouring district's market were written for the district page; inflected spellings of our own
    places were not seen as ours"""
    def test_other_place_in_first_lines(self):
        s = "ചെറിയ ഉള്ളിയുടെ വില കിലോയ്ക്ക് 150 രൂപ വരെ ഉയർന്നു. പാലക്കാട് ജില്ലയിലെ വടക്കഞ്ചേരി ആഴ്ചച്ചന്തയിൽ ഇന്ന് വിൽപന നടന്നു."
        self.assertTrue(allnews.written_elsewhere("ചെറിയ ഉള്ളി വില കുതിച്ചുയർന്നു", s))
        self.assertTrue(post.not_in_district({"source": "https://www.madhyamam.com/kerala/x", "headline_ml": "ചെറിയ ഉള്ളി വില ഉയർന്നു",
                                              "reel_script": s, "caption": s}))

    def test_district_stories_pass(self):
        self.assertEqual(allnews.written_elsewhere("മലപ്പുറത്ത് ധർണ", "കോഴിക്കോട് റോഡിൽ മലപ്പുറത്ത് ധർണ നടന്നു."), "")
        self.assertEqual(allnews.written_elsewhere("തെരുവുനായ ശല്യം", "വളാഞ്ചേരി നഗരസഭ പരിധിയിൽ തെരുവുനായ ശല്യം വർധിക്കുന്നു."), "")
        self.assertTrue(allnews.has_place("ചങ്ങരംകുളത്ത് പരിശീലനം"))


class CaptionCleanRuns(unittest.TestCase):
    """clean_caption used verify without importing it - every post job crashed with NameError for ~2.5 hours"""
    def test_clean_caption_runs(self):
        out = post.clean_caption({"caption": "വാർത്താ വരി ഒന്ന്\n\n#News", "headline_ml": "വാർത്ത", "story_id": "MP-1"})
        self.assertIn(out, (True, False, None) if not isinstance(out, str) else (out,))      # it must simply run


class KnownIssuesNeverRepeat(unittest.TestCase):
    """owner: once an issue is found it must never repeat - every entry of research_free/known_issues.py catches its own
    bad example and lets its good example through, at writing (validate) and at posting (skip_reason)"""

    def test_every_issue_catches_its_example(self):
        import known_issues
        for iid, seen, check, bad, good in known_issues.ISSUES:
            self.assertIn(iid, [x for x, _ in known_issues.problems(bad)], f"{iid} ({seen}) no longer caught")
            self.assertNotIn(iid, [x for x, _ in known_issues.problems(good)], f"{iid} blocks a good story")

    def test_checked_at_posting(self):
        import known_issues, verify
        post.ALL_ROWS = []
        for iid, seen, check, bad, good in known_issues.ISSUES:
            row = dict(bad, story_id="MP-T", source="", published="", researched="", notes="", batch="", review="Auto")
            fixed = known_issues.repair(dict(row, **{k: verify.clean_text(row.get(k) or "") for k in ("headline_ml", "reel_script", "caption")}))
            repaired = iid not in [x for x, _ in known_issues.problems(fixed)]      # e.g. stray letters of another script are repaired
            self.assertTrue(repaired or f"known issue {iid}" in post.skip_reason(row), f"{iid} would be posted again")


class ReachPlan(unittest.TestCase):
    """owner views plan: 60 s reels, full details in the caption, English search line, 5 focused hashtags, location tags"""
    ROW = {"headline_ml": "മഞ്ചേരിയിൽ ബൈക്ക് മോഷണം: യുവാവ് അറസ്റ്റിൽ", "headline_en": "Youth arrested for bike thefts in Manjeri",
           "location": "മഞ്ചേരി, മലപ്പുറം",
           "caption": "🚨 മഞ്ചേരിയിൽ ബൈക്ക് മോഷണം: യുവാവ് അറസ്റ്റിൽ\n\n📰 പൂർണ വിവരം:\nമഞ്ചേരിയിൽ തുടർച്ചയായി ബൈക്കുകൾ മോഷണം പോയി.\n\n"
                      "📍 മഞ്ചേരി, മലപ്പുറം | 29 ഒക്ടോബർ 2026\n\n#Malappuram360 #Malappuram #മഞ്ചേരിമോഷണം #MalappuramNews"}

    def tags(self, page_tag):
        old = post.TAG
        post.TAG = page_tag
        try:
            out = post.final_caption(dict(self.ROW))
        finally:
            post.TAG = old
        return out, out.strip().split("\n")[-1].split()

    def test_five_focused_hashtags_both_pages(self):
        for page_tag in ("#Malappuram360", "#Manjeri360"):
            out, tags = self.tags(page_tag)
            self.assertEqual(5, len(tags), tags)
            for t in (page_tag, "#Malappuram", "#Manjeri", "#CrimeNews", "#MalappuramNews"):
                self.assertIn(t, tags)

    def test_english_search_line_added_whole_words(self):
        out, _ = self.tags("#Malappuram360")
        self.assertIn("Youth arrested for bike thefts in Manjeri | Malappuram news", out)
        row = dict(self.ROW, headline_en="Manjeri substation maintenance: today's power cut shortened to 9 AM-2 PM instead of the usual full day schedule")
        line = next(l for l in post.final_caption(row).split("\n") if l.endswith("| Malappuram news"))
        self.assertTrue(line.split(" | ")[0].split()[-1].isalpha() or line.split(" | ")[0][-1].isdigit(), line)

    def test_switches(self):
        c = json.loads((ROOT / "poster" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(60, c["reel_max_seconds"])
        self.assertTrue(c["location_tags"])
        # the Malappuram / Manjeri Instagram location ids are still to be looked up by the owner (README setup checklist):
        # until then only the "default" entry exists and posts go out without a location
        self.assertIn("default", c["locations"])
        self.assertTrue(all(isinstance(v, str) for v in c["locations"].values()))
        self.assertIn("no brand names", collect.IMG_TEMPLATE)


class CaptionAllFacts(unittest.TestCase):
    """owner: the caption must hold ALL the information of the news (a date, ages, a percentage were missing)"""
    ART = ("മഞ്ചേരി, ഒക്ടോ.29: മഞ്ചേരി ഭാഗത്ത് തുടർച്ചയായി ബൈക്കുകൾ മോഷണം പോയിരുന്നു. "
           "ഇതിനിടെ കഴിഞ്ഞ 17ന് പയ്യനാട് സ്വദേശി മുഹമ്മദിന്റെ ബൈക്ക് മോഷണം പോയി; ആ മോഷണത്തിലും യുവാവിന് പങ്കുണ്ടായിരുന്നു. "
           "ബൈക്ക് മോഷണക്കേസിൽ 23 വയസ്സുള്ള യുവാവിനെ പോലീസ് അറസ്റ്റ് ചെയ്തു. "
           "മലപ്പുറത്ത് നവം.1ന് പിഎസ്സി പരീക്ഷ: 14,199 പേർ എഴുതും")      # the last line is another headline on the same page
    STORY = "മഞ്ചേരിയിൽ ബൈക്ക് മോഷണം: യുവാവ് അറസ്റ്റിൽ. പയ്യനാട് സ്വദേശി മുഹമ്മദിന്റെ ബൈക്ക് മോഷണം പോയി. പോലീസ് യുവാവിനെ അറസ്റ്റ് ചെയ്തു."

    def test_missing_fact_found(self):
        import validate
        miss = validate.caption_missing_facts("📰 പൂർണ വിവരം:\nബൈക്ക് മോഷണക്കേസിൽ 23 വയസ്സുള്ള യുവാവ് അറസ്റ്റിൽ.", self.ART, self.STORY)
        self.assertTrue(any(m.startswith("17") for m in miss), miss)

    def test_other_headlines_and_dateline_ignored(self):
        import validate
        cap = "📰 പൂർണ വിവരം:\nമഞ്ചേരിയിൽ 17ന് പയ്യനാട് സ്വദേശിയുടെ ബൈക്ക് മോഷണം പോയി; ബൈക്ക് മോഷണക്കേസിൽ 23 വയസ്സുള്ള യുവാവ് അറസ്റ്റിൽ."
        self.assertEqual([], validate.caption_missing_facts(cap, self.ART, self.STORY))


class RepairNotLose(unittest.TestCase):
    """owner: stories were held back for a card cut mid-phrase / a sentence said twice - repair them, never lose the news"""

    def test_card_and_repeat_repaired(self):
        import known_issues
        row = {"headline_ml": "പരിശീലന ക്ലാസ്", "caption": "📰 പൂർണ വിവരം:\nവിവരം ഇവിടെ.",
               "reel_script": "ഇന്ന് പരിശീലന ക്ലാസ് ആരംഭിച്ചു. ഇന്ന് പരിശീലന ക്ലാസ് ആരംഭിച്ചു. വിദ്യാർഥികൾ പങ്കെടുത്തു.",
               "slides_spec": json.dumps({"slides": [{"lines": ["വിദ്യാർഥികൾക്കുള്ള സൗജന്യ പരിശീലന ക്ലാസുകളുടെ", "നാളെ തുടക്കം"]}]}, ensure_ascii=False)}
        self.assertTrue(known_issues.problems(row))      # the example really has the issues
        fixed = known_issues.repair(row)
        self.assertEqual([], known_issues.problems(fixed))
        self.assertEqual(1, fixed["reel_script"].count("ഇന്ന് പരിശീലന ക്ലാസ് ആരംഭിച്ചു"))
        self.assertIn("വിദ്യാർഥികൾ പങ്കെടുത്തു", fixed["reel_script"])
        post.ALL_ROWS = []
        self.assertNotIn("known issue", post.skip_reason(dict(row, story_id="MP-T", source="", published="", researched="", review="Auto")))


class CodeBugsNeverRepeat(unittest.TestCase):
    """owner: a bug fixed once must never come back. Every posting job once crashed: 'verify' was used in clean_caption without
    being imported. (1) No file may use a name that is not defined (checked by pyflakes on GitHub). (2) The caption and posting-check
    steps are run end to end on a sample story, so a crash there fails the tests, not the live posting."""

    def test_no_undefined_names(self):
        try:
            from pyflakes import api, reporter
        except ImportError:
            self.skipTest("pyflakes is installed by tests.yml on GitHub")
        import io, glob
        out, err = io.StringIO(), io.StringIO()
        for f in sorted(glob.glob(str(ROOT / "poster" / "*.py")) + glob.glob(str(ROOT / "research_free" / "*.py")) + glob.glob(str(ROOT / "reel" / "*.py"))):
            api.checkPath(f, reporter.Reporter(out, err))
        bad = [l for l in out.getvalue().splitlines() if "undefined name" in l or "referenced before assignment" in l]
        self.assertEqual([], bad)

    def test_posting_text_steps_run(self):
        post.ALL_ROWS = []
        row = {"story_id": "MP-T", "headline_ml": "പരീക്ഷണ വാർത്ത: റോഡ് അപകടം", "headline_en": "Road accident test", "category": "Accident",
               "location": "", "source": "", "published": "", "researched": "", "notes": "", "batch": "", "review": "Auto", "post_to": "",
               "caption": "🚗 പരീക്ഷണ വാർത്ത\n\n📰 പൂർണ വിവരം:\nറോഡിൽ അപകടം ഉണ്ടായി.\n\n#Test",
               "reel_script": "റോഡിൽ അപകടം ഉണ്ടായി. കൂടുതൽ വാർത്തകൾക്ക് ഫോളോ ചെയ്യൂ.", "slides_spec": json.dumps({"v": 3, "slides": []})}
        post.clean_caption(dict(row))
        post.final_caption(dict(row))
        post.check_text(dict(row), json.loads(row["slides_spec"]))
        post.skip_reason(dict(row))


class PortLeftovers(unittest.TestCase):
    """the port from the Namakkal (Tamil) pipeline: no Tamil text, Namakkal pages or old Sheet columns left in the code that runs"""

    def test_no_tamil_or_namakkal_in_code(self):
        import glob
        files = [f for d in ("poster", "research_free", "reel", "kit", "tools") for f in glob.glob(str(ROOT / d / "*.py"))]
        files += [str(ROOT / "apps_script" / "Code.gs"), str(ROOT / "poster" / "config.json")]
        for f in files:
            src = Path(f).read_text(encoding="utf-8")
            if not f.endswith("verify.py"):      # verify.py maps stray Tamil letters to Malayalam on purpose
                self.assertNotRegex(src, "[஀-௿]", f)
            for old in ("headline_ta", "namakkal_link", "rasipuram_link", "IG_TOKEN_NAMAKKAL", "IG_TOKEN_RASIPURAM", "tamilcheck", "tamilnum"):
                self.assertNotIn(old, src, f"{old} in {f}")


if __name__ == "__main__":
    unittest.main()
