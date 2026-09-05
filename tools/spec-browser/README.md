# Spec Browser

設計書とソースの関係をノードキャンバスで見る静的ビューア（REQ-sb-001〜005）。

## 起動

```bash
cd tools/spec-browser
npm install
npm run dev
```

`npm run index` で `docs/design/` を読み `public/snapshot.json` を生成する。`dev` / `build` の前に自動実行される。

## Pages

`develop` への push で `.github/workflows/spec-browser-pages.yml` が `VITE_BASE=/HotStreak/` でビルドし GitHub Pages に公開する。

リポジトリ設定で Pages の Source を **GitHub Actions** にする。
