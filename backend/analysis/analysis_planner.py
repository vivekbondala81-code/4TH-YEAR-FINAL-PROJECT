from typing import Dict, Any, List
import re
from .llm_service import LLMService

class AnalysisPlanner:
    """Creates structured analysis plans from natural language goals using LLM"""
    
    def __init__(self, goal: str, dataset_info: Dict[str, Any], use_llm: bool = True):
        self.goal = goal
        self.dataset_info = dataset_info
        self.use_llm = use_llm
        self.llm_service = LLMService() if use_llm else None
        self.plan = {}
        
    def create_plan(self) -> Dict[str, Any]:
        """Generate detailed analysis plan using LLM or rule-based approach"""
        if self.use_llm and self.llm_service and self.llm_service.model:
            try:
                self.plan = self.llm_service.generate_analysis_plan(self.goal, self.dataset_info)
                # Validate that the LLM returned a meaningful plan
                if self.plan and self.plan.get("steps") and len(self.plan["steps"]) > 0:
                    return self.plan
                print("LLM returned empty plan, falling back to rule-based")
            except Exception as e:
                print(f"LLM planning failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based planning (comprehensive)
        self.plan = {
            "main_goal": self.goal,
            "questions": [],
            "steps": [],
            "verification_tasks": []
        }
        
        # Extract key entities from goal
        entities = self._extract_entities()
        
        # Generate questions based on goal type
        self._generate_questions(entities)
        
        # Generate execution steps
        self._generate_steps(entities)
        
        # Generate verification tasks
        self._generate_verification_tasks()
        
        return self.plan
    
    def _extract_entities(self) -> Dict[str, List[str]]:
        """Extract relevant entities from the goal and dataset"""
        entities = {
            "metrics": [],
            "dimensions": [],
            "time_periods": [],
            "comparisons": []
        }
        
        goal_lower = self.goal.lower()
        
        # Look for common analytical keywords
        metric_keywords = ["sales", "revenue", "profit", "quantity", "growth", "decline", "increase"]
        dimension_keywords = ["region", "product", "category", "customer", "segment"]
        time_keywords = ["month", "year", "quarter", "period", "time"]
        
        # Extract from dataset columns
        for col in self.dataset_info["column_names"]:
            col_lower = col.lower()
            for keyword in metric_keywords:
                if keyword in col_lower:
                    entities["metrics"].append(col)
            for keyword in dimension_keywords:
                if keyword in col_lower:
                    entities["dimensions"].append(col)
            for keyword in time_keywords:
                if keyword in col_lower:
                    entities["time_periods"].append(col)
        
        # Extract from goal text
        for keyword in metric_keywords:
            if keyword in goal_lower:
                if keyword not in entities["metrics"]:
                    entities["metrics"].append(keyword)
        
        for keyword in dimension_keywords:
            if keyword in goal_lower:
                if keyword not in entities["dimensions"]:
                    entities["dimensions"].append(keyword)
        
        return entities
    
    def _generate_questions(self, entities: Dict[str, List[str]]):
        """Generate specific questions to answer the goal"""
        goal_lower = self.goal.lower()
        
        # Base questions for analysis
        if "decline" in goal_lower or "decrease" in goal_lower or "drop" in goal_lower:
            self.plan["questions"].append({
                "id": "q1",
                "question": "Which dimensions show the most significant decline?",
                "focus": entities["dimensions"] if entities["dimensions"] else ["all dimensions"]
            })
            self.plan["questions"].append({
                "id": "q2",
                "question": "What is the magnitude of the decline over time?",
                "focus": entities["time_periods"] if entities["time_periods"] else ["time"]
            })
            self.plan["questions"].append({
                "id": "q3",
                "question": "Which specific metrics are most affected?",
                "focus": entities["metrics"] if entities["metrics"] else ["all metrics"]
            })
        
        if "increase" in goal_lower or "growth" in goal_lower:
            self.plan["questions"].append({
                "id": "q1",
                "question": "Which dimensions show the most growth?",
                "focus": entities["dimensions"] if entities["dimensions"] else ["all dimensions"]
            })
        
        if "correlation" in goal_lower or "relationship" in goal_lower:
            self.plan["questions"].append({
                "id": "q1",
                "question": "What are the relationships between variables?",
                "focus": entities["metrics"] if entities["metrics"] else ["all numeric columns"]
            })
        
        # Default questions if no specific pattern detected
        if not self.plan["questions"]:
            self.plan["questions"].append({
                "id": "q1",
                "question": "What are the overall patterns in the data?",
                "focus": ["all columns"]
            })
            self.plan["questions"].append({
                "id": "q2",
                "question": "Are there any significant differences across dimensions?",
                "focus": entities["dimensions"] if entities["dimensions"] else ["categorical columns"]
            })
    
    def _generate_steps(self, entities: Dict[str, List[str]]):
        """Generate executable analysis steps"""
        step_id = 1
        
        # Step 1: Descriptive statistics
        self.plan["steps"].append({
            "id": f"step{step_id}",
            "description": "Calculate descriptive statistics for all numeric columns",
            "tool": "python/pandas",
            "operation": "describe"
        })
        step_id += 1
        
        # Step 2: Group by dimensions
        if entities["dimensions"]:
            for dim in entities["dimensions"][:3]:  # Limit to top 3 dimensions
                self.plan["steps"].append({
                    "id": f"step{step_id}",
                    "description": f"Analyze metrics grouped by {dim}",
                    "tool": "python/pandas",
                    "operation": "groupby",
                    "dimension": dim
                })
                step_id += 1
        
        # Step 3: Time series analysis if time columns exist
        if entities["time_periods"]:
            self.plan["steps"].append({
                "id": f"step{step_id}",
                "description": "Analyze trends over time",
                "tool": "python/pandas",
                "operation": "time_series"
            })
            step_id += 1
        
        # Step 4: Correlation analysis
        if len(entities["metrics"]) > 1:
            self.plan["steps"].append({
                "id": f"step{step_id}",
                "description": "Calculate correlations between metrics",
                "tool": "python/pandas",
                "operation": "correlation"
            })
            step_id += 1
        
        # Step 5: Outlier detection
        self.plan["steps"].append({
            "id": f"step{step_id}",
            "description": "Detect outliers and anomalies",
            "tool": "python/scipy",
            "operation": "outlier_detection"
        })
        step_id += 1
    
    def _generate_verification_tasks(self):
        """Generate tasks for verifying results"""
        self.plan["verification_tasks"] = [
            {
                "id": "v1",
                "description": "Cross-check calculations using alternative methods",
                "method": "dual_calculation"
            },
            {
                "id": "v2",
                "description": "Validate statistical significance",
                "method": "statistical_test"
            },
            {
                "id": "v3",
                "description": "Check for data quality issues affecting results",
                "method": "quality_check"
            },
            {
                "id": "v4",
                "description": "Verify consistency across different subsets",
                "method": "consistency_check"
            }
        ]
