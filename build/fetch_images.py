# -*- coding: utf-8 -*-
"""J19 HIS Inventory — 下載 Product Shot(fldgmLbXMH) 與 圖片(fldZrjyEeg) 附件。
每筆記錄一次 CLI 呼叫，--output 先落 %TEMP%\\j19dl\\<record_id>\\，再改名搬去 images\\。
命名：images/<record_id>_ps<N>.<ext>、<record_id>_img<N>.<ext>
"""
import json, os, shutil, subprocess, sys, time

CLI = r"C:\Users\Harry\AppData\Local\Doubao\User Data\Default\sandbox_envs_dir\envs\83ab0c2b-d9d8-43d0-ad83-88315d846c79\override_dlcs\lark-cli.exe"
BASE = "ZlzAbNty2a2ZjVsjn0Fcfjbtncc"
TABLE = "tblqoEAMoheCtFhA"
ROOT = r"D:\Onedrive\Harry Information System\豆包Agents Program Backup\HFSInventory"
IMG = os.path.join(ROOT, "images")
TMP = os.path.join(os.environ["TEMP"], "j19dl")
PS_FID = "fldgmLbXMH"
PIC_FID = "fldZrjyEeg"

def vals(v):
    if v is None: return []
    if isinstance(v, str): return [v]
    if isinstance(v, dict): return [v.get("name") or ""]
    out = []
    for x in v: out += vals(x)
    return out

rows = [json.loads(l) for l in open(os.path.join(ROOT, "_raw", "inventory.ndjson"), encoding="utf-8-sig") if l.strip()]
keep = [r for r in rows if set(vals(r.get("Owner"))) & {"Harry", "Father", "Dyna"}]
todo = [r for r in keep if (r.get("Product Shot") or r.get("圖片"))]
print("keep", len(keep), "with attachments", len(todo))

state_p = os.path.join(TMP, "state.json")
state = json.load(open(state_p, encoding="utf-8")) if os.path.exists(state_p) else {}
fail = state.get("__fail__", [])


def job(r):
    rid = r["record_id"]
    if rid in state and state[rid].get("ok"):
        return None
    d = os.path.join(TMP, rid)
    if os.path.isdir(d): shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    cmd = [CLI, "base", "+record-download-attachment", "--base-token", BASE, "--table-id", TABLE,
           "--as", "user", "--record-id", rid, "--output", d, "--overwrite"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    saved = {}
    ok = p.returncode == 0
    try:
        resp = json.loads(p.stdout)
        ok = bool(resp.get("ok"))
        for it in (resp.get("data") or {}).get("downloaded", []):
            saved[it["file_token"]] = it["saved_path"]
    except Exception:
        pass
    if not ok:
        return {"record_id": rid, "ok": False, "err": (p.stdout or p.stderr or "")[:200],"r":r}
    made = []
    for tag, field in (("ps", "Product Shot"), ("img", "圖片")):
        for n, a in enumerate(r.get(field) or [], 1):
            sp = saved.get(a["file_token"])
            if not sp or not os.path.exists(sp): continue
            ext = os.path.splitext(sp)[1].lower() or ".jpg"
            dst = os.path.join(IMG, "%s_%s%d%s" % (rid, tag, n, ext))
            shutil.copyfile(sp, dst)
            made.append(os.path.basename(dst))
    shutil.rmtree(d, ignore_errors=True)
    return {"record_id": rid, "ok": True, "files": made, "r": r}


import concurrent.futures as cf

done = 0
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(job, r) for r in todo]
    for fu in cf.as_completed(futs):
        res = fu.result()
        done += 1
        if res is None:
            continue
        if res["ok"]:
            state[res["record_id"]] = {"ok": True, "files": res["files"]}
        else:
            fail.append({"record_id": res["record_id"], "err": res["err"]})
        if done % 10 == 0:
            state["__fail__"] = fail
            json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False)
            print("progress", done, "/", len(todo), "images", len(os.listdir(IMG)), flush=True)

state["__fail__"] = fail
json.dump(state, open(state_p, "w", encoding="utf-8"), ensure_ascii=False)
print("done; images:", len(os.listdir(IMG)), "fails:", len(fail))
