# J19 — HIS Inventory（固定資產圖庫）

Harry Information System（HIS）固定資產總覽，資料源為 Feishu Base
[Inventory Records](https://feishu.doubao.com/base/ZlzAbNty2a2ZjVsjn0Fcfjbtncc) 的 `HIS Inventory`
表（`tblqoEAMoheCtFhA`），只納入 Owner = **Harry／Father／Dyna** 的資產（263 筆）。

線上：<https://hkharrycheng.github.io/his-inventory/>

## 版本
- v2026.1.00 — 首版：統計 TAB（Pie + 五族 Bar）、搜尋 TAB、Product Shot 圖庫格、詳情 overlay、全屏 lightbox
- v2026.1.01 — 第二版：
  1. 搜尋預設只顯示 **Working**、預設按 **購買日期 新→舊** 排序
  2. **DOCX › 類別** 合併成父子式 filter（DOCX 先收窄，類別選項隨之縮減），可多選；另加 **HIS 系列**、**Source** 多選
  3. 統計：所有 non-working 歸一類（86）；Pie 改為「Working 內各 HIS 系列比較」、Bar 只畫 Working，兩者可點擊跳轉搜尋並自帶 filter
  4. 詳情頁狀態可 **dropdown 修改** → 先寫 Feishu Base，再自動重生（patch）`data.json`（Cloudflare Worker）
  5. 每個 inventory 有 **直達連結**（`?id=<record_id>`），卡片右上 🔗 一鍵複製
  6. 圖片 `onerror` fallback（避免爛圖顯示破圖 icon）；12 個 82-byte 壞圖已用 App 身份重下載修復
- v2026.1.02 — 第三版：
  1. 詳情頁加 **DOCX OneDrive Link**：由 `HIS Inventory Class` 表（`tblCxfZLCRIRMNMU`）的 `OneDrive Link`／`HIS DOCX 名稱` join 每筆 inventory（129／129 有連結），顯示「文檔編號 · DOCX 名 · 章節 · 同步日」＋「📄 開啟 DOCX（OneDrive）」按鈕
  2. HTML ICON（header logo 與 favicon）改用 **Register List 的圖標原件**（`icon.png`，file_token `ZbXAbYPyToxwVmxJDGoc2Pbknve`）
  3. `build_data.py` 讀 `_raw/class.ndjson` 建 mapping；`build/deploy_delta.py` 只推有改動檔案（base_tree 保留其餘）

## TAB 說明
1. **統計**
   - KPI：Working 177／非 Working 86／總數 263／有 DOCX 章節 129
   - Pie：Working 內 HIS 49／HFS 50／HDS 39／HMS 23／HPC 15／FPC 1
   - Bar：同上，只畫 Working；點任何一段／一條 → 搜尋 TAB 並套用該系列 filter
2. **搜尋**
   - Filter 列：狀態（Working／非 Working／全部）、HIS 系列（多選）、DOCX（全部／有／未有，作父層）、↳ 類別（多選，選項按 DOCX＋系列收窄）、Source（多選）、關鍵字、排序（購買日期新→舊為預設）
   - 圖庫格：Product Shot 4:3 圖框、狀態 badge、系列色 badge、DOCX 章節、購買日期；右上 🔗 複製直達連結
   - 詳情 overlay：hero 圖、狀態 dropdown（可寫回）、規格表、DOCX 章節、手冊／Product Link／Online Shop／在 Base 開啟、文字詳細、表格詳細、實物圖；點圖全屏 lightbox 左右切換

## 狀態寫回（v2026.1.01）
```
前端 <select> → POST https://j19-inventory.hkharrycheng.workers.dev/status
  → ①PUT Feishu Base record（App 身份 tenant_access_token，欄位「狀態」）
  → ②GitHub Contents API 讀／改／寫 data.json（只改該筆 status，重算 counts/famStats/workingByFam）
  → ③GitHub Pages 約 1 分鐘後同步
```
- Worker 專案：`build/worker_j19/`（`npx wrangler deploy --name j19-inventory`，部署於 `hkharrycheng.workers.dev`）
- Secrets：`APP_ID`、`APP_SECRET`、`J19_KEY`（前端共享鍵）、`GH_PAT`
- 寫入權限：HIS Tools 企業應用 `cli_aa5c9f01acf8dd08` 已是該 Base 可編輯協作者

## 目錄
```
index.html              前端單檔（深色 760px 版式，底部 2 TAB）
data.json               由 build_data.py 生成（263 筆資產 + 統計 + workingByFam／nonWorking）
images/                 Product Shot / 實物圖，命名 <record_id>_ps<N>.<ext> / <record_id>_img<N>.<ext>
_raw/inventory.ndjson   Base 全欄位 dump（298 筆原始記錄）
build/build_data.py     生成 data.json
build/fetch_app.py      以 App 身份下載 Base 附件（避開個人帳號配額限流）
build/fix_bad_images.py 偵測並重下載壞圖（82-byte JSON 冒充圖）
build/deploy_github.py  REST blobs→tree→commit→PATCH ref＋開 Pages
build/worker_j19/       狀態寫回 Worker（index.js + wrangler.toml）
```

## 本機預覽
```
cd "D:\Onedrive\Harry Information System\豆包Agents Program Backup\HFSInventory"
python -m http.server 8801
```
開 <http://localhost:8801/>

## 重建流程
1. 由 Base dump 記錄到 `_raw/inventory.ndjson`（`lark-cli base +record-list --format ndjson`）
2. `python build\fetch_app.py`（App 身份下載，必要時 `fix_bad_images.py` 補壞圖）
3. `python build\build_data.py`（生成 `data.json`）
4. localhost 驗證 → `python build\deploy_github.py`
