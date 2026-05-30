import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import asyncio
import os
import time
from utils import load, save, err, ok
from gemini_guard import ask_gemini, get_stats

# ── Per-user cooldown (seconds between AI responses) ──────────
USER_COOLDOWN_SECONDS = 15
_user_last_call: dict = {}  # uid -> timestamp

def _check_user_cooldown(uid: str) -> float:
    """Returns remaining seconds or 0 if the user can invoke the AI."""
    last = _user_last_call.get(uid, 0)
    elapsed = time.time() - last
    remaining = USER_COOLDOWN_SECONDS - elapsed
    return max(0.0, remaining)

class AIAssistant(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_guild_config(self, gid):
        return load('config.json').get(str(gid), {})

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Protection against bots and self-triggering
        if message.author.bot or message.author.id == self.bot.user.id or not message.guild:
            return

        gid = str(message.guild.id)
        cfg = self.get_guild_config(gid)
        
        # Guard: Check if AI module is active globally
        if not cfg.get('ai_enabled', True):
            return

        # 2. Check if the bot was mentioned or replied to
        is_mentioned = self.bot.user.mentioned_in(message)
        is_reply_to_bot = False
        
        if message.reference:
            if message.reference.cached_message:
                if message.reference.cached_message.author.id == self.bot.user.id:
                    is_reply_to_bot = True
            else:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    if ref_msg.author.id == self.bot.user.id:
                        is_reply_to_bot = True
                except:
                    pass

        should_reply = cfg.get('ai_reply_on_mention', True)

        # DEBUG PRINTS (Check your terminal console logs to see what's happening!)
        print(f"[AI Log] Message received from {message.author.name}: '{message.content}'")
        print(f"[AI Log] Is Mentioned: {is_mentioned} | Is Reply to Bot: {is_reply_to_bot} | Should Reply: {should_reply}")

        if (is_mentioned or is_reply_to_bot) and should_reply:
            uid = str(message.author.id)
            remaining = _check_user_cooldown(uid)
            
            if remaining > 0:
                print(f"[AI Log] Blocked by cooldown for user {message.author.name}")
                await message.reply(f"⏱️ Please wait {round(remaining, 1)}s before asking again!", delete_after=5)
                return
            
            _user_last_call[uid] = time.time()
            
            # Clean up the mention tags from the prompt text
            prompt = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()
            
            if not prompt and is_reply_to_bot:
                prompt = message.content.strip()

            if not prompt:
                await message.reply("👋 Hello! I am your AI Assistant. How can I help you today?")
                return

            print(f"[AI Log] Sending prompt to Gemini: '{prompt}'")
            
            async with message.channel.typing():
                try:
                    # Strict English system prompt instructions for your server environment
                    system_prompt = (
                        "You are an authentic, high-energy, and witty AI helper for an English gaming server. "
                        "Keep your answers concise, structured, friendly, and strictly under 4 sentences unless requested otherwise."
                    )
                    
                    response_text = await ask_gemini(prompt, system=system_prompt)
                    
                    if response_text:
                        await message.reply(response_text)
                    else:
                        await message.reply("❌ I'm having trouble processing that right now. Try again shortly!")
                except Exception as e:
                    print(f"[AI Assistant Error]: {e}")
                    await message.reply("⚠️ An error occurred while communicating with my AI core.")

        # 3. Auto Emoji Reactions (Only runs if message didn't trigger a direct AI reply)
        elif cfg.get('ai_auto_emojis', True):
            content_lower = message.content.lower()
            if any(x in content_lower for x in ["win", "gg", "ez", "clutch"]):
                await message.add_reaction("🏆")
            elif any(x in content_lower for x in ["hype", "fire", "crazy", "insane"]):
                await message.add_reaction("🔥")
            elif any(x in content_lower for x in ["fail", "rip", "noob", "died", "lost"]):
                await message.add_reaction("💀")

    # ── /ai_status Command ──────────────────────────────────
    @app_commands.command(name="ai_status", description="Check current AI module API analytics")
    async def ai_status(self, interaction: discord.Interaction):
        try:
            stats = get_stats()
            calls_today = stats.get("calls_today", 0)
            calls_min = stats.get("calls_this_min", 0)
            
            em = discord.Embed(title="🤖 AI System Statistics", color=discord.Color.green())
            em.add_field(name="📅 Calls Processed Today", value=f"`{calls_today} / 200`", inline=True)
            em.add_field(name="⏱️ Calls This Minute", value=f"`{calls_min} / 10`", inline=True)
            em.set_footer(text="Powered by Gemini Guard Protection Layer")
            await interaction.response.send_message(embed=em)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching analytics: {e}", ephemeral=True)

    # ── /ai_emoji Command ───────────────────────────────────
    @app_commands.command(name="ai_emoji", description="Use a custom emoji from the web dashboard")
    @app_commands.describe(name="The custom name of the emoji configured in your panel")
    async def ai_emoji(self, interaction: discord.Interaction, name: str):
        gid = str(interaction.guild.id)
        cfg = self.get_guild_config(gid)
        custom_emojis = cfg.get('custom_external_emojis', {})
        
        if name not in custom_emojis:
            return await interaction.response.send_message(
                embed=err(f"Emoji `:{name}:` not found on the web dashboard!"), ephemeral=True)
        
        await interaction.response.defer()
        url = custom_emojis[name]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    await interaction.followup.send(file=discord.File(io.BytesIO(img_data), filename=f"{name}.png"))
                else:
                    await interaction.followup.send(embed=err("Failed to retrieve the emoji source image from the panel."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
