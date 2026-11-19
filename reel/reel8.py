"""മലപ്പുറം 360 / മഞ്ചേരി 360 — news reel v8: "Photo board" design.
Usage: python3 reel8.py spec.json out.mp4 [page]      (same spec, voice and timing as reel4.py; only the screen design differs)

Owner 19 Nov 2026: a different idea that shows the images clearly and highlights the key points.
- Paper board background; every news photo drops in as a big, clear polaroid print (no dark overlay on the photo).
  Earlier prints stay underneath, tilted, so the viewer sees all the pictures of the story.
- The spoken words are written in the polaroid's white bottom strip (the caption), the current word in red.
- A notebook sheet under the photo collects the key points: each fact is added when the voice reaches it,
  a yellow highlighter sweeps over its number / key words, finished points get a tick. At the end the sheet is the full summary.
- Opening: category tape on the print + the headline written large on the sheet with the striking line highlighted.
Kept: logo top-right, safe zone y 150-1600, no top progress line, no bottom logo strip.
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reel as R
import reel4 as R4
from reel4 import E, card_for, accent_for
from reel6 import big_number
from digits import to_digits

CSS = R.ff("CT", "anek-malayalam", [700, 800]) + R.ff("NST", "noto-sans-malayalam", [600, 700, 800]) + R.ff("BT", "baloo-chettan-2", [800]) + """
:root{--acc:#E3151B;--ink:#1C1917;--muted:#78716C;--board:#E9E1D3;--hl:#FFE14D}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden}
body{font-family:'NST','CT',sans-serif;color:var(--ink);position:relative;
  background:radial-gradient(1200px 900px at 20% 10%,#F3EDE2 0%,transparent 60%),radial-gradient(1000px 800px at 90% 90%,#DDD3C2 0%,transparent 60%),var(--board)}
body::before{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(0,0,0,.06) 1.5px,transparent 1.5px);background-size:22px 22px}
.ic{width:1em;height:1em;display:block}
#flash{position:absolute;inset:0;z-index:60;background:#fff;opacity:0}
/* header */
#hdr{position:absolute;left:48px;top:150px;z-index:30}
#hdr .nm{font:800 50px/1.05 'BT','NST';color:var(--ink)}
#hdr .sub{display:flex;align-items:center;gap:12px;margin-top:8px;font:700 30px 'NST','CT';color:var(--muted)}
#hdr .sub .ic{color:var(--acc);font-size:30px;margin-top:-4px}
#plogo{position:absolute;right:48px;top:140px;width:120px;height:120px;border-radius:50%;border:4px solid #fff;z-index:30;box-shadow:0 8px 20px rgba(0,0,0,.25)}
/* polaroids */
.pol{position:absolute;left:84px;top:290px;width:912px;height:770px;background:#fff;padding:26px 26px 0;z-index:10;opacity:0;
  box-shadow:0 26px 60px rgba(0,0,0,.35),0 2px 6px rgba(0,0,0,.2);will-change:transform,opacity;transform-origin:50% 40%}
.pol .ph{width:860px;height:580px;overflow:hidden;background:#222}
.pol .ph img{width:100%;height:100%;object-fit:cover;will-change:transform}
#tape{position:absolute;left:96px;top:262px;z-index:45;background:var(--acc);color:#fff;font:900 40px 'CT','NST';padding:10px 30px 2px;transform:rotate(-6deg);
  box-shadow:0 6px 16px rgba(0,0,0,.25);opacity:0}
#tape2{position:absolute;right:120px;top:268px;z-index:45;width:150px;height:46px;background:rgba(255,255,255,.55);transform:rotate(8deg);
  box-shadow:0 2px 6px rgba(0,0,0,.12);opacity:0}
/* caption written in the polaroid strip */
#cap{position:absolute;left:110px;width:860px;top:896px;height:150px;z-index:46}
.cp{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;align-items:center;justify-content:center;text-align:center;
  font:800 50px/1.25 'CT','NST';color:var(--ink);opacity:0}
.cp span{margin:0 .04em}
.cp span.on{color:var(--acc)}
/* notebook sheet */
#note{position:absolute;left:48px;right:48px;top:1092px;height:520px;z-index:20;background:#FFFEF8;border-radius:10px;
  box-shadow:0 18px 44px rgba(0,0,0,.22);overflow:hidden;
  background-image:linear-gradient(90deg,transparent 86px,rgba(227,21,27,.45) 86px,rgba(227,21,27,.45) 89px,transparent 89px),
    repeating-linear-gradient(180deg,transparent 0 63px,rgba(59,130,246,.18) 63px 65px)}
#note .hole{position:absolute;left:30px;width:26px;height:26px;border-radius:50%;background:var(--board);box-shadow:inset 0 2px 4px rgba(0,0,0,.25)}
#nh{position:absolute;left:112px;right:120px;top:26px}
#nh .t{font:800 40px/1.3 'BT','NST';color:var(--ink)}
#nh .k{display:inline-block;margin-top:12px;font:900 60px/1.2 'CT','NST';color:var(--ink);padding:0 10px}
#pts{position:absolute;left:112px;right:120px;top:0;bottom:22px;overflow:hidden}
.pt{position:absolute;left:0;right:0;display:flex;gap:16px;align-items:flex-start;opacity:0}
.pt .n{flex:none;width:52px;height:52px;border-radius:50%;border:4px solid var(--ink);font:900 32px/44px 'CT';text-align:center;color:var(--ink);margin-top:2px}
.pt.done .n{background:#16A34A;border-color:#16A34A;color:#fff}
.pt .tx{font:800 42px/1.3 'NST','CT';color:var(--ink);min-width:0}
.pt .lb{display:block;font:800 26px/1.2 'NST','CT';color:var(--acc);margin-bottom:2px}
mark{color:inherit;background-repeat:no-repeat;background-image:linear-gradient(transparent 12%,var(--hl) 12%,var(--hl) 88%,transparent 88%);
  background-size:0% 100%;padding:0 6px;border-radius:6px}
/* end */
#end{position:absolute;inset:0;z-index:70;opacity:0;display:flex;align-items:center;justify-content:center;padding:0 90px 280px}
#end .pc{width:100%;background:#fff;padding:40px 40px 46px;text-align:center;box-shadow:0 30px 70px rgba(0,0,0,.35);transform:rotate(-2deg)}
#end img{width:230px;height:230px;border-radius:50%;border:6px solid #F3EDE2}
#end .e1{font:900 64px/1.25 'CT','NST';margin-top:16px}
#end .e3{font:800 36px 'NST','CT';color:var(--muted);margin-top:6px}
#end .fol{display:inline-flex;align-items:center;gap:16px;margin-top:26px;background:var(--acc);color:#fff;font:900 56px 'CT','NST';padding:18px 54px 10px;border-radius:999px}
#end .fol .ic{font-size:50px;margin-top:-6px}
#end .hd{margin-top:22px;font:800 34px 'NST','CT'}
#end .hd mark{background-size:100% 100%}
"""


def mark_key(txt):
    """highlight the number in a fact; without one, its first two words"""
    n = big_number(txt)
    if n and n in txt:
        i = txt.index(n)
        return E(txt[:i]) + "<mark>" + E(n) + "</mark>" + E(txt[i + len(n):])
    w = txt.split()
    return "<mark>" + E(" ".join(w[:2])) + "</mark>" + ((" " + E(" ".join(w[2:]))) if len(w) > 2 else "")


def build_html(spec, shots, sents, caps, hook_end, end_t, total, page):
    logo = f"file://{R.KIT.resolve() / page['logo']}"
    acc = accent_for(spec.get("cat", ""))
    # a new print drops every time the picture changes
    drops, last = [], None
    for s in shots:
        if s["img"] != last:
            drops.append({"a": s["a"], "img": s["img"], "rot": [-1.5, 1.8, -2.4, 2.2][len(drops) % 4]})
            last = s["img"]
    pols = "".join(f'<div class="pol" id="d{i}"><div class="ph"><img src="file://{Path(spec["images"][d["img"]]).resolve()}"></div></div>'
                   for i, d in enumerate(drops))
    # key points: one per fact, added when its sentence is spoken
    pts, meta = "", []
    for i, s in enumerate(sents):
        c = card_for(s.get("card") or s.get("fact"))
        s["has_card"] = bool(c)
        if c:
            k = len(meta)
            pts += (f'<div class="pt" id="k{k}"><div class="n">{k + 1}</div><div class="tx"><span class="lb">{E(c["label"])}</span>'
                    f'{mark_key(to_digits(c["text"]))}</div></div>')
            meta.append({"a": max(s["a"] + 0.1, hook_end + 0.2), "b": s["b"]})
    cap_html = ""
    for gi, g in enumerate(caps):
        spans = " ".join(f'<span id="w{gi}_{k}">{E(w[0])}</span>' for k, w in enumerate(g["words"]))      # spaces: the line can wrap
        cap_html += f'<div class="cp" id="g{gi}"><div>{spans}</div></div>'
    hook = spec.get("hook") or ["", ""]
    mini = spec.get("mini") or hook[0]
    holes = "".join(f'<div class="hole" style="top:{40 + j * 150}px"></div>' for j in range(4))
    data = json.dumps({"drops": drops, "shots": shots, "pts": meta, "caps": [{"a": g["a"], "b": g["b"], "w": [[x[1], x[2]] for x in g["words"]]} for g in caps],
                       "hook_end": hook_end, "end_t": end_t})
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body style="--acc:{acc}">
<div id="hdr"><div class="nm">{E(page['name'])}</div><div class="sub">{R.icon('location-dot')}<span>{E(spec.get('location', ''))}</span><span>• {E(spec['date'])}</span></div></div>
<img id="plogo" src="{logo}">
{pols}
<div id="tape">{E(spec.get('cat', '') or 'വാർത്ത')}</div><div id="tape2"></div>
<div id="cap">{cap_html}</div>
<div id="note">{holes}
<div id="nh"><div class="t" id="nt">{E(hook[0])}</div>{('<div class="k"><mark id="hk">' + E(hook[1]) + '</mark></div>') if hook[1] else ''}</div>
<div id="pts">{pts}</div></div>
<div id="hook" style="display:none"></div>
<div id="flash"></div>
<div id="end"><div class="pc"><img src="{logo}"><div class="e1">{E(page['tagline'])}</div><div class="e3">@{E(page['handle'])}</div>
<div class="fol">{R.icon('user-plus')}<span>FOLLOW</span></div><div class="hd"><mark>📌 Save • ആവശ്യമുള്ളവർക്ക് Share</mark></div></div></div>
<script>
const D={data};
const MINI={json.dumps(E(mini))}, FULL={json.dumps(E(hook[0]))};
const cl=x=>Math.max(0,Math.min(1,x)), ease=x=>1-Math.pow(1-x,3), back=x=>{{const c=1.70158,c3=c+1;return 1+c3*Math.pow(x-1,3)+c*Math.pow(x-1,2)}};
let PH=[], HEADH=0;
window.renderAt=function(t){{
  const live=t<D.end_t;
  // polaroids: the current one lands flat and big; the one before stays under it, tilted
  let cur=0; D.drops.forEach((d,i)=>{{if(t>=d.a)cur=i}});
  D.drops.forEach((d,i)=>{{
    const e=document.getElementById('d'+i), img=e.querySelector('img');
    if(i>cur||i<cur-2||!live&&i!==cur){{e.style.opacity=0;return;}}
    const p=cl((t-d.a)/0.45), b=back(p);
    if(i===cur){{e.style.opacity=cl(p*4); e.style.zIndex=12;
      e.style.transform='translateY('+(-120*(1-Math.min(1,b)))+'px) rotate('+(d.rot*(1-p)*3)+'deg) scale('+(1.18-0.18*Math.min(1.02,b))+')';}}
    else{{const k=cur-i; e.style.opacity=1; e.style.zIndex=11-k;
      e.style.transform='translate('+(k*(i%2?26:-26))+'px,'+(-k*14)+'px) rotate('+(d.rot*2.2*k)+'deg) scale('+(1-0.04*k)+')';}}
    img.style.transform='scale('+(1.0+0.10*cl((t-d.a)/6))+')';
  }});
  const dc=D.drops[cur]; document.getElementById('flash').style.opacity=(cur>0&&t-dc.a<0.1&&live)?0.25*(1-(t-dc.a)/0.1):0;
  const tp=document.getElementById('tape'); tp.style.opacity=live?cl((t-0.3)/0.1):0; tp.style.transform='rotate(-6deg) scale('+(1+0.6*Math.pow(1-cl((t-0.3)/0.3),3))+')';
  document.getElementById('tape2').style.opacity=live?cl((t-0.45)/0.1):0;
  ['hdr','plogo','note','cap'].forEach(id=>document.getElementById(id).style.opacity=live?1:0);
  // sheet: the headline large during the opening, then it shrinks to a title line and the points come in under it
  const nh=document.getElementById('nh'), nt=document.getElementById('nt'), hk=document.getElementById('hk');
  const sh=ease(cl((t-D.hook_end)/0.4));
  nt.style.fontSize=(64-28*sh)+'px'; nt.textContent=t<D.hook_end?FULL:MINI;
  nh.style.opacity=cl(t/0.15);
  if(hk){{hk.parentNode.style.display=t<D.hook_end+0.3?'inline-block':'none'; hk.parentNode.style.opacity=1-sh;
    hk.style.backgroundSize=(100*ease(cl((t-0.6)/0.5)))+'% 100%';}}
  const topY=26+nh.offsetHeight+18;
  // points: newest at the bottom; older ones move up when the sheet is full
  let vis=D.pts.map((p,i)=>i).filter(i=>t>=D.pts[i].a);
  const box=document.getElementById('pts').clientHeight, hgt=v=>v.reduce((s,i)=>s+PH[i]+16,topY);
  while(vis.length>1&&hgt(vis)>box)vis=vis.slice(1);      // the sheet is full: the oldest point leaves, no gap
  let ys=[], y=topY; vis.forEach(i=>{{ys.push(y); y+=PH[i]+16;}});
  const over=0;
  D.pts.forEach((p,i)=>{{
    const e=document.getElementById('k'+i), j=vis.indexOf(i);
    if(j<0){{e.style.opacity=0;return;}}
    const u=ease(cl((t-p.a)/0.35)), yy=ys[j]-over;
    e.style.top=yy+'px'; e.style.opacity=cl(u*2)*(yy<topY-20?0:1); e.style.transform='translateX('+(-40*(1-u))+'px)';
    e.querySelector('mark').style.backgroundSize=(100*ease(cl((t-p.a-0.3)/0.6)))+'% 100%';
    e.className='pt'+(t>p.b+0.2?' done':'');
    if(t>p.b+0.2)e.querySelector('.n').innerHTML='✓'; else e.querySelector('.n').textContent=(i+1);
  }});
  // caption in the polaroid strip
  D.caps.forEach((g,gi)=>{{const ge=document.getElementById('g'+gi), on=t>=g.a&&t<g.b&&live; ge.style.opacity=on?cl((t-g.a)/0.08):0;
    if(on)g.w.forEach((w,k)=>{{document.getElementById('w'+gi+'_'+k).className=(t>=w[0]&&t<w[1])?'on':'';}});}});
  const e=document.getElementById('end'), eu=back(cl((t-D.end_t)/0.45));
  e.style.opacity=ease(cl((t-D.end_t)/0.3)); e.querySelector('.pc').style.transform='rotate(-2deg) translateY('+(-150*(1-Math.min(1,eu)))+'px)';
}};
function fitEl(el,maxH,min){{if(!el)return;let fs=parseFloat(getComputedStyle(el).fontSize),n=0;while((el.scrollWidth>el.clientWidth+1||el.offsetHeight>maxH)&&fs>min&&n++<60){{fs-=2;el.style.fontSize=fs+'px';}}}}
window.fitAll=function(){{
  document.querySelectorAll('.cp > div').forEach(e=>{{e.parentNode.style.opacity=1;fitEl(e,146,30);e.parentNode.style.opacity=0;}});
  document.querySelectorAll('.pt .tx').forEach(e=>fitEl(e,180,28));
  fitEl(document.querySelector('#nh .k'),160,36);
  PH=D.pts.map((p,i)=>document.getElementById('k'+i).offsetHeight);
}};
</script></body></html>"""


R4.build_html = build_html      # reel4.main renders whatever build_html is set here; voice, timing and video encoding are shared

if __name__ == "__main__":
    R4.main(*sys.argv[1:])
