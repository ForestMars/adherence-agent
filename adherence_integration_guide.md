# Integrating Domain Statistics Agent with Adherence Agent

## Integration Architecture

This guide shows how to integrate the Domain Statistics Agent into the adherence-agent healthcare system for comprehensive patient compliance tracking and analysis.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ADHERENCE AGENT SYSTEM                             │
│                                                                       │
│  ┌─────────────────┐         ┌─────────────────┐                    │
│  │ Operational     │────────→│ Compliance Score│                    │
│  │ Agent           │         │ Database         │                    │
│  │ (Calls)         │         └────────┬────────┘                    │
│  └─────────────────┘                  │                             │
│                                        │                             │
│                                        ↓                             │
│         ┌──────────────────────────────────────────┐                │
│         │   DOMAIN STATISTICS AGENT                │                │
│         │   - Discover data shape                  │                │
│         │   - Compute cohort statistics            │                │
│         │   - Track metric trends                  │                │
│         │   - Quality validation                   │                │
│         └─────────┬────────────────────────────────┘                │
│                   │                                                  │
│         ┌─────────▼──────────┐     ┌──────────────────┐            │
│         │ Statistical Reports│     │ Analyst Agent    │            │
│         │ - Cohort summaries │────→│ (Hypothesis &    │            │
│         │ - Trend analysis   │     │  Prediction)     │            │
│         │ - Data quality     │     └──────────────────┘            │
│         └────────────────────┘                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Key Integration Points

### 1. Pre-Analysis Data Quality Gate

**Use Case**: Validate data quality before running expensive predictive models

**Benefits**:
- Catch data collection issues early
- Prevent model training on incomplete/corrupted data
- Reduce wasted compute on low-quality data
- Track data quality trends over time

**Implementation**:
```python
# Before analyst agent runs hypothesis testing
validator = AdherenceDataValidator()
is_valid, issues = validator.validate_compliance_data('compliance_events.csv')

if not is_valid:
    logger.warning(f"Data quality issues detected: {issues}")
    # Fix issues before proceeding to model generation
else:
    # Proceed with analyst agent
    analyst_agent.generate_readmission_model()
```

### 2. Automated Cohort Profiling

**Use Case**: Understand cohort characteristics before intervention

**Benefits**:
- Quick statistical overview of patient populations
- Identify high-risk subgroups automatically
- Track compliance distribution changes
- Measure intervention effectiveness

**Implementation**:
```python
# Daily cohort analysis
analyzer = AdherenceCohortAnalyzer(db_connection_string)
profile = analyzer.analyze_cohort('diabetes_patients', lookback_days=30)

print(f"Cohort size: {profile.total_patients}")
print(f"Avg compliance: {profile.statistical_summary['avg_compliance']:.1%}")
print(f"High-risk patients: {profile.risk_stratification['high_risk']}")
```

### 3. Trend Monitoring & Alert System

**Use Case**: Detect degrading compliance patterns in real-time

**Benefits**:
- Early warning system for cohort deterioration
- Track seasonal patterns in adherence
- Measure impact of policy changes
- Automated reporting for clinical teams

**Implementation**:
```python
# Track compliance score trends over time
trends = analyzer.track_metric_trends(
    cohort_id='hypertension_patients',
    metric='compliance_score',
    time_windows=[7, 30, 90]
)

# Alert if 7-day average drops significantly from 30-day
if trends.loc[0, 'mean'] < trends.loc[1, 'mean'] - 0.15:
    alert_clinical_team(f"Compliance drop detected in hypertension cohort")
```

### 4. A/B Testing & Intervention Measurement

**Use Case**: Compare outcomes between intervention and control groups

**Benefits**:
- Statistically validate intervention effectiveness
- Track ROI of different adherence strategies
- Identify which patient segments respond to interventions
- Generate evidence for clinical decision-making

**Implementation**:
```python
# Compare intervention cohort vs control
comparison = analyzer.compare_cohorts(
    cohort_a='control_group',
    cohort_b='sms_reminder_intervention'
)

print(f"Compliance improvement: {comparison['compliance_delta']['mean']:.1%}")
print(f"High-risk reduction: {comparison['risk_distribution_change']['high_risk']}")
```

## Detailed Integration Examples

### Example 1: Daily Data Quality Pipeline

**File: `daily_quality_check.py`**

```python
#!/usr/bin/env python3
"""
Daily data quality validation for adherence monitoring
Runs before analyst agent to ensure data integrity
"""

from domain_stats_agent import DomainStatsAgent
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyQualityCheck:
    """Daily data quality validation pipeline"""
    
    CRITICAL_FIELDS = {
        'patient_id': {'null_threshold': 0.0, 'unique_ratio_min': 0.95},
        'compliance_score': {'null_threshold': 5.0, 'range': (0.0, 1.0)},
        'medication_adherence': {'null_threshold': 10.0, 'range': (0.0, 1.0)},
        'timestamp': {'null_threshold': 0.0}
    }
    
    def __init__(self, data_source: str):
        self.agent = DomainStatsAgent(verbose=False)
        self.data_source = data_source
        
    def run_quality_checks(self) -> bool:
        """
        Run comprehensive quality checks on yesterday's data
        
        Returns:
            True if all checks pass, False otherwise
        """
        logger.info("Starting daily quality check...")
        
        # Load yesterday's data
        yesterday = datetime.now() - timedelta(days=1)
        self.agent.analyze(self.data_source)
        
        all_passed = True
        
        # Check 1: Required fields present
        if not self._check_required_fields():
            all_passed = False
            
        # Check 2: Null percentages within limits
        if not self._check_null_thresholds():
            all_passed = False
            
        # Check 3: Data ranges valid
        if not self._check_value_ranges():
            all_passed = False
            
        # Check 4: No duplicate patient IDs (per timestamp)
        if not self._check_duplicates():
            all_passed = False
            
        if all_passed:
            logger.info("✓ All quality checks passed")
        else:
            logger.error("✗ Quality checks failed - review issues above")
            
        return all_passed
    
    def _check_required_fields(self) -> bool:
        """Verify all critical fields are present"""
        missing = []
        for field in self.CRITICAL_FIELDS.keys():
            if field not in self.agent.field_stats:
                missing.append(field)
        
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return False
        return True
    
    def _check_null_thresholds(self) -> bool:
        """Check null percentages don't exceed thresholds"""
        failures = []
        
        for field, constraints in self.CRITICAL_FIELDS.items():
            if 'null_threshold' not in constraints:
                continue
                
            stat = self.agent.field_stats.get(field)
            if not stat:
                continue
                
            if stat.null_percentage > constraints['null_threshold']:
                failures.append(
                    f"{field}: {stat.null_percentage:.1f}% null "
                    f"(limit: {constraints['null_threshold']}%)"
                )
        
        if failures:
            logger.error(f"Null threshold violations: {failures}")
            return False
        return True
    
    def _check_value_ranges(self) -> bool:
        """Check numeric fields are within expected ranges"""
        failures = []
        
        for field, constraints in self.CRITICAL_FIELDS.items():
            if 'range' not in constraints:
                continue
                
            stat = self.agent.field_stats.get(field)
            if not stat or stat.min is None:
                continue
                
            min_val, max_val = constraints['range']
            
            if stat.min < min_val or stat.max > max_val:
                failures.append(
                    f"{field}: range [{stat.min:.2f}, {stat.max:.2f}] "
                    f"outside expected [{min_val}, {max_val}]"
                )
        
        if failures:
            logger.error(f"Value range violations: {failures}")
            return False
        return True
    
    def _check_duplicates(self) -> bool:
        """Check for unexpected duplicate records"""
        patient_id_stat = self.agent.field_stats.get('patient_id')
        if not patient_id_stat:
            return True
            
        unique_ratio = patient_id_stat.unique_count / patient_id_stat.count
        expected_min = self.CRITICAL_FIELDS['patient_id']['unique_ratio_min']
        
        if unique_ratio < expected_min:
            logger.error(
                f"Too many duplicate patient_ids: {unique_ratio:.1%} unique "
                f"(expected >{expected_min:.1%})"
            )
            return False
            
        return True


if __name__ == '__main__':
    checker = DailyQualityCheck('compliance_events.csv')
    passed = checker.run_quality_checks()
    
    if not passed:
        # Send alert to clinical team
        import sys
        sys.exit(1)
```

### Example 2: Cohort Statistical Dashboard

**File: `cohort_dashboard.py`**

```python
#!/usr/bin/env python3
"""
Generate statistical dashboard for clinical review
Integrates with adherence-agent's analyst agent
"""

from domain_stats_agent import ExtendedDomainStatsAgent
from typing import Dict, List
import json
from datetime import datetime


class CohortDashboard:
    """Generate statistical dashboards for clinical teams"""
    
    def __init__(self, db_connection: str):
        self.db_conn = db_connection
        self.agent = ExtendedDomainStatsAgent(verbose=False)
        
    def generate_dashboard(self, cohort_ids: List[str]) -> Dict:
        """
        Generate multi-cohort statistical dashboard
        
        Args:
            cohort_ids: List of cohorts to include
            
        Returns:
            Dashboard data structure
        """
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'cohorts': {}
        }
        
        for cohort_id in cohort_ids:
            dashboard['cohorts'][cohort_id] = self._analyze_single_cohort(cohort_id)
        
        # Add cross-cohort comparison
        dashboard['comparison'] = self._compare_cohorts(cohort_ids)
        
        return dashboard
    
    def _analyze_single_cohort(self, cohort_id: str) -> Dict:
        """Analyze a single cohort"""
        
        query = f"""
        SELECT 
            patient_id,
            compliance_score,
            medication_adherence,
            appointment_adherence,
            escalation_count,
            readmission_30day,
            estimated_cost,
            qol_score
        FROM adherence_data
        WHERE cohort_id = '{cohort_id}'
            AND timestamp >= NOW() - INTERVAL '30 days'
        """
        
        self.agent.discover_database(self.db_conn, query)
        stats = self.agent.compute_all_statistics()
        
        return {
            'total_patients': self.agent.domain_shape.row_count,
            'compliance': {
                'mean': stats['compliance_score'].mean,
                'median': stats['compliance_score'].median,
                'distribution': stats['compliance_score'].top_values if stats['compliance_score'].top_values else {}
            },
            'medication_adherence': {
                'mean': stats['medication_adherence'].mean,
                'below_target': len(self.agent.data[
                    self.agent.data['medication_adherence'] < 0.8
                ])
            },
            'outcomes': {
                'readmission_rate': stats['readmission_30day'].mean if stats.get('readmission_30day') else None,
                'avg_qol': stats.get('qol_score', type('obj', (), {'mean': None})).mean
            },
            'costs': {
                'avg_cost_per_patient': stats.get('estimated_cost', type('obj', (), {'mean': None})).mean
            }
        }
    
    def _compare_cohorts(self, cohort_ids: List[str]) -> Dict:
        """Compare metrics across cohorts"""
        comparison = {
            'compliance_means': {},
            'readmission_rates': {},
            'avg_costs': {}
        }
        
        # This would be populated based on individual cohort analyses
        # Placeholder for demonstration
        return comparison
    
    def export_html_report(self, cohort_ids: List[str], output_file: str):
        """Export dashboard as HTML report"""
        dashboard = self.generate_dashboard(cohort_ids)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Adherence Monitoring Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .cohort {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>Adherence Monitoring Dashboard</h1>
    <p>Generated: {dashboard['generated_at']}</p>
"""
        
        for cohort_id, data in dashboard['cohorts'].items():
            html += f"""
    <div class="cohort">
        <h2>{cohort_id}</h2>
        <div class="metric">
            <div class="metric-value">{data['total_patients']}</div>
            <div class="metric-label">Total Patients</div>
        </div>
        <div class="metric">
            <div class="metric-value">{data['compliance']['mean']:.1%}</div>
            <div class="metric-label">Avg Compliance</div>
        </div>
        <div class="metric">
            <div class="metric-value">{data['medication_adherence']['below_target']}</div>
            <div class="metric-label">Below Target</div>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(output_file, 'w') as f:
            f.write(html)


if __name__ == '__main__':
    dashboard = CohortDashboard('postgresql://localhost/adherence_db')
    dashboard.export_html_report(
        cohort_ids=['diabetes', 'hypertension', 'copd'],
        output_file='cohort_dashboard.html'
    )
```

### Example 3: Feeding Analyst Agent with Curated Data

**File: `analyst_agent_integration.py`**

```python
#!/usr/bin/env python3
"""
Integration layer between Domain Statistics Agent and Analyst Agent
Provides curated, validated data for hypothesis generation
"""

from domain_stats_agent import DomainStatsAgent
from typing import Dict, Optional
import pandas as pd


class AnalystAgentDataProvider:
    """
    Prepares and validates data for the Analyst Agent
    Acts as quality gate between raw data and hypothesis generation
    """
    
    def __init__(self, db_connection: str):
        self.db_conn = db_connection
        self.stats_agent = DomainStatsAgent(verbose=True)
        
    def prepare_dataset_for_hypothesis(
        self,
        hypothesis_type: str,
        cohort_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Prepare validated dataset for hypothesis testing
        
        Args:
            hypothesis_type: Type of hypothesis ('readmission', 'compliance', 'cost')
            cohort_filter: Optional SQL WHERE clause to filter cohort
            
        Returns:
            Validated pandas DataFrame ready for analysis
        """
        # Build query based on hypothesis type
        query = self._build_query_for_hypothesis(hypothesis_type, cohort_filter)
        
        # Load and validate
        self.stats_agent.discover_database(self.db_conn, query)
        
        # Run quality checks
        if not self._validate_for_analysis():
            raise ValueError("Data quality insufficient for hypothesis testing")
        
        # Return curated dataset
        return self.stats_agent.data
    
    def _build_query_for_hypothesis(
        self,
        hypothesis_type: str,
        cohort_filter: Optional[str]
    ) -> str:
        """Build SQL query based on hypothesis requirements"""
        
        base_query = """
        SELECT 
            p.patient_id,
            p.age,
            p.gender,
            p.diagnosis_codes,
            cp.complexity_score,
            cp.medication_count,
            ce.compliance_score,
            ce.medication_adherence,
            ce.appointment_adherence,
            ce.escalation_count,
            o.readmission_30day,
            o.emergency_visits,
            o.estimated_cost,
            o.qol_score
        FROM patients p
        JOIN care_plans cp ON p.care_plan_id = cp.plan_id
        JOIN compliance_events ce ON p.patient_id = ce.patient_id
        LEFT JOIN outcomes o ON p.patient_id = o.patient_id
        """
        
        if cohort_filter:
            base_query += f" WHERE {cohort_filter}"
        
        return base_query
    
    def _validate_for_analysis(self) -> bool:
        """
        Validate data meets requirements for analysis
        
        Returns:
            True if data is suitable for hypothesis testing
        """
        stats = self.stats_agent.field_stats
        
        # Minimum sample size
        if self.stats_agent.domain_shape.row_count < 100:
            print("WARNING: Sample size too small (<100 patients)")
            return False
        
        # Critical fields must have <5% nulls
        critical_fields = ['compliance_score', 'medication_adherence']
        for field in critical_fields:
            if field not in stats:
                print(f"ERROR: Missing critical field: {field}")
                return False
            
            if stats[field].null_percentage > 5.0:
                print(f"ERROR: {field} has {stats[field].null_percentage:.1f}% nulls")
                return False
        
        # Sufficient variance in outcome variables
        if 'readmission_30day' in stats:
            if stats['readmission_30day'].unique_count < 2:
                print("WARNING: No variance in readmission outcomes")
                return False
        
        return True
    
    def get_data_summary_for_analyst(self) -> Dict:
        """
        Provide statistical summary to help Analyst Agent understand data
        
        Returns:
            Dict with key statistics and distributions
        """
        return {
            'sample_size': self.stats_agent.domain_shape.row_count,
            'feature_count': self.stats_agent.domain_shape.column_count,
            'features': list(self.stats_agent.domain_shape.columns),
            'key_statistics': {
                field: {
                    'mean': stat.mean,
                    'std': stat.std,
                    'null_pct': stat.null_percentage,
                    'unique_count': stat.unique_count
                }
                for field, stat in self.stats_agent.field_stats.items()
                if stat.mean is not None
            },
            'data_quality_score': self._calculate_quality_score()
        }
    
    def _calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)"""
        # Average completeness across all fields
        avg_completeness = 100 - sum(
            stat.null_percentage 
            for stat in self.stats_agent.field_stats.values()
        ) / len(self.stats_agent.field_stats)
        
        return avg_completeness


# Example usage with existing analyst_agent.py
if __name__ == '__main__':
    # Initialize data provider
    provider = AnalystAgentDataProvider('postgresql://localhost/adherence_db')
    
    # Prepare data for readmission hypothesis
    data = provider.prepare_dataset_for_hypothesis(
        hypothesis_type='readmission',
        cohort_filter="p.diagnosis_codes LIKE '%diabetes%'"
    )
    
    # Get summary for analyst agent
    summary = provider.get_data_summary_for_analyst()
    print(f"Dataset ready: {summary['sample_size']} patients, "
          f"quality score: {summary['data_quality_score']:.1f}/100")
    
    # Now pass to existing analyst agent for hypothesis generation
    # from analyst_agent import AnalystAgent
    # analyst = AnalystAgent()
    # hypothesis = analyst.generate_hypothesis(data, summary)
```

## Recommended Deployment Strategy

### Phase 1: Data Quality Monitoring (Week 1-2)
1. Deploy daily quality checks
2. Establish baseline statistics for all cohorts
3. Set up automated alerting for quality issues

### Phase 2: Cohort Profiling (Week 3-4)
1. Integrate cohort analysis into weekly reporting
2. Create dashboards for clinical teams
3. Validate statistical outputs against manual calculations

### Phase 3: Analyst Agent Integration (Week 5-6)
1. Add data provider layer before analyst agent
2. Use Domain Stats Agent as quality gate
3. Track how data quality impacts model performance

### Phase 4: Automated Reporting (Week 7-8)
1. Generate automated weekly cohort reports
2. Implement A/B test comparison framework
3. Build clinical decision support dashboards

## Benefits Summary

### For Operational Efficiency
- **Reduce manual data analysis**: Automated statistical profiling saves 10-15 hours/week
- **Catch data issues early**: Prevent expensive model retraining on bad data
- **Faster hypothesis validation**: Quick statistical checks before deep analysis

### For Clinical Teams
- **Better visibility**: Clear statistical summaries of patient cohorts
- **Data-driven decisions**: Objective metrics for intervention effectiveness
- **Risk stratification**: Automatic identification of high-risk patient segments

### For Data Science
- **Data quality assurance**: Systematic validation before modeling
- **Feature discovery**: Statistical profiling may reveal relevant patterns
- **Model monitoring**: Track input data drift over time

## Next Steps

1. **Start small**: Begin with daily quality checks on one cohort
2. **Iterate**: Add more sophisticated analysis as you validate outputs
3. **Integrate gradually**: Connect to analyst agent once comfortable with stats
4. **Measure impact**: Track time savings and data quality improvements

## Support & Questions

The Domain Statistics Agent is designed to be a lightweight, flexible tool that integrates easily with your existing adherence-agent infrastructure. For questions about specific integration patterns or custom analysis needs, feel free to extend the base classes provided.