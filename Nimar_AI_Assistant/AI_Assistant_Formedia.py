import asyncio
import os
import aiohttp
import time
from playwright.async_api import async_playwright

from AI_Assistant_Automation import send_to_api

CONTACT = "testing"
API_URL = "http://192.168.18.145:8000/send_message"



class FormediaAIAssistant:
    def __init__(self, session_file="formedia.json"):
        self.session_file = session_file
        

    async def AI_Assistant(self, prompt:str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state="formedia.json")
            page = await context.new_page()

            await page.goto("http://staging.formedia.ai/newsChat?chatId=4", wait_until="networkidle")

            await page.wait_for_timeout(2000)

            await page.wait_for_selector('textarea[placeholder="Type your message..."]', timeout=10000)

            print("Prompt: ", prompt)
            await page.fill('textarea[placeholder="Type your message..."]', prompt)
            await page.wait_for_timeout(1000)

            await page.click('button[type="submit"]')

            #take screenshot of the page after sending the prompt
            await page.wait_for_timeout(5000)

            #path to save the screenshot
            screenshot_path = "screenshots/formedia_assistant.jpg"

            print("taking screenshot...")
            await page.screenshot(path=screenshot_path)


    async def send_to_api(self, msg, screenshot_path: str = "screenshots/formedia_assistant.jpg"):
        if not os.path.exists(screenshot_path):
            print(f"Screenshot not found at {screenshot_path}. Please run the AI_Assistant function first.")
            return

        
        #create client session for api
        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field("receiver_name", CONTACT)
                form.add_field("message", msg)
                form.add_field("send_in_hd", "true")


                #attach screenshot image to the form data
                if screenshot_path and os.path.exists(screenshot_path):
                    form.add_field(
                        "file",
                        open(screenshot_path, "rb"),
                        filename=os.path.basename(screenshot_path),
                        content_type="image/jpeg"
                    )


                # now post the form data to the API
                async with session.post(API_URL, data=form) as resp:
                    status = resp.status
                    body = await resp.text()
                    print(f"API response [{status}]: {body}")


        except Exception as e:
            print(f"API call failed: {e}")

        # to store data into google sheet, we can use gspread library.
        # to store data into csv file we can use csv module in python.




    async def run_formedia_assistant(self, prompt: str, file_path: str):

        prompt = "What is the news about?"
        await self.AI_Assistant(prompt)
        # breakpoint()

        print("Sending to API...")
        msg = f"Formedia_AI_Assistant \n prompt: {prompt}"
        await self.send_to_api(msg, screenshot_path=file_path)

        print("Sent to api succesfully!")



if __name__ == "__main__":
    prompt = "What is the news about?"
    assistant = FormediaAIAssistant()
    asyncio.run(assistant.run_formedia_assistant(prompt, file_path="screenshots/formedia_assistant.jpg")) 




# if __name__ == "__main__":
#     prompt = "What is the news about?"
#     asyncio.run(AI_Assistant(prompt))


#     msg = f"Formedia_AI_Assistant \n prompt: {prompt}"
#     asyncio.run(send_to_api(msg, screenshot_path="screenshots/formedia_assistant.jpg"))
    



