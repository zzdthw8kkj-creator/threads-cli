#!/usr/bin/env python3
import json,re,os,collections

BASE='data/growth_trajectory/sora_shikumi'
SORA=json.load(open(f'{BASE}/annotated.json',encoding='utf-8'))
OSRAW=json.load(open('data/threads_corpus_300.json',encoding='utf-8'))
OSA=OSRAW.get('threads',[]) if isinstance(OSRAW,dict) else OSRAW
DARA=json.load(open('data/corpora/dara_dara_fairy/historical300.json',encoding='utf-8'))


def text(x): return (x.get('combined_text') or x.get('text') or '').strip()
def norm(s): return re.sub(r'[\s\W_]+','',s.lower(),flags=re.UNICODE)
def grams(s,n=8):
    s=norm(s)
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))}

def docfreq(items,n=8):
    c=collections.Counter()
    for x in items: c.update(grams(text(x),n))
    return c

fo=docfreq(OSA); fs=docfreq(SORA); fd=docfreq(DARA)
shared=[]
for g,sc in fs.items():
    oc=fo.get(g,0); dc=fd.get(g,0)
    if sc>=2 and oc>=2 and dc==0:
        shared.append((sc*oc,g,sc,oc))
shared=sorted(shared,reverse=True)[:120]

# block lexical overlap against reference doc-frequency vocabularies
ovocab={g for g,c in fo.items() if c>=2}
dvocab={g for g,c in fd.items() if c>=2}
blocks=[]
for i in range(0,len(SORA),50):
    ch=SORA[i:i+50]; gs=set()
    for x in ch: gs |= grams(text(x))
    denom=max(1,len(gs))
    blocks.append({
        'range':f'{i+1}-{i+len(ch)}',
        'osabori_overlap':round(len(gs&ovocab)/denom,5),
        'dara_overlap':round(len(gs&dvocab)/denom,5),
        'count':len(ch)
    })

# samples around meaningful change points
splits=[26,57,108,134,159,187,217,261,308,426]
samples=[]
for sp in splits:
    before=SORA[max(0,sp-4):sp-1]
    after=SORA[sp-1:min(len(SORA),sp+2)]
    samples.append({
        'split_index':sp,
        'before':[{'index':SORA.index(x)+1,'datetime_utc':x.get('datetime_utc'),'score':x.get('engagement_score'),'text':text(x)} for x in before],
        'after':[{'index':SORA.index(x)+1,'datetime_utc':x.get('datetime_utc'),'score':x.get('engagement_score'),'text':text(x)} for x in after],
    })

# repeated opening formula families
families={
 'dialogue_simulation':['あなた「','潜在意識『','宇宙→','宇宙「'],
 'authority_name':['ニコラ・テスラ','美輪明宏','アインシュタイン','エイブラハム'],
 'certainty_hook':['信じられないかもしれない','嘘みたいな話','知らない人多い','ほとんどの人が知らない'],
 'save_follow_cta':['保存して','フォロー','読んでね','プロフィール'],
 'brain_explanation':['脳は','脳が','潜在意識は','仕組み'],
}
family_blocks=[]
for i in range(0,len(SORA),50):
    ch=SORA[i:i+50]
    row={'range':f'{i+1}-{i+len(ch)}'}
    for name,markers in families.items(): row[name]=round(sum(any(m in text(x) for m in markers) for x in ch)/len(ch),3)
    family_blocks.append(row)

result={'shared_distinctive_8grams':shared,'lexical_overlap_by_50':blocks,'formula_family_by_50':family_blocks,'change_point_samples':samples}
with open(f'{BASE}/deep_dive.json','w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')

lines=['# @sora_shikumi Deep Dive','', '## Lexical overlap by 50-post block']
for x in blocks: lines.append(f"- {x['range']}: osabori={x['osabori_overlap']:.5f} / dara={x['dara_overlap']:.5f}")
lines += ['', '## Formula families by 50-post block']
for x in family_blocks: lines.append('- '+x['range']+': '+', '.join(f'{k}={v}' for k,v in x.items() if k!='range'))
lines += ['', '## Shared distinctive 8-char ngrams (sora & osabori, absent from dara control)']
for _,g,sc,oc in shared[:50]: lines.append(f'- {g}: sora_docs={sc}, osabori_docs={oc}')
lines += ['', '## Change-point samples']
for s in samples:
    lines.append(f"### around post {s['split_index']}")
    for label in ('before','after'):
        lines.append(label+':')
        for x in s[label]: lines.append(f"- #{x['index']} score={x['score']} {x['datetime_utc']} :: {x['text'].replace(chr(10),' / ')[:600]}")
with open(f'{BASE}/DEEP_DIVE.md','w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
