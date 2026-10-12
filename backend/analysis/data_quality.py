from typing import Dict, Any, List
import numpy as np

class DataQualityAnalyzer:
    """Analyzes data quality and generates quality reports"""
    
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.quality_report = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        self.quality_report = {
            "overall_score": 0,
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "column_status": {}
        }
        
        total_issues = 0
        total_warnings = 0
        
        # Analyze each column
        for col_name, col_info in self.profile["columns"].items():
            col_status = {
                "status": "good",
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Check for missing values
            null_pct = col_info.get("null_percentage", 0)
            if null_pct > 20:
                col_status["status"] = "poor"
                col_status["issues"].append(f"High missing values: {null_pct:.1f}%")
                col_status["recommendations"].append("Consider imputation or removal")
                total_issues += 1
            elif null_pct > 5:
                col_status["status"] = "warning"
                col_status["warnings"].append(f"Some missing values: {null_pct:.1f}%")
                col_status["recommendations"].append("Review missing value handling")
                total_warnings += 1
            
            # Check for unique values (potential ID columns)
            unique_pct = col_info.get("unique_percentage", 0)
            if unique_pct > 95 and col_info["type"] == "categorical":
                col_status["warnings"].append("Very high cardinality - possible ID column")
                total_warnings += 1
            
            # Check numeric columns for outliers
            if col_info["type"] == "numeric":
                mean = col_info.get("mean")
                std = col_info.get("std")
                min_val = col_info.get("min")
                max_val = col_info.get("max")
                
                if mean is not None and std is not None and std > 0:
                    # Simple outlier detection using z-score
                    # (would need actual data for full detection)
                    col_status["warnings"].append("Consider outlier analysis")
                    total_warnings += 1
            
            self.quality_report["column_status"][col_name] = col_status
        
        # Check duplicates
        duplicate_pct = self.profile.get("duplicate_percentage", 0)
        if duplicate_pct > 5:
            self.quality_report["issues"].append(f"High duplicate rate: {duplicate_pct:.1f}%")
            self.quality_report["recommendations"].append("Remove duplicate records")
            total_issues += 1
        elif duplicate_pct > 0:
            self.quality_report["warnings"].append(f"Some duplicates: {duplicate_pct:.1f}%")
            self.quality_report["recommendations"].append("Review duplicate records")
            total_warnings += 1
        
        # Calculate overall score
        total_columns = len(self.profile["columns"])
        if total_columns > 0:
            score = 100 - (total_issues * 20) - (total_warnings * 5)
            self.quality_report["overall_score"] = max(0, min(100, score))
        
        # Summary
        self.quality_report["summary"] = {
            "total_columns": total_columns,
            "columns_with_issues": len([
                c for c, s in self.quality_report["column_status"].items()
                if s["status"] == "poor"
            ]),
            "columns_with_warnings": len([
                c for c, s in self.quality_report["column_status"].items()
                if s["status"] == "warning"
            ]),
            "total_issues": total_issues,
            "total_warnings": total_warnings
        }
        
        return self.quality_report
