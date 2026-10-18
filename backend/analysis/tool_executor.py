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
from .llm_service import LLMService


def _to_native(obj):
    """Recursively convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {str(k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if obj is None or obj is pd.NaT:
        return None
    # bool must be checked before int (bool is a subclass of int).
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    if isinstance(obj, np.ndarray):
        return [_to_native(v) for v in obj.tolist()]
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (pd.Timedelta, np.timedelta64)):
        return str(obj)
    if isinstance(obj, np.datetime64):
        return pd.Timestamp(obj).isoformat()
    if isinstance(obj, str):
        return obj
    return str(obj)

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
        self.plan_steps: List[Dict[str, Any]] = []
        self.llm_service = LLMService()
        # (chart_type, dimension, metric) signatures already emitted, so the
        # plan-driven pass never duplicates a chart the plan already asked for.
        self._viz_signatures: set = set()
        self._viz_counter = 0
    
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
        self.plan_steps = steps
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
            if operation == "visualization" or tool == "visualization":
                result["result"] = self._execute_visualization_step(step)
            elif tool == "python/pandas":
                result["result"] = self._execute_pandas_operation(operation, step)
            elif tool == "python/scipy":
                result["result"] = self._execute_scipy_operation(operation, step)
            elif tool == "python/sklearn":
                result["result"] = self._execute_sklearn_operation(operation, step)
            elif tool == "knowledge_base":
                result["result"] = self._execute_knowledge_base(operation, step)
            elif tool == "sql":
                # SQL requests are satisfied by the pandas layer, so record a
                # real result instead of skipping the step.
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
            # Try numeric describe first, fall back to all types if no numeric columns
            numeric_df = self.df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 0:
                result["statistics"] = _to_native(
                    numeric_df.describe().to_dict()
                )
            else:
                # For non-numeric data, provide summary info
                result["summary"] = _to_native({
                    col: {
                        "count": int(self.df[col].count()),
                        "unique": int(self.df[col].nunique()),
                        "top": str(self.df[col].mode()[0]) if len(self.df[col].mode()) > 0 else None,
                        "freq": int(self.df[col].value_counts().iloc[0]) if len(self.df[col].value_counts()) > 0 else 0,
                        "dtype": str(self.df[col].dtype)
                    }
                    for col in self.df.columns
                })
                result["note"] = "Dataset contains no numeric columns. Showing categorical summary."
        elif operation == "groupby":
            dimension = step.get("dimension")
            metric = step.get("metric")
            aggregation = (step.get("aggregation") or "mean").lower()
            if aggregation not in ("sum", "mean", "count", "median", "min", "max"):
                aggregation = "mean"
            if not dimension or dimension not in self.df.columns:
                # Fall back to the first categorical column so the step still runs.
                cat_cols = self.df.select_dtypes(exclude=[np.number]).columns.tolist()
                dimension = cat_cols[0] if cat_cols else None
            if dimension and dimension in self.df.columns:
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                metrics = [metric] if (metric and metric in numeric_cols) else numeric_cols
                if metrics:
                    grouped = self.df.groupby(dimension).agg({m: aggregation for m in metrics})
                    grouped = grouped.reset_index()
                    primary = metrics[0]
                    if primary in grouped.columns:
                        grouped = grouped.sort_values(primary, ascending=False)
                    result["group_by"] = dimension
                    result["metric"] = primary
                    result["aggregation"] = aggregation
                    # Convert to records for clean JSON serialization
                    result["grouped_data"] = _to_native(grouped.to_dict(orient="records"))
        elif operation == "time_series":
            # Simple time series analysis
            date_col = self._find_time_column()
            metric = step.get("metric")
            if date_col:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors="coerce")
                result["time_column"] = date_col
                result["time_range"] = {
                    "start": str(self.df[date_col].min()),
                    "end": str(self.df[date_col].max())
                }
                if metric and metric in self.df.columns:
                    trend = (
                        self.df.dropna(subset=[date_col])
                        .groupby(self.df[date_col].dt.to_period("M"))[metric]
                        .mean()
                        .reset_index()
                    )
                    trend.columns = [date_col, metric]
                    trend[date_col] = trend[date_col].astype(str)
                    result["metric"] = metric
                    result["trend"] = _to_native(trend.to_dict(orient="records"))
        elif operation == "correlation":
            numeric_df = self.df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 1:
                result["correlation_matrix"] = _to_native(numeric_df.corr().to_dict())
            else:
                result["note"] = "Correlation requires at least 2 numeric columns"
        elif operation == "outlier_detection":
            numeric_df = self.df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 0:
                result["outliers"] = self._iqr_outliers()
            else:
                result["note"] = "Outlier detection requires numeric columns"
                # For categorical data, show value frequency outliers
                result["categorical_outliers"] = _to_native({
                    col: {
                        "rare_values": self.df[col].value_counts()[self.df[col].value_counts() < 2].to_dict()
                    }
                    for col in self.df.select_dtypes(exclude=[np.number]).columns
                })
        elif operation == "statistical_test":
            result.update(self._run_statistical_test(step))
        
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
            result.update(self._run_statistical_test(step))
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
    
    def _find_time_column(self):
        """Locate a datetime-like column (real dtype or a parseable name)."""
        date_cols = self.df.select_dtypes(include=["datetime64"]).columns.tolist()
        if date_cols:
            return date_cols[0]
        for col in self.df.columns:
            if any(k in col.lower() for k in ("date", "time", "month", "year", "period")):
                parsed = pd.to_datetime(self.df[col], errors="coerce")
                if parsed.notna().mean() > 0.8:
                    return col
        return None

    def _run_statistical_test(self, step: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compare a numeric metric across groups of a categorical dimension."""
        step = step or {}
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = [
            c for c in self.df.select_dtypes(exclude=[np.number]).columns
            if 2 <= self.df[c].nunique() <= 20
        ]
        if not numeric_cols or not cat_cols:
            return {"note": "No suitable numeric/categorical pair for a group test"}
        
        metric = step.get("metric")
        if metric not in numeric_cols:
            metric = numeric_cols[0]
        group = step.get("dimension")
        if group not in cat_cols:
            group = cat_cols[0]
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
            "group_means": _to_native(
                self.df.groupby(group)[metric].mean().sort_values(ascending=False).to_dict()
            ),
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

    def _execute_knowledge_base(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Answer general questions using LLM's knowledge base."""
        description = step.get("description", "")
        goal = self.session_state.get("goal", "")
        
        # Provide some context about the dataset if we have it
        context = ""
        if self.df is not None:
            context = f"Dataset: {self.dataset_info.get('filename')}\n"
            context += f"Columns: {', '.join(self.df.columns)}\n"
            context += f"Rows: {len(self.df)}\n"
            
        answer = self.llm_service.answer_general_question(
            question=description if "question" in description.lower() else f"{description} (Goal: {goal})",
            context=context
        )
        
        return {
            "answer": answer,
            "type": "general_insight"
        }
    
    def _build_figure(self, chart_type: str, dimension: str = None, metric: str = None,
                      aggregation: str = "mean"):
        """Build a Plotly figure for a requested chart, using real columns.

        Returns None when the requested chart cannot be built from this dataset.
        """
        df = self.df
        aggregation = aggregation if aggregation in ("sum", "mean", "count", "median", "min", "max") else "mean"
        has = lambda c: bool(c) and c in df.columns
        try:
            # If no metric specified, try to find a suitable one
            if not metric:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    metric = numeric_cols[0]
                else:
                    # For non-numeric data, use count aggregation
                    metric = "count"
                    aggregation = "count"

            if has(dimension) and has(metric):
                if chart_type in ("bar", "histogram", "box", "scatter"):
                    if chart_type == "box":
                        return px.box(df, x=dimension, y=metric,
                                      title=f"Distribution of {metric} by {dimension}")
                    if chart_type == "scatter":
                        return px.scatter(df, x=dimension, y=metric,
                                          title=f"{metric} vs {dimension}")
                    # Handle count aggregation for categorical data
                    if aggregation == "count" or metric == "count":
                        grouped = df[dimension].value_counts().head(20).reset_index()
                        grouped.columns = [dimension, "count"]
                        return px.bar(grouped, x=dimension, y="count",
                                      title=f"Count by {dimension}")
                    # Check if metric is numeric
                    if metric in df.select_dtypes(include=[np.number]).columns:
                        grouped = (
                            df.groupby(dimension)[metric].agg(aggregation)
                            .reset_index().sort_values(metric, ascending=False).head(20)
                        )
                        return px.bar(grouped, x=dimension, y=metric,
                                      title=f"{aggregation.title()} {metric} by {dimension}")
                    else:
                        # For categorical metric, use count
                        grouped = df.groupby(dimension).size().head(20).reset_index()
                        grouped.columns = [dimension, "count"]
                        return px.bar(grouped, x=dimension, y="count",
                                      title=f"Count by {dimension}")
                if chart_type == "line":
                    time_col = self._find_time_column()
                    if time_col:
                        d = df.copy()
                        d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
                        series = d.dropna(subset=[time_col])
                        if metric in d.select_dtypes(include=[np.number]).columns:
                            series = series.groupby([dimension, time_col])[metric].agg(aggregation).reset_index()
                            return px.line(series, x=time_col, y=metric, color=dimension,
                                           title=f"{metric} over {time_col} by {dimension}")
                        else:
                            series = series.groupby([dimension, time_col]).size().reset_index()
                            series.columns = [dimension, time_col, "count"]
                            return px.line(series, x=time_col, y="count", color=dimension,
                                           title=f"Count over {time_col} by {dimension}")
            if has(metric):
                if chart_type == "line":
                    time_col = self._find_time_column()
                    if time_col:
                        d = df.copy()
                        d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
                        if metric in d.select_dtypes(include=[np.number]).columns:
                            trend = d.dropna(subset=[time_col]).groupby(time_col)[metric].agg(aggregation).reset_index()
                            return px.line(trend, x=time_col, y=metric, title=f"{metric} over {time_col}")
                        else:
                            trend = d.dropna(subset=[time_col]).groupby(time_col).size().reset_index()
                            trend.columns = [time_col, "count"]
                            return px.line(trend, x=time_col, y="count", title=f"Count over {time_col}")
                if metric in df.select_dtypes(include=[np.number]).columns:
                    return px.histogram(df, x=metric, title=f"Distribution of {metric}")
                else:
                    # For categorical metric, show value counts
                    value_counts = df[metric].value_counts().head(20)
                    return px.bar(x=value_counts.index, y=value_counts.values,
                                  title=f"Distribution of {metric}",
                                  labels={"x": metric, "y": "count"})
        except Exception as e:
            print(f"Figure build failed ({chart_type} {dimension} {metric}): {e}")
        return None

    def _store_figure(self, fig, description: str, operation: str) -> Dict[str, Any]:
        """Persist a figure to disk, the evidence store and the results list."""
        session_id = self.session_state["session_id"]
        viz_dir = os.path.join("analysis_results", session_id)
        os.makedirs(viz_dir, exist_ok=True)

        self._viz_counter += 1
        viz_id = f"viz_{self._viz_counter}"
        viz_path = os.path.join(viz_dir, f"{viz_id}.html")
        fig.write_html(viz_path)
        figure_json = json.loads(fig.to_json())

        # Ship the figure spec to the dashboard so it renders the real chart.
        self.execution_results.append({
            "step_id": viz_id,
            "description": description,
            "tool": "plotly",
            "operation": operation,
            "status": "completed",
            "result": {"visualization_path": viz_path, "figure": figure_json}
        })
        self.evidence_store.store_visualization(
            session_id, viz_id, viz_path, description, figure_json,
        )
        return {"visualization_path": viz_path, "figure": figure_json,
                "chart_type": operation}

    def _execute_visualization_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Produce the exact chart requested by a plan step."""
        chart_type = (step.get("chart_type") or "bar").lower()
        dimension = step.get("dimension")
        metric = step.get("metric")
        aggregation = step.get("aggregation", "mean")

        fig = self._build_figure(chart_type, dimension, metric, aggregation)
        if fig is None:
            return self._execute_generic_operation("visualization", step)

        self._viz_signatures.add((chart_type, dimension, metric))
        return self._store_figure(fig, step.get("description", "Visualization"), f"{chart_type}_chart")

    def _generate_visualizations(self):
        """Generate Plotly charts driven by the analysis plan, plus EDA extras."""
        numeric_cols = list(self.df.select_dtypes(include=[np.number]).columns)
        session_id = self.session_state["session_id"]

        # --- Goal-driven charts derived from the plan steps -------------------
        for step in self.plan_steps:
            operation = step.get("operation")
            dim = step.get("dimension")
            met = step.get("metric")
            agg = step.get("aggregation", "mean")
            if operation == "groupby" and dim and met:
                if ("bar", dim, met) in self._viz_signatures:
                    continue
                fig = self._build_figure("bar", dim, met, agg)
                if fig is not None:
                    self._viz_signatures.add(("bar", dim, met))
                    self._store_figure(fig, f"{agg.title()} {met} by {dim}", "bar_chart")
            elif operation == "time_series" and met:
                time_col = self._find_time_column()
                if time_col and ("line", dim, met) not in self._viz_signatures:
                    fig = self._build_figure("line", None, met, agg)
                    if fig is not None:
                        self._viz_signatures.add(("line", None, met))
                        self._store_figure(fig, f"{met} over {time_col}", "line_chart")
            elif operation == "statistical_test" and dim and met:
                if ("box", dim, met) not in self._viz_signatures:
                    fig = self._build_figure("box", dim, met)
                    if fig is not None:
                        self._viz_signatures.add(("box", dim, met))
                        self._store_figure(fig, f"Distribution of {met} by {dim}", "box_plot")

        # --- Correlation heatmap (always useful, deduped) ---------------------
        if len(numeric_cols) >= 2 and ("heatmap", None, None) not in self._viz_signatures:
            corr_matrix = self.df[numeric_cols].corr()
            fig = px.imshow(corr_matrix, title="Correlation Matrix", color_continuous_scale="RdBu")
            self._viz_signatures.add(("heatmap", None, None))
            self._store_figure(fig, "Correlation heatmap", "heatmap")

        # --- Generic EDA supplements -----------------------------------------
        for col in numeric_cols[:2]:
            if ("histogram", None, col) in self._viz_signatures:
                continue
            fig = px.histogram(self.df, x=col, title=f"Distribution of {col}")
            self._viz_signatures.add(("histogram", None, col))
            self._store_figure(fig, f"Histogram for {col}", "histogram")
    
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
