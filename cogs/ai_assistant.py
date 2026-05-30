import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import time
import PIL.Image
from utils import load, save, err, ok
from gemini_guard import ask_gemini, get_stats

USER_COOLDOWN_SECONDS = 15
_user_last_call: dict = {}

def _check_user_cooldown(uid: str) -> float:
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
        # 1. Protection against self-activation and other bots
        if message.author.bot or message.author.id == self.bot.user.id or not message.guild:
            return

        gid = str(message.guild.id)
        cfg = self.get_guild_config(gid)
        
        if not cfg.get('ai_enabled', True):
            return

        # 2. Mentions and Replies checks
        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference:
            if message.reference.resolved and hasattr(message.reference.resolved, 'author'):
                if message.reference.resolved.author.id == self.bot.user.id:
                    is_reply_to_bot = True
            elif message.reference.cached_message:
                if message.reference.cached_message.author.id == self.bot.user.id:
                    is_reply_to_bot = True

        if is_mentioned or is_reply_to_bot:
            uid = str(message.author.id)
            remaining = _check_user_cooldown(uid)
            
            if remaining > 0:
                await message.reply(f"⏱️ Please wait {round(remaining, 1)} seconds before asking another question!", delete_after=5)
                return
            
            _user_last_call[uid] = time.time()

            # Clean the bot mention from text
            user_input = message.content.replace(f'<@{self.bot.user.id}>', '').replace(f'<@!{self.bot.user.id}>', '').strip()

            contents_to_send = []
            has_image = False

            # 📸 Check for attached images
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        try:
                            async with message.channel.typing():
                                img_bytes = await attachment.read()
                                img = PIL.Image.open(io.BytesIO(img_bytes))
                                contents_to_send.append(img)
                                has_image = True
                        except Exception as img_err:
                            print(f"[AI Error] Image failed to load: {img_err}")

            if user_input:
                contents_to_send.append(user_input)
            elif has_image:
                contents_to_send.append("Describe this image or respond to it.")
            else:
                await message.reply("👋 Hello! I am your AI Assistant. Feel free to ask me questions, send images, or use emojis! 🎨✨")
                return

            try:
                async with message.channel.typing():
                    system_prompt = (
                        "You are a helpful, friendly, and witty AI Assistant for a Discord server. "
                        "You fully support and love using emojis in your responses! Include them naturally. "
                        "Keep your answers engaging, creative, and try to keep them reasonably concise unless asked for details. "
                        "All interactions must be strictly in English."
                    )
                    
                    response_text = await ask_gemini(contents_to_send, system=system_prompt)
                    
                    if response_text:
                        # Discord character limit safety (max 2000 chars)
                        if len(response_text) > 2000:
                            chunks = [response_text[i:i+1900] for i in range(0, len(response_text), 1900)]
                            for chunk in chunks:
                                await message.reply(chunk)
                        else:
                            await message.reply(response_text)
                    else:
                        await message.reply("❌ Failed to generate a response from the AI core.")
            except Exception as e:
                print(f"[AI Assistant Error]: {e}")
                await message.reply(f"⚠️ Error handling request: {str(e)[:100]}")

    # ── Slash Command: /ai_status ──
    @app_commands.command(name="ai_status", description="Check the AI core load and daily statistics")
    async def ai_status(self, interaction: discord.Interaction):
        try:
            stats = get_stats()
            calls_today = stats.get("calls_today", 0)
            limit = stats.get("daily_limit", 200)
            pct = round((calls_today / limit) * 100) if limit > 0 else 0
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            
            em = discord.Embed(title="🤖 AI Specifications & Status", color=discord.Color.green())
            em.add_field(name="🚀 Core Model", value="`gemini-2.5-flash (Latest Global Multimodal)`", inline=False)
            em.add_field(name="📊 Requests Today", value=f"`{calls_today} / {limit}`", inline=True)
            em.add_field(name="📈 Global Server Load", value=f"`{bar}` {pct}%", inline=False)
            await interaction.response.send_message(embed=em)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error fetching stats: {e}", ephemeral=True)

    # ── Slash Command: /ai_emoji ──
    @app_commands.command(name="ai_emoji", description="Render a custom web dashboard emoji directly into chat")
    @app_commands.describe(name="The unique name of the custom emoji")
    async def ai_emoji(self, interaction: discord.Interaction, name: str):
        gid = str(interaction.guild.id)
        cfg = self.get_guild_config(gid)
        custom_emojis = cfg.get('custom_external_emojis', {})
        
        if name not in custom_emojis:
            return await interaction.response.send_message(
                embed=err(f"Emoji `:{name}:` was not found on the web dashboard!"), ephemeral=True)
        
        await interaction.response.defer()
        url = custom_emojis[name]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    await interaction.followup.send(file=discord.File(io.BytesIO(img_data), filename=f"{name}.png"))
                else:
                    await interaction.followup.send(embed=err("Failed to fetch the requested emoji asset."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
