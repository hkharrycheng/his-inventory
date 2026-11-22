// J19 HIS Inventory — 狀態寫回 Worker
// 職責：①寫入 Feishu Base（App 身份）②重生 data.json（GitHub Contents API）③回傳統計
const BASE = "ZlzAbNty2a2ZjVsjn0Fcfjbtncc";
const TABLE = "tblqoEAMoheCtFhA";
const REPO = "hkharrycheng/his-inventory";
const STATUSES = ["Working", "Obsoleted", "Sold", "Donated", "N/A"];
const FAMILIES = ["HIS", "HMS", "HFS", "HDS", "HPC", "FPC"];

let tokCache = { t: "", exp: 0 };

async function tenantToken(env) {
  const now = Date.now();
  if (tokCache.t && tokCache.exp > now) return tokCache.t;
  const r = await fetch("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ app_id: env.APP_ID, app_secret: env.APP_SECRET }),
  });
  const j = await r.json();
  if (!j.tenant_access_token) throw new Error("token fail: " + JSON.stringify(j).slice(0, 200));
  tokCache = { t: j.tenant_access_token, exp: now + (j.expire - 120) * 1000 };
  return tokCache.t;
}

function cors() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "access-control-allow-headers": "content-type,x-j19-key",
    "access-control-max-age": "86400",
  };
}

function b64encode(str) {
  // UTF-8 → base64（Workers 無 btoa for unicode）
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin);
}

function b64decode(b64) {
  const bin = atob(b64.replace(/\s/g, ""));
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function recompute(data, id, status) {
  const it = data.items.find((x) => x.id === id);
  if (!it) return null;
  it.status = status;
  const st = {};
  for (const x of data.items) st[x.status || "未標示"] = (st[x.status || "未標示"] || 0) + 1;
  data.counts.status = st;
  data.counts.working = st["Working"] || 0;
  data.counts.obsoleted = st["Obsoleted"] || 0;
  data.counts.nonWorking = data.items.filter((x) => x.status !== "Working").length;
  data.counts.withDocx = data.items.filter((x) => x.docxNo).length;
  const wbf = {};
  for (const f of FAMILIES) wbf[f] = 0;
  const fs = {};
  for (const f of FAMILIES) fs[f] = { Working: 0, Obsoleted: 0, other: 0 };
  for (const x of data.items) {
    const fam = x.fam && FAMILIES.includes(x.fam) ? x.fam : "未標示";
    if (x.status === "Working") wbf[fam] = (wbf[fam] || 0) + 1;
    if (FAMILIES.includes(x.fam)) {
      fs[x.fam][x.status === "Working" ? "Working" : x.status === "Obsoleted" ? "Obsoleted" : "other"] += 1;
    }
  }
  data.counts.workingByFam = wbf;
  data.famStats = fs;
  data.generated = new Date(Date.now() + 8 * 3600 * 1000).toISOString().slice(0, 16).replace("T", " ");
  return { counts: data.counts, famStats: fs };
}

async function patchJson(env, id, status) {
  const api = `https://api.github.com/repos/${REPO}/contents/data.json`;
  const h = { authorization: `Bearer ${env.GH_PAT}`, accept: "application/vnd.github+json", "user-agent": "j19-worker" };
  const g = await fetch(api + "?ref=main", { headers: h });
  if (!g.ok) throw new Error("gh get " + g.status);
  const gj = await g.json();
  const data = JSON.parse(b64decode(gj.content));
  const res = recompute(data, id, status);
  if (!res) throw new Error("record not in data.json");
  const body = {
    message: `status: ${id} → ${status}`,
    content: b64encode(JSON.stringify(data)),
    sha: gj.sha,
    branch: "main",
  };
  const p = await fetch(api, { method: "PUT", headers: { ...h, "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!p.ok) throw new Error("gh put " + p.status + " " + (await p.text()).slice(0, 200));
  return res;
}

export default {
  async fetch(req, env) {
    const c = cors();
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: c });
    const url = new URL(req.url);
    const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { ...c, "content-type": "application/json; charset=utf-8" } });

    if (url.pathname === "/" || url.pathname === "/health") {
      return json({ ok: true, app: "J19 status worker", table: TABLE });
    }

    if (url.pathname === "/status" && req.method === "POST") {
      if (req.headers.get("x-j19-key") !== env.J19_KEY) return json({ ok: false, error: "unauthorized" }, 401);
      let b;
      try { b = await req.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }
      const id = (b.id || "").trim();
      const status = (b.status || "").trim();
      if (!/^rec\w+$/.test(id)) return json({ ok: false, error: "bad id" }, 400);
      if (!STATUSES.includes(status)) return json({ ok: false, error: "bad status" }, 400);
      try {
        const tk = await tenantToken(env);
        const r = await fetch(`https://open.feishu.cn/open-apis/bitable/v1/apps/${BASE}/tables/${TABLE}/records/${id}`, {
          method: "PUT",
          headers: { authorization: `Bearer ${tk}`, "content-type": "application/json; charset=utf-8" },
          body: JSON.stringify({ fields: { "狀態": status } }),
        });
        const rj = await r.json();
        if (rj.code !== 0) return json({ ok: false, stage: "base", error: rj.msg, code: rj.code }, 502);
        const res = await patchJson(env, id, status);
        return json({ ok: true, id, status, counts: res.counts, famStats: res.famStats });
      } catch (e) {
        return json({ ok: false, error: String(e).slice(0, 300) }, 500);
      }
    }
    return json({ ok: false, error: "not found" }, 404);
  },
};
