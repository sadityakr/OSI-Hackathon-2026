"""Graph dict -> a single self-contained HTML page (Obsidian-style force-directed view).

The vendored ``force-graph`` bundle is *inlined* so the artifact is one portable file that needs no
network and no companion assets — open it on any machine and it renders. All styling and interaction
(colour-by-type, type filters, search, click-to-inspect side panel) live here in one template.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ASSETS = Path(__file__).parent / "assets"

# type-group -> colour (dark theme, tuned to read like Obsidian's graph view)
_COLORS = {
    "document": "#e8b339",
    "section": "#6ea8fe",
    "text": "#57c7a3",
    "figure": "#f0883e",
    "table": "#e0743c",
    "equation": "#b083f0",
    "reference": "#8b93a7",
    "meta": "#c97b9b",
}
_GROUP_LABELS = {
    "document": "Paper",
    "section": "Sections",
    "text": "Text",
    "figure": "Figures",
    "table": "Tables",
    "equation": "Equations",
    "reference": "References",
    "meta": "Front-matter",
}


def render_html(graph: dict[str, Any], lib_js: str | None = None) -> str:
    """Return a complete HTML document visualizing ``graph`` (output of :func:`build_graph`)."""
    if lib_js is None:
        lib_js = (_ASSETS / "force-graph.min.js").read_text(encoding="utf-8")
    meta = graph["meta"]
    payload = json.dumps({"nodes": graph["nodes"], "links": graph["links"]}, ensure_ascii=False)
    colors = json.dumps(_COLORS)
    group_labels = json.dumps(_GROUP_LABELS)
    authors = ", ".join(meta.get("authors") or [])
    title = meta.get("title", "(untitled)")
    subtitle = " · ".join(
        p
        for p in [
            authors[:120] + ("…" if len(authors) > 120 else ""),
            meta.get("doi") or "",
            f"{meta['n_nodes']} nodes · {meta['n_links']} links · ≤{meta['max_tokens']} tok/node",
        ]
        if p
    )
    return _TEMPLATE.format(
        title=_esc(title),
        subtitle=_esc(subtitle),
        payload=payload,
        colors=colors,
        group_labels=group_labels,
        lib_js=lib_js,
    )


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title} — paper graph</title>
<style>
  :root {{
    --bg:#0e1116; --panel:#161b22; --border:#272d38; --fg:#d6dbe3; --dim:#8b93a7;
  }}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; height:100%; background:var(--bg); color:var(--fg);
    font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; overflow:hidden; }}
  #graph {{ position:fixed; inset:0; }}
  .hdr {{ position:fixed; top:0; left:0; right:0; padding:10px 16px; z-index:5;
    background:linear-gradient(180deg, rgba(14,17,22,.92), rgba(14,17,22,0));
    pointer-events:none; }}
  .hdr h1 {{ margin:0; font-size:15px; font-weight:600; letter-spacing:.2px; }}
  .hdr .sub {{ color:var(--dim); font-size:11px; margin-top:2px; }}
  .legend {{ position:fixed; top:54px; left:16px; z-index:6; background:var(--panel);
    border:1px solid var(--border); border-radius:10px; padding:10px 12px; min-width:180px; }}
  .legend h2 {{ margin:0 0 8px; font-size:11px; text-transform:uppercase; letter-spacing:.6px;
    color:var(--dim); font-weight:600; }}
  .row {{ display:flex; align-items:center; gap:8px; padding:3px 2px; cursor:pointer; user-select:none;
    border-radius:6px; }}
  .row:hover {{ background:#1d2330; }}
  .row.off {{ opacity:.4; }}
  .dot {{ width:11px; height:11px; border-radius:50%; flex:0 0 auto; }}
  .row .nm {{ flex:1; }}
  .row .ct {{ color:var(--dim); font-variant-numeric:tabular-nums; }}
  .tools {{ position:fixed; top:54px; right:16px; z-index:6; display:flex; flex-direction:column;
    gap:8px; align-items:flex-end; }}
  #search {{ background:var(--panel); border:1px solid var(--border); color:var(--fg);
    border-radius:8px; padding:7px 10px; width:210px; outline:none; }}
  #search:focus {{ border-color:#3b82f6; }}
  .btn {{ background:var(--panel); border:1px solid var(--border); color:var(--fg);
    border-radius:8px; padding:6px 10px; cursor:pointer; }}
  .btn:hover {{ background:#1d2330; }}
  #panel {{ position:fixed; top:0; right:0; bottom:0; width:340px; z-index:7; background:var(--panel);
    border-left:1px solid var(--border); transform:translateX(100%); transition:transform .18s ease;
    padding:18px 18px 24px; overflow-y:auto; }}
  #panel.open {{ transform:none; }}
  #panel .ptype {{ display:inline-block; font-size:10px; text-transform:uppercase; letter-spacing:.6px;
    padding:2px 8px; border-radius:20px; font-weight:600; }}
  #panel h3 {{ margin:10px 0 4px; font-size:15px; }}
  #panel .meta {{ color:var(--dim); font-size:11px; margin-bottom:12px; }}
  #panel .body {{ white-space:pre-wrap; font-size:13px; color:#c2c8d2;
    border-top:1px solid var(--border); padding-top:12px; }}
  #panel #p-img {{ display:none; width:100%; border-radius:8px; border:1px solid var(--border);
    margin-bottom:12px; background:#fff; }}
  #panel .x {{ position:absolute; top:12px; right:14px; cursor:pointer; color:var(--dim);
    font-size:18px; }}
  .hint {{ position:fixed; bottom:10px; left:16px; z-index:5; color:var(--dim); font-size:11px; }}
</style></head>
<body>
<div id="graph"></div>
<div class="hdr"><h1>{title}</h1><div class="sub">{subtitle}</div></div>
<div class="legend"><h2>Node types</h2><div id="legend"></div></div>
<div class="tools">
  <input id="search" placeholder="search nodes…" autocomplete="off"/>
  <button class="btn" id="fit">Fit to view</button>
</div>
<div id="panel"><span class="x" id="close">×</span>
  <span class="ptype" id="p-type"></span><h3 id="p-label"></h3>
  <div class="meta" id="p-meta"></div><img id="p-img" alt=""/>
  <div class="body" id="p-body"></div></div>
<div class="hint">drag to pan · scroll to zoom · click a node to inspect · click a legend row to toggle</div>

<script>{lib_js}</script>
<script>
const DATA = {payload};
const COLORS = {colors};
const GROUP_LABELS = {group_labels};
const LINK_STYLE = {{
  contains:{{c:'rgba(140,150,170,0.16)',w:0.5}},
  next:{{c:'rgba(140,150,170,0.10)',w:0.4}},
  cites:{{c:'rgba(139,147,167,0.30)',w:0.5}},
  'ref-figure':{{c:'rgba(240,136,62,0.55)',w:1.1}},
  'ref-table':{{c:'rgba(224,116,60,0.55)',w:1.1}},
  'ref-equation':{{c:'rgba(176,131,240,0.55)',w:1.1}},
  'ref-section':{{c:'rgba(110,168,254,0.45)',w:0.9}},
}};

// ---- state ----------------------------------------------------------------
const enabled = {{}};
Object.keys(COLORS).forEach(g => enabled[g] = true);
let query = '';
let selected = null;
const adj = new Map();            // node id -> Set of neighbour ids (for click-highlight)
DATA.links.forEach(l => {{
  const s = typeof l.source==='object'?l.source.id:l.source;
  const t = typeof l.target==='object'?l.target.id:l.target;
  if(!adj.has(s)) adj.set(s,new Set()); if(!adj.has(t)) adj.set(t,new Set());
  adj.get(s).add(t); adj.get(t).add(s);
}});

// ---- legend ---------------------------------------------------------------
const counts = {{}};
DATA.nodes.forEach(n => counts[n.group] = (counts[n.group]||0)+1);
const legendEl = document.getElementById('legend');
Object.keys(COLORS).forEach(g => {{
  if(!counts[g]) return;
  const row = document.createElement('div'); row.className='row'; row.dataset.g=g;
  row.innerHTML = `<span class="dot" style="background:${{COLORS[g]}}"></span>`
    + `<span class="nm">${{GROUP_LABELS[g]||g}}</span><span class="ct">${{counts[g]}}</span>`;
  row.onclick = () => {{ enabled[g]=!enabled[g]; row.classList.toggle('off',!enabled[g]); refresh(); }};
  legendEl.appendChild(row);
}});

// ---- graph ----------------------------------------------------------------
const elem = document.getElementById('graph');
const Graph = ForceGraph()(elem)
  .backgroundColor('#0e1116')
  .nodeId('id')
  .nodeVal('val')
  .nodeRelSize(4)
  .linkColor(l => (LINK_STYLE[l.rel]||LINK_STYLE.contains).c)
  .linkWidth(l => (LINK_STYLE[l.rel]||LINK_STYLE.contains).w)
  .linkDirectionalParticles(0)
  .cooldownTicks(180)
  .onNodeClick(node => {{ openPanel(node); }})
  .onBackgroundClick(() => {{ selected=null; closePanel(); Graph.nodeColor(Graph.nodeColor()); }})
  .nodeCanvasObjectMode(() => 'replace')
  .nodeCanvasObject((node, ctx, scale) => drawNode(node, ctx, scale))
  .nodePointerAreaPaint((node, color, ctx, scale) => paintHit(node, color, ctx, scale));

// ---- figure thumbnails: preload the inlined data-URI images (decode once, redraw on load) ----
const IMG = {{}};
DATA.nodes.forEach(n => {{
  if(!n.image) return;
  const im = new Image();
  im.onload = () => Graph.nodeColor(Graph.nodeColor());  // force a repaint once decoded
  im.src = n.image;
  IMG[n.id] = im;
}});
const THUMB_SCALE = 1.3;  // zoom at which a figure node swaps its dot for its thumbnail
function thumbReady(node, scale) {{
  const img = IMG[node.id];
  return img && img.complete && img.naturalWidth
    && (scale > THUMB_SCALE || node._match || (selected && selected.id===node.id));
}}
function thumbBox(node) {{  // fit the image into a square ~5× the node radius, preserving aspect
  const img = IMG[node.id], r = Math.sqrt(node.val) * 1.6, m = Math.max(16, r * 5);
  const ar = img.naturalWidth / img.naturalHeight;
  return ar >= 1 ? {{w: m, h: m / ar}} : {{w: m * ar, h: m}};
}}
function paintHit(node, color, ctx, scale) {{  // clickable area matches what's drawn (thumb or dot)
  ctx.fillStyle = color;
  if(thumbReady(node, scale)) {{
    const b = thumbBox(node);
    ctx.fillRect(node.x - b.w/2, node.y - b.h/2, b.w, b.h);
  }} else {{
    const r = Math.sqrt(node.val) * 1.6;
    ctx.beginPath(); ctx.arc(node.x, node.y, r, 0, 2*Math.PI); ctx.fill();
  }}
}}

Graph.d3Force('charge').strength(-220).distanceMax(600);
Graph.d3Force('link').distance(l => l.rel==='contains' ? 34 : 78).strength(0.6);
Graph.d3VelocityDecay(0.28);

function dim(node) {{
  if(query) return !(node._match);
  if(selected) return !(node.id===selected.id || (adj.get(selected.id)||new Set()).has(node.id));
  return false;
}}
function drawNode(node, ctx, scale) {{
  const r = Math.sqrt(node.val) * 1.6;
  const faded = dim(node);
  // Figure nodes: once zoomed in (or searched/selected), draw the actual figure in place of the dot.
  if(thumbReady(node, scale)) {{
    const img = IMG[node.id], b = thumbBox(node), x = node.x - b.w/2, y = node.y - b.h/2;
    ctx.globalAlpha = faded ? 0.12 : 1;
    ctx.fillStyle = COLORS[node.group] || '#888';                 // coloured frame = type cue
    ctx.fillRect(x - 1/scale, y - 1/scale, b.w + 2/scale, b.h + 2/scale);
    ctx.drawImage(img, x, y, b.w, b.h);
    if(selected && node.id===selected.id) {{
      ctx.lineWidth = 1.6/scale; ctx.strokeStyle = '#fff'; ctx.strokeRect(x, y, b.w, b.h);
    }}
    if(!faded && (node._match || scale > THUMB_SCALE)) {{
      const fs = Math.max(3, 10/scale);
      ctx.font = `400 ${{fs}}px -apple-system,Segoe UI,sans-serif`;
      ctx.fillStyle = node._match ? '#fff' : 'rgba(206,212,222,0.85)';
      ctx.textAlign='center'; ctx.textBaseline='top';
      ctx.fillText(node.label || '', node.x, y + b.h + 1.5);
    }}
    ctx.globalAlpha = 1;
    return;
  }}
  ctx.globalAlpha = faded ? 0.12 : 1;
  ctx.beginPath(); ctx.arc(node.x, node.y, r, 0, 2*Math.PI);
  ctx.fillStyle = COLORS[node.group] || '#888'; ctx.fill();
  if(selected && node.id===selected.id) {{
    ctx.lineWidth = 1.5/scale; ctx.strokeStyle='#fff'; ctx.stroke();
  }}
  // Label policy (keeps low zoom legible): structure + entity hubs get standing labels; the noisy
  // text-node sentence fragments only appear once you zoom in, or when searched/selected.
  // document title already lives in the header — don't redraw it across the centre
  const structural = node.group==='section';
  const entityHub = (node.group==='figure'||node.group==='table'||node.group==='equation'
    || node.group==='reference') && node.deg>=2;
  const show = node._match || (selected && !faded && scale>1.4)
    || structural || entityHub || scale>2.6;
  if(show && !faded) {{
    const fs = Math.max(3, (structural?12:10)/scale);
    ctx.font = `${{structural?600:400}} ${{fs}}px -apple-system,Segoe UI,sans-serif`;
    ctx.fillStyle = node._match ? '#fff'
      : structural ? 'rgba(190,210,255,0.95)' : 'rgba(206,212,222,0.78)';
    ctx.textAlign='center'; ctx.textBaseline='top';
    ctx.fillText(node.label || '', node.x, node.y + r + 1.5);
  }}
  ctx.globalAlpha = 1;
}}

// ---- filter / search refresh ---------------------------------------------
function refresh() {{
  const ns = DATA.nodes.filter(n => enabled[n.group]);
  const ok = new Set(ns.map(n=>n.id));
  const ls = DATA.links.filter(l => {{
    const s = typeof l.source==='object'?l.source.id:l.source;
    const t = typeof l.target==='object'?l.target.id:l.target;
    return ok.has(s) && ok.has(t);
  }});
  Graph.graphData({{nodes: ns, links: ls}});
}}
const searchEl = document.getElementById('search');
searchEl.oninput = () => {{
  query = searchEl.value.trim().toLowerCase();
  DATA.nodes.forEach(n => n._match = query
    && ((n.label||'').toLowerCase().includes(query) || (n.text||'').toLowerCase().includes(query)));
  Graph.nodeColor(Graph.nodeColor());  // force redraw
}};

// ---- inspector panel ------------------------------------------------------
const panel = document.getElementById('panel');
function openPanel(node) {{
  selected = node;
  const pt = document.getElementById('p-type');
  pt.textContent = node.type; pt.style.background = (COLORS[node.group]||'#888')+'22';
  pt.style.color = COLORS[node.group]||'#888';
  document.getElementById('p-label').textContent = node.label || node.id;
  const bits = [];
  if(node.heading) bits.push(node.heading);
  if(node.page!=null) bits.push('p. '+node.page);
  bits.push(node.deg+' citation'+(node.deg===1?'':'s'));
  document.getElementById('p-meta').textContent = bits.join('  ·  ');
  const pimg = document.getElementById('p-img');
  if(node.image) {{ pimg.src = node.image; pimg.style.display = 'block'; }}
  else {{ pimg.removeAttribute('src'); pimg.style.display = 'none'; }}
  const body = document.getElementById('p-body');
  if(node.ref) {{
    // a resolved reference: show its bibliographic identity, not a bare number
    const r = node.ref, esc = s => {{ const d=document.createElement('div'); d.textContent=s||''; return d.innerHTML; }};
    const line = [r.surname && r.authors.length>1 ? esc(r.surname)+' et al.' : (r.authors||[]).map(esc).join(', '),
                  r.journal?('<i>'+esc(r.journal)+'</i>'):'', r.year].filter(Boolean).join(' · ');
    document.getElementById('p-label').textContent = '['+r.n+']  '+(node.label||'');
    body.innerHTML =
      (r.title ? '<div style="font-weight:600;color:#e8edf4;margin-bottom:6px">'+esc(r.title)+'</div>' : '')
      + (line ? '<div style="color:#aeb6c4;margin-bottom:8px">'+line+'</div>' : '')
      + (r.doi ? '<div style="margin-bottom:10px"><a href="https://doi.org/'+esc(r.doi)
          +'" target="_blank" style="color:#6ea8fe">doi.org/'+esc(r.doi)+'</a>'
          +(r.is_preprint?' <span style="color:#8b93a7">· preprint</span>':'')+'</div>' : '')
      + '<div style="color:#7e8696;font-size:11px;border-top:1px solid var(--border);padding-top:10px">'
          +esc(r.raw)+'</div>';
  }} else {{
    body.textContent = node.text || '(no text)';
  }}
  panel.classList.add('open');
}}
function closePanel() {{ panel.classList.remove('open'); }}
document.getElementById('close').onclick = () => {{ selected=null; closePanel(); }};
document.getElementById('fit').onclick = () => Graph.zoomToFit(500, 60);

refresh();
Graph.onEngineStop(() => Graph.zoomToFit(400, 60));
addEventListener('resize', () => {{ Graph.width(innerWidth); Graph.height(innerHeight); }});
</script>
</body></html>"""
