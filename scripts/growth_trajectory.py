#!/usr/bin/env python3
import json
import math
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import scripts.monetization_corpus as mc

ROOT = "data/growth_trajectory"

SPIRITUAL = ["引き寄せ","潜在意識","宇宙","願い","願望","豊か","波動","周波数","エネルギー","現実創造","叶","執着","手放"]
MONEY = ["お金","収入","臨時収入","金運","円","万円","通帳","財布","豊かさ"]
SCIENCE = ["脳","心理","認知","神経","科学","RAS","自律神経","ホルモン","セロトニン","量子"]
DAILY = ["朝","昼","夜","寝","布団","コーヒー","スマホ","LINE","仕事","予定","家","玄関","財布","電車","コンビニ","風呂","ご飯","散歩","太陽","スーパー","レジ","机","カレンダー"]
BODY = ["疲","眠","息","呼吸","体","身体","胸","頭","落ち着","焦","不安","気分","楽","苦し","心地"]
DIRECT = ["あなた","君","みんな","フォロワー","人は"]
FIRST = ["僕","私","俺","自分"]
ACTION = ["やってみ","してみ","試して","今日","今すぐ","一回","書いて","口に出","見てみ"]
OFFER = ["無料","プレゼント","配布","特典","note","講座","コンサル","オプチャ","オープンチャット","メルマガ","LINE","受け取","プロフィール","プロフ","リンク"]


def has_any(text, words):
    low = text.lower()
    return any(w.lower() in low for w in words)


def nonblank_lines(text):
    return [x.strip() for x in text.splitlines() if x.strip()]


def sentences(text):
    return [x.strip() for x in re.split(r"[。！？!?]+", text) if x.strip()]


def feats(text):
    lines = nonblank_lines(text)
    sents = sentences(text)
    return {
        "spiritual": has_any(text, SPIRITUAL),
        "money": has_any(text, MONEY),
        "science": has_any(text, SCIENCE),
        "daily_scene": has_any(text, DAILY),
        "body_feeling": has_any(text, BODY),
        "direct_reader": has_any(text, DIRECT),
        "first_person": has_any(text, FIRST),
        "immediate_action": has_any(text, ACTION),
        "offer_cta": has_any(text, OFFER),
        "question": ("？" in text or "?" in text),
        "numbers": bool(re.search(r"\d", text)),
        "quotes": ("「" in text and "」" in text),
        "contrast": has_any(text,["でも","実は","じゃない","ではなく","むしろ","逆","違う","よりも"]),
        "causal": has_any(text,["だから","なぜなら","理由","つまり","その結果","というのも"]),
        "personal_story": has_any(text,["僕は","私は","俺は","昔","当時","前は","ある日","その時","経験"]),
        "negation_reframe": bool(re.search(r"(じゃない|ではない|んじゃない|違う)[。\n]", text)),
        "aphorism": bool(re.search(r"[^\n。]{1,18}は、?[^\n。]{1,24}[。\n]", text)),
        "bullet": bool(re.search(r"(^|\n)[・●◯○\-❶❷❸①②③]", text)),
        "arrow": ("↓" in text or "→" in text),
        "chars": len(text),
        "line_count": len(lines),
        "line_len_mean": statistics.mean([len(x) for x in lines]) if lines else 0,
        "sentence_len_mean": statistics.mean([len(x) for x in sents]) if sents else 0,
        "short_line_rate": (sum(len(x)<=18 for x in lines)/len(lines)) if lines else 0,
    }

BOOL_KEYS = ["spiritual","money","science","daily_scene","body_feeling","direct_reader","first_person","immediate_action","offer_cta","question","numbers","quotes","contrast","causal","personal_story","negation_reframe","aphorism","bullet","arrow"]
NUM_KEYS = ["chars","line_count","line_len_mean","sentence_len_mean","short_line_rate"]


def med(vals): return statistics.median(vals) if vals else 0

def mean(vals): return round(statistics.mean(vals),3) if vals else 0


def summarize(items):
    if not items: return {"count":0}
    return {
        "count": len(items),
        "date_range_utc": [items[0].get("datetime_utc"), items[-1].get("datetime_utc")],
        "engagement_mean": mean([x["engagement_score"] for x in items]),
        "engagement_median": med([x["engagement_score"] for x in items]),
        "likes_median": med([x.get("like_count",0) or 0 for x in items]),
        "feature_rates": {k: round(sum(bool(x["features"][k]) for x in items)/len(items),3) for k in BOOL_KEYS},
        "style": {k: mean([x["features"][k] for x in items]) for k in NUM_KEYS},
    }


def vector(summary):
    if summary.get("count",0)==0: return []
    f=summary["feature_rates"]; s=summary["style"]
    # scale numeric style to roughly 0-1 ranges
    return [f[k] for k in BOOL_KEYS] + [
        min(s["chars"]/500,2), min(s["line_count"]/20,2), min(s["line_len_mean"]/60,2),
        min(s["sentence_len_mean"]/80,2), s["short_line_rate"]
    ]


def distance(a,b):
    if not a or not b or len(a)!=len(b): return 0
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/len(a))


def cosine(a,b):
    if not a or not b or len(a)!=len(b): return 0
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0


def annotate(raw):
    out=[]
    for t in raw:
        text=(t.get("combined_text") or t.get("root_text") or "").strip()
        if not text: continue
        x=dict(t)
        x["engagement_score"]=mc.engagement_score(t)
        x["features"]=feats(text)
        out.append(x)
    return sorted(out,key=lambda x:x.get("timestamp") or 0)  # oldest -> newest


def chunks(items,size=50):
    out=[]
    for i in range(0,len(items),size):
        ch=items[i:i+size]
        if ch: out.append({"range":f"{i+1}-{i+len(ch)}_oldest_to_newest","summary":summarize(ch)})
    return out


def change_points(items,window=25,min_gap=25,topn=8):
    cand=[]
    if len(items)<window*2: return []
    for split in range(window,len(items)-window+1):
        before=items[split-window:split]; after=items[split:split+window]
        sb=summarize(before); sa=summarize(after)
        d=distance(vector(sb),vector(sa))
        eb=sb["engagement_median"]; ea=sa["engagement_median"]
        engagement_log_shift=math.log1p(ea)-math.log1p(eb)
        score=d + 0.12*abs(engagement_log_shift)
        cand.append({"split_index":split+1,"datetime_utc":items[split].get("datetime_utc"),"style_distance":round(d,4),"engagement_before":eb,"engagement_after":ea,"engagement_log_shift":round(engagement_log_shift,3),"score":round(score,4),"before":sb,"after":sa})
    chosen=[]
    for c in sorted(cand,key=lambda x:x["score"],reverse=True):
        if all(abs(c["split_index"]-x["split_index"])>=min_gap for x in chosen):
            chosen.append(c)
            if len(chosen)>=topn: break
    return sorted(chosen,key=lambda x:x["split_index"])


def top_posts(items,n=30):
    return [{"root_id":x.get("root_id"),"datetime_utc":x.get("datetime_utc"),"engagement_score":x["engagement_score"],"likes":x.get("like_count",0),"text":(x.get("combined_text") or "")[:1200]} for x in sorted(items,key=lambda x:(x["engagement_score"],x.get("timestamp") or 0),reverse=True)[:n]]


def load_reference_summary(path, max_items=None):
    try:
        obj=json.load(open(path,encoding="utf-8"))
    except Exception:
        return None
    arr=obj.get("threads",[]) if isinstance(obj,dict) else obj
    if max_items: arr=arr[:max_items]
    pseudo=[]
    for t in arr:
        text=(t.get("combined_text") or t.get("text") or "").strip()
        if not text: continue
        pseudo.append({"datetime_utc":t.get("datetime_utc"),"engagement_score":mc.engagement_score(t),"like_count":t.get("like_count",0),"features":feats(text)})
    return summarize(pseudo) if pseudo else None


def similarity_over_time(items, ref_summary, size=50):
    if not ref_summary: return []
    rv=vector(ref_summary); out=[]
    for i in range(0,len(items),size):
        ch=items[i:i+size]
        if ch:
            s=summarize(ch); out.append({"range":f"{i+1}-{i+len(ch)}_oldest_to_newest","cosine_similarity":round(cosine(vector(s),rv),4),"summary":s})
    return out


def main():
    cfg=json.load(open(".growth-trajectory-request.json",encoding="utf-8"))
    acct=cfg["account"]
    target=int(cfg.get("target_count",1000))
    username=acct["username"].lstrip("@")
    os.makedirs(os.path.join(ROOT,username),exist_ok=True)

    mc.ROOTDIR=ROOT
    doc_id,defaults,pcount=mc.load_query_runtime()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        _,_,raw,meta=mc.collect_account(browser,acct,target,doc_id,defaults,pcount)
        browser.close()

    items=annotate(raw)
    ref_osabori=load_reference_summary("data/threads_corpus_300.json",300)
    ref_dara=load_reference_summary("data/corpora/dara_dara_fairy/historical300.json",300)
    analysis={
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "username":username,"crawl":meta,"valid_count":len(items),
        "overall":summarize(items),
        "oldest_50":summarize(items[:50]),
        "newest_50":summarize(items[-50:]),
        "chunks_50_oldest_to_newest":chunks(items,50),
        "change_points_window25":change_points(items,25,25,10),
        "reference_summaries":{"osabori_space_human_300":ref_osabori,"dara_historical300":ref_dara},
        "similarity_to_osabori_by_50":similarity_over_time(items,ref_osabori,50),
        "similarity_to_dara_by_50":similarity_over_time(items,ref_dara,50),
        "top_posts":top_posts(items,40),
    }

    # Feature deltas oldest vs newest
    a=analysis["oldest_50"]; b=analysis["newest_50"]
    deltas=[]
    if a.get("count") and b.get("count"):
        for k in BOOL_KEYS:
            deltas.append({"feature":k,"oldest":a["feature_rates"][k],"newest":b["feature_rates"][k],"delta":round(b["feature_rates"][k]-a["feature_rates"][k],3)})
        deltas.sort(key=lambda x:abs(x["delta"]),reverse=True)
    analysis["oldest_to_newest_feature_deltas"]=deltas

    outdir=os.path.join(ROOT,username)
    with open(os.path.join(outdir,"raw.json"),"w",encoding="utf-8") as f: json.dump(raw,f,ensure_ascii=False,indent=2); f.write("\n")
    with open(os.path.join(outdir,"annotated.json"),"w",encoding="utf-8") as f: json.dump(items,f,ensure_ascii=False,indent=2); f.write("\n")
    with open(os.path.join(outdir,"trajectory_analysis.json"),"w",encoding="utf-8") as f: json.dump(analysis,f,ensure_ascii=False,indent=2); f.write("\n")

    lines=[f"# Growth Trajectory — @{username}","",f"Requested: {target} / retrieved: {meta['retrieved']} / valid: {len(items)}",f"Stop: {meta.get('stop_reason')}",""]
    lines += ["## Oldest → newest",f"Oldest50 engagement median: {a.get('engagement_median')} / newest50: {b.get('engagement_median')}",""]
    lines.append("### Largest feature changes")
    for x in deltas[:15]: lines.append(f"- {x['feature']}: {x['oldest']} → {x['newest']} ({x['delta']:+.3f})")
    lines += ["","## Detected change points"]
    for cp in analysis["change_points_window25"]:
        lines.append(f"- post ~{cp['split_index']} / {cp['datetime_utc']} / style distance {cp['style_distance']} / engagement median {cp['engagement_before']} → {cp['engagement_after']}")
    lines += ["","## Similarity to @osabori_space_human by 50-post block"]
    for row in analysis["similarity_to_osabori_by_50"]: lines.append(f"- {row['range']}: {row['cosine_similarity']}")
    lines += ["","## Highest engagement examples"]
    for x in analysis["top_posts"][:20]: lines.append(f"- score={x['engagement_score']} {x['datetime_utc']} :: {x['text'].replace(chr(10),' / ')[:420]}")
    with open(os.path.join(outdir,"TRAJECTORY_REPORT.md"),"w",encoding="utf-8") as f: f.write("\n".join(lines)+"\n")

if __name__=="__main__": main()
