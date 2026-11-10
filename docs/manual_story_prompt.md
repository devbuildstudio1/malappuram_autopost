# Manual story → e-mail (use when automatic collecting is PAUSED)

## 1. Pause / start automatic collecting
GitHub → repository **malappuram360-autopost** → **Actions** → **collect-switch** → **Run workflow** → choose
`pause` (automatic collecting/writing stops, posting continues) or `start` (automatic collecting again). Same page on the phone.

## 2. Make the news with another Claude account
Paste the prompt below into that Claude (with web search ON), add the news text / link at the end.
Claude gives ONE JSON. Make the images (ChatGPT, 4 images, 9:16, one per slide + 1).

## 3. Send ONE e-mail to the bridge Gmail (`OWNER_EMAIL` in `apps_script/Code.gs`) from your allowed address
- Subject: `NEWS360 STORY` (anything after it is fine)
- Body: paste the JSON (or attach it as story.json)
- Attach the images (png/jpg) or one zip. One story per e-mail. (Several stories in one e-mail: `{"stories":[...]}` and name the images S1_1.png, S1_2.png, S2_1.png …)
- Within ~5 minutes you get **[NEWS360 STORY RECEIVED]**: ADDED MP-xx, or the exact problems / DUPLICATE warning. Then it is posted automatically
  (Instagram recent-captions duplicate check + source fact check run first; an already posted news is never posted again).
- The sender must be listed in Script property `ALLOWED_SENDERS` (your friend's/other mail) or be the owner address.

## Prompt for the other Claude
```
You write Malayalam local-news posts for the Instagram pages "Malappuram 360" / "Manjeri 360" (Malappuram district, Kerala).
Use ONLY facts from the news below (search the web to confirm). Never invent a name, number, place or cause. If a fact is unclear, leave it out.
Write ONE JSON object only (no explanation) with exactly these keys:
{
 "malayalam_headline": "...",        // clear Malayalam headline, full place names (പെരിന്തൽമണ്ണ, തിരൂരങ്ങാടി - never short forms)
 "english_headline": "...",
 "category": "...",                  // Malayalam, e.g. വൈദ്യുതി മുടക്കം, അപകടം, ഭരണം
 "location": "place, taluk, Malappuram district",
 "importance": "High|Medium|Low",
 "post_to": "Manjeri 360 (collab: Malappuram 360)",   // Manjeri-area news (Manjeri, Pandikkad, Edavanna, Areekode ...). District-wide news (Collector / government / jobs): "Malappuram 360 (collab: Manjeri 360)". Other district places: "Malappuram 360"
 "source": "https://link-of-the-news-article",          // used only for the fact check, never shown
 "slides_spec": {"v":3,"cat":"...","loc":"short place","hl1":"max 40 chars","hl2":"max 28 chars",
   "slides":[{"title":"max 18 chars","lines":["2-3 short lines, each max 60 chars; <b>bold</b> allowed for key facts"]}]},   // 3 or 4 slides: who/what/when/where/why/how
 "reel_script": "...",               // friendly spoken Malayalam (like a local telling a neighbour, no dialect spellings; serious news calm), 60-120 Malayalam words, 7-10 sentences with every detail. NO digits and NO English letters (write numbers in Malayalam words: പത്തര മണി, അറുപത്തഞ്ച് വയസ്സ്). Strong hook in the first sentence (no greeting), short sentences, plain words, covers who-what-when-where-why-how, ends with exactly: കൂടുതൽ വാർത്തകൾക്ക് മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ.
 "caption": "..."                    // emoji heading, 3-5 short lines with facts, then a line 📍 place | date, then 5 hashtags, last line: പ്രാദേശിക വാർത്തകൾക്ക് Follow ചെയ്യൂ 🙏
}
Rules: no newspaper/TV/website names or links in any text field except "source"; no "comment below" lines; readable plain Malayalam
with everyday Kerala words (ബസ്, ബൈക്ക്, പോലീസ്, കളക്ടർ, കെഎസ്ഇബി); dates always with the month.
NEWS:
<paste the news text or link here>
```
(`tamil_headline` is still accepted as an old name for `malayalam_headline`.)


---
# READY REEL (video + caption already made) - post as it is
E-mail to the bridge Gmail, subject `NEWS360 REEL`, attach ONE zip containing ONE `.md` (the caption) and ONE video (`.mp4`).
Optional first line of the .md: `PAGE: malappuram` (default) | `PAGE: manjeri` | `PAGE: both`.
Within ~5 minutes: **[NEWS360 REEL RECEIVED]** ADDED MP-xx (or DUPLICATE / the problem). Just before posting, the page's recent Instagram captions
are read: if the same news is already there it is NOT posted (the Sheet row says so). Otherwise the video is posted exactly as it is, with your caption
(standard rule: max 5 hashtags, #Malappuram360 / #Manjeri360 added, AI line).
