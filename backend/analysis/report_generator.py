from typing import Dict, Any, List
from datetime import datetime
from .llm_service import LLMService

class ReportGenerator:
    """Generates the final analytical report with LLM interpretation"""
    
    def __init__(self, session_state: Dict[str, Any], evidence_store, use_llm: bool = True):
        self.session_state = session_state
        self.evidence_store = evidence_store
        self.use_llm = use_llm
        self.llm_service = LLMService() if use_llm else None
        self.llm_insights = None
        self.report = {}
        
    def generate(self) -> Dict[str, Any]:
        """Generate comprehensive analytical report"""
        session_id = self.session_state["session_id"]
        
        self.report = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "goal": self.session_state.get("goal", ""),
            "executive_summary": self._generate_executive_summary(),
            "dataset_overview": self._generate_dataset_overview(),
            "data_quality": self._generate_data_quality_section(),
            "analysis_plan": self.session_state.get("analysis_plan"),
            "hypotheses": self._generate_hypotheses_section(),
            "key_findings": self._generate_key_findings(),
            "insights": (self.llm_insights or {}).get("insights", []),
            "visualizations": self._generate_visualizations_section(),
            "evidence": self._generate_evidence_section(),
            "verification": self._generate_verification_section(),
            "limitations": self._generate_limitations(),
            "confidence": self._generate_confidence_section(),
            "recommendations": self._generate_recommendations()
        }
        
        return self.report
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary"""
        goal = self.session_state.get("goal", "")
        status = self.session_state.get("status", "unknown")
        
        summary = f"This analysis investigated: {goal}\n\n"
        
        # Check if this was a general question
        execution_results = self.session_state.get("execution_results", [])
        general_answer = None
        for result in execution_results:
            if result.get("status") == "completed" and result.get("result", {}).get("type") == "general_insight":
                general_answer = result.get("result", {}).get("answer")
                break
        
        if general_answer:
            summary += f"Direct Answer:\n{general_answer}\n\n"
            summary += "Additionally, the dataset was analyzed to provide context for this question."
        elif status == "completed":
            summary += "The analysis was completed successfully. Key findings are presented below."
        elif status == "verification_failed":
            summary += "The analysis was completed but verification identified some issues. Please review the verification section."
        else:
            summary += f"The analysis status is: {status}"
        
        return summary
    
    def _generate_dataset_overview(self) -> Dict[str, Any]:
        """Generate dataset overview section"""
        # Get dataset info from evidence store
        file_id = self.session_state.get("file_id")
        dataset_info = self.evidence_store.get_dataset(file_id)
        
        if dataset_info:
            profile = dataset_info.get("profile", {})
            return {
                "filename": dataset_info.get("filename", "Unknown"),
                "rows": profile.get("rows", 0),
                "columns": profile.get("columns", 0),
                "column_names": profile.get("column_names", []),
                "numeric_columns": profile.get("numeric_columns", []),
                "categorical_columns": profile.get("categorical_columns", [])
            }
        
        return {"error": "Dataset information not available"}
    
    def _generate_data_quality_section(self) -> Dict[str, Any]:
        """Generate data quality section"""
        file_id = self.session_state.get("file_id")
        dataset_info = self.evidence_store.get_dataset(file_id)
        
        if dataset_info:
            quality_report = dataset_info.get("quality_report", {})
            return quality_report
        
        return {"error": "Quality report not available"}
    
    def _generate_hypotheses_section(self) -> List[Dict[str, Any]]:
        """Generate hypotheses section with results"""
        hypotheses = self.session_state.get("hypotheses", [])
        
        # In a real implementation, this would include test results
        for hypothesis in hypotheses:
            hypothesis["status"] = "pending"  # Would be updated based on actual tests
            hypothesis["evidence_strength"] = "unknown"
        
        return hypotheses
    
    def _generate_key_findings(self) -> List[Dict[str, Any]]:
        """Generate key findings, leading with the goal-specific AI insights."""
        execution_results = self.session_state.get("execution_results", [])
        findings = []

        # First, check if there's a general question answer and make it prominent
        general_answer = None
        for result in execution_results:
            if result.get("status") == "completed" and result.get("result", {}).get("type") == "general_insight":
                general_answer = result.get("result", {}).get("answer")
                if general_answer:
                    findings.append({
                        "source": "General Question Answer",
                        "kind": "general_answer",
                        "description": general_answer,
                        "result": None
                    })
                    break  # Only add the first general answer

        # Ask the LLM for additional insights
        if self.use_llm and self.llm_service:
            try:
                goal = self.session_state.get("goal", "")
                interpretation = self.llm_service.interpret_results(execution_results, goal)
                self.llm_insights = interpretation

                for insight in interpretation.get("key_findings", []):
                    findings.append({
                        "source": "AI Insight",
                        "kind": "insight",
                        "description": insight,
                        "result": None
                    })
            except Exception as e:
                print(f"LLM interpretation failed: {e}")
                self.llm_insights = None

        # Then the traceable evidence-backed findings (skip if we already have general answer)
        for result in execution_results:
            if result.get("status") == "completed":
                # Skip the general query step since we already added it
                if result.get("result", {}).get("type") == "general_insight":
                    continue
                findings.append({
                    "source": result.get("step_id"),
                    "kind": "evidence",
                    "description": result.get("description"),
                    "result": result.get("result")
                })

        return findings
    
    def _generate_visualizations_section(self) -> List[Dict[str, Any]]:
        """Generate visualizations section"""
        session_id = self.session_state["session_id"]
        visualizations = self.evidence_store.get_visualizations(session_id)
        
        return visualizations
    
    def _generate_evidence_section(self) -> Dict[str, Any]:
        """Generate evidence traceability section"""
        session_id = self.session_state["session_id"]
        tool_executions = self.evidence_store.get_tool_executions(session_id)
        
        return {
            "total_tool_executions": len(tool_executions),
            "executions": tool_executions
        }
    
    def _generate_verification_section(self) -> Dict[str, Any]:
        """Generate verification section"""
        verification_results = self.session_state.get("verification_results", {})
        
        return verification_results
    
    def _generate_limitations(self) -> List[str]:
        """Generate limitations section"""
        limitations = []
        
        # Check for data quality issues
        file_id = self.session_state.get("file_id")
        dataset_info = self.evidence_store.get_dataset(file_id)
        
        if dataset_info:
            quality_report = dataset_info.get("quality_report", {})
            if quality_report.get("overall_score", 100) < 80:
                limitations.append("Data quality issues may affect the reliability of some findings")
        
        # Check verification issues
        verification_results = self.session_state.get("verification_results", {})
        if verification_results.get("overall_confidence", 1.0) < 0.8:
            limitations.append("Confidence in findings is moderate due to verification issues")
        
        # General limitations
        limitations.append("Correlation does not imply causation")
        limitations.append("Findings are based on the provided dataset and may not generalize")
        
        return limitations
    
    def _generate_confidence_section(self) -> Dict[str, Any]:
        """Generate confidence section"""
        verification_results = self.session_state.get("verification_results", {})
        
        confidence = verification_results.get("overall_confidence", 0.0)
        
        if confidence >= 0.8:
            level = "High"
        elif confidence >= 0.6:
            level = "Moderate"
        else:
            level = "Low"
        
        return {
            "overall_confidence": confidence,
            "confidence_level": level,
            "verified": verification_results.get("verified", False)
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on findings with LLM insights"""
        recommendations = []
        
        # Use LLM recommendations if available
        if self.use_llm and self.llm_insights and self.llm_insights.get("recommendations"):
            recommendations.extend(self.llm_insights["recommendations"])
        
        # Generate recommendations based on verification
        verification_results = self.session_state.get("verification_results", {})
        if not verification_results.get("verified", True):
            recommendations.append("Review and address verification issues before acting on findings")
        
        # Generate recommendations based on data quality
        file_id = self.session_state.get("file_id")
        dataset_info = self.evidence_store.get_dataset(file_id)
        
        if dataset_info:
            quality_report = dataset_info.get("quality_report", {})
            for rec in quality_report.get("recommendations", []):
                if rec not in recommendations:
                    recommendations.append(rec)
        
        if not recommendations:
            recommendations.append("Proceed with findings based on the analysis results")
        
        return recommendations
