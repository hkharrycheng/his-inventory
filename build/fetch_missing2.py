# -*- coding: utf-8 -*-
"""補下載 v2：短 timeout、單序、失敗快速跳過並記錄；跑完輸出剩餘清單。"""
import json, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
TMP = os.path.join(os.environ.get("TEMP", "/tmp"), "j19dl", "work2")
RAW = os.path.join(ROOT, "_raw", "inventory.ndjson")
BASE = "ZlzAbNty2a2ZjVsjn0Fcfjbtncc"
TABLE = "tblqoEAMoheCtFhA"
CLI = r"C:\Users\Harry\AppData\Local\Doubao\User Data\Default\sandbox_envs_dir\envs\83ab0c2b-d9d8-43d0-ad83-88315d846c79\override_dlcs\lark-cli.exe"
OWN = {"Harry", "Father", "Dyna"}


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


rows = [json.loads(l) for l in open(RAW, encoding="utf-8-sig") if l.strip()]
keep = [r for r in rows if set(vals(r.get("Owner"))) & OWN]
files = set(os.listdir(IMG))
todo = []
for r in keep:
    rid = r["record_id"]
    for tag, field in (("ps", "Product Shot"), ("img", "圖片")):
        atts = r.get(field) or []
        have = sum(1 for f in files if f.startswith(rid + "_" + tag))
        if len(atts) > have:
            todo.append(r)
            break
print("todo", len(todo), flush=True)

limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(todo)
okn = 0
bad = []
for i, r in enumerate(todo[:limit], 1):
    rid = r["record_id"]
    d = os.path.join(TMP, rid)
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    cmd = [CLI, "base", "+record-download-attachment", "--base-token", BASE, "--table-id", TABLE,
           "--as", "user", "--record-id", rid, "--output", d, "--overwrite"]
    resp = None
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=40)
        txt = p.stdout.decode("utf-8", "replace")
        resp = json.loads(txt[txt.find("{"):]) if "{" in txt else None
    except Exception as e:
        resp = {"ok": False, "err": type(e).__name__}
    if not resp or not resp.get("ok"):
        bad.append(rid)
        print("x", rid, str(resp)[:80], flush=True)
        shutil.rmtree(d, ignore_errors=True)
        time.sleep(2)
        continue
    saved = {it["file_token"]: it["saved_path"]
             for it in (resp.get("data") or {}).get("downloaded", [])}
    for tag, field in (("ps", "Product Shot"), ("img", "圖片")):
        for n, a in enumerate(r.get(field) or [], 1):
            sp = saved.get(a["file_token"])
            if not sp or not os.path.exists(sp):
                continue
            ext = os.path.splitext(sp)[1].lower() or ".jpg"
            shutil.copyfile(sp, os.path.join(IMG, "%s_%s%d%s" % (rid, tag, n, ext)))
    shutil.rmtree(d, ignore_errors=True)
    okn += 1
    if i % 5 == 0:
        print("ok", okn, "at", i, "files", len(os.listdir(IMG)), flush=True)
    time.sleep(1.5)

print("FINISH ok", okn, "bad", len(bad), "files", len(os.listdir(IMG)), flush=True)
