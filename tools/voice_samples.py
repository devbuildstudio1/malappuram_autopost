"""Makes one sample file per available Malayalam voice, same news text, so people can compare. Output: samples/voices/*.mp3"""
import asyncio, json, os, subprocess, sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples" / "voices"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "reel"))

TEXT = ("മഞ്ചേരിക്കടുത്ത് കാർ ഇടിച്ച് സ്കൂട്ടർ യാത്രക്കാരനായ കർഷകൻ ഗോവിന്ദൻ മരിച്ചു. "
        "പാണ്ടിക്കാട് റോഡിലെ ഹോട്ടലിന് സമീപമാണ് അപകടം നടന്നത്, ശബരിമല ദർശനം കഴിഞ്ഞ് മടങ്ങിയ ആറുപേർ കാറിലുണ്ടായിരുന്നു. "
        "മറ്റൊരു അപകടത്തിൽ, തിരിച്ചറിയാത്ത കാർ ഇടിച്ച് ഒരു വയോധികയ്ക്ക് ഗുരുതരമായി പരിക്കേറ്റു. "
        "നിർത്താതെ പോയ കാറിനായി മഞ്ചേരി പോലീസ് അന്വേഷണം തുടങ്ങി. "
        "കൂടുതൽ വാർത്തകൾക്ക് മലപ്പുറം ത്രീ സിക്സ്റ്റി പേജ് ഫോളോ ചെയ്യൂ.")
report = []


def mp3(src, name):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", "24000", "-b:a", "64k", str(OUT / name)], check=True)


def guard(label, fn):
    try:
        fn(); report.append(f"ok   {label}")
    except Exception as e:
        report.append(f"FAIL {label}: {str(e)[:150]}"); traceback.print_exc()


EDGE = [("ml-IN-MidhunNeural", "പുരുഷൻ (ഇന്ത്യ)"), ("ml-IN-SobhanaNeural", "സ്ത്രീ (ഇന്ത്യ)")]


def google(v):
    """Google Cloud TTS (Chirp 3 HD), needs GOOGLE_TTS_API_KEY; uses the free allowance only (a few hundred characters)"""
    import base64, requests
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_TTS_API_KEY not set")
    r = requests.post("https://texttospeech.googleapis.com/v1/text:synthesize", params={"key": key}, timeout=60,
                      json={"input": {"text": TEXT}, "voice": {"languageCode": "ml-IN", "name": v}, "audioConfig": {"audioEncoding": "MP3"}})
    r.raise_for_status()
    (OUT / f"google_{v}.mp3").write_bytes(base64.b64decode(r.json()["audioContent"]))


def edge(v):
    import edge_tts
    async def go():
        await edge_tts.Communicate(TEXT, v, rate="+5%").save(str(OUT / f"edge_{v}.mp3"))
    asyncio.run(go())


for v, _ in EDGE:
    guard("edge-tts " + v, lambda v=v: edge(v))
for v in ("ml-IN-Chirp3-HD-Charon", "ml-IN-Chirp3-HD-Aoede"):
    guard("Google " + v, lambda v=v: google(v))


def gtts():
    from gtts import gTTS
    gTTS(TEXT, lang="ml").save(str(OUT / "google_gtts.mp3"))
guard("Google gTTS", gtts)


def mms():
    import torch, scipy.io.wavfile as w
    from transformers import VitsModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained("facebook/mms-tts-mal"); m = VitsModel.from_pretrained("facebook/mms-tts-mal")
    with torch.no_grad():
        y = m(**tok(TEXT, return_tensors="pt")).waveform[0].numpy()
    w.write("/tmp/mms.wav", m.config.sampling_rate, y); mp3("/tmp/mms.wav", "meta_mms.mp3")
guard("Meta MMS", mms)


def indic(g):
    import tts
    Path("/tmp/l.json").write_text(json.dumps([TEXT], ensure_ascii=False))
    tts.main("/tmp/l.json", f"/tmp/ind_{g}", g)
    mp3(f"/tmp/ind_{g}/line0.wav", f"indic_tts_{g}_CURRENT.mp3")
for g in ("female", "male"):
    guard("AI4Bharat Indic-TTS " + g, lambda g=g: indic(g))

(OUT / "report.txt").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
