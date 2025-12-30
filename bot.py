# ============================================
# BOT.PY - DISCORD BOT
# Lua Obfuscator - Roblox 2025 Compatible
# ============================================

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import os
import io
import re
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

TOKEN = os.environ.get('DISCORD_TOKEN', '')
API_URL = os.environ.get('API_URL', 'https://your-app.onrender.com')
PREFIX = os.environ.get('DISCORD_PREFIX', '!')

# Rate limiting
user_cooldowns = {}
COOLDOWN_SECONDS = 5

# ============================================
# BOT SETUP
# ============================================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

# ============================================
# UTILITIES
# ============================================

def is_on_cooldown(user_id):
    now = datetime.now().timestamp()
    if user_id in user_cooldowns:
        diff = now - user_cooldowns[user_id]
        if diff < COOLDOWN_SECONDS:
            return True, COOLDOWN_SECONDS - diff
    user_cooldowns[user_id] = now
    return False, 0

def extract_code(content):
    code_block = re.search(r'```(?:lua)?\n?([\s\S]*?)```', content)
    if code_block:
        return code_block.group(1).strip()
    
    inline = re.search(r'`([^`]+)`', content)
    if inline:
        return inline.group(1).strip()
    
    return content.strip()

# ============================================
# API CALLS
# ============================================

async def call_api(endpoint, method="GET", data=None):
    url = f"{API_URL}{endpoint}"
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method == "GET":
                async with session.get(url) as resp:
                    if resp.content_type == 'application/json':
                        return await resp.json()
                    return {"text": await resp.text()}
            else:
                async with session.post(url, json=data, headers={"Content-Type": "application/json"}) as resp:
                    if resp.content_type == 'application/json':
                        return await resp.json()
                    return {"text": await resp.text()}
    except asyncio.TimeoutError:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

async def obfuscate_code(code, level=2):
    return await call_api("/obfuscate", "POST", {"code": code, "level": level})

async def check_health():
    result = await call_api("/health")
    return result.get("status") == "healthy"

# ============================================
# EMBEDS
# ============================================

def embed_success(result, level):
    embed = discord.Embed(
        title="✅ Obfuscation Complete!",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    
    stats = result.get('stats', {})
    
    embed.add_field(
        name="📊 Statistics",
        value=f"```\nOriginal   : {stats.get('original', 0):,} chars\nObfuscated : {stats.get('obfuscated', 0):,} chars\nRatio      : {stats.get('ratio', 0)}x\nLevel      : {level}/3\n```",
        inline=False
    )
    
    embed.add_field(
        name="🔗 Loadstring URL",
        value=f"```\n{result.get('loadstring_url', 'N/A')}\n```",
        inline=False
    )
    
    embed.add_field(
        name="🎮 Roblox Usage",
        value=f"```lua\n{result.get('roblox_usage', 'N/A')}\n```",
        inline=False
    )
    
    embed.add_field(
        name="🔑 Key",
        value=f"`{result.get('key', 'N/A')}`",
        inline=True
    )
    
    embed.set_footer(text="Lua Obfuscator Bot v2.1")
    
    return embed

def embed_error(message):
    embed = discord.Embed(
        title="❌ Error",
        description=f"```\n{message}\n```",
        color=0xFF0000,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Lua Obfuscator Bot")
    return embed

def embed_cooldown(remaining):
    embed = discord.Embed(
        title="⏳ Cooldown",
        description=f"Please wait **{remaining:.1f}** seconds.",
        color=0xFFAA00
    )
    return embed

def embed_help():
    embed = discord.Embed(
        title="🔒 Lua Obfuscator Bot",
        description="Obfuscate your Lua/Roblox scripts!",
        color=0x5865F2
    )
    
    embed.add_field(
        name="📝 Commands",
        value=f"`{PREFIX}obf <code>` - Obfuscate (Level 2)\n`{PREFIX}obf1 <code>` - Light\n`{PREFIX}obf2 <code>` - Medium\n`{PREFIX}obf3 <code>` - Heavy\n`{PREFIX}obfhelp` - Help",
        inline=False
    )
    
    embed.add_field(
        name="📎 File Support",
        value="Attach `.lua` or `.txt` file with command!",
        inline=False
    )
    
    embed.add_field(
        name="🎚️ Levels",
        value="**1** - String encoding\n**2** - + Variable + XOR\n**3** - + Junk + Anti-tamper",
        inline=False
    )
    
    embed.add_field(
        name="💡 Example",
        value=f"```\n{PREFIX}obf print(\"Hello\")\n```",
        inline=False
    )
    
    embed.set_footer(text="Roblox 2025 Compatible")
    
    return embed

def embed_status(is_healthy, latency):
    embed = discord.Embed(
        title="📡 Bot Status",
        color=0x00FF00 if is_healthy else 0xFF0000,
        timestamp=datetime.now()
    )
    
    embed.add_field(name="🤖 Bot", value="```✅ Online```", inline=True)
    embed.add_field(name="📡 API", value=f"```{'✅ Healthy' if is_healthy else '❌ Offline'}```", inline=True)
    embed.add_field(name="📶 Latency", value=f"```{latency:.0f}ms```", inline=True)
    
    return embed

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"🤖 Bot: {bot.user}")
    print(f"📡 API: {API_URL}")
    print(f"🔧 Prefix: {PREFIX}")
    print("=" * 50)
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{PREFIX}obfhelp | Obfuscator"
        )
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embed_error(f"Missing argument: {error.param.name}"))
    else:
        await ctx.send(embed=embed_error(str(error)))

# ============================================
# OBFUSCATION HANDLER
# ============================================

async def handle_obfuscation(ctx, code, level):
    # Check cooldown
    on_cd, remaining = is_on_cooldown(ctx.author.id)
    if on_cd:
        await ctx.send(embed=embed_cooldown(remaining), delete_after=5)
        return
    
    # Check file attachment
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            try:
                code = (await attachment.read()).decode('utf-8')
            except:
                await ctx.send(embed=embed_error("Failed to read file"))
                return
        else:
            await ctx.send(embed=embed_error("Only .lua and .txt files supported"))
            return
    
    # Clean code
    if code:
        for cmd in ['obf3', 'obf2', 'obf1', 'obf']:
            if code.lower().startswith(cmd):
                code = code[len(cmd):].strip()
                break
        code = extract_code(code)
    
    if not code or len(code.strip()) == 0:
        await ctx.send(embed=embed_error(f"No code provided!\n\nUsage: {PREFIX}obf <code>"))
        return
    
    if len(code) > 100000:
        await ctx.send(embed=embed_error("Code too large! Max 100,000 characters."))
        return
    
    # Process
    processing = await ctx.send("🔄 **Obfuscating...**")
    
    try:
        result = await obfuscate_code(code, level)
        
        if 'error' in result:
            await processing.edit(content=None, embed=embed_error(result['error']))
            return
        
        embed = embed_success(result, level)
        
        obfuscated = result.get('obfuscated', '')
        file = discord.File(
            io.BytesIO(obfuscated.encode('utf-8')),
            filename=f"obfuscated_{result.get('key', 'script')}.lua"
        )
        
        await processing.edit(content=None, embed=embed)
        await ctx.send(file=file)
        
    except Exception as e:
        await processing.edit(content=None, embed=embed_error(str(e)))

# ============================================
# TEXT COMMANDS
# ============================================

@bot.command(name='obf')
async def cmd_obf(ctx, *, code: str = ""):
    await handle_obfuscation(ctx, code, 2)

@bot.command(name='obf1')
async def cmd_obf1(ctx, *, code: str = ""):
    await handle_obfuscation(ctx, code, 1)

@bot.command(name='obf2')
async def cmd_obf2(ctx, *, code: str = ""):
    await handle_obfuscation(ctx, code, 2)

@bot.command(name='obf3')
async def cmd_obf3(ctx, *, code: str = ""):
    await handle_obfuscation(ctx, code, 3)

@bot.command(name='obfhelp', aliases=['help', 'h'])
async def cmd_help(ctx):
    await ctx.send(embed=embed_help())

@bot.command(name='obfstatus', aliases=['status', 'ping'])
async def cmd_status(ctx):
    is_healthy = await check_health()
    latency = bot.latency * 1000
    await ctx.send(embed=embed_status(is_healthy, latency))

# ============================================
# SLASH COMMANDS
# ============================================

@bot.tree.command(name="obfuscate", description="Obfuscate Lua code")
@app_commands.describe(code="Lua code to obfuscate", level="Obfuscation level (1-3)")
@app_commands.choices(level=[
    app_commands.Choice(name="Level 1 - Light", value=1),
    app_commands.Choice(name="Level 2 - Medium", value=2),
    app_commands.Choice(name="Level 3 - Heavy", value=3),
])
async def slash_obfuscate(interaction: discord.Interaction, code: str, level: int = 2):
    on_cd, remaining = is_on_cooldown(interaction.user.id)
    if on_cd:
        await interaction.response.send_message(embed=embed_cooldown(remaining), ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        result = await obfuscate_code(code, level)
        
        if 'error' in result:
            await interaction.followup.send(embed=embed_error(result['error']))
            return
        
        embed = embed_success(result, level)
        obfuscated = result.get('obfuscated', '')
        file = discord.File(
            io.BytesIO(obfuscated.encode('utf-8')),
            filename=f"obfuscated_{result.get('key', 'script')}.lua"
        )
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(embed=embed_error(str(e)))

@bot.tree.command(name="obfhelp", description="Show help")
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=embed_help())

@bot.tree.command(name="obfstatus", description="Check status")
async def slash_status(interaction: discord.Interaction):
    await interaction.response.defer()
    is_healthy = await check_health()
    latency = bot.latency * 1000
    await interaction.followup.send(embed=embed_status(is_healthy, latency))

# ============================================
# RUN BOT
# ============================================

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not set!")
        print("Please set DISCORD_TOKEN environment variable")
        exit(1)
    
    print("🚀 Starting bot...")
    bot.run(TOKEN)
