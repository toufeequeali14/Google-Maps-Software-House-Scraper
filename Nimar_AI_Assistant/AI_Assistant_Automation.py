import asyncio
import json
import os
import time
import aiohttp
from playwright.async_api import async_playwright


API_URL = "http://192.168.18.145:8000/send_message"
# CONTACT = "Ai Assistant for all projects"
CONTACT = "testing"

results = []

path_to_ss = "screenshots"

os.makedirs(path_to_ss, exist_ok=True)


async def send_to_api(prompt, file_path=None):

    msg = f"""Nimar Production AI Assistant

Prompt:
{prompt}
"""

    try:
        async with aiohttp.ClientSession() as session:

            form = aiohttp.FormData()
            form.add_field("receiver_name", CONTACT)
            form.add_field("message", msg)
            form.add_field("send_in_hd", "true")

            if file_path and os.path.exists(file_path):
                form.add_field(
                    "file",
                    open(file_path, "rb"),
                    filename=os.path.basename(file_path),
                    content_type="image/jpeg"
                )

            async with session.post(API_URL, data=form) as resp:
                status = resp.status
                body = await resp.text()
                print(f"API response [{status}]: {body}")

    except Exception as e:
        print(f"API call failed: {e}")


async def get_latest_response(page):
    await asyncio.sleep(2)
    previous_text = ""
    stable_count = 0

    while stable_count < 3:
        elements = await page.query_selector_all(
            "div.break-words.whitespace-pre-wrap.leading-relaxed.text-\\[16px\\] p.my-2"
        )
        if not elements:
            await asyncio.sleep(1)
            continue

        last_element = elements[-1]
        current_text = await last_element.inner_text()

        if current_text == previous_text and current_text.strip():
            stable_count += 1
        else:
            stable_count = 0
            previous_text = current_text

        await asyncio.sleep(1)



        # first step is to cleab the data
    all_blocks = await page.query_selector_all(
        "div.break-words.whitespace-pre-wrap.leading-relaxed.text-\\[16px\\]"
    )
    if not all_blocks:
        return "No response found"

    last_block = all_blocks[-1]
    paragraphs = await last_block.query_selector_all("p.my-2")
    full_text = "\n".join([await p.inner_text() for p in paragraphs])
    return full_text.strip()

import pyscreenshot


# method sends prompt
async def send_prompt(page, text, send_api=False):
    await page.wait_for_selector(
        "textarea[placeholder='Ask Something']",
        timeout=20000
    )
    await page.fill("textarea[placeholder='Ask Something']", text)
    print(f"Prompt: '{text}'")
    await page.click("button[type='submit']")
    print("Submitted! Waiting for response...")

    response = await get_latest_response(page)
    print(f"Response: '{response[:80]}...\n" if len(response) > 80 else f"Response: '{response}'\n")

    # Wait until the response text is actually visible on the page
    # before taking the screenshot — confirms AI has responded
    print("Confirming response is visible on page...")
    try:
        # Wait for the last paragraph to contain our response text
        # Use first 60 chars of response as a unique-enough anchor
        response_anchor = response[:60].strip()
        await page.wait_for_function(
            """(anchor) => {
                const elements = document.querySelectorAll(
                    'div.break-words.whitespace-pre-wrap.leading-relaxed p.my-2'
                );
                return Array.from(elements).some(el => el.innerText.includes(anchor));
            }""",
            arg=response_anchor,
            timeout=30000
        )
        print("Response confirmed visible on page.")
    except Exception as e:
        print(f"Visibility check timed out, proceeding anyway: {e}")

    # Small buffer so the full response block renders completely
    time.sleep(60)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"{path_to_ss}/AI_Assistant_response_{timestamp}.jpg"
    await page.screenshot(path=screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    if send_api:
        print("Sending to API...")
        await send_to_api(text, file_path=screenshot_path)


async def run():
    async with async_playwright() as p:

        #  Connect to already-running browser
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        print("Connected to existing browser session!")
    
        context = browser.contexts[0]

        #  Find the logged-in page
        page = None
        for pg in context.pages:
            if "nimar.gov.pk" in pg.url:
                btn = await pg.query_selector("button:has-text('Login')")
                if btn is None:
                    page = pg
                    break

        if not page:
            print("ERROR: No logged-in Nimar page found.")
            print("Make sure keep_session.py is running and you are logged in.")
            return

        print(f"Using page: {page.url}")

        #  Navigate to AI Assistant using the correct href
        if "aiAssistant" not in page.url:
            print("Navigating to Ai Assistant...")
            await page.click("a[href='/aiAssistant']")
            await page.wait_for_url("**/aiAssistant**", timeout=10000)
            print(f"Navigated! URL: {page.url}")

        #  Wait for the textarea to be ready
        await page.wait_for_selector(
            "textarea[placeholder='Ask Something']",
            timeout=20000
        )
        print("Textarea found! Ready to send prompts.\n")

        # ── Send hardcoded prompts ──

        import random
        #load prompts from txt file
        with open("Nimar_prompts.txt") as f:
            prompts = f.read().splitlines()


        prompt = random.choice(prompts)
        print("This time prompt: ", prompt)

        await send_prompt(page, prompt, send_api=True)
        await asyncio.sleep(2)


# asyncio.run(run())

if __name__=="__main__":
    asyncio.run(run())







