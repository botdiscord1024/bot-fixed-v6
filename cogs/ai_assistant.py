import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import time
import PIL.Image  # Задължително за обработка на снимки
import google.generativeai as genai
from utils import load, save, err, ok
from gemini_guard import get_stats

# ── Кулдаун за потребители (15 секунди между въпросите) ──
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
        
        # Настройка на НАЙ-НОВИЯ модел (gemini-2.5-flash) с инструкции за емоджита
        system_prompt = (
            "You are a helpful, friendly, and witty AI Assistant for a Discord server. "
            "You fully support and love using emojis in your responses! Feel free to include them naturally. "
            "Keep your answers engaging, creative, and try to keep them reasonably concise unless asked for details."
        )
        
        # Директна инициализация по подобие на чистия тест код
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_prompt
        )

    def get_guild_config(self, gid):
        return load('config.json').get(str(gid), {})

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Защита от самозадействане и други ботове
        if message.author.bot or message.author.id == self.bot.user.id or not message.guild:
            return

        gid = str(message.guild.id)
        cfg = self.get_guild_config(gid)
        
        # Проверка дали AI модулът е пуснат в настройките
        if not cfg.get('ai_enabled', True):
            return

        # 2. Изчистена и сигурна проверка за споменаване (от твоя тест код)
        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference:
            if message.reference.resolved and hasattr(message.reference.resolved, 'author'):
                if message.reference.resolved.author.id == self.bot.user.id:
                    is_reply_to_bot = True
            elif message.reference.cached_message:
                if message.reference.cached_message.author.id == self.bot.user.id:
                    is_reply_to_bot = True

        # Проверяваме дали трябва да отговорим
        if is_mentioned or is_reply_to_bot:
            uid = str(message.author.id)
            remaining = _check_user_cooldown(uid)
            
            if remaining > 0:
                await message.reply(f"⏱️ Моля изчакайте {round(remaining, 1)} сек. преди следващия въпрос!", delete_after=5)
                return
            
            _user_last_call[uid] = time.time()

            # Изчистване на тага на бота от текста (запазваме емоджитата и останалия текст)
            user_input = message.content.replace(f'<@{self.bot.user.id}>', '').replace(f'<@!{self.bot.user.id}>', '').strip()

            # Списък със съдържанието, което ще пратим на Gemini (поддържа текст + снимки)
            contents_to_send = []
            has_image = False

            # 📸 ПРОВЕРКА ЗА СНИМКИ (UPLOADS)
            if message.attachments:
                for attachment in message.attachments:
                    # Проверяваме дали файлът е картинка (png, jpeg, webp и т.н.)
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        try:
                            async with message.channel.typing():
                                # Изтегляме снимката в паметта и я отваряме с Pillow
                                img_bytes = await attachment.read()
                                img = PIL.Image.open(io.BytesIO(img_bytes))
                                contents_to_send.append(img)
                                has_image = True
                        except Exception as img_err:
                            print(f"[AI Error] Грешка при зареждане на снимка: {img_err}")

            # Добавяне на текста към заявката
            if user_input:
                contents_to_send.append(user_input)
            elif has_image:
                # Ако потребителят е качил само снимка без текст, подканваме модела да я анализира
                contents_to_send.append("Describe this image or respond to it.")
            else:
                # Ако е тагнат без текст и без снимка
                await message.reply("👋 Здравей! Аз съм твоят AI асистент. Можеш да ми задаваш въпроси, да ми пращаш снимки или емоджита! 🎨✨")
                return

            # Изпращане към новия модел gemini-2.5-flash
            try:
                async with message.channel.typing():
                    # Извикваме модела директно с масива от данни (текст и/или картинка)
                    response = await self.bot.loop.run_in_executor(
                        None, lambda: self.model.generate_content(contents_to_send)
                    )
                    
                    if response.text:
                        reply_text = response.text
                        # Защита от лимита на Discord (макс 2000 символа)
                        if len(reply_text) > 2000:
                            chunks = [reply_text[i:i+1900] for i in range(0, len(reply_text), 1900)]
                            for chunk in chunks:
                                await message.reply(chunk)
                        else:
                            await message.reply(reply_text)
                    else:
                        await message.reply("❌ Неуспешно генериране на отговор от AI core.")
            except Exception as e:
                print(f"[AI Assistant Error]: {e}")
                await message.reply(f"⚠️ Грешка при обработка: {str(e)[:100]}")

    # ── Слаш Команда: /ai_status ──
    @app_commands.command(name="ai_status", description="Проверка на натоварването на изкуствения интелект")
    async def ai_status(self, interaction: discord.Interaction):
        try:
            stats = get_stats()
            calls_today = stats.get("calls_today", 0)
            
            em = discord.Embed(title="🤖 AI Спецификации & Статус", color=discord.Color.blue())
            em.add_field(name="🚀 Текущ Модел", value="`gemini-2.5-flash (Latest Multimodal)`", inline=False)
            em.add_field(name="📸 Поддръжка на медия", value="`Включена (Снимки/Изображения)`", inline=True)
            em.add_field(name="📊 Заявки за днес", value=f"`{calls_today} / 200`", inline=True)
            await interaction.response.send_message(embed=em)
        except Exception as e:
            await interaction.response.send_message(f"❌ Грешка: {e}", ephemeral=True)

    # ── Слаш Команда: /ai_emoji ──
    @app_commands.command(name="ai_emoji", description="Използвай персонализирано емоджи от уеб таблото")
    @app_commands.describe(name="Името на емоджито")
    async def ai_emoji(self, interaction: discord.Interaction, name: str):
        gid = str(interaction.guild.id)
        cfg = self.get_guild_config(gid)
        custom_emojis = cfg.get('custom_external_emojis', {})
        
        if name not in custom_emojis:
            return await interaction.response.send_message(
                embed=err(f"Емоджи `:{name}:` не е намерено в таблото!"), ephemeral=True)
        
        await interaction.response.defer()
        url = custom_emojis[name]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    await interaction.followup.send(file=discord.File(io.BytesIO(img_data), filename=f"{name}.png"))
                else:
                    await interaction.followup.send(embed=err("Неуспешно изтегляне на емоджито."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIAssistant(bot))
