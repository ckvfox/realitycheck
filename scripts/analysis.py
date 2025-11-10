#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 RealityCheck – Global KPI Analysis (Final GPT-Compat, Nov 2025)
─────────────────────────────────────────────
Erzeugt (Schema unverändert):
 • data/analysis.md
 • data/analysis.json
 • data/kpi_analysis.json
 • data/analysis_outliers.json
Kompatibel zu openai v1.54 + (Fun/Safe-Logik).
"""

import os, sys, json, time, math, traceback
from datetime import datetime, timezone, date
from pathlib import Path
from statistics import mean, pstdev
from dotenv import load_dotenv
from openai import OpenAI
from httpx import Client as HttpxClient

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **k): return x

from env_utils import get_openai_key

# === UTF-8 ===
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# === Pfade ===
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.resolve()
DATA_DIR = ROOT_DIR / "data"
META_DIR = DATA_DIR / "meta"
AVAILABLE_FILE = META_DIR / "available_kpis.json"
OUT_MD = DATA_DIR / "analysis.md"
OUT_JSON = DATA_DIR / "analysis.json"
OUT_KPI = DATA_DIR / "kpi_analysis.json"
OUT_OUTLIERS = DATA_DIR / "analysis_outliers.json"
LOG_FILE = DATA_DIR / "fetch_log.txt"

# === OpenAI ===
load_dotenv()
client = OpenAI(api_key=get_openai_key(), http_client=HttpxClient())

# === Logging ===
def log(msg:str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f: f.write(line+"\n")
    except Exception: pass

# === Safe Writes ===
def safe_write_text(p:Path, c:str):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(c or "⚠️ Empty content", encoding="utf-8")
    os.replace(tmp,p)

def safe_write_json(p:Path, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp,p)

# === Loader ===
def load_meta():
    with AVAILABLE_FILE.open(encoding="utf-8") as f:
        meta=json.load(f)
    return list(meta.values()) if isinstance(meta,dict) else meta

def iter_kpi_records(kpi):
    f=DATA_DIR/f"{kpi}.json"
    if not f.exists(): return []
    try: return json.load(f.open(encoding="utf-8"))
    except: return []

def numeric_values(recs):
    for r in recs:
        v=r.get("value")
        if isinstance(v,(int,float)) and not (math.isnan(v) or math.isinf(v)): yield float(v)

# === GPT Helper (Fun/Safe-Style, mit optionalem Silent Mode) ===
VERBOSE = False  # ⬅️ auf True setzen, wenn du Debug-Logs brauchst

def gpt_call(prompt: str, max_tokens: int = 700) -> str:
    """Robuster GPT-Call – mit Fallback und optionalem Silent Mode."""
    text = ""
    last_err = None

    for model in ["gpt-4o", "gpt-4-turbo"]:
        if VERBOSE:
            log(f"➡️ GPT call → {model}")
        try:
            rsp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You analyze global datasets objectively."},
                    {"role": "user", "content": prompt.strip()},
                ],
                max_completion_tokens=max_tokens
            )

            usage = getattr(rsp, "usage", {})
            if VERBOSE:
                log(f"🧮 Tokens: {usage}")

            msg = rsp.choices[0].message
            raw = msg.content  # ✅ new SDK compatible

            if not raw:
                if VERBOSE:
                    log("⚠️ Empty content → next model")
                continue

            text = raw.strip()
            if len(text) > 30:
                if VERBOSE:
                    log(f"✅ {model} OK ({len(text)} chars)")
                return text
            else:
                if VERBOSE:
                    log(f"⚠️ Short response ({len(text)} chars) → retry")
                text = ""

        except Exception as e:
            last_err = e
            if VERBOSE:
                log(f"❌ {model} error: {e}")
            time.sleep(1)

    raise RuntimeError(f"Empty GPT response after retries. Last error: {last_err}")


# === Globale Analyse ===
def run_global_analysis(updated):
    log("➡️ Starting global analysis …")
    try: meta=load_meta()
    except Exception as e:
        log(f"❌ Meta load failed: {e}")
        safe_write_json(OUT_JSON,{"error":str(e)}); return
    allowed={m.get("filename","").replace(".json","") for m in meta}
    targets=sorted(list(allowed if "__force_all__" in updated or not updated else [k for k in updated if k in allowed]))
    summaries=[]
    for kid in targets:
        vals=list(numeric_values(iter_kpi_records(kid)))
        if not vals: continue
        summaries.append(f"• {kid}: mean {round(sum(vals)/len(vals),2)} ({len(vals)} values)")
    if not summaries:
        txt="⚠️ No KPI values found."; safe_write_text(OUT_MD,txt); safe_write_json(OUT_JSON,{"summary":txt}); return
    joined="\n".join(summaries)
    prompt = f"""
You are a senior geopolitical and socio-economic analyst preparing a comprehensive synthesis of global KPI trends.

Your task: write a **structured, insightful, and readable report** (8–10 clearly separated sections) interpreting
cross-domain patterns across economy, environment, society, governance, and technology, based on these aggregated KPIs:

{joined}

**Formatting requirements:**
• Use Markdown with clear section headers (## Economy, ## Environment, ## Society & Governance, ## Technology, ## Regional Insights, ## Outlook, etc.).
• Use short paragraphs (max 5 lines each).
• Add bullet points or numbered lists when summarizing contrasts or correlations.
• Highlight key figures, countries, or anomalies in **bold**.
• Avoid walls of text — readability and structure are essential.

**Analytical focus:**
- Major global progress and regression trends  
- Interconnections between indicators (e.g., GDP ↔ CO₂, democracy ↔ happiness)  
- Contrasts between democracies vs autocracies, and rich vs poor countries  
- Regional differences (Europe, Africa, Asia, Americas)  
- Long-term implications, risks, and opportunities  
- Noteworthy outliers or anomalies  
- A forward-looking outlook (climate, stability, prosperity)

Style: clear, engaging, and accessible English (B2 level).  
Be factual but interpretative, analytical but not technical.
"""

    try:
        text = gpt_call(prompt, 2500)
    except Exception as e:
        text = f"⚠️ GPT request failed: {e}"

    safe_write_text(OUT_MD, text)
    safe_write_json(OUT_JSON, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": text
    })
    log(f"💾 Saved analysis ({len(text)} chars)")


# === KPI Analysen ===
def generate_kpi_analyses(client:OpenAI,data_dir:Path,updated_only=None):
    meta=load_meta()
    if updated_only and "__force_all__" not in updated_only:
        allow={u.replace(".json","") for u in updated_only}
        meta=[m for m in meta if m.get("filename","").replace(".json","") in allow]
        log(f"⚙️ Limiting KPI analysis to {len(meta)} entries.")
    result={}
    for e in tqdm(meta,desc="🧩 KPI summaries"):
        fname=e.get("filename","").replace(".json","")
        if not fname: continue
        title=e.get("title",fname)
        desc=e.get("description","")
        cluster=e.get("cluster","")
        unit=e.get("unit","")
        prompt=f"""
Write a concise (≤900 chars) analysis for '{title}' ({cluster}, unit:{unit}).
Describe what it measures, top/low performers, regional patterns and outlook.
Context: {desc}
"""
        try: summary=gpt_call(prompt,400)
        except Exception as e: summary=f"⚠️ GPT error: {e}"
        result[fname]={"summary":summary,"last_update":str(date.today())}
        time.sleep(0.8)
    existing=json.load(OUT_KPI.open(encoding="utf-8")) if OUT_KPI.exists() else {}
    existing.update(result)
    safe_write_json(OUT_KPI,existing)
    log(f"✅ KPI analyses saved ({len(existing)} total)")

# === Outlier-Berechnung ===
EXCLUDE_AGGREGATES={"World","European Union","Euro area","OECD members",
                     "High income","Upper middle income","Lower middle income","Low income"}

def compute_outliers():
    """Berechnet statistische Ausreißer (Z-Score-basiert), ohne mean/stdev/min/max-Felder."""
    log("🔎 Computing outliers …")
    meta = load_meta()
    out = {}

    for m in tqdm(meta, desc="📈 KPI outliers"):
        kid = m.get("filename", "").replace(".json", "")
        recs = iter_kpi_records(kid)
        if not recs:
            continue

        # Letzter bekannter Wert pro Land (ohne Aggregate)
        latest = {}
        for r in recs:
            c, y, v = r.get("country"), r.get("year"), r.get("value")
            if not c or c in EXCLUDE_AGGREGATES or not isinstance(v, (int, float)):
                continue
            try:
                y = int(float(y))
            except Exception:
                continue
            if c not in latest or y > latest[c][0]:
                latest[c] = (y, float(v))

        if not latest:
            continue

        vals = [v for _, v in latest.values()]
        if len(vals) < 2:
            continue

        mu = mean(vals)
        sigma = pstdev(vals)
        if sigma == 0:
            continue

        zlist = []
        for c, (y, v) in latest.items():
            z = (v - mu) / sigma
            zlist.append({
                "country": c,
                "year": y,
                "value": v,
                "z": round(z, 3)
            })

        highs = sorted([e for e in zlist if e["z"] >= 2], key=lambda x: -x["z"])[:10]
        lows  = sorted([e for e in zlist if e["z"] <= -2], key=lambda x:  x["z"])[:10]

        if highs or lows:
            out[kid] = {"high_outliers": highs, "low_outliers": lows}

    safe_write_json(OUT_OUTLIERS, out)
    log(f"💾 Outliers saved ({len(out)} KPIs, compact format)")


# === Main ===
if __name__=="__main__":
    log("🚀 Running RealityCheck Global Analysis (Final GPT-Compat)")
    state=DATA_DIR/"fetch_state.json"
    updated=[]
    if state.exists():
        try: updated=json.load(state.open(encoding="utf-8")).get("updated_kpis",[])
        except Exception as e: log(f"⚠️ fetch_state read error: {e}")
    if not updated: updated=["__force_all__"]
    try: run_global_analysis(updated)
    except Exception as e: log(f"❌ Global analysis failed: {e}\n{traceback.format_exc()}")
    try: generate_kpi_analyses(client,DATA_DIR,updated_only=None if "__force_all__" in updated else updated)
    except Exception as e: log(f"⚠️ KPI summary failed: {e}")
    try: compute_outliers()
    except Exception as e: log(f"⚠️ Outlier computation failed: {e}")
    log("✅ RealityCheck analysis completed successfully.")
