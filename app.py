"""
Habit MVP — Flask + Anthropic
==============================
Storage : JSON file (swap for PostgreSQL in production)
AI      : Claude Haiku via Anthropic SDK
Server  : Flask dev server (swap for Gunicorn + Nginx in production)

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 app.py
"""

import json
import os
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic
from flask import Flask, jsonify, request, send_from_directory

# Load from .env file if present — takes priority over system env
load_dotenv(Path(__file__).parent / '.env')

# ── SETUP ──────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static')

API_KEY = os.environ.get('ANTHROPIC_API_KEY')
client  = Anthropic(api_key=API_KEY) if API_KEY else None

if not API_KEY:
    print('\n⚠️   ANTHROPIC_API_KEY not set.')
    print('     Run: export ANTHROPIC_API_KEY=sk-ant-...')
    print('     The UI will load but goal generation will fail.\n')

# ── FILE STORAGE ───────────────────────────────────────────────────
# MVP: plain JSON file. Production: PostgreSQL via Supabase.
DATA_FILE = Path(__file__).parent / 'data.json'

def load_data() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {'goals': [], 'habit_logs': []}

def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2))

def today_str() -> str:
    return date.today().isoformat()

# ── STREAK CALCULATION ─────────────────────────────────────────────
def calculate_streak(habit_logs: list) -> int:
    """Count consecutive days with at least one completed habit."""
    if not habit_logs:
        return 0

    streak    = 0
    check_day = date.today()

    while True:
        day_key     = check_day.isoformat()
        has_any     = any(
            log['date'] == day_key and log['completed']
            for log in habit_logs
        )
        if not has_any:
            break
        streak    += 1
        check_day -= timedelta(days=1)

    return streak

# ── AI PROMPT ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a habit design expert. Convert a life goal into a minimal, actionable habit system.

Rules:
1. Return 3–5 habits only. More than 5 kills consistency.
2. Every habit must be binary — done or not done today.
3. ROI score 1–5: how directly does this habit drive the goal?
4. Be honest about timeframes — do not inflate them to sound encouraging.
5. Output valid JSON only. No prose, no markdown fences, no explanation.\
"""

def build_prompt(goal_text: str, existing_goals: list) -> str:
    other = ', '.join(g['text'] for g in existing_goals) or 'none'
    return f"""\
User's other active goals: {other}

New goal: "{goal_text}"

Return exactly this JSON shape:
{{
  "cluster": {{
    "name": "2–3 word label",
    "icon": "single emoji",
    "color": "orange|green|blue|red|purple"
  }},
  "milestones": [
    {{"label": "concrete checkpoint", "order": 1}}
  ],
  "habits": [
    {{
      "name": "verb-first specific action",
      "frequency": "daily or Nx per week",
      "roi_score": 1,
      "meta_label": "subtitle shown in UI (max 40 chars)",
      "overlaps_goal": null
    }}
  ],
  "plan_summary": {{
    "estimated_timeframe": "honest range",
    "biggest_risk": "most likely failure mode",
    "key_insight": "one non-obvious truth about this goal"
  }}
}}\
"""

# ── HELPERS ───────────────────────────────────────────────────────
def attach_done_state(goal: dict, habit_logs: list, date_key: str) -> dict:
    """Return goal with each habit annotated with today's done state."""
    habits_with_state = [
        {
            **h,
            'done': any(
                log['habit_id'] == h['id'] and
                log['date']     == date_key and
                log['completed']
                for log in habit_logs
            )
        }
        for h in goal['habits']
    ]
    return {**goal, 'habits': habits_with_state}

# ── ROUTES ────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/state')
def get_state():
    """
    GET /api/state
    Returns all goals with today's habit completion state + streak.
    In production: scope by authenticated user_id.
    """
    data    = load_data()
    today   = today_str()

    goals_out = [
        attach_done_state(g, data['habit_logs'], today)
        for g in data['goals']
    ]

    return jsonify({
        'goals':  goals_out,
        'streak': calculate_streak(data['habit_logs']),
        'today':  today,
    })


@app.route('/api/goals', methods=['POST'])
def create_goal():
    """
    POST /api/goals  { "text": "..." }
    Calls Claude to generate a habit plan, persists it, returns the new goal.
    In production: rate-limit per user (max 1 regen per goal per 30 days).
    """
    if not client:
        return jsonify({
            'error': 'ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=sk-ant-...'
        }), 503

    goal_text = (request.json or {}).get('text', '').strip()
    if not goal_text:
        return jsonify({'error': 'Goal text is required'}), 400

    data = load_data()

    try:
        msg = client.messages.create(
            model      = 'claude-haiku-4-5-20251001',
            max_tokens = 1024,
            system     = SYSTEM_PROMPT,
            messages   = [{'role': 'user', 'content': build_prompt(goal_text, data['goals'])}],
        )

        raw = msg.content[0].text

        # Extract JSON robustly — handles any accidental prose
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            raise ValueError(f'No JSON in response: {raw[:200]}')

        plan = json.loads(match.group())

    except Exception as exc:
        return jsonify({'error': f'AI generation failed: {exc}'}), 500

    new_goal = {
        'id':          str(uuid.uuid4()),
        'text':        goal_text,
        'cluster':     plan['cluster'],
        'milestones':  [{**m, 'id': str(uuid.uuid4()), 'done': False}
                        for m in plan.get('milestones', [])],
        'habits':      [{**h, 'id': str(uuid.uuid4())}
                        for h in plan.get('habits', [])],
        'plan_summary': plan.get('plan_summary', {}),
        'created_at':  today_str(),
    }

    data['goals'].append(new_goal)
    save_data(data)

    return jsonify({
        **new_goal,
        'habits': [{**h, 'done': False} for h in new_goal['habits']],
    })


@app.route('/api/habits/<habit_id>/toggle', methods=['POST'])
def toggle_habit(habit_id):
    """
    POST /api/habits/:id/toggle
    Toggles today's completion log for a habit.
    In production: split into POST /complete and DELETE /complete.
    """
    data  = load_data()
    today = today_str()

    existing = next(
        (log for log in data['habit_logs']
         if log['habit_id'] == habit_id and log['date'] == today),
        None,
    )

    if existing:
        existing['completed'] = not existing['completed']
        done = existing['completed']
    else:
        data['habit_logs'].append(
            {'habit_id': habit_id, 'date': today, 'completed': True}
        )
        done = True

    save_data(data)
    return jsonify({'id': habit_id, 'done': done})


@app.route('/api/milestones/<milestone_id>/toggle', methods=['POST'])
def toggle_milestone(milestone_id):
    """PATCH /api/milestones/:id in production."""
    data = load_data()

    for goal in data['goals']:
        for ms in goal['milestones']:
            if ms['id'] == milestone_id:
                ms['done'] = not ms['done']
                save_data(data)
                return jsonify({'id': milestone_id, 'done': ms['done']})

    return jsonify({'error': 'Milestone not found'}), 404


@app.route('/api/reset', methods=['DELETE'])
def reset():
    """Wipe everything. Dev only — remove this route in production."""
    save_data({'goals': [], 'habit_logs': []})
    return jsonify({'ok': True})


# ── START ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n✓  Habit MVP running → http://localhost:3000\n')
    app.run(port=3000, debug=True, use_reloader=False)
