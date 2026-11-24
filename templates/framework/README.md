# LLM Wiki 框架

版本 {{VERSION}}，改了什麼見 [`CHANGELOG.md`](CHANGELOG.md)。

一個用純文字和 git 管理的個人知識庫框架，設計給人和 AI agent 一起維護、一起使用。

- 原件（raw）整理成四種頁：筆記（note）、資料（data）、圖（figure）、程式碼（code）。
- 四種頁都依知識點分資料夾，同編號就是同一項；每個知識點有入口 NOTE.md。
- 用多語的詞條（term）把頁串起來，產生索引給 agent 快速檢索。
- 技能（skill）把頁打包成 agent 可以照著做的工作，可以輸出成私人版或公開版，也可以裝進工作專案再把改進帶回來。
- 全部從 `python scripts/wiki.py` 進入，只用 Python 標準庫。

這是空的框架：沒有任何主題、詞條、頁或技能。

## 開始

```bash
python scripts/wiki.py new wiki <名稱> --kind general --title "主題的標題"
python scripts/wiki.py new plan <英文名稱> --title "第一份原件"
python scripts/wiki.py index
python scripts/wiki.py lint
```

接下來讀：

- 整體設計：[`docs/FRAMEWORK.md`](docs/FRAMEWORK.md)
- 給 agent 的入口：[`AGENTS.md`](AGENTS.md)
- 怎麼查和用：[`USING.md`](USING.md)
- 怎麼新增和維護：[`MAINTAINING.md`](MAINTAINING.md)
- 用語：`terms/knowledge-base.csv`、`terms/general.csv`（用 `python scripts/wiki.py query term <名稱>` 查）
- 一次做不完的工作怎麼開計畫、怎麼續作：`MAINTAINING.md` 第 10 節

說明文件裡的範例代號（例如 `project-demo`、`bearing-connection`）只是示範，這個空框架裡沒有這些頁。

## 和工作架構串聯

這個知識庫是獨立的 repo，可以單獨用，也可以接到工作架構（[workspace-framework](https://github.com/warren3dtw/workspace-framework)）。兩個 repo 各自下載、各自 commit，工作架構只記知識庫的網址和放在哪裡，不把知識庫的內容 commit 進去。

在工作架構的根目錄：

```bash
python scripts/ws.py kb link <這個知識庫的 repo 網址>     # 下載到 knowledge/llm-wiki/（已被工作架構的 .gitignore 排除）
python scripts/ws.py kb link ../my-wiki                  # 或指向本機已經有的知識庫資料夾
python scripts/ws.py kb status                           # 串聯狀態、知識庫的 commit
python scripts/ws.py kb pull                             # 更新知識庫
python scripts/ws.py kb query search 搭接                 # 其他參數直接交給 scripts/wiki.py
python scripts/ws.py kb skill <代號> --profile <專案主題>  # 把這裡的技能輸出到工作架構的 skills/，再裝進 .claude 和 .agents
python scripts/ws.py kb ingest-skill <代號>               # 工作架構裡改進的技能帶回這裡的 skills/<代號>/incoming/
```

- 串聯後 `ws.py check` 會順便跑這裡的 `wiki.py lint`。
- 知識庫的改動在這個 repo commit 和 push；工作架構的改動在工作架構 commit。
- 不用工作架構時，`python scripts/wiki.py install skill <代號> <專案路徑> --bare` 一樣可以直接把技能裝進任何專案。

## 放進自己的內容之前

- 有著作權的原件不進 git（`.gitignore` 已經排除），登記卡要填授權和 `share`。
- 專案的內容放在 `project-` 開頭的主題；repo 要不要公開，取決於你放了什麼。
- 根目錄的 `denylist.txt` 填上不能出現在公開輸出裡的字。
