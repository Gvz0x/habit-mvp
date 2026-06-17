# Habit System MVP

An AI-powered habit tracking app. Tell it a goal, it designs the habits to get you there.

You can chat with Claude to refine your goal, or type it directly. It generates a habit plan, you check off habits daily.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey)
![Anthropic](https://img.shields.io/badge/Claude-Haiku-orange)

**Live demo:** https://habit-mvp-production.up.railway.app

---

## How It Works

1. Open the app and tap 💬 to chat with Claude about your goal
2. Claude asks clarifying questions until the goal is specific enough
3. It generates 3–5 daily habits with ROI scores
4. Check off habits each day — progress bar and streak update live
5. Tap milestones to track longer-arc progress

You can also skip the chat and type a goal directly into the input at the bottom.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python + Flask |
| AI | Claude Haiku (`claude-haiku-4-5`) |
| Frontend | Vanilla HTML/CSS/JS |
| Storage | JSON file |
| Hosting | Railway |

---

## Project Structure

```
habit-mvp/
├── app.py              # Flask server + API routes + Claude integration
├── static/
│   └── index.html      # Frontend — UI, state, animations
├── requirements.txt    # Python dependencies
├── demo/
│   └── index.html      # Static mockup (Netlify)
├── forge-mockup.html   # Design mockup v1
└── forge-mockup-v2.html # Design mockup v2 (mobile-first, interactive)
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/state` | All goals + today's habit completion state + streak |
| `POST` | `/api/goals` | Add a goal — calls Claude, returns generated habit plan |
| `POST` | `/api/chat` | Conversational goal refinement with Claude |
| `POST` | `/api/habits/:id/toggle` | Toggle today's completion for a habit |
| `POST` | `/api/milestones/:id/toggle` | Toggle a milestone done/undone |
| `DELETE` | `/api/reset` | Wipe all data |

---

## Data Models

```json
// Goal
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

// Habit log
{ "habit_id": "uuid", "date": "2026-06-17", "completed": true }
```

---

## Running Locally

```bash
# Clone
git clone https://github.com/Gvz0x/habit-mvp.git
cd habit-mvp

# Install dependencies
pip install -r requirements.txt

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Run
python3 app.py
```

Open `http://localhost:3000`.
