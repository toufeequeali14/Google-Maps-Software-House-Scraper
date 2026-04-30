import subprocess

from playwright.sync_api import sync_playwright
import time

def is_logged_in(page):
    try:
        # If login button exists, we're NOT logged in
        login_btn = page.query_selector("button:has-text('Login')")
        return login_btn is None
    except:
        return False

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_profile_BH",
        headless=False,
        args=[
            "--remote-debugging-port=9222",
            "--window-size=1280,800",
        ]
    )


    page = context.new_page()
    page.goto("https://app.nimar.gov.pk/")
    page.wait_for_load_state("networkidle")

    # Check if already logged in
    if not is_logged_in(page):
        print("Not logged in — please login manually + OTP in the browser...")
        input("Press ENTER after login is complete...")
    else:
        print("Already logged in!")

    if not is_logged_in(page):
        print("ERROR: Still not logged in. Please try again.")
        context.close()
        exit()

    print("Session active! Keeping alive...")
    print("DO NOT close the browser. Press Ctrl+C to stop.\n")

    while True:
        try:
            # Check session still alive every 2 minutes
            page.evaluate("fetch('/').catch(()=>{})")

            if not is_logged_in(page):
                print("SESSION DIED — please re-login in the browser...")
                input("Press ENTER after re-login...")

            print(f"Alive — {time.strftime('%H:%M:%S')}", end="\r")
            time.sleep(120)

        except KeyboardInterrupt:
            print("\nStopped.")
            break

    context.close()


















# from playwright.sync_api import sync_playwright
# import time, sys
#
# def main():
#     with sync_playwright() as p:
#         context = p.chromium.launch_persistent_context(
#             user_data_dir="./browser_profile",
#             headless=False,
#             args=[
#                 "--remote-debugging-port=9222",  # 👈 add this
#                 "--window-maximized"
#             ]
#         )
#
#         page = context.new_page()
#         page.goto("https://app.nimar.gov.pk")
#
#         # Check if already logged in or need to login
#         time.sleep(3)
#         if "login" in page.url.lower():
#             print("Not logged in — please login manually in the browser...")
#             input("Complete OTP and press ENTER here...")
#         else:
#             print("Already logged in!")
#
#         print("Session keeper running. Press Ctrl+C to stop.")
#         print("DO NOT close the browser window manually.")
#
#         while True:
#             try:
#                 # Keep session alive
#                 page.evaluate("fetch('/').catch(()=>{})")
#                 print(f"  Alive — {time.strftime('%H:%M:%S')}", end="\r")
#                 time.sleep(180)
#
#             except KeyboardInterrupt:
#                 print("\nStopping session keeper...")
#                 break
#             except Exception as e:
#                 print(f"Error: {e} — retrying...")
#                 time.sleep(10)
#
#         context.close()
#
# if __name__ == "__main__":
#     main()