#!/usr/bin/env python3
import json
import math
import os
import re
import statistics
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

ROOTDIR = "data/monetization_benchmark"
PAGE_SIZE = 24

FEATURES = {
    "monetization_direct": ["収益", "売上", "稼ぐ", "稼げ", "マネタイズ", "利益", "月収", "年収", "副業", "案件", "商品", "販売", "有料", "成約"],
    "offer_product": ["note", "教材", "講座", "コンサル", "スクール", "コミュニティ", "サロン", "ロードマップ", "テンプレ", "プロンプト", "Brain", "Tips", "コンテンツ販売"],
    "lead_magnet": ["無料", "プレゼント", "配布", "特典", "テンプレ", "プロンプト", "受け取", "欲しい人", "保存版", "公開します"],
    "cta_profile": ["プロフィール", "プロフ", "リンク", "固定投稿", "bio", "リンクから", "プロフから"],
    "cta_engagement": ["DM", "コメント", "リプ", "返信", "合言葉", "欲しい人", "フォロー", "保存して"],
    "scarcity": ["限定", "先着", "締切", "今日まで", "残り", "今だけ", "期間限定", "募集終了"],
    "proof": ["実績", "売上", "収益", "フォロワー", "閲覧", "表示", "view", "達成", "成果", "購入", "受講生", "再現", "伸びた", "増えた"],
    "authority_ai": ["Claude", "ChatGPT", "GPT", "AI", "Threads", "スレッズ", "分析", "検証", "データ", "自動化"],
    "pain_problem": ["伸びない", "稼げない", "売れない", "悩", "失敗", "しんど", "できない", "詰む", "伸び悩"],
    "transformation": ["変わった", "伸びた", "増えた", "売れた", "稼げた", "できた", "改善", "達成"],
    "belief_flip": ["実は", "逆", "じゃない", "ではない", "勘違い", "知らない", "間違い", "むしろ"],
    "instruction": ["やり方", "方法", "手順", "ステップ", "まず", "次に", "コツ", "ポイント", "設計", "作り方"],
    "community": ["コミュニティ", "オプチャ", "オープンチャット", "Discord", "サロン", "仲間", "メンバー"],
    "story": ["僕は", "私は", "自分は", "当時", "昔", "最初は", "ある日", "ヶ月前", "年前"],
}

URL_RE = re.compile(r"https?://\S+")
MONEY_RE = re.compile(r"(?<!\d)(\d{1,4}(?:\.\d+)?)(万|千)?円")


def load_query_runtime():
    network = json.load(open("data/network_docids.json", encoding="utf-8"))
    target = next(
        x
        for x in network["relay_operations"]
        if x["name"] == "BarcelonaProfileThreadsTabRefetchableDirectQuery"
    )
    doc_id = target["doc_id"]
    js_url = target["url"]
    with urllib.request.urlopen(
        urllib.request.Request(js_url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30,
    ) as r:
        script = r.read().decode("utf-8", errors="ignore")
    needle = "BarcelonaProfileThreadsTabRefetchableDirectQuery.threads.graphql"
    pos = script.find(needle)
    if pos < 0:
        raise RuntimeError("query module not found in current Threads JS")
    snippet = script[max(0, pos - 5000) : min(len(script), pos + 150000)]
    providers = sorted(
        set(re.findall(r"__relay_internal__pv__[A-Za-z0-9_]+relayprovider", snippet))
    )
    defaults = {k: False for k in providers}
    for k in providers:
        if "IsCrawler" in k or "OptionalCookiesEnabled" in k or "IsLoggedOut" in k:
            defaults[k] = True
    return doc_id, defaults, len(providers)


def text_from_post(post):
    info = post.get("text_post_app_info") or {}
    fragments = ((info.get("text_fragments") or {}).get("fragments") or [])
    parts = [
        x.get("plaintext")
        for x in fragments
        if isinstance(x, dict) and isinstance(x.get("plaintext"), str)
    ]
    if parts:
        return "".join(parts).strip()
    cap = post.get("caption")
    if isinstance(cap, dict) and isinstance(cap.get("text"), str):
        return cap["text"].strip()
    for key in ("text", "caption_text"):
        if isinstance(post.get(key), str):
            return post[key].strip()
    return ""


def ts_from_post(post):
    for key in ("taken_at", "timestamp", "created_at", "published_at"):
        value = post.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    return None


def normalize_segment(post):
    info = post.get("text_post_app_info") or {}
    user = post.get("user") or {}
    ts = ts_from_post(post)
    return {
        "id": str(post.get("pk") or post.get("id") or ""),
        "code": post.get("code") or post.get("shortcode") or "",
        "username": user.get("username"),
        "user_id": str(user.get("pk") or user.get("id") or ""),
        "text": text_from_post(post),
        "like_count": post.get("like_count"),
        "reply_count": info.get("direct_reply_count"),
        "repost_count": info.get("repost_count"),
        "quote_count": info.get("quote_count"),
        "timestamp": ts,
        "datetime_utc": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None,
    }


def extract_lsd(html):
    tokens = []
    for pattern in [
        r'"LSD",\[\],\{"token":"([^"]+)"',
        r'"token":"([A-Za-z0-9_-]{18,80})"',
    ]:
        for value in re.findall(pattern, html):
            if value not in tokens:
                tokens.append(value)
    return tokens[0] if tokens else "t"


def candidate_user_ids(html, username):
    out = []
    lower = html.lower()
    needle = username.lower()
    start = 0
    patterns = [
        r'"(?:pk|id|user_id)":"?(\d{5,15})"?',
        r'\\"(?:pk|id|user_id)\\":\\"(\d{5,15})\\"',
    ]
    while True:
        pos = lower.find(needle, start)
        if pos < 0:
            break
        chunk = html[max(0, pos - 3000) : min(len(html), pos + 3000)]
        for pattern in patterns:
            for value in re.findall(pattern, chunk, re.I | re.S):
                if value not in out:
                    out.append(value)
        start = pos + len(needle)
    return out


def gql_fetch(page, lsd, doc_id, variables):
    payload = {
        "doc_id": doc_id,
        "lsd": lsd,
        "variables": json.dumps(variables, separators=(",", ":")),
    }
    return page.evaluate(
        """async p=>{const f=new URLSearchParams();f.set('lsd',p.lsd);f.set('doc_id',p.doc_id);f.set('variables',p.variables);const r=await fetch('/api/graphql',{method:'POST',credentials:'include',headers:{'Content-Type':'application/x-www-form-urlencoded','X-FB-LSD':p.lsd,'X-IG-App-ID':'238260118697367','X-FB-Friendly-Name':'BarcelonaProfileThreadsTabRefetchableDirectQuery'},body:f.toString()});return {status:r.status,text:await r.text()}}""",
        payload,
    )


def media_from_response(res):
    if res.get("status") != 200:
        return None
    try:
        obj = json.loads(res.get("text") or "{}")
    except Exception:
        return None
    data = obj.get("data") or {}
    media = data.get("mediaData")
    return media if isinstance(media, dict) else None


def discover_user_id(page, html, lsd, doc_id, provider_defaults, username):
    candidates = candidate_user_ids(html, username)
    for uid in candidates[:60]:
        variables = dict(provider_defaults)
        variables.update(
            {
                "allow_page_info_for_lox_user": True,
                "before": None,
                "first": 3,
                "last": None,
                "userID": str(uid),
                "after": None,
            }
        )
        media = media_from_response(gql_fetch(page, lsd, doc_id, variables))
        if not media:
            continue
        for edge in media.get("edges") or []:
            for item in ((edge.get("node") or {}).get("thread_items") or []):
                post = (item or {}).get("post") or {}
                user = post.get("user") or {}
                if (user.get("username") or "").lower() == username.lower():
                    return str(user.get("pk") or user.get("id") or uid)
    raise RuntimeError(
        f"Could not resolve user_id for {username}; candidates={candidates[:15]}"
    )


def has_any(text, words):
    low = text.lower()
    return any(word.lower() in low for word in words)


def feature_tags(text):
    return [name for name, words in FEATURES.items() if has_any(text, words)]


def funnel_stages(text):
    tags = set(feature_tags(text))
    out = []
    if tags & {"pain_problem", "belief_flip", "instruction"}:
        out.append("awareness_education")
    if tags & {"proof", "authority_ai", "story", "transformation"}:
        out.append("authority_trust")
    if tags & {"lead_magnet", "cta_profile", "cta_engagement"}:
        out.append("lead_capture")
    if tags & {"offer_product", "monetization_direct", "scarcity"}:
        out.append("offer_conversion")
    if "community" in tags:
        out.append("retention_community")
    return out or ["unclear"]


def cta_type(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    last = "\n".join(lines[-3:])
    if has_any(last, FEATURES["cta_profile"]):
        return "profile_link"
    if has_any(last, ["DM", "コメント", "リプ", "返信", "合言葉", "欲しい人"]):
        return "engagement_dm_comment"
    if has_any(last, ["フォロー"]):
        return "follow"
    if has_any(last, ["保存"]):
        return "save"
    if URL_RE.search(last):
        return "external_url"
    return "none_or_implicit"


def engagement_score(thread):
    return (
        (thread.get("like_count") or 0)
        + 2 * (thread.get("reply_count") or 0)
        + 3 * (thread.get("repost_count") or 0)
        + 3 * (thread.get("quote_count") or 0)
    )


def annotate(thread):
    item = dict(thread)
    text = item.get("combined_text") or ""
    item["engagement_score"] = engagement_score(item)
    item["monetization_tags"] = feature_tags(text)
    item["funnel_stages"] = funnel_stages(text)
    item["cta_type"] = cta_type(text)
    item["urls"] = URL_RE.findall(text)
    item["money_mentions"] = ["".join(x) for x in MONEY_RE.findall(text)]
    return item


def rate(items, feature):
    if not items:
        return 0
    return round(
        sum(feature in (x.get("monetization_tags") or []) for x in items) / len(items),
        3,
    )


def mean(values):
    return round(statistics.mean(values), 3) if values else 0


def median(values):
    return statistics.median(values) if values else 0


def analyze_account(username, threads, crawl_meta):
    valid = [annotate(t) for t in threads if (t.get("combined_text") or "").strip()]
    ordered = sorted(valid, key=lambda t: t["engagement_score"])
    q = max(1, len(ordered) // 4)
    bottom = ordered[:q]
    top = ordered[-q:]

    feature_perf = []
    for name in FEATURES:
        feature_perf.append(
            {
                "feature": name,
                "rate": rate(valid, name),
                "top_quartile_rate": rate(top, name),
                "bottom_quartile_rate": rate(bottom, name),
                "top_minus_bottom": round(rate(top, name) - rate(bottom, name), 3),
            }
        )
    feature_perf.sort(key=lambda x: abs(x["top_minus_bottom"]), reverse=True)

    cta = Counter(t["cta_type"] for t in valid)
    stages = Counter(stage for t in valid for stage in t["funnel_stages"])

    chronological = sorted(valid, key=lambda t: t.get("timestamp") or 0, reverse=True)
    chunks = []
    for i in range(0, len(chronological), 100):
        chunk = chronological[i : i + 100]
        if not chunk:
            continue
        chunks.append(
            {
                "range": f"{i+1}-{i+len(chunk)}_newest_to_oldest",
                "count": len(chunk),
                "engagement_median": median([x["engagement_score"] for x in chunk]),
                "feature_rates": {k: rate(chunk, k) for k in FEATURES},
                "cta_types": dict(Counter(x["cta_type"] for x in chunk)),
            }
        )

    money_relevant = {
        "monetization_direct",
        "offer_product",
        "lead_magnet",
        "cta_profile",
        "cta_engagement",
        "scarcity",
        "proof",
        "community",
    }
    relevant = [
        t for t in valid if set(t["monetization_tags"]) & money_relevant
    ]
    top_relevant = sorted(
        relevant,
        key=lambda t: (t["engagement_score"], t.get("timestamp") or 0),
        reverse=True,
    )[:120]
    top_overall = sorted(
        valid,
        key=lambda t: (t["engagement_score"], t.get("timestamp") or 0),
        reverse=True,
    )[:60]

    openings = Counter()
    endings = Counter()
    for t in valid:
        lines = [x.strip() for x in (t["combined_text"] or "").splitlines() if x.strip()]
        if lines:
            openings[lines[0][:50]] += 1
            endings[lines[-1][:70]] += 1

    return valid, {
        "username": username,
        "crawl": crawl_meta,
        "count": len(valid),
        "date_range_utc": [
            min((t.get("datetime_utc") for t in valid if t.get("datetime_utc")), default=None),
            max((t.get("datetime_utc") for t in valid if t.get("datetime_utc")), default=None),
        ],
        "engagement": {
            "mean": mean([t["engagement_score"] for t in valid]),
            "median": median([t["engagement_score"] for t in valid]),
            "max": max([t["engagement_score"] for t in valid], default=0),
        },
        "feature_rates": {k: rate(valid, k) for k in FEATURES},
        "feature_performance": feature_perf,
        "cta_distribution": dict(cta),
        "funnel_stage_distribution": dict(stages),
        "chunks_newest_to_oldest": chunks,
        "top_repeated_openings": openings.most_common(30),
        "top_repeated_endings": endings.most_common(30),
        "monetization_relevant_count": len(relevant),
        "top_monetization_posts": top_relevant,
        "top_overall_posts": top_overall,
    }


def collect_account(
    browser,
    acct,
    target_count,
    doc_id,
    provider_defaults,
    provider_count,
):
    username = acct["username"].lstrip("@")
    profile_url = acct.get("profile_url") or f"https://www.threads.com/@{username}"
    outdir = os.path.join(ROOTDIR, username)
    os.makedirs(outdir, exist_ok=True)

    context = browser.new_context(locale="ja-JP", viewport={"width": 1280, "height": 1200})
    page = context.new_page()
    page.goto(profile_url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(5000)
    html = page.content()
    lsd = extract_lsd(html)

    user_id = str(acct.get("user_id") or "")
    if not user_id:
        user_id = discover_user_id(
            page, html, lsd, doc_id, provider_defaults, username
        )

    base_vars = dict(provider_defaults)
    base_vars.update(
        {
            "allow_page_info_for_lox_user": True,
            "before": None,
            "first": PAGE_SIZE,
            "last": None,
            "userID": user_id,
        }
    )

    threads = []
    seen = set()
    cursor = None
    pages = []
    max_pages = max(1, math.ceil(target_count / PAGE_SIZE) + 2)
    stop_reason = None

    for page_no in range(1, max_pages + 1):
        variables = dict(base_vars)
        variables["after"] = cursor
        res = gql_fetch(page, lsd, doc_id, variables)
        media = media_from_response(res)
        if not media:
            stop_reason = f"graphql_http_or_parse_{res.get('status')}"
            break

        edges = media.get("edges") or []
        page_info = media.get("page_info") or {}
        new_count = 0

        for edge in edges:
            node = edge.get("node") or {}
            items = node.get("thread_items") or []
            if not items:
                continue
            raw_posts = [(item or {}).get("post") or {} for item in items]
            segments = [normalize_segment(x) for x in raw_posts if isinstance(x, dict)]
            own = [
                x
                for x in segments
                if x["id"] and (x.get("username") or "").lower() == username.lower()
            ]
            if not own:
                continue
            root = own[0]
            if root["id"] in seen:
                continue
            seen.add(root["id"])
            new_count += 1
            combined = "\n\n".join(x["text"] for x in own if x["text"]).strip()
            threads.append(
                {
                    "profile_order": len(threads) + 1,
                    "root_id": root["id"],
                    "root_code": root["code"],
                    "permalink": f'https://www.threads.com/@{username}/post/{root["code"]}' if root["code"] else None,
                    "timestamp": root["timestamp"],
                    "datetime_utc": root["datetime_utc"],
                    "like_count": root["like_count"] if isinstance(root["like_count"], int) else 0,
                    "reply_count": root["reply_count"] if isinstance(root["reply_count"], int) else 0,
                    "repost_count": root["repost_count"] if isinstance(root["repost_count"], int) else 0,
                    "quote_count": root["quote_count"] if isinstance(root["quote_count"], int) else 0,
                    "segment_count": len(own),
                    "root_text": root["text"],
                    "combined_text": combined,
                    "segments": own,
                }
            )

        pages.append(
            {
                "page": page_no,
                "edges": len(edges),
                "new": new_count,
                "total": len(threads),
                "has_next_page": bool(page_info.get("has_next_page")),
            }
        )

        if len(threads) >= target_count:
            stop_reason = "target_reached"
            break
        next_cursor = page_info.get("end_cursor")
        if not new_count:
            stop_reason = "no_new_posts"
            break
        if not page_info.get("has_next_page") or not next_cursor:
            stop_reason = "no_next_cursor"
            break
        if next_cursor == cursor:
            stop_reason = "cursor_stalled"
            break
        cursor = next_cursor
        page.wait_for_timeout(700)

    context.close()
    threads = threads[:target_count]
    meta = {
        "username": username,
        "profile_url": profile_url,
        "user_id": user_id,
        "requested": target_count,
        "retrieved": len(threads),
        "provider_count": provider_count,
        "pages": pages,
        "stop_reason": stop_reason,
    }
    return username, outdir, threads, meta


def write_account_files(outdir, raw, annotated, analysis):
    for name, obj in [
        ("raw_500.json", raw),
        ("annotated_500.json", annotated),
        ("monetization_analysis.json", analysis),
    ]:
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")


def build_cross_account(all_analyses, all_annotated, target_count, crawl_results):
    feature_cross = []
    for feat in FEATURES:
        rows = []
        positives = 0
        for username, analysis in all_analyses.items():
            perf = next(
                x for x in analysis["feature_performance"] if x["feature"] == feat
            )
            rows.append(
                {
                    "username": username,
                    "rate": perf["rate"],
                    "top_minus_bottom": perf["top_minus_bottom"],
                }
            )
            if perf["top_minus_bottom"] > 0:
                positives += 1
        feature_cross.append(
            {
                "feature": feat,
                "positive_lift_accounts": positives,
                "accounts": rows,
                "mean_top_minus_bottom": round(
                    statistics.mean([x["top_minus_bottom"] for x in rows]), 3
                )
                if rows
                else 0,
            }
        )
    feature_cross.sort(
        key=lambda x: (x["positive_lift_accounts"], x["mean_top_minus_bottom"]),
        reverse=True,
    )

    best_posts = []
    money_relevant = {
        "monetization_direct",
        "offer_product",
        "lead_magnet",
        "cta_profile",
        "cta_engagement",
        "scarcity",
        "proof",
        "community",
    }
    for username, posts in all_annotated.items():
        for item in posts:
            if set(item["monetization_tags"]) & money_relevant:
                best_posts.append({"username": username, **item})
    best_posts = sorted(
        best_posts,
        key=lambda x: (x["engagement_score"], x.get("timestamp") or 0),
        reverse=True,
    )[:240]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_per_account": target_count,
        "crawl_results": crawl_results,
        "accounts": {
            username: {
                "count": analysis["count"],
                "feature_rates": analysis["feature_rates"],
                "engagement": analysis["engagement"],
                "monetization_relevant_count": analysis["monetization_relevant_count"],
            }
            for username, analysis in all_analyses.items()
        },
        "feature_cross_account": feature_cross,
        "funnel_stage_compare": {
            username: analysis["funnel_stage_distribution"]
            for username, analysis in all_analyses.items()
        },
        "cta_compare": {
            username: analysis["cta_distribution"]
            for username, analysis in all_analyses.items()
        },
        "top_cross_account_monetization_posts": best_posts,
    }


def write_evidence_pack(all_analyses, cross, target_count):
    lines = [
        "# Monetization Benchmark Evidence Pack",
        "",
        f"Target: {target_count} posts/account",
        "",
    ]
    for username, analysis in all_analyses.items():
        lines += [
            f"## @{username}",
            f"Retrieved: {analysis['count']} / monetization-relevant: {analysis['monetization_relevant_count']}",
            f"Engagement score median: {analysis['engagement']['median']} / max: {analysis['engagement']['max']}",
            "",
            "### Feature rates",
        ]
        for key, value in sorted(
            analysis["feature_rates"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"- {key}: {value}")
        lines += ["", "### Strongest top-v-bottom lifts"]
        for item in analysis["feature_performance"][:10]:
            lines.append(
                f"- {item['feature']}: {item['top_minus_bottom']:+.3f} (top {item['top_quartile_rate']}, bottom {item['bottom_quartile_rate']})"
            )
        lines += ["", "### CTA distribution"]
        for key, value in analysis["cta_distribution"].items():
            lines.append(f"- {key}: {value}")
        lines += ["", "### Top monetization-relevant examples"]
        for item in analysis["top_monetization_posts"][:20]:
            text = (item["combined_text"] or "").replace("\n", " / ")
            lines.append(
                f"- score={item['engagement_score']} tags={','.join(item['monetization_tags'])} :: {text[:420]}"
            )
        lines.append("")

    lines += ["## Cross-account robust signals"]
    for item in cross["feature_cross_account"]:
        lines.append(
            f"- {item['feature']}: positive in {item['positive_lift_accounts']}/3, mean lift {item['mean_top_minus_bottom']:+.3f}"
        )

    with open(os.path.join(ROOTDIR, "EVIDENCE_PACK.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    cfg = json.load(open(".monetization-corpus-request.json", encoding="utf-8"))
    accounts = cfg["accounts"]
    target_count = int(cfg.get("target_count", 500))
    os.makedirs(ROOTDIR, exist_ok=True)

    doc_id, provider_defaults, provider_count = load_query_runtime()
    all_analyses = {}
    all_annotated = {}
    crawl_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for index, acct in enumerate(accounts):
            username, outdir, raw, meta = collect_account(
                browser,
                acct,
                target_count,
                doc_id,
                provider_defaults,
                provider_count,
            )
            annotated, analysis = analyze_account(username, raw, meta)
            write_account_files(outdir, raw, annotated, analysis)
            all_annotated[username] = annotated
            all_analyses[username] = analysis
            crawl_results[username] = meta
            if index < len(accounts) - 1:
                time.sleep(1.5)
        browser.close()

    cross = build_cross_account(
        all_analyses, all_annotated, target_count, crawl_results
    )
    with open(
        os.path.join(ROOTDIR, "cross_account_analysis.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(cross, f, ensure_ascii=False, indent=2)
        f.write("\n")
    write_evidence_pack(all_analyses, cross, target_count)


if __name__ == "__main__":
    main()
