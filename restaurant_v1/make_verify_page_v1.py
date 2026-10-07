#!/usr/bin/env python3
"""make_verify_page_v1.py - turn a leads CSV into one self-contained HTML checking page.

  python restaurant_v1/make_verify_page_v1.py \
      --leads restaurant_v1/verify_nyc_v1/verify_leads_assistant_v1.csv \
      --market "New York City" --out restaurant_v1/verify_nyc_v1/check_nyc_v1.html

The page lists every row of the verification sheet with two links (a Google Maps search and the lead
an assistant found), five verdict buttons, and a button that downloads the verdicts as a CSV the
analyzer accepts with --verified (columns key, verdict, plus source_url, checked_on, notes).

The page fills in NO verdict. PREREG: a verified restaurant is one "confirmed, by a human opening a
primary source (the restaurant's own site or its Google Maps listing; URL recorded)". The leads are
unchecked machine output; the lead flag is shown so the human knows where to look harder, nothing more.
Not sealed. Refuses to overwrite --out. Standard library only; the page loads nothing from the network.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

NEED = ["key", "display", "tier", "responses", "asked_area", "lead_flag", "lead_url", "lead_address", "lead_note"]

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Name check - __MARKET__</title>
<style>
:root{--bg:#f6f5f1;--card:#fff;--ink:#1b1b1b;--mut:#5d5d5d;--line:#d9d6cc;--acc:#0b5cab;--warn:#8a4b00;--warnbg:#fff3dc;--ok:#1d6b34;--okbg:#e4f3e7;--bad:#9b1c1c;--badbg:#fbe6e6}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--card:#202020;--ink:#ececec;--mut:#a5a5a5;--line:#3a3a3a;--acc:#7db7ff;--warn:#ffc46b;--warnbg:#3a2c10;--ok:#8fd9a1;--okbg:#173020;--bad:#ff9d9d;--badbg:#3a1818}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,Segoe UI,Arial,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:8px 0 4px}
.rung{border:1px solid var(--line);background:var(--warnbg);color:var(--warn);padding:10px 12px;border-radius:8px;margin:10px 0}
.defs{color:var(--mut);margin:8px 0 12px;padding-left:18px}
.defs b{color:var(--ink)}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar .count{font-weight:600;margin-right:auto}
button,.filebtn{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 10px;border-radius:6px;cursor:pointer}
button.on{background:var(--acc);border-color:var(--acc);color:#fff}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
.row{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0}
.row.done{border-left:5px solid var(--ok)}
.top{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}
.name{font-size:17px;font-weight:650}
.meta{color:var(--mut);font-size:13px}
.flag{font-size:12px;padding:2px 7px;border-radius:10px;border:1px solid var(--line)}
.flag.ok{background:var(--okbg);color:var(--ok)}
.flag.warn{background:var(--warnbg);color:var(--warn)}
.flag.bad{background:var(--badbg);color:var(--bad)}
.lead{margin:6px 0;font-size:14px;overflow-wrap:anywhere}
.links a{display:inline-block;margin:4px 10px 4px 0;color:var(--acc)}
.verd{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.extra{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.extra input{font:inherit;flex:1 1 260px;min-width:0;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
.nosrc{color:var(--bad);font-size:13px;margin-top:4px}
.hide{display:none}
</style></head><body><main>
<h1>Name check - __MARKET__ - __N__ names</h1>
<div class="rung"><b>RUNG R1 - working page, not a result.</b> The links and notes below were gathered by an AI
assistant on __LEADS_DATE__ and have NOT been checked. No verdict is filled in for you. A verdict counts only
after you open a source yourself (the restaurant's own site or its Google Maps listing).</div>
<ul class="defs">
<li><b>open</b> - a real place, open today, in the area the question asked about.</li>
<li><b>closed</b> - it existed and is permanently closed.</li>
<li><b>not_found</b> - no evidence it exists.</li>
<li><b>wrong_area</b> - real and open, but not in the area asked about.</li>
<li><b>noise</b> - not a place at all (a dish, a neighbourhood, a heading). No source needed.</li>
</ul>
<div class="bar">
<span class="count" id="count"></span>
<button data-f="all" class="on">All</button><button data-f="todo">Not done</button><button data-f="flag">Flagged leads</button>
<label class="filebtn">Resume from a saved CSV<input id="imp" type="file" accept=".csv" class="hide"></label>
<button class="primary" id="dl">Download verdicts CSV</button>
</div>
<div id="rows"></div>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
var ROWS = JSON.parse(document.getElementById("data").textContent);
var STORE = "__STORE__", OUTNAME = "__OUTNAME__";
var VERDICTS = ["open","closed","not_found","wrong_area","noise"];
var state = {};
try { state = JSON.parse(localStorage.getItem(STORE) || "{}") || {}; } catch (e) { state = {}; }
function save(){ try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {} }
function st(k){ if(!state[k]) state[k] = {verdict:"",source_url:"",checked_on:"",notes:""}; return state[k]; }
function today(){ var d = new Date(); return d.getFullYear()+"-"+("0"+(d.getMonth()+1)).slice(-2)+"-"+("0"+d.getDate()).slice(-2); }
function el(tag, cls, text){ var e = document.createElement(tag); if(cls) e.className = cls; if(text != null) e.textContent = text; return e; }
var filter = "all", nodes = {};
function flagClass(f){ return f === "ok" ? "ok" : (f === "possibly_closed" || f === "not_found") ? "bad" : "warn"; }
function mapsUrl(r){ var area = (r.asked_area || "").replace(/\s*\(\d+\)/g, "").split(";")[0].trim();
  return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(r.display + " " + area + " New York"); }
function refresh(k){
  var n = nodes[k], s = st(k);
  n.box.classList.toggle("done", !!s.verdict);
  n.btns.forEach(function(b){ b.classList.toggle("on", b.dataset.v === s.verdict); });
  n.src.value = s.source_url; n.notes.value = s.notes;
  n.nosrc.classList.toggle("hide", !(s.verdict && s.verdict !== "noise" && !s.source_url));
  var todo = !s.verdict, flagged = n.row.lead_flag !== "ok";
  n.box.classList.toggle("hide", (filter === "todo" && !todo) || (filter === "flag" && !flagged));
}
function count(){
  var done = ROWS.filter(function(r){ return st(r.key).verdict; }).length;
  document.getElementById("count").textContent = done + " of " + ROWS.length + " names have a verdict";
}
function build(){
  var host = document.getElementById("rows");
  ROWS.forEach(function(r){
    var box = el("div","row"), top = el("div","top");
    top.appendChild(el("span","name",r.display));
    top.appendChild(el("span","meta","tier " + r.tier + " - in " + r.responses + " answers - asked about: " + r.asked_area));
    top.appendChild(el("span","flag " + flagClass(r.lead_flag),"lead: " + r.lead_flag));
    box.appendChild(top);
    if (r.lead_address && r.lead_address !== "none") box.appendChild(el("div","lead","Lead address: " + r.lead_address));
    if (r.lead_note) box.appendChild(el("div","lead","Lead note: " + r.lead_note));
    var links = el("div","links"), urls = [["Open Google Maps search", mapsUrl(r)]];
    if (/^https?:\/\//.test(r.lead_url)) urls.push(["Open lead (" + (r.lead_source_type || "link") + ")", r.lead_url]);
    urls.forEach(function(u){
      var a = el("a",null,u[0]); a.href = u[1]; a.target = "_blank"; a.rel = "noopener noreferrer";
      a.addEventListener("click", function(){ st(r.key).source_url = u[1]; save(); refresh(r.key); });
      links.appendChild(a);
    });
    box.appendChild(links);
    var verd = el("div","verd"), btns = [];
    VERDICTS.forEach(function(v){
      var b = el("button",null,v); b.dataset.v = v;
      b.addEventListener("click", function(){
        var s = st(r.key);
        if (s.verdict === v) { s.verdict = ""; s.checked_on = ""; } else { s.verdict = v; s.checked_on = today(); }
        save(); refresh(r.key); count();
      });
      btns.push(b); verd.appendChild(b);
    });
    box.appendChild(verd);
    var extra = el("div","extra"), src = el("input"), notes = el("input");
    src.placeholder = "source you opened (filled when you click a link above; paste another if you used one)";
    notes.placeholder = "notes (optional)";
    src.addEventListener("input", function(){ st(r.key).source_url = src.value.trim(); save(); refresh(r.key); src.focus(); });
    notes.addEventListener("input", function(){ st(r.key).notes = notes.value; save(); });
    extra.appendChild(src); extra.appendChild(notes); box.appendChild(extra);
    var nosrc = el("div","nosrc hide","No source recorded for this verdict - click a link above or paste the page you checked.");
    box.appendChild(nosrc);
    host.appendChild(box);
    nodes[r.key] = {box:box, btns:btns, src:src, notes:notes, nosrc:nosrc, row:r};
    refresh(r.key);
  });
  count();
}
function q(s){ s = String(s == null ? "" : s); return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g,'""') + '"' : s; }
function toCsv(){
  var out = ["key,display,tier,verdict,source_url,checked_on,notes,lead_flag"];
  ROWS.forEach(function(r){ var s = st(r.key);
    out.push([r.key, r.display, r.tier, s.verdict, s.source_url, s.checked_on, s.notes, r.lead_flag].map(q).join(",")); });
  return "﻿" + out.join("\r\n") + "\r\n";
}
function parseCsv(t){
  var rows = [], row = [], cur = "", inq = false, i, c;
  t = t.replace(/^﻿/, "");
  for (i = 0; i < t.length; i++) { c = t[i];
    if (inq) { if (c === '"') { if (t[i+1] === '"') { cur += '"'; i++; } else inq = false; } else cur += c; }
    else if (c === '"') inq = true;
    else if (c === ",") { row.push(cur); cur = ""; }
    else if (c === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; }
    else if (c !== "\r") cur += c; }
  if (cur !== "" || row.length) { row.push(cur); rows.push(row); }
  return rows;
}
document.getElementById("dl").addEventListener("click", function(){
  var a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([toCsv()], {type:"text/csv;charset=utf-8"}));
  a.download = OUTNAME; document.body.appendChild(a); a.click(); a.remove();
});
document.getElementById("imp").addEventListener("change", function(ev){
  var f = ev.target.files[0]; if (!f) return;
  var rd = new FileReader();
  rd.onload = function(){
    var rows = parseCsv(String(rd.result)), h = rows[0] || [], ix = {}, n = 0;
    h.forEach(function(name, i){ ix[name.trim()] = i; });
    if (ix.key == null || ix.verdict == null) { alert("That file has no key and verdict columns."); return; }
    rows.slice(1).forEach(function(c){
      var k = (c[ix.key] || "").trim(), v = (c[ix.verdict] || "").trim().toLowerCase();
      if (!nodes[k] || VERDICTS.indexOf(v) < 0) return;
      var s = st(k); s.verdict = v;
      s.source_url = ix.source_url != null ? (c[ix.source_url] || "") : s.source_url;
      s.checked_on = ix.checked_on != null ? (c[ix.checked_on] || "") : s.checked_on;
      s.notes = ix.notes != null ? (c[ix.notes] || "") : s.notes; n++;
    });
    save(); ROWS.forEach(function(r){ refresh(r.key); }); count();
    alert(n + " verdicts loaded from the file.");
  };
  rd.readAsText(f);
});
Array.prototype.forEach.call(document.querySelectorAll(".bar button[data-f]"), function(b){
  b.addEventListener("click", function(){
    filter = b.dataset.f;
    Array.prototype.forEach.call(document.querySelectorAll(".bar button[data-f]"), function(x){ x.classList.toggle("on", x === b); });
    ROWS.forEach(function(r){ refresh(r.key); });
  });
});
build();
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--leads", required=True, help="leads CSV (one row per verification-sheet name)")
    ap.add_argument("--market", required=True, help='market name for the page heading, e.g. "New York City"')
    ap.add_argument("--leads-date", required=True, help="date the leads were gathered, YYYY-MM-DD")
    ap.add_argument("--out", required=True, help="new HTML path (must not exist)")
    ap.add_argument("--csv-name", default="verified_v1.csv", help="file name the page offers for the download")
    a = ap.parse_args()

    with open(a.leads, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in NEED if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit("REFUSE: %s lacks columns %s" % (a.leads, missing))
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in reader]
    keys = [r["key"] for r in rows]
    if not rows or len(set(keys)) != len(keys) or not all(keys):
        sys.exit("REFUSE: %s has no rows, a blank key, or a repeated key" % a.leads)

    out = Path(a.out)
    data = json.dumps(rows, ensure_ascii=True).replace("</", "<\\/")
    page = (PAGE.replace("__DATA__", data).replace("__MARKET__", a.market).replace("__N__", str(len(rows)))
            .replace("__LEADS_DATE__", a.leads_date).replace("__OUTNAME__", a.csv_name)
            .replace("__STORE__", "aivis_verify_" + out.stem))
    with open(out, "x", encoding="utf-8", newline="\n") as f:   # "x": never overwrite
        f.write(page)
    print("WROTE %s | names %d | POPULATION rows of %s" % (out, len(rows), a.leads))


if __name__ == "__main__":
    main()
