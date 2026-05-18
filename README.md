# CoinDCX Support Chat Automation

GitHub-ready Selenium project to open CoinDCX support, trigger chat, send a message, wait for response, and save output.

## Files
- `app.py`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `LICENSE`

## Quick Start
1. Create and activate a venv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional env vars:
   - `SUPPORT_MESSAGE`
   - `HEADLESS=true|false`
4. Run:
   ```bash
   python app.py
   ```

## Output
- `live_status.json`
- `coindcx_support_result.json`
- `*.png` screenshots on failure

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial CoinDCX support automation"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
