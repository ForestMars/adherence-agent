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