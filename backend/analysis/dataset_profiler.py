import pandas as pd
import numpy as np
from typing import Dict, Any, List
import os


def _to_native(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
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
    if obj is pd.NaT:
        return None
    return obj


class DatasetProfiler:
    """Profiles uploaded datasets to understand structure and content"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self._profile = {}
        
    def _load_data(self) -> pd.DataFrame:
        """Load data from CSV or Excel with automatic type conversion"""
        file_extension = self.file_path.split(".")[-1].lower()

        if file_extension == "csv":
            self.df = pd.read_csv(self.file_path)
        elif file_extension in ["xlsx", "xls"]:
            self.df = pd.read_excel(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        # Automatic type conversion: try to convert object columns to numeric
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                # Try to convert to numeric
                converted = pd.to_numeric(self.df[col], errors='coerce')
                # If conversion succeeded for at least 50% of non-null values, keep it
                if converted.notna().sum() / self.df[col].notna().sum() > 0.5 if self.df[col].notna().sum() > 0 else False:
                    self.df[col] = converted

        return self.df
    
    def profile(self) -> Dict[str, Any]:
        """Generate comprehensive dataset profile"""
        self._load_data()
        
        # Basic info
        result = {
            "rows": int(len(self.df)),
            "columns": int(len(self.df.columns)),
            "column_names": [str(c) for c in self.df.columns],
            "memory_usage": int(self.df.memory_usage(deep=True).sum()),
        }
        
        # Column details
        result["column_stats"] = {}
        for col in self.df.columns:
            col_info = {
                "dtype": str(self.df[col].dtype),
                "non_null_count": int(self.df[col].count()),
                "null_count": int(self.df[col].isnull().sum()),
                "null_percentage": float((self.df[col].isnull().sum() / len(self.df)) * 100),
                "unique_count": int(self.df[col].nunique()),
                "unique_percentage": float((self.df[col].nunique() / len(self.df)) * 100),
            }
            
            # Add statistics for numeric columns
            if pd.api.types.is_numeric_dtype(self.df[col]):
                col_info.update({
                    "min": float(self.df[col].min()) if not self.df[col].empty else None,
                    "max": float(self.df[col].max()) if not self.df[col].empty else None,
                    "mean": float(self.df[col].mean()) if not self.df[col].empty else None,
                    "median": float(self.df[col].median()) if not self.df[col].empty else None,
                    "std": float(self.df[col].std()) if not self.df[col].empty else None,
                    "type": "numeric"
                })
            else:
                col_info["type"] = "categorical"
                # Top values for categorical
                top_values = self.df[col].value_counts().head(10)
                col_info["top_values"] = [
                    {"value": str(val), "count": int(count)}
                    for val, count in top_values.items()
                ]
            
            result["column_stats"][col] = col_info
        
        # Duplicates
        result["duplicate_count"] = int(self.df.duplicated().sum())
        result["duplicate_percentage"] = float((result["duplicate_count"] / len(self.df)) * 100)
        
        # Data types summary
        result["numeric_columns"] = [
            str(col) for col in self.df.columns 
            if pd.api.types.is_numeric_dtype(self.df[col])
        ]
        result["categorical_columns"] = [
            str(col) for col in self.df.columns 
            if not pd.api.types.is_numeric_dtype(self.df[col])
        ]
        
        # Potential relationships (correlation for numeric columns)
        if len(result["numeric_columns"]) > 1:
            try:
                corr_matrix = self.df[result["numeric_columns"]].corr()
                result["correlations"] = _to_native(corr_matrix.to_dict())
            except Exception as e:
                print(f"Warning: Could not compute correlations: {e}")
                result["correlations"] = {}
        else:
            result["correlations"] = {}
        
        self._profile = _to_native(result)
        return self._profile
