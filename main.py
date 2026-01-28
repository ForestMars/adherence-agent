"""
Entry point - simulates a medication adherence call where the agent makes decisions.
"""

import os
from state import get_patient
from provider_anthropic import AnthropicProvider
from agent import MedicationAgent

def simulate_call(patient_id: str):
    """Simulate a call with a patient where the agent decides what to do"""
    
    # Initialize
    patient = get_patient(patient_id)
    if not patient:
        print(f"Patient {patient_id} not found")
        return
    
    # Use Anthropic provider (could swap for any LLM provider)
    llm = AnthropicProvider()
    agent = MedicationAgent(llm)
    
    # Start the call
    state = agent.start_call(patient)
    
    print("=" * 60)
    print(f"MEDICATION ADHERENCE CALL - {patient.name}")
    print(f"Medication: {patient.medication_name} ({patient.medication_schedule})")
    print("=" * 60)
    print(f"\nAGENT: {state.transcript[-1]['content']}\n")
    
    # Conversation loop - agent decides when to end
    call_complete = False
    call_outcome = "in_progress"
    
    while not call_complete:
        # Simulate patient response
        patient_response = input("PATIENT: ")
        print()  # Blank line for readability
        
        if patient_response.lower() in ["quit", "exit"]:
            print("Call ended by user.")
            break
        
        # Agent processes response and decides what to do next
        agent_reply, call_complete, call_outcome = agent.process_patient_response(
            state, 
            patient_response
        )
        
        print(f"AGENT: {agent_reply}\n")
    
    # Print call summary
    print("\n" + "=" * 60)
    print("CALL SUMMARY")
    print("=" * 60)
    print(f"Patient: {patient.name}")
    print(f"Outcome: {call_outcome}")
    print(f"Duration: {len(state.transcript)} exchanges")
    print(f"Escalation needed: {state.escalation_triggered}")
    if state.escalation_triggered:
        print(f"Escalation reason: {state.escalation_reason}")
    print(f"\nInformation gathered:")
    for key, value in state.answers.items():
        print(f"  - {key}: {value}")
    
    print(f"\nFull transcript:")
    for msg in state.transcript:
        role = msg['role'].upper()
        content = msg['content']
        print(f"  {role}: {content}")
    print("=" * 60)

def main():
    """Main entry point"""
    print("\nMEDICATION ADHERENCE AGENT")
    print("The agent will pursue the goal of ensuring medication safety.")
    print("It will decide what to ask and when to escalate based on the conversation.\n")
    
    print("Available patients:")
    print("  P001 - John Smith (Lisinopril)")
    print("  P002 - Maria Garcia (Metformin)")
    print()
    
    patient_id = input("Enter patient ID (or press Enter for P001): ").strip()
    if not patient_id:
        patient_id = "P001"
    
    print()
    simulate_call(patient_id)

if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: Please set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY='your-key-here'")
        exit(1)
    
    main()