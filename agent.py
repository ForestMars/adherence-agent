class MedicationAgent:
    def __init__(self, protocol, state, llm):
        self.protocol = protocol
        self.state = state
        self.llm = llm

    def process_input(self, user_input):
        # Main orchestration logic goes here
        pass

#!/usr/bin/env python3
# agent.py - Provides orchestration forthe agent to pursues goal by stepwise decision
__version__ = '0.1'

import json
from state import ConversationState, Patient
from llm import LLM
from protocol import AGENT_GOAL, PATIENT_SAFETY_GUIDELINES, AVAILABLE_ACTIONS

class MedicationAgent:
    def __init__(self, llm: LLM):
        self.llm = llm
    
    def start_call(self, patient: Patient) -> ConversationState:
        """Initialize a new call with a patient"""
        state = ConversationState(patient=patient)
        
        # Generate greeting
        greeting = self._generate_greeting(patient.name)
        state.add_message("agent", greeting)
        
        return state
    
    def process_patient_response(
        self,
        state: ConversationState,
        patient_response: str
    ) -> tuple[str, bool, str]:
        """
        Process patient's response - the LLM decides what to do next.
        
        Returns:
            (agent_reply: str, call_complete: bool, call_outcome: str)
        """
        
        # Add patient response to transcript
        state.add_message("patient", patient_response)
        
        # LLM decides what to do next based on the goal and conversation so far
        decision = self._decide_next_action(state, patient_response)
        
        # Log the LLM's reasoning (in production, this would go to monitoring)
        print(f"\n[AGENT REASONING: {decision['reasoning']}]")
        
        # Extract any information the LLM gathered
        if decision.get("information_gathered"):
            for key, value in decision["information_gathered"].items():
                state.record_answer(key, value)
        
        # Execute the action the LLM decided on
        action = decision["action"]
        
        if action == "ask_question":
            agent_reply = decision["content"]
            state.add_message("agent", agent_reply)
            return agent_reply, False, "in_progress"
        
        elif action == "provide_information":
            agent_reply = decision["content"]
            state.add_message("agent", agent_reply)
            return agent_reply, False, "in_progress"
        
        elif action == "escalate_to_nurse":
            reason = decision.get("escalation_reason", "Patient needs nurse follow-up")
            state.trigger_escalation(reason)
            agent_reply = decision.get("content", 
                "I'm going to connect you with a nurse right away. Please hold.")
            state.add_message("agent", agent_reply)
            return agent_reply, True, "escalated"
        
        elif action == "schedule_callback":
            reason = decision.get("escalation_reason", "Non-urgent follow-up needed")
            state.trigger_escalation(reason)
            agent_reply = decision.get("content",
                "I'll have a nurse call you back later today to discuss this further.")
            state.add_message("agent", agent_reply)
            return agent_reply, True, "callback_scheduled"
        
        elif action == "end_call":
            agent_reply = decision.get("content",
                f"Thank you for your time, {state.patient.name}. Take care!")
            state.add_message("agent", agent_reply)
            return agent_reply, True, "completed"
        
        else:
            # Unknown action, default to asking for more info
            agent_reply = "Could you tell me a bit more about that?"
            state.add_message("agent", agent_reply)
            return agent_reply, False, "in_progress"
    
    def _decide_next_action(self, state: ConversationState, patient_latest_response: str) -> dict:
        """
        The LLM decides what to do next to achieve the goal.
        
        Returns:
            {
                "action": str,
                "reasoning": str,
                "content": str,
                "escalation_reason": str,
                "information_gathered": dict
            }
        """
        
        # Build conversation context
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in state.transcript
        ])
        
        conv_text += f"\nPATIENT: {patient_latest_response}"
        
        prompt = f"""You are a medication adherence agent. Your goal:

{AGENT_GOAL}

Patient Information:
- Name: {state.patient.name}
- Medication: {state.patient.medication_name}
- Schedule: {state.patient.medication_schedule}

{PATIENT_SAFETY_GUIDELINES}

Available Actions:
{json.dumps(AVAILABLE_ACTIONS, indent=2)}

Conversation so far:
{conv_text}

Decide what to do next. You should:
1. Assess what information you still need
2. Determine if you've learned anything concerning
3. Choose the most appropriate action
4. Be natural and conversational, not robotic

Respond ONLY with a JSON object:
{{
    "action": "ask_question|provide_information|escalate_to_nurse|schedule_callback|end_call",
    "reasoning": "brief explanation of why you chose this action",
    "content": "what you'll say to the patient (if asking/informing)",
    "escalation_reason": "if escalating, why?",
    "information_gathered": {{"key": "value"}}
}}"""

        response_text = self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        
        # Parse JSON response
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                response_text = response_text[json_start:json_end]
            
            decision = json.loads(response_text)
            
            # Validate required fields
            if "action" not in decision or "reasoning" not in decision:
                raise ValueError("Missing required fields")
            
            return decision
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback to safe default
            return {
                "action": "ask_question",
                "reasoning": "Failed to parse decision, defaulting to gathering more info",
                "content": "I apologize, could you tell me more about how you're doing with your medication?",
                "information_gathered": {}
            }
    
    def _generate_greeting(self, patient_name: str) -> str:
        """Generate initial greeting"""
        prompt = f"Generate a brief, warm greeting for a medication adherence call with {patient_name}. Keep it to 2-3 sentences and ask if now is a good time to talk."
        
        return self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )