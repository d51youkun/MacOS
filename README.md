# App on the fly 🛫

GitHub に **レシピ（JSON）を push するだけ**で、GitHub Actions の macOS ランナーが
本物の macOS アプリ（`.app` / `.zip`）をビルドして配布してくれる仕組みです。

サーバーもドメインも要りません。ビルドマシンは GitHub の macOS（無料枠あり）。

```
specs/*.json  ──push──▶  GitHub Actions (macos-14)
                              │  swiftc でコンパイル
                              │  .app に組み立て + ad-hoc 署名
                              ▼
                     Release に .zip が自動で並ぶ
```

## できること

| 起動方法 | やること |
|---|---|
| **push** | `specs/*.json` を書き換えて main に push |
| **手動** | Actions タブ → `App on the fly` → Run workflow → spec を選ぶ |
| **注文フォーム** | Issue を「アプリ注文」テンプレで作る → `build` ラベルを付ける → bot が結果をコメント |

Issue 方式が「サービス」っぽい使い方です。誰でも注文書を書けて、返ってきたリンクから
アプリをダウンロードできます（公開リポジトリの場合）。

## フォルダ構成

```
.github/workflows/build.yml   ← 本体。macOS でビルドするワークフロー
.github/ISSUE_TEMPLATE/       ← 注文フォーム
scripts/prepare_spec.py       ← どのレシピを使うか決める（Issue本文からJSONを抜く）
scripts/render.py             ← JSON → main.swift / Info.plist に流し込む
scripts/build_app.sh          ← コンパイル → .app 組み立て → 署名 → zip
templates/main.swift.tmpl     ← アプリの中身（SwiftUI）
templates/Info.plist.tmpl     ← アプリの身分証
specs/*.json                  ← レシピ。ここを増やすとアプリが増える
```

## レシピの書き方

```json
{
  "name": "アプリ名（40文字まで）",
  "bundle_id": "com.example.myapp",
  "version": "1.0.0",
  "tagline": "画面に出る一言",
  "accent": "#FF6B35",
  "second": "#FFB03A",
  "symbol": "paperplane.fill",
  "min_macos": "13.0"
}
```

- `accent` / `second` … 背景グラデーションの2色（`#RRGGBB`）
- `symbol` … SF Symbols の名前（`sparkles`, `gamecontroller.fill`, `bolt.fill` など）
- `bundle_id` の最後の部分がファイル名・実行ファイル名になります
- `name` に `< > " ' / \ $ ` は使えません（ファイル名になるため）

## 初回だけ必要な設定

1. このフォルダを GitHub のリポジトリに push（**Public 推奨**。理由は下の料金）
2. リポジトリ → Settings → Actions → General →
   **Workflow permissions** を `Read and write permissions` にする
   （Release 作成と Issue コメントに必要。これがないと最後の2ステップが失敗します）
3. Issue 方式を使うなら、リポジトリに `build` というラベルを1つ作る

それ以外のトークン設定は不要です（`GITHUB_TOKEN` で完結します）。

## 料金の目安

- **公開リポジトリ** … 標準ランナーは無料（macOS 含む）
- **非公開リポジトリ** … macOS は $0.062/分（Linux の約10倍）。
  1ビルド 2〜4分なので 1回 十数セント。プランの無料枠から引かれます

出典: [GitHub Actions ランナーの料金](https://docs.github.com/en/billing/reference/actions-runner-pricing)

## 配布されたアプリが開かないとき

証明書を持っていないので **ad-hoc 署名**です。初回は Gatekeeper に止められます。

1. `.app` を右クリック →「開く」→「開く」
2. それでもダメなら:
   ```bash
   xattr -dr com.apple.quarantine "アプリ名.app"
   ```

本気で配るなら Apple Developer Program（年 $99）で署名＋公証（notarization）が必要です。

## 次の改造アイデア

- `scripts/render.py` の `render()` を増やして、画面を何パターンかから選べるようにする
- `templates/` にアイコン（`.icns`）を置いて `Contents/Resources` にコピーする
- `on: repository_dispatch` を足して、外のサイトのボタンから注文できるようにする
