from flask import Flask, render_template_string, current_app, request, jsonify, redirect, url_for
import json
import os

app = Flask(__name__)

def load(f):
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}

def save(f, d):
    json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)

def xp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

def total_xp_for_level(level):
    return sum(xp_for_level(i) for i in range(level))

def get_level_from_xp(xp):
    level = 0
    while xp >= total_xp_for_level(level + 1):
        level += 1
        if level > 500: 
            break
    return level

def get_gid():
    bot = current_app.config.get('BOT')
    if bot and hasattr(bot, 'cached_data'):
        for key in ['moderation', 'levels', 'counting', 'smashkarts', 'story', 'welcomer']:
            d = bot.cached_data.get(key, {})
            if d:
                return list(d.keys())[0]
    return 'default_guild'

# Generic CSS & Navigation Layout wrapper
def render(active_tab, title, subtitle, body_content):
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }}
            body {{ background-color: #1e1f22; color: #dbdee1; padding: 40px; }}
            .container {{ max-width: 1100px; margin: 0 auto; display: flex; gap: 30px; }}
            .sidebar {{ width: 260px; background: #111214; padding: 20px; border-radius: 12px; height: fit-content; }}
            .sidebar h2 {{ font-size: 18px; color: #fff; margin-bottom: 20px; font-weight: 700; padding-left: 10px; }}
            .nav-link {{ display: block; padding: 12px 15px; color: #949ba4; text-decoration: none; border-radius: 8px; font-weight: 500; margin-bottom: 5px; }}
            .nav-link:hover, .nav-link.active {{ background: #2b2d31; color: #fff; }}
            .main {{ flex: 1; }}
            .header {{ margin-bottom: 30px; }}
            .header h1 {{ color: #fff; font-size: 28px; margin-bottom: 5px; }}
            .header p {{ color: #949ba4; font-size: 14px; }}
            .card {{ background: #2b2d31; border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 1px solid #3f4248; }}
            .card-header {{ margin-bottom: 20px; border-bottom: 1px solid #3f4248; padding-bottom: 15px; }}
            .card-header h3 {{ color: #fff; font-size: 18px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; color: #b5bac1; font-size: 13px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; }}
            input[type="text"], input[type="number"], textarea {{ width: 100%; padding: 12px; background: #1e1f22; border: 1px solid #111214; border-radius: 6px; color: #fff; font-size: 14px; }}
            input:focus, textarea:focus {{ border-color: #5865f2; outline: none; }}
            .btn {{ background: #5865f2; color: #fff; padding: 12px 24px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; }}
            .btn:hover {{ background: #4752c4; }}
            .badge-container {{ margin-top: 8px; display: flex; gap: 8px; }}
            .badge {{ background: #111214; padding: 4px 8px; border-radius: 4px; font-size: 12px; color: #5865f2; font-family: monospace; cursor: pointer; }}
            .alert-success {{ background: #23a55a; color: #fff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <h2>🎛️ Control Center</h2>
                <a href="/" class="nav-link {'active' if active_tab=='overview' else ''}">Overview</a>
                <a href="/leveling" class="nav-link {'active' if active_tab=='leveling' else ''}">🎭 Leveling System</a>
                <a href="/smashkarts" class="nav-link {'active' if active_tab=='smashkarts' else ''}">🏎️ Smash Karts</a>
                <a href="/story" class="nav-link {'active' if active_tab=='story' else ''}">📖 Story Session</a>
            </div>
            <div class="main">
                <div class="header">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
                {body_content}
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/')
def index():
    return render('overview', 'Dashboard Overview', 'Manage your connected Discord bot instances seamlessly.', '<div class="card"><h3>Welcome to the core management terminal.</h3></div>')

# ══════════════════════════════════════════════════════════
#  🎯 NEW: LEVELING SYSTEM MANAGEMENT PAGE (Image 3 Style)
# ══════════════════════════════════════════════════════════
@app.route('/leveling', methods=['GET', 'POST'])
def leveling():
    gid = get_gid()
    config_data = load('config.json')
    levels_data = load('levels.json')

    # Establish configuration fallbacks
    if gid not in config_data:
        config_data[gid] = {}
    if 'level_up_msg' not in config_data[gid]:
        config_data[gid]['level_up_msg'] = "🎉 GG {user}, you just leveled up to **Level {level}**! 🚀"

    status_msg = ""

    # Process Form Submissions
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 1. Update Custom Level Up Announcement string
        if action == "update_msg":
            new_msg = request.form.get('level_up_msg', '').strip()
            if new_msg:
                config_data[gid]['level_up_msg'] = new_msg
                save('config.json', config_data)
                status_msg = '<div class="alert-success">✅ Level Up Message updated successfully!</div>'
        
        # 2. Grant administrative XP bonuses to profiles
        elif action == "add_xp":
            user_id = request.form.get('user_id', '').strip()
            xp_to_add = request.form.get('xp_amount', '0').strip()
            
            if user_id and xp_to_add.isdigit():
                xp_amount = int(xp_to_add)
                if gid not in levels_data:
                    levels_data[gid] = {}
                if user_id not in levels_data[gid]:
                    levels_data[gid][user_id] = {"xp": 0, "name": f"User {user_id}"}
                
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
        <form method="POST">
            <input type="hidden" name="action" value="update_msg">
            <div class="form-group">
                <label>Notification Custom Template String</label>
                <textarea name="level_up_msg" rows="3" required>{current_msg}</textarea>
                <p style="color:#949ba4; font-size:12px; margin-top: 8px;">
                    Customize how your system announces a level up milestone. Supported inline context badges:
                </p>
                <div class="badge-container">
                    <span class="badge" onclick="document.querySelector('textarea').value += ' {user}'">{{user}} - Mentions the user</span>
                    <span class="badge" onclick="document.querySelector('textarea').value += ' {{level}}'">{{level}} - Outputs the new level rank</span>
                </div>
            </div>
            <button type="submit" class="btn">Save Configuration</button>
        </form>
    </div>

    <div class="card">
        <div class="card-header">
            <h3>🚀 Grant Leveling XP Points</h3>
        </div>
        <form method="POST">
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
            <button type="submit" class="btn" style="background:#23a55a;">Deposit XP Tokens</button>
        </form>
    </div>
    """
    return render('leveling', '🎭 Leveling Customization Engine', 'Configure dynamic reward settings, modify milestone alerts, and manage user score records.', body)

@app.route('/smashkarts')
def smashkarts():
    return render('smashkarts', '🏎️ Smash Karts Statistics', 'Global race metrics compilation.', '<div class="card">No matches recorded.</div>')

@app.route('/story')
def story():
    return render('story', '📖 Story Mode Session', 'Adventure layout panel.', '<div class="card">No active story profiles.</div>')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
