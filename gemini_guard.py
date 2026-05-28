"""
Централизиран пазач за Gemini API.
Всички cogs трябва да извикват САМО него вместо директно genai.
"""
import asyncio
import time
import os
from datetime import datetime, date
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

# ── Лимити ─────────────────────────────────────────────────
MAX_CALLS_PER_DAY   = 200   # безопасен лимит (free tier = ~1500/ден)
MAX_CALLS_PER_MIN   = 10    # макс на минута
RETRY_ON_429        = True  # автоматично чакай при rate limit
MAX_RETRY_WAIT      = 60    # макс секунди чакане

# ── Вътрешно състояние ──────────────────────────────────────
_calls_today   = 0
_calls_this_min= 0
_today_date    = date.today()
_min_start     = time.time()
_lock          = asyncio.Lock()

def _reset_if_needed():
    global _calls_today, _today_date, _calls_this_min, _min_start
    today = date.today()
    if today != _today_date:
        _calls_today  = 0
        _today_date   = today
    if time.time() - _min_start > 60:
        _calls_this_min = 0
        _min_start      = time.time()

async def ask_gemini(prompt: str, system: str = None, model_name: str = "gemini-2.0-flash") -> str:
    """
    Главната функция. Изпраща заявка към Gemini с:
    - дневен лимит
    - минутен лимит  
    - автоматично чакане при 429
    - fallback при грешка
    """
    global _calls_today, _calls_this_min

    async with _lock:
        _reset_if_needed()

        # Дневен лимит
        if _calls_today >= MAX_CALLS_PER_DAY:
            raise Exception(f"🚫 Daily Gemini limit reached ({MAX_CALLS_PER_DAY} calls). Resets at midnight.")

        # Минутен лимит — изчакай
        if _calls_this_min >= MAX_CALLS_PER_MIN:
            wait_time = 60 - (time.time() - _min_start) + 1
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            _calls_this_min = 0
            _min_start = time.time()

        _calls_today    += 1
        _calls_this_min += 1

    # Извикване с retry при 429
    for attempt in range(3):
        try:
            kwargs = {"model_name": model_name}
            if system:
                kwargs["system_instruction"] = system
            model = genai.GenerativeModel(**kwargs)
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text.strip()

        except Exception as e:
            err_str = str(e)
            if "429" in err_str and RETRY_ON_429 and attempt < 2:
                # Извлечи retry_delay от грешката
                wait = 30
                if "retry_delay" in err_str:
                    try:
                        import re
                        m = re.search(r'seconds:\s*(\d+)', err_str)
                        if m: wait = min(int(m.group(1)) + 2, MAX_RETRY_WAIT)
                    except: pass
                print(f"⚠️ Gemini 429 — waiting {wait}s (attempt {attempt+1}/3)")
                await asyncio.sleep(wait)
                continue
            raise  # Re-raise ако не е 429 или изчерпахме опитите

def get_stats() -> dict:
    """Връща текущата статистика за dashboard-а."""
    _reset_if_needed()
    return {
        "calls_today":    _calls_today,
        "calls_this_min": _calls_this_min,
        "daily_limit":    MAX_CALLS_PER_DAY,
        "minute_limit":   MAX_CALLS_PER_MIN,
        "remaining_today": MAX_CALLS_PER_DAY - _calls_today,
    }
