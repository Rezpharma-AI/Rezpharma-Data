import os
import urllib.request
import zipfile
import hashlib
from typing import Optional
from fastapi import Depends, Header
from fastapi.responses import FileResponse, StreamingResponse

# --- CLOUD DATABASE BOOTSTRAP ---
DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "rezpharma.db")
DB_URL = os.getenv("DB_DOWNLOAD_URL")

if DB_URL and not os.path.exists(DB_PATH):
    print("⚠️ Database not found. Downloading from cloud storage...")
    os.makedirs(DB_DIR, exist_ok=True)
    zip_path = os.path.join(DB_DIR, "rezpharma.zip")
    urllib.request.urlretrieve(DB_URL, zip_path)
    print("📦 Extracting database...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(DB_DIR)
    os.remove(zip_path)
    print("✅ Database ready.")
# --------------------------------
import sys, os
sys.path.insert(0, '.')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from src.m1_ddi_adr.rule_engine import DDIRuleEngine
from src.blackboard.blackboard import Blackboard, ProvenanceError
from src.advisor.utility import ExpectedUtilityCalculator
from src.advisor.knapsack import AlertBudgetSelector
from src.cdss_core.log_lr import LogLikelihoodRatio

app = FastAPI(title="RezpharmaCDSS Microservices", version="1.0")

# Initialize global state (In a real prod env, this would be in Redis/Postgres)
engine = DDIRuleEngine()
bb = Blackboard(patient_id="EHR_PATIENT_001")

class PatientRegimen(BaseModel):
    patient_id: str
    drugs: List[str]

@app.get("/")
def root():
    return {"status": "online", "service": "RezpharmaCDSS M1 & Advisor Microservice", "db_drugs": 4566, "db_ddis": 2855310}

@app.post("/api/v1/m1/analyze")
# ═══════════════════════════════════════════════════════════
#  SYNC / REPLICATION EXPORT  (token-protected)
#  Lets your own host pull a verified copy of the master DB:
#    GET /api/v1/export/checksum  -> {"sha256":..., "size":...}
#    GET /api/v1/export/snapshot  -> raw rezpharma.db bytes
#                                    (supports Range = resumable)
# ═══════════════════════════════════════════════════════════
SYNC_TOKEN = os.getenv("SYNC_TOKEN", "")
_sha_cache = {"sha": None, "size": None}


def _sync_auth(x_sync_token: str = Header(default="")):
    if not SYNC_TOKEN or x_sync_token != SYNC_TOKEN:
        raise HTTPException(status_code=403, detail="bad sync token")


def _db_meta():
    if _sha_cache["sha"] is None and os.path.exists(DB_PATH):
        h = hashlib.sha256()
        with open(DB_PATH, "rb") as f:
            for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
                h.update(block)
        _sha_cache["sha"] = h.hexdigest()
        _sha_cache["size"] = os.path.getsize(DB_PATH)
    return _sha_cache


@app.get("/api/v1/export/checksum")
def export_checksum(_=Depends(_sync_auth)):
    m = _db_meta()
    if not m["sha"]:
        raise HTTPException(status_code=404, detail="database not ready")
    return {"sha256": m["sha"], "size": m["size"]}


@app.get("/api/v1/export/snapshot")
def export_snapshot(
    _=Depends(_sync_auth),
    range_header: Optional[str] = Header(default=None, alias="Range"),
):
    m = _db_meta()
    if not m["sha"]:
        raise HTTPException(status_code=404, detail="database not ready")
    total = m["size"]

    if range_header:
        try:
            rng = range_header.split("=")[1]
            start_s, end_s = rng.split("-")
            start = int(start_s)
            end = min(int(end_s) if end_s else total - 1, total - 1)
            length = end - start + 1

            def iter_file():
                with open(DB_PATH, "rb") as f:
                    f.seek(start)
                    left = length
                    while left > 0:
                        chunk = f.read(min(1024 * 1024, left))
                        if not chunk:
                            break
                        left -= len(chunk)
                        yield chunk

            return StreamingResponse(
                iter_file(),
                status_code=206,
                media_type="application/octet-stream",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{total}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(length),
                },
            )
        except Exception:
            raise HTTPException(status_code=416, detail="bad range")

    return FileResponse(
        DB_PATH,
        media_type="application/octet-stream",
        filename="rezpharma.db",
        headers={"Accept-Ranges": "bytes", "Content-Length": str(total)},
    )
# ═══════════════════ END SYNC EXPORT ═══════════════════
def analyze_regimen(payload: PatientRegimen):
    """Microservice Endpoint: M1 DDI Check + Blackboard Update"""
    # Reset blackboard for new patient analysis
    global bb
    bb = Blackboard(patient_id=payload.patient_id)
    
    # Query 2.85M Knowledge Base
    interactions = engine.check_interactions(payload.drugs)
    
    # Push to Probabilistic Blackboard
    for hit in interactions:
        lr = engine.to_log_lr(hit)
        harm_id = hit['mechanism'].split(':')[0].strip().lower().replace(' ', '_')[:30]
        try:
            bb.add_harm_evidence(harm_id, lr)
        except ProvenanceError:
            pass
            
    return {
        "patient_id": payload.patient_id,
        "drugs_analyzed": len(payload.drugs),
        "interactions_found": len(interactions),
        "blackboard_harm_propositions": list(bb.harm_log_lrs.keys()),
        "interactions": interactions[:20] # Limit payload size
    }

@app.get("/api/v1/advisor/recommendations")
def get_recommendations():
    """Microservice Endpoint: Advisor Expected Utility + Knapsack"""
    harm_props = list(bb.harm_log_lrs.keys())
    if not harm_props:
        return {"alerts": [], "suppressed": [], "message": "No risks detected on blackboard."}
        
    advisor = ExpectedUtilityCalculator()
    advisor.add_action("hold_or_switch_drug", u_harm=-2, u_noharm=-3)
    advisor.add_action("reduce_dose", u_harm=-5, u_noharm=-1)
    advisor.add_action("increase_monitoring", u_harm=-8, u_noharm=0)
    advisor.add_action("continue_current", u_harm=-30, u_noharm=0)
    
    alerts = []
    for harm in harm_props:
        p_harm = bb.get_posterior_probability(harm, prior_prob=0.05)
        best = advisor.select_best_action(p_harm)
        alerts.append({
            "harm": harm,
            "p_harm": p_harm,
            "action": best["selected"],
            "eu": best["expected_utility"],
            "net_benefit": p_harm * 20,
            "attention_cost": 1
        })
        
    selector = AlertBudgetSelector(budget=3)
    selected = selector.select_alerts(alerts)
    suppressed = [a for a in alerts if a not in selected]
    
    return {
        "patient_id": bb.patient_id,
        "total_risks_evaluated": len(alerts),
        "alerts_selected": selected,
        "alerts_suppressed": suppressed
    }
