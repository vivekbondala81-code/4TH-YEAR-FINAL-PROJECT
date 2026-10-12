from typing import Dict, Any, List
from datetime import datetime

class AnalysisMemory:
    """Maintains state and context throughout the analysis process"""
    
    def __init__(self):
        self.sessions = {}
        
    def create_session(self, session_id: str, file_id: str, goal: str):
        """Create a new analysis session"""
        self.sessions[session_id] = {
            "session_id": session_id,
            "file_id": file_id,
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "analysis_plan": None,
            "hypotheses": [],
            "execution_results": [],
            "verification_results": None,
            "revision_results": None,
            "final_report": None,
            "completed_steps": [],
            "pending_steps": []
        }
    
    def store_plan(self, session_id: str, analysis_plan: Dict[str, Any]):
        """Store analysis plan"""
        if session_id in self.sessions:
            self.sessions[session_id]["analysis_plan"] = analysis_plan
            self.sessions[session_id]["status"] = "planned"
            self.sessions[session_id]["completed_steps"].append("analysis_planning")
    
    def store_hypotheses(self, session_id: str, hypotheses: List[Dict[str, Any]]):
        """Store generated hypotheses"""
        if session_id in self.sessions:
            self.sessions[session_id]["hypotheses"] = hypotheses
            self.sessions[session_id]["status"] = "hypotheses_generated"
            self.sessions[session_id]["completed_steps"].append("hypothesis_generation")
    
    def store_execution_results(self, session_id: str, execution_results: List[Dict[str, Any]]):
        """Store tool execution results"""
        if session_id in self.sessions:
            self.sessions[session_id]["execution_results"] = execution_results
            self.sessions[session_id]["status"] = "executed"
            self.sessions[session_id]["completed_steps"].append("tool_execution")
    
    def store_verification(self, session_id: str, verification_results: Dict[str, Any]):
        """Store verification results"""
        if session_id in self.sessions:
            self.sessions[session_id]["verification_results"] = verification_results
            self.sessions[session_id]["completed_steps"].append("verification")
            
            if verification_results.get("verified"):
                self.sessions[session_id]["status"] = "verified"
            else:
                self.sessions[session_id]["status"] = "verification_failed"
    
    def store_revision(self, session_id: str, revision_results: Dict[str, Any]):
        """Store revision results"""
        if session_id in self.sessions:
            self.sessions[session_id]["revision_results"] = revision_results
            self.sessions[session_id]["completed_steps"].append("revision")
            self.sessions[session_id]["status"] = "revised"
    
    def store_report(self, session_id: str, report: Dict[str, Any]):
        """Store final report"""
        if session_id in self.sessions:
            self.sessions[session_id]["final_report"] = report
            self.sessions[session_id]["status"] = "completed"
            self.sessions[session_id]["completed_steps"].append("report_generation")
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get complete session state"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        return {}
    
    def update_status(self, session_id: str, status: str):
        """Update session status"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = status
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Get analysis progress for dashboard"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "session_id": session_id,
                "status": session["status"],
                "completed_steps": session["completed_steps"],
                "total_steps": [
                    "dataset_profiling",
                    "data_quality_analysis",
                    "analysis_planning",
                    "hypothesis_generation",
                    "tool_execution",
                    "verification",
                    "revision",
                    "report_generation"
                ],
                "progress_percentage": len(session["completed_steps"]) / 8 * 100
            }
        return {}
