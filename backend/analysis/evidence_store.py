from typing import Dict, Any, List
import json
import os
from datetime import datetime

class EvidenceStore:
    """Stores all evidence generated during analysis"""
    
    def __init__(self):
        self.store = {}
        self.storage_path = "evidence_store"
        os.makedirs(self.storage_path, exist_ok=True)
        
    def store_dataset(self, file_id: str, filename: str, profile: Dict[str, Any], quality_report: Dict[str, Any], file_path: str = None):
        """Store dataset information"""
        self.store[file_id] = {
            "file_id": file_id,
            "filename": filename,
            "file_path": file_path,
            "profile": profile,
            "quality_report": quality_report,
            "timestamp": datetime.now().isoformat(),
            "tool_executions": [],
            "visualizations": [],
            "anomalies": [],
            "hypotheses_tested": []
        }
        
        self._persist(file_id)
    
    def store_tool_execution(self, session_id: str, step_id: str, result: Dict[str, Any]):
        """Store tool execution result"""
        # Extract file_id from session if available
        if session_id in self.store:
            self.store[session_id]["tool_executions"].append({
                "step_id": step_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(session_id)
    
    def store_visualization(self, session_id: str, viz_id: str, path: str, description: str):
        """Store visualization information"""
        if session_id in self.store:
            self.store[session_id]["visualizations"].append({
                "viz_id": viz_id,
                "path": path,
                "description": description,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(session_id)
    
    def store_anomaly_detection(self, session_id: str, anomalies: List[Dict[str, Any]]):
        """Store anomaly detection results"""
        if session_id in self.store:
            self.store[session_id]["anomalies"] = anomalies
            self._persist(session_id)
    
    def store_hypothesis_test(self, session_id: str, hypothesis_id: str, test_result: Dict[str, Any]):
        """Store hypothesis test result"""
        if session_id in self.store:
            self.store[session_id]["hypotheses_tested"].append({
                "hypothesis_id": hypothesis_id,
                "test_result": test_result,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(session_id)
    
    def get_dataset(self, file_id: str) -> Dict[str, Any]:
        """Retrieve dataset information"""
        if file_id in self.store:
            return self.store[file_id]
        return {}
    
    def get_evidence(self, session_id: str) -> Dict[str, Any]:
        """Get all evidence for a session"""
        if session_id in self.store:
            return self.store[session_id]
        return {}
    
    def get_tool_executions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all tool executions for a session"""
        if session_id in self.store:
            return self.store[session_id].get("tool_executions", [])
        return []
    
    def get_visualizations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all visualizations for a session"""
        if session_id in self.store:
            return self.store[session_id].get("visualizations", [])
        return []
    
    def _persist(self, session_id: str):
        """Persist evidence to disk"""
        file_path = os.path.join(self.storage_path, f"{session_id}.json")
        with open(file_path, "w") as f:
            json.dump(self.store[session_id], f, indent=2, default=str)
    
    def _load(self, session_id: str):
        """Load evidence from disk"""
        file_path = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                self.store[session_id] = json.load(f)
