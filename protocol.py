# Define medication questions and escalation logic
PROTOCOL = {
    "steps": ["identity_check", "medication_confirmation", "dosage_check"],
    "escalation_rules": {
        "emergency": "Transfer to human supervisor"
    }
}
