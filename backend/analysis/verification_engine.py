from typing import Dict, Any, List
import numpy as np
import json
from .llm_service import LLMService

class VerificationEngine:
    """Verifies analysis results and triggers revision if needed with LLM interpretation"""
    
    def __init__(self, session_state: Dict[str, Any], evidence_store, use_llm: bool = True):
        self.session_state = session_state
        self.evidence_store = evidence_store
        self.use_llm = use_llm
        self.llm_service = LLMService() if use_llm else None
        self.verification_results = {}
        
    def verify(self) -> Dict[str, Any]:
        """Perform comprehensive verification of analysis results"""
        self.verification_results = {
            "verified": True,
            "consistency_checks": [],
            "statistical_validations": [],
            "quality_checks": [],
            "execution_checks": [],
            "issues": [],
            "overall_confidence": 0.0
        }
        
        # Perform consistency checks
        self._perform_consistency_checks()
        
        # Perform statistical validations
        self._perform_statistical_validations()
        
        # Perform quality checks
        self._perform_quality_checks()
        
        # Perform execution checks
        self._perform_execution_checks()
        
        # Calculate overall confidence
        self._calculate_confidence()
        
        # Determine if verification passed
        self.verification_results["verified"] = (
            len(self.verification_results["issues"]) == 0 and
            self.verification_results["overall_confidence"] >= 0.7
        )
        
        return self.verification_results
    
    def _perform_consistency_checks(self):
        """Check consistency across different analyses"""
        execution_results = self.session_state.get("execution_results", [])
        
        # Check if calculations are consistent
        for result in execution_results:
            if result.get("status") == "error":
                self.verification_results["issues"].append({
                    "type": "consistency",
                    "message": f"Step {result['step_id']} failed with error: {result.get('error')}"
                })
        
        # Check if groupby results are consistent with totals
        self.verification_results["consistency_checks"].append({
            "check": "calculation_consistency",
            "passed": len([r for r in execution_results if r.get("status") == "error"]) == 0
        })
    
    def _perform_statistical_validations(self):
        """Validate statistical significance of findings with LLM interpretation"""
        hypotheses = self.session_state.get("hypotheses", [])
        execution_results = self.session_state.get("execution_results", [])
        
        for hypothesis in hypotheses:
            # Check if hypothesis has sufficient evidence
            evidence = hypothesis.get("evidence", {})
            
            if not evidence:
                self.verification_results["issues"].append({
                    "type": "statistical",
                    "message": f"Hypothesis {hypothesis['id']} lacks sufficient evidence"
                })
            
            validation_result = {
                "hypothesis_id": hypothesis["id"],
                "has_evidence": bool(evidence),
                "passed": bool(evidence)
            }
            
            # Use LLM to interpret statistical results if available
            if self.use_llm and self.llm_service and self.llm_service.model and execution_results:
                try:
                    prompt = f"""
Interpret the statistical validation for this hypothesis:

HYPOTHESIS: {hypothesis.get('statement')}
EVIDENCE: {json.dumps(evidence, indent=2)}
EXECUTION RESULTS: {json.dumps(execution_results[:3], indent=2)}

Provide:
- confidence_level: High/Medium/Low
- interpretation: Brief interpretation of the evidence
- needs_more_data: Whether more data is needed

Return ONLY valid JSON.
"""
                    response = self.llm_service.model.generate_content(prompt)
                    json_text = response.text.strip()
                    if json_text.startswith("```"):
                        json_text = json_text.replace("```json", "").replace("```", "").strip()
                    
                    interpretation = json.loads(json_text)
                    validation_result.update(interpretation)
                except Exception as e:
                    print(f"LLM statistical interpretation failed: {e}")
            
            self.verification_results["statistical_validations"].append(validation_result)
    
    def _perform_quality_checks(self):
        """Check if data quality issues affect results"""
        dataset_info = self.session_state.get("dataset_info", {})
        quality_report = dataset_info.get("quality_report", {})
        
        # Check for high missing values
        column_status = quality_report.get("column_status", {})
        for col, status in column_status.items():
            if status.get("status") == "poor":
                self.verification_results["issues"].append({
                    "type": "quality",
                    "message": f"Column {col} has data quality issues that may affect results"
                })
        
        self.verification_results["quality_checks"].append({
            "check": "data_quality",
            "passed": len([s for s in column_status.values() if s.get("status") == "poor"]) == 0
        })
    
    def _perform_execution_checks(self):
        """Check if all tools executed successfully"""
        execution_results = self.session_state.get("execution_results", [])
        
        successful_executions = len([r for r in execution_results if r.get("status") == "completed"])
        total_executions = len(execution_results)
        
        if total_executions > 0:
            success_rate = successful_executions / total_executions
            if success_rate < 0.8:
                self.verification_results["issues"].append({
                    "type": "execution",
                    "message": f"Only {success_rate:.1%} of analysis steps completed successfully"
                })
        
        self.verification_results["execution_checks"].append({
            "check": "tool_execution",
            "success_rate": success_rate if total_executions > 0 else 0,
            "passed": success_rate >= 0.8 if total_executions > 0 else False
        })
    
    def _calculate_confidence(self):
        """Calculate overall confidence in the results"""
        # Start with base confidence
        confidence = 1.0
        
        # Reduce confidence for each issue
        for issue in self.verification_results["issues"]:
            if issue["type"] == "consistency":
                confidence -= 0.2
            elif issue["type"] == "statistical":
                confidence -= 0.15
            elif issue["type"] == "quality":
                confidence -= 0.1
            elif issue["type"] == "execution":
                confidence -= 0.15
        
        # Ensure confidence is between 0 and 1
        self.verification_results["overall_confidence"] = max(0.0, min(1.0, confidence))
    
    def revise(self) -> Dict[str, Any]:
        """Revise analysis based on verification failures"""
        revision_results = {
            "revised": False,
            "revisions_made": [],
            "new_session_state": None
        }
        
        # Identify the type of issues
        issue_types = [issue["type"] for issue in self.verification_results["issues"]]
        
        if "quality" in issue_types:
            # Suggest data cleaning
            revision_results["revisions_made"].append({
                "action": "data_cleaning",
                "description": "Clean data by handling missing values and removing duplicates"
            })
        
        if "consistency" in issue_types or "execution" in issue_types:
            # Suggest re-running failed steps
            revision_results["revisions_made"].append({
                "action": "retry_execution",
                "description": "Re-run failed analysis steps"
            })
        
        if "statistical" in issue_types:
            # Suggest additional analysis
            revision_results["revisions_made"].append({
                "action": "additional_analysis",
                "description": "Perform additional statistical tests to strengthen evidence"
            })
        
        revision_results["revised"] = len(revision_results["revisions_made"]) > 0
        
        return revision_results
