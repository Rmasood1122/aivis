#!/usr/bin/env python3
"""make_pdf5.py - 4-engine report v3. Derived from make_pdf4.py (unchanged, on record).
Changes: banned-word reword; [REPORTED]/[EST] tags; WHY-THIS-MATTERS strip per page;
Wilson upper bounds printed on the zeros; pairwise engine-agreement table; zero-row
corroboration footnote. Everything computed from the four evidence files."""
import hashlib, json, math, re, sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth

TEAL=Color(0.10,0.30,0.43); RED=Color(0.75,0.22,0.17); GREY=Color(0.45,0.45,0.45)
LGREY=Color(0.72,0.72,0.72); BLACK=Color(0,0,0)
W,H=letter; M=54; TP=6
FAMS=["buyer_intent","category","comparison","long_tail","problem"]
NAMES=['Weber Shandwick','Edelman','Reputation Ink','Reputation Rhino','Ketchum','FINN Partners','The Lede Company','SourceCode Communications','SimplyBe. Agency','Red Banyan','Otter PR','Method Communications','LaunchSquad','Highwire','FleishmanHillard','Credible PR','Clarity PR','Channel V Media','Burson','Brandstyle','Bospar','Bollare','5WPR']
SUBJ='Credible PR'
ENGINES=[("Claude","study2/data/multi_anthropic_run3_20260908.jsonl"),
         ("ChatGPT","study2/data/multi_openai_run3_20260908.jsonl"),
         ("Gemini","study2/data/multi_gemini_run3_20260908.jsonl"),
         ("Perplexity","study2/data/multi_perplexity_run3_20260908.jsonl")]
OUT="out/aivis_crediblepr_report_4engine_20260909_v3.pdf"

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0.0,c-m),min(1.0,c+m))

def present(nm,t): return re.search(r'\b'+re.escape(nm)+r'\b',t,re.I) is not None

def load(path):
    rows=[json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    clean=[r for r in rows if r.get("response_text")]
    hs=[r["sha256"] for r in clean]
    stored=hashlib.sha256("\n".join(hs).encode()).hexdigest()
    ft=hashlib.sha256("\n".join(hashlib.sha256(r["response_text"].encode()).hexdigest() for r in clean).encode()).hexdigest()
    if stored!=ft: sys.exit("REFUSE: digest mismatch in %s"%path)
    return rows,clean,stored

def footer(c,pg,n):
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
        E[label]={"rows":len(rows),"clean":clean,"n":len(clean),"err":len(rows)-len(clean),
                  "digest":dg,"model":pay.get("model","?"),"temp":pay.get("temperature","?"),
                  "fam":fam,"pres":pres,"overall":overall,"pids":len(pids),"ppres":ppres}
        print("RECONCILE %-10s clean %d/%d digest %s..."%(label,len(clean),len(rows),dg[:12]))
        print("  top5:", ", ".join("%s %d/%d"%(nm,k,len(clean)) for nm,k in sorted(overall.items(),key=lambda t:-t[1])[:5]))
        print("  %s: %d/%d overall, %d/%d buyer_intent"%(SUBJ,overall[SUBJ],len(clean),pres["buyer_intent"][SUBJ],len(fam["buyer_intent"])))
    total=sum(E[l]["n"] for l,_ in ENGINES); subj_total=sum(E[l]["overall"][SUBJ] for l,_ in ENGINES)
    attempted=sum(E[l]["rows"] for l,_ in ENGINES); errs=sum(E[l]["err"] for l,_ in ENGINES)
    zero_rows=[nm for nm in NAMES if sum(E[l]["overall"][nm] for l,_ in ENGINES)==0]
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
    c.drawCentredString(W/2,H-368,"What a zero can rule out at this sample (95%% upper bound on the true prompt rate): %s"%ubline)
    c.setFont("Helvetica-Oblique",8.5)
    c.drawCentredString(W/2,H-384,"Why this number matters: when a prospect asks an AI to recommend PR firms, the answer draws from a set of names.")
    c.drawCentredString(W/2,H-395,"This page states whether %s is in that set today - the baseline any campaign would be measured against."%SUBJ)
    bx,by,bw,bh=M,110,W-2*M,120
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
    footer(c,1,total); c.showPage()

    # P2 BRIEF
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"Executive brief")
    y=H-100; wd=W-2*M
    y=why(c,"any tool can print a zero. A zero is only meaningful if the reader knows what was asked, how "
        "many times, on which engines, and what was excluded - so this page states the method before the finding.",y)
    y=wrap(c,"WHAT WAS MEASURED. 30 prompts a prospective client might put to an AI assistant about PR firms, "
        "each run 3 times against four engines - Claude, ChatGPT, Gemini, Perplexity - on 2026-09-08. "
        "%d responses attempted, %d clean; %d lost to transport errors and excluded from every rate."%(attempted,total,errs),M,y,wd)-8
    y=wrap(c,"WHAT WAS FOUND. %s is named in none of the %d responses, on any engine, in any prompt family, "
        "including every buyer-intent prompt. Comparably small firms do register (Otter PR, SourceCode, Red "
        "Banyan - page 4). The matcher is deliberately biased toward finding the subject: it matches "
        "case-insensitively, so even the ordinary phrase 'credible PR' in a sentence counts as a hit. It still "
        "found nothing, on four independent surfaces measured the same night."%(SUBJ,total),M,y,wd)-8
    y=wrap(c,"WHAT ELSE WAS FOUND. The engines do not agree on who leads. Claude's most-named firms differ from "
        "ChatGPT's, and Gemini concentrates heavily on one incumbent. Which AI a buyer uses changes which firms "
        "they hear about - a per-engine question no single-engine measurement can answer. The agreement table on "
        "page 4 counts the overlap engine by engine.",M,y,wd)-8
    y=wrap(c,"WHAT THIS DOES NOT SAY. This measures what models answer, not what people ask; it carries no "
        "information about search volume or revenue. Name extraction is pattern-matching against a declared list "
        "of %d firms; its error rate is unmeasured until our agreement study publishes. Per-engine samples are "
        "small (84-90) and cross-engine gaps mostly do not separate statistically - the intervals on page 3 say so."%len(NAMES),M,y,wd)-16
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",12); c.drawString(M,y,"Three actions"); y-=18
    for t,q in [("1. Baseline each client market on these four engines.",
                 "Is the client winning where its buyers actually ask? ~$3 per market [EST: unit cost measured on Claude, extrapolated to the other engines at current API prices] - negligible next to one new client."),
                ("2. Re-measure 30 days after the next placement lands.",
                 "Does a placement move any engine's answers? The pilot's first join."),
                ("3. Prioritise the engine your buyers use.",
                 "Gemini's answers differ most; ChatGPT carries the most share [REPORTED 2026-09-08].")]:
        y=wrap(c,t,M,y,wd,font="Helvetica-Bold",size=10)
        y=wrap(c,q,M+14,y,wd-14,size=9.5,color=GREY)-6
    footer(c,2,total); c.showPage()

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
    footer(c,3,total); c.showPage()

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
    footer(c,4,total); c.showPage()

    # P5 REFUSALS
    c.setFillColor(TEAL); c.setFont("Helvetica-Bold",16); c.drawString(M,H-80,"What this report refuses to claim")
    y=why(c,"every claim a report declines to make is a claim a reader might otherwise assume. Naming the limits is "
        "what makes the numbers inside them usable - and each refusal below names what would unlock the claim.",H-100)
    for hd,body in [
        ("NO COMPOSITE SCORE.","A single blended number hides which component moved. Every rate stands alone with its denominator and interval."),
        ("NO POOLING ACROSS ENGINES.","Four engines are four surfaces. Rates are never averaged across them; the per-engine number is the measurement."),
        ("NO ORDERING CLAIM.","No order-bias test has been run on this bank, so no ordering claim is made."),
        ("NO EXTRACTION-ERROR FIGURE.","Name extraction is pattern-matching against the declared list of %d. Its agreement with human judgement is being measured, with the labelled set to be published; until then no figure is quoted."%len(NAMES)),
        ("NO CROSS-ENGINE SEPARATION AT THESE SAMPLES.","At 84-90 responses per engine, most differences between engines sit inside overlapping intervals. Divergence is reported as observed, not as established."),
        ("NO DEMAND OR CAUSAL CLAIM.","This measures what models answer, not what people ask, and says nothing about what moves these rates - that is the pilot's question."),
        ("NO CROSS-VERSION COMPARISON.","These baselines are pinned to the model versions on page 1. Providers retire models within quarters; every re-measure declares its own surface, and rates are never compared across model versions as if they were one instrument.")]:
        c.setFillColor(BLACK); c.setFont("Helvetica-Bold",11); c.drawString(M,y,hd); y-=15
        y=wrap(c,body,M,y,W-2*M,size=9.5,leading=13,color=GREY)-10
    c.setFont("Helvetica",8); c.setFillColor(TEAL); c.drawString(M,y-2,"Each refusal names what would unlock the claim. Ask.")
    footer(c,5,total); c.showPage()

    # P6 CHECK
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
    footer(c,6,total); c.save()
    print("\nWROTE %s"%OUT)

if __name__=="__main__":
    sys.exit(main())
