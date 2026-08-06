# Modern Day College — Daily Reddit Digest Agent

Every day this agent scans a list of subreddits, finds new threads relevant to
Modern Day College's courses (internships while studying, paid opportunities,
early job offers, fast placement after graduation, startups/freelancing), and
sends 5–10 **new, never-before-sent** threads to a Slack channel. It remembers
what it already sent you, so nothing repeats unless a genuinely new question
comes up.

## What's in this repo

- `fetch_and_notify.py` — the main script
- `config.py` — subreddit list, keyword pre-filter, and your course description (**edit this to match your real offerings**)
- `sent_threads.json` — memory file (auto-updated by the workflow, don't edit by hand)
- `.github/workflows/daily.yml` — the free scheduler (GitHub Actions)
- `requirements.txt` — Python dependencies

## How it fetches Reddit data

This version reads each subreddit's **public RSS feed** (e.g.
`reddit.com/r/internships/new/.rss`) instead of using Reddit's official Data
API. This means **no Reddit developer account or API key is needed at all** —
it sidesteps Reddit's app-approval process entirely, which is useful if
you've hit signup/captcha issues there. The tradeoff: RSS gives slightly less
data per post than the full API, and Reddit could tighten access to RSS at
some point without notice. If you later get proper API access, this can be
swapped back — ask for help if you want that.

## One-time setup (about 10 minutes)

### 1. Create a GitHub repo
Push this whole folder to a new **public or private** GitHub repo (private repos get 2,000 free Actions minutes/month, which is more than enough for a once-daily job).

### 2. Get an Anthropic API key
1. Go to https://console.anthropic.com
2. API Keys → Create Key
3. Add a small amount of prepaid credit (a few dollars covers months of this job — it uses the cheap Haiku model)

### 3. Get a Slack Incoming Webhook URL
1. Go to https://api.slack.com/apps → Create New App → From scratch
2. Under "Incoming Webhooks", toggle it on → "Add New Webhook to Workspace"
3. Choose the channel you want the daily digest posted to
4. Copy the webhook URL (looks like `https://hooks.slack.com/services/...`)

### 4. Add secrets to your GitHub repo
In your repo: **Settings → Secrets and variables → Actions → New repository secret**. Add these two:
- `ANTHROPIC_API_KEY`
- `SLACK_WEBHOOK_URL`

### 5. Turn it on
That's it — the workflow in `.github/workflows/daily.yml` runs automatically every day at 08:00 IST. You can also trigger it manually any time from the **Actions** tab → "Daily Reddit Digest" → "Run workflow" (useful for testing before you wait for the schedule).

## Tuning it

- **`config.py`** — add/remove subreddits, adjust keywords, and importantly, rewrite `BRAND_DESCRIPTION` to precisely describe your actual courses so Claude judges relevance accurately.
- **Schedule** — edit the cron line in `daily.yml` (cron times are in UTC; IST is UTC+5:30).
- **Volume** — `MAX_THREADS_PER_RUN` in `config.py` controls the cap (default 10).

## Cost

- GitHub Actions: free at this volume
- Reddit RSS: free
- Slack: free
- Anthropic API: pay-as-you-go, roughly $2–5/month depending on volume, since it uses the cheap Haiku model for relevance judging

## How duplicate prevention works

Every thread ID that gets sent to Slack is logged in `sent_threads.json` with a timestamp. The next run skips any post ID already in that file — so the same thread is never sent twice, but a genuinely new post (even in the same subreddit, about a similar topic) is fair game.
