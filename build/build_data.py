# -*- coding: utf-8 -*-
"""J19 HIS Inventory — 由 _raw/inventory.ndjson + images/ 生成 data.json。
只取 Owner ∈ {Harry, Father, Dyna}。
"""
import datetime, io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
IMG = os.path.join(ROOT, "images")
OUT = os.path.join(ROOT, "data.json")
VERSION = "2026.1.02"
OWNERS = {"Harry", "Father", "Dyna"}
FAMILIES = ["HIS", "HMS", "HFS", "HDS", "HPC", "FPC"]
STATUSES = ["Working", "Obsoleted", "Sold", "Donated", "N/A"]


def vals(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, dict):
        n = v.get("name") or v.get("text")
        return [n] if n else []
    out = []
    for x in v:
        out += vals(x)
    return out


def one(v):
    a = vals(v)
    return a[0] if a else ""


def num(v):
    return v if isinstance(v, (int, float)) else (None if v in (None, "") else v)


def d(v):
    if not v or not isinstance(v, str):
        return ""
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", v)
    return m.group(1) if m else ""


def md_link(v):
    """把 '【text】](url)' 形式的 markdown 取 (text,url)，否則回 (原字串, "")。"""
    if not v:
        return "", ""
    m = re.search(r"\[([^\]]*)\]\((https?://[^)]+)\)", v)
    if m:
        return m.group(1), m.group(2)
    if v.startswith("http"):
        return v, v
    return v, ""


rows = [json.loads(l) for l in open(os.path.join(RAW, "inventory.ndjson"), encoding="utf-8-sig") if l.strip()]
keep = [r for r in rows if set(vals(r.get("Owner"))) & OWNERS]

# HIS Inventory Class（每筆 inventory → 所屬 HIS DOCX 卷 + OneDrive Link）
cls_rows = []
cls_path = os.path.join(RAW, "class.ndjson")
if os.path.exists(cls_path):
    cls_rows = [json.loads(l) for l in open(cls_path, encoding="utf-8-sig") if l.strip()]
docx_map = {}
for c in cls_rows:
    link_ids = []
    for x in (c.get("HIS Inventory") or []):
        if isinstance(x, dict) and x.get("id"):
            link_ids.append(x["id"])
    info = {
        "doc": (c.get("HIS DOCX 名稱") or "").strip(),
        "code": (c.get("文檔編號") or "").strip(),
        "od": (c.get("OneDrive Link") or "").strip(),
        "file": (c.get("本機檔名") or "").strip(),
        "sync": (c.get("上次同步時間") or ""),
    }
    for rid in link_ids:
        docx_map[rid] = info
print("class rows", len(cls_rows), "mapped ids", len(docx_map))


# 圖庫：images/<record_id>_ps<N>.<ext> / _img<N>.<ext>
gal = {"ps": {}, "img": {}}
for f in sorted(os.listdir(IMG)):
    m = re.match(r"^(rec\w*)_(ps|img)(\d+)(\.[A-Za-z0-9]+)$", f)
    if m:
        gal[m.group(2)].setdefault(m.group(1), []).append((int(m.group(3)), "images/" + f))

items = []
for r in keep:
    rid = r["record_id"]
    his = one(r.get("HIS"))
    fam = his[:3] if his else ""
    manual_t, manual_u = md_link(one(r.get("手冊")))
    plink_t, plink_u = md_link(one(r.get("Product Link")))
    row = {
        "id": rid,
        "name": r.get("家電名稱") or "",
        "brand": r.get("品牌") or "",
        "model": r.get("型號") or "",
        "tech": r.get("Technical Class") or "",
        "cat": vals(r.get("類別")),
        "subcat": vals(r.get("子類別")),
        "owner": vals(r.get("Owner")),
        "status": one(r.get("狀態")),
        "his": his,
        "fam": fam,
        "docxNo": (r.get("DOCX 章節編號") or "").strip(),
        "docxTitle": one(r.get("DOCX 章節標題")),
        "docxSync": d(r.get("上次同步DOCX")),
        "docxDoc": docx_map.get(rid, {}).get("doc", ""),
        "docxCode": docx_map.get(rid, {}).get("code", ""),
        "docxLink": docx_map.get(rid, {}).get("od", ""),
        "docxFile": docx_map.get(rid, {}).get("file", ""),
        "buyDate": d(r.get("Buy Date")),
        "abandoned": d(r.get("Abandoned Date")),
        "release": d(r.get("Official Release")),
        "price": num(r.get("購買價 HK$")),
        "sellPrice": num(r.get("Selling Price HK$")),
        "warranty": num(r.get("保固(月)")),
        "weight": num(r.get("重量 (kg)")),
        "capacity": r.get("容量") or "",
        "resolution": r.get("Resolution") or "",
        "spec": r.get("規格") or "",
        "powerCap": r.get("Power Capacity") or "",
        "opPower": r.get("Operating Power") or "",
        "source": one(r.get("Source")),
        "onlineShop": r.get("Online Shop") or "",
        "manual": {"t": manual_t, "u": manual_u},
        "productLink": {"t": plink_t, "u": plink_u},
        "passmark": num(r.get("Passmark")),
        "sc": num(r.get("Single Core Geekbench")),
        "mc": num(r.get("Multi-Core Geekbench")),
        "futuremark": num(r.get("Futuremark")),
        "text": r.get("文字詳細") or "",
        "detailTable": r.get("表格詳細") or "",
        "ps": [p for _, p in sorted(gal["ps"].get(rid, []))],
        "pics": [p for _, p in sorted(gal["img"].get(rid, []))],
    }
    items.append(row)

# 統計
st_counts = {}
for it in items:
    st_counts[it["status"] or "未標示"] = st_counts.get(it["status"] or "未標示", 0) + 1
fam_stats = {f: {"Working": 0, "Obsoleted": 0, "other": 0} for f in FAMILIES}
fam_other = {}
for it in items:
    if it["fam"] in fam_stats:
        key = it["status"] if it["status"] in ("Working", "Obsoleted") else "other"
        fam_stats[it["fam"]][key] += 1
    elif it["fam"]:
        fam_other[it["fam"]] = fam_other.get(it["fam"], 0) + 1

cats = sorted({c for it in items for c in it["cat"]})
subcats = sorted({c for it in items for c in it["subcat"]})
docx_cnt = sum(1 for it in items if it["docxNo"])

# Working 內各系列（Pie/Bar 口徑）；非 Working 一律歸一類
working_by_fam = {f: 0 for f in FAMILIES}
for it in items:
    if it["status"] == "Working":
        working_by_fam[it["fam"] if it["fam"] in working_by_fam else "未標示"] = \
            working_by_fam.get(it["fam"] if it["fam"] in working_by_fam else "未標示", 0) + 1
non_working = sum(1 for it in items if it["status"] != "Working")
sources = sorted({it["source"] for it in items if it["source"]})

data = {
    "app": "J19 HIS Inventory",
    "version": VERSION,
    "base": "ZlzAbNty2a2ZjVsjn0Fcfjbtncc",
    "table": "HIS Inventory（tblqoEAMoheCtFhA）",
    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "owners": ["Harry", "Father", "Dyna"],
    "counts": {
        "total": len(items),
        "sourceRows": len(rows),
        "working": st_counts.get("Working", 0),
        "nonWorking": non_working,
        "workingByFam": working_by_fam,
        "obsoleted": st_counts.get("Obsoleted", 0),
        "status": st_counts,
        "withDocx": docx_cnt,
        "withDocxLink": sum(1 for it in items if it["docxLink"]),
        "noDocx": len(items) - docx_cnt,
        "withPs": sum(1 for it in items if it["ps"]),
        "withPics": sum(1 for it in items if it["pics"]),
        "psFiles": sum(len(it["ps"]) for it in items),
        "picFiles": sum(len(it["pics"]) for it in items),
    },
    "families": FAMILIES,
    "statuses": STATUSES,
    "sources": sources,
    "famStats": fam_stats,
    "famOther": fam_other,
    "cats": cats,
    "subcats": subcats,
    "items": items,
}
io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
print("data.json", os.path.getsize(OUT), "bytes")
print("items", len(items), "status", st_counts, "docx", docx_cnt)
print("famStats", fam_stats, "famOther", fam_other)
print("ps", sum(len(it["ps"]) for it in items), "pics", sum(len(it["pics"]) for it in items))
