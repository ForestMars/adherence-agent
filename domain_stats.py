#!/usr/bin/env python3
"""
Domain Statistics Agent

An intelligent agent that:
1. Discovers the structure/shape of a given domain (files, APIs, databases)
2. Runs comprehensive statistics over the discovered data
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys


@dataclass
class FieldStats:
    """Statistics for a single field/column"""
    name: str
    dtype: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: Optional[int] = None
    
    # Numeric stats
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    
    # Categorical stats
    mode: Optional[Any] = None
    mode_frequency: Optional[int] = None
    top_values: Optional[Dict[str, int]] = None
    
    # String stats
    avg_length: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class DomainShape:
    """Description of the domain's structure"""
    source_type: str  # 'csv', 'json', 'excel', 'parquet', etc.
    source_path: str
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    memory_usage: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DomainStatsAgent:
    """Agent that discovers domain structure and computes statistics"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.domain_shape: Optional[DomainShape] = None
        self.field_stats: Dict[str, FieldStats] = {}
        self.data: Optional[pd.DataFrame] = None
        
    def log(self, message: str):
        """Print message if verbose mode is on"""
        if self.verbose:
            print(f"[Agent] {message}")
    
    def discover_domain(self, source: Union[str, Path, pd.DataFrame]) -> DomainShape:
        """
        Discover the structure of the data domain
        
        Args:
            source: File path, URL, or DataFrame
            
        Returns:
            DomainShape object describing the structure
        """
        self.log("🔍 Discovering domain structure...")
        
        # Handle different source types
        if isinstance(source, pd.DataFrame):
            self.data = source
            source_type = "dataframe"
            source_path = "in-memory"
        else:
            source = Path(source)
            source_path = str(source)
            
            # Detect file type and load
            if source.suffix.lower() == '.csv':
                source_type = 'csv'
                self.data = pd.read_csv(source)
            elif source.suffix.lower() in ['.xlsx', '.xls']:
                source_type = 'excel'
                self.data = pd.read_excel(source)
            elif source.suffix.lower() == '.json':
                source_type = 'json'
                self.data = pd.read_json(source)
            elif source.suffix.lower() == '.parquet':
                source_type = 'parquet'
                self.data = pd.read_parquet(source)
            elif source.suffix.lower() == '.tsv':
                source_type = 'tsv'
                self.data = pd.read_csv(source, sep='\t')
            else:
                raise ValueError(f"Unsupported file type: {source.suffix}")
        
        # Extract shape information
        self.domain_shape = DomainShape(
            source_type=source_type,
            source_path=source_path,
            row_count=len(self.data),
            column_count=len(self.data.columns),
            columns=list(self.data.columns),
            dtypes={col: str(dtype) for col, dtype in self.data.dtypes.items()},
            memory_usage=f"{self.data.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
        )
        
        self.log(f"✓ Domain discovered: {self.domain_shape.row_count} rows × {self.domain_shape.column_count} columns")
        return self.domain_shape
    
    def compute_field_statistics(self, field: str) -> FieldStats:
        """Compute comprehensive statistics for a single field"""
        if self.data is None:
            raise ValueError("No data loaded. Call discover_domain() first.")
        
        series = self.data[field]
        dtype_str = str(series.dtype)
        
        # Basic stats
        stats = FieldStats(
            name=field,
            dtype=dtype_str,
            count=len(series),
            null_count=series.isna().sum(),
            null_percentage=(series.isna().sum() / len(series)) * 100,
            unique_count=series.nunique()
        )
        
        # Remove nulls for further analysis
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return stats
        
        # Numeric statistics (exclude boolean)
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            stats.mean = float(non_null.mean())
            stats.median = float(non_null.median())
            stats.std = float(non_null.std())
            stats.min = float(non_null.min())
            stats.max = float(non_null.max())
            stats.q25 = float(non_null.quantile(0.25))
            stats.q75 = float(non_null.quantile(0.75))
        
        # Categorical statistics (for all types with reasonable cardinality)
        if stats.unique_count and stats.unique_count < len(non_null) * 0.5:
            value_counts = non_null.value_counts()
            stats.mode = value_counts.index[0]
            stats.mode_frequency = int(value_counts.iloc[0])
            stats.top_values = {
                str(k): int(v) for k, v in value_counts.head(10).items()
            }
        
        # String statistics
        if pd.api.types.is_string_dtype(series) or dtype_str == 'object':
            str_series = non_null.astype(str)
            lengths = str_series.str.len()
            stats.avg_length = float(lengths.mean())
            stats.min_length = int(lengths.min())
            stats.max_length = int(lengths.max())
        
        return stats
    
    def compute_all_statistics(self) -> Dict[str, FieldStats]:
        """Compute statistics for all fields in the domain"""
        if self.data is None:
            raise ValueError("No data loaded. Call discover_domain() first.")
        
        self.log("📊 Computing statistics for all fields...")
        
        for column in self.data.columns:
            self.log(f"  Analyzing: {column}")
            self.field_stats[column] = self.compute_field_statistics(column)
        
        self.log(f"✓ Statistics computed for {len(self.field_stats)} fields")
        return self.field_stats
    
    def get_summary_report(self) -> str:
        """Generate a human-readable summary report"""
        if not self.domain_shape or not self.field_stats:
            return "No analysis performed yet. Run analyze() first."
        
        lines = []
        lines.append("=" * 80)
        lines.append("DOMAIN STATISTICS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Domain shape
        lines.append("Domain Shape:")
        lines.append(f"  Source: {self.domain_shape.source_path} ({self.domain_shape.source_type})")
        lines.append(f"  Dimensions: {self.domain_shape.row_count:,} rows × {self.domain_shape.column_count} columns")
        lines.append(f"  Memory: {self.domain_shape.memory_usage}")
        lines.append("")
        
        # Field statistics
        lines.append("Field Statistics:")
        lines.append("-" * 80)
        
        for field_name, stats in self.field_stats.items():
            lines.append(f"\n[{field_name}] ({stats.dtype})")
            lines.append(f"  Records: {stats.count:,} | Nulls: {stats.null_count:,} ({stats.null_percentage:.1f}%)")
            lines.append(f"  Unique: {stats.unique_count:,}")
            
            if stats.mean is not None:
                lines.append(f"  Mean: {stats.mean:.2f} | Median: {stats.median:.2f} | Std: {stats.std:.2f}")
                lines.append(f"  Range: [{stats.min:.2f}, {stats.max:.2f}]")
                lines.append(f"  Quartiles: Q1={stats.q25:.2f}, Q3={stats.q75:.2f}")
            
            if stats.mode is not None:
                lines.append(f"  Mode: {stats.mode} (appears {stats.mode_frequency:,} times)")
            
            if stats.avg_length is not None:
                lines.append(f"  String length: avg={stats.avg_length:.1f}, range=[{stats.min_length}, {stats.max_length}]")
            
            if stats.top_values:
                lines.append("  Top values:")
                for value, count in list(stats.top_values.items())[:5]:
                    pct = (count / stats.count) * 100
                    lines.append(f"    • {value}: {count:,} ({pct:.1f}%)")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def analyze(self, source: Union[str, Path, pd.DataFrame]) -> Dict[str, Any]:
        """
        Complete analysis: discover structure and compute statistics
        
        Returns a dictionary with all results
        """
        # Discover the domain
        shape = self.discover_domain(source)
        
        # Compute statistics
        stats = self.compute_all_statistics()
        
        return {
            'shape': shape.to_dict(),
            'statistics': {name: asdict(stat) for name, stat in stats.items()}
        }
    
    def export_report(self, output_path: Union[str, Path], format: str = 'json'):
        """Export the analysis report to a file"""
        output_path = Path(output_path)
        
        if format == 'json':
            report = {
                'shape': self.domain_shape.to_dict() if self.domain_shape else None,
                'statistics': {name: asdict(stat) for name, stat in self.field_stats.items()}
            }
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.log(f"✓ Report exported to {output_path}")
        
        elif format == 'txt':
            with open(output_path, 'w') as f:
                f.write(self.get_summary_report())
            self.log(f"✓ Report exported to {output_path}")
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python domain_stats_agent.py <data_file>")
        print("\nExample with sample data:")
        
        # Create sample data
        sample_data = pd.DataFrame({
            'id': range(1, 101),
            'name': [f'User_{i}' for i in range(1, 101)],
            'age': np.random.randint(18, 80, 100),
            'score': np.random.normal(75, 15, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'active': np.random.choice([True, False], 100),
        })
        
        # Add some nulls
        sample_data.loc[sample_data.sample(10).index, 'score'] = np.nan
        
        print("\n--- Analyzing sample dataset ---\n")
        agent = DomainStatsAgent(verbose=True)
        agent.analyze(sample_data)
        print("\n" + agent.get_summary_report())
        
        return
    
    # Analyze provided file
    file_path = sys.argv[1]
    agent = DomainStatsAgent(verbose=True)
    
    try:
        agent.analyze(file_path)
        print("\n" + agent.get_summary_report())
        
        # Export to JSON
        output_json = Path(file_path).stem + "_stats.json"
        agent.export_report(output_json, format='json')
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
