"""മലപ്പുറം 360 / മഞ്ചേരി 360 — news reel v7: "Chat" design.
Usage: python3 reel7.py spec.json out.mp4 [page]      (same spec, voice and timing as reel4.py; only the screen design differs)

Owner 19 Nov 2026: a different idea. The story is told like messages from the page in a chat (own colours, no real app copied):
- The photo is the chat wallpaper (it keeps moving underneath, cuts as before).
- Header: the page as the chat contact, status "ടൈപ്പ് ചെയ്യുന്നു…" while the voice speaks; logo top-right (owner rule).
- First message: the headline (big) + the striking line in a red box.
- Every spoken sentence arrives as a new message; its words light up as they are said (the message is the caption).
- A fact for that sentence is attached under the message as a chip (big number when there is one).
- Older messages scroll up like a real chat; the last one is the "പൂർണ വിവരം" summary.
Safe zone y 150-1600 kept; no bottom logo strip; no top progress line.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel as R
import reel4 as R4
from reel4 import E, card_for, accent_for
from reel5 import summary_rows
from reel6 import big_number
from digits import to_digits

CSS = R.ff("CT", "anek-malayalam", [700, 800]) + R.ff("NST", "noto-sans-malayalam", [600, 700, 800]) + R.ff("BT", "baloo-chettan-2", [800]) + """
:root{--acc:#E3151B;--ink:#0F172A;--muted:#64748B;--bub:#FFFFFF;--bar:rgba(10,18,40,.82)}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
body{font-family:'NST','CT',sans-serif;color:#fff;position:relative}
.ic{width:1em;height:1em;display:block}
#stage{position:absolute;inset:0;overflow:hidden}
.pic{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;opacity:0;will-change:transform,filter}
#shade{position:absolute;inset:0;z-index:5;background:linear-gradient(180deg,rgba(5,10,25,.55) 0%,rgba(5,10,25,.30) 30%,rgba(5,10,25,.45) 60%,rgba(5,10,25,.8) 100%)}
#flash{position:absolute;inset:0;z-index:7;background:#fff;opacity:0}
/* chat header */
#bar{position:absolute;left:0;right:0;top:120px;height:170px;z-index:30;background:var(--bar);backdrop-filter:blur(18px);display:flex;align-items:center;
  padding:0 48px;gap:20px;border-bottom:2px solid rgba(255,255,255,.12)}
#bar .who{flex:1;min-width:0}
#bar .nm{font:800 48px/1.1 'BT','NST'}
#bar .st{font:700 30px/1.2 'NST','CT';color:#9FB0C8;margin-top:6px;white-space:nowrap}
#bar .st b{color:#7CE3A1;font-weight:800}
#bar img{width:118px;height:118px;border-radius:50%;border:4px solid #fff}
#day{position:absolute;left:0;right:0;top:318px;z-index:29;text-align:center}
#day span{display:inline-block;background:rgba(10,18,40,.7);border-radius:14px;padding:8px 22px 4px;font:700 28px 'NST','CT';color:#E2E8F0}
/* messages */
#chat{position:absolute;left:0;right:0;top:0;bottom:0;z-index:20}
.msg{position:absolute;left:48px;max-width:880px;background:var(--bub);color:var(--ink);border-radius:8px 38px 38px 38px;padding:22px 30px 14px;
  box-shadow:0 14px 40px rgba(0,0,0,.4);opacity:0;will-change:transform,opacity;transform-origin:0 100%}
.msg .tm{display:flex;justify-content:flex-end;align-items:center;gap:8px;font:700 24px 'NST','CT';color:var(--muted);margin-top:6px}
.msg .tm .ic{font-size:26px;color:#3B82F6}
.msg .tx{font:800 54px/1.3 'NST','CT';color:#CBD5E1}
.msg .tx span{transition:none}
.msg .tx span.sd{color:var(--ink)}
.msg .tx span.on{color:var(--acc)}
.msg .cat{display:inline-block;background:var(--acc);color:#fff;font:800 28px 'NST','CT';padding:6px 16px 2px;border-radius:8px;margin-bottom:12px}
.msg.hk .h1{font:900 76px/1.15 'CT','NST';color:var(--ink)}
.msg.hk .h2{display:inline-block;margin-top:16px;background:var(--acc);color:#fff;font:900 58px/1.15 'CT','NST';padding:10px 24px 2px;border-radius:14px}
.msg.hk .loc{display:flex;align-items:center;gap:10px;margin-top:16px;font:800 34px 'NST','CT';color:var(--muted)}
.msg.hk .loc .ic{color:var(--acc);font-size:34px;margin-top:-4px}
.chip{display:flex;align-items:stretch;margin-top:16px;border-radius:22px;overflow:hidden;background:#F1F5F9;border:2px solid #E2E8F0}
.chip .num{flex:none;padding:14px 22px 6px;background:#FFD233;color:#000;font:900 70px/1 'CT','NST';display:flex;align-items:center;white-space:nowrap}
.chip .ico{flex:none;width:100px;display:flex;align-items:center;justify-content:center;background:var(--acc);color:#fff;font-size:48px}
.chip .c{padding:12px 20px 8px;min-width:0}
.chip .lb{font:800 26px 'NST','CT';color:var(--acc)}
.chip .vl{font:800 38px/1.25 'NST','CT';color:var(--ink)}
.msg.sm .ttl{display:flex;align-items:center;gap:14px;font:900 46px 'CT','NST';color:var(--acc);margin-bottom:8px}
.msg.sm .ttl .ic{font-size:42px;margin-top:-6px}
.msg.sm .rw{display:flex;align-items:center;gap:18px;padding:12px 0 8px;border-top:2px solid #E2E8F0;opacity:0}
.msg.sm .rw .ic{flex:none;font-size:38px;color:var(--acc);margin-top:-6px}
.msg.sm .rw .l{flex:none;width:180px;font:800 28px/1.2 'NST','CT';color:var(--muted);overflow:hidden}
.msg.sm .rw .v{font:800 36px/1.3 'NST','CT';color:var(--ink)}
/* typing dots */
#typing{position:absolute;left:48px;z-index:21;background:var(--bub);border-radius:8px 30px 30px 30px;padding:26px 30px;display:flex;gap:12px;opacity:0}
#typing i{width:18px;height:18px;border-radius:50%;background:#94A3B8;display:block}
/* end */
#end{position:absolute;inset:0;z-index:40;opacity:0;display:flex;align-items:center;justify-content:center;padding:0 48px 260px;background:rgba(5,10,25,.55)}
#end .box{width:100%;background:var(--bub);color:var(--ink);border-radius:8px 46px 46px 46px;padding:40px 44px 34px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.6)}
#end img{width:190px;height:190px;border-radius:50%;border:6px solid #fff;box-shadow:0 10px 30px rgba(0,0,0,.25)}
#end .e1{font:900 62px/1.25 'CT','NST';margin-top:18px}
#end .e3{font:800 36px 'NST','CT';color:var(--muted);margin-top:6px}
#end .fol{display:inline-flex;align-items:center;gap:16px;margin-top:28px;background:var(--acc);color:#fff;font:900 56px 'CT','NST';padding:18px 54px 10px;border-radius:999px}
#end .fol .ic{font-size:50px;margin-top:-6px}
#end .hd{font:800 34px 'NST','CT';color:var(--acc);margin-top:22px}
"""


def build_html(spec, shots, sents, caps, hook_end, end_t, total, page):
    logo = f"file://{R.KIT.resolve() / page['logo']}"
    acc = accent_for(spec.get("cat", ""))
    tick = '<div class="tm">ഇപ്പോൾ ' + R.icon('check-double') + '</div>'
    imgs = "".join(f'<img class="pic" id="p{i}" src="file://{Path(p).resolve()}">' for i, p in enumerate(spec["images"]))
    hook = spec.get("hook") or ["", ""]
    msgs, meta = [], []
    # 1: headline message, right at the start
    msgs.append(f'<div class="msg hk" id="m0"><div class="cat">{E(spec.get("cat", "") or "വാർത്ത")}</div><div class="h1">{E(hook[0])}</div>'
                + (f'<div class="h2">{E(hook[1])}</div>' if hook[1] else '')
                + f'<div class="loc">{R.icon("location-dot")}<span>{E(spec.get("location", ""))}</span></div>{tick}</div>')
    meta.append({"a": 0.05, "w": []})
    # one message per spoken sentence after the opening line; its words light up as they are said
    for i, s in enumerate(sents):
        if i == 0:
            continue
        words = [w for g in caps if s["a"] - 0.01 <= g["a"] <= s["b"] + 0.01 for w in g["words"]]
        if not words:
            continue
        mi = len(msgs)
        tx = "".join(f'<span id="w{mi}_{k}">{E(w[0])} </span>' for k, w in enumerate(words))
        chip = ""
        c = card_for(s.get("card") or s.get("fact"))
        if c:
            txt = to_digits(c["text"])
            n = big_number(txt)
            fw = {w[:4] for w in re.findall(r"[\u0D00-\u0D7F]{3,}", txt)}
            sw = {w[:4] for w in re.findall(r"[\u0D00-\u0D7F]{3,}", s["say"])}
            if not n and fw and len(fw & sw) >= 0.6 * len(fw):      # the chip would only repeat the message
                c = None
        if c:
            left = f'<div class="num">{E(n)}</div>' if n else f'<div class="ico">{R.icon(c["icon"])}</div>'
            chip = f'<div class="chip">{left}<div class="c"><div class="lb">{E(c["label"])}</div><div class="vl">{E(txt)}</div></div></div>'
        msgs.append(f'<div class="msg" id="m{mi}"><div class="tx">{tx}</div>{chip}{tick}</div>')
        meta.append({"a": s["a"], "w": [[w[1], w[2]] for w in words]})
    rows = summary_rows(spec, sents)
    sum_a = None
    if len(rows) >= 3 and len(sents) > 3:
        sum_a = sents[-1]["b"] + 0.05 if sents[-1]["b"] + 0.6 < end_t else max(sents[-1]["a"], end_t - 1.2)
        mi = len(msgs)
        msgs.append(f'<div class="msg sm" id="m{mi}"><div class="ttl">{R.icon("circle-info")}<span>പൂർണ വിവരം</span></div>' + "".join(
            f'<div class="rw">{R.icon(c["icon"])}<div class="l">{E(c["label"])}</div><div class="v">{E(to_digits(c["text"]))}</div></div>' for c in rows)
            + f'{tick}</div>')
        meta.append({"a": sum_a, "w": [], "rows": len(rows)})
    data = json.dumps({"shots": shots, "m": meta, "end_t": end_t, "n": len(spec["images"]),
                       "talk": [[s["a"], s["b"]] for s in sents]})
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body style="--acc:{acc}">
<div id="stage">{imgs}</div><div id="shade"></div><div id="flash"></div>
<div id="bar"><div class="who"><div class="nm">{E(page['name'])}</div><div class="st" id="st">{E(spec['date'])}</div></div><img src="{logo}"></div>
<div id="day"><span>{E(spec['date'])}</span></div>
<div id="cap"></div><div id="hook" style="display:none"></div>
<div id="chat">{''.join(msgs)}<div id="typing"><i></i><i></i><i></i></div></div>
<div id="end"><div class="box"><img src="{logo}"><div class="e1">{E(page['tagline'])}</div><div class="e3">@{E(page['handle'])}</div>
<div class="fol">{R.icon('user-plus')}<span>FOLLOW</span></div><div class="hd">📌 Save • ആവശ്യമുള്ളവർക്ക് Share</div></div></div>
<script>
const D={data};
const cl=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-x,3), back=x=>{{const c=1.70158,c3=c+1;return 1+c3*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
const BOTTOM=1560, TOP=350, GAP=26;
let HS=[];
function place(sh_,t,el,extra){{
  const dur=Math.max(0.5,sh_.b-sh_.a), tt=Math.min(t,sh_.b), pr=cl((tt-sh_.a)/Math.min(dur,2.4));
  const pe=pr<0.5?2*pr*pr:1-Math.pow(-2*pr+2,2)/2, z=sh_.z0+(sh_.z1-sh_.z0)*pe;
  el.style.transformOrigin=(sh_.fx*100)+'% '+(sh_.fy*100)+'%';
  el.style.transform='translate('+(sh_.px*(pe-0.5)+(extra||0))+'px,'+(sh_.py*(pe-0.5))+'px) scale('+(z*1.02)+')';
}}
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
  ['bar','day','chat'].forEach(id=>document.getElementById(id).style.opacity=live);
  const talking=D.talk.some(x=>t>=x[0]&&t<x[1]);
  document.getElementById('st').innerHTML=talking?'<b>ടൈപ്പ് ചെയ്യുന്നു…</b>':'ഓൺലൈൻ';
  // stack: newest message at the bottom, older ones pushed up (smoothly while a new one grows in)
  let y=BOTTOM;
  for(let i=D.m.length-1;i>=0;i--){{
    const m=D.m[i], e=document.getElementById('m'+i);
    if(t<m.a){{e.style.opacity=0;continue;}}
    const sc=back(cl((t-m.a)/0.35)), p=Math.min(1,sc), h=HS[i]*p;      // pops from its bottom-left corner like a chat bubble
    const top=y-h;
    e.style.top=(y-HS[i])+'px';
    const fadeTop=cl((top-TOP+80)/80);
    e.style.opacity=cl((t-m.a)/0.08)*fadeTop;
    e.style.transform='scale('+Math.max(0.02,sc)+')';
    y=top-GAP*p;
    m.w.forEach((w,k2)=>{{const s=document.getElementById('w'+i+'_'+k2); s.className=(t>=w[0]&&t<w[1])?'on':(t>=w[1]?'sd':'');}});
    if(m.rows){{e.querySelectorAll('.rw').forEach((r,j)=>{{const a=m.a+0.2+j*0.25;r.style.opacity=cl((t-a)/0.2);}});}}
  }}
  // typing dots between messages (when nothing new is arriving and the voice pauses)
  const ty=document.getElementById('typing'); ty.style.opacity=0;
  const nxt=D.m.find(m=>m.a>t);
  if(nxt&&nxt.a-t<0.5&&t>0.3){{ty.style.top=(BOTTOM+10)+'px';ty.style.opacity=0.95;
    ty.querySelectorAll('i').forEach((d,j)=>d.style.transform='translateY('+(-8*Math.max(0,Math.sin(t*12-j*0.9)))+'px)');}}
  const e=document.getElementById('end'), eu=back(cl((t-D.end_t)/0.45));
  e.style.opacity=ease(cl((t-D.end_t)/0.3)); e.querySelector('.box').style.transform='scale('+(0.85+0.15*Math.min(1.05,eu))+')';
}};
function fitEl(el,maxH,min){{if(!el)return;let fs=parseFloat(getComputedStyle(el).fontSize),n=0;while((el.scrollWidth>el.clientWidth+1||el.offsetHeight>maxH)&&fs>min&&n++<60){{fs-=2;el.style.fontSize=fs+'px';}}}}
window.fitAll=function(){{
  fitEl(document.querySelector('.msg.hk .h1'),360,50); fitEl(document.querySelector('.msg.hk .h2'),160,38);
  document.querySelectorAll('.msg .tx').forEach(e=>fitEl(e,290,40));
  document.querySelectorAll('.chip .vl').forEach(e=>fitEl(e,110,28));
  document.querySelectorAll('.msg.sm .v').forEach(e=>fitEl(e,96,24));
  HS=D.m.map((m,i)=>document.getElementById('m'+i).offsetHeight);
}};
</script></body></html>"""


R4.build_html = build_html      # reel4.main renders whatever build_html is set here; voice, timing and video encoding are shared

if __name__ == "__main__":
    R4.main(*sys.argv[1:])
