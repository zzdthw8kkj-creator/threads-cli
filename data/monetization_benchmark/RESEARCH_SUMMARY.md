# Threads Monetization Benchmark — Research Summary v0.1

## Scope

2026-08-31 に以下3アカウントを匿名ブラウザRelay paginationで各500 root投稿まで遡って取得した。

- `@shiro_sns01`: 500/500
- `@shiro_money01`: 500/500
- `@nekasegi`: 500 root取得、本文有効499

総取得: 1,500 root投稿。本文有効: 1,499。

Rawは各アカウント `raw_500.json`、特徴タグ付きは `annotated_500.json`、個別集計は `monetization_analysis.json`、横断集計は `cross_account_analysis.json` に保存する。

注意: engagement score は `likes + 2*replies + 3*reposts + 3*quotes` の内部比較用ヒューリスティック。view数を含まず、投稿日・配信量・アカウント状態等の交絡があるため因果推論には使わない。

---

## 1. 最重要Finding — 平常フィードと変換イベントを分ける

CTAなし / 暗黙CTAの比率:

- shiro_sns01: 451 / 500 = 90.2%
- shiro_money01: 474 / 500 = 94.8%
- nekasegi: 480 / 499 = 96.2%

3者とも、日常投稿で毎回外部誘導していない。

一方、無料企画・セミナー・ローンチ・募集・書籍発売などの**変換イベント**では、CTA、無料配布、再投稿、フォロー、リンク、希少性、期限、実績を一つの投稿に高密度で束ねる。

したがって、`常時CTA固定` よりも、

> **Normal Feed = Reach / Trust / Category**
> **Conversion Event = Lead / Offer / CTA**

の状態分離が有力仮説。

CTAを毎投稿に入れないことは「導線がない」のではなく、フィードの役割とローンチの役割を分ける設計と解釈できる。

---

## 2. 3アカウントで共通して上位側に多かった特徴

Top quartile - Bottom quartile が3/3アカウントで正だった特徴:

| Feature | 3者平均lift |
|---|---:|
| authority_ai | +0.284 |
| instruction | +0.118 |
| community | +0.078 |
| belief_flip | +0.075 |
| cta_engagement | +0.064 |
| story | +0.045 |
| pain_problem | +0.032 |

最も頑健なのは **AI/Threads/検証/データ等の具体的な専門文脈**。次に、手順・方法・設計など「実装可能な知識」。

これは「AIと言えば伸びる」という因果ではない。対象3アカウント自体がClaude/AI×Threads領域であるため、**自分のカテゴリ中心に具体的専門性を出す投稿が上位へ入りやすい**という解釈を優先する。

---

## 3. 2/3で強かった変換要素

- lead magnet: mean lift +0.099
- proof: +0.075
- offer/product: +0.064
- direct monetization: +0.035
- scarcity: +0.024
- transformation: +0.022
- profile CTA: +0.021

これらは全アカウントで常時有効ではない。

特に `shiro_money01` では direct monetization が -0.072、offer/product が -0.024。したがって「売上・商品を直接書くほど伸びる」というルール化は禁止。

**Conversion要素はLaunch/Event文脈にまとめて使用し、Normal Feedの常時骨格にはしない**方がデータ整合的。

---

## 4. Archetype A — shiro_sns01: Authority + Instruction + Build-in-Public

500投稿中:

- authority_ai 50.0%
- offer_product 25.8%
- proof 20.6%
- direct monetization 17.8%
- instruction 14.0%

上位と下位の差は authority_ai +0.392、instruction +0.192、lead magnet +0.152、engagement CTA +0.120。

代表的な強い機能:

1. **権威を具体的な作業量・実績・データで置く**
   - 複数アカウント運用実績
   - 投稿データ分析
   - 講座生/アカウントの結果
2. **その場で使える手順へ落とす**
3. **無料企画で需要を測る**
4. **講座・セミナー・noteローンチ自体をリアルタイムコンテンツ化する**
5. **講座生、オフ会、メンバーの出来事を社会的証明とコミュニティ物語にする**

重要なのは、商品を売る投稿だけでなく、**商品を作っている過程・教えている過程・検証している過程そのものをフィード資産にしている**点。

---

## 5. Archetype B — shiro_money01: Trust / Operator Narrative / Customer Success

500投稿中:

- authority_ai 25.8%
- offer_product 24.8%
- proof 13.8%
- direct monetization 11.2%

しかし direct monetization と offer/product は上位quartileでむしろ弱い。

強い機能は:

- story +0.040
- belief flip +0.032
- engagement CTA +0.024
- instruction +0.024
- community +0.024

投稿内容では、講座生への呼びかけ、講座改善、運営上の失敗、メンバー問題、本人の仕事姿勢などが多い。

ここから得るべき機能は、**高頻度で売り込むことではなく「運営者が本当に現場にいる」証拠を継続公開すること**。

商品品質・フィードバック・受講者支援がコンテンツになり、販売文脈外でもTrustを蓄積する。

---

## 6. Archetype C — nekasegi: Event Launch + Free Education + Proof Cascade

本文有効499投稿中:

- authority_ai 29.9%
- proof 14.6%
- direct monetization 12.2%
- offer/product 10.8%
- community 9.6%
- instruction 9.2%
- lead magnet 6.8%

上位差:

- authority_ai +0.411
- proof +0.154
- offer_product +0.153
- lead_magnet +0.145
- belief_flip +0.137
- instruction +0.137
- community +0.137
- direct monetization +0.105

代表的変換構造:

> Pain / FOMO
> → 無料講義・無料企画
> → 具体的ベネフィット列挙
> → like/repost/follow/profile等のAction
> → Owned Channel / Live Event
> → 実績・参加者成果・感想
> → 低価格入口 / 本商品 / コンサル・コミュニティ
> → 感謝企画 / 次イベント

無料企画が単なるプレゼントではなく、**需要獲得・リスト形成・社会的証明・ローンチ予熱を同時に行うイベント装置**として働いている。

99円書籍のような低価格Entry Offerを「利益商品」ではなく、TrustとBuyer化の入口として使う例も確認できる。

---

## 7. 3者から抽出する共通Revenue System

投稿単体ではなく、以下の循環として見る。

1. **Normal Feed**
   - カテゴリ認知
   - 専門性
   - 実装知識
   - Belief shift
   - 人格/物語
2. **Demand Sensor**
   - いいね、コメント、質問
   - 「欲しい人いる？」
   - 企画予告
3. **Lead Magnet / Free Event**
   - 無料資料
   - 無料講義
   - セミナー
   - 実演
4. **Owned Audience**
   - メルマガ
   - オプチャ等
   - 外部リンク先
5. **Proof Cascade**
   - 自分の結果
   - 利用者結果
   - 感想
   - 参加人数
   - 実装過程
6. **Entry Offer**
   - 低価格コンテンツ / 書籍 / 小規模ツール
7. **Core Offer**
   - 講座 / ツール / 実装支援
8. **Retention / Community**
   - 継続アップデート
   - オフ会
   - フィードバック
   - メンバー成功
9. **Build-in-Public Loop**
   - 7〜8の出来事が再びNormal FeedのEvidenceになる

これにより、販売とコンテンツが別業務ではなく、**運営自体が次の集客コンテンツを生成する閉ループ**になる。

---

## 8. Dara Dara Fairyへ移植する時の禁止事項

外部3アカウントからコピーするのは**機能**のみ。

コピーしない:

- 誇張された実績
- 根拠のない収益数字
- 他者の顧客成果
- 人格、方言、口癖
- Fake scarcity
- 「絶対」「100%」等の無根拠保証
- 高圧FOMO

P3 Truth Gateを優先し、本人の確認済み実績・自前データ・実際の利用者データだけをProofとして使う。

---

## 9. Monetization Engineへの設計要件

1. Normal FeedとConversion Eventを別Runtimeにする。
2. 平常時CTAを固定しない。
3. Conversion Event開始時だけCTA / Lead / Offerの整合を固定する。
4. 無料配布は単なるフォロワー獲得ではなく、**次の有料実装で必要になる前段成果物**にする。
5. Free → Paidで情報を隠すのではなく、Paidは「実装速度・個別化・記録・継続・ツール化」を売る。
6. ProofはEvidence Ladderを持ち、ClaimとEvidenceを分離する。
7. 企画・開発・検証・利用者結果をBuild-in-PublicとしてFeedへ還流させる。
8. Raw corpusは生成AIの常時Contextへ入れない。分析結果だけをRuntimeへ昇格させる。
9. 1回のバズや1アカウントの成功を永久ルール化しない。
10. Revenue KPIだけでなくActivation / Completion / Outcome / Refund / Retentionも見る。

---

## 10. Evidence confidence

### Strong observational signal

- 3者とも平常投稿の90%以上で明示CTAなし
- authority/category-specific expertise の上位liftが3/3で正
- instruction / community / belief flip / engagement CTA / story / pain が3/3で正

### Medium

- Lead magnet / proof / offerが2/3で正
- Event Launch型が高engagement例で複数観察

### Weak / Hypothesis only

- 特定価格帯が最適
- 特定CTA文言が最適
- Scarcity自体が成果原因
- いいね数と売上の直接対応

これらは自アカウントで別途実験する。
