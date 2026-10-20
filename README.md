# 東京デザインマップ（試作版）

建築家・アーティストの設計による施設や、カフェ・ショップ・公園・公共施設を地図で探す個人用マップ。東京23区の494件を収録している（2026-10-20時点）。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `index.html` | 画面の骨組み |
| `style.css` | 見た目（スマホは下から出る一覧、PCは左の列） |
| `app.js` | 地図・現在地・近くの一覧・詳細・絞り込みの動作 |
| `data/spots.json` | サイトが読み込むスポットのデータ（`tools/build_data.py` で生成） |
| `data/src/*.psv` | スポットの元データ（カテゴリ別、`|` 区切り） |
| `data/ledger.csv` | 台帳（Google スプレッドシート）に貼り付けるための書き出し |
| `tools/build_data.py` | 元データから `spots.json` と `ledger.csv` を作るスクリプト |
| `data/wards.json` | 23区の区境（claude.ai 上のプレビュー用。GitHub Pages 版では使わない） |
| `vendor/` | 地図ライブラリ Leaflet 1.9.4 と Leaflet.markercluster 1.5.3（同梱） |

## GitHub Pages での公開手順

1. GitHub で新しいリポジトリを作る（例：`tokyo-design-map`、Public）。
2. このフォルダの中身をすべてリポジトリの直下にアップロードする（「Add file」→「Upload files」でフォルダごとドラッグできる）。
3. リポジトリの「Settings」→「Pages」で、Source を「Deploy from a branch」、Branch を `main` と `/ (root)` にして保存する。
4. 数分後に `https://<ユーザー名>.github.io/tokyo-design-map/` で開ける。

現在地の表示には https が必要なため、スマホでの確認は GitHub Pages の URL で行う。

## パソコンで手早く確認する場合

`index.html` をダブルクリックで開くとデータを読み込めない。フォルダ内で次のコマンドを実行し、ブラウザで `http://localhost:8000` を開く。

```
python -m http.server 8000
```

## 収録データの状態

| 区分 | 件数 |
| --- | --- |
| 建築・アート | 217 |
| カフェ・飲食 | 93 |
| ショップ | 80 |
| 公園・庭園 | 55 |
| 公共施設 | 49 |

- `status: "checked"`（80件）はウェブで営業・開館状況を確認済み。`checkedAt` に確認日を入れている。
- `status: "unverified"` は未確認。詳細画面に「公式情報でご確認ください」と表示する。
- `approx: true`（21件）は地図上の位置が丁目単位の概略。経路ボタンは住所で検索するため、案内先はずれない。
- 休館日 `closedDays` が空欄（null）のものは「未確認」と表示し、「今日開いている」の絞り込みでは除外しない。

## データの更新

`data/src/` のファイルに1行ずつ追加・修正し、次のコマンドで `data/spots.json` と `data/ledger.csv` を作り直す。引数は丁目ごとの代表座標（geolonia/japanese-addresses の `api/ja/東京都/<区>.json`）を保存したフォルダ。

```
python tools/build_data.py <丁目座標のフォルダ>
```

元データの列は次のとおり（`|` 区切り、複数値は `;` 区切り）。

`カテゴリ|名称|区|住所|緯度|経度|設計者|設計者区分|竣工・開業年|概要|見どころ|見学可否|休み|無料|屋内|タグ`

`spots.json` の項目は台帳（Google スプレッドシート）と対応している。

| 台帳の列 | JSONの項目 | 書き方 |
| --- | --- | --- |
| ID | `id` | `S-021` のように連番 |
| 用途カテゴリ | `category` | `architecture` / `cafe` / `shop` / `park` / `public` |
| 設計者・設計者区分 | `designers` / `designerTypes` | 配列。同じ順番で対応させる |
| 休館日 | `closedDays` | 曜日番号の配列（日=0、月=1 … 土=6）。空配列は定休日なし、null は未確認 |
| 料金 | `free` | 無料なら `true` |
| 屋内外 | `indoor` | 屋内中心なら `true` |
| 掲載状態 | `status` | `checked` / `unverified`。`hidden` にすると表示しない |

## 地図の出典

国土地理院「淡色地図」、OpenStreetMap。プレビュー用の区境は国土数値情報（行政区域データ、国土交通省）を加工したもの。地図の左上に常に出典を表示している。
