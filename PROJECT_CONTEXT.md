# malappuram360-autopost - project context

Automatic Malappuram-district (Kerala) news in Malayalam for Instagram pages **മലപ്പുറം 360** (@malappuram.360.official) and
**മഞ്ചേരി 360** (@manjeri.360), and for the website **malappuram360.workers.dev** (placeholder; website repo: a Malayalam copy of
news360-tn/namakkal360-web, not in this repo). Ported from news360-autopost (Namakkal 360, Tamil) on 30 Oct 2026.
Everything runs on GitHub Actions; the Google Sheet (through the Apps Script bridge) is the working store.

## How it works (end to end)

```
every 4 h   research_free.yml   collect news (Malayalam newspaper sites, Google/Bing News) -> open + check each article
                                 -> only Malappuram-district news of today/yesterday -> queue (research_free/archive/queue.json)
every 20 min write_stories.yml  write each queued news by priority (LLM chain) -> 3 AI images (cover FLUX dev, scenes FLUX schnell)
                                 -> story saved in the Sheet -> starts posting at once
every 5 min  post.yml           checks (Malappuram only, not stale, no duplicate, prime time) -> reel (reel/reel4.py) -> Instagram
                                 -> the posted story is sent to the website (poster/website.py)
daily        insights.yml       Instagram insights -> learned topic weights (writer priority)
```

## Rules the owner decided (keep them)

| Area | Rule |
|---|---|
| News scope | Only Malappuram-district news, published today or yesterday. Manjeri-area news (Manjeri, Pandikkad, Edavanna, Areekode, Kizhuparamba, Trikkalangode, Anakkayam, Pulpatta, Payyanad, Nellikuth, Kavanur, Eranad) -> Manjeri 360 (Malappuram 360 invited as collab); district-wide news -> Malappuram 360 (Manjeri 360 collab). Kozhikode, Palakkad, Thrissur, Wayanad, Nilgiris and state-wide news are skipped |
| Never miss news | Everything eligible is queued and written; duplicates and other-district news are skipped; nothing eligible is dropped |
| Posting time | Urgent news (power cut / KSEB notice, accident, rain warning, Collector/Govt notice, jobs, exams, today/tomorrow) posts at once. Other reels are made ahead and posted 09:00-12:00 / 18:00-21:30 IST; no reel waits more than 12 h (`poster/config.json` `prime_time`) |
| Instagram limit | 50 posts per page per 24 h; no internal cap below that |
| Voice | Google Chirp 3 HD **`ml-IN-Chirp3-HD-Charon`** for every reel, ONLY inside Google's free allowance (code stops at 700,000 characters/month), then edge-tts **`ml-IN-MidhunNeural`**. Never paid |
| Watch to the end (owner 10 Nov) | Reel 45-75 words (~25-40 s), hook = place + most striking fact in <=8 words, key answer kept for the second half, share line ("... അയച്ചുകൊടുക്കണേ") before the follow line for useful news (not death/crime/court/accident), short ending (0.35 s beat, "Follow Malappuram Three Sixty.") |
| Topics for followers (owner 11 Nov) | Queue order: power cuts > weather/holidays, water/road closures, strikes, health alerts, hotel inspections, prices > jobs > education, schemes/deadlines, local pride/viral > transport/civic > festivals > accidents > arrests. Not written at all: inaugurations, meetings, awards, tributes, party politics, court hearings, protests, proposals, tips/recipes, editorials (collect.py low_interest; poster/config.json selection.skip_low_interest=false turns it off). State-wide KSEB power restriction / load shedding news is posted as Malappuram news (allnews.kerala_power_alert); more power-cut searches for every big town |
| Reel opening | Striking fact spoken first with the big headline; no double reading when the one-line story already says it; then one-line story, then full news |
| Reel language | Voice (reel_script): friendly spoken Malayalam, like a local telling a neighbour - no dialect spellings, serious news calm (owner choice 10 Nov 2026). Caption and slides: formal written Malayalam; everyday Kerala words in voice, subtitles and cards (ബസ്, ബൈക്ക്, പോലീസ്, കളക്ടർ, കെഎസ്ഇബി, കെഎസ്ആർടിസി ...); dates always with the month |
| Follow line | Reel ends with: കൂടുതൽ വാർത്തകൾക്ക് മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ. (Manjeri page: മഞ്ചേരി ത്രീ സിക്സ്റ്റി) |
| Images | New AI images for every story, made from the story's own scenes; older pictures are never reused |
| Text | No `<b>` marks on screen; website never shows long dashes |
| Proofread | The last Malayalam proofread only fixes small spelling/sandhi mistakes of whole words; never page/place names, the follow line, English lines, words the article itself uses, or anything that changes meaning |
| Costs | Free tiers first (Gemini/Groq/NVIDIA/Cloudflare/Mistral...); Claude Haiku only as backup; FAL images ~₹2.7 per reel |
| Privacy | Personal project: commits only as **news360-tn**; no office account, office email or AI-assistant co-author lines in commits; files only in the owner's personal folder |

## Main files

| Path | What |
|---|---|
| `research_free/collect.py`, `allnews.py`, `sources.py`, `sources.json` | collection, district checks (`DISTRICT_WORDS`, `TOWN_AREA`, `TOWN_NEAR`), queue, writer, images |
| `research_free/rules.md`, `examples.json`, `names.py` | Malayalam writing rules and spoken-word fixes |
| `poster/post.py` | posting checks (`not_in_district`), prime time, Instagram publishing |
| `poster/freshness.py` | stale / duplicate / power-cut timing rules |
| `poster/mlcheck.py` | Malayalam text check / proofread |
| `poster/website.py` | sends posted stories to the website (+ English version); `backfill` for old stories |
| `poster/config.json` | voice, prime time, hashtags, location IDs, design switches |
| `reel/reel4.py`, `reel/mlnum.py`, `reel/tts.py` | reel renderer (Malayalam fonts, voice, numbers spoken in Malayalam) |
| `kit/` | carousel renderer, logos (`logo_malappuram.png`, `logo_manjeri.png`) |
| `apps_script/Code.gs` | Google Sheet bridge (redeploy in Apps Script after changes). Story ids `MP-1`, `MP-2` ... |
| `tests/test_regressions.py` | regression tests (run before every push) |

## Placeholders the owner must fill before going live

| Where | What |
|---|---|
| `apps_script/Code.gs` | `SHEET_ID`, `ROOT_FOLDER_ID`, `OWNER_EMAIL`, `CLOUD_NAME`, `UPLOAD_PRESET`, `COLLAB_USERNAME` (if handle differs) |
| Apps Script properties | `IG_TOKEN_MALAPPURAM`, `IG_TOKEN_MANJERI`, optional `ALLOWED_SENDERS` |
| `poster/config.json` | Instagram handles, Facebook place IDs in `locations` |
| `poster/website.py` | website address if not `malappuram360.workers.dev` |
| GitHub secrets | all listed below |
| repository root | `LIVE` file - create LAST, after a successful dry run |

## Secrets (GitHub -> Settings -> Secrets -> Actions; values never in the repo)

BRIDGE_URL, BRIDGE_KEY, GEMINI_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY, MISTRAL_API_KEY, GH_MODELS_TOKEN, CLOUDFLARE_API_TOKEN,
CLOUDFLARE_ACCOUNT_ID, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, FAL_KEY, CLOUDINARY_CLOUD, CLOUDINARY_PRESET, GOOGLE_TTS_API_KEY,
WEBSITE_INGEST_KEY. Local copies live only in `.env` (git-ignored).

## Run and check

```
python3 -m unittest discover -s tests        # regression tests (also run by tests.yml on every code push)
python3 poster/website.py backfill --from MP-1   # (Actions: website-backfill) resend posted stories to the website
python3 tools/repost.py MP-158                   # (Actions: repost) post a reel again after it was removed from Instagram
```

## Recent changes
<!-- recent-changes:start (updated automatically by .github/workflows/context.yml - do not edit by hand) -->
| Date | Commit | Change |
|---|---|---|
| 2026-11-11 | `fd0cef8` | ig probe: optional public stats of other pages for comparison |
| 2026-11-11 | `4726c18` | ig probe output |
| 2026-11-10 | `7049ce1` | Heartbeat |
| 2026-11-10 | `e0b09e7` | Heartbeat |
| 2026-11-10 | `deb965c` | Heartbeat |
| 2026-11-10 | `8b3d928` | Remove temporary Claude key check |
| 2026-11-10 | `563589d` | Temporary check of the Claude key |
| 2026-11-10 | `321843f` | Remove temporary Claude key check |
| 2026-11-10 | `bbc9bd9` | Temporary check of the Claude key format |
| 2026-11-10 | `11dd9b6` | Record posts Instagram published despite a temporary error |
| 2026-11-10 | `e1490cf` | Shorter reels with a stronger hook and a share line |
| 2026-11-10 | `5cdf219` | Reel voice in friendly spoken Malayalam |
| 2026-11-09 | `ac92ddb` | Heartbeat |
<!-- recent-changes:end -->
