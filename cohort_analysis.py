#!/usr/bin/env python3
"""
Cohort Analysis Module for Adherence Agent
Integrates Domain Statistics Agent for patient cohort profiling
"""

from domain_stats_agent import DomainStatsAgent
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CohortProfile:
    """Statistical profile of a patient cohort"""
    cohort_id: str
    analysis_date: datetime
    total_patients: int
    compliance_distribution: Dict[str, int]
    risk_stratification: Dict[str, int]
    data_quality_score: float
    completeness_by_field: Dict[str, float]
    statistical_summary: Dict
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['analysis_date'] = self.analysis_date.isoformat()
        return result


class AdherenceCohortAnalyzer:
    """
    Specialized analyzer for patient adherence cohorts
    Uses Domain Statistics Agent for automated profiling
    """
    
    # Risk thresholds
    HIGH_RISK_COMPLIANCE_THRESHOLD = 0.6
    MEDIUM_RISK_COMPLIANCE_THRESHOLD = 0.8
    HIGH_RISK_ESCALATION_THRESHOLD = 2
    
    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize cohort analyzer
        
        Args:
            db_connection_string: SQLAlchemy connection string (optional)
        """
        self.db_conn = db_connection_string
        self.stats_agent = DomainStatsAgent(verbose=True)
        
    def analyze_cohort(self, 
                      cohort_id: str,
                      data_source: Optional[str] = None,
                      lookback_days: int = 90) -> CohortProfile:
        """
        Analyze a patient cohort using domain statistics
        
        Args:
            cohort_id: Identifier for the patient cohort
            data_source: File path or DataFrame (if not using database)
            lookback_days: Days of historical data to analyze
        
        Returns:
            CohortProfile with comprehensive statistics
        """
        logger.info(f"Analyzing cohort: {cohort_id}")
        
        # Load data from appropriate source
        if data_source is not None:
            # Use file or DataFrame
            self.stats_agent.analyze(data_source)
        elif self.db_conn is not None:
            # Query from database - note: requires sqlalchemy
            # For now, raise informative error
            raise NotImplementedError(
                "Database connection requires sqlalchemy. "
                "Install with: pip install sqlalchemy"
            )
        else:
            raise ValueError("Must provide either data_source or db_connection_string")
        
        # Build comprehensive profile
        profile = self._build_cohort_profile(
            cohort_id,
            self.stats_agent.field_stats,
            self.stats_agent.data
        )
        
        logger.info(f"✓ Cohort analysis complete: {profile.total_patients} patients")
        return profile
    
    def _build_cohort_query(self, cohort_id: str, lookback_days: int) -> str:
        """Build SQL query for cohort data"""
        return f"""
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
            ce.lifestyle_goal_adherence,
            ce.last_contact_date,
            ce.escalation_count,
            o.readmission_30day,
            o.emergency_visits,
            o.qol_score,
            o.estimated_cost
        FROM patients p
        JOIN care_plans cp ON p.care_plan_id = cp.plan_id
        JOIN compliance_events ce ON p.patient_id = ce.patient_id
        LEFT JOIN outcomes o ON p.patient_id = o.patient_id
        WHERE p.cohort_id = '{cohort_id}'
            AND ce.timestamp >= CURRENT_DATE - INTERVAL '{lookback_days} days'
        """
    
    def _build_cohort_profile(self,
                             cohort_id: str,
                             field_stats: Dict,
                             data: pd.DataFrame) -> CohortProfile:
        """Build cohort profile from statistical analysis"""
        
        # Compliance distribution
        compliance_dist = {
            'high_compliance (>80%)': 0,
            'moderate_compliance (60-80%)': 0,
            'low_compliance (<60%)': 0
        }
        
        if 'compliance_score' in data.columns:
            compliance_dist['high_compliance (>80%)'] = len(
                data[data['compliance_score'] > self.MEDIUM_RISK_COMPLIANCE_THRESHOLD]
            )
            compliance_dist['moderate_compliance (60-80%)'] = len(
                data[
                    (data['compliance_score'] >= self.HIGH_RISK_COMPLIANCE_THRESHOLD) & 
                    (data['compliance_score'] <= self.MEDIUM_RISK_COMPLIANCE_THRESHOLD)
                ]
            )
            compliance_dist['low_compliance (<60%)'] = len(
                data[data['compliance_score'] < self.HIGH_RISK_COMPLIANCE_THRESHOLD]
            )
        
        # Risk stratification based on compliance and escalations
        risk_strat = {'high_risk': 0, 'medium_risk': 0, 'low_risk': 0}
        
        if 'compliance_score' in data.columns:
            # High risk: low compliance OR multiple escalations
            high_risk_mask = (
                (data['compliance_score'] < self.HIGH_RISK_COMPLIANCE_THRESHOLD) |
                (data.get('escalation_count', 0) > self.HIGH_RISK_ESCALATION_THRESHOLD)
            )
            risk_strat['high_risk'] = high_risk_mask.sum()
            
            # Medium risk: moderate compliance
            medium_risk_mask = (
                (data['compliance_score'] >= self.HIGH_RISK_COMPLIANCE_THRESHOLD) & 
                (data['compliance_score'] < self.MEDIUM_RISK_COMPLIANCE_THRESHOLD) &
                (~high_risk_mask)
            )
            risk_strat['medium_risk'] = medium_risk_mask.sum()
            
            # Low risk: high compliance
            risk_strat['low_risk'] = len(data) - risk_strat['high_risk'] - risk_strat['medium_risk']
        
        # Data quality score (inverse of average null percentage)
        quality_score = 100 - sum(
            stat.null_percentage for stat in field_stats.values()
        ) / len(field_stats) if field_stats else 0
        
        # Completeness by field
        completeness = {
            name: 100 - stat.null_percentage 
            for name, stat in field_stats.items()
        }
        
        # Statistical summary
        summary = {}
        
        if 'compliance_score' in field_stats:
            cs = field_stats['compliance_score']
            summary['avg_compliance'] = cs.mean
            summary['median_compliance'] = cs.median
            summary['std_compliance'] = cs.std
        
        if 'age' in field_stats:
            summary['avg_age'] = field_stats['age'].mean
        
        if 'readmission_30day' in data.columns:
            summary['readmission_rate'] = data['readmission_30day'].mean()
        
        if 'qol_score' in field_stats:
            summary['avg_qol_score'] = field_stats['qol_score'].mean
        
        if 'estimated_cost' in field_stats:
            summary['avg_cost_per_patient'] = field_stats['estimated_cost'].mean
        
        return CohortProfile(
            cohort_id=cohort_id,
            analysis_date=datetime.now(),
            total_patients=len(data),
            compliance_distribution=compliance_dist,
            risk_stratification=risk_strat,
            data_quality_score=quality_score,
            completeness_by_field=completeness,
            statistical_summary=summary
        )
    
    def compare_cohorts(self, cohort_a: str, cohort_b: str, 
                       source_a: Optional[str] = None,
                       source_b: Optional[str] = None) -> Dict:
        """
        Compare two cohorts statistically
        
        Useful for:
        - Control vs intervention groups
        - Different time periods
        - Different patient populations
        
        Args:
            cohort_a: First cohort ID
            cohort_b: Second cohort ID
            source_a: Data source for cohort A (optional if using DB)
            source_b: Data source for cohort B (optional if using DB)
        
        Returns:
            Dictionary with comparison metrics
        """
        logger.info(f"Comparing cohorts: {cohort_a} vs {cohort_b}")
        
        profile_a = self.analyze_cohort(cohort_a, data_source=source_a)
        profile_b = self.analyze_cohort(cohort_b, data_source=source_b)
        
        comparison = {
            'cohort_a': cohort_a,
            'cohort_b': cohort_b,
            'size_difference': profile_b.total_patients - profile_a.total_patients,
            'size_ratio': profile_b.total_patients / profile_a.total_patients if profile_a.total_patients > 0 else None,
            'compliance_delta': {},
            'quality_score_delta': profile_b.data_quality_score - profile_a.data_quality_score,
            'risk_distribution_change': {},
            'outcome_improvements': {}
        }
        
        # Compliance deltas
        if 'avg_compliance' in profile_a.statistical_summary and 'avg_compliance' in profile_b.statistical_summary:
            comparison['compliance_delta'] = {
                'mean': profile_b.statistical_summary['avg_compliance'] - 
                       profile_a.statistical_summary['avg_compliance'],
                'median': profile_b.statistical_summary.get('median_compliance', 0) - 
                         profile_a.statistical_summary.get('median_compliance', 0),
                'improvement_pct': (
                    (profile_b.statistical_summary['avg_compliance'] - 
                     profile_a.statistical_summary['avg_compliance']) /
                    profile_a.statistical_summary['avg_compliance'] * 100
                ) if profile_a.statistical_summary['avg_compliance'] > 0 else None
            }
        
        # Risk distribution changes
        for risk_level in ['high_risk', 'medium_risk', 'low_risk']:
            comparison['risk_distribution_change'][risk_level] = (
                profile_b.risk_stratification.get(risk_level, 0) - 
                profile_a.risk_stratification.get(risk_level, 0)
            )
        
        # Outcome improvements
        if 'readmission_rate' in profile_a.statistical_summary and 'readmission_rate' in profile_b.statistical_summary:
            comparison['outcome_improvements']['readmission_reduction'] = (
                profile_a.statistical_summary['readmission_rate'] -
                profile_b.statistical_summary['readmission_rate']
            )
        
        if 'avg_cost_per_patient' in profile_a.statistical_summary and 'avg_cost_per_patient' in profile_b.statistical_summary:
            comparison['outcome_improvements']['cost_reduction'] = (
                profile_a.statistical_summary['avg_cost_per_patient'] -
                profile_b.statistical_summary['avg_cost_per_patient']
            )
        
        logger.info("✓ Cohort comparison complete")
        return comparison
    
    def track_metric_trends(self,
                          cohort_id: str,
                          metric: str,
                          time_windows: List[int],
                          data_source: Optional[str] = None) -> pd.DataFrame:
        """
        Track how a metric changes over different time windows
        
        Args:
            cohort_id: Cohort to analyze
            metric: Field to track (e.g., 'compliance_score')
            time_windows: List of lookback days (e.g., [7, 30, 90])
            data_source: File path or DataFrame (if not using database)
        
        Returns:
            DataFrame with metric statistics over time
        """
        logger.info(f"Tracking {metric} trends for cohort {cohort_id}")
        
        trends = []
        
        for days in time_windows:
            # Analyze for this time window
            if data_source is not None:
                # For file-based, we'd need to filter the data
                # This is simplified - in practice, filter by date column
                profile = self.analyze_cohort(cohort_id, data_source=data_source)
            else:
                profile = self.analyze_cohort(cohort_id, lookback_days=days)
            
            # Extract metric statistics
            if metric in self.stats_agent.field_stats:
                stat = self.stats_agent.field_stats[metric]
                trends.append({
                    'time_window_days': days,
                    'mean': stat.mean,
                    'median': stat.median,
                    'std': stat.std,
                    'min': stat.min,
                    'max': stat.max,
                    'null_pct': stat.null_percentage,
                    'sample_size': stat.count
                })
        
        trend_df = pd.DataFrame(trends)
        logger.info(f"✓ Trend analysis complete for {len(time_windows)} time windows")
        return trend_df
    
    def generate_report(self, cohort_id: str, 
                       data_source: Optional[str] = None) -> str:
        """
        Generate human-readable report for a cohort
        
        Args:
            cohort_id: Cohort to report on
            data_source: Data source (optional if using DB)
        
        Returns:
            Formatted report string
        """
        profile = self.analyze_cohort(cohort_id, data_source=data_source)
        
        report = f"""
{'='*80}
ADHERENCE COHORT ANALYSIS REPORT
{'='*80}

Cohort: {profile.cohort_id}
Analysis Date: {profile.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}
Total Patients: {profile.total_patients:,}

COMPLIANCE DISTRIBUTION
{'-'*80}
High Compliance (>80%):    {profile.compliance_distribution.get('high_compliance (>80%)', 0):4d} patients
Moderate Compliance (60-80%): {profile.compliance_distribution.get('moderate_compliance (60-80%)', 0):4d} patients
Low Compliance (<60%):     {profile.compliance_distribution.get('low_compliance (<60%)', 0):4d} patients

RISK STRATIFICATION
{'-'*80}
High Risk:    {profile.risk_stratification.get('high_risk', 0):4d} patients
Medium Risk:  {profile.risk_stratification.get('medium_risk', 0):4d} patients
Low Risk:     {profile.risk_stratification.get('low_risk', 0):4d} patients

STATISTICAL SUMMARY
{'-'*80}
"""
        
        if 'avg_compliance' in profile.statistical_summary:
            report += f"Average Compliance Score: {profile.statistical_summary['avg_compliance']:.1%}\n"
            report += f"Median Compliance Score:  {profile.statistical_summary.get('median_compliance', 0):.1%}\n"
            report += f"Std Dev Compliance:       {profile.statistical_summary.get('std_compliance', 0):.3f}\n\n"
        
        if 'avg_age' in profile.statistical_summary:
            report += f"Average Patient Age: {profile.statistical_summary['avg_age']:.1f} years\n\n"
        
        if 'readmission_rate' in profile.statistical_summary:
            report += f"30-Day Readmission Rate: {profile.statistical_summary['readmission_rate']:.1%}\n"
        
        if 'avg_cost_per_patient' in profile.statistical_summary:
            report += f"Average Cost per Patient: ${profile.statistical_summary['avg_cost_per_patient']:,.2f}\n"
        
        if 'avg_qol_score' in profile.statistical_summary:
            report += f"Average Quality of Life Score: {profile.statistical_summary['avg_qol_score']:.1f}/100\n"
        
        report += f"""
DATA QUALITY
{'-'*80}
Overall Quality Score: {profile.data_quality_score:.1f}/100

Field Completeness:
"""
        
        for field, completeness in sorted(profile.completeness_by_field.items()):
            report += f"  {field:30s} {completeness:5.1f}%\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report


if __name__ == '__main__':
    # Example usage
    print("Adherence Cohort Analyzer - Example Usage\n")
    
    # Create sample data for demonstration
    sample_data = pd.DataFrame({
        'patient_id': [f'P{i:04d}' for i in range(1, 201)],
        'age': np.random.randint(35, 85, 200),
        'compliance_score': np.random.beta(8, 2, 200),  # Skewed toward high compliance
        'medication_adherence': np.random.beta(7, 3, 200),
        'appointment_adherence': np.random.beta(6, 4, 200),
        'escalation_count': np.random.poisson(0.5, 200),
        'readmission_30day': np.random.choice([0, 1], 200, p=[0.85, 0.15]),
        'qol_score': np.random.normal(72, 12, 200).clip(0, 100),
        'estimated_cost': np.random.lognormal(9, 0.5, 200)
    })
    
    # Initialize analyzer
    analyzer = AdherenceCohortAnalyzer()
    
    # Analyze cohort
    print("Analyzing sample cohort...")
    profile = analyzer.analyze_cohort('diabetes_patients', data_source=sample_data)
    
    # Print report
    print(analyzer.generate_report('diabetes_patients', data_source=sample_data))
    
    # Create intervention group with improved compliance
    intervention_data = sample_data.copy()
    intervention_data['compliance_score'] *= 1.15
    intervention_data['compliance_score'] = intervention_data['compliance_score'].clip(0, 1)
    
    # Compare cohorts
    print("\nComparing control vs intervention...")
    comparison = analyzer.compare_cohorts(
        'control',
        'intervention',
        source_a=sample_data,
        source_b=intervention_data
    )
    
    print(f"\nCompliance Improvement: {comparison['compliance_delta'].get('improvement_pct', 0):.1f}%")
    print(f"High-Risk Patients Change: {comparison['risk_distribution_change'].get('high_risk', 0)}")
