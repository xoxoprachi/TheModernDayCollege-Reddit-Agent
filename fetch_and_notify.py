"""
Modern Day College - Daily Reddit Thread Finder
-------------------------------------------------
Scans a list of subreddits for new posts, uses keyword pre-filtering + Claude
to judge relevance to Modern Day College's course offerings, sends 5-10 new
(never-before-sent) threads to Slack, and remembers what's been sent so the
same thread is never repeated.

Run via GitHub Actions on a daily schedule. See .github/workflows/daily.yml
"""

import os
import re
import json
import time
import datetime
import requests
import feedparser

import config

SENT_FILE = "sent_threads.json"

# Reddit blocks default/generic user agents. Use something descriptive.
HEADERS = {
    "User-Agent": "ModernDayCollegeRedditDigest/1.0 (personal daily digest bot)"
}


def load_sent_threads():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return {}


def save_sent_threads(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f, indent=2)


def keyword_prefilter(title, selftext):
    text = f"{title} {selftext}".lower()
    return any(kw in text for kw in config.KEYWORD_PREFILTER)


def extract_post_id(entry_id_or_link):
    """Reddit RSS entry ids/links look like .../comments/<post_id>/<slug>/"""
    match = re.search(r"/comments/([a-z0-9]+)/", entry_id_or_link)
    return match.group(1) if match else entry_id_or_link


def strip_html(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    return re.sub(r"\s+", " ", text).strip()


def extract_subreddit_from_link(link):
    match = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)/comments/", link)
    return match.group(1) if match else "unknown"


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def fetch_candidate_posts(sent_ids):
    """Pull recent posts via batched multi-subreddit RSS requests (no API key
    needed), apply age + keyword filter, and skip anything already sent.
    Subreddits are combined with '+' into groups so we make far fewer HTTP
    requests overall, which avoids Reddit's rate limiting on shared IPs
    (like GitHub Actions runners)."""
    cutoff = time.time() - (config.MAX_POST_AGE_HOURS * 3600)
    candidates = []

    for group in chunked(config.SUBREDDITS, 5):
        combined = "+".join(group)
        url = f"https://www.reddit.com/r/{combined}/new/.rss?limit={config.POSTS_PER_SUBREDDIT * len(group)}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 429:
                print(f"[warn] rate limited on group {combined}, waiting 15s and retrying once...")
                time.sleep(15)
                resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            for entry in feed.entries:
                link = entry.get("link", "")
                post_id = extract_post_id(entry.get("id", link))
                if post_id in sent_ids:
                    continue

                if "published_parsed" in entry and entry.published_parsed:
                    created_ts = time.mktime(entry.published_parsed)
                    if created_ts < cutoff:
                        continue

                title = entry.get("title", "")
                selftext = strip_html(entry.get("summary", ""))[:1200]

                if not keyword_prefilter(title, selftext):
                    continue

                candidates.append(
                    {
                        "id": post_id,
                        "subreddit": extract_subreddit_from_link(link),
                        "title": title,
                        "selftext": selftext,
                        "url": link,
                    }
                )
        except Exception as e:
            print(f"[warn] failed to fetch group {combined}: {e}")

        time.sleep(5)  # be polite to Reddit's servers between batches

    return candidates


def judge_relevance(post):
    """Ask Claude whether this post is relevant to Modern Day College, and why.
    Returns dict: {"relevant": bool, "reason": str, "course_angle": str} or None on failure.
    """
    prompt = f"""{config.BRAND_DESCRIPTION}

Here is a Reddit post to evaluate:

Subreddit: r/{post['subreddit']}
Title: {post['title']}
Body: {post['selftext'] if post['selftext'] else '(no body text, title only)'}

Decide if this post is a genuine opportunity for Modern Day College to
helpfully engage (e.g. answer a real question, offer guidance, mention a
relevant course/resource) - NOT spam, NOT a meme, NOT unrelated venting with
no actionable question.

Respond with ONLY a JSON object, no other text, in this exact format:
{{"relevant": true or false, "reason": "one sentence why", "course_angle": "one short phrase naming which course/topic fits, or empty string if not relevant"}}
"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.CLAUDE_MODEL,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if response.status_code != 200:
            print(f"[warn] Anthropic API returned {response.status_code}: {response.text[:500]}")
        response.raise_for_status()
        data = response.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        ).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[warn] relevance check failed for post {post['id']}: {e}")
        return None


def send_to_slack(threads):
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    today = datetime.date.today().strftime("%B %d, %Y")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📌 Modern Day College — Reddit digest ({today})"},
        },
        {"type": "divider"},
    ]

    for t in threads:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*<{t['url']}|{t['title']}>*\n"
                        f"r/{t['subreddit']}  •  _{t['course_angle']}_\n"
                        f"{t['reason']}"
                    ),
                },
            }
        )
        blocks.append({"type": "divider"})

    payload = {"text": f"Modern Day College — {len(threads)} new Reddit threads today", "blocks": blocks}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()


def check_anthropic_key():
    """Quick standalone check so a bad key fails loudly once, with a clear
    reason, instead of silently failing on every single post."""
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.CLAUDE_MODEL,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say OK"}],
            },
            timeout=30,
        )
        if response.status_code == 200:
            print("[info] Anthropic API key check: OK")
            return True
        else:
            print(f"[ERROR] Anthropic API key check FAILED ({response.status_code}): {response.text[:500]}")
            return False
    except Exception as e:
        print(f"[ERROR] Anthropic API key check FAILED: {e}")
        return False


def main():
    if not check_anthropic_key():
        print("[ERROR] Stopping early - fix ANTHROPIC_API_KEY before continuing.")
        return

    sent = load_sent_threads()
    sent_ids = set(sent.keys())

    candidates = fetch_candidate_posts(sent_ids)
    print(f"Found {len(candidates)} keyword-matched candidates after dedup.")

    relevant_threads = []
    for post in candidates:
        if len(relevant_threads) >= config.MAX_THREADS_PER_RUN:
            break
        verdict = judge_relevance(post)
        if verdict and verdict.get("relevant"):
            post["reason"] = verdict.get("reason", "")
            post["course_angle"] = verdict.get("course_angle", "")
            relevant_threads.append(post)

    if not relevant_threads:
        print("No relevant new threads found today. Skipping Slack post.")
        return

    send_to_slack(relevant_threads)
    print(f"Sent {len(relevant_threads)} threads to Slack.")

    now = datetime.datetime.utcnow().isoformat()
    for post in relevant_threads:
        sent[post["id"]] = {
            "title": post["title"],
            "subreddit": post["subreddit"],
            "sent_at": now,
        }
    save_sent_threads(sent)


if __name__ == "__main__":
    main()
