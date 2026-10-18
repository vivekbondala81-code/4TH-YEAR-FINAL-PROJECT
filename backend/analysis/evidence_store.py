from typing import Dict, Any, List
import json
import os
from datetime import datetime

class EvidenceStore:
    """Stores all evidence generated during analysis"""
    
    def __init__(self):
        self.store = {}
        self.session_to_file = {}
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
    
    def register_session(self, session_id: str, file_id: str):
        """Register a session_id mapped to a file_id so evidence can be stored by session."""
        self.session_to_file[session_id] = file_id
        # Ensure the file entry exists (copy reference if needed)
        if file_id not in self.store:
            self.store[file_id] = {
                "file_id": file_id,
                "tool_executions": [],
                "visualizations": [],
                "anomalies": [],
                "hypotheses_tested": []
            }
        # Also keep a session-level entry pointing at the same data for direct lookup
        self.store[session_id] = self.store[file_id]
    
    def _resolve_key(self, session_id: str) -> str:
        """Resolve a session_id to its underlying storage key (file_id)."""
        return self.session_to_file.get(session_id, session_id)
    
    def store_tool_execution(self, session_id: str, step_id: str, result: Dict[str, Any]):
        """Store tool execution result"""
        key = self._resolve_key(session_id)
        if key in self.store:
            self.store[key]["tool_executions"].append({
                "step_id": step_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(key)
    
    def store_visualization(self, session_id: str, viz_id: str, path: str, description: str, figure: Dict[str, Any] = None):
        """Store visualization information including its interactive figure spec"""
        key = self._resolve_key(session_id)
        if key in self.store:
            self.store[key]["visualizations"].append({
                "viz_id": viz_id,
                "path": path,
                "description": description,
                "figure": figure,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(key)
    
    def store_anomaly_detection(self, session_id: str, anomalies: List[Dict[str, Any]]):
        """Store anomaly detection results"""
        key = self._resolve_key(session_id)
        if key in self.store:
            self.store[key]["anomalies"] = anomalies
            self._persist(key)
    
    def store_hypothesis_test(self, session_id: str, hypothesis_id: str, test_result: Dict[str, Any]):
        """Store hypothesis test result"""
        key = self._resolve_key(session_id)
        if key in self.store:
            self.store[key]["hypotheses_tested"].append({
                "hypothesis_id": hypothesis_id,
                "test_result": test_result,
                "timestamp": datetime.now().isoformat()
            })
            self._persist(key)
    
    def get_dataset(self, file_id: str) -> Dict[str, Any]:
        """Retrieve dataset information"""
        key = self._resolve_key(file_id)
        if key in self.store:
            return self.store[key]
        return {}
    
    def get_evidence(self, session_id: str) -> Dict[str, Any]:
        """Get all evidence for a session"""
        key = self._resolve_key(session_id)
        if key in self.store:
            return self.store[key]
        return {}
    
    def get_tool_executions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all tool executions for a session"""
        key = self._resolve_key(session_id)
        if key in self.store:
            return self.store[key].get("tool_executions", [])
        return []
    
    def get_visualizations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all visualizations for a session"""
        key = self._resolve_key(session_id)
        if key in self.store:
            return self.store[key].get("visualizations", [])
        return []
    
    def _persist(self, key: str):
        """Persist evidence to disk"""
        file_path = os.path.join(self.storage_path, f"{key}.json")
        with open(file_path, "w") as f:
            json.dump(self.store[key], f, indent=2, default=str)
    
    def _load(self, session_id: str):
        """Load evidence from disk"""
        file_path = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                self.store[session_id] = json.load(f)
