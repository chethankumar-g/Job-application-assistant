import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class PlaywrightDriver:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def start_browser(self):
        print("[*] Playwright: Launching browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.firefox.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def navigate_to_form(self, url):
        print(f"[*] Playwright: Navigating to {url}")
        await self.page.goto(url)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        return True

    async def strict_linkedin_login(self, email, password):
        """Strict manual workflow as requested."""
        import asyncio
        loop = asyncio.get_event_loop()
        
        print("[*] Step 1: Navigating to jobs url...")
        await self.page.goto("https://www.linkedin.com/jobs/")
        await self.page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        
        print("[*] Analyzing form fields directly on jobs page...")
        email_loc = self.page.locator("#username, #session_key, input[type='email'], input[name='session_key']").first
        password_loc = self.page.locator("#password, #session_password, input[type='password'], input[name='session_password']").first
        
        print(f"[*] Step 2: Filling email ({email})...")
        await email_loc.wait_for(state="visible", timeout=15000)
        await email_loc.fill(email)
        
        print("\n🛑 MANUAL REVIEW REQUIRED")
        await loop.run_in_executor(None, input, "Email filled successfully! Press Enter to continue to password... ")
        
        print(f"\n[*] Step 3: Filling password...")
        await password_loc.fill(password)
        
        print("\n🛑 MANUAL REVIEW REQUIRED")
        await loop.run_in_executor(None, input, "Password filled successfully! Press Enter to click Sign In... ")
        
        print("\n[*] Step 4: Clicking Sign In...")
        submit_btn = self.page.locator("button[type='submit']").first
        await submit_btn.click()
        
        print("[*] Step 5: Waiting 10 seconds for LinkedIn jobs to load securely...")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        await asyncio.sleep(10)
        print("[+] Strict LinkedIn login workflow complete!")

    async def extract_compressed_page_state(self):
        """Injects markers into the DOM and returns a lightweight compressed text representation for local LLMs."""
        print("[*] Playwright: Scanning DOM for interactive elements...")
        
        js_script = """
        () => {
            let elements = [];
            let interactables = document.querySelectorAll('a, button, input, select, textarea, [role="button"], [role="link"], [role="menuitem"], [role="tab"]');
            
            let id_counter = 1;
            interactables.forEach(el => {
                // Skip hidden elements
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || el.offsetWidth === 0 || el.offsetHeight === 0) return;
                
                let nameOrLabel = el.ariaLabel || el.placeholder || el.name || el.id || el.innerText || '';
                nameOrLabel = nameOrLabel.trim().substring(0, 50).replace(/\\n/g, ' ');
                
                let type = el.tagName.toLowerCase();
                let currentValue = '';
                
                if (type === "input" || type === "textarea" || type === "select") {
                    if (type === "input") type = `input[type=${el.type || 'text'}]`;
                    if (el.value) currentValue = ` (FILLED_WITH: '${el.value}')`;
                }
                
                if (nameOrLabel || currentValue) {
                    el.setAttribute('data-agent-id', id_counter);
                    elements.push(`[${id_counter}] ${type} "${nameOrLabel}"${currentValue}`);
                    id_counter++;
                }
            });
            return elements.join('\\n');
        }
        """
        
        state_text = await self.page.evaluate(js_script)
        url = self.page.url
        return state_text, url

    async def execute_agent_action(self, action_dict):
        """Physically executes the action decided by the LLM."""
        action = action_dict.get("action")
        target_id = action_dict.get("target_id")
        value = action_dict.get("value")
        reasoning = action_dict.get("reasoning")
        
        print(f"\n🧠 AGENT REASONING: {reasoning}")
        print(f"🤖 AGENT ACTION: {str(action).upper()} | Target ID: {target_id} | Value: {value}")
        
        try:
            if action == 'click' and target_id:
                locator = self.page.locator(f"[data-agent-id='{target_id}']").first
                await locator.scroll_into_view_if_needed()
                await locator.click()
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=5000)
                except: pass
                
            elif action == 'fill' and target_id:
                locator = self.page.locator(f"[data-agent-id='{target_id}']").first
                await locator.scroll_into_view_if_needed()
                
                # Mimic human typing for anti-bot
                await locator.fill("") # Clear first
                for char in str(value):
                    await locator.type(char, delay=75)
                
            elif action == 'navigate' and value:
                await self.page.goto(value)
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                except: pass
                
            elif action == 'wait_for_user':
                print("🛑 The AI agent paused execution and requested human intervention.")
                import asyncio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, input, "Press Enter here after you've manually resolved the issue in the browser: ")
                
            elif action == 'done':
                print("✅ Agent believes it has accomplished the goal in this cycle.")
            else:
                print(f"[!] Unknown action command received: {action}")
                
        except Exception as e:
            print(f"[!] Action execution failed: {e}")

    async def close(self):
        if self.browser:
            await self.browser.close()