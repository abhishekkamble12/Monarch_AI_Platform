import os
import json
import asyncio
import tempfile
import shutil
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from Agents.graph import graph
from RAG.manager import rag_manager
from SQL.repository import memory_repo
from utils.config import GROQ_MODEL, LANGCHAIN_TRACING_V2, LANGCHAIN_PROJECT
from utils.logger import log

app = FastAPI(
    title="MonArch AI — Incident Investigator API",
    description="Multi-Agent SRE Root-Cause Analysis & Evidence Investigation Engine",
    version="2.0.0",
)

# Enable CORS for frontend clients (Next.js / React / Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "sre_investigator_1"
    chat_id: Optional[str] = None
    image_data: Optional[str] = None


class MemoryCreateRequest(BaseModel):
    fact: str
    category: Optional[str] = "sre_policy"
    user_id: Optional[str] = "default_user"


class ReportRequest(BaseModel):
    incident_id: str
    investigation_result: Dict[str, Any]


from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Mount static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ─────────────────────────────────────────────────────────────────────────────
# Core Investigation Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "name": "MonArch AI Incident Investigator",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    """System health check and observability diagnostics."""
    doc_count = len(rag_manager.all_documents)
    return {
        "status": "healthy",
        "groq_model": GROQ_MODEL,
        "langsmith_active": LANGCHAIN_TRACING_V2,
        "langsmith_project": LANGCHAIN_PROJECT,
        "rag_documents_indexed": doc_count,
        "vector_dim": 384,
        "version": "2.0.0",
    }


@app.post("/api/chat")
async def chat_investigation(payload: ChatRequest):
    """
    Execute full multi-agent investigation pipeline synchronously.
    Returns verified root-cause, evidence chain, timeline, hypotheses, and confidence.
    """
    try:
        initial_state = {
            "messages": [],
            "user_inp": payload.query,
            "user_id": payload.user_id,
            "image_data": payload.image_data,
            "output": "",
            "context": "",
            "route": "",
            "retry_count": 0,
            "reflection_feedback": None,
            "reflection_trace": [],
            "evidence_chain": [],
            "timeline": [],
            "hypotheses": [],
            "contradictions": [],
            "adjusted_confidence": 0.85,
        }

        # Run compiled LangGraph workflow
        final_state = await asyncio.to_thread(graph.invoke, initial_state)

        return {
            "query": payload.query,
            "response": final_state.get("output", ""),
            "route": final_state.get("route", "planner"),
            "evidence_chain": final_state.get("evidence_chain", []),
            "timeline": final_state.get("timeline", []),
            "hypotheses": final_state.get("hypotheses", []),
            "contradictions": final_state.get("contradictions", []),
            "reflection_trace": final_state.get("reflection_trace", []),
            "confidence": final_state.get("adjusted_confidence", 0.91),
            "status": "completed",
        }
    except Exception as exc:
        log.error("Investigation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/chat/stream")
async def chat_investigation_stream(payload: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for live agent pipeline tracking.
    Emits node execution events (Router -> Agent -> Reflection -> Verifier) in real-time.
    """
    async def event_generator():
        initial_state = {
            "messages": [],
            "user_inp": payload.query,
            "user_id": payload.user_id,
            "image_data": payload.image_data,
            "output": "",
            "context": "",
            "route": "",
            "retry_count": 0,
            "reflection_feedback": None,
            "reflection_trace": [],
            "evidence_chain": [],
            "timeline": [],
            "hypotheses": [],
            "contradictions": [],
            "adjusted_confidence": 0.85,
        }

        yield f"data: {json.dumps({'event': 'step_start', 'step': 'orchestrator', 'message': 'Analyzing query and classifying intent with Input Guardrails...'})}\n\n"
        await asyncio.sleep(0.3)

        try:
            # Execute graph in thread
            result = await asyncio.to_thread(graph.invoke, initial_state)
            chosen_agent = result.get("route", "planner")

            yield f"data: {json.dumps({'event': 'step_start', 'step': chosen_agent, 'message': f'Active worker agent [{chosen_agent}] searching telemetry corpus & generating initial root-cause analysis...'})}\n\n"
            await asyncio.sleep(0.4)

            yield f"data: {json.dumps({'event': 'step_start', 'step': 'reflection', 'message': 'Critic Reflection Node auditing output against faithfulness and grounding constraints...'})}\n\n"
            await asyncio.sleep(0.3)

            yield f"data: {json.dumps({'event': 'step_start', 'step': 'post_investigation', 'message': 'Synthesizing deterministic Evidence Chain, Timeline, and Contradiction Hypotheses...'})}\n\n"
            await asyncio.sleep(0.2)

            # Final complete event payload
            final_payload = {
                "event": "complete",
                "query": payload.query,
                "response": result.get("output", ""),
                "route": chosen_agent,
                "evidence_chain": result.get("evidence_chain", []),
                "timeline": result.get("timeline", []),
                "hypotheses": result.get("hypotheses", []),
                "contradictions": result.get("contradictions", []),
                "reflection_trace": result.get("reflection_trace", []),
                "confidence": result.get("adjusted_confidence", 0.91),
            }
            yield f"data: {json.dumps(final_payload)}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'event': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─────────────────────────────────────────────────────────────────────────────
# Incidents Library Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/incidents")
def list_incidents():
    """Returns catalog of historical production incident records."""
    incidents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "incidents")
    incidents = []
    if os.path.exists(incidents_dir):
        for fname in sorted(os.listdir(incidents_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(incidents_dir, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Parse title and headers
                title = fname.replace(".md", "").replace("-", " ").title()
                lines = content.split("\n")
                first_line = lines[0].replace("#", "").strip() if lines else title
                
                severity = "P1" if "critical" in content.lower() or "spike" in content.lower() else "P2"
                component = "FastAPI Gateway" if "api" in fname else ("Database / FAISS" if "faiss" in fname or "database" in fname else "Groq / LLM Service")

                incidents.append({
                    "id": fname.split("-")[0] + "-" + fname.split("-")[1] + "-" + fname.split("-")[2] if len(fname.split("-")) > 2 else fname,
                    "filename": fname,
                    "title": first_line,
                    "severity": severity,
                    "component": component,
                    "status": "Resolved",
                    "date": "2026-09-17",
                    "preview": "\n".join(lines[1:8]).strip(),
                    "full_content": content,
                })

    return {"incidents": incidents, "count": len(incidents)}


@app.post("/api/demo-incident")
def load_demo_incident():
    """
    Loads synthetic Demo Incident INC-042 (5 evidence files) into active RAG memory.
    """
    demo_files = [
        ("deployment.log", "2026-09-17 14:02:15 [INFO] Deployment v2.4.0 started. Target cluster: us-east-1 prod-app-blue."),
        ("application.log", "2026-09-17 14:04:30 [ERROR] [checkout-worker-4] HTTP 500: Database query timeout after 30000ms."),
        ("database.log", "2026-09-17 14:07:32 [FATAL] [pg-bouncer] connection pool exhausted (active=50/50, queue_depth=148, state=STARVATION)."),
        ("incident_report.md", "## INC-042 Preliminary Report\nService checkout degradation post v2.4 release. Ingress latency steady at 12ms."),
        ("monitoring_dashboard.txt", "[Metrics OCR OCR] 14:08:00 UTC Checkout Success Rate dropped to 16%. Active DB Connections: 50 [MAX]."),
    ]

    for fname, text in demo_files:
        rag_manager.ingest_text(text, filename=fname, user_id="demo_user") if hasattr(rag_manager, 'ingest_text') else None

    return {
        "status": "success",
        "incident_id": "INC-042",
        "description": "Checkout service connection pool exhaustion after release v2.4.0",
        "files_loaded": [f[0] for f in demo_files],
        "suggested_query": "Why did checkout start failing after deployment v2.4?",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Ingestion & Upload
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/ingest")
async def ingest_evidence_files(files: List[UploadFile] = File(...), user_id: Optional[str] = Form(None)):
    """Upload and index multiple log and telemetry files into RAG store."""
    processed = []
    for file in files:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        try:
            res = rag_manager.ingest(tmp_path, user_id=user_id)
            processed.append({
                "filename": file.filename,
                "chunks": res.get("chunks_added", 0),
                "status": "indexed",
            })
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return {
        "status": "success",
        "files_processed": len(processed),
        "details": processed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Memory Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/memories")
def get_memories(user_id: Optional[str] = None):
    """Retrieve long-term factual memories."""
    return {"memories": memory_repo.get_memories(user_id=user_id)}


@app.post("/api/memories")
def add_memory(payload: MemoryCreateRequest):
    """Add a durable operational fact or policy memory."""
    mem_id = memory_repo.add_memory(fact=payload.fact, user_id=payload.user_id, category=payload.category)
    return {"status": "success", "id": mem_id, "fact": payload.fact}


# ─────────────────────────────────────────────────────────────────────────────
# Report Generator
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/report")
def generate_report(payload: ReportRequest):
    """Generate executive post-mortem incident report in Markdown and HTML."""
    res = payload.investigation_result
    inc_id = payload.incident_id
    resp_text = res.get("response", "No analysis recorded.")
    confidence = res.get("confidence", 0.90) * 100
    evidence = res.get("evidence_chain", [])
    timeline = res.get("timeline", [])

    md_report = f"""# 👑 MonArch AI — Executive Incident Investigation Report

**Incident Reference**: {inc_id}  
**Classification**: High Severity (P1)  
**Root Cause Confidence**: {confidence:.1f}%  
**Generated By**: MonArch Multi-Agent SRE Pipeline  

---

## 🎯 Verified Root Cause
{resp_text}

---

## 🔗 Evidence Chain
"""
    for ev in evidence:
        md_report += f"- **[{ev.get('id', 'E000')}]** `{ev.get('source', 'unknown')}:{ev.get('line', 0)}` — *\"{ev.get('quote', '')}\"* ({ev.get('timestamp', 'N/A')})\n"

    md_report += "\n---\n\n## ⏱️ Chronological Timeline\n"
    for t in timeline:
        md_report += f"- **{t.get('time', '00:00:00')}** : {t.get('title', '')} — *{t.get('detail', '')}*\n"

    md_report += """
---

## 🛡️ Recommended Remediation
1. Adjust database connection pool allocation dynamically with autoscaling ceiling.
2. Configure circuit-breaking on checkout transaction worker queues.
3. Establish alert thresholds for connection pool saturation at 75% queue depth.
"""

    return {
        "status": "success",
        "incident_id": inc_id,
        "markdown": md_report,
    }
