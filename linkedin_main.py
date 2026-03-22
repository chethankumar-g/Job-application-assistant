import asyncio
from config import config
from scrapers.driver.form_filler import PlaywrightDriver
from ai_engine.agent_brain import AgentBrain

async def main():
    print("=== LinkedIn Hybrid Pipeline ===")
    
    if not config.LINKEDIN_EMAIL or not config.LINKEDIN_PASSWORD:
        print("[!] Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your .env file")
        return

    driver = PlaywrightDriver(headless=False)
    brain = AgentBrain()

    try:
        await driver.start_browser()
        
        # --- PHASE 1: STRICT DETERMINISTIC LOGIN ---
        print("\n--- PHASE 1: STRICT LOGIN ---")
        await driver.strict_linkedin_login(config.LINKEDIN_EMAIL, config.LINKEDIN_PASSWORD)
        
        
        # --- PHASE 2: AUTONOMOUS AGENT LOOP ---
        print("\n--- PHASE 2: AUTONOMOUS LLM AGENT ACTIVATED ---")
        print("[*] Transitioning control to the local AI Agent...")
        
        # Define Agent's Logical Goal for Phase 2
        goal = """
        STATUS: We are currently logged into LinkedIn and physically on the Jobs page.
        GOAL: Use the 'wait_for_user' action immediately to pause and ask the human what they want you to do next on this page.
        """
        
        # Autonomous Agent Loop limit to prevent infinite runaways
        max_steps = 15
        for step in range(max_steps):
            print(f"\n--- AI Decision Cycle {step+1}/{max_steps} ---")
            
            # 1. PERCEIVE: Get compressed page state
            state_text, current_url = await driver.extract_compressed_page_state()
            
            print("\n----- DOM STATE VISIBLE TO AGENT -----")
            print(state_text)
            print("--------------------------------------")
            
            if not state_text:
                print("[-] No interactive elements found immediately. Re-evaluating...")
                await asyncio.sleep(2)
                continue
                
            # 2. THINK: Ask LLM what to do next
            action_dict = brain.decide_next_action(state_text, current_url, goal)
            
            # 3. ACT: Execute physical command
            await driver.execute_agent_action(action_dict)
            
            if action_dict.get("action") == "done":
                print("\n[+] Autonomous goal set concluded successfully!")
                break
                
            await asyncio.sleep(2) # Brief human pause between actions

        print("\n[*] Reached end of execution. Browser will remain open for your testing.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "Press Enter to shut down browser...")

    except Exception as e:
        print(f"\n[!] Critical System Error: {e}")
    finally:
        print("[*] Shutting down agent...")
        await driver.close()

if __name__ == "__main__":
    asyncio.run(main())
