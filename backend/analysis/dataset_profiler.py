import pandas as pd
import numpy as np
from typing import Dict, Any, List
import os

class DatasetProfiler:
    """Profiles uploaded datasets to understand structure and content"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None
        self.profile = {}
        
    def _load_data(self) -> pd.DataFrame:
        """Load data from CSV or Excel"""
        file_extension = self.file_path.split(".")[-1].lower()
        
        if file_extension == "csv":
            self.df = pd.read_csv(self.file_path)
        elif file_extension in ["xlsx", "xls"]:
            self.df = pd.read_excel(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        return self.df
    
    def profile(self) -> Dict[str, Any]:
        """Generate comprehensive dataset profile"""
        self._load_data()
        
        # Basic info
        self.profile = {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "column_names": list(self.df.columns),
            "memory_usage": self.df.memory_usage(deep=True).sum(),
        }
        
        # Column details
        self.profile["columns"] = {}
        for col in self.df.columns:
            col_info = {
                "dtype": str(self.df[col].dtype),
                "non_null_count": self.df[col].count(),
                "null_count": self.df[col].isnull().sum(),
                "null_percentage": (self.df[col].isnull().sum() / len(self.df)) * 100,
                "unique_count": self.df[col].nunique(),
                "unique_percentage": (self.df[col].nunique() / len(self.df)) * 100,
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
            
            self.profile["columns"][col] = col_info
        
        # Duplicates
        self.profile["duplicate_count"] = self.df.duplicated().sum()
        self.profile["duplicate_percentage"] = (self.profile["duplicate_count"] / len(self.df)) * 100
        
        # Data types summary
        self.profile["numeric_columns"] = [
            col for col in self.df.columns 
            if pd.api.types.is_numeric_dtype(self.df[col])
        ]
        self.profile["categorical_columns"] = [
            col for col in self.df.columns 
            if not pd.api.types.is_numeric_dtype(self.df[col])
        ]
        
        # Potential relationships (correlation for numeric columns)
        if len(self.profile["numeric_columns"]) > 1:
            corr_matrix = self.df[self.profile["numeric_columns"]].corr()
            self.profile["correlations"] = corr_matrix.to_dict()
        
        return self.profile
