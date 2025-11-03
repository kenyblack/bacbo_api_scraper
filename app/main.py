from flask import Flask, jsonify, make_response
import os, time, logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bacbo_api_scraper')
# Config from env or defaults
TARGET_URL = os.environ.get('TARGET_URL', 'https://casino.bet365.com/play/BacBo')
IFRAMES = [
    '/html/body/div[2]/div[2]/div[1]/main/div[1]/div[3]/iframe',
    '/html/body/div/div/iframe',
    '/html/body/div[5]/div[2]/iframe'
]
ROADS_SELECTOR = os.environ.get('ROADS_SELECTOR', '#root > div > div > div.content--6d02a > div:nth-child(2) > div > div.top-container--67c84 > div.top-right--83089 > div > div > div')
ROUND_CONTAINER_XPATH = os.environ.get('ROUND_XPATH', '/html/body/div[4]/div/div/div[2]/div[2]/div/div[6]/div[2]/div/div/div/div[2]')
PLAYER_CSS = os.environ.get('PLAYER_CSS', '#root > div > div > div.content--6d02a > div.footerWrapper--81d5c > div > div.perspectiveContainer--a9ee2 > div.bettingGrid--b7137 > div > div > div > div > div > div.betSpot--52675.Player--4a71b > div:nth-child(3) > svg > path:nth-child(7)')
BANKER_CSS = os.environ.get('BANKER_CSS', '#root > div > div > div.content--6d02a > div.footerWrapper--81d5c > div > div.perspectiveContainer--a9ee2 > div.bettingGrid--b7137 > div > div > div > div > div > div.betSpot--52675.Banker--80884 > div:nth-child(3) > svg > path:nth-child(7)')
# Helper to create chrome driver
def make_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64)')
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver
def switch_to_iframes(driver):
    driver.switch_to.default_content()
    for path in IFRAMES:
        try:
            iframe = driver.find_element('xpath', path)
            driver.switch_to.frame(iframe)
        except Exception:
            driver.switch_to.default_content()
            continue
def extract_from_round_container(driver):
    try:
        el = driver.find_element('xpath', ROUND_CONTAINER_XPATH)
        text = el.text.strip().lower()
        # attempt to parse tokens like 'player' 'banker' 'tie' from text
        tokens = []
        for word in ['player','banker','tie','player','banker','empate','jogador','banco']:
            if word in text:
                # naive: map to english names
                if 'player' in word or 'jogador' in word:
                    tokens.append('player')
                elif 'banker' in word or 'banco' in word:
                    tokens.append('banker')
                elif 'tie' in word or 'empate' in word:
                    tokens.append('tie')
        if tokens:
            return tokens
    except Exception as e:
        logger.debug('round container not found or empty: %s', e)
    return None
def extract_from_roads(driver):
    try:
        el = driver.find_element('css selector', ROADS_SELECTOR)
        text = el.text.strip().lower()
        # simple heuristic: split by whitespace and map words
        out = []
        for token in text.split():
            if token in ('player','banker','tie','empate','jogador','banco'):
                if token in ('player','jogador'):
                    out.append('player')
                elif token in ('banker','banco'):
                    out.append('banker')
                else:
                    out.append('tie')
        if out:
            return out
    except Exception as e:
        logger.debug('roads extraction failed: %s', e)
    return None
def extract_via_svg_presence(driver):
    # Try to determine last result by checking which SVG path is visible/clickable
    try:
        # check banker first
        try:
            b = driver.find_element('css selector', BANKER_CSS)
            if b.is_displayed():
                return ['banker']
        except Exception:
            pass
        try:
            p = driver.find_element('css selector', PLAYER_CSS)
            if p.is_displayed():
                return ['player']
        except Exception:
            pass
    except Exception as e:
        logger.debug('svg presence check failed: %s', e)
    return None
@app.route('/history', methods=['GET'])
def history():
    # Return recent history as JSON list of 'player'/'banker'/'tie'
    driver = None
    try:
        driver = make_driver()
        driver.get(TARGET_URL)
        time.sleep(2)
        # try switching to iframes and reading
        switch_to_iframes(driver)
        # priority: round container -> roads -> svg presence
        out = extract_from_round_container(driver)
        if not out:
            out = extract_from_roads(driver)
        if not out:
            out = extract_via_svg_presence(driver)
        if not out:
            # try reading page source fallback: look for common words
            src = driver.page_source.lower()
            cand = []
            for word in ['player','banker','tie','empate','jogador','banco']:
                if word in src:
                    # append a single occurrence as fallback
                    if word in ('player','jogador'):
                        cand.append('player')
                    elif word in ('banker','banco'):
                        cand.append('banker')
                    else:
                        cand.append('tie')
            if cand:
                out = cand[:40]
        if not out:
            return make_response(jsonify([]), 200)
        # Normalize and return most recent first (best effort)
        normalized = []
        for v in out:
            if v in ('player','banker','tie'):
                normalized.append(v)
        return make_response(jsonify(normalized[:100]), 200)
    except WebDriverException as e:
        logger.exception('WebDriver error: %s', e)
        return make_response(jsonify({'error':'webdriver','detail':str(e)}), 500)
    except Exception as e:
        logger.exception('unexpected error: %s', e)
        return make_response(jsonify({'error':'unexpected','detail':str(e)}), 500)
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
