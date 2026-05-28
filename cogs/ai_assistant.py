import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import asyncio
import os
import time
import urllib.parse
from utils import load, save, err, ok
from gemini_guard import ask_gemini, get_stats

# ── Per-user cooldown (секунди между AI отговори) ──────────
USER_COOLDOWN_SECONDS = 15
_user_last_call: dict = {}  # uid -> timestamp

def _check_user_cooldown(uid: str) -> float:
    """Връща оставащите секунди или 0 ако може да отговори."""
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
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        cfg = self.get_guild_config(gid)
        if not cfg.get('ai_enabled', True):
            return

        bot_mention      = f"<@{self.bot.user.id}>"
        bot_mention_nick = f"<@!{self.bot.user.id}>"
        pure_text        = message.content.replace(bot_mention, "").replace(bot_mention_nick, "").strip()

        # Игнорирай команди и единични букви (бесеница и т.н.)
        if pure_text.startswith(('!', '?', '/', '$', '.', '-', '>')):
            return
        if len(pure_text) == 1:
            return

        # Провери дали е reply към бота или mention
        is_reply_to_bot = False
        referenced_msg  = None
        if message.reference:
            try:
                referenced_msg = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
            except:
                referenced_msg = None
            if referenced_msg and referenced_msg.author.id == self.bot.user.id:
                is_reply_to_bot = True

        is_mentioning_bot = self.bot.user in message.mentions

        if not (is_reply_to_bot or is_mentioning_bot):
            return
        if not cfg.get('ai_reply_on_mention', True):
            return

        # ── User cooldown check ────────────────────────────
        uid       = str(message.author.id)
        remaining = _check_user_cooldown(uid)
        if remaining > 0:
            await message.add_reaction("⏳")
            cooldown_msg = await message.channel.send(
                f"{message.author.mention} ⏳ Please wait **{remaining:.0f}s** before asking me again!",
                delete_after=remaining
            )
            return

        _user_last_call[uid] = time.time()

        async with message.channel.typing():
            try:
                # Събери съдържание (текст + изображения)
                contents = [message.content or "Look at this image."]
                for att in message.attachments:
                    if att.content_type and att.content_type.startswith("image/"):
                        contents.append({"mime_type": att.content_type, "data": await att.read()})
                if referenced_msg:
                    for att in referenced_msg.attachments:
                        if att.content_type and att.content_type.startswith("image/"):
                            contents.append({"mime_type": att.content_type, "data": await att.read()})

                # Ако има само текст, използваме ask_gemini
                # Ако има изображения, трябва директен genai call
                if len(contents) == 1:
                    system = (
                        "You are a witty, hype, and slightly chaotic Discord assistant for an English "
                        "Smash Karts gaming community. Match the high-energy vibe. Drop casual gaming slang, "
                        "reference karts, power-ups, weapons. Keep responses concise and fun. Always reply in English."
                    )
                    reply_text = await ask_gemini(contents[0], system=system)
                else:
                    # Директен call за multimodal (изображения)
                    import google.generativeai as genai
                    model = genai.GenerativeModel(
                        model_name="gemini-2.0-flash",
                        system_instruction=(
                            "You are a witty Discord assistant for a Smash Karts gaming community. "
                            "Analyze images and keep responses concise and fun. Always reply in English."
                        )
                    )
                    response = await asyncio.to_thread(model.generate_content, contents)
                    reply_text = response.text

                await message.reply(reply_text)

            except Exception as e:
                err_str = str(e)
                if "Daily Gemini limit" in err_str:
                    await message.reply("🚫 I've hit my daily AI limit! Try again tomorrow. 😅")
                elif "429" in err_str:
                    await message.reply("⏳ Too many AI requests right now! Try again in ~30 seconds.")
                else:
                    await message.reply(f"🎰 *Engine stalled!* Something went wrong. Try again!")
                    print(f"[AI Error] {e}")

    # ── /imagine ───────────────────────────────────────────
    @app_commands.command(name="imagine", description="Generate a unique image using AI!")
    @app_commands.describe(prompt="Describe what you want the AI to draw")
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&model=flux"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Image provider error ({resp.status})")
                    image_bytes = await resp.read()
            img_file = discord.File(io.BytesIO(image_bytes), filename="ai_artwork.png")
            await interaction.followup.send(
                content=f"🎨 **Look what I created for you!**\n`Prompt:` *{prompt}*",
                file=img_file
            )
        except Exception as e:
            await interaction.followup.send(embed=err(f"Error drawing image: `{e}`"), ephemeral=True)

    # ── /ai_stats ──────────────────────────────────────────
    @app_commands.command(name="ai_stats", description="Show Gemini API usage stats (Admin)")
    @app_commands.default_permissions(administrator=True)
    async def ai_stats(self, interaction: discord.Interaction):
        stats = get_stats()
        em = discord.Embed(title="🤖 Gemini API Stats", color=discord.Color.blue())
        em.add_field(name="📊 Today's Calls",    value=f"{stats['calls_today']} / {stats['daily_limit']}")
        em.add_field(name="⚡ This Minute",       value=f"{stats['calls_this_min']} / {stats['minute_limit']}")
        em.add_field(name="✅ Remaining Today",   value=str(stats['remaining_today']))
        pct = round(stats['calls_today'] / stats['daily_limit'] * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        em.add_field(name="📈 Usage", value=f"`{bar}` {pct}%", inline=False)
        await interaction.response.send_message(embed=em)

    # ── /ai_emoji ──────────────────────────────────────────
    @app_commands.command(name="ai_emoji", description="Use a custom emoji from the web dashboard")
    @app_commands.describe(name="The custom name of the emoji")
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
                    await interaction.followup.send(embed=err("Failed to download the emoji asset."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
