from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
import os
import json
import html
import asyncio
from typing import Dict, Any
import uuid

from analysis.dataset_profiler import DatasetProfiler
from analysis.data_quality import DataQualityAnalyzer
from analysis.analysis_planner import AnalysisPlanner
from analysis.hypothesis_engine import HypothesisEngine
from analysis.tool_executor import ToolExecutor
from analysis.verification_engine import VerificationEngine
from analysis.evidence_store import EvidenceStore
from analysis.report_generator import ReportGenerator
from analysis.analysis_memory import AnalysisMemory
from websocket.connection_manager import ConnectionManager

# Initialize analysis memory and evidence store
analysis_memory = AnalysisMemory()
evidence_store = EvidenceStore()
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Autonomous Data Analyst Backend...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Autonomous Data Analyst",
    description="AI-powered autonomous data analysis system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("analysis_results", exist_ok=True)
os.makedirs("exports", exist_ok=True)


def _render_report_html(report: Dict[str, Any]) -> str:
    """Render a stored analysis report into a standalone, self-contained HTML file.

    Charts are embedded as real interactive Plotly figures (loaded from the CDN)
    using the same figure spec the dashboard renders, so the downloaded report is
    a faithful, shareable copy of the on-screen analysis.
    """
    def esc(value: Any) -> str:
        return html.escape("" if value is None else str(value))

    def bullets(items, empty: str = "None") -> str:
        items = [i for i in (items or []) if i not in (None, "")]
        if not items:
            return f'<p class="muted">{esc(empty)}</p>'
        return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

    goal = report.get("goal") or "Not specified"
    overview = report.get("dataset_overview") or {}
    quality = report.get("data_quality") or {}
    confidence = report.get("confidence") or {}
    verification = report.get("verification") or {}

    # Split the goal-specific AI insights from the traceable evidence findings.
    findings = report.get("key_findings") or []
    ai_insights = [f.get("description") for f in findings if f.get("kind") == "insight"]
    for extra in report.get("insights") or []:
        if extra not in ai_insights:
            ai_insights.append(extra)
    evidence_findings = [f.get("description") for f in findings if f.get("kind") != "insight"]

    charts_html, chart_scripts = [], []
    for idx, viz in enumerate(report.get("visualizations") or []):
        figure = viz.get("figure") or {}
        desc = esc(viz.get("description") or f"Chart {idx + 1}")
        if figure.get("data"):
            div_id = f"chart_{idx}"
            charts_html.append(
                f'<figure><figcaption>{desc}</figcaption>'
                f'<div id="{div_id}" class="chart"></div></figure>'
            )
            payload = json.dumps({
                "data": figure.get("data"),
                "layout": figure.get("layout") or {},
            }).replace("</", "<\\/")
            chart_scripts.append(
                f'Plotly.newPlot("{div_id}", {payload}.data, {payload}.layout, '
                f'{{responsive: true, displayModeBar: false}});'
            )
        else:
            charts_html.append(
                f'<figure><figcaption>{desc}</figcaption>'
                f'<p class="muted">Chart file: {esc(viz.get("path"))}</p></figure>'
            )

    hypotheses_html = "".join(
        f'<div class="card sub"><p class="h-id">{esc(h.get("id"))}</p>'
        f'<p>{esc(h.get("statement"))}</p>'
        f'<span class="tag">{esc(h.get("type"))}</span></div>'
        for h in (report.get("hypotheses") or [])
    ) or '<p class="muted">None</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Analysis Report - {esc(overview.get("filename", "Dataset"))}</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
         margin: 0; padding: 32px 16px; background: #f4f6fb; color: #1f2937; line-height: 1.55; }}
  .wrap {{ max-width: 960px; margin: 0 auto; }}
  header {{ background: linear-gradient(135deg, #4f46e5, #9333ea); color: #fff;
            padding: 28px 32px; border-radius: 16px; margin-bottom: 24px; }}
  header h1 {{ margin: 0 0 8px; font-size: 26px; }}
  header p {{ margin: 0; opacity: .9; }}
  .card {{ background: #fff; border-radius: 14px; padding: 22px 26px; margin-bottom: 20px;
           box-shadow: 0 1px 3px rgba(16,24,40,.08); }}
  .card.sub {{ padding: 14px 16px; margin: 10px 0; background: #f8faff; border-left: 4px solid #6366f1; }}
  h2 {{ font-size: 18px; margin: 0 0 14px; color: #312e81; }}
  h3 {{ font-size: 15px; margin: 18px 0 8px; color: #4338ca; }}
  p {{ margin: 0 0 10px; }}
  ul {{ margin: 0; padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
  .muted {{ color: #6b7280; font-size: 14px; }}
  .goal {{ background: #eef2ff; border-left: 4px solid #4f46e5; padding: 12px 16px;
           border-radius: 8px; font-weight: 500; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
  .stat {{ background: #f8faff; border-radius: 10px; padding: 12px 14px; }}
  .stat .k {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: .04em; }}
  .stat .v {{ font-size: 18px; font-weight: 600; color: #111827; }}
  .tag {{ display: inline-block; background: #e0e7ff; color: #3730a3; font-size: 12px;
          padding: 2px 10px; border-radius: 999px; }}
  .h-id {{ font-weight: 700; color: #3730a3; margin: 0 0 4px; }}
  .bar {{ height: 10px; background: #e5e7eb; border-radius: 999px; overflow: hidden; margin: 6px 0 4px; }}
  .bar > span {{ display: block; height: 100%; background: linear-gradient(90deg, #34d399, #059669); }}
  figure {{ margin: 0 0 22px; }}
  figcaption {{ font-weight: 600; color: #374151; margin-bottom: 8px; }}
  .chart {{ width: 100%; height: 380px; }}
  .two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
  footer {{ text-align: center; color: #9ca3af; font-size: 12px; margin-top: 24px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Autonomous Data Analyst &mdash; Final Report</h1>
    <p>{esc(overview.get("filename", "Dataset"))} &middot; generated {esc(report.get("generated_at"))}</p>
  </header>

  <div class="card">
    <h2>Analysis Goal</h2>
    <p class="goal">{esc(goal)}</p>
  </div>

  <div class="card">
    <h2>Executive Summary</h2>
    <p>{esc(report.get("executive_summary"))}</p>
  </div>

  <div class="card">
    <h2>Dataset Overview</h2>
    <div class="grid">
      <div class="stat"><div class="k">Rows</div><div class="v">{esc(overview.get("rows"))}</div></div>
      <div class="stat"><div class="k">Columns</div><div class="v">{esc(overview.get("columns"))}</div></div>
      <div class="stat"><div class="k">Numeric</div><div class="v">{esc(len(overview.get("numeric_columns") or []))}</div></div>
      <div class="stat"><div class="k">Categorical</div><div class="v">{esc(len(overview.get("categorical_columns") or []))}</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Data Quality</h2>
    <p>Overall Score: <strong>{esc(quality.get("overall_score", 0))}%</strong></p>
    <div class="bar"><span style="width:{esc(quality.get("overall_score", 0))}%"></span></div>
  </div>

  <div class="card">
    <h2>Key Findings</h2>
    <h3>AI Insights (goal-specific)</h3>
    {bullets(ai_insights, "No AI insights available")}
    <h3>Evidence-backed Findings</h3>
    {bullets(evidence_findings, "No evidence-backed findings")}
  </div>

  <div class="card">
    <h2>Hypotheses</h2>
    {hypotheses_html}
  </div>

  <div class="card">
    <h2>Visualizations</h2>
    {"".join(charts_html) or '<p class="muted">No visualizations available.</p>'}
  </div>

  <div class="card two">
    <div>
      <h2>Verification</h2>
      <p>Verified: <strong>{esc("Yes" if verification.get("verified") else "No")}</strong></p>
      <p>Confidence: <strong>{esc(round(float(confidence.get("overall_confidence", 0)) * 100))}%</strong>
         ({esc(confidence.get("confidence_level"))})</p>
    </div>
    <div>
      <h2>Limitations</h2>
      {bullets(report.get("limitations"))}
    </div>
  </div>

  <div class="card">
    <h2>Recommendations</h2>
    {bullets(report.get("recommendations"))}
  </div>

  <footer>Generated by Autonomous Data Analyst</footer>
</div>
<script>
{chr(10).join(chart_scripts)}
</script>
</body>
</html>"""


@app.get("/")
async def root():
    return {
        "message": "Autonomous Data Analyst API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a dataset (CSV, Excel) for analysis"""
    try:
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1]
        file_path = f"uploads/{file_id}.{file_extension}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Profiling is CPU-bound; run it off the event loop.
        def _profile_dataset():
            profiler = DatasetProfiler(file_path)
            profile = profiler.profile()
            
            quality_analyzer = DataQualityAnalyzer(profile)
            quality_report = quality_analyzer.analyze()
            
            evidence_store.store_dataset(file_id, file.filename, profile, quality_report, file_path)
            return profile, quality_report
        
        profile, quality_report = await run_in_threadpool(_profile_dataset)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "profile": profile,
            "quality_report": quality_report
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/analyze")
async def start_analysis(request: Dict[str, Any]):
    """Start autonomous analysis with a natural language goal"""
    try:
        file_id = request.get("file_id")
        goal = request.get("goal")
        
        if not file_id or not goal:
            return JSONResponse(
                status_code=400,
                content={"error": "file_id and goal are required"}
            )
        
        # Create analysis session
        session_id = str(uuid.uuid4())
        
        # Initialize analysis memory for this session
        analysis_memory.create_session(session_id, file_id, goal)
        
        # Register session with evidence store (maps session_id -> file_id)
        evidence_store.register_session(session_id, file_id)
        
        # Get dataset profile
        dataset_info = evidence_store.get_dataset(file_id)
        # The planner/hypothesis engine expect the profile fields at top level
        profile = dataset_info.get("profile", dataset_info)
        
        # Planning + hypothesis generation call the LLM (blocking network I/O),
        # so they run in a worker thread to keep the event loop responsive.
        def _build_plan():
            planner = AnalysisPlanner(goal, profile, use_llm=True)
            plan = planner.create_plan()
            hypothesis_engine = HypothesisEngine(goal, plan, profile, use_llm=True)
            return plan, hypothesis_engine.generate_hypotheses()
        
        analysis_plan, hypotheses = await run_in_threadpool(_build_plan)
        
        # Store in memory
        analysis_memory.store_plan(session_id, analysis_plan)
        analysis_memory.store_hypotheses(session_id, hypotheses)
        
        return {
            "session_id": session_id,
            "analysis_plan": analysis_plan,
            "hypotheses": hypotheses
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/execute")
async def execute_analysis(request: Dict[str, Any]):
    """Execute the analysis plan with tool execution"""
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )
        
        # Get analysis state
        session_state = analysis_memory.get_session(session_id)
        dataset_info = evidence_store.get_dataset(session_state["file_id"])
        
        # Execute tools in a worker thread so WebSocket progress updates can be
        # delivered to the dashboard in real time while analysis runs.
        loop = asyncio.get_running_loop()
        tool_executor = ToolExecutor(
            dataset_info, session_state, evidence_store, connection_manager, loop=loop
        )
        execution_results = await run_in_threadpool(tool_executor.execute_all)
        
        # Store results
        analysis_memory.store_execution_results(session_id, execution_results)
        
        return {
            "session_id": session_id,
            "execution_results": execution_results
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/verify")
async def verify_analysis(request: Dict[str, Any]):
    """Verify analysis results and potentially trigger revision"""
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )
        
        # Get analysis state
        session_state = analysis_memory.get_session(session_id)
        
        # Verify results with LLM interpretation
        verification_engine = VerificationEngine(session_state, evidence_store, use_llm=True)
        verification_results = await run_in_threadpool(verification_engine.verify)
        
        # Store verification results
        analysis_memory.store_verification(session_id, verification_results)
        
        # If verification fails, trigger revision
        if not verification_results["verified"]:
            revision_results = await run_in_threadpool(verification_engine.revise)
            analysis_memory.store_revision(session_id, revision_results)
            return {
                "session_id": session_id,
                "verification": verification_results,
                "revision": revision_results,
                "needs_revision": True
            }
        
        return {
            "session_id": session_id,
            "verification": verification_results,
            "needs_revision": False
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/report")
async def generate_report(request: Dict[str, Any]):
    """Generate final analytical report"""
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )
        
        # Get complete analysis state
        session_state = analysis_memory.get_session(session_id)
        
        # Generate report with LLM interpretation
        report_generator = ReportGenerator(session_state, evidence_store, use_llm=True)
        report = await run_in_threadpool(report_generator.generate)
        
        # Store report
        analysis_memory.store_report(session_id, report)
        
        return {
            "session_id": session_id,
            "report": report
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/report/{session_id}/download")
async def download_report(session_id: str, format: str = "html"):
    """Download the generated report as a standalone HTML file (or raw JSON)."""
    session_state = analysis_memory.get_session(session_id)
    report = (session_state or {}).get("final_report")

    if not report:
        return JSONResponse(
            status_code=404,
            content={"error": "Report not found. Generate the report first."}
        )

    short_id = session_id[:8]

    if format == "json":
        return JSONResponse(
            content=report,
            headers={
                "Content-Disposition": f'attachment; filename="analysis_report_{short_id}.json"'
            },
        )

    return HTMLResponse(
        content=_render_report_html(report),
        headers={
            "Content-Disposition": f'attachment; filename="analysis_report_{short_id}.html"'
        },
    )


@app.post("/export")
async def export_data(request: Dict[str, Any]):
    """Export analysis results in various formats (CSV, Excel, JSON)"""
    try:
        session_id = request.get("session_id")
        export_format = request.get("format", "csv")  # csv, excel, json

        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )

        session_state = analysis_memory.get_session(session_id)
        file_id = session_state.get("file_id")
        dataset_info = evidence_store.get_dataset(file_id)

        if not dataset_info:
            return JSONResponse(
                status_code=404,
                content={"error": "Dataset not found"}
            )

        import pandas as pd

        # Load the original dataset
        file_path = dataset_info.get("file_path")
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Create export directory
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)

        export_filename = f"analysis_export_{session_id[:8]}"
        export_path = os.path.join(export_dir, export_filename)

        if export_format == "csv":
            export_path += ".csv"
            df.to_csv(export_path, index=False)
        elif export_format == "excel":
            export_path += ".xlsx"
            df.to_excel(export_path, index=False)
        elif export_format == "json":
            export_path += ".json"
            df.to_json(export_path, orient="records", indent=2)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported format: {export_format}"}
            )

        return {
            "success": True,
            "filename": export_filename,
            "format": export_format,
            "path": export_path
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/compare")
async def compare_dimensions(request: Dict[str, Any]):
    """Compare different dimensions in the dataset"""
    try:
        session_id = request.get("session_id")
        dimensions = request.get("dimensions", [])  # List of column names to compare

        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )

        session_state = analysis_memory.get_session(session_id)
        file_id = session_state.get("file_id")
        dataset_info = evidence_store.get_dataset(file_id)

        if not dataset_info:
            return JSONResponse(
                status_code=404,
                content={"error": "Dataset not found"}
            )

        import pandas as pd

        # Load the dataset
        file_path = dataset_info.get("file_path")
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # If no dimensions specified, use top categorical columns
        if not dimensions:
            dimensions = [col for col in df.select_dtypes(exclude=['number']).columns[:3]]

        # Generate comparison data
        comparison_results = {}

        for dim in dimensions:
            if dim in df.columns:
                # Value counts for this dimension
                value_counts = df[dim].value_counts()
                comparison_results[dim] = {
                    "unique_values": int(df[dim].nunique()),
                    "top_values": [
                        {"value": str(val), "count": int(count)}
                        for val, count in value_counts.head(10).items()
                    ],
                    "null_count": int(df[dim].isnull().sum()),
                    "null_percentage": float((df[dim].isnull().sum() / len(df)) * 100)
                }

        return {
            "session_id": session_id,
            "dimensions": dimensions,
            "comparison": comparison_results
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/filter")
async def filter_data(request: Dict[str, Any]):
    """Filter dataset based on criteria"""
    try:
        session_id = request.get("session_id")
        filters = request.get("filters", {})  # {column: value} or {column: {operator: value}}

        if not session_id:
            return JSONResponse(
                status_code=400,
                content={"error": "session_id is required"}
            )

        session_state = analysis_memory.get_session(session_id)
        file_id = session_state.get("file_id")
        dataset_info = evidence_store.get_dataset(file_id)

        if not dataset_info:
            return JSONResponse(
                status_code=404,
                content={"error": "Dataset not found"}
            )

        import pandas as pd

        # Load the dataset
        file_path = dataset_info.get("file_path")
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Apply filters
        for column, criteria in filters.items():
            if column not in df.columns:
                continue

            if isinstance(criteria, dict):
                # Advanced filtering with operators
                operator = criteria.get("operator", "eq")
                value = criteria.get("value")

                if operator == "eq":
                    df = df[df[column] == value]
                elif operator == "ne":
                    df = df[df[column] != value]
                elif operator == "gt":
                    df = df[df[column] > value]
                elif operator == "lt":
                    df = df[df[column] < value]
                elif operator == "gte":
                    df = df[df[column] >= value]
                elif operator == "lte":
                    df = df[df[column] <= value]
                elif operator == "contains":
                    df = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
                elif operator == "not_contains":
                    df = df[~df[column].astype(str).str.contains(str(value), case=False, na=False)]
            else:
                # Simple equality filter
                df = df[df[column] == criteria]

        return {
            "session_id": session_id,
            "original_rows": len(dataset_info.get("profile", {}).get("column_stats", {})),
            "filtered_rows": len(df),
            "data": df.head(100).to_dict(orient="records")  # Return first 100 rows
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get complete session state"""
    try:
        session_state = analysis_memory.get_session(session_id)
        return session_state
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time analysis updates"""
    await connection_manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process any client messages if needed
            await connection_manager.send_personal_message(
                json.dumps({"status": "received", "message": data}),
                websocket
            )
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
