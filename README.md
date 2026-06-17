# Habit System MVP

An AI-powered habit tracking app that takes your life goals and designs the daily habits to get you there.

You type a goal. Claude generates a habit plan. You check off habits daily.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)
![Anthropic](https://img.shields.io/badge/Claude-Haiku-orange)

---

## How It Works

1. Enter a life goal (e.g. "Become a black belt in BJJ")
2. Claude Haiku analyses the goal and generates 3–5 high-ROI habits
3. Habits appear grouped under a goal cluster
4. Check off habits daily — progress bar and streak update live
5. Tap milestones to track longer-arc progress

---

## Stack

| Layer | Tech | Notes |
|---|---|---|
| Backend | Python + Flask | REST API, file-based storage |
| AI | Claude Haiku (`claude-haiku-4-5`) | Goal → habit generation |
| Frontend | Vanilla HTML/CSS/JS | No framework, single file |
| Storage | JSON file | Swap for PostgreSQL in production |

---

## Project Structure

```
habit-mvp/
├── app.py              # Flask server + API routes + Claude integration
├── static/
│   └── index.html      # Full frontend — UI, state, animations
├── data.json           # Auto-created on first run (git-ignored)
├── .env                # API key (git-ignored)
├── forge-mockup.html   # Design mockup v1
└── forge-mockup-v2.html # Design mockup v2 (mobile-first, interactive)
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/state` | All goals + today's habit completion state + streak |
| `POST` | `/api/goals` | Add a goal — calls Claude, returns generated habit plan |
| `POST` | `/api/habits/:id/toggle` | Toggle today's completion for a habit |
| `POST` | `/api/milestones/:id/toggle` | Toggle a milestone done/undone |
| `DELETE` | `/api/reset` | Wipe all data (dev only) |

---

## Data Models

```json
// Goal (stored in data.json)
{
  "id": "uuid",
  "text": "Become a black belt in BJJ",
  "cluster": { "name": "BJJ Progression", "icon": "🥋", "color": "blue" },
  "habits": [
    {
      "id": "uuid",
      "name": "Attend BJJ class",
      "frequency": "3x per week",
      "roi_score": 5,
      "meta_label": "Mat time is non-negotiable"
    }
  ],
  "milestones": [
    { "id": "uuid", "label": "Achieve 4 stripes at white belt", "order": 1, "done": false }
  ],
  "plan_summary": {
    "estimated_timeframe": "18–36 months",
    "biggest_risk": "Inconsistent attendance",
    "key_insight": "Technique beats strength, but only if you train it daily"
  }
}

// Habit log entry
{ "habit_id": "uuid", "date": "2026-06-17", "completed": true }
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
# Clone the repo
git clone https://github.com/Gvz0x/habit-mvp.git
cd habit-mvp

# Install dependencies
pip install flask anthropic python-dotenv

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Run
python3 app.py
```

Open `http://localhost:3000` in your browser.

---

## Roadmap

This is an MVP. The production version would include:

- [ ] User authentication (Supabase Auth)
- [ ] PostgreSQL database (replacing JSON file)
- [ ] Redis caching for streaks and daily habit state
- [ ] Weekly Honest Hour — AI-powered weekly reflection and habit adjustment
- [ ] Mobile app (React Native)
- [ ] BigQuery analytics pipeline via dbt + Looker Studio

---

## Architecture Notes (Production)

```
Mobile (React Native)  ←→  FastAPI backend  ←→  PostgreSQL + Redis
                                ↓
                         Claude Haiku API
                                ↓
                    BigQuery (nightly export via dbt)
                                ↓
                         Looker Studio dashboard
```

AI fires **infrequently** — only on goal creation and weekly review. Daily habit interactions are pure database reads/writes, keeping costs minimal (~$0.0003/user/week).

---

## Cost Estimate

| Scale | AI cost | Infra cost | Per-user/year |
|---|---|---|---|
| 1,000 users | ~$2,600/yr | ~$540/yr | ~$3.14 |
| 10,000 users | ~$26,000/yr | ~$3,000/yr | ~$2.90 |
