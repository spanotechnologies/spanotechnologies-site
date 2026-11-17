# Automatic stock updates — setup notes

Goal: the "In stock now" section on spanotechnologies.com refreshes itself from eBay every
few hours, with no manual upload.

## What is ready (2026-11-17)

- `fetch_stock.py` — reads the store's public listings through eBay's Browse API using an
  application token. Tested locally: it found the live listing. It cannot see orders or change
  anything on eBay.
- `refresh-stock.yml` — the GitHub Actions workflow: fetch listings, run `build.py`, publish.

## What is left (needs Cole at the keyboard)

1. **Git access on the Mac.** In Terminal: `brew install gh` (if needed), then `gh auth login`
   and sign in as `spanotechnologies`. Cole does the sign-in.
2. **Move the source into the repo.** Today the repo holds only the built pages, uploaded by
   hand. Push this whole folder instead (`src/`, `build.py`, `automation/`, `site/assets/`),
   with the workflow at `.github/workflows/refresh-stock.yml`. Leave `preview/`, `brand/` and
   `ebay_profile.py` out (add a `.gitignore`).
3. **Add two secrets** in the repo: Settings → Secrets and variables → Actions →
   `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`. Cole pastes these himself. They are the same
   app keys laptop-tools uses; they only read public listings here.
4. **Switch Pages to Actions:** Settings → Pages → Source → "GitHub Actions". The custom
   domain and HTTPS settings stay as they are.
5. Run the workflow once by hand (Actions tab → "Build and publish site" → Run workflow) and
   check the live site.

After that, updating the site is `git push`, and stock refreshes on its own every 3 hours.

## Notes

- `build.py` writes a local preview mirror only if the scratch folder exists; on GitHub it
  skips that step.
- The numbers in `src/data.json` (items sold, feedback score) stay manual: the public API
  does not expose them.
