#!/usr/bin/env python3
"""make_pdf6.py - 4-engine report v4. make_pdf5.py is UNCHANGED and IMPORTED:
wilson/present/load and every constant come from it, so v4 counts cannot drift
from v3 (B7 lesson). New in v4: P5 family-x-engine grid; P6 position-in-answer
(first-three, legal at 23 candidates per the D1 floor); P7 verbatim exhibits
with row hashes inside EXHIBIT markers; P8 refusals gain NO SOURCE/CITATION
TABLE (URL count computed at emit, never typed) and NO SENTIMENT SCORE, and
the ordering refusal is restated as observed-not-validated. Pages 1-9.
Refuses to overwrite any existing path."""
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import make_pdf5 as m5
from make_pdf5 import wilson,present,load
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth

for req in ("ENGINES","NAMES","SUBJ","FAMS","OUT","TEAL","RED","GREY","LGREY","BLACK"):
    if not hasattr(m5,req): sys.exit("REFUSE: make_pdf5.%s missing - import contract broken"%req)
ENGINES=m5.ENGINES; NAMES=m5.NAMES; SUBJ=m5.SUBJ; FAMS=m5.FAMS
TEAL=m5.TEAL; RED=m5.RED; GREY=m5.GREY; LGREY=m5.LGREY; BLACK=m5.BLACK
W,H=letter; M=54; TP=9
OUT=str(Path(m5.OUT).with_name("aivis_crediblepr_report_4engine_20260909_v6.pdf"))
EXB="--- EXHIBIT BEGIN ---"
EXE="--- EXHIBIT END ---"

def footer(c,pg):
    c.setFont("Helvetica",7); c.setFillColor(GREY)
    c.drawCentredString(W/2,28,"aivis - four evidence files, digests on page %d - page %d of %d"%(TP,pg,TP))

def wrap(c,text,x,y,width,font="Helvetica",size=10,leading=14,color=BLACK):
    c.setFillColor(color); c.setFont(font,size); line=""
    for w_ in text.split():
        t=(line+" "+w_).strip()
        if stringWidth(t,font,size)<=width: line=t
        else: c.drawString(x,y,line); y-=leading; line=w_
    if line: c.drawString(x,y,line); y-=leading
    return y

def why(c,text,y):
    return wrap(c,"WHY THIS PAGE MATTERS - "+text,M,y,W-2*M,
                font="Helvetica-Oblique",size=8.5,leading=11,color=GREY)-8

UMAP={"\u2014":"-","\u2013":"-","\u2018":"'","\u2019":"'","\u201c":'"',"\u201d":'"',
      "\u2022":"-","\u2026":"...","\u00a0":" ","\u2192":"->","\u00b7":"-"}
def latin(t):
    for k,v in UMAP.items(): t=t.replace(k,v)
    return t.encode("latin-1","replace").decode("latin-1")

def first3_names(text):
    pos=[]
    for nm in NAMES:
        mt=re.search(r'\b'+re.escape(nm)+r'\b',text,re.I)
        if mt: pos.append((mt.start(),nm))
    return [nm for _,nm in sorted(pos)[:3]]

def main():
    E={}
    for label,path in ENGINES:
        rows,clean,dg=load(path)
        pay=clean[0]["request_payload"]
        fam={f:[r for r in clean if r.get("family")==f] for f in FAMS}
        pres={f:{nm:sum(1 for r in fam[f] if present(nm,r["response_text"])) for nm in NAMES} for f in FAMS}
        overall={nm:sum(pres[f][nm] for f in FAMS) for nm in NAMES}
        pids=sorted({r.get("prompt_id") for r in clean})
        byp={pid:[r for r in clean if r.get("prompt_id")==pid] for pid in pids}
        ppres={nm:sum(1 for pid in pids if any(present(nm,r["response_text"]) for r in byp[pid])) for nm in NAMES}
        fam_pp={}
        for f in FAMS:
            fp=sorted({r.get("prompt_id") for r in fam[f]})
            fbyp={pid:[r for r in fam[f] if r.get("prompt_id")==pid] for pid in fp}
            fam_pp[f]=(len(fp),{nm:sum(1 for pid in fp if any(present(nm,r["response_text"]) for r in fbyp[pid])) for nm in NAMES})
        f3={nm:sum(1 for pid in pids if any(nm in first3_names(r["response_text"]) for r in byp[pid])) for nm in NAMES}
        urls=sum(r["response_text"].count("http") for r in clean)
        E[label]={"rows":len(rows),"clean":clean,"n":len(clean),"err":len(rows)-len(clean),
                  "digest":dg,"model":pay.get("model","?"),"temp":pay.get("temperature","?"),
                  "fam":fam,"pres":pres,"overall":overall,"pids":len(pids),"ppres":ppres,
                  "fam_pp":fam_pp,"f3":f3,"urls":urls}
        print("RECONCILE %-10s clean %d/%d digest %s..."%(label,len(clean),len(rows),dg[:12]))
        print("  top5:", ", ".join("%s %d/%d"%(nm,k,len(clean)) for nm,k in sorted(overall.items(),key=lambda t:-t[1])[:5]))
        print("  %s: %d/%d overall, %d/%d buyer_intent"%(SUBJ,overall[SUBJ],len(clean),pres["buyer_intent"][SUBJ],len(fam["buyer_intent"])))
        print("  first-three top3:", ", ".join("%s %d/%d"%(nm,k,len(pids)) for nm,k in sorted(f3.items(),key=lambda t:-t[1])[:3]))
        print("  URLS in stored text: %d"%urls)
    total=sum(E[l]["n"] for l,_ in ENGINES); subj_total=sum(E[l]["overall"][SUBJ] for l,_ in ENGINES)
    attempted=sum(E[l]["rows"] for l,_ in ENGINES); errs=sum(E[l]["err"] for l,_ in ENGINES)
    zero_rows=[nm for nm in NAMES if sum(E[l]["overall"][nm] for l,_ in ENGINES)==0]
    url_total=sum(E[l]["urls"] for l,_ in ENGINES)
    outp=Path(OUT)
    if outp.exists(): sys.exit("REFUSE: %s exists"%OUT)

    c=pdfcanvas.Canvas(OUT,pagesize=letter)
    # P1 COVER
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",28); c.drawString(M,H-90,"aivis")
    c.setFillColor(GREY); c.setFont("Helvetica",11); c.drawString(M,H-112,"AI VISIBILITY MEASUREMENT - FOUR ENGINES")
    c.setFillColor(BLACK); c.setFont("Helvetica-Bold",20); c.drawString(M,H-140,SUBJ)
    c.setFont("Helvetica",10); c.setFillColor(GREY); c.drawString(M,H-158,"Prepared for Max Muir - collected 2026-09-08, one night, one prompt bank")
    c.setFillColor(RED); c.setFont("Helvetica-Bold",58); c.drawCentredString(W/2,H-290,"%d of %d"%(subj_total,total))
    c.setFillColor(BLACK); c.setFont("Helvetica",12)
    c.drawCentredString(W/2,H-320,"%s appears in %d of %d clean AI responses (%d attempted), across four engines."%(SUBJ,subj_total,total,attempted))
    perline=" - ".join("%s %d/%d"%(l,E[l]["overall"][SUBJ],E[l]["n"]) for l,_ in ENGINES)
    c.setFont("Helvetica",10); c.drawCentredString(W/2,H-338,perline)
    tp2=sum(E[l]["pids"] for l,_ in ENGINES)
    c.setFont("Helvetica",9); c.setFillColor(GREY)
    c.drawCentredString(W/2,H-354,"0 of %d prompts on any engine - the 3 runs per prompt are near-replicates, so the prompt is the sampling unit"%tp2)
    ubline=" - ".join("%s <= %.1f%%"%(l,wilson(0,E[l]["pids"])[1]*100) for l,_ in ENGINES)
    c.drawCentredString(W/2,H-368,"What a zero can rule out at this sample (95% upper bound on the true prompt rate):")
    c.drawCentredString(W/2,H-379,ubline)
    c.setFont("Helvetica-Oblique",8.5)
    c.drawCentredString(W/2,H-393,"Why this number matters: when a prospect asks an AI to recommend PR firms, the answer draws from a set of names.")
    c.drawCentredString(W/2,H-404,"This page states whether %s is in that set today - the baseline any campaign would be measured against."%SUBJ)
    bx,by,bw,bh=M,104,W-2*M,130
    c.setStrokeColor(TEAL); c.rect(bx,by,bw,bh)
    c.setFont("Helvetica-Bold",8); c.setFillColor(TEAL); yy=by+bh-14
    c.drawString(bx+10,yy,"BANK pr_agency_v1 - 30 PROMPTS, 5 FAMILIES - 3 RUNS/PROMPT - RUNG R1"); yy-=13
    for l,_ in ENGINES:
        e=E[l]
        c.drawString(bx+10,yy,"%-10s MODEL %s - TEMP %s - CLEAN %d of %d - SHA-256 %s...%s"%(
            l.upper(),e["model"],e["temp"],e["n"],e["rows"],e["digest"][:8],e["digest"][-5:])); yy-=13
    c.setFont("Helvetica",7.5); c.setFillColor(GREY)
    c.drawString(bx+10,yy,"ChatGPT measured via the OpenAI consumer-chat alias 'chat-latest'; the concrete snapshot is not disclosed by the")
    c.drawString(bx+10,yy-10,"API at call time. Claude rejects the temperature parameter; it is omitted and declared. Gemini free tier: inputs")
    c.drawString(bx+10,yy-20,"and outputs may be used by Google to improve its models; this bank contains only generic prospect questions,")
    c.drawString(bx+10,yy-30,"no client data. Copilot excluded (no public API). Grok excluded (<3% share, REPORTED 2026-09-08). All engines")
    c.drawString(bx+10,yy-40,"are developer-API surfaces; consumer apps add search and memory.")
    footer(c,1); c.showPage()

    # P2 BRIEF
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Executive brief")
    y=H-100; wd=W-2*M
    y=why(c,"any tool can print a zero. A zero is only meaningful if the reader knows what was asked, how "
        "many times, on which engines, and what was excluded - so this page states the method before the finding.",y)
    y=wrap(c,"WHAT WAS MEASURED. 30 prompts a prospective client might put to an AI assistant about PR firms, "
        "each run 3 times against four engines - Claude, ChatGPT, Gemini, Perplexity - on 2026-09-08. "
        "%d responses attempted, %d clean; %d lost to transport errors and excluded from every rate."%(attempted,total,errs),M,y,wd)-8
    y=wrap(c,"WHAT WAS FOUND. %s is named in none of the %d responses, on any engine, in any prompt family, "
        "including every buyer-intent prompt. Comparably small firms do register (page 4). The matcher is "
        "deliberately biased toward finding the subject: it matches case-insensitively, so even the ordinary "
        "phrase 'credible PR' in a sentence counts as a hit. It still found nothing, on four independent "
        "surfaces measured the same night."%(SUBJ,total),M,y,wd)-8
    y=wrap(c,"WHAT ELSE WAS FOUND. The engines do not agree on who leads. Claude's most-named firms differ from "
        "ChatGPT's, and Gemini concentrates heavily on one incumbent. Which AI a buyer uses changes which firms "
        "they hear about - a per-engine question no single-engine measurement can answer. Pages 5 and 6 break "
        "this down by prompt family and by position in the answer.",M,y,wd)-8
    y=wrap(c,"WHAT THIS DOES NOT SAY. This measures what models answer, not what people ask; it carries no "
        "information about search volume or revenue. Name extraction is pattern-matching against a declared list "
        "of %d firms; its error rate is unmeasured until the agreement study publishes. Per-engine samples are "
        "small (84-90) and cross-engine gaps mostly do not separate statistically - the intervals on page 3 say so."%len(NAMES),M,y,wd)-16
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",12); c.drawString(M,y,"Three actions"); y-=18
    for t,q in [("1. Baseline each client market on these four engines.",
                 "Is the client winning where its buyers actually ask? One baseline per client market, same bank, same evidence trail as this report."),
                ("2. Re-measure 30 days after the next placement lands.",
                 "Does a placement move any engine's answers? The pilot's first join."),
                ("3. Prioritise the engine your buyers use.",
                 "Gemini's answers differ most; ChatGPT carries the most share [REPORTED 2026-09-08].")]:
        y=wrap(c,t,M,y,wd,font="Helvetica-Bold",size=10)
        y=wrap(c,q,M+14,y,wd-14,size=9.5,color=GREY)-6
    footer(c,2); c.showPage()

    # P3 CHART
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Who each engine names - and who it doesn't")
    y=why(c,"the four engines disagree about who leads, and every buyer uses one engine at a time - so an average "
        "across them would describe a market nobody is in. Rates are counted per PROMPT, not per response, because "
        "the 3 runs of one prompt are near-replicates: counting them separately would triple the sample without "
        "adding information. The whiskers show where the true rate plausibly sits at this sample size.",H-100)
    x0=M+150; pw=W-M-x0-24; ytop=y-6
    c.setFont("Helvetica",7); c.setFillColor(GREY); XMAX=0.60
    for pct in (0,15,30,45,60):
        xx=x0+(pct/100.0)/XMAX*pw
        c.drawCentredString(xx,ytop,"%d%%"%pct)
        c.setStrokeColor(LGREY); c.line(xx,ytop-6,xx,150)
    yb=ytop-14; bh2=10; gap=4; ggap=14
    for l,_ in ENGINES:
        e=E[l]; np_=e["pids"]
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold",9)
        c.drawString(M,yb,"%s  (%d prompts x 3 runs, %s)"%(l,np_,e["model"])); yb-=bh2+6
        top3=sorted(e["ppres"].items(),key=lambda t:-t[1])[:3]
        for nm,k in top3+[(SUBJ,e["ppres"][SUBJ])]:
            lo,hi=wilson(k,np_); p=k/np_; col=RED if nm==SUBJ else TEAL
            c.setFillColor(BLACK); c.setFont("Helvetica-Bold" if nm==SUBJ else "Helvetica",7.5)
            c.drawRightString(x0-6,yb-bh2+2,"%s %d/%d"%(nm,k,np_))
            c.setFillColor(col)
            if p>0: c.rect(x0,yb-bh2,min(p,XMAX)/XMAX*pw,bh2,fill=1,stroke=0)
            c.setStrokeColor(col); c.setLineWidth(1)
            xl,xh=x0+min(lo,XMAX)/XMAX*pw,x0+min(hi,XMAX)/XMAX*pw; ym=yb-bh2/2
            c.line(xl,ym,xh,ym); c.line(xl,ym-3,xl,ym+3); c.line(xh,ym-3,xh,ym+3)
            yb-=bh2+gap
        yb-=ggap
    wrap(c,"Share of PROMPTS naming each firm - a prompt counts if any of its 3 runs names it. Each engine's three "
        "most-named firms, then %s in red. Whiskers are 95%% Wilson intervals at the prompt level, the honest "
        "sampling unit given near-replicate runs. Where intervals overlap, no separation is claimed."%SUBJ,M,138,W-2*M,size=8,leading=11,color=GREY)
    footer(c,3); c.showPage()

    # P4 FULL TABLE
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"All candidates, all engines")
    y=why(c,"measuring the subject alone cannot distinguish 'these models never name boutiques' from 'these models "
        "do not name this boutique'. The %d competitor rows are the control: small firms that DO register prove the "
        "instrument finds small firms."%(len(NAMES)-1),H-100)
    cx=[M,M+205,M+280,M+355,M+430,M+505]
    c.setFont("Helvetica-Bold",7.5); c.setFillColor(BLACK)
    c.drawString(cx[0],y,"candidate (overall presence)")
    for i,(l,_) in enumerate(ENGINES): c.drawString(cx[i+1],y,"%s n=%d"%(l,E[l]["n"]))
    y-=12
    order=sorted(NAMES,key=lambda nm:-sum(E[l]["overall"][nm] for l,_ in ENGINES))
    for nm in order:
        c.setFont("Helvetica-Bold" if nm==SUBJ else "Helvetica",7.5)
        c.setFillColor(RED if nm==SUBJ else BLACK); c.drawString(cx[0],y,nm[:34])
        for i,(l,_) in enumerate(ENGINES):
            k=E[l]["overall"][nm]
            c.setFillColor(LGREY if k==0 else (RED if nm==SUBJ else BLACK))
            c.drawString(cx[i+1],y,str(k))
        y-=11
    y-=8
    y=wrap(c,"%d of %d declared candidates scored zero on every engine: %s. The subject's zero is one of %d, "
        "found by a list declared before the run - not an artifact of a list built to find it."%(
        len(zero_rows),len(NAMES),", ".join(zero_rows),len(zero_rows)),M,y,W-2*M,size=8.5,leading=12)-4
    bi_parts=[]
    for l,_ in ENGINES:
        nbi=len(E[l]["fam"]["buyer_intent"]); ub=wilson(0,nbi)[1]*100
        bi_parts.append("%s 0/%d (<=%.0f%%)"%(l,nbi,ub))
    y=wrap(c,"Buyer-intent prompts specifically - the questions asked at the moment of hiring - with the 95%% upper "
        "bound each zero supports: %s: %s. Small samples give wide bounds; printing them wide is the point."%(
        SUBJ," - ".join(bi_parts)),M,y,W-2*M,size=8.5,leading=12)-4
    y=wrap(c,"Transport errors were not evenly distributed (Perplexity's fell in one family), so every rate in the "
        "evidence prints against its own family denominator, never a pooled one.",M,y,W-2*M,size=8.5,leading=12,color=GREY)-6
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",10); c.drawString(M,y,"How much the engines agree"); y-=13
    labels=[l for l,_ in ENGINES]
    top5={l:set(nm for nm,_k in sorted(E[l]["ppres"].items(),key=lambda t:-t[1])[:5]) for l in labels}
    pair_txt=[]
    for i in range(len(labels)):
        for j in range(i+1,len(labels)):
            a,b=labels[i],labels[j]
            pair_txt.append("%s-%s %d/5"%(a[:4],b[:4],len(top5[a]&top5[b])))
    y=wrap(c,"Overlap of each pair's five most-named firms: "+" - ".join(pair_txt)+
        ". Fewer shared names means a buyer's engine choice changes which firms they hear about.",M,y,W-2*M,size=8.5,leading=12)-6
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",10); c.drawString(M,y,"Three of the buyer-intent prompts, verbatim"); y-=13
    bank=json.loads(Path("study2/config/prompts_pr_agency_v1.json").read_text(encoding="utf-8"))
    for pr2 in bank["families"]["buyer_intent"][:3]:
        y=wrap(c,'"%s"'%pr2["text"],M,y,W-2*M,size=8.5,leading=11,color=GREY)-2
    y=wrap(c,"The category structure of the bank is public; the full instantiated prompt set ships to the audited "
        "party only, so it cannot be optimised against.",M,y,W-2*M,size=8,leading=11)
    footer(c,4); c.showPage()

    # P5 FAMILY x ENGINE GRID  (new)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Five prompt families, four engines")
    y=why(c,"a zero on 'best PR firms' and a zero on 'should I hire a firm or do it myself' are different business "
        "problems. The five families are declared prompt text, not simulated audiences - and transport errors "
        "clustered by family (a measured property of this run), so every cell prints its own denominator.",H-100)
    gx=[M,M+168,M+256,M+344,M+432]
    c.setFont("Helvetica-Bold",7.5); c.setFillColor(BLACK)
    c.drawString(gx[0],y,"family (prompt-level)")
    for i,(l,_) in enumerate(ENGINES): c.drawString(gx[i+1],y,l)
    y-=13
    for f in FAMS:
        c.setFont("Helvetica-Bold",8); c.setFillColor(TEAL); c.drawString(gx[0],y,f); y-=11
        c.setFont("Helvetica",7.2); c.setFillColor(RED); c.drawString(gx[0]+8,y,"%s"%SUBJ[:22])
        for i,(l,_) in enumerate(ENGINES):
            nfp,pp=E[l]["fam_pp"][f]; k=pp[SUBJ]
            ub=wilson(k,nfp)[1]*100 if nfp else 0.0
            c.setFillColor(RED)
            c.drawString(gx[i+1],y,"%d/%d (<=%.0f%%)"%(k,nfp,ub) if nfp else "no clean prompts")
        y-=10
        c.setFillColor(GREY); c.setFont("Helvetica",7.2); c.drawString(gx[0]+8,y,"most-named")
        for i,(l,_) in enumerate(ENGINES):
            nfp,pp=E[l]["fam_pp"][f]
            if nfp:
                nm,k=sorted(pp.items(),key=lambda t:(-t[1],t[0]))[0]
                if k==0:
                    c.setFillColor(LGREY); c.drawString(gx[i+1],y,"none of %d named"%len(NAMES))
                else:
                    c.setFillColor(BLACK); c.drawString(gx[i+1],y,"%s %d/%d"%(nm[:13],k,nfp))
            else:
                c.setFillColor(LGREY); c.drawString(gx[i+1],y,"-")
        y-=15
    y-=4
    y=wrap(c,"Reading the grid: the subject's cell shows presence with the 95%% Wilson upper bound its zero (or count) "
        "supports at that family's prompt count; the second line names the family's most-named firm on that engine. "
        "Family-level samples are small (5-6 prompts) - the bounds are wide, and printing them wide is the point. "
        "Per-family tables for all %d candidates are reproducible from the evidence files."%len(NAMES),M,y,W-2*M,size=8.5,leading=12,color=GREY)
    footer(c,5); c.showPage()

    # P6 POSITION IN ANSWER (new)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Named early, or merely named")
    y=why(c,"being one name in a list of ten is not the same as being the first name a buyer reads. This page counts, "
        "per prompt, whether a firm appears among the FIRST THREE distinct candidate names in the answer text, by "
        "first occurrence. The candidate list holds %d names, above the five-name floor this metric requires - a "
        "shorter list would make first-three collapse into mention."%len(NAMES),H-100)
    for l,_ in ENGINES:
        e=E[l]; np_=e["pids"]
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold",10)
        c.drawString(M,y,"%s  (%d prompts, %s)"%(l,np_,e["model"])); y-=14
        top3=sorted(e["f3"].items(),key=lambda t:(-t[1],t[0]))[:3]
        for nm,k in top3+[(SUBJ,e["f3"][SUBJ])]:
            lo,hi=wilson(k,np_)
            c.setFillColor(RED if nm==SUBJ else BLACK)
            c.setFont("Helvetica-Bold" if nm==SUBJ else "Helvetica",8.5)
            c.drawString(M+14,y,"%-26s %2d/%d   95%% CI %4.0f-%3.0f%%"%(nm[:26],k,np_,lo*100,hi*100)); y-=12
        y-=8
    y-=2
    y=wrap(c,"A prompt counts for a firm if ANY of its 3 runs places that firm in the answer's first three distinct "
        "candidate names. This is an observation about where names sit in these stored answers - it is not a "
        "validated ordering metric; see the refusal on page 8 for exactly what is and is not claimed.",M,y,W-2*M,size=8.5,leading=12,color=GREY)
    footer(c,6); c.showPage()

    # P7 EXHIBITS (new)
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"What the engines actually said")
    y=why(c,"every number in this report is computed from stored response text, and this page shows some of that "
        "text. Selection is by fixed rule, not curation: for each engine, its most-named firm, then the first "
        "buyer-intent row in file order naming that firm (first clean row anywhere if buyer-intent has none). "
        "Verbatim model text sits between the EXHIBIT markers; it is the engines' language, not aivis's. "
        "The excerpt is windowed around that firm's first mention; whitespace and typography are normalised for layout - the byte-exact text lives in the "
        "evidence file at the row hash printed above each exhibit.",H-100)
    for label,_ in ENGINES:
        e=E[label]
        top_nm=sorted(e["ppres"].items(),key=lambda t:(-t[1],t[0]))[0][0]
        pick=next((r for r in e["fam"]["buyer_intent"] if present(top_nm,r["response_text"])),None)
        rule="first buyer-intent row naming it"
        if pick is None:
            pick=next((r for r in e["clean"] if present(top_nm,r["response_text"])),None)
            rule="first clean row naming it (none in buyer-intent)"
        if pick is None: continue
        c.setFillColor(TEAL); c.setFont("Helvetica-Bold",9)
        c.drawString(M,y,"%s - most-named firm %s - %s"%(label,top_nm,rule)); y-=11
        c.setFillColor(GREY); c.setFont("Courier",6.5)
        c.drawString(M,y,"prompt %s - run %s - row sha256 %s"%(pick.get("prompt_id"),pick.get("run_index"),pick.get("sha256"))); y-=10
        c.setFillColor(BLACK); c.setFont("Courier",6.5); c.drawString(M,y,EXB); y-=9
        t=latin(pick["response_text"])
        mt=re.search(r'\b'+re.escape(top_nm)+r'\b',t,re.I)
        st=0
        if mt and mt.end()>430:
            st=max(0,mt.start()-140); st=t.rfind(" ",0,st)+1
        seg=t[st:st+430]
        cut=("[...] " if st>0 else "")+seg+(" [...truncated for layout - full text in the evidence file at the row hash above]" if st+430<len(t) else "")
        y=wrap(c,cut,M,y,W-2*M,font="Courier",size=6.5,leading=8.5)-1
        c.setFillColor(BLACK); c.setFont("Courier",6.5); c.drawString(M,y,EXE); y-=16
    footer(c,7); c.showPage()

    # P8 REFUSALS
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"What this report refuses to claim")
    y=why(c,"every claim a report declines to make is a claim a reader might otherwise assume. Naming the limits is "
        "what makes the numbers inside them usable - and each refusal below names what would unlock the claim.",H-100)
    for hd,body in [
        ("NO COMPOSITE SCORE.","A single blended number hides which component moved. Every rate stands alone with its denominator and interval."),
        ("NO POOLING ACROSS ENGINES.","Four engines are four surfaces. Rates are never averaged across them; the per-engine number is the measurement."),
        ("POSITION-IN-ANSWER: OBSERVED, NOT VALIDATED.","Page 6 counts who appears in an answer's first three names. That is an observation about these stored responses, not a validated ordering metric: no order-flip test has been run on this bank, so no claim is made that the ordering is stable or meaningful. The order-flip delta is the unlock."),
        ("NO EXTRACTION-ERROR FIGURE.","Name extraction is pattern-matching against the declared list of %d. Its agreement with human judgement is being measured, with the labelled set to be published; until then no figure is quoted."%len(NAMES)),
        ("NO SOURCE OR CITATION TABLE.","Which domains the engines cite is the most actionable data in this category, and this run cannot show it honestly: the v1 runner stored response text only, and that text contains %d URLs across all %d clean responses [computed at emit time]. Unlocked by capturing each engine's citation fields from the next run onward."%(url_total,total)),
        ("NO SENTIMENT SCORE.","Sentiment classifiers ship unvalidated across this category. None exists here with a published agreement figure, so no sentiment number ships. The unlock is the same agreement study that governs extraction."),
        ("NO CROSS-ENGINE SEPARATION AT THESE SAMPLES.","At 84-90 responses per engine, most differences between engines sit inside overlapping intervals. Divergence is reported as observed, not as established."),
        ("NO DEMAND OR CAUSAL CLAIM.","This measures what models answer, not what people ask, and says nothing about what moves these rates - that is the pilot's question."),
        ("NO CROSS-VERSION COMPARISON.","These baselines are pinned to the model versions on page 1. Providers retire models within quarters; every re-measure declares its own surface, and rates are never compared across model versions as if they were one instrument.")]:
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold",10.5); c.drawString(M,y,hd); y-=13
        y=wrap(c,body,M,y,W-2*M,size=9,leading=12,color=GREY)-7
    c.setFont("Helvetica",8); c.setFillColor(TEAL); c.drawString(M,y-2,"Each refusal names what would unlock the claim. Ask.")
    footer(c,8); c.showPage()

    # P9 CHECK
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Check this yourself")
    y=why(c,"reports in this category ask to be trusted. This one ships its raw material instead. If the check "
        "fails, the report is wrong - that is the point of the check.",H-100)
    y=wrap(c,"Four evidence files ship with this report - every response, its request payload, its hash - plus "
        "verify_evidence.py, a checker that needs only standard Python. No install, nothing from us. One command "
        "per file:",M,y,W-2*M,size=9.5)-4
    c.setFont("Courier",6.6); c.setFillColor(BLACK)
    for l,path in ENGINES:
        fn=Path(path).name
        c.drawString(M,y,"python verify_evidence.py %s \\"%fn); y-=9
        c.drawString(M,y,"  --expect %s"%E[l]["digest"]); y-=12
    y-=6
    y=wrap(c,"Expected last line each time: VERDICT PASS.",M,y,W-2*M,font="Helvetica-Bold",size=9.5)-2
    y=wrap(c,"WHAT PASS MEANS: the stored text and the stored hashes are consistent with each other. The file has "
        "not been edited since it was written.",M,y,W-2*M,size=9,leading=12)-3
    y=wrap(c,"WHAT PASS DOES NOT MEAN: that the responses came from the engine named in the payload, or that the "
        "run happened as described. A hash cannot establish either. Ask for the console receipt and the probe record.",M,y,W-2*M,size=9,leading=12)-8
    wrap(c,"If you run this and any verdict is anything but PASS, that is a finding - send it back.",M,y,W-2*M,font="Helvetica-Bold",size=10,color=TEAL)
    footer(c,9); c.save()
    print("\nWROTE %s"%OUT)
    print("GRADE NEXT: digest, banned-word grep (exhibit blocks excluded per amended D04), placeholder count, eyeball.")

if __name__=="__main__":
    main()
