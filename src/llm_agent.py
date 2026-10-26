import json
import re
import os
from openai import OpenAI

class LLMHarbourMaster:
    def __init__(self, log_path="logs/llm_log.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        # Initializes OpenAI client (requires OPENAI_API_KEY environment variable)
        try:
            self.client = OpenAI()
        except Exception:
            self.client = None

    def _format_prompt(self, env_state):
        return f"""
[ROLE]
You are the Stormwatch Harbour Master managing a 20x12 harbour grid.

[CONTEXT]
- Current Tick: {env_state['tick']}/600
- Storm Warning Active: {env_state['storm_warning']}
- Unsafe Berths during Storms: B2, B3
- Active Ship Queue: {json.dumps(env_state['berth_ships'])}
- Delivered Cargo: {env_state['delivered_cargo']}

[CONSTRAINTS]
1. Never send workers to berths B2 or B3 when Storm Warning is True.
2. Output strictly in ReAct format.

[FORMAT]
Thought: <reasoning step>
Action: assign_workers(berth_id="<B1|B2|B3|B4>", count=<1-5>)
Final Report: <brief summary>
"""

    def decide(self, env_state):
        prompt = self._format_prompt(env_state)
        
        if self.client is None:
            # Fallback if API key is not present
            return "FALLBACK_UTILITY", None

        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.2
                )
                text = response.choices[0].message.content

                # Audit Log Entry (Task C Requirement)
                with open(self.log_path, "a") as f:
                    f.write(json.dumps({
                        "tick": env_state["tick"],
                        "prompt": prompt,
                        "response": text
                    }) + "\n")

                # Parse ReAct Action
                action_match = re.search(r'Action:\s*(\w+)\((.*)\)', text)
                if action_match:
                    action_name = action_match.group(1)
                    args = action_match.group(2)
                    return action_name, args
            except Exception as e:
                print(f"[LLM Agent] Retry attempt {attempt + 1} failed: {e}")

        # Fallback to Utility policy if retries fail
        return "FALLBACK_UTILITY", None