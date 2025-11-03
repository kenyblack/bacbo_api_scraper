BacBo API Scraper (Flask + Selenium)
----------------------------------
This service exposes /history which returns a JSON array of recent results: ["player","banker","tie",...]
IMPORTANT: This scraper loads Bet365 in a headless Chrome instance and attempts to read the page content.
Deploying this to a public host requires the host to support Docker with Chrome and chromedriver (e.g., Railway with Docker, Render with Docker, Fly.io, or a VPS).

How to deploy (Railway - Docker):
1. Create an account on https://railway.app
2. New Project -> Deploy from GitHub (or Upload ZIP)
3. Push this project and deploy. Railway will build the Dockerfile and run the service.
4. After deploy, get the service URL and call /history

Environment variables (optional):
- TARGET_URL : URL to load (default Bet365 BacBo)
- PLAYER_CSS, BANKER_CSS, ROADS_SELECTOR, ROUND_XPATH : selectors (defaults set)

Notes & risks:
- Scraping live gambling sites may violate terms of service. Use at your own risk.
- The page structure may change and selectors may need updates.
- Headless Chrome in some hosts may be blocked; test locally first.
