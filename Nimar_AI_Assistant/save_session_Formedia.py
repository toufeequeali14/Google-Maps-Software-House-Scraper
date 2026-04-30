import json
import asyncio
from playwright.async_api import async_playwright


async def login_and_save_session(
    url: str,
    username: str,
    password: str,
    session_file: str = "formedia.json"
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )

        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to website
        await page.goto(url, wait_until="networkidle")
        
        await page.wait_for_selector('input[id="email"]', timeout=5000)

        # Fill login form
        await page.fill('input[id="email"]', username)
        await asyncio.sleep(2)

        await page.fill('input[id="password"]', password)
        await asyncio.sleep(2)

        # Submit form
        await page.click('button[type="submit"]')
        await asyncio.sleep(2)
        # Wait after login
        await page.wait_for_load_state("networkidle")

        # Save storage/session
        storage = await context.storage_state()

        with open(session_file, "w") as f:
            json.dump(storage, f, indent=4)

        print(f"Session saved to {session_file}")

        await browser.close()


if __name__=="__main__":

    username = "qa@forbmax.ai"
    password = "123456"

    asyncio.run(login_and_save_session(
    url="http://staging.formedia.ai/login",
    username=username,
    password=password,
    session_file="formedia.json"
    ))