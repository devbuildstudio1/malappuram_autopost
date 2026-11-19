"""Design themes shared by the photo carousel (render_photo.py), the follow slide (render_v2.py) and the reel (reel4.py).

Pick one with poster/config.json "design_style" (or env DESIGN_STYLE for a test render):
  A  = the original navy / red / yellow look (no overrides)
  D  = Newsprint: cream paper panels, black ink headlines, red accents (calm, editorial, trusted)
  E  = Night Teal: dark teal glass, lime + teal accents (modern, soft)
  F  = Lower Third: TV-style black bands, red tags, photo-forward (urgent, broadcast)
Each theme is CSS appended after the base CSS, so the layout, auto-fit and timing code stay the same.
"""
import json, os
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "poster" / "config.json"


def current():
    s = os.environ.get("DESIGN_STYLE")
    if not s:
        try:
            s = json.loads(CONFIG.read_text()).get("design_style")
        except Exception:
            s = None
    return (s or "A").upper()


def css(part, style=None):
    """part: photo | follow | reel"""
    return THEMES.get((style or current()).upper(), {}).get(part, "")


# the photo cover's "പൂർണ വിവരം" button is styled inline; this selector reaches it
BTN = '.layer > div[style*="FFCC1F"]'

THEMES = {
    "A": {},

    # ---------------------------------------------------------------- D: Newsprint
    "D": {
        "photo": """
:root{--paper:#F6F1E7;--ink:#141414;--red:#D7261E;--rule:#DCD3C2}
.date{background:var(--ink);color:#fff;border:0;border-radius:4px;box-shadow:none;font-size:30px}
.date .ic{color:#fff}
/* cover: photo on top, paper panel below */
.photo.full{bottom:auto;height:740px}
.shade{top:700px;background:var(--paper);border-top:12px solid var(--red)}
.cover-cat{top:740px;left:40px;background:transparent;color:var(--red);clip-path:none;transform:none;padding:0;font:800 44px 'BT','NST';letter-spacing:.5px}
.cover-cat::after{content:"";display:block;width:90px;height:6px;background:var(--red);margin-top:6px}
.cover-h1{top:815px;height:270px;color:var(--ink);text-shadow:none;font-size:92px}
.cover-h2{top:1095px;color:var(--red);text-shadow:none;font-size:68px}
.cover-loc{color:var(--ink);border-top:3px solid var(--ink);font-size:34px}
.cover-loc .ic{color:var(--red)}
""" + BTN + """{background:var(--ink)!important;color:#fff!important;border-radius:4px!important;box-shadow:none!important}
/* detail: photo strip on top, paper below */
.top-shade{top:400px;height:950px;background:var(--paper);border-top:12px solid var(--red)}
.top-img{height:420px}
.cat2{top:320px;left:40px;background:var(--ink);transform:none;border-radius:4px;font-size:34px;padding:8px 24px 0}
.brush2{top:440px;background:transparent;color:var(--ink);transform:none;padding:0 0 10px;left:40px;border-bottom:4px solid var(--ink);border-radius:0}
.brush2 h2{font-size:60px}
.pts{top:560px;gap:14px}
.pt{background:#fff;border:2px solid var(--rule);border-radius:6px;padding:14px 22px 10px}
.pt .dot{background:transparent;color:var(--red);font:900 60px/58px 'BT','CT';flex-basis:50px}
.pt .tx{color:var(--ink)}
.pt .tx b{color:var(--red)}
.ai{background:rgba(20,20,20,.75)}
""",
        "follow": """
:root{--paper:#F6F1E7;--ink:#141414;--red:#D7261E}
.bg{background:var(--paper)!important}
.bg::after{background-image:none!important}
.slash{display:none}
.date{background:var(--ink);border:0;border-radius:4px;box-shadow:none}
.brush{background:transparent;color:var(--ink);clip-path:none;transform:none;padding-left:16px}
.underline{background:var(--red);transform:none;height:8px;border-radius:0}
.follow{background:var(--red);border-radius:8px}
.follow .fy{background:#fff;color:var(--ink);border-radius:6px}
.row{border-radius:8px;box-shadow:none;border:2px solid #DCD3C2}
.row[style*="yellow"]{background:var(--ink)!important;border-color:var(--ink)}
.row[style*="yellow"] .t1{color:#fff}
.tile{border-radius:8px;background:#EFE8DA}
.t1{color:var(--ink)}
""",
        "reel": """
/* SPLIT SCREEN: moving photo in the top half, a paper news panel below (red rule between).
   Photo half: header, logo, opening headline, then the fact cards as lower-thirds.
   Panel half: place, the short headline, the spoken captions in big black type. */
:root{--paper:#F6F1E7;--ink:#141414;--yellow:#F6F1E7;--split:1010px}
body{background:var(--paper)}
#stage{height:var(--split);bottom:auto}
.pic{height:var(--split)}
#shade{height:var(--split);bottom:auto;background:linear-gradient(180deg,rgba(0,0,0,.62) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 50%,rgba(0,0,0,.72) 100%)}
#shade::after{content:"";position:absolute;left:0;right:0;bottom:-14px;height:14px;background:var(--acc)}
#hdr .tag{border-radius:3px}
/* panel */
#pin{top:1060px;left:48px;background:transparent;box-shadow:none;color:var(--ink);padding:0;font-size:36px;border-radius:0}
#pin .ic{color:var(--acc)}
#mini{top:1130px;left:48px;right:130px;color:var(--ink);text-shadow:none;border-left:0;padding:0 0 14px;border-bottom:4px solid var(--ink);font:800 48px/1.25 'BT','NST'}
#cap{top:1280px;height:300px;left:48px;right:130px}
.ph{-webkit-text-stroke:0;text-shadow:none;color:var(--ink);font-size:66px;line-height:1.28;top:0;bottom:auto}
.ph span.on{color:var(--acc)}
/* photo half: opening headline, then fact cards as lower-thirds */
#hook{top:auto;bottom:calc(1920px - var(--split) + 40px);left:48px;right:48px}
#hook .h1{-webkit-text-stroke:0;color:#fff;font-size:92px;text-shadow:0 4px 24px rgba(0,0,0,.8)}
#hook .h2{background:var(--acc);color:#fff;border-radius:0;box-shadow:none;margin-top:14px}
.card{top:auto;bottom:calc(1920px - var(--split) + 40px);left:0;width:940px;border-radius:0;background:var(--ink);box-shadow:0 14px 40px rgba(0,0,0,.5)}
.card .ico{background:var(--acc);width:130px;font-size:62px}
.card .lb{color:#fff;opacity:.65}
.card .vl{color:#fff;font-size:48px}
#sum{top:290px;border-radius:0;background:var(--paper);box-shadow:0 20px 60px rgba(0,0,0,.6)}
#sum .st{background:var(--ink)}
#sum .row{border-top:2px solid #DCD3C2}
#sum .row .v{color:var(--ink)}
#end{background:var(--paper)}
#end .e1{color:var(--ink)}
#end .e2,#end .fol{border-radius:0}
#end .e4{background:var(--ink)}
#end .e3{color:var(--acc)}
""",
    },

    # ---------------------------------------------------------------- E: Night Teal
    "E": {
        "photo": """
:root{--deep:#04161A;--teal:#19C3B1;--lime:#D4FF3A}
.date{background:rgba(4,22,26,.72);border:2px solid var(--teal);border-radius:999px;box-shadow:none;backdrop-filter:blur(8px)}
.date .ic{color:var(--lime)}
.shade{background:linear-gradient(180deg,rgba(4,22,26,.5) 0%,rgba(4,22,26,0) 22%,rgba(4,22,26,0) 36%,rgba(4,22,26,.9) 64%,var(--deep) 100%)}
.cover-cat{background:var(--lime);color:var(--deep);clip-path:none;transform:none;border-radius:999px;font-size:42px;padding:10px 34px 2px}
.cover-h1{text-shadow:0 4px 30px rgba(0,0,0,.6)}
.cover-h2{color:var(--teal);text-shadow:0 4px 24px rgba(0,0,0,.6)}
.cover-loc{border-top:2px solid rgba(25,195,177,.5)}
.cover-loc .ic{color:var(--teal)}
""" + BTN + """{background:var(--lime)!important;color:var(--deep)!important}
.top-shade{background:linear-gradient(180deg,rgba(4,22,26,.5) 0%,rgba(4,22,26,0) 20%,rgba(4,22,26,0) 28%,rgba(4,22,26,.85) 46%,rgba(4,22,26,.97) 60%,var(--deep) 100%)}
.cat2{background:var(--lime);color:var(--deep);transform:none;border-radius:999px;font-size:34px;padding:8px 26px 0}
.brush2{background:transparent;color:#fff;transform:none;border-left:12px solid var(--teal);border-radius:0;padding:4px 0 0 24px}
.pt{background:rgba(25,195,177,.08);border:2px solid rgba(25,195,177,.35);border-radius:28px}
.pt .dot{background:var(--teal);color:var(--deep)}
.pt .tx b{color:var(--lime)}
""",
        "follow": """
:root{--deep:#04161A;--teal:#19C3B1;--lime:#D4FF3A}
.bg{background:radial-gradient(900px 700px at 90% 0%,#0B3A3E 0%,transparent 60%),radial-gradient(900px 700px at 0% 100%,#082A2E 0%,transparent 60%),var(--deep)!important}
.slash{background:var(--teal)}
.slash.s2{background:var(--lime)}
.date{background:rgba(4,22,26,.72);border:2px solid var(--teal);border-radius:999px}
.brush{background:var(--lime);color:var(--deep);clip-path:none;border-radius:20px;transform:none}
.underline{display:none}
.follow{background:linear-gradient(140deg,#0E6E66,#19C3B1);border-radius:36px}
.follow .fy{background:var(--lime);color:var(--deep);border-radius:999px}
.row{background:rgba(255,255,255,.06);border:2px solid rgba(25,195,177,.4);box-shadow:none}
.row[style*="yellow"]{background:var(--lime)!important}
.t1{color:#fff}.t2{color:#A9C6C4}
.row[style*="yellow"] .t1{color:var(--deep)}
.tile{background:rgba(25,195,177,.15);color:var(--teal)}
.tile.red{color:var(--lime)}
""",
        "reel": """
:root{--deep:#04161A;--teal:#19C3B1;--yellow:#D4FF3A}
#shade{background:linear-gradient(180deg,rgba(4,22,26,.75) 0%,rgba(4,22,26,0) 26%,rgba(4,22,26,0) 52%,rgba(4,22,26,.55) 72%,rgba(4,22,26,.9) 100%)}
#hdr .tag{background:var(--teal);color:var(--deep);border-radius:999px}
#pin{background:rgba(4,22,26,.7);color:#fff;border:2px solid var(--teal);backdrop-filter:blur(14px)}
#pin .ic{color:var(--yellow)}
#hook .h1{-webkit-text-stroke:0;text-shadow:0 6px 40px rgba(0,0,0,.9),0 2px 6px rgba(0,0,0,.8)}
#hook .h2{background:var(--yellow);color:var(--deep);border-radius:999px;padding:10px 40px 0}
#mini{border-left-color:var(--teal)}
.card{background:rgba(4,22,26,.72);border:2px solid rgba(25,195,177,.6);backdrop-filter:blur(18px);border-radius:34px}
.card .ico{background:transparent;color:var(--yellow)}
.card .lb{color:var(--teal)}
.card .vl{color:#fff}
.ph{-webkit-text-stroke:0;text-shadow:0 4px 24px rgba(0,0,0,.95),0 2px 4px rgba(0,0,0,.9)}
#sum{background:rgba(4,22,26,.82);border:2px solid rgba(25,195,177,.6);backdrop-filter:blur(20px);border-radius:34px}
#sum .st{background:transparent;color:var(--yellow);border-bottom:2px solid rgba(25,195,177,.4)}
#sum .row{border-top:1px solid rgba(255,255,255,.1)}
#sum .row .ic{color:var(--teal)}
#sum .row .l{color:#A9C6C4}
#sum .row .v{color:#fff}
#end{background:rgba(4,22,26,.8)}
#end img{border-color:var(--teal)}
#end .e2,#end .fol{background:var(--teal);color:var(--deep)}
#end .e4{border:2px solid rgba(25,195,177,.5)}
""",
    },

    # ---------------------------------------------------------------- F: Lower Third
    "F": {
        "photo": """
:root{--red:#E10600;--blk:#0B0B0B}
.date{background:#fff;color:var(--blk);border:0;border-radius:0;box-shadow:0 6px 18px rgba(0,0,0,.35);left:0;padding-left:40px}
.date .ic{color:var(--red)}
.shade{background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 20%,rgba(0,0,0,0) 44%,rgba(0,0,0,.85) 60%,var(--blk) 72%)}
.cover-cat{left:0;top:720px;background:var(--red);clip-path:none;transform:none;padding:12px 40px 2px 40px;font-size:46px}
.cover-h1{top:820px;height:280px;text-shadow:none;font-size:96px}
.cover-h2{top:1110px;right:auto;width:fit-content;background:#fff;color:var(--blk);text-shadow:none;padding:8px 24px 0;font-size:64px}
.cover-loc{border-top:0;background:var(--red);left:0;right:0;bottom:0;padding:20px 40px 14px;font-size:36px}
.cover-loc .ic{color:#fff}
""" + BTN + """{background:#fff!important;color:var(--blk)!important;border-radius:0!important;bottom:16px!important;padding:12px 22px 8px!important;box-shadow:none!important}
.top-shade{background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 18%,rgba(0,0,0,0) 26%,rgba(0,0,0,.85) 42%,var(--blk) 54%)}
.cat2{left:0;background:var(--red);transform:none;border-radius:0;padding:10px 30px 2px 36px}
.brush2{left:0;background:#fff;color:var(--blk);transform:none;border-radius:0;padding:12px 36px 4px 36px}
.pt{background:transparent;border:0;border-left:8px solid var(--red);border-radius:0;padding:6px 0 2px 22px}
.pt .dot{background:var(--red);color:#fff;border-radius:0}
.pt .tx b{color:#FF4A3D}
""",
        "follow": """
:root{--red:#E10600;--blk:#0B0B0B}
.bg{background:var(--blk)!important}
.bg::after{background-image:repeating-linear-gradient(0deg,rgba(255,255,255,.03) 0 2px,transparent 2px 6px)!important;background-size:auto!important}
.slash{background:var(--red)}
.slash.s2{background:#fff}
.date{background:#fff;color:var(--blk);border:0;border-radius:0}
.date .ic{color:var(--red)}
.brush{background:#fff;color:var(--blk);clip-path:none;transform:none;left:0;padding-left:40px}
.underline{background:var(--red);left:0;transform:none;border-radius:0}
.follow{background:var(--red);border-radius:0}
.follow .fy{background:#fff;color:var(--blk);border-radius:0}
.row{border-radius:0}
.row[style*="yellow"]{background:var(--red)!important}
.row[style*="yellow"] .t1{color:#fff}
.tile{border-radius:0}
""",
        "reel": """
:root{--blk:#0B0B0B;--yellow:#FFFFFF}
#hdr{background:var(--blk);left:0;padding:12px 30px 12px 48px}
#hdr .tag{border-radius:0}
#pin{left:0;border-radius:0;background:var(--acc);color:#fff;padding-left:48px;box-shadow:none}
#pin .ic{color:#fff}
#hook{left:0;right:0}
#hook .h1{-webkit-text-stroke:0;background:var(--blk);padding:22px 48px 10px;text-shadow:none;font-size:94px}
#hook .h2{margin:0 0 0 48px;background:var(--acc);color:#fff;border-radius:0;box-shadow:none}
#mini{left:0;right:0;background:var(--blk);border-left:0;border-bottom:6px solid var(--acc);padding:14px 48px 6px;text-shadow:none;font-size:42px}
.card{left:0;border-radius:0;background:var(--blk);width:900px}
.card .vl{color:#fff}
.card .lb{color:#fff;opacity:.7}
#cap{left:0;right:0}
.ph{-webkit-text-stroke:0;text-shadow:none;background:var(--blk);padding:14px 48px 4px;border-bottom:8px solid var(--acc);font-size:62px}
.ph span.on{color:#fff;background:var(--acc);padding:0 8px}
#sum{left:0;right:0;border-radius:0;background:var(--blk)}
#sum .row{border-top:1px solid rgba(255,255,255,.14)}
#sum .row .l{color:#9A9A9A}
#sum .row .v{color:#fff}
#end{background:rgba(11,11,11,.88)}
#end .e2,#end .fol,#end .send{border-radius:0}
#end .e3{color:#fff}
""",
    },
}
