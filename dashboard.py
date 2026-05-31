from flask import Flask, render_template_string, current_app, request, jsonify, redirect, url_for
import json
import os

app = Flask(__name__)

def load(f):
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}

def save(f, d):
    json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)

def get_gid():
    bot = current_app.config.get('BOT')
    if bot and hasattr(bot, 'cached_data'):
        for key in ['levels', 'config', 'moderation']:
            d = bot.cached_data.get(key, {})
            if d: return str(list(d.keys())[0])
    cfg = load('config.json')
    if cfg:
        real_ids = [k for k in cfg.keys() if k != 'default_guild']
        if real_ids: return str(real_ids[0])
    return 'default_guild'

# ✨ ВЪЗСТАНОВЕН ДИЗАЙН И СТРУКТУРА ОТ IMAGE_043163.PNG (ПЪЛЕН ЕКРАН)
def render(active_tab, title, subtitle, body_content):
    gid = get_gid()
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }}
            
            /* Разпъване на целия екран без излишни полета */
            body {{ 
                background-color: #1e1f22; 
                color: #dbdee1; 
                display: flex; 
                min-height: 100vh; 
                width: 100%;
            }}
            
            /* Странично меню точно като на първата снимка */
            .sidebar {{ 
                width: 260px; 
                background: #111214; 
                padding: 24px 16px; 
                display: flex; 
                flex-direction: column;
                border-right: 1px solid #1c1d20;
                flex-shrink: 0;
            }}
            
            .sidebar h2 {{ 
                font-size: 19px; 
                color: #fff; 
                margin-bottom: 25px; 
                font-weight: 700; 
                padding-left: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .sidebar-divider {{
                height: 1px;
                background: #2b2d31;
                margin-bottom: 20px;
                width: 100%;
            }}
            
            /* Навигационни линкове с оригиналния дизайн */
            .nav-link {{ 
                display: flex; 
                align-items: center; 
                padding: 12px 15px; 
                color: #949ba4; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: 500; 
                margin-bottom: 6px; 
                font-size: 14px;
                transition: background 0.15s, color 0.15s;
            }}
            
            .nav-link:hover {{ 
                background: #2b2d31; 
                color: #fff; 
            }}
            
            /* Наситено лилав маркер за активен таб от Image_043163.png */
            .nav-link.active {{ 
                background: #7c00ff; 
                color: #fff; 
                font-weight: 600;
            }}
            
            /* Основен контейнер - заема останалото пространство */
            .main-content {{ 
                flex: 1; 
                padding: 40px; 
                overflow-y: auto;
            }}
            
            .header {{ margin-bottom: 35px; }}
            .header h1 {{ color: #fff; font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
            .header p {{ color: #949ba4; font-size: 14px; }}
            
            /* Карти и Инпути */
            .card {{ 
                background: #2b2d31; 
                border-radius: 8px; 
                padding: 25px; 
                margin-bottom: 25px; 
                border: 1px solid #202225; 
            }}
            
            .card-header {{ 
                margin-bottom: 20px; 
                border-bottom: 1px solid #3f4248; 
                padding-bottom: 15px; 
            }}
            
            .card-header h3 {{ color: #fff; font-size: 18px; font-weight: 600; }}
            
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; color: #b5bac1; font-size: 12px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
            
            input[type="text"], input[type="number"], textarea {{ 
                width: 100%; 
                padding: 12px; 
                background: #1e1f22; 
                border: 1px solid #111214; 
                border-radius: 6px; 
                color: #fff; 
                font-size: 14px; 
            }}
            
            input:focus, textarea:focus {{ border-color: #7c00ff; outline: none; }}
            
            /* Бутони от първата картинка */
            .btn {{ 
                background: #7c00ff; 
                color: #fff; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 6px; 
                font-weight: 600; 
                cursor: pointer; 
                font-size: 14px;
                transition: background 0.2s;
            }}
            .btn:hover {{ background: #6600d1; }}
            
            .btn-green {{
                background: #00e676;
                color: #000;
            }}
            .btn-green:hover {{ background: #00c853; color: #fff; }}
            
            .badge-container {{ margin-top: 10px; display: flex; gap: 8px; }}
            .badge {{ background: #111214; padding: 6px 10px; border-radius: 4px; font-size: 12px; color: #00e676; font-family: monospace; cursor: pointer; }}
            .alert-success {{ background: #23a55a; color: #fff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <!-- СТРАНИЧНА ЛЕНТА (ВЪЗСТАНОВЕНА НАПЪЛНО) -->
        <div class="sidebar">
            <h2>👑 Admin Panel</h2>
            <div class="sidebar-divider"></div>
            <a href="/moderation?guild_id={gid}" class="nav-link {'active' if active_tab=='moderation' else ''}">🛡️ Moderation</a>
            <a href="/welcomer?guild_id={gid}" class="nav-link {'active' if active_tab=='welcomer' else ''}">👋 Welcomer</a>
            <a href="/leveling?guild_id={gid}" class="nav-link {'active' if active_tab=='leveling' else ''}">⭐ Leveling System</a>
            <a href="/counting?guild_id={gid}" class="nav-link {'active' if active_tab=='counting' else ''}">🔢 Counting Game</a>
            <a href="/ai_assistant?guild_id={gid}" class="nav-link {'active' if active_tab=='ai_assistant' else ''}">🤖 AI Assistant</a>
            <a href="/daily?guild_id={gid}" class="nav-link {'active' if active_tab=='daily' else ''}">📅 Daily Modules</a>
            <a href="/smashkarts?guild_id={gid}" class="nav-link {'active' if active_tab=='smashkarts' else ''}">🏎️ Smash Karts</a>
            <a href="/story?guild_id={gid}" class="nav-link {'active' if active_tab=='story' else ''}">📖 Story Mode</a>
        </div>
        
        <!-- ОСНОВНО СЪДЪРЖАНИЕ -->
        <div class="main-content">
            <div class="header">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {body_content}
        </div>
    </body>
    </html>
    """)

# ЗАПАЗВАНЕ НА ОРИГИНАЛНИТЕ СТРАНИЦИ ТАКА, ЧЕ ДА НЕ ДАВАТ ГРЕШКИ
@app.route('/')
@app.route('/moderation')
def moderation():
    return render('moderation', 'Moderation Settings', 'Configure moderation patterns and automation parameters.', '<div class="card"><h3>Moderation modules are running sub-routines safely.</h3></div>')

@app.route('/welcomer')
def welcomer():
    return render('welcomer', 'Welcomer Settings', 'Configure joining and leaving announcement settings.', '<div class="card"><h3>Welcomer module is active.</h3></div>')

@app.route('/counting')
def counting():
    return render('counting', 'Counting Game Configuration', 'Track and modify current counting steps.', '<div class="card"><h3>Counting logic active.</h3></div>')

@app.route('/ai_assistant')
def ai_assistant():
    return render('ai_assistant', 'AI Assistant', 'Configure AI actions and external emojis', """
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong>Auto Emoji Reactions</strong><br>
                <span style="color:#949ba4; font-size:13px;">Allow the AI to automatically place smart emojis on messages</span>
            </div>
            <div style="background:#23a55a; width:40px; height:22px; border-radius:12px; position:relative; cursor:pointer;"><div style="background:white; width:18px; height:18px; border-radius:50%; position:absolute; right:2px; top:2px;"></div></div>
        </div>
        <div style="text-align:right; margin-top:20px;"><button class="btn">Save Settings</button></div>
    </div>
    """)

@app.route('/daily')
def daily():
    return render('daily', 'Daily Modules', 'Manage continuous daily retention metrics.', '<div class="card"><h3>Daily triggers ready.</h3></div>')

@app.route('/smashkarts')
def smashkarts():
    return render('smashkarts', '🏎️ Smash Karts Statistics', 'Global race metrics compilation.', '<div class="card">No matches recorded.</div>')

@app.route('/story')
def story():
    return render('story', '📖 Story Mode Session', 'Adventure layout panel.', '<div class="card">No active story profiles.</div>')

# ══════════════════════════════════════════════════════════
#  🎯 ПРАВИЛНАТА СТРАНИЦА ЗА НИВАТА (ИНТЕГРИРАНА В СТАРИЯ СТИЛ)
# ══════════════════════════════════════════════════════════
@app.route('/leveling', methods=['GET', 'POST'])
def leveling():
    gid = get_gid()
    config_data = load('config.json')
    levels_data = load('levels.json')

    if gid not in config_data: config_data[gid] = {}
    if 'level_up_msg' not in config_data[gid]:
        config_data[gid]['level_up_msg'] = "🎉 GG {user}, you just leveled up to **Level {level}**! 🚀"

    status_msg = ""

    if request.method == 'POST':
        action = request.form.get('action')
        if action == "update_msg":
            new_msg = request.form.get('level_up_msg', '').strip()
            if new_msg:
                config_data[gid]['level_up_msg'] = new_msg
                save('config.json', config_data)
                status_msg = '<div class="alert-success">✅ Level Up Message updated successfully!</div>'
        elif action == "add_xp":
            user_id = request.form.get('user_id', '').strip()
            xp_to_add = request.form.get('xp_amount', '0').strip()
            if user_id and xp_to_add.isdigit():
                xp_amount = int(xp_to_add)
                if gid not in levels_data: levels_data[gid] = {}
                if user_id not in levels_data[gid]: levels_data[gid][user_id] = {"xp": 0, "name": f"User {user_id}"}
                levels_data[gid][user_id]["xp"] += xp_amount
                save('levels.json', levels_data)
                status_msg = f'<div class="alert-success">✅ Successfully added {xp_amount} XP points to User {user_id}!</div>'

    current_msg = config_data[gid]['level_up_msg']

    body = f"""
    {status_msg}
    <div class="card">
        <div class="card-header">
            <h3>📝 Edit Level Up Notification Layout</h3>
        </div>
        <form method="POST" action="/leveling?guild_id={gid}">
            <input type="hidden" name="action" value="update_msg">
            <div class="form-group">
                <label>Notification Custom Template String</label>
                <textarea name="level_up_msg" rows="3" required>{current_msg}</textarea>
                <p style="color:#949ba4; font-size:12px; margin-top: 8px;">
                    Click tokens below to inject them into the template layout structure:
                </p>
                <div class="badge-container">
                    <span class="badge" onclick="document.querySelector('textarea').value += ' {user}'">{{user}} - Ping User</span>
                    <span class="badge" onclick="document.querySelector('textarea').value += ' {{level}}'">{{level}} - Target Level</span>
                </div>
            </div>
            <div style="text-align:right;"><button type="submit" class="btn">Save Settings</button></div>
        </form>
    </div>

    <div class="card">
        <div class="card-header">
            <h3>🚀 Grant Leveling XP Points</h3>
        </div>
        <form method="POST" action="/leveling?guild_id={gid}">
            <input type="hidden" name="action" value="add_xp">
            <div class="form-group" style="display: flex; gap: 15px;">
                <div style="flex: 2;">
                    <label>Target User Account Snowflake ID</label>
                    <input type="text" name="user_id" placeholder="e.g. 23849201948572019" required>
                </div>
                <div style="flex: 1;">
                    <label>XP Token Amount</label>
                    <input type="number" name="xp_amount" placeholder="e.g. 500" min="1" required>
                </div>
            </div>
            <button type="submit" class="btn btn-green">Deposit XP Tokens</button>
        </form>
    </div>
    """
    return render('leveling', 'Leveling System', 'Configure AI actions and level up message templates.', body)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
