# Textile Intelligence Bot
### Automated Multi-Source News Aggregation, AI Summarization & Telegram Delivery Pipeline

> **Tech Stack:** n8n · OpenAI GPT-4o-mini API · Telegram Bot API · Google Sheets API · JavaScript · Web Scraping

> **Project Owner:** Mert Ovet | [LinkedIn](https://linkedin.com/in/mertovet)

---

## Project Overview

I built this project to solve a real problem I face daily: staying up to date with global textile industry news across multiple sources, in multiple languages, without spending time every morning reading through sites manually.

The result is a fully automated pipeline that scrapes 4 international and local textile news sources every morning at 08:00, extracts article titles and links using custom JavaScript parsing, sends each title through OpenAI's GPT-4o-mini API for AI summarization, and delivers clean Turkish-language briefings with clickable source links directly to Telegram — all without any manual input.

This project has gone through three iterations. The first version established the core pipeline but ran locally — it only fired when my laptop was on, which defeated the purpose of a fully automated morning briefing. The second moved the entire workflow to Railway's cloud infrastructure, making it run 24/7 regardless of local machine state. The third — and current — version adds a persistent memory system: the bot now tracks every article it has ever delivered, and never sends the same story twice.
The sections below document both layers: the pipeline architecture that handles scraping, AI summarization, and Telegram delivery, and the memory system built on top of it that makes the whole thing reliable as a daily briefing tool.

---

## The Problem

Our family business operates in textile manufacturing. So, keeping track of raw material price movements, new technologies, and global market shifts is critical but time-consuming.

**Before this project:**
- Manually checking 4-5 websites every morning
- Content in English, no quick way to prioritize
- No consolidated view of what actually matters that day

**After this project:**
- Multiple Telegram messages every morning at 08:00
- AI-filtered, Turkish-summarized, sector-specific news
- Each summary includes a direct clickable link to the full article
- Zero manual effort

---

## The first Pipeline Architecture (Before the Memory System)

<img width="900" alt="Pipeline architecture" src="https://github.com/user-attachments/assets/a05440fb-930e-4d86-9a8e-715d57cb7929" />

The system runs 4 independent parallel pipelines, all triggered by a single Schedule Trigger at 08:00 daily. Each pipeline is fully self-contained. If one source fails, the others continue unaffected.

**Design decision:** I chose 4 independent pipelines over a single merged pipeline deliberately. In the first version of this project, I tried merging all sources into one stream before passing to AI — this caused the article URLs to get lost in the data flow. The independent pipeline approach keeps each article's metadata (title, url, source) intact throughout the entire chain.

---

## Technical Implementation

### 1. Web Scraping (HTTP Request Nodes)

Each pipeline starts with an HTTP GET request to a news source. No authentication or API keys required — pure open-web scraping.

**Sources:**
| Source | URL | Language |
|--------|-----|----------|
| Just Style | just-style.com/news | English |
| Textile World | textileworld.com | English |
| Dünya Gazetesi | dunya.com/sektorler/tekstil | Turkish |
| Fibre2Fashion | fibre2fashion.com/news/textile-news | English |

The raw HTML returned by each request is passed directly to the next node for parsing.

### 2. Custom JavaScript Parsing (Code Nodes)

Each source has a different HTML structure, so I wrote a custom parser for each one. The parsers use regex to extract article titles and URLs from raw HTML, filter out navigation links and category pages, and return a clean array of `{ title, url, source }` objects.

The approach varies by site. For most sources, the title lives inside the anchor tag itself. For Dünya Gazetesi, the URL pattern is distinct (`haberi-\d+`) but the title sits in a nearby `<span>` element — so the parser locates the URL first, then searches the surrounding HTML for the title.

Every parser returns the same structure:
```javascript
results.push({
  title: title,
  url: url,
  source: 'Source Name'
});
```

This consistent output is what allows the rest of the pipeline — OpenAI call, Telegram delivery — to work identically regardless of which source the data came from.

### 3. OpenAI API Integration (Manual HTTP Request)

Rather than using n8n's built-in OpenAI node, I call the API directly via HTTP Request. This was a deliberate architectural choice — the built-in node doesn't pass input fields through to its output, which meant article URLs were getting lost. The manual HTTP Request approach gives full control over both input and output.

**Key decisions:**
- **GPT-4o-mini** over GPT-4o — cost efficiency. Daily cost is well under $0.01 for all 4 pipelines combined
- **Title-only input** — instead of sending full HTML content (which hits token limits and loses URL context), I send only the article title. The model summarizes based on title alone, which works well for news headlines
- **150 max tokens** — enough for 2-3 sentences, prevents runaway responses
- **Turkish output** — eliminates a separate translation step for English sources

### 4. Telegram Delivery

Each pipeline sends its summaries to a private Telegram bot (`@tekstil_haber_bot`) created via BotFather. The message format:

```
{{ $json.choices[0].message.content }}
🔗 {{ $('Code in JavaScript').item.json.url }}
```

The URL is retrieved directly from the Code node's output using n8n's node reference syntax — this is how we preserve the article link across the OpenAI API call.

---

## Output Samples

Every morning the bot delivers messages like this for each source:

<img width="400" alt="Telegram output sample 1" src="https://github.com/user-attachments/assets/46d87c0c-4d7d-457e-a12f-e3a3a2899eef" />

<img width="400" alt="Telegram output sample 2" src="https://github.com/user-attachments/assets/8e184d55-ff95-4d54-98e8-c050d4698148" />

<img width="400" alt="Telegram output sample 3" src="https://github.com/user-attachments/assets/f074de58-2cf8-4a0f-8be1-eec1db176175" />

---

## Architecture Decisions

| Decision | Alternative Considered | Reason |
|----------|----------------------|--------|
| Manual OpenAI HTTP Request | n8n built-in OpenAI node | URL field preservation |
| 4 independent pipelines | Single merged pipeline | Fault isolation, URL tracking |
| Title-only AI input | Full HTML content | Token limits, URL loss |
| GPT-4o-mini | GPT-4o | Cost — ~100x cheaper, sufficient quality |
| Telegram | WhatsApp, Email | Easiest n8n integration, free |

---

### 5. Credentials & Setup

This project requires three external credentials to run:

**OpenAI API Key**
- Obtained from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Used in the HTTP Request node as a Bearer token in the Authorization header
- Model used: `gpt-4o-mini` — cost-efficient, sufficient for headline summarization
- Estimated monthly cost for this use case: under $0.30

**Telegram Bot Token**
- Created via [@BotFather](https://t.me/BotFather) on Telegram
- Send `/newbot`, choose a name and username ending in `_bot`
- BotFather returns a token in the format `123456789:ABCdef...`
- Used in n8n's Telegram node credential setup

**Telegram Chat ID**
- Your personal Telegram user ID — not a username
- Obtained by messaging [@userinfobot](https://t.me/userinfobot) and sending `/start`
- Returns your numeric ID (e.g. `7984195604`)
- Used as the `chatId` parameter in each Telegram node

## 6. Cloud Deployment

The pipeline is deployed on Railway using the official n8n Docker image, running 24/7 regardless of local machine state.

**The problem it solves:** During development, n8n ran locally. This meant the Schedule Trigger only fired when my machine was on — defeating the purpose of a fully automated morning briefing.

**The solution:** Migrated the entire workflow to Railway's cloud infrastructure using a production-grade template (n8n with workers, Redis, and PostgreSQL). The deployment took under 10 minutes.

| Component | Role |
|---|---|
| Primary (n8n) | Workflow execution engine |
| Worker | Handles background job processing |
| Redis | Queue management between primary and worker |
| PostgreSQL | Persistent workflow and execution storage |

**Key outcome:** The workflow is now published and running on a Railway-hosted URL. Every morning at 08:00, the pipeline executes automatically — no local dependency, no manual trigger, no open laptop required.

## Version 2: Persistent Memory System

### The Problem I Noticed

After the pipeline had been running for several days, a clear pattern emerged: **the same articles kept appearing in Telegram every morning.**

News sites keep their articles on the front page for days — sometimes weeks. So every time the bot ran, it would scrape the same headlines it had already processed the day before, pass them through OpenAI, and deliver them again to Telegram. There was no mechanism to distinguish between a genuinely new article and one that had already been delivered.

The fix required the bot to have **persistent memory** — a record of every article it had ever sent, that it could check against on each new run.

---

### Choosing the Right Storage Solution

| Option | Problem |
|--------|---------|
| n8n internal database | Not easily queryable from Code nodes mid-execution |
| External database (PostgreSQL, Redis) | Requires additional infrastructure and credentials |
| Google Sheets | Simple, free, human-readable, natively supported in n8n |

Google Sheets was the clear choice for this scale. It acts as an append-only log of delivered articles — visible, editable, and easy to reset if needed. No extra infrastructure required beyond what Railway already provides.

---

### Setting Up the Google Sheets Integration

**Google Cloud & Service Account**


Rather than OAuth2 — which requires periodic re-authentication and would silently break the morning automation — I used a **Google Service Account**. A service account key never expires and requires no human interaction after initial setup.

I created a dedicated Google Cloud project (`n8n-textile-bot`), enabled the Google Sheets API, and created a Service Account named `tekstil-haber-bot`. The setup generates a JSON key file containing a `private_key` and `client_email` — these are what n8n uses to authenticate.

> *<img width="1568" height="750" alt="image" src="https://github.com/user-attachments/assets/0426614c-d519-4f9d-b5e8-deea684d1610" />
*

**The Memory Sheet**

I created a Google Sheet called **Textile News Memory** with two columns: `title` and `date`, shared with the service account email as Editor. Every article delivered to Telegram is written here. On the next run, the bot reads this sheet before doing anything else.

> *<img width="2812" height="1450" alt="image" src="https://github.com/user-attachments/assets/bf8b1a24-b29a-45cb-a018-d2f3fefd7e33" />
*

In n8n, I added a credential of type **Google Service Account API** — not OAuth2 — using the `client_email` and `private_key` from the JSON key file. This single credential is shared across all four pipelines.

---

### Rethinking the Pipeline Architecture

The first approach I tried was adding an IF node after the JavaScript parser — check each article against the sheet, route new ones forward, drop old ones. This failed for a fundamental reason: the IF node only evaluates one condition at a time. When the parser returns 5 articles, the IF node checks the first one and routes it correctly, but the remaining 4 pass through regardless of whether they had been seen before.

The solution was to move the Google Sheets read to **before** the JavaScript parser — making it the second node in every pipeline, right after the HTTP Request. The Code node can reference any upstream node by name, so the parser can simultaneously pull the raw HTML from the scraping node and the full list of saved titles from the Sheets node, filtering everything in a single pass. No branching. No IF nodes. No conditional routing.

The final pipeline order for each source:

```
HTTP Request (scrape site)
  → Get row(s) in sheet (read full memory — no filters)
    → Code in JavaScript (parse HTML + deduplicate against sheet)
      → HTTP Request (OpenAI summarize)
        → Telegram (deliver)
          → Append row in sheet (write to memory)
```

> *<img width="2420" height="1094" alt="image" src="https://github.com/user-attachments/assets/488e6c5a-e67a-4576-971f-8c999588de56" />
*

---

### The JavaScript Parsers: Updated for Deduplication

Each parser now builds two sets before iterating: `savedTitles` (pulled from the Google Sheet — articles already delivered) and `seenTitles` (duplicates found within the current page's HTML). An article is only added to the output if its title appears in neither set.

Each source required a slightly different extraction approach based on its HTML structure. Most sources embed the article title directly inside the anchor tag, so a single regex captures both the URL and the title in one pass. Dünya Gazetesi is the exception — titles are not inside the anchor tag, so I extract URLs first using their unique article ID pattern (`haberi-\d+`), then derive the title from the URL slug.

Every parser returns the same structure regardless of source — `{ title, url, source }` — which is what allows the OpenAI, Telegram, and Sheets nodes downstream to work identically across all four pipelines.

If a parser returns zero items, the pipeline stops naturally at that node. No OpenAI calls are made, no Telegram messages are sent, no sheet writes occur.

---

### Writing to Memory: The Append Row Node

After each article is delivered to Telegram, its title and timestamp are written back to the Google Sheet:

```
title: {{ $('Code in JavaScript').item.json.title }}
date:  {{ $now.toISO() }}
```

The `.item` reference is critical here. Because the pipeline processes multiple articles per run, each write must correspond to the article currently being processed — not always the first one. Using `.first()` would write the same title to the sheet repeatedly, once for each item in the pipeline, completely defeating the memory system.

> *<img width="2761" height="1345" alt="image" src="https://github.com/user-attachments/assets/930eda21-1e23-470f-9b8f-8b4a8987f3ce" />
*

---

### Key Decisions in This Update

| Decision | Alternative Tried | Why I Changed It |
|----------|-------------------|----------------|
| Read sheet before parser | IF node after parser | IF node only checks first item, rest pass through unfiltered |
| Filter inside Code node (single pass) | Separate filter node downstream | Node reference errors across branches |
| Service Account auth | OAuth2 | OAuth tokens expire, breaks automation silently |
| `.item` reference in Append Row | `.first()` | `.first()` writes same title N times, defeating the memory system |
| `Always Output Data` on Get Row(s) | Default behavior | Pipeline halts on first run when sheet is empty |

---

---

## Python Version

In addition to the n8n pipeline, I built a pure Python implementation of the same system as part of my AI engineering learning path.

**Located in:** [`python-version/`](https://github.com/movet306/Textile-Intelligence-Bot/tree/main/python-version)

### What it does

- Scrapes all 4 news sources using `requests` and `BeautifulSoup`
- Sends collected headlines to OpenAI API in a single batch call
- Returns a consolidated Turkish-language summary of the day's textile news

### Tech stack

| Library | Purpose |
|---------|---------|
| `requests` | HTTP requests to news sources |
| `beautifulsoup4` | HTML parsing and headline extraction |
| `openai` | OpenAI API integration |
| `python-dotenv` | Secure API key management via `.env` |

### How to run
```bash
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your OpenAI API key
echo OPENAI_API_KEY=your-key-here > .env

# 4. Run
python fetch_news.py
```

### Key difference from n8n version

The n8n version processes each article individually and sends separate Telegram messages. The Python version collects all headlines first, then summarizes them in a single OpenAI call — a more token-efficient approach that produces a consolidated daily briefing.


---
## Project Owner

**Mert Ovet**  
[LinkedIn: linkedin.com/in/mertovet](https://linkedin.com/in/mertovet)
