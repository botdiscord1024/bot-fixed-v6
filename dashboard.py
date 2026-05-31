from flask import Flask, render_template_string, current_app, request, jsonify, redirect, url_for
import json
import os
import asyncio

app = Flask(__name__)

def load(f):
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}

def save(f, d):
    json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)

def get_gid():
    bot = current_app.config.get('BOT')
    if bot and hasattr(bot, 'cached_data'):
        for key in ['moderation', 'levels', 'counting', 'smashkarts', 'story', 'welcomer']:
            d = bot.cached_data.get(key, {})
            if d:
                return list(d.keys())[0]
    cfg = load('config.json')
    if cfg:
        real_ids = [k for k in cfg.keys() if k != 'default_guild']
        if real_ids:
            return real_ids[0]
    return 'default'

# 🟢 API ENDPOINT ЗА ТЕСТОВИТЕ БУТОНИ
@app.route('/api/test-message', methods=['POST'])
def api_test_message():
    data = request.json
    module = data.get('module', 'Unknown Module')
    channel_id = data.get('channel_id')
    
    if not channel_id or not channel_id.isdigit():
        return jsonify({'error': 'Invalid or empty Channel ID'}), 400
        
    bot = current_app.config.get('BOT')
    if bot:
        async def send_test():
            try:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(f"🧪 **Dashboard Test:** Успешна връзка с канал за модул `{module}`!")
                else:
                    print(f"Test fail: Channel {channel_id} not found by bot.")
            except Exception as e:
                print(f"Failed to send test message: {e}")
                
        if hasattr(bot, 'loop'):
            asyncio.run_coroutine_threadsafe(send_test(), bot.loop)
            return jsonify({'ok': True})
            
    return jsonify({'error': 'Bot is not connected to dashboard'}), 500

# 🎨 ГЛАВЕН РЕНДЕР С ДИЗАЙН И JAVASCRIPT ЗА ТЕСТОВЕТЕ
def render(active_tab, title, subtitle, body_content):
    gid = get_gid() or 'default'
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }}
            body {{ background-color: #1e1f22; color: #dbdee1; display: flex; min-height: 100vh; width: 100%; }}
            .sidebar {{ width: 260px; background: #111214; padding: 24px 16px; display: flex; flex-direction: column; border-right: 1px solid #1c1d20; flex-shrink: 0; }}
            .sidebar h2 {{ font-size: 19px; color: #fff; margin-bottom: 25px; font-weight: 700; padding-left: 10px; }}
            .sidebar-divider {{ height: 1px; background: #2b2d31; margin-bottom: 20px; width: 100%; }}
            .nav-link {{ display: flex; align-items: center; padding: 12px 15px; color: #949ba4; text-decoration: none; border-radius: 8px; font-weight: 500; margin-bottom: 6px; font-size: 14px; transition: 0.15s; }}
            .nav-link:hover {{ background: #2b2d31; color: #fff; }}
            .nav-link.active {{ background: #7c00ff; color: #fff; font-weight: 600; }}
            .main-content {{ flex: 1; padding: 40px; overflow-y: auto; }}
            .header {{ margin-bottom: 35px; }}
            .header h1 {{ color: #fff; font-size: 28px; font-weight: 700; margin-bottom: 6px; }}
            .header p {{ color: #949ba4; font-size: 14px; }}
            
            .card {{ background: #2b2d31; border-radius: 8px; padding: 25px; margin-bottom: 25px; border: 1px solid #202225; }}
            .card-header {{ margin-bottom: 20px; border-bottom: 1px solid #3f4248; padding-bottom: 15px; }}
            .card-header h3 {{ color: #fff; font-size: 18px; font-weight: 600; }}
            
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; color: #b5bac1; font-size: 12px; font-weight: 700; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
            
            .input-group {{ display: flex; gap: 10px; }}
            input[type="text"], input[type="number"], textarea {{ width: 100%; padding: 12px; background: #1e1f22; border: 1px solid #111214; border-radius: 6px; color: #fff; font-size: 14px; }}
            input:focus, textarea:focus {{ border-color: #7c00ff; outline: none; }}
            
            .btn {{ background: #7c00ff; color: #fff; padding: 12px 24px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; transition: 0.2s; }}
            .btn:hover {{ background: #6600d1; }}
            .btn-green {{ background: #00e676; color: #000; }}
            .btn-green:hover {{ background: #00c853; color: #fff; }}
            .btn-test {{ background: #4e5058; padding: 12px 20px; white-space: nowrap; }}
            .btn-test:hover {{ background: #6d6f78; }}
            
            .badge-container {{ margin-top: 10px; display: flex; gap: 8px; }}
            .badge {{ background: #111214; padding: 6px 10px; border-radius: 4px; font-size: 12px; color: #00e676; font-family: monospace; cursor: pointer; }}
            .alert-success {{ background: #23a55a; color: #fff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>👑 Admin Panel</h2>
            <div class="sidebar-divider"></div>
            <a href="/moderation" class="nav-link {'active' if active_tab=='moderation' else ''}">🛡️ Moderation</a>
            <a href="/welcomer" class="nav-link {'active' if active_tab=='welcomer' else ''}">👋 Welcomer</a>
            <a href="/leveling" class="nav-link {'active' if active_tab=='leveling' else ''}">⭐ Leveling System</a>
            <a href="/counting" class="nav-link {'active' if active_tab=='counting' else ''}">🔢 Counting Game</a>
            <a href="/daily" class="nav-link {'active' if active_tab=='daily' else ''}">📅 Daily Modules</a>
            <a href="/smashkarts" class="nav-link {'active' if active_tab=='smashkarts' else ''}">🏎️ Smash Karts</a>
            <a href="/story" class="nav-link {'active' if active_tab=='story' else ''}">📖 Story Mode</a>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {body_content}
        </div>
        
        <script>
        function sendTestMessage(moduleName, inputId) {{
            const channelId = document.getElementById(inputId).value.trim();
            if (!channelId) {{
                alert('Please enter a valid Channel ID first!');
                return;
            }}
            fetch('/api/test-message', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ module: moduleName, channel_id: channelId }})
            }}).then(res => res.json()).then(data => {{
                if (data.error) alert('Error: ' + data.error);
                else alert('✅ Test message sent to the channel!');
            }}).catch(err => alert('Failed to send test request. Is bot running?'));
        }}
        </script>
    </body>
    </html>
    """)

@app.route('/')
@app.route('/moderation')
def moderation():
    return render('moderation', 'Moderation Settings', 'Configure moderation patterns.', '<div class="card"><h3>Active</h3></div>')

# ══════════════════════════════════════════════════════════
#  WELCOMER (С ТЕСТОВИ БУТОНИ)
# ══════════════════════════════════════════════════════════
@app.route('/welcomer')
def welcomer():
    gid = get_gid() or 'default'
    w_data = load('config.json').get(gid, {}).get('welcomer', {})
    chan = w_data.get('welcome_channel', '')
    l_chan = w_data.get('leave_channel', '')
    
    body = f"""
    <div class="card">
        <div class="card-header"><h3>Join Notification Configuration</h3></div>
        <div class="form-group">
            <label>Welcome Channel ID</label>
            <div class="input-group">
                <input type="text" id="w_channel" value="{chan}" readonly>
                <button type="button" class="btn btn-test" onclick="sendTestMessage('Welcomer Join', 'w_channel')">Test Channel</button>
            </div>
        </div>
        <div class="form-group" style="margin-top:20px;">
            <label>Leave Channel ID</label>
            <div class="input-group">
                <input type="text" id="l_channel" value="{l_chan}" readonly>
                <button type="button" class="btn btn-test" onclick="sendTestMessage('Welcomer Leave', 'l_channel')">Test Channel</button>
            </div>
        </div>
    </div>
    """
    return render('welcomer', 'Welcomer Settings', 'Configure joining and leaving announcement settings', body)

# ══════════════════════════════════════════════════════════
#  ⭐ LEVELING (ПЪЛНА ФУНКЦИОНАЛНОСТ + ТЕСТ)
# ══════════════════════════════════════════════════════════
@app.route('/leveling', methods=['GET', 'POST'])
def leveling():
    gid = get_gid() or 'default'
    config_data = load('config.json')
    levels_data = load('levels.json')

    if gid not in config_data: config_data[gid] = {}
    if 'leveling' not in config_data[gid]: config_data[gid]['leveling'] = {}
    
    cfg = config_data[gid]['leveling']
    if 'level_up_msg' not in cfg:
        cfg['level_up_msg'] = "🎉 GG {user}, you just leveled up to **Level {level}**! 🚀"

    status_msg = ""

    if request.method == 'POST':
        action = request.form.get('action')
        if action == "update_settings":
            cfg['level_up_msg'] = request.form.get('level_up_msg', '').strip()
            cfg['level_channel'] = request.form.get('level_channel', '').strip()
            save('config.json', config_data)
            status_msg = '<div class="alert-success">✅ Leveling Settings updated successfully!</div>'
        elif action == "add_xp":
            user_id = request.form.get('user_id', '').strip()
            xp_amount = int(request.form.get('xp_amount', '0'))
            if user_id and xp_amount > 0:
                if gid not in levels_data: levels_data[gid] = {}
                if user_id not in levels_data[gid]: levels_data[gid][user_id] = {"xp": 0, "name": f"User {user_id}"}
                levels_data[gid][user_id]["xp"] += xp_amount
                save('levels.json', levels_data)
                status_msg = f'<div class="alert-success">✅ Successfully added {xp_amount} XP points to User {user_id}!</div>'

    current_msg = cfg.get('level_up_msg', '')
    current_chan = cfg.get('level_channel', '')

    body = f"""
    {status_msg}
    <div class="card">
        <div class="card-header">
            <h3>📝 Edit Level Up Notification Layout & Channel</h3>
        </div>
        <form method="POST" action="/leveling">
            <input type="hidden" name="action" value="update_settings">
            
            <div class="form-group">
                <label>Target Channel ID (Leave empty for current channel)</label>
                <div class="input-group">
                    <input type="text" id="lvl_channel" name="level_channel" value="{current_chan}" placeholder="e.g. 123456789012345678">
                    <button type="button" class="btn btn-test" onclick="sendTestMessage('Level Up System', 'lvl_channel')">Test Channel</button>
                </div>
            </div>

            <div class="form-group" style="margin-top: 20px;">
                <label>Notification Custom Template String</label>
                <textarea name="level_up_msg" rows="3" required>{current_msg}</textarea>
                <div class="badge-container">
                    <span class="badge" onclick="document.querySelector('textarea').value += ' {{user}}'">{{user}} - Ping User</span>
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
        <form method="POST" action="/leveling">
            <input type="hidden" name="action" value="add_xp">
            <div class="form-group input-group">
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
    return render('leveling', 'Leveling System', 'Configure XP actions and level up message templates.', body)

# ══════════════════════════════════════════════════════════
#  DAILY MODULES (С ТЕСТОВИ БУТОНИ)
# ══════════════════════════════════════════════════════════
@app.route('/daily')
def daily():
    gid = get_gid() or 'default'
    cfg = load('config.json').get(gid, {})
    
    f_chan = cfg.get('fotd_settings', {}).get('channel_id', '')
    q_chan = cfg.get('qotd_settings', {}).get('channel_id', '')
    r_chan = cfg.get('rotd_settings', {}).get('channel_id', '')
    s_chan = cfg.get('sotd_settings', {}).get('channel_id', '')

    body = f"""
    <div class="card">
        <div class="card-header"><h3>📅 Daily Modules Channel Config</h3></div>
        
        <div class="form-group"><label>FOTD (Fact of the Day) Channel</label>
            <div class="input-group"><input type="text" id="fc" value="{f_chan}" readonly>
            <button type="button" class="btn btn-test" onclick="sendTestMessage('FOTD', 'fc')">Test</button></div>
        </div>
        <div class="form-group"><label>QOTD (Question of the Day) Channel</label>
            <div class="input-group"><input type="text" id="qc" value="{q_chan}" readonly>
            <button type="button" class="btn btn-test" onclick="sendTestMessage('QOTD', 'qc')">Test</button></div>
        </div>
        <div class="form-group"><label>ROTD (Riddle of the Day) Channel</label>
            <div class="input-group"><input type="text" id="rc" value="{r_chan}" readonly>
            <button type="button" class="btn btn-test" onclick="sendTestMessage('ROTD', 'rc')">Test</button></div>
        </div>
        <div class="form-group"><label>SOTD (Song of the Day) Channel</label>
            <div class="input-group"><input type="text" id="sc" value="{s_chan}" readonly>
            <button type="button" class="btn btn-test" onclick="sendTestMessage('SOTD', 'sc')">Test</button></div>
        </div>
    </div>
    """
    return render('daily', 'Daily Modules', 'Manage continuous daily retention metrics', body)

@app.route('/counting')
def counting(): return render('counting', 'Counting Game', 'Track math progress', '<div class="card"><h3>Active</h3></div>')
@app.route('/smashkarts')
def smashkarts(): return render('smashkarts', 'Smash Karts', 'Global metrics', '<div class="card"><h3>Active</h3></div>')
@app.route('/story')
def story(): return render('story', 'Story Mode', 'Adventure configurations', '<div class="card"><h3>Active</h3></div>')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
