# Medication Adherence & Care Plan Compliance Agent

A learning agent system that monitors patient care plan compliance, predicts adverse outcomes, and optimizes for both cost reduction and patient health through iterative data analysis and model generation.

## Overview

This system comprises two cooperating agents operating on patient care plan data:

1. **Operational Agent**: Conducts patient calls to verify care plan compliance (medication adherence, appointment attendance, lifestyle modifications), calculates compliance scores, and escalates clinical concerns.

2. **Analyst Agent**: Performs exploratory analysis to discover novel compliance patterns, generates predictive models for patient outcomes (re-admission, missed appointments, compliance deterioration), and proposes schema extensions when analytical gaps emerge.

Both agents optimize for dual objectives: reducing system costs (preventing avoidable re-admissions, emergency visits) and maximizing patient outcomes (medication effectiveness, quality of life improvements).

## Architecture

```
┌─────────────────────┐
│ Care Plan Templates │
│ (Clinical Protocols)│
└──────────┬──────────┘
           │ instantiated per patient
           ↓
┌──────────────────────┐
│ Patient Care Plan    │──→ ┌─────────────────┐
│ (Individualized)     │    │ Operational     │──→ Structured Data
│ - Medications        │←───│ Agent           │
│ - Appointments       │    │ (Compliance     │
│ - Lifestyle Goals    │    │  Tracking)      │
└──────────────────────┘    └─────────────────┘
                                     │
                                     ↓
                            ┌─────────────────┐
                            │ Compliance Score│
                            │ (Calculated)    │
                            └────────┬────────┘
                                     │
                            ┌────────▼─────────────────┐
                            │ Cohort Data Store        │
                            │ - Compliance history     │
                            │ - Clinical outcomes      │
                            │ - Cost data              │
                            └────────┬─────────────────┘
                                     │
                                     ↓
                            ┌─────────────────┐
                            │ Analyst Agent   │
                            │ (Exploration &  │
                            │  Prediction)    │
                            └────────┬────────┘
                                     │
          ┌──────────────────────────┼──────────────────────┐
          ↓                          ↓                      ↓
   ┌─────────────┐         ┌──────────────────┐    ┌──────────────┐
   │ Predictive  │         │ Hypothesis       │    │ Schema       │
   │ Models      │         │ Generation       │    │ Proposals    │
   │ - Re-admit  │         │ - Compliance     │    └──────┬───────┘
   │ - Compliance│         │ - Cost drivers   │           │
   │ - Outcomes  │         │ - Interventions  │           ↓
   └─────────────┘         └──────────────────┘    ┌──────────────┐
                                                   │ Collibra API │
                                                   └──────────────┘

External Integrations:
┌──────────────┐  ┌──────────────┐
│ FHIR (HL7)   │  │ Epic (Fyre)  │
│ - EHR Data   │  │ - Scheduling │
│ - Clinical   │  │ - Care Plans │
└──────────────┘  └──────────────┘
```

## Files 
```
medication-agent/
├── agent.py                 # Agent orchestration (provider-agnostic)
├── protocol.py              # Goal and guidelines
├── state.py                 # State management
├── llm.py                   # Abstract LLM interface
├── providers.py             # API endpoint implementations
├── main.py                  # Entry point
├── requirements.txt
└── README.md
```
## Design Principles

**Care Plan as Contract**: Each patient has a care plan instantiated from templates. Compliance is measured against this plan, not abstract ideals. The plan defines what "success" means.

**Dual Optimization**: The system explicitly tracks both cost savings and patient outcomes. Models predict both re-admission risk (cost) and quality-of-life improvements (outcomes). Trade-offs are made explicit.

**Predictive Intervention**: Rather than reactive escalation, the analyst generates models that predict compliance degradation, enabling proactive outreach before patients fall out of compliance.

**Schema Evolution**: The analyst proposes schema extensions based on discovered patterns. Changes flow through Collibra for clinical stewardship approval.

**Interoperability**: Native FHIR integration for clinical data exchange. Epic Fyre integration for care plan synchronization and appointment scheduling.

## Components

### Care Plan Management
- `care_plan.py`: Care plan templates and patient instantiation
- `compliance_scoring.py`: Compliance calculation and historical tracking

### Operational Agent
- `agent.py`: Patient interaction orchestration
- `state.py`: Conversation and compliance state
- `protocol.py`: Clinical goals and safety guidelines

### Analyst Agent
- `analyst_agent.py`: Hypothesis generation and model creation
- `cohort_data.py`: Multi-dimensional patient data interface
- `models/`: Generated predictive models
  - `readmission_risk.py`
  - `compliance_predictor.py`
  - `appointment_adherence.py`

### Integration Layer
- `integrations/fhir_client.py`: HL7 FHIR R4 interface
- `integrations/epic_fyre.py`: Epic scheduling and care plan sync
- `integrations/collibra_client.py`: Schema governance

## Data Model

### Care Plan Schema
```python
{
  "plan_id": str,
  "patient_id": str,
  "template_id": str,
  "start_date": datetime,
  "medications": [
    {
      "name": str,
      "dosage": str,
      "frequency": str,
      "adherence_target": float  # 0.0-1.0
    }
  ],
  "appointments": [
    {
      "type": str,
      "frequency": str,
      "last_attended": Optional[datetime]
    }
  ],
  "lifestyle_goals": [
    {
      "goal": str,
      "target_metric": str,
      "measurement_frequency": str
    }
  ]
}
```

### Compliance Event Schema
```python
{
  "patient_id": str,
  "timestamp": datetime,
  "event_type": Enum["medication_taken", "medication_missed", 
                     "appointment_attended", "appointment_missed",
                     "goal_achieved", "goal_missed"],
  "plan_item_id": str,
  "compliance_score": float,  # Updated cumulative score
  "side_effects_reported": bool,
  "escalation_triggered": bool,
  "cost_impact": Optional[Decimal],  # Estimated cost of event
  "outcome_impact": Optional[float]   # Quality of life delta
}
```

### Outcome Tracking Schema
```python
{
  "patient_id": str,
  "timestamp": datetime,
  "readmission": bool,
  "emergency_visit": bool,
  "planned_visit": bool,
  "clinical_metrics": dict,  # Lab values, vitals, etc.
  "estimated_cost": Decimal,
  "qol_score": float  # Quality of life assessment
}
```

## Optimization Targets

### Cost Reduction (System Perspective)
**Primary Wins**:
1. **Prevent 30-day re-admissions** - Typical cost: $15k-25k per re-admission. Target: 20% reduction through predictive intervention.
2. **Reduce emergency department visits** - Typical cost: $2k-4k per visit. Target: 30% reduction through proactive compliance monitoring.

**Secondary Wins**:
- Reduce missed appointments requiring rescheduling overhead
- Optimize clinical resource allocation (nurse callbacks only for high-risk patients)
- Prevent medication-related adverse events requiring treatment

### Patient Outcomes (Clinical Perspective)
**Primary Wins**:
1. **Improve medication adherence** - Target: 15% improvement in patients below 80% adherence, leading to measurable clinical improvement (HbA1c, blood pressure, etc.)
2. **Reduce symptom burden** - Early detection of side effects and medication adjustment prevents patient suffering and treatment abandonment.

**Secondary Wins**:
- Improved appointment attendance leads to better chronic disease management
- Patient empowerment through understanding of own compliance patterns
- Reduced anxiety from proactive monitoring vs reactive crisis management

## Analytical Capabilities

### Hypothesis Generation
The analyst agent explores patterns such as:
- "Patients with diabetes + hypertension who miss morning medications are 3.2x more likely to be re-admitted within 30 days compared to those who miss evening doses"
- "Compliance drops 40% in patients living alone when appointment intervals exceed 60 days, but only 10% for patients with family support"
- "Cost of intervention calls ($12/call) break-even at 0.3% re-admission prevention rate, suggesting broad deployment is cost-effective"

### Predictive Models
Generated models include:
- **Re-admission risk**: 7-day, 14-day, 30-day prediction windows
- **Compliance degradation**: Identifies patients likely to drop below target compliance in next 2 weeks
- **Appointment no-show**: Predicts missed appointments 3+ days in advance for proactive outreach
- **Medication adjustment need**: Flags patients likely experiencing side effects before they escalate

### Schema Evolution Examples
Analyst may propose:
- Add `transportation_access` field after discovering it predicts appointment adherence
- Add `caregiver_involvement_score` when family support proves significant
- Add `medication_complexity_score` when polypharmacy patterns emerge
- Add `seasonal_compliance_variance` when winter shows different patterns

## FHIR Integration

The system implements FHIR R4 resources:
- **CarePlan**: Sync care plan definitions
- **MedicationStatement**: Record adherence events
- **Observation**: Clinical measurements and outcomes
- **Appointment**: Schedule and attendance tracking
- **Communication**: Document patient interactions

All compliance data is exportable as FHIR bundles for EHR integration.

## Epic Fyre Integration

- **Care Plan Sync**: Bidirectional sync of care plans between agent system and Epic
- **Appointment Management**: Real-time appointment scheduling and modification
- **Clinical Documentation**: Compliance scores and agent interactions documented in Epic flowsheets
- **Alert Integration**: High-risk predictions trigger BPA (Best Practice Advisory) in Epic

## Usage

### Operational Mode
```bash
# Conduct patient compliance call
python main.py --patient P001

# Batch compliance check for cohort
python main.py --batch --cohort hypertension_patients
```

### Analytical Mode
```bash
# Explore compliance patterns
python analyze.py --mode explore --focus readmission

# Generate predictive model
python analyze.py --mode generate-model --target 30day_readmit

# Test hypothesis
python analyze.py --mode test-hypothesis --hypothesis "living_situation_affects_compliance"

# Propose schema extension
python analyze.py --mode propose-schema --field transportation_access
```

### Integration Sync
```bash
# Pull care plans from Epic
python sync.py --source epic --resource CarePlan

# Push compliance data to FHIR server
python sync.py --target fhir --push-compliance

# Sync with Collibra schema registry
python sync.py --collibra --sync-schema
```

## Requirements

- Python 3.10+
- PostgreSQL 14+ (cohort data, compliance history)
- FHIR server (R4 compliant)
- Epic on FHIR credentials
- Collibra API access
- LLM provider access (Anthropic, OpenAI, or local)

## Dependencies

```
anthropic>=0.39.0
fhir.resources>=7.0
pydantic>=2.0
sqlalchemy>=2.0
scipy>=1.11
numpy>=1.24
httpx>=0.24
```

Statistical libraries and ML frameworks imported dynamically by generated analytical code.

## Monitoring

The system tracks:
- Compliance score distributions across cohort
- Prediction accuracy for re-admission, compliance degradation
- Cost savings from prevented re-admissions and ED visits
- Patient outcome improvements (clinical metrics, QoL scores)
- Model drift and retraining triggers

## Clinical Validation

All predictive models undergo clinical review before deployment. False positive rates for escalation are monitored to prevent alert fatigue. Cost-effectiveness analysis is performed quarterly.

## License

Internal research use. Not FDA approved for clinical decision-making.
