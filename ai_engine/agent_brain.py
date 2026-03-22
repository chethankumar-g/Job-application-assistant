import sys
import json
import requests

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

# Provide absolute path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import config

class AgentAction(BaseModel):
    reasoning: str = Field(description="Briefly explain WHY you chose this action and which specific element label you want to target.")
    action: str = Field(description="Must be strictly one of: 'click', 'fill', 'wait_for_user', 'navigate', 'done'")
    target_id: Optional[int] = Field(description="The exact numeric ID inside brackets [X] of the element you decided to target (e.g., 3)")
    value: Optional[str] = Field(description="The exact text to type if action is 'fill', or a URL if 'navigate'")

class AgentBrain:
    def __init__(self):
        self.ollama_url = config.OLLAMA_BASE_URL
        self.model = config.DEFAULT_MODEL
        
    def decide_next_action(self, page_state_text, current_url, goal):
        """Passes the state of the page to the local LLM and returns forced JSON."""
        print("[*] Agent Brain: Analyzing screen...")
        
        prompt = f"""
        You are an autonomous web-browsing agent. Your primary goal is:
        {goal}
        
        CURRENT URL: {current_url}
        
        AVAILABLE INTERACTIVE ELEMENTS:
        {page_state_text}
        
        CRITICAL INSTRUCTIONS:
        1. Examine the CURRENT URL and AVAILABLE ELEMENTS. Decide the next logical step to achieve your goal.
        2. To click a button or link, use action "click" and provide the exact numeric target_id.
        3. To type text into an input field, use action "fill", provide the numeric target_id, and the "value".
        4. IF AN ELEMENT HAS "(FILLED_WITH: '...')", IT IS ALREADY COMPLETED. Do NOT fill it again. Move to the next step (e.g., filling the password or clicking Submit).
        5. If the page is asking for a security check, captcha, or manual puzzle, immediately choose action "wait_for_user".
        6. If you have completely achieved your goal, use action "done".
        
        Output strictly in JSON matching the schema requirements.
        """
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": AgentAction.model_json_schema()
        }
        
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
            if not response.ok:
                print(f"[!] Ollama returned HTTP {response.status_code}: {response.text}")
                return {"action": "wait_for_user", "reasoning": f"Local AI 404 Error: {response.text}"}
                
            ai_response = response.json().get("response", "{}")
            return json.loads(ai_response)
        except Exception as e:
            print(f"[!] Brain Error: {e}")
            return {"action": "wait_for_user", "reasoning": f"Local AI Error: {e}"}
