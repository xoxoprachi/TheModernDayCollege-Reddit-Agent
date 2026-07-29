"""
Configuration for the Modern Day College Reddit agent.
Edit this file to tune subreddits, keywords, and the course description
that Claude uses to judge relevance.
"""

# Subreddits to scan every run. Mix of India-focused + global career subs.
SUBREDDITS = [
    "developersIndia",
    "Btechtards",
    "IndianStudents",
    "college",
    "csMajors",
    "cscareerquestions",
    "ITCareerQuestions",
    "internships",
    "jobs",
    "careerguidance",
    "EngineeringStudents",
    "GetStudying",
    "freelance",
    "Entrepreneur",
    "gigwork",
]

# How many of the newest posts to pull per subreddit, per run.
POSTS_PER_SUBREDDIT = 40

# Only consider posts newer than this many hours (avoids re-scanning old threads).
MAX_POST_AGE_HOURS = 30

# Cheap keyword pre-filter, applied BEFORE the AI relevance check, to cut down
# on how many posts we pay to have Claude judge. Case-insensitive substring match
# against title + selftext. A post only needs to match ONE of these.
KEYWORD_PREFILTER = [
    "intern", "internship", "stipend", "paid while studying",
    "part time job", "part-time job", "side income", "earn while",
    "no experience", "zero experience", "first job", "first gig",
    "freelance", "freelancing", "gig work", "remote job",
    "student job", "portfolio", "proof of work",
    "resume", "cv review", "cold email", "cold dm", "cold message",
    "linkedin", "get noticed", "recruiters", "founders",
    "is this internship legit", "internship scam", "fake internship",
    "unpaid internship", "feel lost", "feel behind", "feel stuck",
    "falling behind", "don't know where to start", "no direction",
    "how to get started", "start my own", "startup idea",
    "interview prep", "interview tips", "ats resume",
]

# How many threads to send to Slack per run, at most.
MAX_THREADS_PER_RUN = 10
MIN_THREADS_PER_RUN = 5  # informational only - we send whatever qualifies, up to MAX

# Description of your courses/offering, given to Claude so it can judge fit.
# Edit this to accurately describe what Modern Day College actually teaches/offers.
BRAND_DESCRIPTION = """
Modern Day College is a paid course + community (₹5,999, lifetime content
access + 1 year community access) for college students in India who want to
earn and build a career WITHOUT waiting on traditional campus placements.

It is NOT a placement-prep or campus-recruitment program. It teaches
self-driven income and career-building through:
- Picking a beginner-friendly online skill and landing a first paid gig (~₹10K)
- Building "proof of work" / a portfolio from scratch, with zero prior experience
- Growing a LinkedIn/social presence to get noticed by founders and recruiters
- Finding real internships and freelance gigs beyond Internshala (LinkedIn,
  Twitter/X, Discord, Slack communities, startup job boards)
- Cold DMs and cold emails to founders/recruiters that don't sound desperate
- Building a resume with no internship experience, and passing ATS screening
- Interview prep for students/freshers (self-intro, STAR method, take-home tasks)
- Spotting fake/unpaid/scammy internship offers before wasting time on them
- Turning all of the above into a 30-60-90 day execution plan
- A mindset/discipline track: focus, avoiding FOMO/scroll-doom-loops,
  confidence, and resilience after setbacks

WHO IT'S FOR: college students (any year, any branch) who feel stuck, behind,
or directionless, and are ready to put in effort to earn/build a career on
their own terms rather than wait for campus placements or a "system" to help
them.

We are looking for Reddit threads (usually from students, sometimes recent
grads) that show a real, specific need matching ANY of the above - for
example: "how do I get my first internship with no experience", "is this
internship/offer a scam", "how do I cold email founders", "how do I build a
portfolio/resume with nothing to show", "how do I find freelance work as a
student", "I feel lost/behind in college and don't know what to do", "how do
I get noticed on LinkedIn with no experience".

IMPORTANT NUANCE - since this is a PAID product:
- Prioritize threads showing real frustration, effort, or "I've tried X and Y
  and nothing worked" over someone casually asking for a single free resource
  or link. Someone asking "any free YouTube channels for X" alone is a weak
  fit. Someone saying they're serious, stuck, and want a real system/roadmap
  is a strong fit.
- Do NOT flag threads that are purely about government job exams (UPSC, SSC,
  banking), MBA/CAT prep, study-abroad admissions, or pure academic/exam
  doubts - these are out of scope even if "student" is mentioned.
"""

# Claude model used for relevance judging. Haiku is cheap and sufficient here.
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
