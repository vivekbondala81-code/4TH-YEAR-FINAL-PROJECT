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

class ToolExecutor:
    """Executes analysis tools (Python, SQL, Statistics, ML, Visualization)"""
    
    def __init__(self, dataset_info: Dict[str, Any], session_state: Dict[str, Any], evidence_store):
        self.dataset_info = dataset_info
        self.session_state = session_state
        self.evidence_store = evidence_store
        self.df = None
        self.execution_results = []
        
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
        """Execute all analysis steps from the plan"""
        self._load_dataset()
        
        if self.df is None:
            return [{"error": "Could not load dataset"}]
        
        analysis_plan = self.session_state.get("analysis_plan", {})
        steps = analysis_plan.get("steps", [])
        
        for step in steps:
            result = self._execute_step(step)
            self.execution_results.append(result)
            
            # Store in evidence store
            self.evidence_store.store_tool_execution(
                self.session_state["session_id"],
                step["id"],
                result
            )
        
        # Generate visualizations
        self._generate_visualizations()
        
        # Detect anomalies
        self._detect_anomalies()
        
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
            else:
                result["status"] = "skipped"
                result["error"] = f"Unknown tool: {tool}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _execute_pandas_operation(self, operation: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pandas operation"""
        result = {}
        
        if operation == "describe":
            result["statistics"] = self.df.describe().to_dict()
        elif operation == "groupby":
            dimension = step.get("dimension")
            if dimension and dimension in self.df.columns:
                grouped = self.df.groupby(dimension).agg({
                    col: ['mean', 'sum', 'count'] 
                    for col in self.df.select_dtypes(include=[np.number]).columns
                })
                result["grouped_data"] = grouped.to_dict()
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
            result["correlation_matrix"] = numeric_df.corr().to_dict()
        
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
        """Generate appropriate visualizations"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        categorical_cols = self.df.select_dtypes(exclude=[np.number]).columns
        
        viz_id = 1
        
        # Histogram for numeric columns
        for col in numeric_cols[:3]:  # Limit to first 3
            fig = px.histogram(self.df, x=col, title=f"Distribution of {col}")
            viz_path = f"analysis_results/viz_{viz_id}.html"
            fig.write_html(viz_path)
            
            self.execution_results.append({
                "step_id": f"viz_{viz_id}",
                "description": f"Histogram for {col}",
                "tool": "plotly",
                "operation": "histogram",
                "status": "completed",
                "result": {"visualization_path": viz_path}
            })
            
            self.evidence_store.store_visualization(
                self.session_state["session_id"],
                f"viz_{viz_id}",
                viz_path,
                f"Histogram for {col}"
            )
            viz_id += 1
        
        # Bar chart for categorical columns
        for col in categorical_cols[:2]:  # Limit to first 2
            value_counts = self.df[col].value_counts().head(10)
            fig = px.bar(x=value_counts.index, y=value_counts.values, 
                        title=f"Top 10 values in {col}")
            viz_path = f"analysis_results/viz_{viz_id}.html"
            fig.write_html(viz_path)
            
            self.execution_results.append({
                "step_id": f"viz_{viz_id}",
                "description": f"Bar chart for {col}",
                "tool": "plotly",
                "operation": "bar_chart",
                "status": "completed",
                "result": {"visualization_path": viz_path}
            })
            
            self.evidence_store.store_visualization(
                self.session_state["session_id"],
                f"viz_{viz_id}",
                viz_path,
                f"Bar chart for {col}"
            )
            viz_id += 1
        
        # Correlation heatmap if enough numeric columns
        if len(numeric_cols) >= 2:
            corr_matrix = self.df[numeric_cols].corr()
            fig = px.imshow(corr_matrix, 
                           title="Correlation Matrix",
                           color_continuous_scale="RdBu")
            viz_path = f"analysis_results/viz_{viz_id}.html"
            fig.write_html(viz_path)
            
            self.execution_results.append({
                "step_id": f"viz_{viz_id}",
                "description": "Correlation heatmap",
                "tool": "plotly",
                "operation": "heatmap",
                "status": "completed",
                "result": {"visualization_path": viz_path}
            })
            
            self.evidence_store.store_visualization(
                self.session_state["session_id"],
                f"viz_{viz_id}",
                viz_path,
                "Correlation heatmap"
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
