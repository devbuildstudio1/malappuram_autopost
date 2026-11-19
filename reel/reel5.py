"""മലപ്പുറം 360 / മഞ്ചേരി 360 — news reel v5: "phone notification" design.
Usage: python3 reel5.py spec.json out.mp4 [page]      (same spec, voice and timing as reel4.py; only the screen design differs)

Idea (owner 18 Nov 2026: a really different reel look):
- The story arrives like an alert on a phone: the headline drops in as one big notification from the page.
- After the opening it shrinks into a pinned notification at the top, so a viewer who joins late still knows the story.
- Every fact the voice reads drops in as a new notification on top of the stack; older ones slide down and fade (max 3 on screen).
- The last news sentence opens a grouped "പൂർണ വിവരം" notification with every key fact (people pause on it / screenshot it).
- Captions: big white phrases at the bottom of the safe zone, the spoken word on a coloured pill.
- End card: the page "app" card with Follow / Share action buttons.
Safe zone (y 150-1600, x 48-950) and the page logo top-right are kept from v4.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel as R
import reel4 as R4
from reel4 import E, card_for, accent_for
from digits import to_digits

CSS = R.ff("CT", "anek-malayalam", [700, 800]) + R.ff("NST", "noto-sans-malayalam", [600, 700, 800]) + R.ff("BT", "baloo-chettan-2", [800]) + """
:root{--acc:#E3151B;--ink:#111827;--muted:#6B7280;--card:rgba(255,255,255,.94);--glass:rgba(17,24,39,.55)}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
body{font-family:'NST','CT',sans-serif;color:#fff;position:relative}
.ic{width:1em;height:1em;display:block}
#stage{position:absolute;inset:0;overflow:hidden}
.pic{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;opacity:0;will-change:transform,filter}
#shade{position:absolute;inset:0;z-index:5;background:linear-gradient(180deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.15) 30%,rgba(0,0,0,.15) 55%,rgba(0,0,0,.6) 75%,rgba(0,0,0,.85) 100%)}
#flash{position:absolute;inset:0;z-index:7;background:#fff;opacity:0}
#plogo{position:absolute;right:48px;top:150px;width:112px;height:112px;border-radius:50%;border:4px solid #fff;z-index:30;box-shadow:0 8px 24px rgba(0,0,0,.5)}
/* top status pill */
#hdr{position:absolute;left:48px;top:160px;z-index:30;display:flex;align-items:center;gap:16px;background:var(--glass);backdrop-filter:blur(18px);
  border:2px solid rgba(255,255,255,.25);border-radius:999px;padding:12px 30px 8px 16px;font:800 34px/1 'NST','CT'}
#hdr .dot{width:22px;height:22px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 6px rgba(255,255,255,.18);margin-top:-4px}
#hdr .cat{color:#fff}
#hdr .sep{opacity:.5}
#hdr .dt{color:#E5E7EB;font-weight:700}
#pin{position:absolute;left:48px;top:236px;z-index:30;display:flex;align-items:center;gap:10px;font:800 34px/1.2 'NST','CT';color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.8)}
#pin .ic{color:var(--acc);font-size:34px;margin-top:-4px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.6))}
/* notification card (shared look) */
.nt{position:absolute;left:48px;width:900px;z-index:24;background:var(--card);backdrop-filter:blur(24px);color:var(--ink);border-radius:38px;
  box-shadow:0 22px 60px rgba(0,0,0,.45);padding:24px 30px 20px;opacity:0;will-change:transform,opacity}
.nt .top{display:flex;align-items:center;gap:14px;font:700 28px/1 'NST','CT';color:var(--muted)}
.nt .top img{width:46px;height:46px;border-radius:12px}
.nt .top .app{color:var(--ink);font-weight:800}
.nt .top .ago{margin-left:auto}
.nt .body{display:flex;gap:22px;align-items:center;margin-top:16px}
.nt .ico{flex:none;width:96px;height:96px;border-radius:26px;background:var(--acc);color:#fff;display:flex;align-items:center;justify-content:center;font-size:52px}
.nt .lb{font:800 30px/1.2 'NST','CT';color:var(--acc)}
.nt .vl{font:800 50px/1.25 'NST','CT';color:var(--ink)}
/* opening: the big headline notification */
#hook{top:560px;padding:30px 36px 30px}
#hook .h1{font:900 82px/1.16 'CT','NST';color:var(--ink);margin-top:20px}
#hook .h2{display:inline-block;margin-top:20px;background:var(--acc);color:#fff;font:900 62px/1.15 'CT','NST';padding:12px 28px 4px;border-radius:18px}
/* pinned headline after the opening */
#mini{top:300px;padding:18px 26px 14px;border-radius:30px}
#mini .vl{font:800 42px/1.25 'NST','CT';margin-top:10px}
#mini .top .ago{display:flex;align-items:center;gap:8px}
#mini .top .ago .ic{font-size:26px;color:var(--acc)}
/* fact stack */
.fc{top:520px}
/* grouped summary */
#sum{top:520px;padding:22px 30px 10px}
#sum .rw{display:flex;align-items:center;gap:20px;padding:14px 0 10px;border-top:2px solid #E5E7EB;opacity:0}
#sum .rw .ic{flex:none;font-size:40px;color:var(--acc);margin-top:-6px}
#sum .rw .l{flex:none;width:190px;font:800 28px/1.2 'NST','CT';color:var(--muted);overflow:hidden}
#sum .rw .v{font:800 36px/1.3 'NST','CT';color:var(--ink)}
#sum .ttl{font:900 46px/1.2 'CT','NST';margin:14px 0 10px}
/* captions */
#cap{position:absolute;left:48px;right:130px;top:1250px;height:300px;z-index:25}
.ph{position:absolute;left:0;right:0;bottom:0;font:800 68px/1.32 'CT','NST';color:#fff;opacity:0;text-shadow:0 4px 22px rgba(0,0,0,.95),0 2px 4px rgba(0,0,0,.9)}
.ph span{display:inline-block;margin-right:.22em;padding:0 10px;border-radius:14px}
.ph span.on{background:var(--acc);color:#fff;text-shadow:none}
/* end card: the page as an app card with action buttons */
#end{position:absolute;inset:0;z-index:40;opacity:0;display:flex;align-items:center;justify-content:center;padding:0 48px 300px;background:rgba(0,0,0,.45)}
#end .box{width:100%;background:var(--card);color:var(--ink);border-radius:46px;padding:44px 44px 40px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.6)}
#end img{width:200px;height:200px;border-radius:50%;border:6px solid #fff;box-shadow:0 10px 30px rgba(0,0,0,.25)}
#end .e1{font:900 64px/1.25 'CT','NST';margin-top:22px}
#end .e3{font:800 38px 'NST','CT';color:var(--muted);margin-top:8px}
#end .acts{display:flex;gap:22px;margin-top:34px}
#end .b{flex:1;display:flex;align-items:center;justify-content:center;gap:14px;border-radius:26px;padding:24px 10px 16px;font:900 46px 'CT','NST'}
#end .b .ic{font-size:44px;margin-top:-8px}
#end .b.f{background:var(--acc);color:#fff}
#end .b.s{background:#EEF0F4;color:var(--ink)}
#end .hd{font:800 34px 'NST','CT';color:var(--acc);margin-top:22px}
"""

ORDER = ["സ്ഥലം", "തീയതി", "സമയം", "എന്താണ് സംഭവിച്ചത്", "ആര്", "ഗുരുതര പരിക്ക്", "എത്ര പേർ", "പരിക്കേറ്റവർ", "തുക", "ചികിത്സ",
         "നടപടി", "ആവശ്യം", "ജനങ്ങളുടെ പരാതി", "പൊതുജന ശ്രദ്ധയ്ക്ക്", "പ്രധാന വിവരം"]
MUST = ["സ്ഥലം", "ചികിത്സ", "നടപടി", "പൊതുജന ശ്രദ്ധയ്ക്ക്", "തുക", "സമയം", "തീയതി"]


def summary_rows(spec, sents):
    best = {}
    for c in [{"icon": "location-dot", "label": "സ്ഥലം", "text": spec.get("location", "")}] + [card_for(s.get("card") or s.get("fact")) for s in sents] + list(spec.get("summary") or []):
        if c and c.get("text"):
            k = c["label"]
            if k not in best or len(c["text"]) > len(best[k]["text"]):
                best[k] = c
    keys = sorted(best, key=lambda k: (k not in MUST, ORDER.index(k) if k in ORDER else 99))[:6]
    return [best[k] for k in sorted(keys, key=lambda k: ORDER.index(k) if k in ORDER else 99)]


def build_html(spec, shots, sents, caps, hook_end, end_t, total, page):
    logo = f"file://{R.KIT.resolve() / page['logo']}"
    acc = accent_for(spec.get("cat", ""))
    name = E(page["name"])
    top = lambda ago: f'<div class="top"><img src="{logo}"><span class="app">{name}</span><span class="ago">{ago}</span></div>'
    imgs = "".join(f'<img class="pic" id="p{i}" src="file://{Path(p).resolve()}">' for i, p in enumerate(spec["images"]))
    cards = ""
    for i, s in enumerate(sents):
        c = card_for(s.get("card") or s.get("fact"))
        s["has_card"] = bool(c)
        if c:
            cards += (f'<div class="nt fc" id="c{i}">{top("ഇപ്പോൾ")}<div class="body"><div class="ico">{R.icon(c["icon"])}</div>'
                      f'<div><div class="lb">{E(c["label"])}</div><div class="vl">{E(to_digits(c["text"]))}</div></div></div></div>')
    rows = summary_rows(spec, sents)
    summary = "" if len(rows) < 3 else (f'<div class="nt" id="sum">{top(str(len(rows)) + " അറിയിപ്പുകൾ")}<div class="ttl">പൂർണ വിവരം</div>' + "".join(
        f'<div class="rw" id="r{i}">{R.icon(c["icon"])}<div class="l">{E(c["label"])}</div><div class="v">{E(to_digits(c["text"]))}</div></div>'
        for i, c in enumerate(rows)) + '</div>')
    cap_html = ""
    for gi, g in enumerate(caps):
        spans = "".join(f'<span id="w{gi}_{k}">{E(w[0])}</span>' for k, w in enumerate(g["words"]))
        cap_html += f'<div class="ph" id="g{gi}">{spans}</div>'
    hook = spec.get("hook") or ["", ""]
    mini = spec.get("mini") or " ".join(x for x in hook if x)
    fc = [i for i, s in enumerate(sents) if s["has_card"]]
    data = json.dumps({"shots": shots, "fc": [{"i": i, "a": max(sents[i]["a"] + 0.15, hook_end + 0.1)} for i in fc],
                       "caps": [{"a": g["a"], "b": g["b"], "w": [[x[1], x[2]] for x in g["words"]]} for g in caps],
                       "hook_end": hook_end, "end_t": end_t, "total": total, "n": len(spec["images"]),
                       "sum_a": (sents[-2]["a"] if len(sents) > 5 else sents[-1]["a"]) if (len(sents) > 3 and summary) else 1e9,
                       "rows": len(rows) if summary else 0})
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body style="--acc:{acc}">
<div id="stage">{imgs}</div><div id="shade"></div><div id="flash"></div>
<img id="plogo" src="{logo}">
<div id="hdr"><span class="dot"></span><span class="cat">{E(spec.get('cat', '') or 'വാർത്ത')}</span><span class="sep">•</span><span class="dt">{E(spec['date'])}</span></div>
<div id="pin">{R.icon('location-dot')}<span>{E(spec.get('location', ''))}</span></div>
<div class="nt" id="hook">{top("ഇപ്പോൾ")}<div class="h1">{E(hook[0])}</div>{('<div class="h2">' + E(hook[1]) + '</div>') if hook[1] else ''}</div>
<div class="nt" id="mini"><div class="top"><img src="{logo}"><span class="app">{name}</span><span class="ago">{R.icon('thumbtack')}</span></div><div class="vl">{E(mini)}</div></div>
{cards}
{summary}
<div id="cap">{cap_html}</div>
<div id="end"><div class="box"><img src="{logo}"><div class="e1">{E(page['tagline'])}</div><div class="e3">@{E(page['handle'])}</div>
<div class="acts"><div class="b f">{R.icon('user-plus')}<span>Follow</span></div><div class="b s">{R.icon('share-nodes')}<span>Share</span></div></div>
<div class="hd">📌 Save ചെയ്യൂ • ആവശ്യമുള്ളവർക്ക് അയക്കൂ</div></div></div>
<script>
const D={data};
const cl=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-x,3), back=x=>{{const c=1.70158,c3=c+1;return 1+c3*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
function place(sh_,t,el,extra){{
  const dur=Math.max(0.5,sh_.b-sh_.a), tt=Math.min(t,sh_.b), pr=cl((tt-sh_.a)/Math.min(dur,2.4));
  const pe=pr<0.5?2*pr*pr:1-Math.pow(-2*pr+2,2)/2, z=sh_.z0+(sh_.z1-sh_.z0)*pe;
  el.style.transformOrigin=(sh_.fx*100)+'% '+(sh_.fy*100)+'%';
  el.style.transform='translate('+(sh_.px*(pe-0.5)+(extra||0))+'px,'+(sh_.py*(pe-0.5))+'px) scale('+(z*1.02)+')';
}}
const STEP=230, MAXV=3;
window.renderAt=function(t){{
  let ai=D.shots.length-1; D.shots.forEach((s,i)=>{{if(t>=s.a&&t<s.b)ai=i}});
  const active=D.shots[ai], k=t-active.a, prev=ai>0?D.shots[ai-1]:null;
  const TR=0.3, trans=(prev&&prev.img!==active.img&&k<TR)?cl(k/TR):1;
  for(let i=0;i<D.n;i++){{const e=document.getElementById('p'+i);e.style.opacity=0;e.style.zIndex=0;e.style.filter='none';}}
  const el=document.getElementById('p'+active.img); el.style.opacity=ease(trans); el.style.zIndex=2; place(active,t,el,(1-ease(trans))*90);
  if(trans<1){{const pe_=document.getElementById('p'+prev.img);pe_.style.opacity=1;pe_.style.zIndex=1;place(prev,t,pe_,-ease(trans)*120);}}
  if(t>=D.end_t)el.style.filter='blur('+(18*Math.min(1,(t-D.end_t)/0.3))+'px)';
  document.getElementById('flash').style.opacity=(active.a>0&&k<0.1&&prev&&prev.img!==active.img)?0.12*(1-k/0.1):0;
  const live=t<D.end_t?1:0;
  ['hdr','pin','plogo'].forEach(id=>document.getElementById(id).style.opacity=live);
  // opening: big notification drops in from above, then lifts away into the pinned one
  const h=document.getElementById('hook'), hin=back(cl(t/0.45)), hout=ease(cl((t-(D.hook_end-0.3))/0.3));
  h.style.opacity=(t<D.hook_end)?cl(t/0.15)*(1-hout):0;
  h.style.transform='translateY('+(-220*(1-Math.min(1,hin))-260*hout)+'px) scale('+(1-0.25*hout)+')';
  const m=document.getElementById('mini'), mi=back(cl((t-(D.hook_end-0.1))/0.4));
  m.style.opacity=(t>=D.hook_end-0.1&&t<D.end_t)?cl(mi*1.4):0; m.style.transform='translateY('+(-80*(1-Math.min(1,mi)))+'px)';
  // fact stack: the newest on top, older ones slide down; after MAXV they fade out
  const sumOn=t>=D.sum_a;
  D.fc.forEach((f,idx)=>{{
    const c=document.getElementById('c'+f.i);
    if(t<f.a||sumOn||t>=D.end_t){{c.style.opacity=0;return;}}
    let slot=0; for(let j=idx+1;j<D.fc.length;j++){{if(t>=D.fc[j].a)slot+=ease(cl((t-D.fc[j].a)/0.35));}}
    const pin=back(cl((t-f.a)/0.45));
    const fade=cl(slot-(MAXV-1)), dim=1-0.12*Math.min(slot,2);
    c.style.opacity=cl((t-f.a)/0.12)*(1-fade);
    c.style.zIndex=50-Math.round(slot);
    c.style.transform='translateY('+(slot*STEP-160*(1-Math.min(1,pin)))+'px) scale('+(dim-0.04*(1-Math.min(1,pin)))+')';
  }});
  // grouped summary
  const sm=document.getElementById('sum');
  if(sm){{const u=back(cl((t-D.sum_a)/0.45)); sm.style.opacity=(sumOn&&t<D.end_t)?cl(u*1.5):0; sm.style.transform='translateY('+(-120*(1-Math.min(1,u)))+'px)';
    for(let i=0;i<D.rows;i++){{const r=document.getElementById('r'+i), a=D.sum_a+0.3+i*0.28; r.style.opacity=cl((t-a)/0.25); r.style.transform='translateX('+(-30*(1-ease(cl((t-a)/0.3))))+'px)';}}}}
  // captions
  D.caps.forEach((g,gi)=>{{
    const ge=document.getElementById('g'+gi), on=(t>=g.a&&t<g.b)&&t<D.end_t;
    ge.style.opacity=on?cl((t-g.a)/0.08):0;
    if(on){{const u=ease(cl((t-g.a)/0.2)); ge.style.transform='translateY('+(22*(1-u))+'px)';
      g.w.forEach((w,k)=>{{document.getElementById('w'+gi+'_'+k).className=(t>=w[0]&&t<w[1])?'on':'';}});}}
  }});
  const e=document.getElementById('end'), eu=back(cl((t-D.end_t)/0.45));
  e.style.opacity=ease(cl((t-D.end_t)/0.3)); e.querySelector('.box').style.transform='translateY('+(-200*(1-Math.min(1,eu)))+'px)';
}};
function fitEl(el,maxH,min){{if(!el)return;let fs=parseFloat(getComputedStyle(el).fontSize),n=0;while((el.scrollWidth>el.clientWidth+1||el.offsetHeight>maxH)&&fs>min&&n++<60){{fs-=2;el.style.fontSize=fs+'px';}}}}
window.fitAll=function(){{
  document.querySelectorAll('.ph').forEach(e=>fitEl(e,200,56));
  document.querySelectorAll('.fc .vl').forEach(e=>fitEl(e,130,32));
  fitEl(document.querySelector('#hook .h1'),400,52); fitEl(document.querySelector('#hook .h2'),170,40);
  fitEl(document.querySelector('#mini .vl'),110,28);
  document.querySelectorAll('#sum .v').forEach(e=>fitEl(e,100,24)); document.querySelectorAll('#sum .l').forEach(e=>fitEl(e,72,20));
  fitEl(document.querySelector('#pin span'),50,24);
}};
</script></body></html>"""


R4.build_html = build_html      # reel4.main renders whatever build_html is set here; voice, timing and video encoding are shared

if __name__ == "__main__":
    R4.main(*sys.argv[1:])
