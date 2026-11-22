# -*- coding: utf-8 -*-
"""J19 delta deploy：只推有改動的檔案（base_tree 保留其餘）。"""
import base64, json, os, sys
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "_raw")
API = "https://api.github.com"
REPO = "his-inventory"


def token():
    for line in open(r"D:\Onedrive\Harry Information System\豆包Agents Program Backup\MHO\_raw\consts.ndjson", encoding="utf-8"):
        if "ghp_" not in line:
            continue
        r = json.loads(line)
        if r.get("工作名") == "Cathay Tickets (J09)":
            v = str(r["Parameter"])
            import re
            m = re.search(r"ghp_[A-Za-z0-9_]{30,}", v)
            if m:
                return m.group(0)
    raise SystemExit("PAT not found")


TOK = token()
S = requests.Session()
S.headers.update({"Authorization": "Bearer " + TOK, "Accept": "application/vnd.github+json",
                  "X-GitHub-Api-Version": "2022-11-28"})


def call(method, url, **kw):
    r = S.request(method, API + url, timeout=120, **kw)
    if r.status_code >= 300:
        print("ERR", method, url, r.status_code, r.text[:400])
        raise SystemExit(1)
    return r.json() if r.text else {}


def blob_sha_for(rel, fp):
    ext = os.path.splitext(fp)[1].lower()
    size = os.path.getsize(fp)
    if ext in {".html", ".json", ".md", ".py", ".css", ".js", ".txt"} and size < 2_000_000:
        return None
    b64 = base64.b64encode(open(fp, "rb").read()).decode()
    return call("POST", "/repos/%s/%s/git/blobs" % (login, REPO),
                json={"content": b64, "encoding": "base64"})["sha"]


def text_of(fp):
    return open(fp, "rb").read().decode("utf-8")


login = call("GET", "/user")["login"]
ver = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))["version"]

# 只放有改動的檔案
rels = ["index.html", "data.json", "icon.png", "README.md", "build/build_data.py",
        "build/deploy_delta.py", "build/worker_j19/index.js", "build/worker_j19/wrangler.toml",
        "versions/%s/index.html" % ver, "versions/%s/data.json" % ver, "versions/%s/README.md" % ver]
files = []
for rel in rels:
    if rel.startswith("versions/"):
        src = os.path.join(ROOT, rel.split("/", 2)[2])
    else:
        src = os.path.join(ROOT, rel)
    if os.path.exists(src):
        files.append((rel, src))
print("delta files:", [f[0] for f in files])

tree = []
for rel, fp in files:
    if os.path.splitext(fp)[1].lower() in {".html", ".json", ".md", ".py", ".js", ".toml"} and os.path.getsize(fp) < 2_000_000:
        tree.append({"path": rel, "mode": "100644", "type": "blob", "content": text_of(fp)})
    else:
        sha = blob_sha_for(rel, fp)
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": sha})

ref = S.get(API + "/repos/%s/%s/git/ref/heads/main" % (login, REPO))
head = ref.json()["object"]["sha"] if ref.status_code == 200 else None
base_tree = call("GET", "/repos/%s/%s/git/commits/%s" % (login, REPO, head))["tree"]["sha"] if head else None

body = {"tree": tree}
if base_tree:
    body["base_tree"] = base_tree
t = call("POST", "/repos/%s/%s/git/trees" % (login, REPO), json=body)["sha"]
kw = {"message": "J19 v%s: 詳情加 DOCX OneDrive Link（HIS Inventory Class join）＋轉用 Register List 圖標" % ver, "tree": t}
if base_tree:
    kw["parents"] = [head]
c = call("POST", "/repos/%s/%s/git/commits" % (login, REPO), json=kw)["sha"]
call("PATCH", "/repos/%s/%s/git/refs/heads/main" % (login, REPO), json={"sha": c})
print("commit", c[:8])
print("pages https://%s.github.io/%s/" % (login, REPO))
