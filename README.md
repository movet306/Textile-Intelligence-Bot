# Textile Intelligence Bot
### Automated Multi-Source News Aggregation, AI Summarization & Telegram Delivery Pipeline

> **Tech Stack:** n8n · OpenAI GPT-4o-mini API · Telegram Bot API · JavaScript · Web Scraping  
> **Author:** Mert Ovet | [LinkedIn](https://linkedin.com/in/mertovet)

---

## Project Overview

I built this project to solve a real problem I face daily: staying up to date with global textile industry news across multiple sources, in multiple languages, without spending time every morning reading through sites manually.

The result is a fully automated pipeline that scrapes 4 international and local textile news sources every morning at 08:00, extracts article titles and links using custom JavaScript parsing, sends each title through OpenAI's GPT-4o-mini API for AI summarization, and delivers clean Turkish-language briefings with clickable source links directly to Telegram — all without any manual input.

This is my second iteration of the project. The first version taught me where the real technical challenges are. This version solves them properly.

---

## The Problem

Our family business operates in textile manufacturing — weaving, dyeing, lamination, coating, and yarn imports. Keeping track of raw material price movements, new technologies, and global market shifts is critical but time-consuming.

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

## Pipeline Architecture

<img width="1880" height="937" alt="image" src="https://github.com/user-attachments/assets/a05440fb-930e-4d86-9a8e-715d57cb7929" />


The system runs 4 independent parallel pipelines, all triggered by a single Schedule Trigger at 08:00 daily. Each pipeline is fully self-contained — if one source fails, the others continue unaffected.

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

```

**Key decisions:**
- **GPT-4o-mini** over GPT-4o — cost efficiency. Daily cost is well under $0.01 for all 4 pipelines combined
- **Title-only input** — instead of sending full HTML content (which hits token limits and loses URL context), I send only the article title. The model summarizes based on title alone, which works well for news headlines
- **150 max tokens** — enough for 2-3 sentences, prevents runaway responses
- **Turkish output** — eliminates a separate translation step for English sources

### 4. Telegram Delivery

Each pipeline sends its summaries to a private Telegram bot (`@tekstil_haber_bot`) created via BotFather. The message format:
{{ $json.choices[0].message.content }}
🔗 {{ $('Code in JavaScript').item.json.url }}

The URL is retrieved directly from the Code node's output using n8n's node reference syntax — this is how we preserve the article link across the OpenAI API call.


## Output Samples

Every morning the bot delivers messages like this for each source:

<img width="945" height="2048" alt="image" src="https://github.com/user-attachments/assets/46d87c0c-4d7d-457e-a12f-e3a3a2899eef" />

<img width="945" height="2048" alt="image" src="https://github.com/user-attachments/assets/8e184d55-ff95-4d54-98e8-c050d4698148" />

<img width="945" height="2048" alt="image" src="https://github.com/user-attachments/assets/f074de58-2cf8-4a0f-8be1-eec1db176175" />

## Architecture Decisions

| Decision | Alternative Considered | Reason |
|----------|----------------------|--------|
| Manual OpenAI HTTP Request | n8n built-in OpenAI node | URL field preservation |
| 4 independent pipelines | Single merged pipeline | Fault isolation, URL tracking |
| Title-only AI input | Full HTML content | Token limits, URL loss |
| GPT-4o-mini | GPT-4o | Cost — ~100x cheaper, sufficient quality |
| Telegram | WhatsApp, Email | Easiest n8n integration, free |

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

## Project Owner

**Mert Ovet**  
[LinkedIn: linkedin.com/in/mertovet](https://linkedin.com/in/mertovet)
