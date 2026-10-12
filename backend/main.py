from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import json
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
        
        # Profile the dataset
        profiler = DatasetProfiler(file_path)
        profile = profiler.profile()
        
        # Analyze data quality
        quality_analyzer = DataQualityAnalyzer(profile)
        quality_report = quality_analyzer.analyze()
        
        # Store in evidence store
        evidence_store.store_dataset(file_id, file.filename, profile, quality_report, file_path)
        
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
        
        # Get dataset profile
        dataset_info = evidence_store.get_dataset(file_id)
        
        # Create analysis plan
        planner = AnalysisPlanner(goal, dataset_info)
        analysis_plan = planner.create_plan()
        
        # Generate hypotheses
        hypothesis_engine = HypothesisEngine(goal, analysis_plan, dataset_info)
        hypotheses = hypothesis_engine.generate_hypotheses()
        
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
        
        # Execute tools
        tool_executor = ToolExecutor(dataset_info, session_state, evidence_store)
        execution_results = tool_executor.execute_all()
        
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
        
        # Verify results
        verification_engine = VerificationEngine(session_state, evidence_store)
        verification_results = verification_engine.verify()
        
        # Store verification results
        analysis_memory.store_verification(session_id, verification_results)
        
        # If verification fails, trigger revision
        if not verification_results["verified"]:
            revision_results = verification_engine.revise()
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
        
        # Generate report
        report_generator = ReportGenerator(session_state, evidence_store)
        report = report_generator.generate()
        
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
