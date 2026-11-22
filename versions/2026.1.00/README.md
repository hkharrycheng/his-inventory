# J19 — HIS Inventory（固定資產圖庫）

Harry Information System（HIS）固定資產總覽，資料源為 Feishu Base
[Inventory Records](https://feishu.doubao.com/base/ZlzAbNty2a2ZjVsjn0Fcfjbtncc) 的 `HIS Inventory`
表（`tblqoEAMoheCtFhA`），只納入 Owner = **Harry／Father／Dyna** 的資產。

## 版本
- v2026.1.00 — 首版：統計 TAB（Pie + 五族 Bar）、搜尋 TAB（DOCX／OWNER／類別／文字）、Product Shot 圖庫格、詳情 overlay、全屏 lightbox

## TAB 說明
1. **統計**
   - KPI：總資產 263、Working 177、Obsoleted 52、有 DOCX 章節 129
   - Pie：Working vs Obsoleted（Sold／Donated／N/A 不入圖，另列註記）
   - Bar：HIS／HMS／HFS／HDS／HPC 五族，綠＝Working、紅＝Obsoleted、灰＝其他狀態
2. **搜尋**
   - Filter：DOCX（全部／有／未有）、OWNER（全部／Harry／Father／Dyna）、類別（32 類）、文字搜尋（名稱／品牌／型號／規格／詳細文字／DOCX 章節）
   - 結果以 Product Shot 圖庫格呈現（4:3 圖框、狀態色點、名稱、品牌·型號、HIS／狀態／類別標籤）
   - 點卡片開啟詳情：Specification 各欄位值、文字詳細、表格詳細、圖片詳細（Product Shot ＋實物圖），點圖可全屏放大並左右切換

## 目錄
```
index.html            前端單檔（深色 760px 版式，底部 2 TAB）
data.json             由 build_data.py 生成（263 筆資產 + 統計）
images/               Product Shot / 實物圖，命名 <record_id>_ps<N>.<ext> / <record_id>_img<N>.<ext>
_raw/inventory.ndjson Base 全欄位 dump（298 筆原始記錄）
build/fetch_images.py 由 Base 附件下載圖片（state 斷點續跑）
build/build_data.py   生成 data.json
```

## 本機預覽
```
cd "D:\Onedrive\Harry Information System\豆包Agents Program Backup\HFSInventory"
python -m http.server 8801
```
開 http://localhost:8801/

## 重建流程
1. 由 Base dump 記錄到 `_raw/inventory.ndjson`（`lark-cli base +record-list --format ndjson`）
2. `python build\fetch_images.py`（必需時再跑 `build\fetch_missing.py` 補漏）
3. `python build\build_data.py`（生成 `data.json`）
4. localhost 驗證 → 部署
