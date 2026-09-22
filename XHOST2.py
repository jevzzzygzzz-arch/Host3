# -*- coding: utf-8 -*-
"""
ATX Hosting - XHOST Bot v6.1 (Malware Scanner Removed)
- Walang malware scanner (para walang false positive)
- Fixed admin add/remove
- AI Generator with bot token + admin ID
- Complete handlers
"""
import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import random
import secrets
from collections import defaultdict, deque

from flask import Flask, request, jsonify, render_template_string

# ==========================================================
#  FLASK - ATX HOSTING
# ==========================================================
app = Flask('')

DASHBOARD_HTML = """
<!DOCTYPE html><html><head><title>ATX Hosting</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0a1a;color:#e0e0e0;padding:20px}
.container{max-width:1400px;margin:0 auto}
h1{color:#00d4ff;margin-bottom:5px;font-size:2em}
.subtitle{color:#666;margin-bottom:25px;font-size:0.9em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:30px}
.card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #2a2a4e;border-radius:12px;padding:20px}
.card h3{color:#00d4ff;margin-bottom:8px;font-size:0.75em;text-transform:uppercase}
.card .value{font-size:2em;font-weight:bold;color:#fff}
table{width:100%;border-collapse:collapse;background:#1a1a2e;border-radius:12px;overflow:hidden}
th,td{padding:12px;text-align:left;border-bottom:1px solid #2a2a4e;font-size:0.9em}
th{background:#252540;color:#00d4ff;text-transform:uppercase;font-size:0.75em}
tr:hover{background:#252540}
</style></head><body><div class="container">
<h1>ATX Hosting</h1>
<p class="subtitle">Live - {{ now }}</p>
<div class="grid">
<div class="card"><h3>Total Users</h3><div class="value">{{ stats.users }}</div></div>
<div class="card"><h3>Running Scripts</h3><div class="value">{{ stats.running }}</div></div>
<div class="card"><h3>Total Files</h3><div class="value">{{ stats.files }}</div></div>
<div class="card"><h3>Subscriptions</h3><div class="value">{{ stats.subs }}</div></div>
<div class="card"><h3>Revenue (Stars)</h3><div class="value">{{ stats.revenue }}</div></div>
<div class="card"><h3>Storage</h3><div class="value" style="font-size:1.1em">{{ stats.storage }}</div></div>
</div>
<h2 style="color:#00d4ff;margin:20px 0">Running Scripts</h2>
<table><thead><tr><th>Owner</th><th>File</th><th>Type</th><th>Uptime</th><th>CPU</th><th>RAM</th><th>Status</th></tr></thead><tbody>
{% for s in scripts %}<tr><td>{{ s.owner }}</td><td>{{ s.file }}</td><td>{{ s.type }}</td><td>{{ s.uptime }}</td><td>{{ s.cpu }}</td><td>{{ s.ram }}</td><td style="color:#00ff88">Running</td></tr>{% endfor %}
{% if not scripts %}<tr><td colspan="7" style="text-align:center;padding:40px;color:#666">No running scripts</td></tr>{% endif %}
</tbody></table>
<p style="margin-top:30px;color:#444;font-size:0.85em;text-align:center">ATX Hosting</p>
</div></body></html>
"""

# ==========================================================
#  CONFIG
# ==========================================================
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
ADMIN_ID = int(os.environ.get('ADMIN_ID', OWNER_ID))
YOUR_USERNAME = os.environ.get('YOUR_USERNAME', '@AntraxdevZ')
UPDATE_CHANNEL = os.environ.get('UPDATE_CHANNEL', 'https://t.me/atxxxchannel')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
REST_API_KEY = os.environ.get('REST_API_KEY', '')
DOCKER_ENABLED = os.environ.get('DOCKER_ENABLED', 'false').lower() == 'true'
PAYMENT_ENABLED = os.environ.get('PAYMENT_ENABLED', 'true').lower() == 'true'
SANDBOX_MODE = os.environ.get('SANDBOX_MODE', 'false').lower() == 'true'
CLUSTER_MODE = os.environ.get('CLUSTER_MODE', 'false').lower() == 'true'
CLUSTER_SECRET = os.environ.get('CLUSTER_SECRET', '')
CLUSTER_WORKERS = os.environ.get('CLUSTER_WORKERS', '').split(',') if os.environ.get('CLUSTER_WORKERS') else []
K8S_ENABLED = os.environ.get('K8S_ENABLED', 'false').lower() == 'true'
IP_WHITELIST = os.environ.get('IP_WHITELIST', '').split(',') if os.environ.get('IP_WHITELIST') else []

PUBLIC_URL = "https://hostatx-production.up.railway.app"

if not TOKEN:
    raise ValueError("BOT_TOKEN required!")
if not OWNER_ID:
    raise ValueError("OWNER_ID required!")

RAILWAY_VOLUME_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '')
BASE_DIR = None
for p in [RAILWAY_VOLUME_PATH, '/data', os.environ.get('RAILWAY_VOLUME_PATH', '')]:
    if p and os.path.isdir(p) and os.access(p, os.W_OK):
        BASE_DIR = p
        print(f"Volume: {BASE_DIR}")
        break
if not BASE_DIR:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    print(f"Ephemeral: {BASE_DIR}")

UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf')
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')
ENV_DIR = os.path.join(BASE_DIR, 'env_vars')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
GITHUB_REPOS_DIR = os.path.join(BASE_DIR, 'github_repos')
MARKETPLACE_DIR = os.path.join(BASE_DIR, 'marketplace')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')
VERSIONS_DIR = os.path.join(BASE_DIR, 'versions')
CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
SANDBOX_DIR = os.path.join(BASE_DIR, 'sandbox')

for d in [UPLOAD_BOTS_DIR, IROTECH_DIR, ENV_DIR, TEMPLATES_DIR, GITHUB_REPOS_DIR,
          MARKETPLACE_DIR, BACKUPS_DIR, VERSIONS_DIR, CHARTS_DIR, SANDBOX_DIR]:
    os.makedirs(d, exist_ok=True)

# ==========================================================
#  TIERS
# ==========================================================
TIERS = {
    'free': {'name': 'Free', 'scripts': 10, 'file_mb': 20, 'ram_mb': 256,
             'cpu_percent': 10, 'api_rate': 10, 'ai_requests_day': 5,
             'price_stars': 0, 'price_usd': 0, 'backups': 1, 'concurrent': 1},
    'basic': {'name': 'Basic', 'scripts': 25, 'file_mb': 50, 'ram_mb': 512,
              'cpu_percent': 25, 'api_rate': 30, 'ai_requests_day': 50,
              'price_stars': 50, 'price_usd': 1, 'backups': 3, 'concurrent': 3},
    'pro': {'name': 'Pro', 'scripts': 50, 'file_mb': 100, 'ram_mb': 1024,
            'cpu_percent': 50, 'api_rate': 100, 'ai_requests_day': 200,
            'price_stars': 100, 'price_usd': 2, 'backups': 5, 'concurrent': 5},
    'business': {'name': 'Business', 'scripts': 100, 'file_mb': 200, 'ram_mb': 2048,
                 'cpu_percent': 75, 'api_rate': 300, 'ai_requests_day': 1000,
                 'price_stars': 200, 'price_usd': 3, 'backups': 10, 'concurrent': 10},
    'enterprise': {'name': 'Enterprise', 'scripts': 9999, 'file_mb': 500, 'ram_mb': 8192,
                   'cpu_percent': 100, 'api_rate': 9999, 'ai_requests_day': 9999,
                   'price_stars': 300, 'price_usd': 5, 'backups': 50, 'concurrent': 999},
}

bot = telebot.TeleBot(TOKEN)

# ==========================================================
#  STATE
# ==========================================================
bot_scripts = {}
user_subscriptions = {}
user_files = {}
user_tags = defaultdict(list)
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
moderator_ids = set()
bot_locked = False
emergency_killed = False

auto_restart_config = {}
script_restart_count = {}
script_crash_count = {}
script_total_runtime = {}
user_ai_model = {}
user_referrals = {}
user_daily_bonus = {}
user_webhooks = {}
user_collab = {}
user_health_urls = {}
user_api_keys = {}
user_tiers = {}
user_usage = defaultdict(lambda: {'cpu_minutes': 0, 'ai_requests_today': 0,
                                   'ai_reset_date': None, 'api_calls_today': 0,
                                   'api_reset_date': None})
user_batch_selection = {}
user_bot_tokens = {}

rate_limits = defaultdict(lambda: deque(maxlen=100))
api_rate_limits = defaultdict(lambda: deque(maxlen=500))
cpu_graphs = defaultdict(lambda: deque(maxlen=60))
ram_graphs = defaultdict(lambda: deque(maxlen=60))
command_history = defaultdict(lambda: deque(maxlen=50))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================================
#  DETECT VIRTUALENV
# ==========================================================
def is_in_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None)


def get_pip_install_cmd(packages):
    base_cmd = [sys.executable, '-m', 'pip', 'install']
    if not is_in_venv():
        base_cmd.append('--user')
    if isinstance(packages, str):
        base_cmd.append(packages)
    else:
        base_cmd.extend(packages)
    return base_cmd

# ==========================================================
#  AI SEEK
# ==========================================================
AI_SEEK_URL = "https://ai-seek.thebetter.ai/v4/chat/send"
AI_SEEK_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJBUy1YNkNZUiIsImF1ZCI6ImFpLXNlZWsiLCJwcm92aWRlciI6InV1aWQiLCJpc3MiOiJhaS1zZWVrIiwiZXhwIjoyMDkzMTk5ODY1LCJpYXQiOjE3Nzc4Mzk4NjV9.w2wlNLg2S-om4xqWmakO2tEUjiPjxtGwFozmoI217VUu7KGC1O3qaL7KdyEIBYrGxIZV3lMWospZPPgVOYJjOeDgKBFnhg1_7NRKfmCEum_0moUEqH6dGFtQUQixDi63k63wv6GhOs1Sorj6hLzdBxX6NHU6otOo6brls5UNYbc"
AI_SEEK_HEADERS = {
    'User-Agent': "okhttp/4.12.0",
    'Accept': "text/event-stream",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/json",
    'x-app-id': "ai-seek",
    'x-device-info': "appIdentifier=ai.chatbot.ask.chat.deep.seek.assistant.search.free;appVersion=2.7.1-26042486;deviceType=android;deviceCountry=EG;appCountry=eg;local=ar_EG;language=ar;timezone=Asia/Baghdad;brand=POCO;model=2311DRK48G;androidId=6a33f4473da78ff9",
    'x-guru-internal-send-timeout-ms': "60000",
    'x-guru-internal-connect-timeout-ms': "60000",
    'x-guru-internal-receive-timeout-ms': "120000",
    'x-access-token': AI_SEEK_TOKEN
}
AI_SEEK_MODELS = [
    "qwen/qwen-coder-32b", "openai/gpt-5-mini", "deepseek/deepseek-chat",
    "grok/grok-4-fast", "qwen/qwen3-32b", "google/gemini-2.5-flash-lite",
    "meta-llama/llama-4-scout", "microsoft/phi-4-mini"
]
AI_SEEK_MODEL_LABELS = {
    "qwen/qwen-coder-32b": "Qwen Coder 32B",
    "openai/gpt-5-mini": "GPT-5 Mini",
    "deepseek/deepseek-chat": "DeepSeek Chat",
    "grok/grok-4-fast": "Grok 4 Fast",
    "qwen/qwen3-32b": "Qwen 3 32B",
    "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite",
    "meta-llama/llama-4-scout": "Llama 4 Scout",
    "microsoft/phi-4-mini": "Phi-4 Mini"
}

# ==========================================================
#  LANGUAGES
# ==========================================================
LANG_CONFIG = {
    '.py': {'runner': 'python', 'cmd': [sys.executable], 'type': 'py'},
    '.js': {'runner': 'node', 'cmd': ['node'], 'type': 'js'},
    '.ts': {'runner': 'ts-node', 'cmd': ['npx', 'ts-node'], 'type': 'ts'},
    '.rb': {'runner': 'ruby', 'cmd': ['ruby'], 'type': 'rb'},
    '.go': {'runner': 'go', 'cmd': ['go', 'run'], 'type': 'go'},
    '.php': {'runner': 'php', 'cmd': ['php'], 'type': 'php'},
    '.sh': {'runner': 'bash', 'cmd': ['bash'], 'type': 'sh'},
    '.bash': {'runner': 'bash', 'cmd': ['bash'], 'type': 'sh'},
}

# ==========================================================
#  TEMPLATES
# ==========================================================
SCRIPT_TEMPLATES = {
    'inline_bot': {
        'name': 'InlineKeyboard Bot',
        'lang': 'py',
        'code': '''# InlineKeyboard Telegram Bot - ATX Hosting
import os
import sys
import time
import traceback
from datetime import datetime
import telebot
from telebot import types

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN env var missing!")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


def main_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("Status", callback_data='menu_status'),
        types.InlineKeyboardButton("Time", callback_data='menu_time')
    )
    mk.row(
        types.InlineKeyboardButton("About", callback_data='menu_about'),
        types.InlineKeyboardButton("Ping", callback_data='menu_ping')
    )
    mk.row(types.InlineKeyboardButton("Close", callback_data='menu_close'))
    return mk


@bot.message_handler(commands=['start', 'help'])
def cmd_start(m):
    text = (
        f"Welcome, {m.from_user.first_name}!\\n\\n"
        f"Commands:\\n/start - Main menu\\n/menu - Show menu\\n"
        f"/ping - Check latency\\n/time - Show time\\n"
    )
    bot.reply_to(m, text, reply_markup=main_menu())


@bot.message_handler(commands=['menu'])
def cmd_menu(m):
    bot.reply_to(m, "Main Menu:", reply_markup=main_menu())


@bot.message_handler(commands=['ping'])
def cmd_ping(m):
    t0 = time.time()
    msg = bot.reply_to(m, "Pong!")
    latency = round((time.time() - t0) * 1000, 2)
    bot.edit_message_text(f"Pong! {latency} ms", m.chat.id, msg.message_id)


@bot.message_handler(commands=['time'])
def cmd_time(m):
    bot.reply_to(m, f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}")


@bot.callback_query_handler(func=lambda c: True)
def on_callback(c):
    try:
        if c.data == 'menu_status':
            bot.answer_callback_query(c.id, "OK")
            bot.send_message(c.message.chat.id, "Bot: Online\\nStatus: OK")
        elif c.data == 'menu_time':
            bot.answer_callback_query(c.id, "Time")
            bot.send_message(c.message.chat.id, f"{datetime.now():%Y-%m-%d %H:%M:%S}")
        elif c.data == 'menu_about':
            bot.answer_callback_query(c.id, "About")
            bot.send_message(c.message.chat.id, "InlineKeyboard bot template by ATX Hosting")
        elif c.data == 'menu_ping':
            bot.answer_callback_query(c.id, "Pong!")
            bot.send_message(c.message.chat.id, "Pong!")
        elif c.data == 'menu_close':
            bot.answer_callback_query(c.id, "Closed")
            bot.edit_message_text("Menu closed.", c.message.chat.id, c.message.message_id)
    except Exception as e:
        print(f"Callback error: {e}")


@bot.message_handler(func=lambda m: True)
def echo(m):
    bot.reply_to(m, f"You said: {m.text}", reply_markup=main_menu())


if __name__ == "__main__":
    print("Bot starting...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}")
            traceback.print_exc()
            time.sleep(5)
'''
    },
    'echo_bot': {
        'name': 'Echo Bot',
        'lang': 'py',
        'code': '''# Echo Bot - ATX Hosting
import os
import telebot

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_TOKEN_HERE')
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def s(m):
    bot.reply_to(m, f"Hello {m.from_user.first_name}!")


@bot.message_handler(func=lambda m: True)
def e(m):
    bot.reply_to(m, f"You said: {m.text}")


if __name__ == "__main__":
    print("Echo bot running...")
    bot.infinity_polling()
'''
    },
    'web_scraper': {
        'name': 'Web Scraper',
        'lang': 'py',
        'code': '''# Web Scraper - ATX Hosting
import requests
import time
from datetime import datetime

URL = "https://example.com"
INTERVAL = 60

while True:
    try:
        r = requests.get(URL, timeout=10)
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Status: {r.status_code}, Size: {len(r.text)} bytes")
    except Exception as e:
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Error: {e}")
    time.sleep(INTERVAL)
'''
    },
    'data_logger': {
        'name': 'Data Logger',
        'lang': 'py',
        'code': '''# Data Logger - ATX Hosting
import time
import json
import random
from datetime import datetime

while True:
    entry = {
        "ts": datetime.now().isoformat(),
        "value": random.randint(1, 100),
        "sensor": "temp"
    }
    with open("data_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\\n")
    print(f"Logged: {entry}")
    time.sleep(30)
'''
    },
    'cron_worker': {
        'name': 'Cron Worker',
        'lang': 'py',
        'code': '''# Cron Worker - ATX Hosting
import time
from datetime import datetime

while True:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Working...")
    time.sleep(3600)
'''
    },
}

# ==========================================================
#  DB INIT
# ==========================================================
def init_db():
    logger.info(f"DB: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, expiry TEXT, tier TEXT DEFAULT "free")')
    c.execute('CREATE TABLE IF NOT EXISTS user_files (user_id INTEGER, file_name TEXT, file_type TEXT, PRIMARY KEY (user_id, file_name))')
    c.execute('CREATE TABLE IF NOT EXISTS active_users (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS moderators (user_id INTEGER PRIMARY KEY)')
    c.execute('CREATE TABLE IF NOT EXISTS env_vars (user_id INTEGER, script_name TEXT, key TEXT, value TEXT, PRIMARY KEY (user_id, script_name, key))')
    c.execute('CREATE TABLE IF NOT EXISTS analytics (user_id INTEGER, script_name TEXT, crashes INTEGER DEFAULT 0, restarts INTEGER DEFAULT 0, total_runtime REAL DEFAULT 0, PRIMARY KEY (user_id, script_name))')
    c.execute('CREATE TABLE IF NOT EXISTS schedules (user_id INTEGER, script_name TEXT, cron_expr TEXT, next_run TEXT, PRIMARY KEY (user_id, script_name))')
    c.execute('CREATE TABLE IF NOT EXISTS referrals (user_id INTEGER PRIMARY KEY, referred_by INTEGER, count INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS daily_bonus (user_id INTEGER PRIMARY KEY, last_claim TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS webhooks (user_id INTEGER, script_name TEXT, url TEXT, PRIMARY KEY (user_id, script_name))')
    c.execute('CREATE TABLE IF NOT EXISTS collaboration (owner_id INTEGER, script_name TEXT, collab_id INTEGER, role TEXT, PRIMARY KEY (owner_id, script_name, collab_id))')
    c.execute('CREATE TABLE IF NOT EXISTS marketplace (id INTEGER PRIMARY KEY AUTOINCREMENT, uploader_id INTEGER, name TEXT, description TEXT, language TEXT, file_path TEXT, downloads INTEGER DEFAULT 0, rating REAL DEFAULT 0, rating_count INTEGER DEFAULT 0, verified INTEGER DEFAULT 0, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS marketplace_reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, script_id INTEGER, reviewer_id INTEGER, rating INTEGER, comment TEXT, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_urls (user_id INTEGER, script_name TEXT, url TEXT, PRIMARY KEY (user_id, script_name))')
    c.execute('CREATE TABLE IF NOT EXISTS versions (user_id INTEGER, script_name TEXT, version INTEGER, file_path TEXT, created TEXT, PRIMARY KEY (user_id, script_name, version))')
    c.execute('CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, details TEXT, timestamp TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, days INTEGER, method TEXT, status TEXT, tier TEXT, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tags (user_id INTEGER, script_name TEXT, tag TEXT, PRIMARY KEY (user_id, script_name, tag))')
    c.execute('CREATE TABLE IF NOT EXISTS api_keys (user_id INTEGER, key TEXT PRIMARY KEY, created TEXT, last_used TEXT, active INTEGER DEFAULT 1)')
    c.execute('CREATE TABLE IF NOT EXISTS usage (user_id INTEGER, date TEXT, cpu_minutes REAL DEFAULT 0, api_calls INTEGER DEFAULT 0, ai_requests INTEGER DEFAULT 0, PRIMARY KEY (user_id, date))')
    c.execute('CREATE TABLE IF NOT EXISTS ci_cd (user_id INTEGER, script_name TEXT, repo_url TEXT, branch TEXT, auto_deploy INTEGER DEFAULT 0, last_commit TEXT, PRIMARY KEY (user_id, script_name))')
    c.execute('CREATE TABLE IF NOT EXISTS sponsored (script_id INTEGER PRIMARY KEY, until TEXT, amount INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS scheduled_broadcasts (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, schedule_cron TEXT, next_run TEXT, created_by INTEGER, created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_tiers (user_id INTEGER PRIMARY KEY, tier TEXT DEFAULT "free")')
    c.execute('CREATE TABLE IF NOT EXISTS user_bot_tokens (user_id INTEGER PRIMARY KEY, bot_token TEXT, admin_id INTEGER, created TEXT)')
    c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
    if ADMIN_ID != OWNER_ID:
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
    conn.commit()
    conn.close()
    logger.info("DB ready")


def load_data():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT user_id, expiry, tier FROM subscriptions')
    for uid, ex, tier in c.fetchall():
        try: user_subscriptions[uid] = {'expiry': datetime.fromisoformat(ex), 'tier': tier or 'free'}
        except: pass
    c.execute('SELECT user_id, file_name, file_type FROM user_files')
    for uid, fn, ft in c.fetchall():
        user_files.setdefault(uid, []).append((fn, ft))
    c.execute('SELECT user_id FROM active_users')
    active_users.update(r[0] for r in c.fetchall())
    c.execute('SELECT user_id FROM admins')
    admin_ids.update(r[0] for r in c.fetchall())
    c.execute('SELECT user_id FROM moderators')
    moderator_ids.update(r[0] for r in c.fetchall())
    c.execute('SELECT user_id, script_name, crashes, restarts, total_runtime FROM analytics')
    for uid, sn, cr, rs, rt in c.fetchall():
        key = f"{uid}_{sn}"
        script_crash_count[key] = cr or 0
        script_total_runtime[key] = rt or 0
    c.execute('SELECT user_id, referred_by, count FROM referrals')
    for uid, rb, cnt in c.fetchall():
        user_referrals[uid] = {'referred_by': rb, 'count': cnt or 0}
    c.execute('SELECT user_id, last_claim FROM daily_bonus')
    for uid, lc in c.fetchall():
        try: user_daily_bonus[uid] = datetime.fromisoformat(lc)
        except: pass
    c.execute('SELECT user_id, script_name, url FROM webhooks')
    for uid, sn, url in c.fetchall():
        user_webhooks[f"{uid}_{sn}"] = url
    c.execute('SELECT user_id, script_name, url FROM health_urls')
    for uid, sn, url in c.fetchall():
        user_health_urls[f"{uid}_{sn}"] = url
    c.execute('SELECT user_id, script_name, tag FROM tags')
    for uid, sn, tag in c.fetchall():
        user_tags[f"{uid}_{sn}"].append(tag)
    c.execute('SELECT user_id, key FROM api_keys WHERE active=1')
    for uid, key in c.fetchall():
        user_api_keys[key] = uid
    c.execute('SELECT user_id, tier FROM user_tiers')
    for uid, tier in c.fetchall():
        user_tiers[uid] = tier
    try:
        c.execute('SELECT user_id, bot_token, admin_id FROM user_bot_tokens')
        for uid, bt, aid in c.fetchall():
            user_bot_tokens[uid] = {'bot_token': bt, 'admin_id': aid}
    except: pass
    conn.close()
    logger.info(f"Loaded: {len(active_users)} users")


init_db()
load_data()

# ==========================================================
#  TIER HELPERS
# ==========================================================
def get_user_tier(uid):
    if uid == OWNER_ID: return 'enterprise'
    if uid in admin_ids: return 'business'
    if uid in moderator_ids: return 'pro'
    if uid in user_tiers:
        return user_tiers[uid]
    if uid in user_subscriptions:
        sub = user_subscriptions[uid]
        if sub.get('expiry') and sub['expiry'] > datetime.now():
            return sub.get('tier', 'basic')
    return 'free'


def get_tier_limits(uid):
    return TIERS.get(get_user_tier(uid), TIERS['free'])


def is_premium(uid):
    return get_user_tier(uid) != 'free'


def get_user_file_limit(uid):
    return get_tier_limits(uid)['scripts']


def get_max_file_mb(uid):
    return get_tier_limits(uid)['file_mb']


def get_user_file_count(uid):
    return len(user_files.get(uid, []))

# ==========================================================
#  ACTIVITY LOG
# ==========================================================
def log_activity(uid, action, details=""):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT INTO activity_log (user_id, action, details, timestamp) VALUES (?,?,?,?)',
                  (uid, action, details[:500], datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"log_activity: {e}")

# ==========================================================
#  RATE LIMITERS
# ==========================================================
def check_rate_limit(uid, limit=10, window=60):
    now = time.time()
    q = rate_limits[uid]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


def check_api_rate(uid):
    limits = get_tier_limits(uid)
    limit = limits['api_rate']
    now = time.time()
    q = api_rate_limits[uid]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        return False
    q.append(now)
    return True


def check_ai_quota(uid):
    limits = get_tier_limits(uid)
    today = datetime.now().date().isoformat()
    u = user_usage[uid]
    if u['ai_reset_date'] != today:
        u['ai_requests_today'] = 0
        u['ai_reset_date'] = today
    if u['ai_requests_today'] >= limits['ai_requests_day']:
        return False
    u['ai_requests_today'] += 1
    return True

# ==========================================================
#  AI SEEK FUNCTIONS
# ==========================================================
def ai_seek_query(model, question, timeout=90):
    result = {"model": model, "answer": None, "error": None}
    ms = int(time.time() * 1000)
    rand = random.getrandbits(80)
    uuid_int = (ms << 80) | (0x7 << 76) | (rand & 0x0FFFFFFFFFFFFFFFFFFFFFFF)
    h = f'{uuid_int:032x}'
    ai_message_id = f'{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}'
    payload = {
        "sessionId": "019def83-b582-7410-95dd-b747cc648582",
        "userMessageId": "019def8d-103e-78ba-9329-c9b714b900d0",
        "aiMessageId": ai_message_id,
        "model": model, "text": question,
        "restrictedType": "FREE_USER", "sessionType": "NORMAL"
    }
    try:
        r = requests.post(AI_SEEK_URL, json=payload, headers=AI_SEEK_HEADERS, stream=True, timeout=timeout)
        parts = []
        for line in r.iter_lines():
            if line:
                line = line.decode('utf-8', errors='ignore')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'content' in data and data['content']:
                            parts.append(data['content'])
                    except: pass
        if parts:
            result["answer"] = ''.join(parts).strip()
        else:
            result["error"] = "No response."
    except requests.exceptions.Timeout:
        result["error"] = "Timeout."
    except Exception as e:
        result["error"] = str(e)
    return result


def clean_ai_code(raw):
    """Remove think tags, markdown fences, and common AI artifacts."""
    if not raw:
        return ""
    code = raw.strip()
    code = re.sub(r'<think\b[^>]*>.*?</think\s*>', '', code, flags=re.DOTALL | re.IGNORECASE)
    code = re.sub(r'</?think\b[^>]*>', '', code, flags=re.IGNORECASE)
    code = re.sub(r'<reasoning\b[^>]*>.*?</reasoning\s*>', '', code, flags=re.DOTALL | re.IGNORECASE)
    code = re.sub(r'</?reasoning\b[^>]*>', '', code, flags=re.IGNORECASE)
    for tag in ['analysis', 'reflection', 'inner_monologue', 'scratchpad', 'chain_of_thought']:
        code = re.sub(rf'<{tag}\b[^>]*>.*?</{tag}\s*>', '', code, flags=re.DOTALL | re.IGNORECASE)
        code = re.sub(rf'</?{tag}\b[^>]*>', '', code, flags=re.IGNORECASE)
    code = re.sub(r'^\s*```[a-zA-Z0-9_+-]*\s*\n', '', code)
    code = re.sub(r'\n\s*```\s*$', '', code)
    code = re.sub(r'^\s*```\s*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'^(?:here\s+is|here\'s)\s+(?:the\s+)?(?:code|script|python\s+code)[:\s]*\n+',
                  '', code, flags=re.IGNORECASE)
    return code.strip()


def ai_seek_send_long(chat_id, model, question, reply_to_msg_id=None):
    label = AI_SEEK_MODEL_LABELS.get(model, model)
    wait_msg = None
    try:
        wait_msg = bot.send_message(chat_id, f"{label} is thinking... (up to 90s)",
                                     reply_to_message_id=reply_to_msg_id)
    except: pass
    res = ai_seek_query(model, question)
    if wait_msg:
        try: bot.delete_message(chat_id, wait_msg.message_id)
        except: pass
    if res.get("error"):
        try:
            bot.send_message(chat_id, f"{label} error: {res['error']}",
                             reply_to_message_id=reply_to_msg_id)
        except: pass
        return
    answer = res.get("answer", "").strip()
    if not answer:
        try:
            bot.send_message(chat_id, f"{label}: empty response.",
                             reply_to_message_id=reply_to_msg_id)
        except: pass
        return
    chunks = []
    rem = answer
    while rem:
        if len(rem) <= 4000:
            chunks.append(rem)
            break
        sp = rem.rfind('\n', 0, 4000)
        if sp == -1: sp = 4000
        chunks.append(rem[:sp])
        rem = rem[sp:].lstrip('\n')
    for i, ch in enumerate(chunks):
        pre = f"[{label}]\n\n" if i == 0 else f"[{label} cont.]\n\n"
        try:
            bot.send_message(chat_id, pre + ch, reply_to_message_id=reply_to_msg_id)
        except:
            try: bot.send_message(chat_id, pre + ch, reply_to_message_id=reply_to_msg_id)
            except: pass
        time.sleep(0.5)


def get_user_ai_model(uid):
    return user_ai_model.get(uid, "deepseek/deepseek-chat")

# ==========================================================
#  HELPERS
# ==========================================================
def get_user_folder(uid):
    p = os.path.join(UPLOAD_BOTS_DIR, str(uid))
    os.makedirs(p, exist_ok=True)
    return p


def is_bot_running(owner, fname):
    key = f"{owner}_{fname}"
    info = bot_scripts.get(key)
    if info and info.get('process'):
        try:
            p = psutil.Process(info['process'].pid)
            run = p.is_running() and p.status() != psutil.STATUS_ZOMBIE
            if not run:
                if 'log_file' in info and hasattr(info['log_file'], 'close') and not info['log_file'].closed:
                    try: info['log_file'].close()
                    except: pass
                if key in bot_scripts: del bot_scripts[key]
            return run
        except psutil.NoSuchProcess:
            if 'log_file' in info and hasattr(info['log_file'], 'close') and not info['log_file'].closed:
                try: info['log_file'].close()
                except: pass
            if key in bot_scripts: del bot_scripts[key]
            return False
        except: return False
    return False


def kill_process_tree(pi):
    key = pi.get('script_key', 'N/A')
    try:
        if 'log_file' in pi and hasattr(pi['log_file'], 'close') and not pi['log_file'].closed:
            try: pi['log_file'].close()
            except: pass
        proc = pi.get('process')
        if proc and hasattr(proc, 'pid') and proc.pid:
            try:
                parent = psutil.Process(proc.pid)
                children = parent.children(recursive=True)
                for ch in children:
                    try: ch.terminate()
                    except:
                        try: ch.kill()
                        except: pass
                gone, alive = psutil.wait_procs(children, timeout=1)
                for p in alive:
                    try: p.kill()
                    except: pass
                try:
                    parent.terminate()
                    try: parent.wait(timeout=1)
                    except psutil.TimeoutExpired: parent.kill()
                except psutil.NoSuchProcess: pass
                except:
                    try: parent.kill()
                    except: pass
            except psutil.NoSuchProcess: pass
    except Exception as e:
        logger.error(f"kill {key}: {e}")


def format_uptime(sec):
    sec = int(sec)
    d, h = sec // 86400, (sec % 86400) // 3600
    m, s = (sec % 3600) // 60, sec % 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def get_script_uptime(key):
    info = bot_scripts.get(key)
    if not info: return None
    st = info.get('start_time')
    if not st: return None
    return (datetime.now() - st).total_seconds()


def get_script_resources(key):
    info = bot_scripts.get(key)
    if not info: return None
    try:
        p = psutil.Process(info['process'].pid)
        with p.oneshot():
            return {"cpu": p.cpu_percent(interval=0.1),
                    "mem_mb": p.memory_info().rss / (1024 * 1024),
                    "threads": p.num_threads()}
    except: return None


def notify_webhook(key, event, message):
    url = user_webhooks.get(key) or WEBHOOK_URL
    if not url: return
    try:
        requests.post(url, json={"content": f"[{event}] {message}"}, timeout=5)
    except Exception as e:
        logger.error(f"webhook: {e}")

# ==========================================================
#  SUB EXPIRY CHECKER
# ==========================================================
def check_expired_subs():
    while True:
        try:
            time.sleep(3600)
            now = datetime.now()
            expired = []
            for uid, sub in list(user_subscriptions.items()):
                if sub.get('expiry') and sub['expiry'] < now:
                    expired.append(uid)
            for uid in expired:
                try:
                    remove_subscription_db(uid)
                    bot.send_message(uid, "Your subscription has expired. You are now on Free tier.")
                except: pass
        except Exception as e:
            logger.error(f"check_expired: {e}")

threading.Thread(target=check_expired_subs, daemon=True).start()

# ==========================================================
#  AUTO-RESTART MONITOR
# ==========================================================
def auto_restart_monitor():
    while True:
        try:
            time.sleep(15)
            for key in list(bot_scripts.keys()):
                info = bot_scripts.get(key)
                if not info: continue
                proc = info.get('process')
                if not proc: continue
                rc = proc.poll()
                if rc is None: continue
                owner = info.get('script_owner_id')
                fname = info.get('file_name')
                chat_id = info.get('chat_id')
                folder = info.get('user_folder')
                ftype = info.get('type', 'py')
                up = get_script_uptime(key) or 0
                script_total_runtime[key] = script_total_runtime.get(key, 0) + up
                script_crash_count[key] = script_crash_count.get(key, 0) + 1
                if 'log_file' in info and hasattr(info['log_file'], 'close') and not info['log_file'].closed:
                    try: info['log_file'].close()
                    except: pass
                del bot_scripts[key]
                log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
                log_tail = ""
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            log_tail = "\n".join(f.read().splitlines()[-50:])
                    except: pass
                try: bot.send_message(chat_id, f"{fname} crashed (exit {rc}).")
                except: pass
                notify_webhook(key, "CRASH", f"{fname} crashed")
                if log_tail and get_user_tier(owner) in ['pro', 'business', 'enterprise']:
                    threading.Thread(target=ai_autofix_suggest,
                                     args=(chat_id, owner, fname, log_tail), daemon=True).start()
                maxa = auto_restart_config.get(f"{owner}_{fname}", 0)
                cur = script_restart_count.get(key, 0)
                if maxa > 0 and cur < maxa:
                    script_restart_count[key] = cur + 1
                    fp = os.path.join(folder, fname)
                    if os.path.exists(fp):
                        time.sleep(3)
                        dummy = type('Msg', (), {
                            'chat': type('C', (), {'id': chat_id})(),
                            'message_id': None,
                            'from_user': type('U', (), {'id': owner})()
                        })()
                        if ftype == 'py':
                            threading.Thread(target=run_script, args=(fp, owner, folder, fname, dummy), daemon=True).start()
                        elif ftype == 'js':
                            threading.Thread(target=run_js_script, args=(fp, owner, folder, fname, dummy), daemon=True).start()
                        else:
                            threading.Thread(target=run_generic_script, args=(fp, owner, folder, fname, ftype, dummy), daemon=True).start()
                        try: bot.send_message(chat_id, f"{fname} restarted ({cur+1}/{maxa}).")
                        except: pass
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('INSERT OR REPLACE INTO analytics VALUES (?,?,?,?,?)',
                              (owner, fname, script_crash_count.get(key, 0),
                               script_restart_count.get(key, 0), script_total_runtime.get(key, 0)))
                    conn.commit()
                    conn.close()
                except: pass
        except Exception as e:
            logger.error(f"monitor: {e}", exc_info=True)

threading.Thread(target=auto_restart_monitor, daemon=True).start()


def ai_autofix_suggest(chat_id, owner, fname, log_tail):
    try:
        prompt = f"""Script "{fname}" crashed. Analyze the log and give a SHORT fix suggestion.

Log:
{log_tail[:2000]}

Reply with:
1. What went wrong (1-2 lines)
2. How to fix (1-3 lines, with code if needed)

Do NOT use <think> tags. Straight answer only."""
        model = get_user_ai_model(owner)
        res = ai_seek_query(model, prompt, timeout=60)
        if res.get('answer'):
            try: bot.send_message(chat_id, f"AI Auto-Fix for {fname}:\n\n{res['answer'][:3500]}")
            except: pass
    except Exception as e:
        logger.error(f"ai_autofix: {e}")

# ==========================================================
#  SCHEDULER
# ==========================================================
def parse_cron(expr):
    m = re.match(r'^(\d+)\s*([smhd])$', expr.strip().lower())
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        return n * {'s':1,'m':60,'h':3600,'d':86400}[unit]
    if expr.strip() == '* * * * *': return 60
    if expr.strip() == '0 * * * *': return 3600
    if expr.strip() == '0 0 * * *': return 86400
    return None


def run_scheduler():
    while True:
        try:
            time.sleep(30)
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT user_id, script_name, cron_expr, next_run FROM schedules')
            rows = c.fetchall()
            now = datetime.now()
            for uid, sn, cron, nxt in rows:
                try: next_dt = datetime.fromisoformat(nxt) if nxt else now
                except: next_dt = now
                if now >= next_dt:
                    interval_sec = parse_cron(cron)
                    if interval_sec:
                        folder = get_user_folder(uid)
                        fp = os.path.join(folder, sn)
                        if os.path.exists(fp) and not is_bot_running(uid, sn):
                            ftype = next((f[1] for f in user_files.get(uid, []) if f[0] == sn), 'py')
                            dummy = type('Msg', (), {
                                'chat': type('C', (), {'id': uid})(),
                                'message_id': None,
                                'from_user': type('U', (), {'id': uid})()
                            })()
                            if ftype == 'py':
                                threading.Thread(target=run_script, args=(fp, uid, folder, sn, dummy), daemon=True).start()
                            elif ftype == 'js':
                                threading.Thread(target=run_js_script, args=(fp, uid, folder, sn, dummy), daemon=True).start()
                            else:
                                threading.Thread(target=run_generic_script, args=(fp, uid, folder, sn, ftype, dummy), daemon=True).start()
                        nxt_dt = now + timedelta(seconds=interval_sec)
                        c.execute('UPDATE schedules SET next_run=? WHERE user_id=? AND script_name=?',
                                  (nxt_dt.isoformat(), uid, sn))
                        conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"scheduler: {e}", exc_info=True)

threading.Thread(target=run_scheduler, daemon=True).start()

# ==========================================================
#  AUTO BACKUP
# ==========================================================
def auto_backup_monitor():
    while True:
        try:
            time.sleep(6 * 3600)
            logger.info("Auto-backup running...")
            for uid in list(user_files.keys()):
                folder = get_user_folder(uid)
                bdir = os.path.join(BACKUPS_DIR, str(uid))
                os.makedirs(bdir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                for fn, ft in user_files[uid]:
                    src = os.path.join(folder, fn)
                    if os.path.exists(src):
                        try: shutil.copy2(src, os.path.join(bdir, f"{ts}_{fn}"))
                        except: pass
                limits = get_tier_limits(uid)
                files = sorted(os.listdir(bdir))
                if len(files) > limits['backups'] * max(len(user_files[uid]), 1):
                    for old in files[:len(files) - limits['backups'] * max(len(user_files[uid]), 1)]:
                        try: os.remove(os.path.join(bdir, old))
                        except: pass
            cutoff = time.time() - 7 * 86400
            for uid_folder in os.listdir(UPLOAD_BOTS_DIR):
                fpath = os.path.join(UPLOAD_BOTS_DIR, uid_folder)
                if not os.path.isdir(fpath): continue
                for f in os.listdir(fpath):
                    if f.endswith('.log'):
                        fp = os.path.join(fpath, f)
                        try:
                            if os.path.getmtime(fp) < cutoff:
                                os.remove(fp)
                        except: pass
        except Exception as e:
            logger.error(f"backup monitor: {e}")

threading.Thread(target=auto_backup_monitor, daemon=True).start()

# ==========================================================
#  RESOURCE MONITOR
# ==========================================================
def resource_monitor():
    while True:
        try:
            time.sleep(60)
            now = datetime.now()
            for key in list(bot_scripts.keys()):
                res = get_script_resources(key)
                if res:
                    cpu_graphs[key].append((now, res['cpu']))
                    ram_graphs[key].append((now, res['mem_mb']))
        except Exception as e:
            logger.error(f"resource_monitor: {e}")

threading.Thread(target=resource_monitor, daemon=True).start()

# ==========================================================
#  USAGE TRACKER
# ==========================================================
def usage_tracker():
    while True:
        try:
            time.sleep(300)
            today = datetime.now().date().isoformat()
            for key in list(bot_scripts.keys()):
                uid = bot_scripts[key]['script_owner_id']
                user_usage[uid]['cpu_minutes'] = user_usage[uid].get('cpu_minutes', 0) + 5
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('INSERT OR IGNORE INTO usage (user_id, date) VALUES (?,?)', (uid, today))
                    c.execute('UPDATE usage SET cpu_minutes = cpu_minutes + 5 WHERE user_id=? AND date=?', (uid, today))
                    conn.commit()
                    conn.close()
                except: pass
            for key in list(bot_scripts.keys()):
                uid = bot_scripts[key]['script_owner_id']
                limits = get_tier_limits(uid)
                res = get_script_resources(key)
                if res and res['mem_mb'] > limits['ram_mb']:
                    logger.warning(f"Script {key} over RAM limit")
                    info = bot_scripts.get(key)
                    if info:
                        kill_process_tree(info)
                        bot_scripts.pop(key, None)
                        try: bot.send_message(info['chat_id'], f"{info['file_name']} killed: RAM limit ({limits['ram_mb']}MB).")
                        except: pass
        except Exception as e:
            logger.error(f"usage_tracker: {e}")

threading.Thread(target=usage_tracker, daemon=True).start()

# ==========================================================
#  SCHEDULED BROADCAST MONITOR
# ==========================================================
def scheduled_broadcast_monitor():
    while True:
        try:
            time.sleep(60)
            now = datetime.now()
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT id, message, schedule_cron, next_run FROM scheduled_broadcasts')
            rows = c.fetchall()
            for bid, msg, cron, nxt in rows:
                try: next_dt = datetime.fromisoformat(nxt) if nxt else now
                except: next_dt = now
                if now >= next_dt:
                    interval = parse_cron(cron)
                    if interval:
                        threading.Thread(target=execute_broadcast,
                                         args=(msg, None, None, None, OWNER_ID), daemon=True).start()
                        nxt_dt = now + timedelta(seconds=interval)
                        c.execute('UPDATE scheduled_broadcasts SET next_run=? WHERE id=?',
                                  (nxt_dt.isoformat(), bid))
                        conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"sched_broadcast: {e}")

threading.Thread(target=scheduled_broadcast_monitor, daemon=True).start()

# ==========================================================
#  PACKAGE INSTALL
# ==========================================================
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot',
    'aiogram': 'aiogram', 'pyrogram': 'pyrogram', 'telethon': 'telethon',
    'bs4': 'beautifulsoup4', 'requests': 'requests', 'pillow': 'Pillow',
    'cv2': 'opencv-python', 'yaml': 'PyYAML', 'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil', 'pandas': 'pandas', 'numpy': 'numpy',
    'flask': 'Flask', 'django': 'Django', 'sqlalchemy': 'SQLAlchemy',
    'psutil': 'psutil', 'discord': 'discord.py', 'openai': 'openai',
    'anthropic': 'anthropic', 'matplotlib': 'matplotlib',
    'asyncio': None, 'json': None, 'datetime': None, 'os': None, 'sys': None,
    're': None, 'time': None, 'math': None, 'random': None, 'logging': None,
    'threading': None, 'subprocess': None, 'zipfile': None, 'tempfile': None,
    'shutil': None, 'sqlite3': None, 'atexit': None,
}


def attempt_install_pip(mod, message):
    pkg = TELEGRAM_MODULES.get(mod.lower(), mod)
    if pkg is None: return False
    try:
        bot.reply_to(message, f"Installing {pkg}...")
        cmd = get_pip_install_cmd(pkg)
        logger.info(f"pip cmd: {' '.join(cmd)}")
        r = subprocess.run(cmd,
                           capture_output=True, text=True, check=False,
                           encoding='utf-8', errors='ignore', timeout=300)
        if r.returncode == 0:
            bot.reply_to(message, f"Installed {pkg}.")
            return True
        bot.reply_to(message, f"Failed {pkg}.\n{(r.stderr or r.stdout)[:1500]}")
        return False
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")
        return False


def attempt_install_npm(mod, folder, message):
    try:
        bot.reply_to(message, f"Installing Node {mod}...")
        r = subprocess.run(['npm', 'install', mod], capture_output=True, text=True,
                           check=False, cwd=folder, encoding='utf-8', errors='ignore', timeout=300)
        if r.returncode == 0:
            bot.reply_to(message, f"Installed {mod}.")
            return True
        bot.reply_to(message, f"Failed.\n{(r.stderr or r.stdout)[:1500]}")
        return False
    except FileNotFoundError:
        bot.reply_to(message, "npm not found.")
        return False

# ==========================================================
#  ENV
# ==========================================================
def _load_user_env(owner, sname):
    env = os.environ.copy()
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT key, value FROM env_vars WHERE user_id=? AND script_name=?', (owner, sname))
        for k, v in c.fetchall():
            env[k] = v
        conn.close()
    except: pass
    return env

# ==========================================================
#  SANDBOX
# ==========================================================
def apply_sandbox_limits(process, uid):
    if not SANDBOX_MODE: return
    try:
        p = psutil.Process(process.pid)
        try:
            if psutil.POSIX: p.nice(10)
        except: pass
    except Exception as e:
        logger.error(f"sandbox: {e}")

# ==========================================================
#  SCRIPT RUNNERS
# ==========================================================
def run_script(spath, owner, folder, fname, msg, attempt=1):
    if attempt > 2:
        try: bot.send_message(msg.chat.id, f"Failed {fname} after 2 attempts.")
        except: pass
        return
    key = f"{owner}_{fname}"
    def _reply(t, **kw):
        try:
            if getattr(msg, 'message_id', None): bot.reply_to(msg, t, **kw)
            else: bot.send_message(msg.chat.id, t, **kw)
        except: pass
    try:
        if not os.path.exists(spath):
            _reply(f"Script {fname} not found!")
            remove_user_file_db(owner, fname)
            return
        if attempt == 1:
            env = _load_user_env(owner, fname)
            cp = None
            try:
                cp = subprocess.Popen([sys.executable, spath], cwd=folder, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, encoding='utf-8', errors='ignore')
                out, err = cp.communicate(timeout=5)
                if cp.returncode != 0 and err:
                    m = re.search(r"ModuleNotFoundError: No module named '(.+?)'", err)
                    if m:
                        mod = m.group(1).strip().strip("'\"")
                        if attempt_install_pip(mod, msg):
                            _reply(f"Retrying {fname}...")
                            time.sleep(2)
                            threading.Thread(target=run_script, args=(spath, owner, folder, fname, msg, 2)).start()
                            return
                        return
                    _reply(f"Error:\n{err[:500]}")
                    return
            except subprocess.TimeoutExpired:
                if cp and cp.poll() is None: cp.kill(); cp.communicate()
            except: pass
            finally:
                if cp and cp.poll() is None: cp.kill(); cp.communicate()
        log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        env = _load_user_env(owner, fname)
        process = subprocess.Popen([sys.executable, spath], cwd=folder,
                                   stdout=log_file, stderr=log_file, stdin=subprocess.PIPE,
                                   encoding='utf-8', errors='ignore', env=env)
        apply_sandbox_limits(process, owner)
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'file_name': fname,
            'chat_id': msg.chat.id, 'script_owner_id': owner,
            'start_time': datetime.now(), 'user_folder': folder,
            'type': 'py', 'script_key': key
        }
        _reply(f"Python {fname} started! (PID: {process.pid})")
        log_activity(owner, "start", fname)
    except Exception as e:
        logger.error(f"run_script: {e}", exc_info=True)
        _reply(f"Error: {e}")


def run_js_script(spath, owner, folder, fname, msg, attempt=1):
    if attempt > 2:
        try: bot.send_message(msg.chat.id, f"Failed {fname} after 2 attempts.")
        except: pass
        return
    key = f"{owner}_{fname}"
    def _reply(t, **kw):
        try:
            if getattr(msg, 'message_id', None): bot.reply_to(msg, t, **kw)
            else: bot.send_message(msg.chat.id, t, **kw)
        except: pass
    try:
        if not os.path.exists(spath):
            _reply(f"Script {fname} not found!")
            remove_user_file_db(owner, fname)
            return
        if attempt == 1:
            env = _load_user_env(owner, fname)
            cp = None
            try:
                cp = subprocess.Popen(['node', spath], cwd=folder, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, encoding='utf-8', errors='ignore')
                out, err = cp.communicate(timeout=5)
                if cp.returncode != 0 and err:
                    m = re.search(r"Cannot find module '(.+?)'", err)
                    if m:
                        mod = m.group(1).strip().strip("'\"")
                        if not mod.startswith('.') and not mod.startswith('/'):
                            if attempt_install_npm(mod, folder, msg):
                                _reply(f"Retrying {fname}...")
                                time.sleep(2)
                                threading.Thread(target=run_js_script, args=(spath, owner, folder, fname, msg, 2)).start()
                                return
                            return
                    _reply(f"JS error:\n{err[:500]}")
                    return
            except subprocess.TimeoutExpired:
                if cp and cp.poll() is None: cp.kill(); cp.communicate()
            except: pass
            finally:
                if cp and cp.poll() is None: cp.kill(); cp.communicate()
        log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        env = _load_user_env(owner, fname)
        process = subprocess.Popen(['node', spath], cwd=folder,
                                   stdout=log_file, stderr=log_file, stdin=subprocess.PIPE,
                                   encoding='utf-8', errors='ignore', env=env)
        apply_sandbox_limits(process, owner)
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'file_name': fname,
            'chat_id': msg.chat.id, 'script_owner_id': owner,
            'start_time': datetime.now(), 'user_folder': folder,
            'type': 'js', 'script_key': key
        }
        _reply(f"JS {fname} started! (PID: {process.pid})")
        log_activity(owner, "start", fname)
    except Exception as e:
        logger.error(f"run_js: {e}", exc_info=True)
        _reply(f"Error: {e}")


def run_generic_script(spath, owner, folder, fname, ftype, msg, attempt=1):
    key = f"{owner}_{fname}"
    def _reply(t, **kw):
        try:
            if getattr(msg, 'message_id', None): bot.reply_to(msg, t, **kw)
            else: bot.send_message(msg.chat.id, t, **kw)
        except: pass
    ext = '.' + ftype
    cfg = LANG_CONFIG.get(ext)
    if not cfg:
        _reply(f"Unsupported language: {ftype}")
        return
    try:
        if not os.path.exists(spath):
            _reply(f"Script {fname} not found!")
            return
        log_path = os.path.join(folder, f"{os.path.splitext(fname)[0]}.log")
        log_file = open(log_path, 'w', encoding='utf-8', errors='ignore')
        env = _load_user_env(owner, fname)
        cmd = cfg['cmd'] + [spath]
        process = subprocess.Popen(cmd, cwd=folder, stdout=log_file, stderr=log_file,
                                   stdin=subprocess.PIPE, encoding='utf-8', errors='ignore', env=env)
        apply_sandbox_limits(process, owner)
        bot_scripts[key] = {
            'process': process, 'log_file': log_file, 'file_name': fname,
            'chat_id': msg.chat.id, 'script_owner_id': owner,
            'start_time': datetime.now(), 'user_folder': folder,
            'type': ftype, 'script_key': key
        }
        _reply(f"{ftype.upper()} {fname} started! (PID: {process.pid})")
        log_activity(owner, "start", fname)
    except FileNotFoundError:
        _reply(f"Runtime {cfg['runner']} not found.")
    except Exception as e:
        _reply(f"Error: {e}")

# ==========================================================
#  DB OPS
# ==========================================================
DB_LOCK = threading.Lock()


def save_user_file(uid, fname, ftype='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files VALUES (?,?,?)', (uid, fname, ftype))
            conn.commit()
            user_files.setdefault(uid, [])
            user_files[uid] = [(fn, ft) for fn, ft in user_files[uid] if fn != fname]
            user_files[uid].append((fname, ftype))
        except: pass
        finally: conn.close()


def remove_user_file_db(uid, fname):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id=? AND file_name=?', (uid, fname))
            conn.commit()
            if uid in user_files:
                user_files[uid] = [f for f in user_files[uid] if f[0] != fname]
                if not user_files[uid]: del user_files[uid]
        except: pass
        finally: conn.close()


def add_active_user(uid):
    active_users.add(uid)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users VALUES (?)', (uid,))
            conn.commit()
        except: pass
        finally: conn.close()


def save_env_var(uid, sn, k, v):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO env_vars VALUES (?,?,?,?)', (uid, sn, k, v))
            conn.commit()
        except: pass
        finally: conn.close()


def save_subscription(uid, expiry, tier='basic'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO subscriptions VALUES (?,?,?)', (uid, expiry.isoformat(), tier))
            c.execute('INSERT OR REPLACE INTO user_tiers VALUES (?,?)', (uid, tier))
            conn.commit()
            user_subscriptions[uid] = {'expiry': expiry, 'tier': tier}
            user_tiers[uid] = tier
        except: pass
        finally: conn.close()


def remove_subscription_db(uid):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id=?', (uid,))
            c.execute('DELETE FROM user_tiers WHERE user_id=?', (uid,))
            conn.commit()
            user_subscriptions.pop(uid, None)
            user_tiers.pop(uid, None)
        except: pass
        finally: conn.close()


def add_admin_db(aid):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins VALUES (?)', (aid,))
            conn.commit()
            admin_ids.add(aid)
            logger.info(f"Admin {aid} added")
        except Exception as e:
            logger.error(f"add_admin_db: {e}")
        finally: conn.close()


def remove_admin_db(aid):
    if aid == OWNER_ID: return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM admins WHERE user_id=?', (aid,))
            conn.commit()
            admin_ids.discard(aid)
            logger.info(f"Admin {aid} removed")
            return True
        except Exception as e:
            logger.error(f"remove_admin_db: {e}")
            return False
        finally: conn.close()


def add_moderator_db(mid):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO moderators VALUES (?)', (mid,))
            conn.commit()
            moderator_ids.add(mid)
        except: pass
        finally: conn.close()


def remove_moderator_db(mid):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM moderators WHERE user_id=?', (mid,))
            conn.commit()
            moderator_ids.discard(mid)
            return True
        except: return False
        finally: conn.close()


def save_user_bot_token(uid, bot_token, admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_bot_tokens VALUES (?,?,?,?)',
                      (uid, bot_token, admin_id, datetime.now().isoformat()))
            conn.commit()
            user_bot_tokens[uid] = {'bot_token': bot_token, 'admin_id': admin_id}
        except: pass
        finally: conn.close()

# ==========================================================
#  MENUS
# ==========================================================
def create_main_menu_inline(uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(types.InlineKeyboardButton('Updates Channel', url=UPDATE_CHANNEL))
    mk.row(
        types.InlineKeyboardButton('Upload File', callback_data='upload'),
        types.InlineKeyboardButton('Check Files', callback_data='check_files')
    )
    mk.row(
        types.InlineKeyboardButton('Bot Speed', callback_data='speed'),
        types.InlineKeyboardButton('Statistics', callback_data='stats')
    )
    mk.row(
        types.InlineKeyboardButton('AI Assistant', callback_data='ai_menu'),
        types.InlineKeyboardButton('AI Generator', callback_data='ai_gen')
    )
    mk.row(
        types.InlineKeyboardButton('Templates', callback_data='templates'),
        types.InlineKeyboardButton('GitHub Import', callback_data='github_import')
    )
    mk.row(
        types.InlineKeyboardButton('Daily Bonus', callback_data='daily_bonus'),
        types.InlineKeyboardButton('Referral', callback_data='referral')
    )
    mk.row(
        types.InlineKeyboardButton('Marketplace', callback_data='marketplace'),
        types.InlineKeyboardButton('My Tier', callback_data='my_tier')
    )
    mk.row(
        types.InlineKeyboardButton('Buy Premium', callback_data='buy_premium'),
        types.InlineKeyboardButton('API Keys', callback_data='api_keys')
    )
    mk.row(
        types.InlineKeyboardButton('Usage', callback_data='my_usage'),
        types.InlineKeyboardButton('Send Command', callback_data='send_command')
    )
    mk.add(types.InlineKeyboardButton('API Dashboard', url=f"{PUBLIC_URL}/dashboard"))
    if uid in admin_ids:
        mk.row(
            types.InlineKeyboardButton('Subscriptions', callback_data='subscription'),
            types.InlineKeyboardButton('Broadcast', callback_data='broadcast')
        )
        mk.row(
            types.InlineKeyboardButton('Lock Bot' if not bot_locked else 'Unlock Bot',
                                        callback_data='lock_bot' if not bot_locked else 'unlock_bot'),
            types.InlineKeyboardButton('Run All Scripts', callback_data='run_all_scripts')
        )
        mk.row(
            types.InlineKeyboardButton('Admin Panel', callback_data='admin_panel'),
            types.InlineKeyboardButton('Emergency Kill', callback_data='emergency_kill')
        )
    mk.add(types.InlineKeyboardButton('Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    return mk


def create_reply_keyboard_main_menu(uid):
    layout = [
        ["Upload File", "Check Files"],
        ["AI Assistant", "AI Generator"],
        ["Templates", "Marketplace"],
        ["My Tier", "Buy Premium"],
        ["Daily Bonus", "Referral"],
        ["Bot Speed", "Statistics"],
        ["API Dashboard", "Contact Owner"]
    ]
    if uid in admin_ids:
        layout = [
            ["Upload File", "Check Files"],
            ["AI Assistant", "Subscriptions"],
            ["Broadcast", "Lock Bot"],
            ["Run All Scripts", "Admin Panel"],
            ["Bot Speed", "Statistics"],
            ["API Dashboard", "Contact Owner"]
        ]
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for row in layout:
        mk.add(*[types.KeyboardButton(t) for t in row])
    return mk


def create_control_buttons(owner, fname, running=True):
    mk = types.InlineKeyboardMarkup(row_width=2)
    if running:
        mk.row(
            types.InlineKeyboardButton("Stop", callback_data=f'stop_{owner}_{fname}'),
            types.InlineKeyboardButton("Restart", callback_data=f'restart_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Delete", callback_data=f'delete_{owner}_{fname}'),
            types.InlineKeyboardButton("Logs", callback_data=f'logs_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Info", callback_data=f'info_{owner}_{fname}'),
            types.InlineKeyboardButton("Download", callback_data=f'download_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Env Vars", callback_data=f'env_{owner}_{fname}'),
            types.InlineKeyboardButton("AutoRestart", callback_data=f'autorestart_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Rename", callback_data=f'rename_{owner}_{fname}'),
            types.InlineKeyboardButton("Live Logs", callback_data=f'livelog_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("CPU Graph", callback_data=f'graph_{owner}_{fname}'),
            types.InlineKeyboardButton("History", callback_data=f'history_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Webhook", callback_data=f'webhook_{owner}_{fname}'),
            types.InlineKeyboardButton("Schedule", callback_data=f'schedule_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Backup", callback_data=f'backup_{owner}_{fname}'),
            types.InlineKeyboardButton("Versions", callback_data=f'versions_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Tags", callback_data=f'tags_{owner}_{fname}'),
            types.InlineKeyboardButton("CI/CD", callback_data=f'cicd_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Share to Market", callback_data=f'sharemarket_{owner}_{fname}'),
            types.InlineKeyboardButton("Sandbox", callback_data=f'sandbox_{owner}_{fname}')
        )
    else:
        mk.row(
            types.InlineKeyboardButton("Start", callback_data=f'start_{owner}_{fname}'),
            types.InlineKeyboardButton("Delete", callback_data=f'delete_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Logs", callback_data=f'logs_{owner}_{fname}'),
            types.InlineKeyboardButton("Info", callback_data=f'info_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Download", callback_data=f'download_{owner}_{fname}'),
            types.InlineKeyboardButton("Env Vars", callback_data=f'env_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("AutoRestart", callback_data=f'autorestart_{owner}_{fname}'),
            types.InlineKeyboardButton("Rename", callback_data=f'rename_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Webhook", callback_data=f'webhook_{owner}_{fname}'),
            types.InlineKeyboardButton("Schedule", callback_data=f'schedule_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Backup", callback_data=f'backup_{owner}_{fname}'),
            types.InlineKeyboardButton("Versions", callback_data=f'versions_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Tags", callback_data=f'tags_{owner}_{fname}'),
            types.InlineKeyboardButton("CI/CD", callback_data=f'cicd_{owner}_{fname}')
        )
        mk.row(
            types.InlineKeyboardButton("Share to Market", callback_data=f'sharemarket_{owner}_{fname}'),
            types.InlineKeyboardButton("Sandbox", callback_data=f'sandbox_{owner}_{fname}')
        )
    mk.add(types.InlineKeyboardButton("Back to Files", callback_data='check_files'))
    return mk


def create_ai_menu(uid):
    mk = types.InlineKeyboardMarkup(row_width=2)
    label = AI_SEEK_MODEL_LABELS.get(get_user_ai_model(uid), get_user_ai_model(uid))
    mk.row(
        types.InlineKeyboardButton("Debug Error", callback_data='ai_debug'),
        types.InlineKeyboardButton("Explain Code", callback_data='ai_explain')
    )
    mk.row(
        types.InlineKeyboardButton("Optimize Code", callback_data='ai_optimize'),
        types.InlineKeyboardButton("Ask Anything", callback_data='ai_ask')
    )
    mk.row(types.InlineKeyboardButton(f"Model: {label}", callback_data='ai_change_model'))
    mk.row(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
    return mk


def create_ai_model_menu():
    mk = types.InlineKeyboardMarkup(row_width=1)
    for m in AI_SEEK_MODELS:
        mk.add(types.InlineKeyboardButton(AI_SEEK_MODEL_LABELS.get(m, m), callback_data=f'ai_set_{m}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='ai_menu'))
    return mk


def create_admin_panel():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton('Add Admin', callback_data='add_admin'),
        types.InlineKeyboardButton('Remove Admin', callback_data='remove_admin')
    )
    mk.row(
        types.InlineKeyboardButton('Add Moderator', callback_data='add_mod'),
        types.InlineKeyboardButton('Remove Moderator', callback_data='remove_mod')
    )
    mk.row(types.InlineKeyboardButton('List Staff', callback_data='list_admins'))
    mk.row(types.InlineKeyboardButton('View Activity', callback_data='admin_all_logs'))
    mk.row(types.InlineKeyboardButton('Payment Settings', callback_data='payment_settings'))
    mk.row(types.InlineKeyboardButton('Scheduled Broadcasts', callback_data='sched_broadcasts'))
    mk.row(types.InlineKeyboardButton('API Dashboard', url=f"{PUBLIC_URL}/dashboard"))
    mk.row(types.InlineKeyboardButton('Back', callback_data='back_to_main'))
    return mk


def create_subscription_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton('Add Sub', callback_data='add_subscription'),
        types.InlineKeyboardButton('Remove Sub', callback_data='remove_subscription')
    )
    mk.row(types.InlineKeyboardButton('Check Sub', callback_data='check_subscription'))
    mk.row(types.InlineKeyboardButton('Set Tier', callback_data='set_tier'))
    mk.row(types.InlineKeyboardButton('Back', callback_data='back_to_main'))
    return mk


def create_send_command_menu():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton('Send to Process', callback_data='send_to_process'),
        types.InlineKeyboardButton('View All Logs', callback_data='view_all_logs')
    )
    mk.row(types.InlineKeyboardButton('Back', callback_data='back_to_main'))
    return mk


def create_templates_menu():
    mk = types.InlineKeyboardMarkup(row_width=1)
    for key, t in SCRIPT_TEMPLATES.items():
        mk.add(types.InlineKeyboardButton(t['name'], callback_data=f'tpl_{key}'))
    mk.row(
        types.InlineKeyboardButton("AI Generator", callback_data='ai_gen'),
        types.InlineKeyboardButton("Back", callback_data='back_to_main')
    )
    return mk


def create_marketplace_menu():
    mk = types.InlineKeyboardMarkup(row_width=1)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('''SELECT m.id, m.name, m.language, m.downloads, m.rating, m.verified, s.until
                     FROM marketplace m LEFT JOIN sponsored s ON m.id = s.script_id
                     ORDER BY (s.until IS NOT NULL AND s.until > ?) DESC, m.downloads DESC LIMIT 20''',
                  (datetime.now().isoformat(),))
        for mid, name, lang, dl, rating, verified, sponsored_until in c.fetchall():
            tag = "[SPONSORED] " if sponsored_until and sponsored_until > datetime.now().isoformat() else ""
            v = "*" if verified else ""
            r = f" {rating:.1f}" if rating else ""
            mk.add(types.InlineKeyboardButton(f"{tag}{name} ({lang}){v} | {dl} dl{r}",
                                              callback_data=f'mkt_{mid}'))
        conn.close()
    except: pass
    mk.add(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
    return mk


def create_batch_menu(uid):
    mk = types.InlineKeyboardMarkup(row_width=1)
    fl = user_files.get(uid, [])
    sel = user_batch_selection.get(uid, set())
    for fn, ft in sorted(fl):
        r = is_bot_running(uid, fn)
        check = "[X]" if fn in sel else "[ ]"
        mk.add(types.InlineKeyboardButton(f"{check} {fn} ({ft}) {'R' if r else 'S'}",
                                          callback_data=f'batch_toggle_{uid}_{fn}'))
    mk.row(
        types.InlineKeyboardButton("Start Selected", callback_data=f'batch_start_{uid}'),
        types.InlineKeyboardButton("Stop Selected", callback_data=f'batch_stop_{uid}')
    )
    mk.row(
        types.InlineKeyboardButton("Delete Selected", callback_data=f'batch_delete_{uid}'),
        types.InlineKeyboardButton("Clear Selection", callback_data=f'batch_clear_{uid}')
    )
    mk.row(
        types.InlineKeyboardButton("Select All", callback_data=f'batch_all_{uid}'),
        types.InlineKeyboardButton("Back", callback_data='check_files')
    )
    return mk


def create_tier_menu():
    mk = types.InlineKeyboardMarkup(row_width=1)
    for tier_key, tier in TIERS.items():
        if tier_key == 'free': continue
        mk.add(types.InlineKeyboardButton(
            f"{tier['name']} - {tier['price_stars']} Stars",
            callback_data=f'buy_{tier_key}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
    return mk

# ==========================================================
#  TIER LOGIC
# ==========================================================
def _logic_my_tier(msg):
    uid = msg.from_user.id
    tier_key = get_user_tier(uid)
    tier = TIERS[tier_key]
    exp_info = ""
    if uid in user_subscriptions:
        exp = user_subscriptions[uid].get('expiry')
        if exp:
            days = (exp - datetime.now()).days
            exp_info = f"\nExpires: {exp:%Y-%m-%d} ({days} days left)"
    text = (f"Your Tier: {tier['name']}{exp_info}\n\n"
            f"Scripts: {tier['scripts']}\n"
            f"Max File: {tier['file_mb']} MB\n"
            f"RAM Limit: {tier['ram_mb']} MB\n"
            f"CPU Limit: {tier['cpu_percent']}%\n"
            f"API Rate: {tier['api_rate']}/min\n"
            f"AI Requests: {tier['ai_requests_day']}/day\n"
            f"Backups: {tier['backups']}\n"
            f"Concurrent Scripts: {tier['concurrent']}")
    bot.reply_to(msg, text)


def _logic_buy_premium(msg):
    bot.reply_to(msg, "Choose a premium tier:", reply_markup=create_tier_menu())


def cb_buy_tier(call):
    tier_key = call.data.replace('buy_', '')
    if tier_key not in TIERS:
        bot.answer_callback_query(call.id, "Invalid tier.")
        return
    tier = TIERS[tier_key]
    uid = call.from_user.id
    if not PAYMENT_ENABLED:
        bot.answer_callback_query(call.id, "Payments disabled.", show_alert=True)
        return
    try:
        prices = [types.LabeledPrice(label=f"{tier['name']} Tier", amount=tier['price_stars'])]
        bot.send_invoice(
            chat_id=uid,
            title=f"ATX Hosting {tier['name']} Tier",
            description=f"{tier['name']} tier for 30 days. {tier['scripts']} scripts, {tier['ram_mb']}MB RAM.",
            invoice_payload=f"tier_{tier_key}_{uid}",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter=f"tier_{tier_key}"
        )
        bot.answer_callback_query(call.id, "Invoice sent!")
    except Exception as e:
        logger.error(f"buy_tier: {e}")
        bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)


@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(pre_checkout_q):
    bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def successful_payment(msg):
    uid = msg.from_user.id
    payload = msg.successful_payment.invoice_payload
    try:
        parts = payload.split('_')
        if parts[0] == 'tier':
            tier_key = parts[1]
            tier = TIERS.get(tier_key)
            if tier:
                cur_exp = user_subscriptions.get(uid, {}).get('expiry')
                start = cur_exp if cur_exp and cur_exp > datetime.now() else datetime.now()
                new_exp = start + timedelta(days=30)
                save_subscription(uid, new_exp, tier_key)
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('INSERT INTO payments (user_id, amount, days, method, status, tier, created) VALUES (?,?,?,?,?,?,?)',
                              (uid, tier['price_stars'], 30, 'stars', 'completed', tier_key, datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                except: pass
                bot.send_message(uid, f"Payment received! {tier['name']} tier active until {new_exp:%Y-%m-%d}.")
                try: bot.send_message(OWNER_ID, f"Payment from {uid}: {tier['name']}, {tier['price_stars']} stars")
                except: pass
    except Exception as e:
        logger.error(f"payment: {e}")

# ==========================================================
#  API KEYS
# ==========================================================
def _logic_api_keys(msg):
    uid = msg.from_user.id
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("Create Key", callback_data='apikey_create'),
        types.InlineKeyboardButton("List Keys", callback_data='apikey_list')
    )
    mk.row(types.InlineKeyboardButton("API Dashboard", url=f"{PUBLIC_URL}/dashboard"))
    mk.row(types.InlineKeyboardButton("API Docs (Health)", url=f"{PUBLIC_URL}/health"))
    mk.row(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
    bot.reply_to(msg, "API Key Management", reply_markup=mk)


def cb_apikey_create(call):
    uid = call.from_user.id
    existing = [k for k, v in user_api_keys.items() if v == uid]
    if len(existing) >= 5:
        bot.answer_callback_query(call.id, "Max 5 keys.", show_alert=True)
        return
    key = 'ATXhost_' + secrets.token_urlsafe(32)
    user_api_keys[key] = uid
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT INTO api_keys VALUES (?,?,?,?)', (uid, key, datetime.now().isoformat(), None, 1))
        conn.commit()
        conn.close()
    except: pass
    bot.answer_callback_query(call.id, "Key created!")
    bot.send_message(uid, f"New API Key:\n{key}\n\nSave this! Hindi na maipapakita muli.")


def cb_apikey_list(call):
    uid = call.from_user.id
    keys = [(k, v) for k, v in user_api_keys.items() if v == uid]
    if not keys:
        bot.answer_callback_query(call.id, "No keys.", show_alert=True)
        return
    mk = types.InlineKeyboardMarkup(row_width=1)
    text = "Your API Keys:\n\n"
    for i, (k, _) in enumerate(keys, 1):
        short = k[:15] + "..." + k[-5:]
        text += f"{i}. {short}\n"
        mk.add(types.InlineKeyboardButton(f"Revoke {i}", callback_data=f'apikey_revoke_{k}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='api_keys'))
    bot.answer_callback_query(call.id)
    bot.send_message(uid, text, reply_markup=mk)


def cb_apikey_revoke(call):
    uid = call.from_user.id
    key = call.data.replace('apikey_revoke_', '')
    if user_api_keys.get(key) != uid:
        bot.answer_callback_query(call.id, "Not your key.", show_alert=True)
        return
    user_api_keys.pop(key, None)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('UPDATE api_keys SET active=0 WHERE key=?', (key,))
        conn.commit()
        conn.close()
    except: pass
    bot.answer_callback_query(call.id, "Revoked.")
    bot.send_message(uid, "API key revoked.")

# ==========================================================
#  USAGE
# ==========================================================
def _logic_my_usage(msg):
    uid = msg.from_user.id
    cpu_min = user_usage[uid].get('cpu_minutes', 0)
    ai_req = user_usage[uid].get('ai_requests_today', 0)
    limits = get_tier_limits(uid)
    text = (f"Your Usage (today)\n\n"
            f"CPU Minutes: {cpu_min:.0f}\n"
            f"AI Requests: {ai_req}/{limits['ai_requests_day']}\n"
            f"API Calls: {user_usage[uid].get('api_calls_today', 0)}\n"
            f"\nTier: {limits['name']}")
    bot.reply_to(msg, text)

# ==========================================================
#  AI GENERATOR - WITH TOKEN + ADMIN ID REQUIRED
# ==========================================================
def cb_ai_gen(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    if uid not in user_bot_tokens:
        m = bot.send_message(
            call.message.chat.id,
            "AI Bot Generator Setup\n\n"
            "Bago ka makapag-generate ng AI bot, kailangan mo munang i-save ang:\n\n"
            "1. Bot Token (mula kay @BotFather)\n"
            "2. Admin ID (ang Telegram ID mo o ng ibang admin)\n\n"
            "Ipadala mo ngayon ang BOT TOKEN mo:"
        )
        bot.register_next_step_handler(m, process_setup_bot_token)
        return
    m = bot.send_message(
        call.message.chat.id,
        "AI Script Generator\n\n"
        f"Bot Token: {user_bot_tokens[uid]['bot_token'][:15]}...\n"
        f"Admin ID: {user_bot_tokens[uid]['admin_id']}\n\n"
        "Ngayon, i-describe mo kung anong bot ang gusto mong gawin:\n"
        "Example: 'telegram bot that replies to /start with hello'\n\n"
        "/cancel to abort"
    )
    bot.register_next_step_handler(m, process_ai_gen)


def process_setup_bot_token(message):
    uid = message.from_user.id
    token = (message.text or "").strip()
    if token.lower() == '/cancel':
        bot.reply_to(message, "Cancelled.")
        return
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
        bot.reply_to(message, "Invalid bot token format. Dapat ganto: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`\n\nTry again or /cancel.", parse_mode='Markdown')
        m = bot.send_message(message.chat.id, "Ipadala muli ang BOT TOKEN:")
        bot.register_next_step_handler(m, process_setup_bot_token)
        return
    m = bot.send_message(message.chat.id,
                         "Bot token saved!\n\n"
                         "Ngayon naman, ipadala ang ADMIN ID.\n"
                         "Ito ang Telegram user ID na magiging admin ng bot mo.\n"
                         "Kung ikaw mismo ang admin, ipadala ang sarili mong ID.\n\n"
                         "/cancel to abort")
    bot.register_next_step_handler(m, process_setup_admin_id, token)


def process_setup_admin_id(message, bot_token):
    uid = message.from_user.id
    admin_id_str = (message.text or "").strip()
    if admin_id_str.lower() == '/cancel':
        bot.reply_to(message, "Cancelled.")
        return
    try:
        admin_id = int(admin_id_str)
        if admin_id <= 0:
            raise ValueError()
    except:
        bot.reply_to(message, "Invalid admin ID. Dapat number.\n\nTry again or /cancel.")
        m = bot.send_message(message.chat.id, "Ipadala muli ang ADMIN ID:")
        bot.register_next_step_handler(m, process_setup_admin_id, bot_token)
        return
    save_user_bot_token(uid, bot_token, admin_id)
    log_activity(uid, "setup_bot_token", f"token=***{bot_token[-6:]}, admin={admin_id}")
    bot.reply_to(
        message,
        f"Setup Complete!\n\n"
        f"Bot Token: {bot_token[:15]}...\n"
        f"Admin ID: {admin_id}\n\n"
        f"Ngayon pwede ka nang mag-generate ng AI bot. I-describe ang gusto mong bot:"
    )
    m = bot.send_message(message.chat.id,
                         "Example: 'telegram bot that replies to /start with hello'\n\n/cancel to abort")
    bot.register_next_step_handler(m, process_ai_gen)


def process_ai_gen(message):
    uid = message.from_user.id
    desc = (message.text or "").strip()
    if desc.lower() == '/cancel': return
    if not desc:
        bot.reply_to(message, "Empty description.")
        return
    if uid not in user_bot_tokens:
        bot.reply_to(message, "Walang bot token na naka-save. I-click muli ang AI Generator.")
        return
    if not check_ai_quota(uid):
        bot.reply_to(message, "AI quota exceeded.")
        return
    bot.reply_to(message, "Generating script... (up to 90s)")
    bt = user_bot_tokens[uid]
    prompt = f"""You are a Python code generator. Generate ONE complete working Python script.

USER REQUEST:
{desc}

STRICT RULES - follow ALL:
1. Output ONLY the Python code. Nothing else.
2. Do NOT include any explanation, no "Here is", no intro, no outro.
3. Do NOT use markdown fences. No ```python. No ```.
4. Do NOT include <think>, <reasoning>, or any XML-like tags.
5. Do NOT include comments before the code starts. Code must start at line 1.
6. Use telebot (pyTelegramBotAPI) for Telegram bots.
7. ALWAYS include InlineKeyboardMarkup with buttons for main commands.
8. Use this BOT_TOKEN: os.environ.get('BOT_TOKEN', '{bt['bot_token']}')
9. Use this ADMIN_ID: os.environ.get('ADMIN_ID', '{bt['admin_id']}')
10. Include a startup message that sends to ADMIN_ID.
11. Wrap main loop in try/except so it never crashes silently.
12. Add short inline comments.

Start your response with the first line of Python code. Nothing before it."""

    model = get_user_ai_model(uid)
    threading.Thread(target=_generate_and_save, args=(uid, desc, prompt, model, message)).start()


def _generate_and_save(uid, desc, prompt, model, message):
    res = ai_seek_query(model, prompt, timeout=120)
    if res.get('error'):
        try: bot.send_message(message.chat.id, f"Error: {res['error']}")
        except: pass
        return
    raw = res.get('answer', '')
    code = clean_ai_code(raw)
    if not code:
        try: bot.send_message(message.chat.id, "AI returned empty or invalid code.")
        except: pass
        return
    if not any(k in code for k in ('import ', 'def ', 'print(', 'class ')):
        try: bot.send_message(message.chat.id, "AI output doesn't look like valid code. Try again.")
        except: pass
        return
    folder = get_user_folder(uid)
    fname = f"ai_gen_{int(time.time())}.py"
    fp = os.path.join(folder, fname)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(code)
    save_user_file(uid, fname, 'py')
    bt = user_bot_tokens.get(uid)
    if bt:
        save_env_var(uid, fname, 'BOT_TOKEN', bt['bot_token'])
        save_env_var(uid, fname, 'ADMIN_ID', str(bt['admin_id']))
    log_activity(uid, "ai_generated", fname)
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("Start Now", callback_data=f'start_{uid}_{fname}'),
        types.InlineKeyboardButton("View Code", callback_data=f'download_{uid}_{fname}')
    )
    mk.row(
        types.InlineKeyboardButton("AI Debug", callback_data='ai_debug'),
        types.InlineKeyboardButton("AI Optimize", callback_data='ai_optimize')
    )
    mk.row(types.InlineKeyboardButton("Check Files", callback_data='check_files'))
    try:
        bot.send_message(
            message.chat.id,
            f"Bot generated: {fname}\n\n"
            f"Description: {desc[:200]}\n\n"
            f"Bot Token at Admin ID ay naka-save na as env vars.\n\n"
            f"Preview (first 1000 chars):\n{code[:1000]}",
            reply_markup=mk
        )
    except:
        try: bot.send_document(message.chat.id, open(fp, 'rb'))
        except: pass

# ==========================================================
#  LOGIC FUNCTIONS
# ==========================================================
def _logic_send_welcome(msg):
    uid = msg.from_user.id
    cid = msg.chat.id
    name = msg.from_user.first_name
    uname = msg.from_user.username
    if bot_locked and uid not in admin_ids:
        bot.send_message(cid, "Bot is locked.")
        return
    if uid not in active_users:
        add_active_user(uid)
        try: bot.send_message(OWNER_ID, f"New user: {name} (@{uname or 'N/A'}) ID: {uid}")
        except: pass
    tier_key = get_user_tier(uid)
    tier = TIERS[tier_key]
    cur = get_user_file_count(uid)
    text = (f"Welcome back, {name}!\n\n"
            f"ID: {uid}\n"
            f"Tier: {tier['name']}\n"
            f"Files: {cur}/{tier['scripts']}\n\n"
            f"Host Python, JS, TS, Ruby, Go, PHP, Bash scripts.\n"
            f"Premium features: AI Generator, Marketplace, API, and more.\n\n"
            f"Use buttons or commands below.")
    try:
        bot.send_message(cid, text, reply_markup=create_reply_keyboard_main_menu(uid))
    except:
        bot.send_message(cid, text)


def _logic_upload(msg):
    uid = msg.from_user.id
    if bot_locked and uid not in admin_ids:
        bot.reply_to(msg, "Bot is locked.")
        return
    limits = get_tier_limits(uid)
    if get_user_file_count(uid) >= limits['scripts']:
        bot.reply_to(msg, f"File limit reached ({limits['scripts']}).")
        return
    bot.reply_to(msg, f"Send .py, .js, .ts, .rb, .go, .php, .sh, or .zip (max {limits['file_mb']} MB).")


def _logic_check_files(msg):
    uid = msg.from_user.id
    fl = user_files.get(uid, [])
    if not fl:
        bot.reply_to(msg, "No files.")
        return
    mk = types.InlineKeyboardMarkup(row_width=1)
    for fn, ft in sorted(fl):
        r = is_bot_running(uid, fn)
        mk.add(types.InlineKeyboardButton(f"{fn} ({ft}) - {'Running' if r else 'Stopped'}",
                                          callback_data=f'file_{uid}_{fn}'))
    mk.add(types.InlineKeyboardButton("Batch Select", callback_data=f'batch_open_{uid}'))
    bot.reply_to(msg, "Your files:", reply_markup=mk)


def _logic_batch(msg):
    uid = msg.from_user.id
    user_batch_selection[uid] = set()
    bot.reply_to(msg, "Batch Selection\n\nTap to toggle scripts:",
                 reply_markup=create_batch_menu(uid))


def _logic_speed(msg):
    uid = msg.from_user.id
    cid = msg.chat.id
    t0 = time.time()
    w = bot.reply_to(msg, "Testing...")
    try:
        bot.send_chat_action(cid, 'typing')
        rt = round((time.time() - t0) * 1000, 2)
        s = "Unlocked" if not bot_locked else "Locked"
        lvl = TIERS[get_user_tier(uid)]['name']
        bot.edit_message_text(f"Speed: {rt} ms\nStatus: {s}\nTier: {lvl}", cid, w.message_id)
    except: pass


def _logic_contact(msg):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton('Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    bot.reply_to(msg, "Contact:", reply_markup=mk)


def _logic_stats(msg):
    uid = msg.from_user.id
    total_users = len(active_users)
    total_files = sum(len(f) for f in user_files.values())
    running = 0
    for k, i in list(bot_scripts.items()):
        if is_bot_running(i['script_owner_id'], i['file_name']):
            running += 1
    st = "Persistent" if RAILWAY_VOLUME_PATH else "Ephemeral"
    text = (f"ATX Hosting Statistics\n\nUsers: {total_users}\nFiles: {total_files}\n"
            f"Running: {running}\nStorage: {st}\nYour Tier: {TIERS[get_user_tier(uid)]['name']}")
    bot.reply_to(msg, text)


def _logic_ai(msg):
    uid = msg.from_user.id
    if bot_locked and uid not in admin_ids:
        bot.reply_to(msg, "Bot is locked.")
        return
    limits = get_tier_limits(uid)
    used = user_usage[uid].get('ai_requests_today', 0)
    bot.reply_to(msg, f"AI Assistant\n\nDaily quota: {used}/{limits['ai_requests_day']}",
                 reply_markup=create_ai_menu(uid))


def _logic_ai_gen(msg):
    uid = msg.from_user.id
    if uid not in user_bot_tokens:
        m = bot.send_message(msg.chat.id,
                             "AI Bot Generator Setup\n\n"
                             "Bago ka makapag-generate, kailangan mo i-save:\n"
                             "1. Bot Token (mula kay @BotFather)\n"
                             "2. Admin ID\n\n"
                             "Ipadala ang BOT TOKEN mo:")
        bot.register_next_step_handler(m, process_setup_bot_token)
        return
    if not check_ai_quota(uid):
        bot.reply_to(msg, "AI quota exceeded.")
        return
    m = bot.send_message(msg.chat.id,
                         f"Bot Token: {user_bot_tokens[uid]['bot_token'][:15]}...\n"
                         f"Admin ID: {user_bot_tokens[uid]['admin_id']}\n\n"
                         "I-describe ang bot:\n/cancel to abort")
    bot.register_next_step_handler(m, process_ai_gen)


def _logic_templates(msg):
    bot.reply_to(msg, "Templates\n\nChoose a starter script:", reply_markup=create_templates_menu())


def _logic_github(msg):
    m = bot.reply_to(msg, "GitHub Import\n\nSend URL: https://github.com/user/repo\n/cancel to abort.")
    bot.register_next_step_handler(m, process_github_import)


def _logic_daily(msg):
    uid = msg.from_user.id
    now = datetime.now()
    last = user_daily_bonus.get(uid)
    if last and (now - last) < timedelta(hours=24):
        rem = timedelta(hours=24) - (now - last)
        h = rem.seconds // 3600
        m = (rem.seconds % 3600) // 60
        bot.reply_to(msg, f"Next bonus in {h}h {m}m.")
        return
    cur_exp = user_subscriptions.get(uid, {}).get('expiry')
    cur_tier = get_user_tier(uid)
    start = cur_exp if cur_exp and cur_exp > now else now
    new_exp = start + timedelta(hours=24)
    tier = 'basic' if cur_tier == 'free' else cur_tier
    save_subscription(uid, new_exp, tier)
    user_daily_bonus[uid] = now
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO daily_bonus VALUES (?,?)', (uid, now.isoformat()))
        conn.commit()
        conn.close()
    except: pass
    bot.reply_to(msg, f"Daily Bonus Claimed!\n+24h {tier} tier!\nExpires: {new_exp:%Y-%m-%d %H:%M}")


def _logic_referral(msg):
    uid = msg.from_user.id
    cnt = user_referrals.get(uid, {}).get('count', 0)
    try: bot_username = bot.get_me().username
    except: bot_username = "yourbot"
    link = f"https://t.me/{bot_username}?start=ref_{uid}"
    text = (f"Referral System\n\nYour link:\n{link}\n\n"
            f"Referred: {cnt} users\nEarn: +3 days premium per referral!")
    mk = types.InlineKeyboardMarkup()
    share_url = f"https://t.me/share/url?url={link}&text=Try ATX Hosting!"
    mk.add(types.InlineKeyboardButton("Share", url=share_url))
    bot.reply_to(msg, text, reply_markup=mk)


def _logic_marketplace(msg):
    bot.reply_to(msg, "Marketplace\n\nShared scripts:", reply_markup=create_marketplace_menu())


def _logic_send_cmd(msg):
    bot.reply_to(msg, "Send Command Options:", reply_markup=create_send_command_menu())


def _logic_runall(mo):
    if isinstance(mo, telebot.types.Message):
        auid = mo.from_user.id
        rf = lambda t, **k: bot.reply_to(mo, t, **k)
        amsg = mo
    elif isinstance(mo, telebot.types.CallbackQuery):
        auid = mo.from_user.id
        acid = mo.message.chat.id
        bot.answer_callback_query(mo.id)
        rf = lambda t, **k: bot.send_message(acid, t, **k)
        amsg = mo.message
    else: return
    if auid not in admin_ids:
        rf("Admin only.")
        return
    rf("Starting all scripts...")
    started = 0
    for tuid, files in dict(user_files).items():
        folder = get_user_folder(tuid)
        for fn, ft in files:
            if not is_bot_running(tuid, fn):
                fp = os.path.join(folder, fn)
                if os.path.exists(fp):
                    if ft == 'py':
                        threading.Thread(target=run_script, args=(fp, tuid, folder, fn, amsg), daemon=True).start()
                    elif ft == 'js':
                        threading.Thread(target=run_js_script, args=(fp, tuid, folder, fn, amsg), daemon=True).start()
                    else:
                        threading.Thread(target=run_generic_script, args=(fp, tuid, folder, fn, ft, amsg), daemon=True).start()
                    started += 1
                    time.sleep(0.7)
    rf(f"Started {started} scripts.")


def _logic_broadcast(msg):
    if msg.from_user.id not in admin_ids:
        bot.reply_to(msg, "Admin only.")
        return
    m = bot.reply_to(msg, "Send message to broadcast.\n/cancel to abort.")
    bot.register_next_step_handler(m, process_broadcast_message)


def _logic_lock(msg):
    if msg.from_user.id not in admin_ids:
        bot.reply_to(msg, "Admin only.")
        return
    global bot_locked
    bot_locked = not bot_locked
    bot.reply_to(msg, f"Bot {'locked' if bot_locked else 'unlocked'}.")


def _logic_admin(msg):
    if msg.from_user.id not in admin_ids:
        bot.reply_to(msg, "Admin only.")
        return
    bot.reply_to(msg, "Admin Panel", reply_markup=create_admin_panel())


def _logic_subs(msg):
    if msg.from_user.id not in admin_ids:
        bot.reply_to(msg, "Admin only.")
        return
    bot.reply_to(msg, "Subscriptions", reply_markup=create_subscription_menu())


def _logic_updates_channel(msg):
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton('Updates Channel', url=UPDATE_CHANNEL))
    bot.reply_to(msg, "Updates Channel:", reply_markup=mk)


def _logic_api_dashboard(msg):
    text = (f"ATX Hosting API\n\n"
            f"Base URL: {PUBLIC_URL}\n\n"
            f"Endpoints:\n"
            f"- GET /health - Status\n"
            f"- GET /dashboard - Web dashboard\n"
            f"- GET /api/stats - Statistics\n"
            f"- GET /api/scripts - List scripts\n"
            f"- GET /api/my/usage - Your usage\n"
            f"- POST /api/script/<uid>/<file>/stop\n"
            f"- POST /api/broadcast (Owner only)\n\n"
            f"Auth: Add header X-API-Key or ?api_key=\n"
            f"Get your key: /apikeys")
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("Open Dashboard", url=f"{PUBLIC_URL}/dashboard"))
    mk.add(types.InlineKeyboardButton("Health Check", url=f"{PUBLIC_URL}/health"))
    mk.add(types.InlineKeyboardButton("Manage API Keys", callback_data='api_keys'))
    bot.reply_to(msg, text, reply_markup=mk)

# ==========================================================
#  BTN ROUTING
# ==========================================================
BTN_LOGIC = {
    "Updates Channel": _logic_updates_channel,
    "Upload File": _logic_upload,
    "Check Files": _logic_check_files,
    "Bot Speed": _logic_speed,
    "Statistics": _logic_stats,
    "AI Assistant": _logic_ai,
    "AI Generator": _logic_ai_gen,
    "Templates": _logic_templates,
    "GitHub Import": _logic_github,
    "Daily Bonus": _logic_daily,
    "Referral": _logic_referral,
    "Marketplace": _logic_marketplace,
    "Send Command": _logic_send_cmd,
    "Contact Owner": _logic_contact,
    "Subscriptions": _logic_subs,
    "Broadcast": _logic_broadcast,
    "Lock Bot": _logic_lock,
    "Run All Scripts": _logic_runall,
    "Admin Panel": _logic_admin,
    "My Tier": _logic_my_tier,
    "Buy Premium": _logic_buy_premium,
    "API Keys": _logic_api_keys,
    "Usage": _logic_my_usage,
    "API Dashboard": _logic_api_dashboard,
}

# ==========================================================
#  COMMANDS
# ==========================================================
@bot.message_handler(commands=['start', 'help'])
def cmd_start(m):
    if m.text and m.text.startswith('/start ref_'):
        try:
            referrer = int(m.text.split('ref_')[1].strip())
            uid = m.from_user.id
            if referrer != uid and uid not in user_referrals:
                user_referrals[uid] = {'referred_by': referrer, 'count': 0}
                user_referrals.setdefault(referrer, {'referred_by': None, 'count': 0})
                user_referrals[referrer]['count'] = user_referrals[referrer].get('count', 0) + 1
                cur_exp = user_subscriptions.get(referrer, {}).get('expiry')
                start = cur_exp if cur_exp and cur_exp > datetime.now() else datetime.now()
                new_exp = start + timedelta(days=3)
                save_subscription(referrer, new_exp, get_user_tier(referrer))
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('INSERT OR REPLACE INTO referrals VALUES (?,?,?)', (uid, referrer, 0))
                    c.execute('INSERT OR REPLACE INTO referrals VALUES (?,?,?)',
                              (referrer, user_referrals[referrer].get('referred_by'),
                               user_referrals[referrer]['count']))
                    conn.commit()
                    conn.close()
                except: pass
                try: bot.send_message(referrer, "You earned +3 days premium from a referral!")
                except: pass
        except: pass
    _logic_send_welcome(m)


@bot.message_handler(commands=['ai'])
def cmd_ai(m): _logic_ai(m)


@bot.message_handler(commands=['gen'])
def cmd_gen(m): _logic_ai_gen(m)


@bot.message_handler(commands=['filter'])
def cmd_filter(m): cb_filter_tags(m)


@bot.message_handler(commands=['my_tier'])
def cmd_my_tier(m): _logic_my_tier(m)


@bot.message_handler(commands=['usage'])
def cmd_usage(m): _logic_my_usage(m)


@bot.message_handler(commands=['buy'])
def cmd_buy(m): _logic_buy_premium(m)


@bot.message_handler(commands=['batch'])
def cmd_batch(m): _logic_batch(m)


@bot.message_handler(commands=['api'])
def cmd_api(m): _logic_api_dashboard(m)


@bot.message_handler(commands=['reset_token'])
def cmd_reset_token(m):
    uid = m.from_user.id
    if uid in user_bot_tokens:
        del user_bot_tokens[uid]
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM user_bot_tokens WHERE user_id=?', (uid,))
            conn.commit()
            conn.close()
        except: pass
    bot.reply_to(m, "Bot token reset. Use /gen to setup again.")


@bot.message_handler(commands=['aiseek'])
def cmd_aiseek(m):
    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(m, "Usage: /aiseek <question>")
        return
    uid = m.from_user.id
    if not check_ai_quota(uid):
        bot.reply_to(m, "AI quota exceeded.")
        return
    if not check_rate_limit(uid, limit=5, window=60):
        bot.reply_to(m, "Rate limit. Wait 1 minute.")
        return
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), args[1].strip(), m.message_id)


@bot.message_handler(commands=['debug'])
def cmd_debug(m):
    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(m, "Usage: /debug <error or script name>")
        return
    q = args[1].strip()
    uf = user_files.get(m.from_user.id, [])
    match = next((f for f in uf if q.lower() in f[0].lower()), None)
    if match:
        lp = os.path.join(get_user_folder(m.from_user.id), f"{os.path.splitext(match[0])[0]}.log")
        if os.path.exists(lp):
            try:
                with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
                    q = f"Logs of {match[0]}. Find error and explain:\n\n{chr(10).join(f.read().splitlines()[-150:])}"
            except: pass
    uid = m.from_user.id
    if not check_ai_quota(uid):
        bot.reply_to(m, "AI quota exceeded.")
        return
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), q, m.message_id)


@bot.message_handler(commands=['daily'])
def cmd_daily(m): _logic_daily(m)


@bot.message_handler(commands=['refer'])
def cmd_refer(m): _logic_referral(m)


@bot.message_handler(commands=['templates'])
def cmd_tpl(m): _logic_templates(m)


@bot.message_handler(commands=['market'])
def cmd_market(m): _logic_marketplace(m)


@bot.message_handler(commands=['apikeys'])
def cmd_apikeys(m): _logic_api_keys(m)


@bot.message_handler(commands=['ping'])
def cmd_ping(m):
    t0 = time.time()
    msg = bot.reply_to(m, "Pong!")
    latency = round((time.time() - t0) * 1000, 2)
    bot.edit_message_text(f"Pong! Latency: {latency} ms", m.chat.id, msg.message_id)


@bot.message_handler(commands=['status', 'stats'])
def cmd_status(m): _logic_stats(m)


@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(m): _logic_broadcast(m)


@bot.message_handler(commands=['runall'])
def cmd_runall(m): _logic_runall(m)


@bot.message_handler(commands=['schedbc'])
def cmd_schedbc(m):
    if m.from_user.id not in admin_ids: return
    args = m.text.split(maxsplit=3)
    if len(args) < 2:
        bot.reply_to(m, "Usage: /schedbc add|list|remove ...")
        return
    subcmd = args[1].lower()
    if subcmd == 'add' and len(args) >= 4:
        cron = args[2]
        message = args[3]
        sec = parse_cron(cron)
        if not sec:
            bot.reply_to(m, "Invalid cron.")
            return
        nxt = (datetime.now() + timedelta(seconds=sec)).isoformat()
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('INSERT INTO scheduled_broadcasts (message, schedule_cron, next_run, created_by, created) VALUES (?,?,?,?,?)',
                      (message, cron, nxt, m.from_user.id, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            bot.reply_to(m, f"Scheduled: '{message}' every {cron}")
        except Exception as e:
            bot.reply_to(m, f"Error: {e}")
    elif subcmd == 'list':
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT id, message, schedule_cron, next_run FROM scheduled_broadcasts')
            rows = c.fetchall()
            conn.close()
            if not rows:
                bot.reply_to(m, "No scheduled broadcasts.")
                return
            text = "Scheduled Broadcasts:\n\n"
            for bid, msg, cron, nxt in rows:
                text += f"[{bid}] '{msg[:40]}' every {cron}, next: {nxt[:19]}\n"
            bot.reply_to(m, text[:4000])
        except: pass
    elif subcmd == 'remove' and len(args) >= 3:
        try:
            bid = int(args[2])
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM scheduled_broadcasts WHERE id=?', (bid,))
            conn.commit()
            conn.close()
            bot.reply_to(m, f"Removed schedule {bid}.")
        except: pass


@bot.message_handler(func=lambda m: m.text in BTN_LOGIC)
def handle_btn(m):
    f = BTN_LOGIC.get(m.text)
    if f: f(m)

# ==========================================================
#  DOCUMENT HANDLER
# ==========================================================
SUPPORTED_EXTS = list(LANG_CONFIG.keys()) + ['.zip']


@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    uid = msg.from_user.id
    cid = msg.chat.id
    doc = msg.document
    if bot_locked and uid not in admin_ids:
        bot.reply_to(msg, "Bot is locked.")
        return
    limits = get_tier_limits(uid)
    if get_user_file_count(uid) >= limits['scripts']:
        bot.reply_to(msg, f"Limit reached ({limits['scripts']}).")
        return
    fn = doc.file_name
    if not fn:
        bot.reply_to(msg, "No name.")
        return
    ext = os.path.splitext(fn)[1].lower()
    if ext not in SUPPORTED_EXTS:
        bot.reply_to(msg, f"Allowed: {', '.join(SUPPORTED_EXTS)}")
        return
    max_size = limits['file_mb'] * 1024 * 1024
    if doc.file_size > max_size:
        bot.reply_to(msg, f"Max {limits['file_mb']} MB for your tier.")
        return
    try:
        try: bot.forward_message(OWNER_ID, cid, msg.message_id)
        except: pass
        w = bot.reply_to(msg, f"Downloading {fn}...")
        fi = bot.get_file(doc.file_id)
        content = bot.download_file(fi.file_path)
        bot.edit_message_text(f"Downloaded. Processing...", cid, w.message_id)
        ufolder = get_user_folder(uid)
        if ext == '.zip':
            handle_zip_file(content, fn, msg)
        else:
            fp = os.path.join(ufolder, fn)
            with open(fp, 'wb') as f: f.write(content)
            cfg = LANG_CONFIG.get(ext)
            if not cfg: return
            ftype = cfg['type']
            if ftype == 'py': handle_py_file(fp, uid, ufolder, fn, msg)
            elif ftype == 'js': handle_js_file(fp, uid, ufolder, fn, msg)
            else: handle_generic_file(fp, uid, ufolder, fn, ftype, msg)
    except telebot.apihelper.ApiTelegramException as e:
        bot.reply_to(msg, f"API: {e}")
    except Exception as e:
        logger.error(f"doc: {e}", exc_info=True)
        bot.reply_to(msg, f"Error: {e}")


def handle_zip_file(content, fname_zip, msg):
    uid = msg.from_user.id
    ufolder = get_user_folder(uid)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"u_{uid}_")
        zp = os.path.join(temp_dir, fname_zip)
        with open(zp, 'wb') as f: f.write(content)
        with zipfile.ZipFile(zp, 'r') as zr:
            for m in zr.infolist():
                mp = os.path.abspath(os.path.join(temp_dir, m.filename))
                if not mp.startswith(os.path.abspath(temp_dir)):
                    raise zipfile.BadZipFile(f"Unsafe: {m.filename}")
            zr.extractall(temp_dir)
        target = temp_dir
        root = os.listdir(target)
        all_exts = tuple(LANG_CONFIG.keys())
        if not any(f.endswith(all_exts) for f in root):
            for r, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                if any(f.endswith(all_exts) for f in files):
                    target = r
                    break
        if target != temp_dir:
            for it in os.listdir(target):
                s = os.path.join(target, it)
                d = os.path.join(temp_dir, it)
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                shutil.move(s, d)
            items = os.listdir(temp_dir)
        else:
            items = root
        scripts = [f for f in items if any(f.endswith(e) for e in all_exts)]
        req = 'requirements.txt' if 'requirements.txt' in items else None
        pkg = 'package.json' if 'package.json' in items else None
        if req:
            try:
                bot.reply_to(msg, "Installing Python deps...")
                cmd = get_pip_install_cmd(['-r', os.path.join(temp_dir, req)])
                subprocess.run(cmd, capture_output=True, text=True, check=True,
                               encoding='utf-8', errors='ignore', timeout=300)
                bot.reply_to(msg, "Python deps installed.")
            except Exception as e:
                bot.reply_to(msg, f"Deps failed: {e}")
                return
        if pkg:
            try:
                bot.reply_to(msg, "Installing Node deps...")
                subprocess.run(['npm', 'install'], capture_output=True, text=True, check=True,
                               cwd=temp_dir, encoding='utf-8', errors='ignore', timeout=300)
                bot.reply_to(msg, "Node deps installed.")
            except Exception as e:
                bot.reply_to(msg, f"Node deps failed: {e}")
                return
        if not scripts:
            bot.reply_to(msg, "No supported script found!")
            return
        preferred = ['main.py','bot.py','app.py','index.js','main.js','bot.js','app.js']
        main_script = next((p for p in preferred if p in scripts), scripts[0])
        ext = os.path.splitext(main_script)[1].lower()
        ftype = LANG_CONFIG.get(ext, {}).get('type', 'py')
        for it in os.listdir(temp_dir):
            if it == fname_zip: continue
            src = os.path.join(temp_dir, it)
            dst = os.path.join(ufolder, it)
            if os.path.isdir(dst): shutil.rmtree(dst)
            elif os.path.exists(dst): os.remove(dst)
            shutil.move(src, dst)
        save_user_file(uid, main_script, ftype)
        bot.reply_to(msg, f"Files extracted. Starting {main_script}...")
        sp = os.path.join(ufolder, main_script)
        if ftype == 'py':
            threading.Thread(target=run_script, args=(sp, uid, ufolder, main_script, msg)).start()
        elif ftype == 'js':
            threading.Thread(target=run_js_script, args=(sp, uid, ufolder, main_script, msg)).start()
        else:
            threading.Thread(target=run_generic_script, args=(sp, uid, ufolder, main_script, ftype, msg)).start()
    except zipfile.BadZipFile as e:
        bot.reply_to(msg, f"Bad ZIP: {e}")
    except Exception as e:
        logger.error(f"zip: {e}", exc_info=True)
        bot.reply_to(msg, f"Error: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except: pass


def handle_py_file(fp, owner, folder, fname, msg):
    try:
        save_user_file(owner, fname, 'py')
        threading.Thread(target=run_script, args=(fp, owner, folder, fname, msg)).start()
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")


def handle_js_file(fp, owner, folder, fname, msg):
    try:
        save_user_file(owner, fname, 'js')
        threading.Thread(target=run_js_script, args=(fp, owner, folder, fname, msg)).start()
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")


def handle_generic_file(fp, owner, folder, fname, ftype, msg):
    try:
        save_user_file(owner, fname, ftype)
        threading.Thread(target=run_generic_script, args=(fp, owner, folder, fname, ftype, msg)).start()
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")

# ==========================================================
#  CALLBACK HANDLER
# ==========================================================
@bot.callback_query_handler(func=lambda c: True)
def handle_cb(call):
    uid = call.from_user.id
    d = call.data
    if bot_locked and uid not in admin_ids and d not in ['back_to_main', 'speed', 'stats', 'ai_menu']:
        bot.answer_callback_query(call.id, "Bot is locked.", show_alert=True)
        return
    if not check_rate_limit(uid, limit=60, window=60):
        bot.answer_callback_query(call.id, "Rate limit. Slow down.", show_alert=True)
        return
    try:
        if d.startswith('batch_open_'): cb_batch_open(call)
        elif d.startswith('batch_toggle_'): cb_batch_toggle(call)
        elif d.startswith('batch_start_'): cb_batch_start(call)
        elif d.startswith('batch_stop_'): cb_batch_stop(call)
        elif d.startswith('batch_delete_'): cb_batch_delete(call)
        elif d.startswith('batch_clear_'): cb_batch_clear(call)
        elif d.startswith('batch_all_'): cb_batch_all(call)
        elif d == 'my_tier': _logic_my_tier(call.message); bot.answer_callback_query(call.id)
        elif d == 'buy_premium': _logic_buy_premium(call.message); bot.answer_callback_query(call.id)
        elif d.startswith('buy_'): cb_buy_tier(call)
        elif d == 'api_keys': _logic_api_keys(call.message); bot.answer_callback_query(call.id)
        elif d == 'apikey_create': cb_apikey_create(call)
        elif d == 'apikey_list': cb_apikey_list(call)
        elif d.startswith('apikey_revoke_'): cb_apikey_revoke(call)
        elif d == 'my_usage': _logic_my_usage(call.message); bot.answer_callback_query(call.id)
        elif d == 'ai_gen': cb_ai_gen(call)
        elif d.startswith('graph_'): cb_graph(call)
        elif d.startswith('history_'): cb_history(call)
        elif d.startswith('tags_'): cb_tags(call)
        elif d.startswith('cicd_setup_github_'): cb_cicd_setup(call)
        elif d.startswith('cicd_'): cb_cicd(call)
        elif d.startswith('sandbox_'): cb_sandbox(call)
        elif d.startswith('mkt_dl_'): cb_mkt_dl(call)
        elif d.startswith('mkt_rate_set_'): cb_mkt_rate_set(call)
        elif d.startswith('mkt_rate_'): cb_mkt_rate(call)
        elif d.startswith('mkt_reviews_'): cb_mkt_reviews(call)
        elif d.startswith('mkt_'): cb_mktitem(call)
        elif d == 'upload': cb_upload(call)
        elif d == 'check_files': cb_checkfiles(call)
        elif d.startswith('file_'): cb_filecontrol(call)
        elif d.startswith('start_'): cb_start(call)
        elif d.startswith('stop_'): cb_stop(call)
        elif d.startswith('restart_'): cb_restart(call)
        elif d.startswith('delete_'): cb_delete(call)
        elif d.startswith('logs_'): cb_logs(call)
        elif d.startswith('info_'): cb_info(call)
        elif d.startswith('download_'): cb_download(call)
        elif d.startswith('env_'): cb_env(call)
        elif d.startswith('autorestart_'): cb_autorestart(call)
        elif d.startswith('ar_set_'): cb_ar_set(call)
        elif d.startswith('rename_'): cb_rename(call)
        elif d.startswith('livelog_'): cb_livelog(call)
        elif d.startswith('webhook_'): cb_webhook(call)
        elif d.startswith('schedule_'): cb_schedule(call)
        elif d.startswith('backup_'): cb_backup(call)
        elif d.startswith('versions_'): cb_versions(call)
        elif d.startswith('sharemarket_'): cb_sharemarket(call)
        elif d == 'speed': cb_speed(call)
        elif d == 'back_to_main': cb_backmain(call)
        elif d.startswith('confirm_broadcast_'): cb_confirmbroadcast(call)
        elif d == 'cancel_broadcast': cb_cancelbroadcast(call)
        elif d == 'send_command': cb_sendcmd(call)
        elif d == 'send_to_process': cb_sendtoproc(call)
        elif d.startswith('sendcmd_select_'): cb_sendcmdsel(call)
        elif d == 'view_all_logs': cb_viewlogs(call)
        elif d.startswith('viewlog_'): cb_viewlog(call)
        elif d == 'subscription': admin_cb(call, cb_subs)
        elif d == 'stats': cb_stats(call)
        elif d == 'lock_bot': admin_cb(call, cb_lock)
        elif d == 'unlock_bot': admin_cb(call, cb_unlock)
        elif d == 'run_all_scripts': admin_cb(call, cb_runall)
        elif d == 'broadcast': admin_cb(call, cb_broadcast)
        elif d == 'admin_panel': admin_cb(call, cb_admin)
        elif d == 'add_admin': owner_cb(call, cb_addadmin)
        elif d == 'remove_admin': owner_cb(call, cb_remadmin)
        elif d == 'add_mod': owner_cb(call, cb_addmod)
        elif d == 'remove_mod': owner_cb(call, cb_remmod)
        elif d == 'list_admins': admin_cb(call, cb_listadmins)
        elif d == 'add_subscription': admin_cb(call, cb_addsub)
        elif d == 'remove_subscription': admin_cb(call, cb_remsub)
        elif d == 'check_subscription': admin_cb(call, cb_checksub)
        elif d == 'set_tier': admin_cb(call, cb_set_tier)
        elif d == 'admin_all_logs': admin_cb(call, cb_admin_all_logs)
        elif d == 'payment_settings': admin_cb(call, cb_payment_settings)
        elif d == 'sched_broadcasts': admin_cb(call, cb_sched_broadcasts)
        elif d == 'emergency_kill': owner_cb(call, cb_emergency_kill)
        elif d == 'ai_menu': cb_aimenu(call)
        elif d == 'ai_debug': cb_aidebug(call)
        elif d == 'ai_explain': cb_aiexplain(call)
        elif d == 'ai_optimize': cb_aioptimize(call)
        elif d == 'ai_ask': cb_aiask(call)
        elif d == 'ai_change_model': cb_aichangemodel(call)
        elif d.startswith('ai_set_'): cb_aisetmodel(call)
        elif d == 'templates': cb_tplmenu(call)
        elif d.startswith('tpl_'): cb_tpluse(call)
        elif d == 'github_import': cb_github(call)
        elif d == 'daily_bonus': _logic_daily(call.message); bot.answer_callback_query(call.id)
        elif d == 'referral': _logic_referral(call.message); bot.answer_callback_query(call.id)
        elif d == 'marketplace': cb_market(call)
        else:
            bot.answer_callback_query(call.id, "Unknown.")
    except Exception as e:
        logger.error(f"cb '{d}': {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "Error.")
        except: pass


def admin_cb(call, f):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "Admin only.", show_alert=True)
        return
    f(call)


def owner_cb(call, f):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "Owner only.", show_alert=True)
        return
    f(call)

# ==========================================================
#  CALLBACK IMPLEMENTATIONS
# ==========================================================
def cb_upload(call):
    bot.answer_callback_query(call.id)
    _logic_upload(call.message)


def cb_checkfiles(call):
    uid = call.from_user.id
    fl = user_files.get(uid, [])
    mk = types.InlineKeyboardMarkup(row_width=1)
    if not fl:
        mk.add(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
        try: bot.edit_message_text("No files.", call.message.chat.id, call.message.message_id, reply_markup=mk)
        except: pass
        bot.answer_callback_query(call.id)
        return
    for fn, ft in sorted(fl):
        r = is_bot_running(uid, fn)
        mk.add(types.InlineKeyboardButton(f"{fn} ({ft}) - {'Running' if r else 'Stopped'}",
                                          callback_data=f'file_{uid}_{fn}'))
    mk.add(types.InlineKeyboardButton("Batch Select", callback_data=f'batch_open_{uid}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='back_to_main'))
    bot.answer_callback_query(call.id)
    try: bot.edit_message_text("Your files:", call.message.chat.id, call.message.message_id, reply_markup=mk)
    except: pass


def cb_filecontrol(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        ruid = call.from_user.id
        if not (ruid == soid or ruid in admin_ids):
            bot.answer_callback_query(call.id, "Own files only.", show_alert=True)
            return
        fl = user_files.get(soid, [])
        if not any(f[0] == fn for f in fl):
            bot.answer_callback_query(call.id, "Not found.", show_alert=True)
            return
        r = is_bot_running(soid, fn)
        ft = next((f[1] for f in fl if f[0] == fn), '?')
        extra = ""
        if r:
            up = get_script_uptime(f"{soid}_{fn}")
            if up: extra += f"\nUptime: {format_uptime(up)}"
            res = get_script_resources(f"{soid}_{fn}")
            if res: extra += f"\nCPU: {res['cpu']:.1f}% | RAM: {res['mem_mb']:.1f}MB"
        tags = user_tags.get(f"{soid}_{fn}", [])
        if tags: extra += f"\nTags: {', '.join(tags)}"
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                f"Controls for: {fn} ({ft})\nStatus: {'Running' if r else 'Stopped'}{extra}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(soid, fn, r))
        except: pass
    except Exception as e:
        logger.error(f"cb_filecontrol: {e}")
        bot.answer_callback_query(call.id, "Error.")


def cb_start(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        fl = user_files.get(soid, [])
        info = next((f for f in fl if f[0] == fn), None)
        if not info: return
        ft = info[1]
        folder = get_user_folder(soid)
        fp = os.path.join(folder, fn)
        if not os.path.exists(fp):
            bot.answer_callback_query(call.id, "File missing!", show_alert=True)
            remove_user_file_db(soid, fn)
            return
        if is_bot_running(soid, fn):
            bot.answer_callback_query(call.id, "Already running.", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Starting...")
        if ft == 'py': threading.Thread(target=run_script, args=(fp, soid, folder, fn, call.message)).start()
        elif ft == 'js': threading.Thread(target=run_js_script, args=(fp, soid, folder, fn, call.message)).start()
        else: threading.Thread(target=run_generic_script, args=(fp, soid, folder, fn, ft, call.message)).start()
        time.sleep(1.5)
        r = is_bot_running(soid, fn)
        try:
            bot.edit_message_text(
                f"Controls for: {fn} ({ft})\nStatus: {'Running' if r else 'Starting...'}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(soid, fn, r))
        except: pass
    except Exception as e:
        logger.error(f"cb_start: {e}")


def cb_stop(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        if not is_bot_running(soid, fn):
            bot.answer_callback_query(call.id, "Not running.", show_alert=True)
            return
        up = get_script_uptime(key) or 0
        script_total_runtime[key] = script_total_runtime.get(key, 0) + up
        auto_restart_config[key] = 0
        pi = bot_scripts.get(key)
        if pi: kill_process_tree(pi)
        bot_scripts.pop(key, None)
        bot.answer_callback_query(call.id, "Stopped.")
        try:
            bot.edit_message_text(f"Controls for: {fn}\nStatus: Stopped",
                                  call.message.chat.id, call.message.message_id,
                                  reply_markup=create_control_buttons(soid, fn, False))
        except: pass
    except Exception as e:
        logger.error(f"cb_stop: {e}")


def cb_restart(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        fl = user_files.get(soid, [])
        info = next((f for f in fl if f[0] == fn), None)
        if not info: return
        ft = info[1]
        folder = get_user_folder(soid)
        fp = os.path.join(folder, fn)
        if not os.path.exists(fp): return
        bot.answer_callback_query(call.id, "Restarting...")
        key = f"{soid}_{fn}"
        if is_bot_running(soid, fn):
            up = get_script_uptime(key) or 0
            script_total_runtime[key] = script_total_runtime.get(key, 0) + up
            pi = bot_scripts.get(key)
            if pi: kill_process_tree(pi)
            bot_scripts.pop(key, None)
            time.sleep(1.5)
        if ft == 'py': threading.Thread(target=run_script, args=(fp, soid, folder, fn, call.message)).start()
        elif ft == 'js': threading.Thread(target=run_js_script, args=(fp, soid, folder, fn, call.message)).start()
        else: threading.Thread(target=run_generic_script, args=(fp, soid, folder, fn, ft, call.message)).start()
        time.sleep(1.5)
        r = is_bot_running(soid, fn)
        try:
            bot.edit_message_text(f"Controls for: {fn}\nStatus: {'Running' if r else 'Starting...'}",
                                  call.message.chat.id, call.message.message_id,
                                  reply_markup=create_control_buttons(soid, fn, r))
        except: pass
    except Exception as e:
        logger.error(f"cb_restart: {e}")


def cb_delete(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        if is_bot_running(soid, fn):
            pi = bot_scripts.get(key)
            if pi: kill_process_tree(pi)
            bot_scripts.pop(key, None)
            time.sleep(0.5)
        folder = get_user_folder(soid)
        for p in [os.path.join(folder, fn), os.path.join(folder, f"{os.path.splitext(fn)[0]}.log")]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        remove_user_file_db(soid, fn)
        bot.answer_callback_query(call.id, "Deleted.")
        try:
            bot.edit_message_text(f"{fn} deleted.", call.message.chat.id, call.message.message_id, reply_markup=None)
        except: pass
    except Exception as e:
        logger.error(f"cb_delete: {e}")


def cb_logs(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        lp = os.path.join(get_user_folder(soid), f"{os.path.splitext(fn)[0]}.log")
        if not os.path.exists(lp):
            bot.answer_callback_query(call.id, "No logs.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if len(content) > 3800: content = "...\n" + content[-3800:]
        if not content.strip(): content = "(empty)"
        bot.send_message(call.message.chat.id, f"Logs for {fn}:\n{content}")
    except Exception as e:
        logger.error(f"cb_logs: {e}")


def cb_info(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        r = is_bot_running(soid, fn)
        lines = [f"Info for {fn}", f"Owner: {soid}", f"Status: {'Running' if r else 'Stopped'}"]
        lines.append(f"Crashes: {script_crash_count.get(key, 0)}")
        lines.append(f"Total Runtime: {format_uptime(script_total_runtime.get(key, 0))}")
        if r:
            up = get_script_uptime(key)
            if up: lines.append(f"Current Uptime: {format_uptime(up)}")
            res = get_script_resources(key)
            if res:
                lines.append(f"CPU: {res['cpu']:.1f}%")
                lines.append(f"RAM: {res['mem_mb']:.1f}MB")
        auto = auto_restart_config.get(key, 0)
        lines.append(f"AutoRestart: {'ON(' + str(auto) + ')' if auto else 'OFF'}")
        tags = user_tags.get(key, [])
        if tags: lines.append(f"Tags: {', '.join(tags)}")
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "\n".join(lines))
    except Exception as e:
        logger.error(f"cb_info: {e}")


def cb_download(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        fp = os.path.join(get_user_folder(soid), fn)
        if not os.path.exists(fp): return
        bot.answer_callback_query(call.id, "Sending...")
        with open(fp, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"{fn}")
    except: pass


def cb_env(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        rows = []
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('SELECT key, value FROM env_vars WHERE user_id=? AND script_name=?', (soid, fn))
            rows = c.fetchall()
            conn.close()
        except: pass
        ex = "\n".join(f"{k} = {v[:20]}..." if len(v) > 20 else f"{k} = {v}" for k, v in rows) if rows else "(none)"
        m = bot.send_message(call.message.chat.id,
                             f"Env Vars for {fn}\n\nCurrent:\n{ex}\n\nFormat: KEY=VALUE\n/cancel to stop.")
        bot.register_next_step_handler(m, proc_env_set, soid, fn)
    except: pass


def proc_env_set(m, soid, fn):
    uid = m.from_user.id
    if not (uid == soid or uid in admin_ids): return
    t = (m.text or "").strip()
    if t.lower() == '/cancel':
        bot.reply_to(m, "Done.")
        return
    if '=' not in t:
        bot.reply_to(m, "Format: KEY=VALUE")
        return
    k, v = t.split('=', 1)
    k, v = k.strip(), v.strip()
    if not k: return
    save_env_var(soid, fn, k, v)
    bot.reply_to(m, f"Saved {k}.")


def cb_autorestart(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        cur = auto_restart_config.get(key, 0)
        bot.answer_callback_query(call.id)
        mk = types.InlineKeyboardMarkup(row_width=4)
        for n in [0, 1, 3, 5]:
            label = "OFF" if n == 0 else f"{n}x"
            mark = " *" if cur == n else ""
            mk.add(types.InlineKeyboardButton(f"{label}{mark}",
                                              callback_data=f'ar_set_{soid}_{fn}_{n}'))
        mk.add(types.InlineKeyboardButton("Back", callback_data=f'file_{soid}_{fn}'))
        bot.send_message(call.message.chat.id,
                         f"AutoRestart for {fn}\nCurrent: {'OFF' if cur == 0 else str(cur) + 'x'}",
                         reply_markup=mk)
    except: pass


def cb_ar_set(call):
    try:
        parts = call.data.split('_')
        soid, fn, n = int(parts[2]), parts[3], int(parts[4])
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        if n == 0: auto_restart_config.pop(key, None)
        else: auto_restart_config[key] = n
        script_restart_count[key] = 0
        bot.answer_callback_query(call.id, f"Set to {'OFF' if n == 0 else str(n) + 'x'}")
    except: pass


def cb_rename(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        m = bot.send_message(call.message.chat.id, f"Rename {fn}\n\nSend new name (with ext):\n/cancel to abort.")
        bot.register_next_step_handler(m, proc_rename, soid, fn)
    except: pass


def proc_rename(m, soid, fn):
    uid = m.from_user.id
    if not (uid == soid or uid in admin_ids): return
    new = (m.text or "").strip()
    if new.lower() == '/cancel': return
    if not new or '/' in new or '\\' in new: return
    ext = os.path.splitext(new)[1].lower()
    if ext not in LANG_CONFIG: return
    folder = get_user_folder(soid)
    old_p = os.path.join(folder, fn)
    new_p = os.path.join(folder, new)
    if not os.path.exists(old_p): return
    if os.path.exists(new_p):
        bot.reply_to(m, "Name exists.")
        return
    try:
        os.rename(old_p, new_p)
        remove_user_file_db(soid, fn)
        save_user_file(soid, new, LANG_CONFIG[ext]['type'])
        bot.reply_to(m, f"Renamed to {new}.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_livelog(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"Live Logs for {fn}\n\nStreaming 30 seconds...")
        lp = os.path.join(get_user_folder(soid), f"{os.path.splitext(fn)[0]}.log")
        threading.Thread(target=stream_logs, args=(call.message.chat.id, lp, soid, fn), daemon=True).start()
    except: pass


def stream_logs(chat_id, log_path, soid, fn):
    last_size = 0
    for _ in range(10):
        time.sleep(3)
        if not os.path.exists(log_path): continue
        try:
            size = os.path.getsize(log_path)
            if size > last_size:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_size)
                    new = f.read()
                last_size = size
                if new.strip():
                    if len(new) > 3800: new = new[-3800:]
                    try: bot.send_message(chat_id, f"[{fn}]:\n{new}")
                    except: pass
        except: pass


def cb_webhook(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        cur = user_webhooks.get(f"{soid}_{fn}", "none")
        m = bot.send_message(call.message.chat.id,
                             f"Webhook Notify for {fn}\n\nCurrent: {cur}\n\nSend URL.\n/cancel to remove.")
        bot.register_next_step_handler(m, proc_webhook, soid, fn)
    except: pass


def proc_webhook(m, soid, fn):
    if m.from_user.id != soid and m.from_user.id not in admin_ids: return
    t = (m.text or "").strip()
    if t.lower() == '/cancel':
        user_webhooks.pop(f"{soid}_{fn}", None)
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM webhooks WHERE user_id=? AND script_name=?', (soid, fn))
            conn.commit(); conn.close()
        except: pass
        bot.reply_to(m, "Removed.")
        return
    if not (t.startswith('http://') or t.startswith('https://')): return
    user_webhooks[f"{soid}_{fn}"] = t
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO webhooks VALUES (?,?,?)', (soid, fn, t))
        conn.commit(); conn.close()
    except: pass
    bot.reply_to(m, "Webhook set!")


def cb_schedule(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        m = bot.send_message(call.message.chat.id,
                             f"Schedule {fn}\n\nFormat: 5m, 1h, 24h, 7d, or * * * * *\n/cancel to remove.")
        bot.register_next_step_handler(m, proc_schedule, soid, fn)
    except: pass


def proc_schedule(m, soid, fn):
    if m.from_user.id != soid and m.from_user.id not in admin_ids: return
    t = (m.text or "").strip()
    if t.lower() == '/cancel':
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM schedules WHERE user_id=? AND script_name=?', (soid, fn))
            conn.commit(); conn.close()
        except: pass
        bot.reply_to(m, "Removed.")
        return
    sec = parse_cron(t)
    if not sec: return
    nxt = (datetime.now() + timedelta(seconds=sec)).isoformat()
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO schedules VALUES (?,?,?,?)', (soid, fn, t, nxt))
        conn.commit(); conn.close()
    except: pass
    bot.reply_to(m, f"Schedule: every {t}")


def cb_backup(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        fp = os.path.join(get_user_folder(soid), fn)
        if not os.path.exists(fp): return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bk = os.path.join(BACKUPS_DIR, f"{soid}_{fn}_{ts}.bak")
        shutil.copy2(fp, bk)
        bot.answer_callback_query(call.id, "Backup created.")
        with open(bk, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"Backup: {fn}")
    except: pass


def cb_versions(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        fp = os.path.join(get_user_folder(soid), fn)
        if not os.path.exists(fp): return
        vdir = os.path.join(VERSIONS_DIR, str(soid), fn.replace('/', '_'))
        os.makedirs(vdir, exist_ok=True)
        existing = sorted(os.listdir(vdir))
        next_ver = len(existing) + 1
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        vpath = os.path.join(vdir, f"v{next_ver}_{ts}.bak")
        shutil.copy2(fp, vpath)
        all_v = sorted(os.listdir(vdir))
        for old in all_v[:-3]:
            try: os.remove(os.path.join(vdir, old))
            except: pass
        bot.answer_callback_query(call.id, f"Version {next_ver} saved.")
        bot.send_message(call.message.chat.id, f"Version {next_ver} saved for {fn}.")
    except: pass


def cb_sharemarket(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if call.from_user.id != soid: return
        bot.answer_callback_query(call.id)
        m = bot.send_message(call.message.chat.id, f"Share {fn}\n\nSend description:\n/cancel to abort.")
        bot.register_next_step_handler(m, proc_sharemarket, soid, fn)
    except: pass


def proc_sharemarket(m, soid, fn):
    if m.from_user.id != soid: return
    t = (m.text or "").strip()
    if t.lower() == '/cancel': return
    ext = os.path.splitext(fn)[1].lower()
    ftype = LANG_CONFIG.get(ext, {}).get('type', 'py')
    src = os.path.join(get_user_folder(soid), fn)
    if not os.path.exists(src): return
    mid = secrets.token_hex(8)
    dst = os.path.join(MARKETPLACE_DIR, f"{mid}_{fn}")
    shutil.copy2(src, dst)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT INTO marketplace (uploader_id, name, description, language, file_path, downloads, rating, rating_count, verified, created) VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (soid, fn, t[:200], ftype, dst, 0, 0, 0, 0, datetime.now().isoformat()))
        conn.commit(); conn.close()
        bot.reply_to(m, f"Shared to marketplace as {fn}!")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_market(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Marketplace", call.message.chat.id, call.message.message_id,
                              reply_markup=create_marketplace_menu())
    except: pass


def cb_speed(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    t0 = time.time()
    try:
        bot.edit_message_text("Testing...", cid, call.message.message_id)
        bot.send_chat_action(cid, 'typing')
        rt = round((time.time() - t0) * 1000, 2)
        s = "Unlocked" if not bot_locked else "Locked"
        lvl = TIERS[get_user_tier(uid)]['name']
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"Speed: {rt} ms\nStatus: {s}\nTier: {lvl}",
                              cid, call.message.message_id, reply_markup=create_main_menu_inline(uid))
    except: pass


def cb_backmain(call):
    uid = call.from_user.id
    text = f"Welcome to ATX Hosting, {call.from_user.first_name}!\n\nID: {uid}\nTier: {TIERS[get_user_tier(uid)]['name']}"
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=create_main_menu_inline(uid))
    except: pass


def cb_stats(call):
    bot.answer_callback_query(call.id)
    _logic_stats(call.message)


def cb_sendcmd(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Send Command Options:", call.message.chat.id, call.message.message_id,
                              reply_markup=create_send_command_menu())
    except: pass


def cb_sendtoproc(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send command:")
    bot.register_next_step_handler(m, send_to_process_init)


def send_to_process_init(m):
    uid = m.from_user.id
    scripts = []
    for k, i in bot_scripts.items():
        o = i['script_owner_id']
        if (uid == o or uid in admin_ids) and is_bot_running(o, i['file_name']):
            scripts.append((k, i))
    if not scripts:
        bot.reply_to(m, "No running scripts.")
        return
    mk = types.InlineKeyboardMarkup(row_width=1)
    for k, i in scripts:
        mk.add(types.InlineKeyboardButton(f"{i['file_name']} (User {i['script_owner_id']})",
                                          callback_data=f'sendcmd_select_{k}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='send_command'))
    bot.reply_to(m, "Select:", reply_markup=mk)


def cb_sendcmdsel(call):
    try:
        key = call.data.replace('sendcmd_select_', '')
        bot.answer_callback_query(call.id, f"Selected: {key}")
        m = bot.send_message(call.message.chat.id, f"Command for {key}:")
        bot.register_next_step_handler(m, lambda mm: proc_send_cmd(mm, key))
    except: pass


def proc_send_cmd(m, key):
    if key not in bot_scripts:
        bot.reply_to(m, "Not running.")
        return
    try:
        p = bot_scripts[key]['process']
        if p and p.poll() is None:
            p.stdin.write((m.text or '') + '\n')
            p.stdin.flush()
            command_history[key].append({'cmd': m.text, 'ts': datetime.now().strftime('%H:%M:%S')})
            bot.reply_to(m, f"Sent: {m.text}")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_viewlogs(call):
    bot.answer_callback_query(call.id)
    uid = call.from_user.id
    folder = get_user_folder(uid)
    if not os.path.exists(folder):
        bot.send_message(call.message.chat.id, "No logs.")
        return
    mk = types.InlineKeyboardMarkup(row_width=1)
    for f in os.listdir(folder):
        if f.endswith('.log'):
            sz = os.path.getsize(os.path.join(folder, f))
            mk.add(types.InlineKeyboardButton(f"{f} ({sz/1024:.1f}KB)",
                                              callback_data=f'viewlog_{uid}_{f}'))
    mk.add(types.InlineKeyboardButton("Back", callback_data='send_command'))
    bot.send_message(call.message.chat.id, "Logs:", reply_markup=mk)


def cb_viewlog(call):
    try:
        _, uid_s, lf = call.data.split('_', 2)
        uid = int(uid_s)
        if not (call.from_user.id == uid or call.from_user.id in admin_ids): return
        lp = os.path.join(get_user_folder(uid), lf)
        if not os.path.exists(lp): return
        bot.answer_callback_query(call.id, "Sending...")
        with open(lp, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"{lf}")
    except: pass


def cb_aimenu(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("AI Assistant\n\nChoose action:",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=create_ai_menu(call.from_user.id))
    except: pass


def cb_aidebug(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Debug - script name or error:")
    bot.register_next_step_handler(m, proc_ai_debug)


def proc_ai_debug(m):
    uid = m.from_user.id
    q = (m.text or "").strip()
    if not q: return
    if not check_ai_quota(uid):
        bot.reply_to(m, "AI quota exceeded.")
        return
    uf = user_files.get(uid, [])
    match = next((f for f in uf if q.lower() in f[0].lower()), None)
    if match:
        lp = os.path.join(get_user_folder(uid), f"{os.path.splitext(match[0])[0]}.log")
        if os.path.exists(lp):
            try:
                with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
                    content = "\n".join(f.read().splitlines()[-150:])
                q = (f"Ito ang logs ng script ko. Hanapin ang error at ipaliwanag. "
                     f"Huwag gumamit ng <think> tags.\n\nScript: {match[0]}\n\nLogs:\n{content}")
            except: pass
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), q, m.message_id)


def cb_aiexplain(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Explain - script name or code:")
    bot.register_next_step_handler(m, proc_ai_explain)


def proc_ai_explain(m):
    uid = m.from_user.id
    q = (m.text or "").strip()
    if not q: return
    if not check_ai_quota(uid): return
    uf = user_files.get(uid, [])
    match = next((f for f in uf if q.lower() in f[0].lower()), None)
    if match:
        fp = os.path.join(get_user_folder(uid), match[0])
        if os.path.exists(fp):
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()[:6000]
                q = f"Ipaliwanag ang code na ito sa simpleng Tagalog. Huwag gumamit ng <think> tags.\n\n{code}"
            except: pass
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), q, m.message_id)


def cb_aioptimize(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Optimize - script name or code:")
    bot.register_next_step_handler(m, proc_ai_optimize)


def proc_ai_optimize(m):
    uid = m.from_user.id
    q = (m.text or "").strip()
    if not q: return
    if not check_ai_quota(uid): return
    uf = user_files.get(uid, [])
    match = next((f for f in uf if q.lower() in f[0].lower()), None)
    if match:
        fp = os.path.join(get_user_folder(uid), match[0])
        if os.path.exists(fp):
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()[:6000]
                q = f"I-optimize ang code na ito. Huwag gumamit ng <think> tags.\n\n{code}"
            except: pass
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), q, m.message_id)


def cb_aiask(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Ask:")
    bot.register_next_step_handler(m, proc_ai_ask)


def proc_ai_ask(m):
    uid = m.from_user.id
    q = (m.text or "").strip()
    if not q: return
    if not check_ai_quota(uid): return
    ai_seek_send_long(m.chat.id, get_user_ai_model(uid), q, m.message_id)


def cb_aichangemodel(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Choose model:", call.message.chat.id, call.message.message_id,
                              reply_markup=create_ai_model_menu())
    except: pass


def cb_aisetmodel(call):
    uid = call.from_user.id
    model = call.data.replace('ai_set_', '')
    if model in AI_SEEK_MODELS:
        user_ai_model[uid] = model
        bot.answer_callback_query(call.id, f"{AI_SEEK_MODEL_LABELS.get(model, model)}")
        try:
            bot.edit_message_text(
                f"Model: {AI_SEEK_MODEL_LABELS.get(model, model)}",
                call.message.chat.id, call.message.message_id,
                reply_markup=create_ai_menu(uid))
        except: pass


def cb_tplmenu(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Templates:", call.message.chat.id, call.message.message_id,
                              reply_markup=create_templates_menu())
    except: pass


def cb_tpluse(call):
    key = call.data.replace('tpl_', '')
    tpl = SCRIPT_TEMPLATES.get(key)
    if not tpl: return
    uid = call.from_user.id
    folder = get_user_folder(uid)
    ext = '.py' if tpl['lang'] == 'py' else '.js'
    fname = f"{key}_template{ext}"
    i = 1
    while os.path.exists(os.path.join(folder, fname)):
        fname = f"{key}_template_{i}{ext}"
        i += 1
    fp = os.path.join(folder, fname)
    with open(fp, 'w', encoding='utf-8') as f: f.write(tpl['code'])
    save_user_file(uid, fname, tpl['lang'])
    bot.answer_callback_query(call.id, "Added!")
    bot.send_message(call.message.chat.id, f"{tpl['name']} added as {fname}.")


def cb_github(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "GitHub Import\n\nSend URL:\n/cancel to abort.")
    bot.register_next_step_handler(m, process_github_import)


def process_github_import(m):
    uid = m.from_user.id
    t = (m.text or "").strip()
    if t.lower() == '/cancel': return
    if not re.match(r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$', t):
        bot.reply_to(m, "Invalid URL.")
        return
    bot.reply_to(m, "Cloning...")
    folder = get_user_folder(uid)
    repo_name = t.rstrip('/').split('/')[-1].replace('.git', '')
    clone_path = os.path.join(folder, f"gh_{repo_name}_{secrets.token_hex(4)}")
    try:
        r = subprocess.run(['git', 'clone', '--depth', '1', t, clone_path],
                           capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
        if r.returncode != 0:
            bot.reply_to(m, f"Failed: {(r.stderr or r.stdout)[:500]}")
            return
        all_exts = tuple(LANG_CONFIG.keys())
        scripts = []
        for root, dirs, files in os.walk(clone_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if any(f.endswith(e) for e in all_exts):
                    scripts.append(os.path.join(root, f))
        if not scripts:
            bot.reply_to(m, "No scripts found.")
            shutil.rmtree(clone_path, ignore_errors=True)
            return
        preferred = ['main.py','bot.py','app.py','index.js','main.js','bot.js','app.js']
        main = None
        for p in preferred:
            for s in scripts:
                if os.path.basename(s) == p: main = s; break
            if main: break
        if not main: main = scripts[0]
        for item in os.listdir(clone_path):
            if item == '.git': continue
            s = os.path.join(clone_path, item)
            d = os.path.join(folder, item)
            if os.path.exists(d):
                if os.path.isdir(d): shutil.rmtree(d)
                else: os.remove(d)
            shutil.move(s, d)
        shutil.rmtree(clone_path, ignore_errors=True)
        main_name = os.path.basename(main)
        ext = os.path.splitext(main_name)[1].lower()
        ftype = LANG_CONFIG.get(ext, {}).get('type', 'py')
        save_user_file(uid, main_name, ftype)
        bot.reply_to(m, f"Cloned! Main: {main_name}")
    except FileNotFoundError:
        bot.reply_to(m, "git not found.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")
        shutil.rmtree(clone_path, ignore_errors=True)


def cb_lock(call):
    global bot_locked
    bot_locked = True
    bot.answer_callback_query(call.id, "Locked.")


def cb_unlock(call):
    global bot_locked
    bot_locked = False
    bot.answer_callback_query(call.id, "Unlocked.")


def cb_runall(call): _logic_runall(call)


def cb_broadcast(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send broadcast:\n/cancel to abort.")
    bot.register_next_step_handler(m, process_broadcast_message)


def cb_admin(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Admin Panel", call.message.chat.id, call.message.message_id,
                              reply_markup=create_admin_panel())
    except: pass


def cb_subs(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Subscriptions", call.message.chat.id, call.message.message_id,
                              reply_markup=create_subscription_menu())
    except: pass


def cb_addadmin(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to promote:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_addadmin)


def proc_addadmin(m):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "Owner only.")
        return
    if (m.text or "").lower() == '/cancel':
        bot.reply_to(m, "Cancelled.")
        return
    try:
        aid = int(m.text.strip())
        if aid <= 0:
            bot.reply_to(m, "Invalid ID.")
            return
        if aid == OWNER_ID:
            bot.reply_to(m, "Already Owner.")
            return
        if aid in admin_ids:
            bot.reply_to(m, f"{aid} is already Admin.")
            return
        add_admin_db(aid)
        bot.reply_to(m, f"{aid} promoted to Admin.")
        try: bot.send_message(aid, "You are now Admin!")
        except: pass
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_remadmin(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to demote:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_remadmin)


def proc_remadmin(m):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "Owner only.")
        return
    if (m.text or "").lower() == '/cancel':
        bot.reply_to(m, "Cancelled.")
        return
    try:
        aid = int(m.text.strip())
        if aid == OWNER_ID:
            bot.reply_to(m, "Cannot remove Owner.")
            return
        if aid not in admin_ids:
            bot.reply_to(m, f"{aid} is not Admin.")
            return
        if remove_admin_db(aid):
            bot.reply_to(m, f"{aid} removed from Admin.")
            try: bot.send_message(aid, "You are no longer Admin.")
            except: pass
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_addmod(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to make Moderator:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_addmod)


def proc_addmod(m):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "Owner only.")
        return
    if (m.text or "").lower() == '/cancel':
        bot.reply_to(m, "Cancelled.")
        return
    try:
        mid = int(m.text.strip())
        if mid <= 0 or mid == OWNER_ID or mid in moderator_ids:
            bot.reply_to(m, "Invalid or already moderator.")
            return
        add_moderator_db(mid)
        bot.reply_to(m, f"{mid} is now Moderator.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_remmod(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to remove Moderator:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_remmod)


def proc_remmod(m):
    if m.from_user.id != OWNER_ID:
        bot.reply_to(m, "Owner only.")
        return
    if (m.text or "").lower() == '/cancel':
        bot.reply_to(m, "Cancelled.")
        return
    try:
        mid = int(m.text.strip())
        if mid not in moderator_ids:
            bot.reply_to(m, "Not a Moderator.")
            return
        if remove_moderator_db(mid):
            bot.reply_to(m, f"{mid} removed.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_listadmins(call):
    bot.answer_callback_query(call.id)
    try:
        lst = "\n".join(f"{a} {'(Owner)' if a == OWNER_ID else ''}" for a in sorted(admin_ids))
        mods = "\n".join(str(m) for m in sorted(moderator_ids)) or "(none)"
        text = f"Admins:\n{lst}\n\nModerators:\n{mods}"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=create_admin_panel())
    except: pass


def cb_addsub(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Format: USER_ID DAYS [TIER]\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_addsub)


def proc_addsub(m):
    if m.from_user.id not in admin_ids: return
    if (m.text or "").lower() == '/cancel': return
    try:
        parts = m.text.split()
        if len(parts) < 2:
            bot.reply_to(m, "Format: USER_ID DAYS [TIER]")
            return
        uid = int(parts[0]); days = int(parts[1])
        tier = parts[2] if len(parts) > 2 else 'basic'
        if tier not in TIERS: tier = 'basic'
        cur = user_subscriptions.get(uid, {}).get('expiry')
        start = cur if cur and cur > datetime.now() else datetime.now()
        new_exp = start + timedelta(days=days)
        save_subscription(uid, new_exp, tier)
        bot.reply_to(m, f"{uid} +{days}d ({tier}). Exp: {new_exp:%Y-%m-%d}")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_remsub(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to remove sub:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_remsub)


def proc_remsub(m):
    if m.from_user.id not in admin_ids: return
    if (m.text or "").lower() == '/cancel': return
    try:
        uid = int(m.text.strip())
        remove_subscription_db(uid)
        bot.reply_to(m, f"Removed {uid}.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_checksub(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Send User ID to check:\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_checksub)


def proc_checksub(m):
    if m.from_user.id not in admin_ids: return
    if (m.text or "").lower() == '/cancel': return
    try:
        uid = int(m.text.strip())
        if uid in user_subscriptions:
            e = user_subscriptions[uid].get('expiry')
            tier = user_subscriptions[uid].get('tier', 'free')
            if e and e > datetime.now():
                bot.reply_to(m, f"Active: {tier} until {e:%Y-%m-%d}")
            else:
                bot.reply_to(m, "Expired.")
                remove_subscription_db(uid)
        else:
            bot.reply_to(m, "No sub.")
    except Exception as e:
        bot.reply_to(m, f"Error: {e}")


def cb_set_tier(call):
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id, "Format: USER_ID TIER\nTiers: free, basic, pro, business, enterprise\n/cancel to abort.")
    bot.register_next_step_handler(m, proc_set_tier)


def proc_set_tier(message):
    if message.from_user.id not in admin_ids: return
    text = (message.text or "").strip()
    if text.lower() == '/cancel': return
    parts = text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Format: USER_ID TIER")
        return
    try:
        uid = int(parts[0])
        tier = parts[1].lower()
        if tier not in TIERS:
            bot.reply_to(message, f"Invalid tier. Options: {', '.join(TIERS.keys())}")
            return
        if tier == 'free':
            remove_subscription_db(uid)
        else:
            new_exp = datetime.now() + timedelta(days=30)
            save_subscription(uid, new_exp, tier)
        bot.reply_to(message, f"{uid} set to {tier} tier.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


def cb_admin_all_logs(call):
    bot.answer_callback_query(call.id)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, action, details, timestamp FROM activity_log ORDER BY id DESC LIMIT 30')
        rows = c.fetchall()
        conn.close()
        if not rows:
            bot.send_message(call.message.chat.id, "No activity.")
            return
        text = "Recent Activity:\n\n"
        for uid, act, det, ts in rows:
            text += f"[{ts[:19]}] {uid} {act}: {det[:60]}\n"
        bot.send_message(call.message.chat.id, text[:4000])
    except: pass


def cb_payment_settings(call):
    bot.answer_callback_query(call.id)
    text = (f"Payment Settings\n\n"
            f"Status: {'Enabled' if PAYMENT_ENABLED else 'Disabled'}\n"
            f"Tiers: {len(TIERS)}\n"
            f"Currency: Telegram Stars (XTR)\n\nTier Pricing:\n")
    for k, t in TIERS.items():
        if k == 'free': continue
        text += f"{t['name']}: {t['price_stars']} Stars\n"
    bot.send_message(call.message.chat.id, text[:4000])


def cb_sched_broadcasts(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
                     "Scheduled Broadcasts\n\n"
                     "Commands:\n"
                     "/schedbc add <cron> <message>\n"
                     "/schedbc list\n"
                     "/schedbc remove <id>")


def cb_emergency_kill(call):
    global emergency_killed
    bot.answer_callback_query(call.id, "Emergency kill!")
    emergency_killed = True
    logger.critical(f"EMERGENCY KILL by Owner {call.from_user.id}")
    bot.send_message(call.message.chat.id, "EMERGENCY KILL. Stopping all scripts...")
    for key in list(bot_scripts.keys()):
        pi = bot_scripts.get(key)
        if pi: kill_process_tree(pi)
        bot_scripts.pop(key, None)
    bot.send_message(call.message.chat.id, "All stopped.")


def process_broadcast_message(m):
    if m.from_user.id not in admin_ids: return
    if (m.text or "").lower() == '/cancel': return
    if not m.text and not (m.photo or m.video): return
    mk = types.InlineKeyboardMarkup()
    mk.row(
        types.InlineKeyboardButton("Confirm", callback_data=f"confirm_broadcast_{m.message_id}"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel_broadcast")
    )
    txt = (m.text or "(media)")[:500]
    bot.reply_to(m, f"Confirm broadcast to {len(active_users)} users:\n\n{txt}", reply_markup=mk)


def cb_confirmbroadcast(call):
    if call.from_user.id not in admin_ids: return
    try:
        orig = call.message.reply_to_message
        txt = orig.text if orig.text else None
        photo = orig.photo[-1].file_id if orig.photo else None
        video = orig.video.file_id if orig.video else None
        cap = orig.caption if (photo or video) else None
        bot.answer_callback_query(call.id, "Starting...")
        bot.edit_message_text("Broadcasting...", call.message.chat.id, call.message.message_id, reply_markup=None)
        threading.Thread(target=execute_broadcast, args=(txt, photo, video, cap, call.message.chat.id)).start()
    except: pass


def cb_cancelbroadcast(call):
    bot.answer_callback_query(call.id, "Cancelled.")
    bot.delete_message(call.message.chat.id, call.message.message_id)


def execute_broadcast(txt, photo, video, cap, admin_chat):
    sent = failed = blocked = 0
    t0 = time.time()
    users = list(active_users)
    total = len(users)
    for i, u in enumerate(users):
        try:
            if txt: bot.send_message(u, txt)
            elif photo: bot.send_photo(u, photo, caption=cap)
            elif video: bot.send_video(u, video, caption=cap)
            sent += 1
        except telebot.apihelper.ApiTelegramException as e:
            ed = str(e).lower()
            if any(s in ed for s in ["blocked", "deactivated", "not found", "kicked", "restricted"]):
                blocked += 1
            elif "flood" in ed or "too many" in ed:
                m = re.search(r"retry after (\d+)", ed)
                wait = int(m.group(1)) + 1 if m else 5
                time.sleep(wait)
                try:
                    if txt: bot.send_message(u, txt)
                    sent += 1
                except: failed += 1
            else: failed += 1
        except: failed += 1
        if (i + 1) % 25 == 0 and i < total - 1: time.sleep(1.5)
        elif i % 5 == 0: time.sleep(0.2)
    dur = round(time.time() - t0, 2)
    try: bot.send_message(admin_chat, f"Done!\nSent: {sent}\nFailed: {failed}\nBlocked: {blocked}\nTotal: {total}\nDuration: {dur}s")
    except: pass


def cb_graph(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        cpu_data = list(cpu_graphs.get(key, []))
        ram_data = list(ram_graphs.get(key, []))
        if not cpu_data:
            bot.answer_callback_query(call.id, "No data yet.", show_alert=True)
            return
        text = f"Resource Graph for {fn}\n\nCPU (last 60 min):\n"
        text += _ascii_chart([d[1] for d in cpu_data], max_val=100, width=40, height=5)
        text += "\n\nRAM (MB):\n"
        max_ram = max((d[1] for d in ram_data), default=1)
        text += _ascii_chart([d[1] for d in ram_data], max_val=max_ram, width=40, height=5)
        bot.answer_callback_query(call.id)
        try: bot.send_message(call.message.chat.id, text)
        except: bot.send_message(call.message.chat.id, text[:3000])
    except Exception as e:
        logger.error(f"cb_graph: {e}")


def _ascii_chart(values, max_val=100, width=40, height=5):
    if not values: return "(no data)"
    if max_val <= 0: max_val = 1
    step = max(1, len(values) // width)
    sampled = values[::step][:width]
    rows = []
    for y in range(height, 0, -1):
        threshold = (y / height) * max_val
        line = "".join("###" if v >= threshold else "   " for v in sampled)
        rows.append(f"{threshold:5.1f} | {line}")
    rows.append("      +" + "-" * (len(sampled) * 3))
    return "\n".join(rows)


def cb_history(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        history = list(command_history.get(key, []))
        if not history:
            bot.answer_callback_query(call.id, "No history.", show_alert=True)
            return
        text = f"Command History for {fn}\n\n"
        for entry in history[-20:]:
            text += f"[{entry['ts']}] {entry['cmd']}\n"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text[:4000])
    except: pass


def cb_tags(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        key = f"{soid}_{fn}"
        tags = user_tags.get(key, [])
        tags_str = ", ".join(tags) if tags else "(none)"
        m = bot.send_message(call.message.chat.id,
                             f"Tags for {fn}\n\nCurrent: {tags_str}\n\n"
                             f"Send tags (space-separated) or /clear to remove.")
        bot.register_next_step_handler(m, proc_tags, soid, fn)
    except: pass


def proc_tags(message, soid, fn):
    if message.from_user.id != soid and message.from_user.id not in admin_ids: return
    text = (message.text or "").strip()
    key = f"{soid}_{fn}"
    if text.lower() == '/clear':
        user_tags[key] = []
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute('DELETE FROM tags WHERE user_id=? AND script_name=?', (soid, fn))
            conn.commit(); conn.close()
        except: pass
        bot.reply_to(message, "Tags cleared.")
        return
    new_tags = [t.strip() for t in text.split() if t.strip()][:5]
    user_tags[key] = new_tags
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM tags WHERE user_id=? AND script_name=?', (soid, fn))
        for t in new_tags:
            c.execute('INSERT OR IGNORE INTO tags VALUES (?,?,?)', (soid, fn, t))
        conn.commit(); conn.close()
    except: pass
    bot.reply_to(message, f"Tags saved: {', '.join(new_tags)}")


def cb_filter_tags(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /filter <tag>")
        return
    tag = args[1].strip().lower()
    uid = message.from_user.id
    matching = []
    for key, tags in user_tags.items():
        oid, fn = key.split('_', 1)
        if int(oid) == uid and tag in [t.lower() for t in tags]:
            matching.append(fn)
    if not matching:
        bot.reply_to(message, f"No scripts with tag '{tag}'.")
        return
    bot.reply_to(message, f"Scripts with tag '{tag}':\n" + "\n".join(matching))


def cb_mktitem(call):
    try:
        mid = int(call.data.split('_', 1)[1])
        uid = call.from_user.id
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT id, uploader_id, name, description, language, file_path, downloads, rating, rating_count, verified FROM marketplace WHERE id=?', (mid,))
        row = c.fetchone()
        if not row:
            bot.answer_callback_query(call.id, "Not found.", show_alert=True)
            conn.close()
            return
        _, uploader, name, desc, lang, fpath, dl, rating, rc, verified = row
        c.execute('UPDATE marketplace SET downloads=downloads+1 WHERE id=?', (mid,))
        conn.commit()
        conn.close()
        mk = types.InlineKeyboardMarkup(row_width=2)
        mk.row(
            types.InlineKeyboardButton("Download", callback_data=f'mkt_dl_{mid}'),
            types.InlineKeyboardButton("Rate", callback_data=f'mkt_rate_{mid}')
        )
        mk.row(types.InlineKeyboardButton("View Reviews", callback_data=f'mkt_reviews_{mid}'))
        v = " (VERIFIED)" if verified else ""
        text = (f"{name}{v}\nLanguage: {lang}\nUploader: {uploader}\n"
                f"Downloads: {dl+1}\nRating: {rating:.1f}/5 ({rc} reviews)\n\n"
                f"Description:\n{desc}")
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=mk)
    except Exception as e:
        logger.error(f"cb_mktitem: {e}")
        bot.answer_callback_query(call.id, "Error.")


def cb_mkt_dl(call):
    try:
        mid = int(call.data.split('_')[2])
        uid = call.from_user.id
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT name, language, file_path FROM marketplace WHERE id=?', (mid,))
        row = c.fetchone()
        conn.close()
        if not row: return
        name, lang, fpath = row
        if not os.path.exists(fpath): return
        ufolder = get_user_folder(uid)
        dst = os.path.join(ufolder, name)
        shutil.copy2(fpath, dst)
        save_user_file(uid, name, lang)
        bot.answer_callback_query(call.id, "Downloaded!")
        bot.send_message(uid, f"{name} downloaded to your files.")
    except Exception as e:
        logger.error(f"mkt_dl: {e}")


def cb_mkt_rate(call):
    try:
        mid = int(call.data.split('_')[2])
        uid = call.from_user.id
        mk = types.InlineKeyboardMarkup(row_width=5)
        for i in range(1, 6):
            mk.add(types.InlineKeyboardButton(str(i), callback_data=f'mkt_rate_set_{mid}_{i}'))
        bot.answer_callback_query(call.id)
        bot.send_message(uid, "Rate this script (1-5):", reply_markup=mk)
    except Exception as e:
        logger.error(f"mkt_rate: {e}")


def cb_mkt_rate_set(call):
    try:
        parts = call.data.split('_')
        mid, rating = int(parts[3]), int(parts[4])
        uid = call.from_user.id
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT INTO marketplace_reviews (script_id, reviewer_id, rating, comment, created) VALUES (?,?,?,?,?)',
                  (mid, uid, rating, "", datetime.now().isoformat()))
        c.execute('SELECT AVG(rating), COUNT(*) FROM marketplace_reviews WHERE script_id=?', (mid,))
        avg, cnt = c.fetchone()
        c.execute('UPDATE marketplace SET rating=?, rating_count=? WHERE id=?', (avg or 0, cnt or 0, mid))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Rated {rating}/5!")
        bot.send_message(uid, f"Thank you for rating {rating}/5!")
    except Exception as e:
        logger.error(f"mkt_rate_set: {e}")


def cb_mkt_reviews(call):
    try:
        mid = int(call.data.split('_')[2])
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT reviewer_id, rating, comment, created FROM marketplace_reviews WHERE script_id=? ORDER BY id DESC LIMIT 10', (mid,))
        rows = c.fetchall()
        conn.close()
        if not rows:
            bot.answer_callback_query(call.id, "No reviews.", show_alert=True)
            return
        text = "Recent Reviews:\n\n"
        for uid, r, comment, ts in rows:
            text += f"User {uid}: {r}/5"
            if comment: text += f" - {comment[:100]}"
            text += "\n"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text[:4000])
    except Exception as e:
        logger.error(f"mkt_reviews: {e}")


def cb_cicd(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        mk = types.InlineKeyboardMarkup(row_width=1)
        mk.add(types.InlineKeyboardButton("Setup GitHub", callback_data=f'cicd_setup_github_{soid}_{fn}'))
        mk.add(types.InlineKeyboardButton("Back", callback_data=f'file_{soid}_{fn}'))
        bot.send_message(call.message.chat.id,
                         f"CI/CD Pipeline for {fn}\n\nAuto-deploy from GitHub on push.",
                         reply_markup=mk)
    except Exception as e:
        logger.error(f"cicd: {e}")


def cb_cicd_setup(call):
    parts = call.data.split('_')
    soid, fn = int(parts[3]), parts[4]
    if call.from_user.id != soid:
        bot.answer_callback_query(call.id, "Denied.", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    m = bot.send_message(call.message.chat.id,
                         f"GitHub CI/CD for {fn}\n\n"
                         f"Send repo URL and branch:\n"
                         f"Format: https://github.com/user/repo branch\n\n"
                         f"/cancel to abort.")
    bot.register_next_step_handler(m, proc_cicd_setup, soid, fn)


def proc_cicd_setup(message, soid, fn):
    if message.from_user.id != soid: return
    text = (message.text or "").strip()
    if text.lower() == '/cancel': return
    parts = text.split()
    if not parts: return
    url = parts[0]
    branch = parts[1] if len(parts) > 1 else 'main'
    if not re.match(r'^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?$', url):
        bot.reply_to(message, "Invalid GitHub URL.")
        return
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO ci_cd VALUES (?,?,?,?,?,?)',
                  (soid, fn, url, branch, 1, None))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"CI/CD configured!\nRepo: {url}\nBranch: {branch}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


def cb_sandbox(call):
    try:
        _, soid, fn = call.data.split('_', 2)
        soid = int(soid)
        if not (call.from_user.id == soid or call.from_user.id in admin_ids): return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                         f"Sandbox Info for {fn}\n\n"
                         f"Status: {'ENABLED' if SANDBOX_MODE else 'DISABLED'}")
    except: pass


def cb_batch_open(call):
    uid = int(call.data.split('_')[2])
    if call.from_user.id != uid and call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "Denied.", show_alert=True)
        return
    user_batch_selection[uid] = set()
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Batch Selection\n\nTap to toggle:",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=create_batch_menu(uid))
    except: pass


def cb_batch_toggle(call):
    try:
        _, _, uid_s, fn = call.data.split('_', 3)
        uid = int(uid_s)
        if call.from_user.id != uid and call.from_user.id not in admin_ids:
            bot.answer_callback_query(call.id, "Denied.", show_alert=True)
            return
        sel = user_batch_selection.setdefault(uid, set())
        if fn in sel: sel.discard(fn)
        else: sel.add(fn)
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                          reply_markup=create_batch_menu(uid))
        except: pass
    except Exception as e:
        logger.error(f"batch_toggle: {e}")


def cb_batch_start(call):
    uid = int(call.data.split('_')[2])
    if call.from_user.id != uid and call.from_user.id not in admin_ids: return
    sel = user_batch_selection.get(uid, set())
    folder = get_user_folder(uid)
    started = 0
    for fn in sel:
        if is_bot_running(uid, fn): continue
        fp = os.path.join(folder, fn)
        if not os.path.exists(fp): continue
        ft = next((f[1] for f in user_files.get(uid, []) if f[0] == fn), 'py')
        if ft == 'py':
            threading.Thread(target=run_script, args=(fp, uid, folder, fn, call.message), daemon=True).start()
        elif ft == 'js':
            threading.Thread(target=run_js_script, args=(fp, uid, folder, fn, call.message), daemon=True).start()
        else:
            threading.Thread(target=run_generic_script, args=(fp, uid, folder, fn, ft, call.message), daemon=True).start()
        started += 1
        time.sleep(0.3)
    bot.answer_callback_query(call.id, f"Started {started}")


def cb_batch_stop(call):
    uid = int(call.data.split('_')[2])
    if call.from_user.id != uid and call.from_user.id not in admin_ids: return
    sel = user_batch_selection.get(uid, set())
    stopped = 0
    for fn in sel:
        key = f"{uid}_{fn}"
        pi = bot_scripts.get(key)
        if pi:
            kill_process_tree(pi)
            bot_scripts.pop(key, None)
            stopped += 1
    bot.answer_callback_query(call.id, f"Stopped {stopped}")


def cb_batch_delete(call):
    uid = int(call.data.split('_')[2])
    if call.from_user.id != uid and call.from_user.id not in admin_ids: return
    sel = user_batch_selection.get(uid, set())
    folder = get_user_folder(uid)
    deleted = 0
    for fn in sel:
        key = f"{uid}_{fn}"
        pi = bot_scripts.get(key)
        if pi:
            kill_process_tree(pi)
            bot_scripts.pop(key, None)
        fp = os.path.join(folder, fn)
        lp = os.path.join(folder, f"{os.path.splitext(fn)[0]}.log")
        for p in [fp, lp]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        remove_user_file_db(uid, fn)
        deleted += 1
    user_batch_selection[uid] = set()
    bot.answer_callback_query(call.id, f"Deleted {deleted}")


def cb_batch_clear(call):
    uid = int(call.data.split('_')[2])
    user_batch_selection[uid] = set()
    bot.answer_callback_query(call.id, "Cleared.")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=create_batch_menu(uid))
    except: pass


def cb_batch_all(call):
    uid = int(call.data.split('_')[2])
    user_batch_selection[uid] = set(fn for fn, _ in user_files.get(uid, []))
    bot.answer_callback_query(call.id, "Selected all.")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=create_batch_menu(uid))
    except: pass

# ==========================================================
#  FLASK ROUTES
# ==========================================================
def check_ip_whitelist():
    if not IP_WHITELIST: return True
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip: ip = ip.split(',')[0].strip()
    return ip in IP_WHITELIST


def check_api_auth():
    if not REST_API_KEY and not user_api_keys: return None
    key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if key == REST_API_KEY and REST_API_KEY: return OWNER_ID
    if key in user_api_keys:
        uid = user_api_keys[key]
        if check_api_rate(uid):
            user_usage[uid]['api_calls_today'] = user_usage[uid].get('api_calls_today', 0) + 1
            return uid
    return None


@app.before_request
def ip_check():
    if request.path.startswith('/api/') and not check_ip_whitelist():
        return jsonify({"error": "IP not allowed"}), 403


@app.route('/')
def home():
    return "ATX Hosting"


@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "ATX Hosting",
        "version": "123",
        "running_scripts": len(bot_scripts),
        "active_users": len(active_users),
        "storage": "persistent" if RAILWAY_VOLUME_PATH else "ephemeral"
    })


@app.route('/dashboard')
def dashboard():
    stats = {
        "users": len(active_users), "running": 0,
        "files": sum(len(f) for f in user_files.values()),
        "subs": len(user_subscriptions), "revenue": 0,
        "storage": "Persistent" if RAILWAY_VOLUME_PATH else "Ephemeral"
    }
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT SUM(amount) FROM payments WHERE status="completed"')
        r = c.fetchone()
        stats["revenue"] = r[0] or 0
        conn.close()
    except: pass
    scripts_data = []
    for key, info in list(bot_scripts.items()):
        if not is_bot_running(info['script_owner_id'], info['file_name']): continue
        stats["running"] += 1
        up = get_script_uptime(key)
        res = get_script_resources(key)
        scripts_data.append({
            "owner": info['script_owner_id'], "file": info['file_name'],
            "type": info.get('type', '?'),
            "uptime": format_uptime(up) if up else 'N/A',
            "cpu": f"{res['cpu']:.1f}%" if res else 'N/A',
            "ram": f"{res['mem_mb']:.1f}MB" if res else 'N/A'
        })
    return render_template_string(DASHBOARD_HTML, stats=stats, scripts=scripts_data,
                                   now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/api/stats')
def api_stats():
    uid = check_api_auth()
    if not uid: return jsonify({"error": "unauthorized"}), 401
    return jsonify({
        "users": len(active_users), "running_scripts": len(bot_scripts),
        "files": sum(len(f) for f in user_files.values()),
        "subscriptions": len(user_subscriptions)
    })


@app.route('/api/scripts')
def api_scripts():
    uid = check_api_auth()
    if not uid: return jsonify({"error": "unauthorized"}), 401
    data = []
    for key, info in list(bot_scripts.items()):
        if uid != OWNER_ID and info['script_owner_id'] != uid: continue
        up = get_script_uptime(key)
        data.append({
            "key": key, "owner": info['script_owner_id'],
            "file": info['file_name'], "type": info.get('type'),
            "uptime": up, "running": is_bot_running(info['script_owner_id'], info['file_name'])
        })
    return jsonify(data)


@app.route('/api/my/usage')
def api_usage():
    uid = check_api_auth()
    if not uid: return jsonify({"error": "unauthorized"}), 401
    return jsonify({
        "tier": get_user_tier(uid),
        "cpu_minutes": user_usage[uid].get('cpu_minutes', 0),
        "ai_requests": user_usage[uid].get('ai_requests_today', 0),
        "api_calls": user_usage[uid].get('api_calls_today', 0),
        "limits": get_tier_limits(uid)
    })


@app.route('/api/script/<int:owner_id>/<file_name>/stop', methods=['POST'])
def api_stop(owner_id, file_name):
    uid = check_api_auth()
    if not uid: return jsonify({"error": "unauthorized"}), 401
    if uid != owner_id and uid != OWNER_ID:
        return jsonify({"error": "forbidden"}), 403
    key = f"{owner_id}_{file_name}"
    info = bot_scripts.get(key)
    if not info: return jsonify({"error": "not running"}), 404
    kill_process_tree(info)
    bot_scripts.pop(key, None)
    return jsonify({"status": "stopped"})


@app.route('/api/broadcast', methods=['POST'])
def api_broadcast():
    uid = check_api_auth()
    if not uid: return jsonify({"error": "unauthorized"}), 401
    if uid != OWNER_ID: return jsonify({"error": "forbidden"}), 403
    data = request.get_json() or {}
    msg = data.get('message')
    if not msg: return jsonify({"error": "message required"}), 400
    threading.Thread(target=execute_broadcast,
                     args=(msg, None, None, None, OWNER_ID), daemon=True).start()
    return jsonify({"status": "started", "targets": len(active_users)})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    print(f"Flask running on port {os.environ.get('PORT', 8080)}")

# ==========================================================
#  CLEANUP & MAIN
# ==========================================================
def cleanup():
    logger.warning("Shutdown cleanup...")
    for k in list(bot_scripts.keys()):
        if k in bot_scripts:
            kill_process_tree(bot_scripts[k])

atexit.register(cleanup)


def signal_handler(signum, frame):
    logger.warning(f"Signal {signum}")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("ATX Hosting")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Base: {BASE_DIR}")
    logger.info(f"Owner: {OWNER_ID}")
    logger.info(f"Admins: {admin_ids}")
    logger.info(f"Tiers: {len(TIERS)}")
    logger.info(f"Public URL: {PUBLIC_URL}")
    logger.info(f"In venv: {is_in_venv()}")
    logger.info(f"Port: {os.environ.get('PORT', 8080)}")
    logger.info("=" * 50)
    keep_alive()
    logger.info("Starting polling...")

    def polling_loop():
        while True:
            try:
                bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
            except requests.exceptions.ReadTimeout:
                time.sleep(5)
            except requests.exceptions.ConnectionError:
                time.sleep(15)
            except Exception as e:
                logger.critical(f"Polling error: {e}", exc_info=True)
                time.sleep(30)

    threading.Thread(target=polling_loop, daemon=True).start()
    while True:
        time.sleep(60)