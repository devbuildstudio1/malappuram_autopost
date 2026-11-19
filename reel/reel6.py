"""മലപ്പുറം 360 / മഞ്ചേരി 360 — news reel v6: "Impact" (built to be watched to the end).
Usage: python3 reel6.py spec.json out.mp4 [page]      (same spec, voice and timing as reel4.py; only the screen design differs)

Owner 19 Nov 2026: a template that pulls people in and keeps them watching. What does that:
- Frame 1 is never still: the photo punches in, the category stamp slams down, the headline words land one by one.
  (Instagram decides in the first second whether the reel is shown to more people.)
- Captions build word by word as the voice says them (big, centred, the spoken word pops): eyes follow the words.
- A visual change about every 2 seconds: photo cuts with a zoom punch, white flash and a short shake; fact cards bounce in.
- The number in a fact is shown huge (8:30, 2 പേർ, ₹5 ലക്ഷം): numbers stop the scroll.
- A small "മുഴുവൻ വിവരം 👇" teaser under the opening headline promises the details, so people wait for them.
- End card: pulsing Follow button.
Kept from the owner's earlier rules: logo top-right, everything in the safe zone (y 150-1600), no top progress line, no bottom logo strip.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel as R
import reel4 as R4
from reel4 import E, card_for, accent_for
from reel5 import summary_rows
from digits import to_digits

CSS = R.ff("CT", "anek-malayalam", [700, 800]) + R.ff("NST", "noto-sans-malayalam", [600, 700, 800]) + R.ff("BT", "baloo-chettan-2", [800]) + """
:root{--acc:#E3151B;--navy:#071433;--yellow:#FFD233}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
body{font-family:'NST','CT',sans-serif;color:#fff;position:relative}
.ic{width:1em;height:1em;display:block}
#wrap{position:absolute;inset:0;will-change:transform}
#stage{position:absolute;inset:0;overflow:hidden}
.pic{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;opacity:0;will-change:transform,filter}
#shade{position:absolute;inset:0;z-index:5;background:linear-gradient(180deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.25) 20%,rgba(0,0,0,0) 36%,rgba(0,0,0,0) 50%,rgba(0,0,0,.45) 64%,rgba(0,0,0,.85) 100%)}
#vig{position:absolute;inset:0;z-index:6;box-shadow:inset 0 0 220px rgba(0,0,0,.65);pointer-events:none}
#flash{position:absolute;inset:0;z-index:7;background:#fff;opacity:0}
#plogo{position:absolute;right:48px;top:140px;width:124px;height:124px;border-radius:50%;border:4px solid #fff;z-index:30;box-shadow:0 8px 24px rgba(0,0,0,.5)}
/* header */
#hdr{position:absolute;left:48px;top:150px;z-index:30}
#hdr .nm{font:800 48px/1.05 'BT','NST';text-shadow:0 3px 12px rgba(0,0,0,.7)}
#hdr .sub{display:flex;align-items:center;gap:12px;margin-top:8px;font:700 30px 'NST','CT';color:#E8ECF5;text-shadow:0 2px 8px rgba(0,0,0,.8)}
#hdr .live{display:flex;align-items:center;gap:10px;background:var(--acc);color:#fff;padding:5px 16px 1px 12px;border-radius:8px;font:800 28px 'NST','CT'}
#hdr .live i{display:block;width:16px;height:16px;border-radius:50%;background:#fff;margin-top:-4px}
#pin{position:absolute;left:48px;top:296px;z-index:30;display:flex;align-items:center;gap:12px;background:#fff;color:var(--navy);
  padding:10px 26px 6px 16px;border-radius:999px;font:800 36px/1.2 'NST','CT';box-shadow:0 10px 30px rgba(0,0,0,.45);transform-origin:0 50%}
#pin .ic{font-size:36px;color:var(--acc);margin-top:-4px}
#pin span{white-space:nowrap;overflow:hidden;max-width:820px;display:block}
/* opening */
#stamp{position:absolute;left:48px;top:430px;z-index:23;background:var(--acc);color:#fff;font:900 52px 'CT','NST';padding:12px 34px 4px;
  transform-origin:30% 50%;opacity:0;box-shadow:0 12px 30px rgba(0,0,0,.5);border:4px solid #fff}
#hook{position:absolute;left:48px;right:48px;top:540px;z-index:22}
#hook .h1{font:900 110px/1.12 'CT','NST';color:#fff;-webkit-text-stroke:14px #000;paint-order:stroke fill}
#hook .h1 span{display:inline-block;opacity:0;margin-right:.2em;transform-origin:50% 80%}
#hook .h2{display:inline-block;margin-top:22px;font:900 92px/1.12 'CT','NST';color:#000;background:var(--yellow);padding:12px 30px 2px;border-radius:16px;
  box-shadow:0 0 0 6px #000,0 16px 40px rgba(0,0,0,.5);opacity:0;transform-origin:20% 50%}
#tease{display:flex;align-items:center;gap:14px;margin-top:34px;font:800 44px 'NST','CT';color:#fff;opacity:0;text-shadow:0 3px 14px rgba(0,0,0,.9)}
#tease b{color:var(--yellow)}
/* persistent headline */
#mini{position:absolute;left:48px;right:150px;top:400px;z-index:22;opacity:0;font:800 46px/1.28 'NST','CT';color:#fff;
  border-left:10px solid var(--yellow);padding:4px 0 0 22px;text-shadow:0 3px 14px rgba(0,0,0,.85)}
/* fact cards: big number when the fact has one */
.card{position:absolute;left:48px;top:620px;width:880px;z-index:23;opacity:0;display:flex;align-items:stretch;background:#fff;border-radius:28px;
  box-shadow:0 22px 60px rgba(0,0,0,.55);overflow:hidden;transform-origin:0 50%}
.card .ico{flex:none;width:150px;display:flex;align-items:center;justify-content:center;background:var(--acc);color:#fff;font-size:72px}
.card .num{flex:none;min-width:230px;max-width:380px;padding:18px 26px 8px;display:flex;align-items:center;justify-content:center;background:var(--yellow);color:#000;
  font:900 104px/1 'CT','NST';white-space:nowrap}
.card .tx{padding:22px 30px 16px;display:flex;flex-direction:column;justify-content:center;gap:4px;min-width:0}
.card .lb{font:800 30px 'NST','CT';color:var(--acc)}
.card .vl{font:800 50px/1.25 'NST','CT';color:var(--navy)}
/* captions: build word by word, centred */
#cap{position:absolute;left:60px;right:140px;top:1160px;height:380px;z-index:25}
.ph{position:absolute;left:0;right:0;bottom:0;text-align:center;font:900 80px/1.28 'CT','NST';color:#fff;opacity:0;-webkit-text-stroke:14px #000;paint-order:stroke fill;
  text-shadow:0 8px 22px rgba(0,0,0,.6)}
.ph span{display:inline-block;transform-origin:50% 80%;margin:0 .16em;opacity:0}
.ph span.on{color:var(--yellow)}
/* summary */
#sum{position:absolute;left:48px;right:48px;top:520px;z-index:24;opacity:0;background:#fff;border-radius:30px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.6)}
#sum .st{background:var(--acc);color:#fff;font:900 46px 'CT','NST';padding:18px 34px 10px;display:flex;align-items:center;gap:16px}
#sum .st .ic{font-size:42px;margin-top:-6px}
#sum .row{display:flex;align-items:center;gap:22px;padding:14px 30px 8px;border-top:2px solid #E6E9F0;opacity:0}
#sum .row .ic{flex:none;font-size:42px;color:var(--acc);margin-top:-6px}
#sum .row .l{flex:none;width:200px;font:800 30px/1.2 'NST','CT';color:#6B7280;overflow:hidden}
#sum .row .v{font:800 38px/1.3 'NST','CT';color:var(--navy)}
/* end card */
#end{position:absolute;inset:0;z-index:40;opacity:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center;
  padding:0 70px 260px;background:rgba(0,0,0,.6)}
#end img{width:250px;height:250px;border-radius:50%;border:6px solid #fff;box-shadow:0 14px 50px rgba(0,0,0,.6)}
#end .e1{font:900 72px/1.25 'CT','NST'}
#end .fol{display:flex;align-items:center;gap:18px;background:var(--acc);font:900 58px 'CT','NST';padding:20px 54px 12px;border-radius:999px;border:5px solid #fff;
  box-shadow:0 0 0 0 rgba(227,21,27,.7)}
#end .fol .ic{font-size:52px;margin-top:-6px}
#end .hd{font:800 40px 'NST','CT';color:#fff;background:rgba(0,0,0,.45);padding:12px 30px 6px;border-radius:16px}
#end .e3{font:800 46px 'CT','NST';color:var(--yellow)}
"""

NUM = re.compile(r"(₹\s?[\d,.]+(?:\s?(?:ലക്ഷം|കോടി))?|\d{1,2}[:.]\d{2}|\d[\d,.]*\s?(?:%|പേർ|പേരെ|പേർക്ക്|കി\.?മീ|മണിക്കൂർ|ദിവസം|വയസ്)?)")


def big_number(text):
    """the striking number in a fact ('8:30', '2 പേരെ', '₹5 ലക്ഷം'); '' when there is none or it is too long to show huge"""
    m = NUM.search(text)
    if not m:
        return ""
    n = m.group(1).strip().rstrip(",.")
    return n if 0 < len(n) <= 9 and re.search(r"\d", n) else ""


def build_html(spec, shots, sents, caps, hook_end, end_t, total, page):
    logo = f"file://{R.KIT.resolve() / page['logo']}"
    acc = accent_for(spec.get("cat", ""))
    imgs = "".join(f'<img class="pic" id="p{i}" src="file://{Path(p).resolve()}">' for i, p in enumerate(spec["images"]))
    cards = ""
    for i, s in enumerate(sents):
        c = card_for(s.get("card") or s.get("fact"))
        s["has_card"] = bool(c)
        if c:
            txt = to_digits(c["text"])
            n = big_number(txt)
            left = f'<div class="num">{E(n)}</div>' if n else f'<div class="ico">{R.icon(c["icon"])}</div>'
            cards += f'<div class="card" id="c{i}">{left}<div class="tx"><div class="lb">{E(c["label"])}</div><div class="vl">{E(txt)}</div></div></div>'
    rows = summary_rows(spec, sents)
    summary = "" if len(rows) < 3 else ('<div id="sum"><div class="st">' + R.icon('circle-info') + '<span>പൂർണ വിവരം</span></div>' + "".join(
        f'<div class="row" id="r{i}">{R.icon(c["icon"])}<div class="l">{E(c["label"])}</div><div class="v">{E(to_digits(c["text"]))}</div></div>' for i, c in enumerate(rows)) + '</div>')
    cap_html = ""
    for gi, g in enumerate(caps):
        spans = "".join(f'<span id="w{gi}_{k}">{E(w[0])}</span>' for k, w in enumerate(g["words"]))
        cap_html += f'<div class="ph" id="g{gi}">{spans}</div>'
    hook = spec.get("hook") or ["", ""]
    hw = E(hook[0]).split()
    h1 = "".join(f'<span id="hw{i}">{w}</span>' for i, w in enumerate(hw))
    mini = spec.get("mini") or " ".join(x for x in hook if x)
    data = json.dumps({"shots": shots, "sents": [{"a": s["a"], "b": s["b"], "card": s["has_card"]} for s in sents],
                       "caps": [{"a": g["a"], "b": g["b"], "w": [[x[1], x[2]] for x in g["words"]]} for g in caps],
                       "hook_end": hook_end, "end_t": end_t, "total": total, "n": len(spec["images"]), "hw": len(hw), "h2": bool(hook[1]),
                       "sum_a": (sents[-2]["a"] if len(sents) > 5 else sents[-1]["a"]) if (len(sents) > 3 and summary) else 1e9,
                       "rows": len(rows) if summary else 0})
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body style="--acc:{acc}">
<div id="wrap"><div id="stage">{imgs}</div></div><div id="shade"></div><div id="vig"></div><div id="flash"></div>
<img id="plogo" src="{logo}">
<div id="hdr"><div class="nm">{page['name']}</div>
<div class="sub"><span class="live"><i></i>{E(spec.get('cat', '') or 'വാർത്ത')}</span><span>{E(spec['date'])}</span></div></div>
<div id="pin">{R.icon('location-dot')}<span>{E(spec.get('location', ''))}</span></div>
<div id="stamp">{E(spec.get('cat', '') or 'വാർത്ത')}</div>
<div id="hook"><div class="h1">{h1}</div>{('<div class="h2">' + E(hook[1]) + '</div>') if hook[1] else ''}
<div id="tease">മുഴുവൻ വിവരം <b>👇</b></div></div>
<div id="mini">{E(mini)}</div>
{cards}
{summary}
<div id="cap">{cap_html}</div>
<div id="end"><img src="{logo}"><div class="e1">{E(page['tagline'])}</div>
<div class="fol">{R.icon('user-plus')}<span>FOLLOW</span></div>
<div class="hd">📌 Save • ആവശ്യമുള്ളവർക്ക് Share</div><div class="e3">@{E(page['handle'])}</div></div>
<script>
const D={data};
const cl=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-x,3), back=x=>{{const c=1.70158,c3=c+1;return 1+c3*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
const slam=x=>x<=0?0:(x>=1?1:1+2.2*Math.pow(1-x,3)*Math.sin(x*9));
function place(sh_,t,el,extra,punch){{
  const dur=Math.max(0.5,sh_.b-sh_.a), tt=Math.min(t,sh_.b), pr=cl((tt-sh_.a)/Math.min(dur,2.4));
  const pe=pr<0.5?2*pr*pr:1-Math.pow(-2*pr+2,2)/2, z=sh_.z0+(sh_.z1-sh_.z0)*pe;
  el.style.transformOrigin=(sh_.fx*100)+'% '+(sh_.fy*100)+'%';
  el.style.transform='translate('+(sh_.px*(pe-0.5)+(extra||0))+'px,'+(sh_.py*(pe-0.5))+'px) scale('+(z*1.02*(1+(punch||0)))+')';
}}
window.renderAt=function(t){{
  let ai=D.shots.length-1; D.shots.forEach((s,i)=>{{if(t>=s.a&&t<s.b)ai=i}});
  const active=D.shots[ai], k=t-active.a, prev=ai>0?D.shots[ai-1]:null;
  const cut=(ai===0)||(prev&&prev.img!==active.img);
  const TR=0.18, trans=(prev&&prev.img!==active.img&&k<TR)?cl(k/TR):1;
  // zoom punch on every cut (and on frame 1)
  const punch=cut?0.16*Math.pow(1-cl(k/0.45),3):0;
  for(let i=0;i<D.n;i++){{const e=document.getElementById('p'+i);e.style.opacity=0;e.style.zIndex=0;e.style.filter='none';}}
  const el=document.getElementById('p'+active.img); el.style.opacity=ease(trans); el.style.zIndex=2; place(active,t,el,0,punch);
  if(trans<1){{const pe_=document.getElementById('p'+prev.img);pe_.style.opacity=1;pe_.style.zIndex=1;place(prev,t,pe_,0,0);}}
  if(t>=D.end_t)el.style.filter='blur('+(18*Math.min(1,(t-D.end_t)/0.3))+'px)';
  document.getElementById('flash').style.opacity=(cut&&k<0.12&&t<D.end_t)?0.35*(1-k/0.12):0;
  // short shake on a cut
  const sh=(cut&&k<0.22&&t<D.end_t)?(1-k/0.22):0;
  document.getElementById('wrap').style.transform='translate('+(Math.sin(t*90)*14*sh)+'px,'+(Math.cos(t*77)*10*sh)+'px)';
  const live=t<D.end_t?1:0;
  ['hdr','plogo'].forEach(id=>document.getElementById(id).style.opacity=live);
  const dot=document.querySelector('#hdr .live i'); dot.style.opacity=0.35+0.65*Math.abs(Math.sin(t*4));
  const pn=document.getElementById('pin'); pn.style.opacity=live*cl((t-0.25)/0.1); pn.style.transform='scale('+slam(cl((t-0.25)/0.35))+')';
  // opening: stamp slams, headline words land one by one, the number box pops, then the teaser
  const st=document.getElementById('stamp'), sp=cl(t/0.3);
  st.style.opacity=(t<D.hook_end)?cl(sp*3):0; st.style.transform='rotate(-3deg) scale('+(1+1.2*Math.pow(1-sp,3))+')';
  const hout=cl((t-(D.hook_end-0.2))/0.2);
  document.getElementById('hook').style.opacity=t<D.hook_end?1-hout:0;
  const step=Math.min(0.12,1.0/Math.max(1,D.hw));
  for(let i=0;i<D.hw;i++){{const w=document.getElementById('hw'+i), a=0.15+i*step, p=cl((t-a)/0.22);
    w.style.opacity=cl(p*3); w.style.transform='scale('+(1+0.5*Math.pow(1-p,3))+') translateY('+(-30*Math.pow(1-p,2))+'px)';}}
  const ha=0.2+D.hw*step+0.1;
  if(D.h2){{const h2=document.querySelector('#hook .h2'), p=cl((t-ha)/0.35); h2.style.opacity=cl(p*4);
    h2.style.transform='scale('+(p<1?slam(p):1+0.04*Math.sin((t-ha)*8))+')';}}
  const te=document.getElementById('tease'), tp=cl((t-(ha+0.45))/0.3);
  te.style.opacity=tp; te.style.transform='translateY('+(8*Math.sin(t*7))+'px)';
  // persistent headline
  const m=document.getElementById('mini'), min_=ease(cl((t-D.hook_end)/0.3));
  m.style.opacity=(t>=D.hook_end&&t<D.end_t)?min_:0; m.style.transform='translateX('+(-(1-min_)*80)+'px)';
  // fact cards bounce in with their sentence
  D.sents.forEach((s,i)=>{{
    if(!s.card)return; const c=document.getElementById('c'+i);
    const a=Math.max(s.a+0.1,D.hook_end+0.1), b=s.b+0.25;
    const p=cl((t-a)/0.45), out=cl((t-(b-0.15))/0.15);
    c.style.opacity=(t>=a&&t<b&&t<D.end_t&&t<D.sum_a)?cl(p*4)*(1-out):0;
    c.style.transform='translateX('+(-500*Math.pow(1-p,3))+'px) rotate('+(-4*(1-slam(p)))+'deg) scale('+(0.9+0.1*slam(p))+')';
    const nm=c.querySelector('.num'); if(nm)nm.style.transform='scale('+(p<1?slam(cl((t-a-0.15)/0.4)):1)+')';
  }});
  // summary
  const sm=document.getElementById('sum');
  if(sm){{const u=back(cl((t-D.sum_a)/0.4)); sm.style.opacity=(t>=D.sum_a&&t<D.end_t)?cl(u*1.5):0; sm.style.transform='translateY('+(60*(1-Math.min(1,u)))+'px)';
    for(let i=0;i<D.rows;i++){{const r=document.getElementById('r'+i), a=D.sum_a+0.25+i*0.25; r.style.opacity=cl((t-a)/0.2); r.style.transform='translateX('+(-50*(1-ease(cl((t-a)/0.3))))+'px)';}}}}
  // captions: words appear as they are spoken
  D.caps.forEach((g,gi)=>{{
    const ge=document.getElementById('g'+gi), on=(t>=g.a-0.05&&t<g.b+0.05)&&t<D.end_t;
    ge.style.opacity=on?1:0;
    if(on)g.w.forEach((w,k)=>{{const s=document.getElementById('w'+gi+'_'+k), p=cl((t-w[0]+0.04)/0.16);
      s.style.opacity=cl(p*3); s.className=(t>=w[0]&&t<w[1])?'on':'';
      s.style.transform='scale('+((t>=w[0]&&t<w[1])?1.05:1)*(1+0.35*Math.pow(1-p,3))+')';}});
  }});
  // end card
  const e=document.getElementById('end'), eu=cl((t-D.end_t)/0.35); e.style.opacity=ease(eu);
  e.style.transform='scale('+(0.92+0.08*ease(eu))+')';
  const f=e.querySelector('.fol'), ph=(t-D.end_t)*3.2, pl=Math.max(0,Math.sin(ph));
  f.style.transform='scale('+(1+0.07*pl)+')'; f.style.boxShadow='0 0 0 '+(28*((ph/Math.PI)%1))+'px rgba(255,255,255,'+(0.5*(1-((ph/Math.PI)%1)))+')';
}};
function fitEl(el,maxH,min){{if(!el)return;let fs=parseFloat(getComputedStyle(el).fontSize),n=0;while((el.scrollWidth>el.clientWidth+1||el.offsetHeight>maxH)&&fs>min&&n++<60){{fs-=2;el.style.fontSize=fs+'px';}}}}
window.fitAll=function(){{
  document.querySelectorAll('.ph').forEach(e=>fitEl(e,220,58));
  document.querySelectorAll('.card .vl').forEach(e=>fitEl(e,190,32));
  document.querySelectorAll('.card .num').forEach(e=>fitEl(e,999,48));
  fitEl(document.querySelector('#hook .h1'),380,60); fitEl(document.querySelector('#hook .h2'),200,48);
  fitEl(document.getElementById('mini'),124,30); document.querySelectorAll('#sum .v').forEach(e=>fitEl(e,104,26)); document.querySelectorAll('#sum .l').forEach(e=>fitEl(e,76,20));
  fitEl(document.querySelector('#pin span'),60,26);
}};
</script></body></html>"""


R4.build_html = build_html      # reel4.main renders whatever build_html is set here; voice, timing and video encoding are shared

if __name__ == "__main__":
    R4.main(*sys.argv[1:])
