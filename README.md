# Google Maps Software House Scraper

A Python-based web scraper that extracts software house details—including websites, contact information, and other useful data—from Google Maps using Playwright.

## Installation & Setup

Follow these steps to set up your local environment and install all necessary dependencies:

### 1. Create and Activate a Virtual Environment

Open your terminal in the project directory and run:

# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# 1. Install Playwright
pip install playwright

# 2. Install the Chromium browser binary
playwright install chromium

# Usage
    Follow these steps in order to run the scraper successfully:

1. Save Authentication Cookies (Manual Login).
    python save_cookies.py
2. Run the Scraper
    python software_houses_scraper.py