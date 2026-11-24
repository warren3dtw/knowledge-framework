# 索引總覽

由 `scripts/wiki.py index` 產生，不要手改。agent 先讀這一頁，再依需要讀 `points.json`、`catalog.jsonl`、`terms.json`。

## 主題

| 主題 | 種類 | 範圍 | 知識點 | 原件 | 筆記 | 資料 | 圖 |
|---|---|---|---|---|---|---|---|

## 知識點

每個知識點的入口是 `wikis/<主題>/note/<知識點>/NOTE.md`，列出全部的頁和閱讀順序。編號全部主題共用。

| 知識點 | 主題 | 標題 | 摘要 | 項目數 |
|---|---|---|---|---|

## 技能

技能放在 `skills/<代號>/SKILL.md`，是 agent 可以照著做的能力包。points 是它用到的知識點。

| 技能 | 版本 | 標題 | 用到的知識點 | 可見度 | 狀態 |
|---|---|---|---|---|---|
| — | | 目前沒有技能 | | | |


詞條（term）共 44 個：指令與快捷鍵 9、概念 33、方法與理論 1、軟體與工具 1

## 怎麼查

- 用程式：`python scripts/wiki.py query search <關鍵字>`、`query point <知識點>`，說明見 `USING.md`。
- 不用程式：`catalog.jsonl` 每行是一頁的 JSON，有 title、summary、keywords（含中英日名稱）、path、file。
  用關鍵字篩出幾行，再打開 path 讀說明、打開 file 讀數據、圖或程式。
- 專案主題預設不查。問題提到專案時才查。
- share 是可見度：public 可以公開、attribution 要標出處、private 不能拿出這個 repo。由原件的授權推算。
- 同一個 item（知識點-編號）的頁是同一項，pair 欄位互相列出。
- 每行的 status 不是 reviewed 的，還沒經過擁有者確認。origin 是 fileback 的，是查詢後回存的頁。
