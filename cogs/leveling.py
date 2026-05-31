import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import random
from utils import load, save, ok, err, info

def xp_for_level(level):
    return 5 * (level ** 2) + 50 * level + 100

def total_xp_for_level(level):
    return sum(xp_for_level(i) for i in range(level))

def get_level(xp):
    level = 0
    while xp >= total_xp_for_level(level + 1):
        level += 1
        if level > 500: 
            break
    return level

def xp_progress(xp):
    level = get_level(xp)
    cur = xp - total_xp_for_level(level)
    needed = xp_for_level(level)
    return level, cur, needed

def generate_bar(cur, total, length=12):
    filled = round((cur / total) * length) if total > 0 else 0
    return "█" * filled + "░" * (length - filled)

XP_CD = {}       
VOICE_LAST_CHECK = {} 

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_xp_ticker.start()

    def cog_unload(self):
        self.voice_xp_ticker.cancel()

    def get_guild_settings(self, gid: str):
        cfg = load('config.json')
        if gid not in cfg:
            cfg[gid] = {}
        if 'level_up_msg' not in cfg[gid]:
            cfg[gid]['level_up_msg'] = "🎉 GG {user}, you just leveled up to **Level {level}**! 🚀"
        return cfg[gid]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        uid = str(message.author.id)
        
        # Cooldown check (1 message per minute yields XP)
        now = time.time()
        if uid in XP_CD and now - XP_CD[uid] < 60:
            return
        XP_CD[uid] = now

        lvl_data = load('levels.json')
        if gid not in lvl_data:
            lvl_data[gid] = {}
        if uid not in lvl_data[gid]:
            lvl_data[gid][uid] = {"xp": 0, "name": message.author.name}

        old_xp = lvl_data[gid][uid]["xp"]
        old_level = get_level(old_xp)
        
        # Add random XP between 15 and 25
        gained_xp = random.randint(15, 25)
        new_xp = old_xp + gained_xp
        lvl_data[gid][uid]["xp"] = new_xp
        lvl_data[gid][uid]["name"] = message.author.name
        save('levels.json', lvl_data)

        new_level = get_level(new_xp)
        
        # ── ✨ PREMIUM EMBED LEVEL UP NOTIFICATION ──
        if new_level > old_level:
            settings = self.get_guild_settings(gid)
            raw_msg = settings.get('level_up_msg')
            
            # Formulating formatting placeholders
            formatted_msg = raw_msg.replace("{user}", message.author.mention).replace("{level}", str(new_level))
            
            # Creating a clean, modern Discord Embed layout (Image 1 Style)
            em = discord.Embed(
                title="⚡ LEVEL UP!",
                description=formatted_msg,
                color=discord.Color.from_rgb(88, 101, 242) # Premium Blurple Accent
            )
            em.set_thumbnail(url=message.author.display_avatar.url)
            em.set_footer(text=f"Progressing towards Level {new_level + 1} • Total XP: {new_xp}")
            
            await message.channel.send(embed=em)
            
            # Process Role Rewards if any
            lr = load('levelroles.json').get(gid, {})
            if str(new_level) in lr:
                role_id = lr[str(new_level)]
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role)
                    except:
                        pass

    @tasks.loop(minutes=1.0)
    async def voice_xp_ticker(self):
        # Background loop for handling active voice channels XP distribution
        for guild in self.bot.guilds:
            gid = str(guild.id)
            lvl_data = load('levels.json')
            if gid not in lvl_data:
                lvl_data[gid] = {}
                
            for vc in guild.voice_channels:
                if len(vc.members) < 2:
                    continue
                for member in vc.members:
                    if member.bot or member.voice.self_deaf or member.voice.deaf:
                        continue
                    uid = str(member.id)
                    if uid not in lvl_data[gid]:
                        lvl_data[gid][uid] = {"xp": 0, "name": member.name}
                    
                    old_xp = lvl_data[gid][uid]["xp"]
                    old_lvl = get_level(old_xp)
                    lvl_data[gid][uid]["xp"] += random.randint(10, 20)
                    lvl_data[gid][uid]["name"] = member.name
                    
                    if get_level(lvl_data[gid][uid]["xp"]) > old_lvl:
                        # Notify optionally or update seamlessly
                        pass
            save('levels.json', lvl_data)

    @app_commands.command(name="rank", description="Check your current level progress status")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        gid = str(interaction.guild.id)
        uid = str(member.id)
        
        lvl_data = load('levels.json').get(gid, {}).get(uid, {"xp": 0})
        xp = lvl_data["xp"]
        level, cur_xp, needed_xp = xp_progress(xp)
        progress_bar = generate_bar(cur_xp, needed_xp)
        
        em = discord.Embed(title=f"📊 Rank Statistics for {member.name}", color=discord.Color.purple())
        em.set_thumbnail(url=member.display_avatar.url)
        em.add_field(name="✨ Current Level", value=f"`Level {level}`", inline=True)
        em.add_field(name="📈 Total XP Collected", value=f"`{xp} XP`", inline=True)
        em.add_field(name="🎯 Next Level Progress", value=f"`{cur_xp} / {needed_xp} XP`\n{progress_bar}", inline=False)
        await interaction.response.send_message(embed=em)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
