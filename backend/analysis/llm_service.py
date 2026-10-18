import warnings
warnings.filterwarnings('ignore')

from typing import Dict, Any, List, Optional
import json
import re
from config import get_gemini_api_keys

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    GENAI_AVAILABLE = False


# Free-tier Gemini projects are rate limited per model, and Google retires old
# model names over time. Trying a short list of aliases (higher-quota lite model
# first) before falling back keeps the public demo working without paid quota.
MODEL_CANDIDATES = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

DEFAULT_MODEL = MODEL_CANDIDATES[0]


class LLMService:
    """Gemini LLM service for AI-powered analysis.

    Uses the modern ``google-genai`` SDK, rotates across every configured API
    key and model alias on failure, and requests strict JSON output so
    downstream parsing is reliable. Every method degrades gracefully to a
    rule-based result when no key is configured or the API is unavailable.
    """

    def __init__(self):
        self.api_keys = get_gemini_api_keys()
        self.clients: List[Any] = []
        self.active_index = 0
        self.model_name = DEFAULT_MODEL

        if not GENAI_AVAILABLE:
            print("Warning: google-genai SDK not installed. LLM features disabled.")
        elif not self.api_keys:
            print("Warning: No Gemini API key configured. LLM features will be disabled.")
        else:
            for key in self.api_keys:
                try:
                    self.clients.append(genai.Client(api_key=key))
                except Exception as e:
                    print(f"Warning: Failed to initialize Gemini client: {e}")

        # `model` stays truthy only when a usable client exists so the rest of
        # the codebase can keep using `if self.llm_service.model:` checks.
        self.model = self.clients[0] if self.clients else None

    # ------------------------------------------------------------------
    # Core generation + parsing helpers
    # ------------------------------------------------------------------
    def _generate(self, prompt: str, json_mode: bool = False) -> Optional[str]:
        """Generate text, rotating through (model, api key) pairs until one succeeds."""
        if not self.clients:
            return None

        last_error: Optional[Exception] = None
        for model in MODEL_CANDIDATES:
            for offset in range(len(self.clients)):
                idx = (self.active_index + offset) % len(self.clients)
                client = self.clients[idx]
                try:
                    config = None
                    if json_mode:
                        config = types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=config,
                    )
                    text = getattr(response, "text", None)
                    if text:
                        self.active_index = idx  # remember a working key
                        self.model_name = model
                        return text
                except Exception as e:  # rate limited / unavailable -> try next
                    last_error = e
                    continue

        if last_error:
            raise last_error
        return None

    @staticmethod
    def _parse_json(text: Optional[str]) -> Any:
        """Parse a JSON payload, tolerating markdown code fences."""
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to salvage the first JSON object/array in the text
            for start, end in (("{", "}"), ("[", "]")):
                s, e = cleaned.find(start), cleaned.rfind(end)
                if s != -1 and e != -1 and e > s:
                    try:
                        return json.loads(cleaned[s:e + 1])
                    except json.JSONDecodeError:
                        continue
        return None

    # ------------------------------------------------------------------
    # High level AI features
    # ------------------------------------------------------------------
    def generate_analysis_plan(self, goal: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis plan using LLM"""
        if not self.model:
            return self._normalize_plan(self._fallback_plan(goal, dataset_info), dataset_info, goal)

        prompt = f"""
You are an expert data analyst. Generate a detailed analysis plan that directly
answers the user's goal using THIS dataset.

GOAL: {goal}

DATASET INFORMATION:
- Rows: {dataset_info.get('rows', 0)}
- Columns: {dataset_info.get('columns', 0)}
- All Columns: {', '.join(dataset_info.get('column_names', []))}
- Numeric Columns: {', '.join(dataset_info.get('numeric_columns', []))}
- Categorical Columns: {', '.join(dataset_info.get('categorical_columns', []))}

Return a JSON object with:
1. main_goal: refined understanding of the goal
2. questions: array of specific questions (each with id, question, focus)
3. steps: array of executable steps
4. verification_tasks: array of verification methods (each with id, description, method)

EVERY step must be a JSON object with these keys:
- id: "step_1", "step_2", ...
- description: what is computed AND why it answers the goal
- tool: one of "python/pandas", "python/scipy", "python/sklearn", "visualization"
- operation: one of "describe", "groupby", "correlation", "time_series",
  "outlier_detection", "statistical_test", "visualization"
- dimension: EXACT categorical column name to group/split by (required for groupby,
  statistical_test and visualization steps)
- metric: EXACT numeric column name to measure (required for groupby, time_series,
  visualization and statistical_test steps)
- aggregation: "sum", "mean" or "count" (for groupby steps)
- chart_type: "bar", "line", "box", "scatter" or "histogram" (for visualization steps)

Rules:
- Use ONLY column names exactly as listed above. Never invent column names.
- Prefer the columns the goal mentions (e.g. a "sales" goal should use the Sales metric).
- Include at least one groupby step comparing the key metric across the most relevant
  categorical dimension, one correlation or statistical_test step, and one visualization
  step that charts the key metric.
- 5 to 7 steps total.

Return ONLY valid JSON.
"""
        try:
            plan = self._parse_json(self._generate(prompt, json_mode=True))
            if isinstance(plan, dict) and plan.get("steps"):
                return self._normalize_plan(plan, dataset_info, goal)
            print("LLM returned empty/invalid plan, falling back to rule-based.")
        except Exception as e:
            print(f"LLM Error: {e}")
        return self._normalize_plan(self._fallback_plan(goal, dataset_info), dataset_info, goal)

    @staticmethod
    def _best_column(goal: str, candidates: List[str]) -> Optional[str]:
        """Pick the candidate column most relevant to the goal text."""
        if not candidates:
            return None
        goal_tokens = [t for t in re.split(r"[^a-z0-9]+", goal.lower()) if len(t) > 2]
        for col in candidates:
            col_tokens = set(re.split(r"[^a-z0-9]+", col.lower()))
            for token in goal_tokens:
                if token in col_tokens or any(token in c or c in token for c in col_tokens if len(c) > 2):
                    return col
        return candidates[0]

    def _normalize_plan(self, plan: Dict[str, Any], dataset_info: Dict[str, Any], goal: str) -> Dict[str, Any]:
        """Validate/repair the LLM plan so every step maps to real dataset columns.

        This is what makes the executed analysis goal-specific: each groupby /
        visualization step is guaranteed to carry a concrete dimension and metric
        taken from the actual dataset.
        """
        columns = list(dataset_info.get("column_names", []))
        numeric = list(dataset_info.get("numeric_columns", []))
        categorical = list(dataset_info.get("categorical_columns", []))
        if not numeric:
            numeric = [c for c in columns if c.lower() not in {x.lower() for x in categorical}]
        if not columns:
            return plan

        default_dim = self._best_column(goal, categorical) or (categorical[0] if categorical else columns[0])
        default_metric = self._best_column(goal, numeric) or (numeric[0] if numeric else None)

        valid_ops = {
            "describe", "groupby", "correlation", "time_series",
            "outlier_detection", "statistical_test", "visualization",
        }
        valid_tools = {"python/pandas", "python/scipy", "python/sklearn", "visualization"}

        for step in plan.get("steps", []):
            operation = (step.get("operation") or "").strip()
            if operation not in valid_ops:
                operation = "describe"
            step["operation"] = operation

            if step.get("tool") not in valid_tools:
                step["tool"] = "python/pandas"

            dimension = step.get("dimension")
            metric = step.get("metric")
            if dimension not in columns:
                dimension = None
            if metric not in columns:
                metric = None

            if operation in ("groupby", "statistical_test"):
                step["dimension"] = dimension or default_dim
                step["metric"] = metric or default_metric
            elif operation in ("time_series", "visualization"):
                step["metric"] = metric or default_metric
                if operation == "visualization":
                    step["dimension"] = dimension or default_dim
                    step["chart_type"] = step.get("chart_type") or "bar"
            elif dimension:
                step["dimension"] = dimension
            if metric:
                step["metric"] = metric

        return plan

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

Generate 5-7 hypotheses as a JSON array. Each hypothesis must have:
- id: H1, H2, etc.
- statement: Clear testable statement
- type: hypothesis type (correlation, dimensional, metric, interaction, data_quality)
- evidence_required: Array of evidence types needed
- test_method: How to test this hypothesis

Return ONLY valid JSON array.
"""
        try:
            hypotheses = self._parse_json(self._generate(prompt, json_mode=True))
            if isinstance(hypotheses, list) and hypotheses:
                return hypotheses
            print("LLM returned empty/invalid hypotheses, falling back to rule-based.")
        except Exception as e:
            print(f"LLM Error: {e}")
        return self._fallback_hypotheses(goal, dataset_info)

    def interpret_results(self, results: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
        """Interpret analysis results using LLM"""
        fallback = {
            "key_findings": ["Analysis completed successfully"],
            "insights": ["Review the detailed results"],
            "recommendations": ["Proceed with findings"],
            "confidence": "Medium",
            "limitations": ["LLM interpretation unavailable"]
        }
        if not self.model:
            return fallback

        # Keep the payload compact to control token usage / latency.
        compact = json.dumps(results[:8], default=str)[:8000]
        prompt = f"""
You are an expert data analyst. Interpret the following analysis results and provide insights:

GOAL: {goal}

RESULTS:
{compact}

Provide a JSON object with:
- key_findings: Array of main findings (strings)
- insights: Array of deeper insights (strings)
- recommendations: Array of actionable recommendations (strings)
- confidence: Overall confidence level (High/Medium/Low)
- limitations: Array of analysis limitations (strings)

Return ONLY valid JSON.
"""
        try:
            interpretation = self._parse_json(self._generate(prompt, json_mode=True))
            if isinstance(interpretation, dict) and interpretation.get("key_findings"):
                return interpretation
        except Exception as e:
            print(f"LLM Error: {e}")
        return fallback

    def interpret_verification(self, hypothesis: Dict[str, Any], evidence: Any, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Interpret a single hypothesis' statistical validation using the LLM."""
        if not self.model:
            return {}

        compact = json.dumps(execution_results[:3], default=str)[:4000]
        prompt = f"""
Interpret the statistical validation for this hypothesis:

HYPOTHESIS: {hypothesis.get('statement')}
EVIDENCE: {json.dumps(evidence, default=str)}
EXECUTION RESULTS: {compact}

Provide a JSON object with:
- confidence_level: High/Medium/Low
- interpretation: Brief interpretation of the evidence
- needs_more_data: boolean

Return ONLY valid JSON.
"""
        try:
            result = self._parse_json(self._generate(prompt, json_mode=True))
            return result if isinstance(result, dict) else {}
        except Exception as e:
            print(f"LLM statistical interpretation failed: {e}")
            return {}

    def select_tools(self, hypothesis: Dict[str, Any], dataset_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select appropriate tools for testing a hypothesis"""
        fallback = [
            {
                "tool": "python/pandas",
                "operation": "describe",
                "description": "Basic statistical analysis"
            }
        ]
        if not self.model:
            return fallback

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
            tools = self._parse_json(self._generate(prompt, json_mode=True))
            if isinstance(tools, list) and tools:
                return tools
        except Exception as e:
            print(f"LLM Error: {e}")
        return fallback

    # ------------------------------------------------------------------
    # Rule-based fallbacks (used when the API is unavailable)
    # ------------------------------------------------------------------
    def _fallback_plan(self, goal: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based planning (still goal-aware via column matching)."""
        numeric = list(dataset_info.get("numeric_columns", []))
        categorical = list(dataset_info.get("categorical_columns", []))
        metric = self._best_column(goal, numeric) or (numeric[0] if numeric else None)
        dimension = self._best_column(goal, categorical) or (categorical[0] if categorical else None)

        steps: List[Dict[str, Any]] = []
        if metric:
            steps.append({
                "id": "step_1",
                "description": f"Profile the distribution of {metric}",
                "tool": "python/pandas",
                "operation": "describe",
                "metric": metric,
            })
        if dimension and metric:
            steps.append({
                "id": f"step_{len(steps) + 1}",
                "description": f"Compare {metric} across each {dimension}",
                "tool": "python/pandas",
                "operation": "groupby",
                "dimension": dimension,
                "metric": metric,
                "aggregation": "mean",
            })
            steps.append({
                "id": f"step_{len(steps) + 1}",
                "description": f"Test whether {metric} differs significantly across {dimension}",
                "tool": "python/scipy",
                "operation": "statistical_test",
                "dimension": dimension,
                "metric": metric,
            })
            steps.append({
                "id": f"step_{len(steps) + 1}",
                "description": f"Chart {metric} by {dimension}",
                "tool": "visualization",
                "operation": "visualization",
                "dimension": dimension,
                "metric": metric,
                "chart_type": "bar",
            })
        if len(numeric) > 1:
            steps.append({
                "id": f"step_{len(steps) + 1}",
                "description": "Check correlations between numeric variables",
                "tool": "python/scipy",
                "operation": "correlation",
            })
        steps.append({
            "id": f"step_{len(steps) + 1}",
            "description": "Detect outliers across numeric columns",
            "tool": "python/scipy",
            "operation": "outlier_detection",
        })

        if not steps:
            steps = [
                {"id": "step_1", "description": "Calculate descriptive statistics", "tool": "python/pandas", "operation": "describe"},
            ]

        return {
            "main_goal": goal,
            "questions": [
                {"id": "q1", "question": f"What patterns in the data explain: {goal}?", "focus": numeric or ["all columns"]},
                {"id": "q2", "question": f"How does the key metric vary across {dimension}?" if dimension else "Are there significant differences across dimensions?", "focus": [dimension] if dimension else categorical},
            ],
            "steps": steps,
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
