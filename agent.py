import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

class WorkdayAgent:
    def __init__(self, headless=False):
        self.headless = headless
        self.email = os.getenv("WORKDAY_EMAIL")
        self.password = os.getenv("WORKDAY_PASSWORD")
        self.resume_path = os.getenv("RESUME_PATH")

    async def run(self, job_urls):
        # Notice we are now accepting a list of URLs
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            for url in job_urls:
                print(f"\n[*] Processing URL: {url}")
                await self.process_job(page, url)

            print("\n[*] All jobs processed. Closing browser.")
            await browser.close()

    async def process_job(self, page, job_url):
        try:
            await page.goto(job_url)
            await page.wait_for_load_state("networkidle")

            # --- Validation Phase: Is the job still active? ---
            # Workday usually shows this text if a job is closed
            inactive_text = await page.locator('text="This job is no longer available"').is_visible()
            
            # Or it might redirect away from the specific job posting
            if inactive_text or "job" not in page.url:
                print("[!] Job is expired or unavailable. Skipping...")
                return # Exit this specific job attempt gracefully

            # --- Apply Flow ---
            print("[*] Job active. Looking for Apply button...")
            apply_button = page.locator("a[data-automation-id='applyNowButton'], button:has-text('Apply')").first
            await apply_button.wait_for(state="visible", timeout=5000)
            await apply_button.click()
            
            print("[*] Selecting 'Autofill with Resume'...")
            autofill_btn = page.locator("button:has-text('Autofill with Resume')").first
            await autofill_btn.click()
            
            # --- Continue with Authentication & Upload here... ---
            # (Insert the login/signup and upload logic from our previous step)
            print("[+] Successfully reached the application portal.")

        except PlaywrightTimeoutError:
            print("[!] Timed out trying to interact with the page. Layout might have changed.")
        except Exception as e:
            print(f"[!] An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Now we pass a list. You can add a fresh test link here.
    test_urls = [
        "https://kenvue.wd5.myworkdayjobs.com/en-US/kenvue/job/Asia-Pacific%2C-India%2C-Karnataka%2C-Bangalore/GCC-Intern_2607043587W?source=LinkedIn", # The expired one
        # Add a new, active Workday link here to test!
        "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/India-Bengaluru/Senior-System-Software-Engineer--Deep-Learning-Accelerator-_JR2014631/apply?source=Eightfold",
        
    ]
    agent = WorkdayAgent(headless=False)
    asyncio.run(agent.run(test_urls))