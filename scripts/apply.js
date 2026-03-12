const { chromium } = require("playwright");
const { jobLink } = require("../config/job");

(async () => {

    const browser = await chromium.launch({
        headless: false
    });

    const page = await browser.newPage();

    await page.goto(jobLink);

    // Click Apply
    await page.waitForSelector('text=Apply');
    await page.click('text=Apply');

    // Click Autofill with Resume
    await page.waitForSelector('text=Autofill with Resume');
    await page.click('text=Autofill with Resume');

    // Small wait for redirect
    await page.waitForTimeout(2000);

    // Detect state
    const createAccount = await page.locator('text=Create Account').isVisible().catch(() => false);
    const signIn = await page.locator('text=Sign In').isVisible().catch(() => false);

    if (createAccount) {

        console.log("Create Account flow detected");

        await page.getByLabel("Email Address").fill("mahadevd3108@gmail.com");

        await page.locator('[data-automation-id="password"]').fill("Mahadev@Automation123");

        await page.locator('[data-automation-id="verifyPassword"]').fill("Mahadev@Automation123");

        await page.getByRole("checkbox").check();

        await page.getByRole("button", { name: "Create Account" }).click();

        // Wait for redirect
        await page.waitForTimeout(3000);

        console.log("Signup submitted, checking for login page...");

    }

    // Try login if login page exists
    try {

    // Wait for login container
    await page.waitForSelector('[data-automation-id="signInContent"]', { timeout: 8000 });

    console.log("Login page detected");

    const loginForm = page.locator('[data-automation-id="signInContent"]');

    // Fill email
    await loginForm.getByLabel("Email Address").fill("mahadevd3108@gmail.com");

    // Fill password
    await loginForm.locator('[data-automation-id="password"]').fill("Mahadev@Automation2025");

    // Click sign in
    await loginForm.getByRole("button", { name: "Sign In" }).click();

    console.log("Login submitted");

} catch (err) {

    console.log("Login page not detected, continuing...");

}

    // Wait for next page to load
    await page.waitForLoadState("networkidle");

    // Resume upload
    try {

        await page.waitForSelector('input[type="file"]', { timeout: 10000 });

        console.log("Resume upload page detected");

        await page.setInputFiles('input[type="file"]', '../assets/resume.pdf');

        console.log("Resume uploaded successfully");

    } catch (err) {

        console.log("Resume upload page not found (maybe already uploaded)");

    }

})();