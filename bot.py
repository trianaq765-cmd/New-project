## 📜 Script 5: bot.py (Updated dengan Fitur Baru)

```python
# ============================================
# BOT.PY - DISCORD BOT (UPDATED)
# Full features + Roblox 2025 compatible
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
from typing import Optional

# ============================================
# CONFIGURATION
# ============================================

TOKEN = os.environ.get('DISCORD_TOKEN', 'YOUR_BOT_TOKEN')
API_URL = os.environ.get('API_URL', 'https://your-app.onrender.com')
PREFIX = os.environ.get('DISCORD_PREFIX', '!')
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))

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
    help_command=None  # Custom help
)

# ============================================
# UTILITIES
# ============================================

def is_on_cooldown(user_id: int) -> tuple[bool, float]:
    """Check if user is on cooldown"""
    now = datetime.now().timestamp()
    if user_id in user_cooldowns:
        diff = now - user_cooldowns[user_id]
        if diff < COOLDOWN_SECONDS:
            return True, COOLDOWN_SECONDS - diff
    user_cooldowns[user_id] = now
    return False, 0

def format_code(code: str, max_length: int = 1900) -> str:
    """Format code untuk discord"""
    if len(code) > max_length:
        return code[:max_length] + "\n... (truncated)"
    return code

def extract_code_from_message(content: str) -> str:
    """Extract code dari message (handle code blocks)"""
    # Check untuk ```lua atau ```
    code_block = re.search(r'```(?:lua)?\n?([\s\S]*?)```', content)
    if code_block:
        return code_block.group(1).strip()
    
    # Check untuk inline code `code`
    inline = re.search(r'`([^`]+)`', content)
    if inline:
        return inline.group(1).strip()
    
    return content.strip()

# ============================================
# API CALLS
# ============================================

async def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Generic API call"""
    url = f"{API_URL}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, timeout=30) as resp:
                    if resp.content_type == 'application/json':
                        return await resp.json()
                    return {"text": await resp.text()}
            else:
                async with session.post(
                    url, 
                    json=data, 
                    headers={"Content-Type": "application/json"},
                    timeout=30
                ) as resp:
                    if resp.content_type == 'application/json':
                        return await resp.json()
                    return {"text": await resp.text()}
    except asyncio.TimeoutError:
        return {"error": "Request timeout"}
    except Exception as e:
        return {"error": str(e)}

async def obfuscate_code(code: str, level: int = 2) -> dict:
    """Call obfuscate API"""
    return await call_api("/obfuscate", "POST", {"code": code, "level": level})

async def check_api_health() -> bool:
    """Check if API is healthy"""
    result = await call_api("/health")
    return result.get("status") == "healthy"

# ============================================
# EMBEDS
# ============================================

class Embeds:
    @staticmethod
    def success(result: dict, level: int) -> discord.Embed:
        """Success embed"""
        embed = discord.Embed(
            title="✅ Obfuscation Complete!",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        stats = result.get('stats', {})
        
        embed.add_field(
            name="📊 Statistics",
            value=f"```\n"
                  f"Original   : {stats.get('original', 0):,} chars\n"
                  f"Obfuscated : {stats.get('obfuscated', 0):,} chars\n"
                  f"Ratio      : {stats.get('ratio', 0)}x\n"
                  f"Level      : {level}/3\n"
                  f"```",
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
        
        embed.add_field(
            name="⏱️ Expires",
            value="24 hours",
            inline=True
        )
        
        embed.set_footer(text="Lua Obfuscator Bot v2.1")
        
        return embed
    
    @staticmethod
    def error(message: str) -> discord.Embed:
        """Error embed"""
        embed = discord.Embed(
            title="❌ Error",
            description=f"```\n{message}\n```",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Lua Obfuscator Bot")
        return embed
    
    @staticmethod
    def cooldown(remaining: float) -> discord.Embed:
        """Cooldown embed"""
        embed = discord.Embed(
            title="⏳ Cooldown",
            description=f"Please wait **{remaining:.1f}** seconds before using this command again.",
            color=0xFFAA00,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def help() -> discord.Embed:
        """Help embed"""
        embed = discord.Embed(
            title="🔒 Lua Obfuscator Bot",
            description="Obfuscate your Lua/Roblox scripts with ease!",
            color=0x5865F2
        )
        
        embed.add_field(
            name="📝 Basic Commands",
            value=f"""
`{PREFIX}obf <code>` - Obfuscate (Level 2)
`{PREFIX}obf1 <code>` - Light obfuscation
`{PREFIX}obf2 <code>` - Medium obfuscation
`{PREFIX}obf3 <code>` - Heavy obfuscation
            """,
            inline=False
        )
        
        embed.add_field(
            name="📎 File Support",
            value="Attach `.lua` or `.txt` file with command!",
            inline=False
        )
        
        embed.add_field(
            name="🎚️ Obfuscation Levels",
            value="""
**Level 1** - String encoding only
**Level 2** - + Variable obfuscation + XOR
**Level 3** - + Junk code + Anti-tamper
            """,
            inline=False
        )
        
        embed.add_field(
            name="🎮 Supported Executors",
            value="Synapse X, Script-Ware, Fluxus, KRNL, Hydrogen, Delta, Arceus X",
            inline=False
        )
        
        embed.add_field(
            name="💡 Example",
            value=f"```\n{PREFIX}obf print(\"Hello World\")\n```",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Links",
            value=f"[API]({API_URL}) • [GitHub](https://github.com)",
            inline=False
        )
        
        embed.set_footer(text="Lua Obfuscator Bot v2.1 | Roblox 2025 Compatible")
        
        return embed
    
    @staticmethod
    def info() -> discord.Embed:
        """Info/about embed"""
        embed = discord.Embed(
            title="ℹ️ About Lua Obfuscator",
            color=0x5865F2
        )
        
        embed.add_field(
            name="🔧 Features",
            value="""
• XOR Encryption (bit32 compatible)
• String byte encoding
• Variable name obfuscation
• Junk code injection
• Control flow obfuscation
• Anti-tamper protection
• Byte lookup table (0-255)
• Bytecode header validation
            """,
            inline=True
        )
        
        embed.add_field(
            name="📦 Technical",
            value="""
• `string.byte/char/sub/gsub/rep`
• `setmetatable, pcall, assert`
• `loadstring, table.unpack`
• `bit32.bxor` compatible
• Luau/Roblox 2025 ready
            """,
            inline=True
        )
        
        embed.set_footer(text="Made with ❤️ for Roblox developers")
        
        return embed
    
    @staticmethod
    def status(is_healthy: bool, latency: float) -> discord.Embed:
        """Status embed"""
        embed = discord.Embed(
            title="📡 Bot Status",
            color=0x00FF00 if is_healthy else 0xFF0000,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🤖 Bot",
            value="```\n✅ Online\n```",
            inline=True
        )
        
        embed.add_field(
            name="📡 API",
            value=f"```\n{'✅ Healthy' if is_healthy else '❌ Offline'}\n```",
            inline=True
        )
        
        embed.add_field(
            name="📶 Latency",
            value=f"```\n{latency:.0f}ms\n```",
            inline=True
        )
        
        return embed

# ============================================
# EVENTS
# ============================================

@bot.event
async def on_ready():
    print(f"{'='*50}")
    print(f"🤖 Bot: {bot.user}")
    print(f"📡 API: {API_URL}")
    print(f"🔧 Prefix: {PREFIX}")
    print(f"{'='*50}")
    
    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{PREFIX}obfhelp | Lua Obfuscator"
        )
    )
    
    # Sync slash commands
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
        await ctx.send(embed=Embeds.error(f"Missing argument: {error.param.name}"))
    else:
        await ctx.send(embed=Embeds.error(str(error)))

# ============================================
# OBFUSCATION HANDLER
# ============================================

async def handle_obfuscation(ctx, code: str, level: int):
    """Handle obfuscation request"""
    
    # Check cooldown
    on_cd, remaining = is_on_cooldown(ctx.author.id)
    if on_cd:
        await ctx.send(embed=Embeds.cooldown(remaining), delete_after=5)
        return
    
    # Check for file attachment
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith(('.lua', '.txt')):
            try:
                code = (await attachment.read()).decode('utf-8')
            except:
                await ctx.send(embed=Embeds.error("Failed to read file"))
                return
        else:
            await ctx.send(embed=Embeds.error("Only .lua and .txt files are supported"))
            return
    
    # Extract code from message
    if not code and not ctx.message.attachments:
        await ctx.send(embed=Embeds.error(f"No code provided!\n\nUsage: `{PREFIX}obf <code>`"))
        return
    
    # Clean code from command prefix
    if code:
        # Remove command dari awal
        for cmd in ['obf3', 'obf2', 'obf1', 'obf']:
            if code.lower().startswith(cmd):
                code = code[len(cmd):].strip()
                break
        
        code = extract_code_from_message(code)
    
    if not code or len(code.strip()) == 0:
        await ctx.send(embed=Embeds.error("No valid code found"))
        return
    
    # Check code size
    if len(code) > 100000:
        await ctx.send(embed=Embeds.error("Code too large! Max 100,000 characters."))
        return
    
    # Send processing message
    processing = await ctx.send("🔄 **Obfuscating your code...**")
    
    try:
        # Call API
        result = await obfuscate_code(code, level)
        
        if 'error' in result:
            await processing.edit(content=None, embed=Embeds.error(result['error']))
            return
        
        # Create embed
        embed = Embeds.success(result, level)
        
        # Create file
        obfuscated = result.get('obfuscated', '')
        file = discord.File(
            io.BytesIO(obfuscated.encode('utf-8')),
            filename=f"obfuscated_{result.get('key', 'script')}.lua"
        )
        
        # Edit message
        await processing.edit(content=None, embed=embed)
        await ctx.send(file=file)
        
    except Exception as e:
        await processing.edit(content=None, embed=Embeds.error(str(e)))

# ============================================
# TEXT COMMANDS
# ============================================

@bot.command(name='obf')
async def cmd_obf(ctx, *, code: str = ""):
    """Obfuscate with default level (2)"""
    await handle_obfuscation(ctx, code, 2)

@bot.command(name='obf1')
async def cmd_obf1(ctx, *, code: str = ""):
    """Obfuscate with level 1"""
    await handle_obfuscation(ctx, code, 1)

@bot.command(name='obf2')
async def cmd_obf2(ctx, *, code: str = ""):
    """Obfuscate with level 2"""
    await handle_obfuscation(ctx, code, 2)

@bot.command(name='obf3')
async def cmd_obf3(ctx, *, code: str = ""):
    """Obfuscate with level 3"""
    await handle_obfuscation(ctx, code, 3)

@bot.command(name='obfhelp', aliases=['help', 'h'])
async def cmd_help(ctx):
    """Show help"""
    await ctx.send(embed=Embeds.help())

@bot.command(name='obfinfo', aliases=['info', 'about'])
async def cmd_info(ctx):
    """Show info"""
    await ctx.send(embed=Embeds.info())

@bot.command(name='obfstatus', aliases=['status', 'ping'])
async def cmd_status(ctx):
    """Show status"""
    is_healthy = await check_api_health()
    latency = bot.latency * 1000
    await ctx.send(embed=Embeds.status(is_healthy, latency))

# ============================================
# SLASH COMMANDS
# ============================================

@bot.tree.command(name="obfuscate", description="Obfuscate Lua/Roblox code")
@app_commands.describe(
    code="The Lua code to obfuscate",
    level="Obfuscation level (1-3)"
)
@app_commands.choices(level=[
    app_commands.Choice(name="Level 1 - Light", value=1),
    app_commands.Choice(name="Level 2 - Medium (Recommended)", value=2),
    app_commands.Choice(name="Level 3 - Heavy", value=3),
])
async def slash_obfuscate(
    interaction: discord.Interaction, 
    code: str, 
    level: int = 2
):
    """Slash command for obfuscation"""
    
    # Check cooldown
    on_cd, remaining = is_on_cooldown(interaction.user.id)
    if on_cd:
        await interaction.response.send_message(
            embed=Embeds.cooldown(remaining), 
            ephemeral=True
        )
        return
    
    await interaction.response.defer()
    
    try:
        result = await obfuscate_code(code, level)
        
        if 'error' in result:
            await interaction.followup.send(embed=Embeds.error(result['error']))
            return
        
        embed = Embeds.success(result, level)
        
        obfuscated = result.get('obfuscated', '')
        file = discord.File(
            io.BytesIO(obfuscated.encode('utf-8')),
            filename=f"obfuscated_{result.get('key', 'script')}.lua"
        )
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(embed=Embeds.error(str(e)))

@bot.tree.command(name="obfhelp", description="Show obfuscator help")
async def slash_help(interaction: discord.Interaction):
    """Slash help"""
    await interaction.response.send_message(embed=Embeds.help())

@bot.tree.command(name="obfinfo", description="Show obfuscator info")
async def slash_info(interaction: discord.Interaction):
    """Slash info"""
    await interaction.response.send_message(embed=Embeds.info())

@bot.tree.command(name="obfstatus", description="Check bot and API status")
async def slash_status(interaction: discord.Interaction):
    """Slash status"""
    await interaction.response.defer()
    is_healthy = await check_api_health()
    latency = bot.latency * 1000
    await interaction.followup.send(embed=Embeds.status(is_healthy, latency))

# ============================================
# ADMIN COMMANDS (Optional)
# ============================================

@bot.command(name='sync')
@commands.is_owner()
async def cmd_sync(ctx):
    """Sync slash commands (owner only)"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# ============================================
# RUN BOT
# ============================================

if __name__ == '__main__':
    if TOKEN == 'YOUR_BOT_TOKEN':
        print("❌ Please set DISCORD_TOKEN environment variable!")
        exit(1)
    
    bot.run(TOKEN
