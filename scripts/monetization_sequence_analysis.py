#!/usr/bin/env python3
import json
import os
import statistics
from collections import Counter
from datetime import datetime, timezone

ROOT='data/monetization_benchmark'
ACCOUNTS=['shiro_sns01','shiro_money01','nekasegi']
CONVERSION_TAGS={'lead_magnet','offer_product','scarcity','cta_profile','cta_engagement','monetization_direct','community','proof'}

PHASE_WORDS={
  'demand_sensor':['欲しい人','知りたい人','いますか','いいね多かったら','反応あれば','興味ある','需要'],
  'announce':['ご報告','開催','やります','企画','募集','出版','発売','セミナー','勉強会','講義'],
  'free_value':['無料','配布','プレゼント','特典','ばら撒','還元','99円'],
  'proof':['実績','達成','フォロワー','売上','収益','成果','受講生','講座生','同接','参加者','伸びた','売れた'],
  'offer':['販売','購入','参加','申し込','登録','講座','コンサル','note','書籍','商品','メルマガ','オプチャ'],
  'urgency':['限定','先着','締切','今日まで','残り','今だけ','消える','募集終了','あと'],
  'aftercare':['ありがとう','感謝','終わりました','終了','閉幕','参加してくれ','感想','振り返'],
}

def ts(x): return int(x.get('timestamp') or 0)
def text(x): return x.get('combined_text') or ''
def days(a,b): return abs(ts(a)-ts(b))/86400 if ts(a) and ts(b) else 999

def phases(txt):
    out=[]
    low=txt.lower()
    for name,words in PHASE_WORDS.items():
        if any(w.lower() in low for w in words): out.append(name)
    return out or ['unclear']

def engagement(x): return x.get('engagement_score') or 0

def median(v): return statistics.median(v) if v else 0

def mean(v): return round(statistics.mean(v),2) if v else 0

def snippet(x,n=260): return text(x).replace('\n',' / ')[:n]

def cluster_posts(posts, max_gap_days=5):
    candidates=[p for p in posts if set(p.get('monetization_tags') or []) & CONVERSION_TAGS]
    candidates=sorted(candidates,key=ts)
    clusters=[]; cur=[]
    for p in candidates:
        if not cur or days(cur[-1],p)<=max_gap_days:
            cur.append(p)
        else:
            if len(cur)>=3: clusters.append(cur)
            cur=[p]
    if len(cur)>=3: clusters.append(cur)
    return clusters

def surrounding(posts, cluster, days_each=7):
    lo=ts(cluster[0])-days_each*86400; hi=ts(cluster[-1])+days_each*86400
    return [p for p in posts if lo<=ts(p)<=hi]

def analyze_cluster(all_posts, cluster, index):
    around=surrounding(all_posts,cluster,7)
    phase_counts=Counter(ph for p in cluster for ph in phases(text(p)))
    tag_counts=Counter(t for p in cluster for t in p.get('monetization_tags') or [])
    cta_counts=Counter(p.get('cta_type') or 'unknown' for p in cluster)
    top=sorted(cluster,key=engagement,reverse=True)[:8]
    timeline=[]
    for p in cluster:
        timeline.append({
          'datetime_utc':p.get('datetime_utc'),
          'engagement_score':engagement(p),
          'phases':phases(text(p)),
          'tags':p.get('monetization_tags') or [],
          'cta_type':p.get('cta_type'),
          'snippet':snippet(p,360),
        })
    return {
      'cluster_id':index,
      'start_utc':cluster[0].get('datetime_utc'),
      'end_utc':cluster[-1].get('datetime_utc'),
      'duration_days':round((ts(cluster[-1])-ts(cluster[0]))/86400,1),
      'conversion_post_count':len(cluster),
      'surrounding_7d_post_count':len(around),
      'engagement_median':median([engagement(p) for p in cluster]),
      'engagement_mean':mean([engagement(p) for p in cluster]),
      'engagement_max':max([engagement(p) for p in cluster],default=0),
      'phase_counts':dict(phase_counts),
      'tag_counts':dict(tag_counts),
      'cta_counts':dict(cta_counts),
      'top_posts':[{'score':engagement(p),'datetime_utc':p.get('datetime_utc'),'phases':phases(text(p)),'snippet':snippet(p,520)} for p in top],
      'timeline':timeline,
    }

def main():
    result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'accounts':{}}
    md=['# Monetization Temporal Sequence Analysis','', 'Conversion-like posts are grouped when adjacent events are <=5 days apart; clusters require >=3 posts. This is heuristic sequence discovery, not causal proof.','']
    cross_phases=Counter(); cross_clusters=0
    for username in ACCOUNTS:
        path=os.path.join(ROOT,username,'annotated_500.json')
        posts=json.load(open(path,encoding='utf-8'))
        posts=sorted(posts,key=ts)
        clusters=cluster_posts(posts)
        analyzed=[analyze_cluster(posts,c,i+1) for i,c in enumerate(clusters)]
        # rank by a mix of scale and engagement so we retain both long and intense events
        ranked=sorted(analyzed,key=lambda c:(c['engagement_max'],c['conversion_post_count']),reverse=True)
        result['accounts'][username]={'cluster_count':len(analyzed),'clusters':analyzed,'top_clusters':ranked[:12]}
        md += [f'## @{username}',f'Clusters detected: {len(analyzed)}','']
        for c in ranked[:8]:
            md += [f"### Cluster {c['cluster_id']} — {c['start_utc']} → {c['end_utc']}",
                   f"conversion posts={c['conversion_post_count']}, duration={c['duration_days']}d, median score={c['engagement_median']}, max={c['engagement_max']}",
                   f"phases={c['phase_counts']}",f"CTA={c['cta_counts']}",'Top examples:']
            for p in c['top_posts'][:4]: md.append(f"- score={p['score']} phases={','.join(p['phases'])} :: {p['snippet']}")
            md.append('')
        for c in analyzed:
            cross_clusters+=1; cross_phases.update(c['phase_counts'])
    result['cross_account']={'cluster_count':cross_clusters,'phase_counts':dict(cross_phases)}
    md += ['## Cross-account phase frequency across detected clusters']
    for k,v in cross_phases.most_common(): md.append(f'- {k}: {v}')
    with open(os.path.join(ROOT,'sequence_analysis.json'),'w',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
    with open(os.path.join(ROOT,'SEQUENCE_ANALYSIS.md'),'w',encoding='utf-8') as f:
        f.write('\n'.join(md)+'\n')

if __name__=='__main__': main()
