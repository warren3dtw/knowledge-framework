# 框架版本紀錄

框架（腳本、schema、規則、模板、技能層）的版本。只往上追加。版本號寫在 `schema.json` 的 `framework_version`，和這裡最上面一筆要相同，lint 會檢查。

- 主版本：改了檔案格式或欄位，舊的頁要跟著改。
- 次版本：加了新的功能、規則或模板，舊的頁不必改。
- 修正：修錯，行為不變。

知識內容的變動不記在這裡。

## 1.2.0（2026-11-24）

- 知識庫獨立成一個 repo：文件放回知識庫自己的 `docs/`（`schema.json` 的 `docs` 寫成 `docs`），說明文件跟著改。
- README 新增「和工作架構串聯」：工作架構用 `ws.py kb link` 下載這個 repo，`ws.py kb skill`／`kb ingest-skill` 輸出技能和帶回改動。
- 空框架不附任何技能（`framework.json` 的 `skills` 清空），技能另外發。

## 1.1.2（2026-11-18）

- 知識點入口的樣板改名 `templates/point.md`。原本的 `templates/NOTE.md` 和筆記的樣板 `templates/note.md` 在 Windows 上是同一個檔名，git 裡的 `NOTE.md` 其實是舊版的筆記樣板，所以一直顯示有修改；現在從 git 移除，另寫一份真正的知識點入口樣板（FEEDBACK F-021）。
- `tests/mvp_test.py` 的回存測試不再寫死下一個編號是 005，改成比對回存前後多出來的那一頁（`clt-design-strength` 已經用到 008）。

## 1.1.1（2026-11-17）

- lint 不再對 `schema.json` 的 `types.term.unused_ok` 列出的領域（knowledge-base、general）提醒「沒有頁用到的詞條」。

## 1.1.0（2026-11-17）

- `GLOSSARY.md` 移除，內容改成詞條：知識庫框架的用語放新領域 `knowledge-base`（頁、詞條、技能、五個動作等），通用的軟體用語放新領域 `general`（檔頭、CSV、OCR、git），`agent` 也放 `general`；「存檔點」沿用原有的 `checkpoint`。用 `query term <名稱>` 查。
- `export framework` 帶上 `framework.json` 的 `term_domains` 列出的領域（預設 knowledge-base、general）的完整詞條，其他領域只留欄位那一列。

## 1.0.0（2026-11-17）

- 原子（atom）改名為**詞條**（term）：資料夾 `atoms/` → `terms/`、代號 `atom:<名稱>` → `term:<名稱>`、頁和技能檔頭的 `atoms` 欄位 → `terms`、索引 `atoms.json` → `terms.json`、查詢 `query atom` → `query term`。舊的頁要跟著改（已全部改好）。
- 詞條依領域（domain）分檔：`terms/<領域>.csv`，領域登記在 `schema.json` 的 `types.term.domains`（structural 結構、construction 施工、ai-agent、javascript、web3d、organization 組織與專案）。檔名就是領域，代號全部領域共用一套；lint 檢查領域有沒有登記。`query term` 和 `terms.json` 會列出領域。
- 文件（FRAMEWORK、FEEDBACK、計畫、討論紀錄）從知識庫的 `docs/` 移到工作架構文件區的 `docs/`，位置寫在 `schema.json` 的 `docs`（相對於知識庫根目錄）。`new plan`、lint 的計畫檢查跟著這個位置；`export framework` 把文件放回輸出裡的 `docs/` 並改好連結。

## 0.8.0（2026-11-17）

- 新增 `mcp-001-rhino-cadcraft-tools`：同時維護 Claude Code 與 Codex 的 Rhino MCP 設定，並恢復 CADCraft CLI 專案權限。
- Rhino MCP 改用 `Rhinoceros/ai/bin` 穩定入口，避免套件版本資料夾更新後設定失效；空框架預設帶入此技能。

## 0.7.0（2026-11-16）

- 程式碼不再是獨立的頁：程式檔和說明併進**同編號**的筆記（同名的程式檔放在 `note/<知識點>/`，筆記檔頭加 `file`、`language`、`runtime`、`verified`，內文加「## 程式碼」小節，這個小節不算進內文長度）。頁剩筆記、資料、圖三種。
- 沒有對應筆記的程式碼頁改成筆記，種類用新的 `snippet`（程式片段）或 `config`（設定），屬於「做法」組。
- `code/` 資料夾和 `templates/code.md` 移除；`--type code` 等於 `--type note`。NOTE.md 的表格拿掉「程式碼」欄，附程式的筆記標「（含程式碼）」。

## 0.6.0（2026-11-16）

- 原子（詞條）從一個一個的檔案改成一張對照表 `atoms/atoms.csv`，一列一個；代號（`atom:<名稱>`）、查詢、索引都不變。`templates/atom.md` 移除。
- 凍結分享用的功能：`share` 推算、公開版技能輸出、空框架輸出、機密掃描。保留、照常可用，之後只修錯，不再擴充；目前的重點是保存經驗和再利用。
- 技能只改這裡的主版本；工作專案裡的副本由程式安裝，不手改，也不用 `ingest skill` 從副本帶回來（`ingest skill` 只用在第一次匯入外面的技能）。

## 0.5.0（2026-11-16）

- 技能代號改成「前綴-三位數-英文簡短描述」（例如 `rhino-002-sequence-fasteners`），描述必填、64 字元以內；lint、`new skill`、`ingest skill` 照新格式檢查。
- 六個技能改名：init-001-project-scaffold、rhino-001-point-line-surface、rhino-002-sequence-fasteners、rhino-003-assembly-animation、pdf-001-detail-index、timber-001-assembly-sequence。
- 移除 `export skill --folder full`（資料夾名稱就是代號，已經包含描述）。

## 0.4.0（2026-11-14）

- 多次工作的計畫：`docs/plans/<日期-名稱>/` 和 `templates/plan/` 的 plan、specs、tasks，tasks 有階段與存檔點表。lint 檢查計畫資料夾的三份檔案。
- `docs/FEEDBACK.md` 記框架的問題和調整；本檔記框架的版本，版本號在 `schema.json`。
- `.claude/`：空的權限設定、唯讀的確認助手 `page-reviewer`、hooks 說明（不啟用）。
- MAINTAINING 新增「多次工作的計畫、存檔與 commit」。規則原文寫成知識點 `project-harness` 的筆記，init-001 依據它們。
- `export framework` 帶上版本號、本檔、計畫模板和 `.claude/`；技能依據的頁附在技能的 `references/`。

## 0.3.1（2026-11-14）

- 同編號有幾種頁時，只寫檔名先取筆記並提示其他頁。
- 輸出接到 `head` 時不印錯誤。
- 空框架的名稱替換支援正規表示式。
- `tests/mvp_test.py`：101 項 MVP 測試。

## 0.3.0（2026-11-14）

- 技能層：`skills/<代號>/`，用 `atoms`、`points`、`from`、`uses` 連到知識；`profiles/<專案主題>/` 放專案的慣例。
- 可見度：原件標 `share`，頁和技能用推算的；專案主題一律私人。
- 指令：`new wiki`、`new skill`、`ingest skill`、`export skill`、`install skill`、`export framework`、`query share`。
- 輸出前掃描：禁用字、本機路徑、Email、照抄的原件文字。
- lint：通用主題不能用內文連結或 raw 引用專案主題；依據更新後提醒重看。

## 0.2.0（2026-11-12）

- 改名：原件 raw、原子 atom、筆記 note、資料 data、圖 figure、程式碼 code。
- 四種頁依知識點分資料夾；檔名「知識點-編號-描述」，同編號就是同一項；每個知識點有入口 NOTE.md。

## 0.1.0（2026-11-11）

- 第一版 MVP：依形式分頁、多語原子、索引、ingest、query、fileback、lint、export。
