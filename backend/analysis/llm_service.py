import warnings
warnings.filterwarnings('ignore')

import google.generativeai as genai
from typing import Dict, Any, List
import json
from config import settings, get_gemini_api_key

class LLMService:
    """Gemini LLM service for AI-powered analysis"""
    
    def __init__(self):
        # Use the first available API key
        api_key = get_gemini_api_key()
        if not api_key:
            print("Warning: No Gemini API key configured. LLM features will be disabled.")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini model: {e}")
                self.model = None
        
    def generate_analysis_plan(self, goal: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis plan using LLM"""
        if not self.model:
            return self._fallback_plan(goal, dataset_info)
        
        prompt = f"""
You are an expert data analyst. Generate a detailed analysis plan for the following goal:

GOAL: {goal}

DATASET INFORMATION:
- Rows: {dataset_info.get('rows', 0)}
- Columns: {dataset_info.get('columns', 0)}
- Column Names: {', '.join(dataset_info.get('column_names', []))}
- Numeric Columns: {', '.join(dataset_info.get('numeric_columns', []))}
- Categorical Columns: {', '.join(dataset_info.get('categorical_columns', []))}

Generate a JSON response with:
1. main_goal: The refined understanding of the goal
2. questions: Array of specific questions to answer (each with id, question, focus)
3. steps: Array of executable steps (each with id, description, tool, operation)
4. verification_tasks: Array of verification methods

Tools available: python/pandas, python/scipy, python/sklearn, sql, visualization
Operations: describe, groupby, correlation, time_series, outlier_detection, statistical_test

Return ONLY valid JSON.
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse the response as JSON
            json_text = response.text.strip()
            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                json_text = json_text.replace("```json", "").replace("```", "").strip()
            
            plan = json.loads(json_text)
            return plan
        except Exception as e:
            print(f"LLM Error: {e}")
            # Fallback to rule-based planning
            return self._fallback_plan(goal, dataset_info)
    
    def generate_hypotheses(self, goal: str, analysis_plan: Dict[str, Any], dataset_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate hypotheses using LLM"""
        if not self.model:
            return self._fallback_hypotheses(goal, dataset_info)
        
        prompt = f"""
You are an expert data analyst. Generate multiple testable hypotheses for the following analysis:

GOAL: {goal}

ANALYSIS PLAN:
{json.dumps(analysis_plan, indent=2)}

DATASET:
- Numeric Columns: {', '.join(dataset_info.get('numeric_columns', []))}
- Categorical Columns: {', '.join(dataset_info.get('categorical_columns', []))}

Generate 5-7 hypotheses as a JSON array. Each hypothesis should have:
- id: H1, H2, etc.
- statement: Clear testable statement
- type: hypothesis type (correlation, dimensional, metric, interaction, data_quality)
- evidence_required: Array of evidence types needed
- test_method: How to test this hypothesis

Return ONLY valid JSON array.
"""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            if json_text.startswith("```"):
                json_text = json_text.replace("```json", "").replace("```", "").strip()
            
            hypotheses = json.loads(json_text)
            return hypotheses if isinstance(hypotheses, list) else []
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_hypotheses(goal, dataset_info)
    
    def interpret_results(self, results: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
        """Interpret analysis results using LLM"""
        if not self.model:
            return {
                "key_findings": ["Analysis completed successfully"],
                "insights": ["Review the detailed results"],
                "recommendations": ["Proceed with findings"],
                "confidence": "Medium",
                "limitations": ["LLM interpretation unavailable"]
            }
        
        prompt = f"""
You are an expert data analyst. Interpret the following analysis results and provide insights:

GOAL: {goal}

RESULTS:
{json.dumps(results, indent=2)}

Provide a JSON response with:
- key_findings: Array of main findings
- insights: Array of deeper insights
- recommendations: Array of actionable recommendations
- confidence: Overall confidence level (High/Medium/Low)
- limitations: Array of analysis limitations

Return ONLY valid JSON.
"""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            if json_text.startswith("```"):
                json_text = json_text.replace("```json", "").replace("```", "").strip()
            
            interpretation = json.loads(json_text)
            return interpretation
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "key_findings": ["Analysis completed successfully"],
                "insights": ["Review the detailed results"],
                "recommendations": ["Proceed with findings"],
                "confidence": "Medium",
                "limitations": ["LLM interpretation unavailable"]
            }
    
    def select_tools(self, hypothesis: Dict[str, Any], dataset_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select appropriate tools for testing a hypothesis"""
        if not self.model:
            return [
                {
                    "tool": "python/pandas",
                    "operation": "describe",
                    "description": "Basic statistical analysis"
                }
            ]
        
        prompt = f"""
You are an expert data analyst. Select the best tools to test this hypothesis:

HYPOTHESIS: {hypothesis.get('statement')}
TYPE: {hypothesis.get('type')}
EVIDENCE REQUIRED: {', '.join(hypothesis.get('evidence_required', []))}

DATASET:
- Numeric Columns: {', '.join(dataset_info.get('numeric_columns', []))}
- Categorical Columns: {', '.join(dataset_info.get('categorical_columns', []))}

Available tools: python/pandas, python/scipy, python/sklearn, sql, visualization

Return a JSON array of tool selections with:
- tool: The tool to use
- operation: Specific operation
- description: What this will accomplish

Return ONLY valid JSON array.
"""
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            if json_text.startswith("```"):
                json_text = json_text.replace("```json", "").replace("```", "").strip()
            
            tools = json.loads(json_text)
            return tools if isinstance(tools, list) else []
        except Exception as e:
            print(f"LLM Error: {e}")
            return [
                {
                    "tool": "python/pandas",
                    "operation": "describe",
                    "description": "Basic statistical analysis"
                }
            ]
    
    def _fallback_plan(self, goal: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based planning"""
        return {
            "main_goal": goal,
            "questions": [
                {"id": "q1", "question": "What are the overall patterns in the data?", "focus": ["all columns"]},
                {"id": "q2", "question": "Are there significant differences across dimensions?", "focus": dataset_info.get("categorical_columns", [])}
            ],
            "steps": [
                {"id": "step1", "description": "Calculate descriptive statistics", "tool": "python/pandas", "operation": "describe"},
                {"id": "step2", "description": "Detect outliers", "tool": "python/scipy", "operation": "outlier_detection"}
            ],
            "verification_tasks": [
                {"id": "v1", "description": "Cross-check calculations", "method": "dual_calculation"}
            ]
        }
    
    def _fallback_hypotheses(self, goal: str, dataset_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback rule-based hypotheses"""
        return [
            {
                "id": "H1",
                "statement": "There are significant patterns in the data that explain the goal",
                "type": "general",
                "evidence_required": ["statistics", "correlation"],
                "test_method": "statistical_analysis"
            }
        ]
