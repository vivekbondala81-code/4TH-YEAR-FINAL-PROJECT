from typing import Dict, Any, List
from .llm_service import LLMService

class HypothesisEngine:
    """Generates and tests multiple hypotheses for analysis using LLM"""
    
    def __init__(self, goal: str, analysis_plan: Dict[str, Any], dataset_info: Dict[str, Any], use_llm: bool = True):
        self.goal = goal
        self.analysis_plan = analysis_plan
        self.dataset_info = dataset_info
        self.use_llm = use_llm
        self.llm_service = LLMService() if use_llm else None
        self.hypotheses = []
        
    def generate_hypotheses(self) -> List[Dict[str, Any]]:
        """Generate multiple hypotheses to explain the observed patterns using LLM"""
        if self.use_llm and self.llm_service and self.llm_service.model:
            try:
                self.hypotheses = self.llm_service.generate_hypotheses(
                    self.goal, self.analysis_plan, self.dataset_info
                )
                # Validate that the LLM returned meaningful hypotheses
                if self.hypotheses and len(self.hypotheses) > 0:
                    return self.hypotheses
                print("LLM returned empty hypotheses, falling back to rule-based")
            except Exception as e:
                print(f"LLM hypothesis generation failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based generation
        goal_lower = self.goal.lower()
        
        # Get numeric and categorical columns
        numeric_cols = self.dataset_info.get("numeric_columns", [])
        categorical_cols = self.dataset_info.get("categorical_columns", [])
        
        # Generate hypotheses based on goal type
        if "decline" in goal_lower or "decrease" in goal_lower or "drop" in goal_lower:
            self._generate_decline_hypotheses(numeric_cols, categorical_cols)
        elif "increase" in goal_lower or "growth" in goal_lower:
            self._generate_growth_hypotheses(numeric_cols, categorical_cols)
        elif "correlation" in goal_lower or "relationship" in goal_lower:
            self._generate_correlation_hypotheses(numeric_cols)
        else:
            self._generate_general_hypotheses(numeric_cols, categorical_cols)
        
        # Always add data quality hypothesis
        self.hypotheses.append({
            "id": f"H{len(self.hypotheses) + 1}",
            "statement": "Observed patterns are caused by data quality issues or anomalies",
            "type": "data_quality",
            "evidence_required": ["missing_values", "duplicates", "outliers"],
            "test_method": "quality_analysis"
        })
        
        return self.hypotheses
    
    def _generate_decline_hypotheses(self, numeric_cols: List[str], categorical_cols: List[str]):
        """Generate hypotheses for decline analysis"""
        hypothesis_id = 1
        
        # Regional/dimensional decline hypothesis
        if categorical_cols:
            for col in categorical_cols[:2]:  # Top 2 categorical columns
                self.hypotheses.append({
                    "id": f"H{hypothesis_id}",
                    "statement": f"Decline is primarily driven by specific categories in {col}",
                    "type": "dimensional",
                    "dimension": col,
                    "evidence_required": ["group_statistics", "comparison"],
                    "test_method": "groupby_analysis"
                })
                hypothesis_id += 1
        
        # Metric-specific decline hypothesis
        if numeric_cols:
            for col in numeric_cols[:2]:  # Top 2 numeric columns
                self.hypotheses.append({
                    "id": f"H{hypothesis_id}",
                    "statement": f"Decline is concentrated in {col} metric",
                    "type": "metric",
                    "metric": col,
                    "evidence_required": ["trend_analysis", "distribution"],
                    "test_method": "time_series_analysis"
                })
                hypothesis_id += 1
        
        # Interaction hypothesis
        if len(categorical_cols) >= 2:
            self.hypotheses.append({
                "id": f"H{hypothesis_id}",
                "statement": f"Decline is caused by interaction between {categorical_cols[0]} and {categorical_cols[1]}",
                "type": "interaction",
                "dimensions": categorical_cols[:2],
                "evidence_required": ["interaction_analysis", "segment_comparison"],
                "test_method": "multivariate_analysis"
            })
            hypothesis_id += 1
    
    def _generate_growth_hypotheses(self, numeric_cols: List[str], categorical_cols: List[str]):
        """Generate hypotheses for growth analysis"""
        hypothesis_id = 1
        
        # Regional/dimensional growth hypothesis
        if categorical_cols:
            for col in categorical_cols[:2]:
                self.hypotheses.append({
                    "id": f"H{hypothesis_id}",
                    "statement": f"Growth is primarily driven by specific categories in {col}",
                    "type": "dimensional",
                    "dimension": col,
                    "evidence_required": ["group_statistics", "comparison"],
                    "test_method": "groupby_analysis"
                })
                hypothesis_id += 1
        
        # Metric-specific growth hypothesis
        if numeric_cols:
            for col in numeric_cols[:2]:
                self.hypotheses.append({
                    "id": f"H{hypothesis_id}",
                    "statement": f"Growth is concentrated in {col} metric",
                    "type": "metric",
                    "metric": col,
                    "evidence_required": ["trend_analysis", "distribution"],
                    "test_method": "time_series_analysis"
                })
                hypothesis_id += 1
    
    def _generate_correlation_hypotheses(self, numeric_cols: List[str]):
        """Generate hypotheses for correlation analysis"""
        hypothesis_id = 1
        
        if len(numeric_cols) >= 2:
            for i in range(min(3, len(numeric_cols))):
                for j in range(i + 1, min(i + 3, len(numeric_cols))):
                    self.hypotheses.append({
                        "id": f"H{hypothesis_id}",
                        "statement": f"There is a significant relationship between {numeric_cols[i]} and {numeric_cols[j]}",
                        "type": "correlation",
                        "variables": [numeric_cols[i], numeric_cols[j]],
                        "evidence_required": ["correlation_coefficient", "statistical_test"],
                        "test_method": "correlation_analysis"
                    })
                    hypothesis_id += 1
    
    def _generate_general_hypotheses(self, numeric_cols: List[str], categorical_cols: List[str]):
        """Generate general exploration hypotheses"""
        hypothesis_id = 1
        
        # Distribution hypothesis
        if numeric_cols:
            self.hypotheses.append({
                "id": f"H{hypothesis_id}",
                "statement": "Numeric variables follow normal distribution",
                "type": "distribution",
                "variables": numeric_cols,
                "evidence_required": ["distribution_test", "histogram"],
                "test_method": "normality_test"
            })
            hypothesis_id += 1
        
        # Categorical hypothesis
        if categorical_cols:
            self.hypotheses.append({
                "id": f"H{hypothesis_id}",
                "statement": "Categorical variables have uneven distribution",
                "type": "categorical",
                "variables": categorical_cols,
                "evidence_required": ["frequency_distribution", "chi_square"],
                "test_method": "chi_square_test"
            })
            hypothesis_id += 1
