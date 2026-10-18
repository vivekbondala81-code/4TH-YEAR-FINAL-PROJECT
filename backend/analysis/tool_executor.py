import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import json
import os


def _to_native(obj):
    """Recursively convert numpy/pandas types to native Python types for JSON."""
    if isinstance(obj, dict):
        return {str(k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [_to_native(v) for v in obj.tolist()]
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj

class ToolExecutor:
    """Executes analysis tools (Python, SQL, Statistics, ML, Visualization) with real-time updates"""
    
    def __init__(self, dataset_info: Dict[str, Any], session_state: Dict[str, Any], evidence_store, connection_manager=None, loop=None):
        self.dataset_info = dataset_info
        self.session_state = session_state
        self.evidence_store = evidence_store
        self.connection_manager = connection_manager
        self.loop = loop
        self.df = None
        self.execution_results = []
    
    def _notify(self, session_id: str, step: str, status: str):
        """Push a progress update to the WebSocket without blocking analysis.

        Analysis runs in a worker thread, so the coroutine is scheduled back onto
        the main event loop in a thread-safe way.
        """
        if not self.connection_manager or not self.loop:
            return
        import asyncio
        asyncio.run_coroutine_threadsafe(
            self.connection_manager.send_progress(session_id, step, status),
            self.loop,
        )
        
    def _load_dataset(self):
        """Load the dataset for analysis"""
        file_path = self.dataset_info.get("file_path")
        if file_path and os.path.exists(file_path):
            if file_path.endswith(".csv"):
                self.df = pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                self.df = pd.read_excel(file_path)
        else:
            raise ValueError("Dataset file not found")
    
    def execute_all(self) -> List[Dict[str, Any]]:
        """Execute all analysis steps from the plan with real-time updates"""
        self._load_dataset()
        
        if self.df is None:
            return [{"error": "Could not load dataset"}]
        
        analysis_plan = self.session_state.get("analysis_plan", {})
        steps = analysis_plan.get("steps", [])
        session_id = self.session_state.get("session_id")
        
        for step in steps:
            self._notify(session_id, step["id"], "running")
            
            result = self._execute_step(step)
            self.execution_results.append(result)
            
            # Store in evidence store
            self.evidence_store.store_tool_execution(
                session_id,
                step["id"],
                result
            )
            
            self._notify(session_id, step["id"], "completed")
        
        # Generate visualizations
        self._notify(session_id, "visualization", "running")
        self._generate_visualizations()
        self._notify(session_id, "visualization", "completed")
        
        # Detect anomalies
        self._notify(session_id, "anomaly_detection", "running")
        self._detect_anomalies()
        self._notify(session_id, "anomaly_detection", "completed")
        
        return self.execution_results
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single analysis step"""
        tool = step.get("tool")
        operation = step.get("operation")
        
        result = {
            "step_id": step["id"],
            "description": step["description"],
            "tool": tool,
            "operation": operation,
            "status": "completed",
            "result": None
        }
        
        try:
            if tool == "python/pandas":
                result["result"] = self._execute_pandas_operation(operation, step)
            elif tool == "python/scipy":
                result["result"] = self._execute_scipy_operation(operation, step)
            elif tool == "python/sklearn":
                result["result"] = self._execute_sklearn_operation(operation, step)
            elif tool in ("sql", "visualization"):
                # SQL/visualization requests are satisfied by the pandas + plotting
                # layers, so record a real result instead of skipping the step.
                result["result"] = self._execute_generic_operation(operation, step)
            else:
                # Unknown tool from the LLM -> fall back to a descriptive pass so
                # the step still produces usable evidence.
                result["result"] = self._execute_generic_operation(operation, step)
                result["note"] = f"Tool '{tool}' mapped to default pandas analysis"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _execute_pandas_operation(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pandas operation"""
        result = {}
        
        if operation == "describe":
            result["statistics"] = _to_native(self.df.describe().to_dict())
        elif operation == "groupby":
            dimension = step.get("dimension")
            if not dimension or dimension not in self.df.columns:
                # Fall back to the first categorical column so the step still runs.
                cat_cols = self.df.select_dtypes(exclude=[np.number]).columns.tolist()
                dimension = cat_cols[0] if cat_cols else None
            if dimension and dimension in self.df.columns:
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    grouped = self.df.groupby(dimension)[numeric_cols].agg(['mean', 'sum', 'count'])
                    # Flatten MultiIndex columns to avoid tuple keys in JSON
                    grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
                    grouped = grouped.reset_index()
                    result["group_by"] = dimension
                    # Convert to records for clean JSON serialization
                    result["grouped_data"] = _to_native(grouped.to_dict(orient="records"))
        elif operation == "time_series":
            # Simple time series analysis
            date_cols = self.df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                date_col = date_cols[0]
                self.df[date_col] = pd.to_datetime(self.df[date_col])
                self.df = self.df.sort_values(date_col)
                result["time_range"] = {
                    "start": str(self.df[date_col].min()),
                    "end": str(self.df[date_col].max())
                }
        elif operation == "correlation":
            numeric_df = self.df.select_dtypes(include=[np.number])
            result["correlation_matrix"] = _to_native(numeric_df.corr().to_dict())
        elif operation == "outlier_detection":
            result["outliers"] = self._iqr_outliers()
        elif operation == "statistical_test":
            result.update(self._run_statistical_test())
        
        return result
    
    def _execute_scipy_operation(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scipy statistical operation"""
        result = {}
        
        if operation == "outlier_detection":
            numeric_df = self.df.select_dtypes(include=[np.number])
            outliers = {}
            for col in numeric_df.columns:
                col_data = numeric_df[col].dropna()
                if len(col_data) > 0:
                    z_scores = np.abs(stats.zscore(col_data))
                    outliers[col] = {
                        "count": int((z_scores > 3).sum()),
                        "percentage": float((z_scores > 3).sum() / len(col_data) * 100)
                    }
            result["outliers"] = outliers
        elif operation == "statistical_test":
            result.update(self._run_statistical_test())
        elif operation == "correlation":
            result["correlation_tests"] = self._run_correlation_tests()
        
        return result
    
    def _iqr_outliers(self) -> Dict[str, Any]:
        """IQR-based outlier counts per numeric column."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        outliers: Dict[str, Any] = {}
        for col in numeric_df.columns:
            col_data = numeric_df[col].dropna()
            if len(col_data) == 0:
                continue
            q1, q3 = col_data.quantile(0.25), col_data.quantile(0.75)
            iqr = q3 - q1
            mask = (col_data < q1 - 1.5 * iqr) | (col_data > q3 + 1.5 * iqr)
            outliers[col] = {
                "count": int(mask.sum()),
                "percentage": float(mask.sum() / len(col_data) * 100),
            }
        return outliers
    
    def _run_statistical_test(self) -> Dict[str, Any]:
        """Compare a numeric metric across groups of a categorical dimension."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = [
            c for c in self.df.select_dtypes(exclude=[np.number]).columns
            if 2 <= self.df[c].nunique() <= 20
        ]
        if not numeric_cols or not cat_cols:
            return {"note": "No suitable numeric/categorical pair for a group test"}
        
        metric, group = numeric_cols[0], cat_cols[0]
        groups = [
            g[metric].dropna().values
            for _, g in self.df.groupby(group)
            if len(g[metric].dropna()) >= 2
        ]
        if len(groups) < 2:
            return {"note": f"Not enough groups in {group} to run a significance test"}
        
        stat, p_value = stats.kruskal(*groups)
        return {
            "test": "kruskal_wallis",
            "metric": metric,
            "group_by": group,
            "groups": len(groups),
            "statistic": float(stat),
            "p_value": float(p_value),
            "significant": bool(p_value < 0.05),
        }
    
    def _run_correlation_tests(self) -> List[Dict[str, Any]]:
        """Pearson correlation with significance for each numeric column pair."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        tests: List[Dict[str, Any]] = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                pair = self.df[[numeric_cols[i], numeric_cols[j]]].dropna()
                if len(pair) < 3:
                    continue
                r, p_value = stats.pearsonr(pair.iloc[:, 0], pair.iloc[:, 1])
                tests.append({
                    "var1": numeric_cols[i],
                    "var2": numeric_cols[j],
                    "correlation": float(r),
                    "p_value": float(p_value),
                    "significant": bool(p_value < 0.05),
                })
        tests.sort(key=lambda t: abs(t["correlation"]), reverse=True)
        return tests[:10]
    
    def _execute_generic_operation(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Best-effort descriptive analysis for tools handled outside the dispatcher."""
        result: Dict[str, Any] = {
            "note": f"Handled '{operation}' via default pandas analysis"
        }
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            result["summary"] = _to_native(self.df[numeric_cols].describe().to_dict())
        return result
    
    def _execute_sklearn_operation(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sklearn ML operation"""
        result = {}
        
        if operation == "outlier_detection":
            numeric_df = self.df.select_dtypes(include=[np.number]).fillna(0)
            if len(numeric_df.columns) > 0:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(numeric_df)
                
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                outliers = iso_forest.fit_predict(scaled_data)
                
                result["outlier_count"] = int((outliers == -1).sum())
                result["outlier_percentage"] = float((outliers == -1).sum() / len(outliers) * 100)
        
        return result
    
    def _generate_visualizations(self):
        """Generate interactive Plotly visualizations and persist their figures"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        categorical_cols = self.df.select_dtypes(exclude=[np.number]).columns
        session_id = self.session_state["session_id"]

        # Namespace outputs per session so concurrent analyses never overwrite
        # each other's charts.
        viz_dir = os.path.join("analysis_results", session_id)
        os.makedirs(viz_dir, exist_ok=True)

        figures: List[tuple] = []

        # Histogram for numeric columns (limit to first 3)
        for col in numeric_cols[:3]:
            figures.append((
                px.histogram(self.df, x=col, title=f"Distribution of {col}"),
                f"Histogram for {col}",
                "histogram",
            ))

        # Bar chart for categorical columns (limit to first 2)
        for col in categorical_cols[:2]:
            value_counts = self.df[col].value_counts().head(10)
            figures.append((
                px.bar(x=value_counts.index, y=value_counts.values,
                       title=f"Top 10 values in {col}"),
                f"Bar chart for {col}",
                "bar_chart",
            ))

        # Correlation heatmap if enough numeric columns
        if len(numeric_cols) >= 2:
            corr_matrix = self.df[numeric_cols].corr()
            figures.append((
                px.imshow(corr_matrix, title="Correlation Matrix",
                          color_continuous_scale="RdBu"),
                "Correlation heatmap",
                "heatmap",
            ))

        for idx, (fig, description, operation) in enumerate(figures, start=1):
            viz_id = f"viz_{idx}"
            viz_path = os.path.join(viz_dir, f"{viz_id}.html")
            fig.write_html(viz_path)

            # Ship the figure spec to the dashboard so it can render the real
            # interactive chart (not just a placeholder).
            figure_json = json.loads(fig.to_json())

            self.execution_results.append({
                "step_id": viz_id,
                "description": description,
                "tool": "plotly",
                "operation": operation,
                "status": "completed",
                "result": {"visualization_path": viz_path, "figure": figure_json}
            })

            self.evidence_store.store_visualization(
                session_id,
                viz_id,
                viz_path,
                description,
                figure_json,
            )
    
    def _detect_anomalies(self):
        """Detect and flag anomalies in the data"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        anomalies = []
        
        for col in numeric_df.columns:
            col_data = numeric_df[col].dropna()
            if len(col_data) > 0:
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
                outlier_count = outlier_mask.sum()
                
                if outlier_count > 0:
                    anomalies.append({
                        "column": col,
                        "outlier_count": int(outlier_count),
                        "outlier_percentage": float(outlier_count / len(col_data) * 100),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound)
                    })
        
        self.execution_results.append({
            "step_id": "anomaly_detection",
            "description": "Anomaly detection",
            "tool": "custom",
            "operation": "anomaly_detection",
            "status": "completed",
            "result": {"anomalies": anomalies}
        })
        
        self.evidence_store.store_anomaly_detection(
            self.session_state["session_id"],
            anomalies
        )
