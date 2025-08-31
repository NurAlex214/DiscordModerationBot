import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Union
import re
import aiohttp
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Create logger for bot actions
bot_logger = logging.getLogger('bot_actions')
bot_logger.setLevel(logging.INFO)

# Create logger for security events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

# Create logger for errors
error_logger = logging.getLogger('errors')
error_logger.setLevel(logging.ERROR)

# Bot configuration
class BotConfig:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.token = config.get('token', '')
                self.prefix = config.get('prefix', '!')
                self.owner_ids = config.get('owner_ids', [])
                self.log_channel = config.get('log_channel', None)
        except FileNotFoundError:
            self.create_default_config()
    
    def create_default_config(self):
        default_config = {
            "token": "YOUR_BOT_TOKEN_HERE",
            "prefix": "!",
            "owner_ids": [],
            "log_channel": None
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        print("Created config.json - Please add your bot token and configure settings!")

config = BotConfig()

# Bot setup with all necessary intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.moderation = True

class ModerationBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config.prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.config = config
        self.db = None
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        await self.setup_database()
        await self.load_extensions()
        
    async def setup_database(self):
        """Initialize the database"""
        self.db = sqlite3.connect('moderation.db')
        cursor = self.db.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mutes (
                user_id INTEGER,
                guild_id INTEGER,
                end_time DATETIME,
                reason TEXT,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                log_channel INTEGER,
                mute_role INTEGER,
                automod_enabled BOOLEAN DEFAULT 0,
                max_warnings INTEGER DEFAULT 3,
                warning_action TEXT DEFAULT 'timeout'
            )
        ''')
        
        # Economy system tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_economy (
                user_id INTEGER,
                guild_id INTEGER,
                balance INTEGER DEFAULT 0,
                bank_balance INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_daily DATETIME,
                last_work DATETIME,
                last_rob DATETIME,
                total_earned INTEGER DEFAULT 0,
                times_robbed INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                guild_id INTEGER,
                item_name TEXT,
                item_price INTEGER,
                item_description TEXT,
                item_emoji TEXT,
                PRIMARY KEY (guild_id, item_name)
            )
        ''')
        
        self.db.commit()
        
    async def load_extensions(self):
        """Load all cog extensions"""
        cogs_to_load = [
            'cogs.moderation',
            'cogs.admin',
            'cogs.utility',
            'cogs.automod',
            'cogs.settings',
            'cogs.fun',
            'cogs.economy',
            'cogs.social',
            'cogs.images',
            'cogs.server_management',
            'cogs.music'
        ]
        
        loaded = 0
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                loaded += 1
                print(f"✅ Loaded {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        print(f"Successfully loaded {loaded}/{len(cogs_to_load)} extensions!")

    async def on_ready(self):
        """Called when the bot is ready"""
        bot_logger.info(f'{self.user} has connected to Discord!')
        bot_logger.info(f'Bot is in {len(self.guilds)} guilds')
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        
        # Log guild information
        for guild in self.guilds:
            bot_logger.info(f'Connected to guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            bot_logger.info(f'Successfully synced {len(synced)} slash command(s)')
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            bot_logger.error(f'Failed to sync commands: {e}')
            print(f'Failed to sync commands: {e}')
            
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for rule violations"
            )
        )
        bot_logger.info('Bot status set to "Watching for rule violations"')
    
    async def on_command(self, ctx):
        """Log when a prefix command is used"""
        bot_logger.info(f'Prefix command used: {ctx.command.name} by {ctx.author} ({ctx.author.id}) in {ctx.guild.name if ctx.guild else "DM"}')
    
    async def on_app_command_completion(self, interaction: discord.Interaction, command: Union[app_commands.Command, app_commands.ContextMenu]):
        """Log when a slash command is completed"""
        guild_info = f"{interaction.guild.name} ({interaction.guild.id})" if interaction.guild else "DM"
        bot_logger.info(f'Slash command completed: /{command.name} by {interaction.user} ({interaction.user.id}) in {guild_info}')
    
    async def on_member_join(self, member):
        """Log when a member joins"""
        bot_logger.info(f'Member joined: {member} ({member.id}) in {member.guild.name} ({member.guild.id})')
    
    async def on_member_remove(self, member):
        """Log when a member leaves"""
        bot_logger.info(f'Member left: {member} ({member.id}) from {member.guild.name} ({member.guild.id})')
    
    async def on_guild_join(self, guild):
        """Log when bot joins a guild"""
        bot_logger.info(f'Bot joined new guild: {guild.name} ({guild.id}) with {guild.member_count} members')
    
    async def on_guild_remove(self, guild):
        """Log when bot leaves a guild"""
        bot_logger.info(f'Bot removed from guild: {guild.name} ({guild.id})')
    
    async def on_message(self, message):
        """Log automod actions and process commands"""
        # Don't log bot messages to avoid spam
        if message.author.bot:
            return
            
        # Log messages in a simplified format (avoid logging every message for privacy)
        if message.guild:
            # Only log if message triggers automod or contains certain keywords
            content_lower = message.content.lower()
            if any(word in content_lower for word in ['spam', 'raid', 'discord.gg/', 'http']):
                bot_logger.info(f'Potentially flagged message by {message.author} ({message.author.id}) in #{message.channel.name}: "{message.content[:50]}..."')
        
        await self.process_commands(message)
    
    async def on_error(self, event, *args, **kwargs):
        """Handle all unhandled exceptions"""
        import traceback
        error_logger.critical(f'UNHANDLED EXCEPTION in event {event}: {traceback.format_exc()}')
    
    async def on_command_error(self, ctx, error):
        """Handle prefix command errors"""
        command_name = ctx.command.name if ctx.command else 'unknown'
        guild_info = f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM"
        user_info = f"{ctx.author} ({ctx.author.id})"
        
        if isinstance(error, commands.MissingPermissions):
            security_logger.warning(f'PERMISSION DENIED (PREFIX): {user_info} attempted {ctx.prefix}{command_name} in {guild_info} without required permissions: {error.missing_permissions}')
        elif isinstance(error, commands.CommandOnCooldown):
            bot_logger.info(f'COOLDOWN (PREFIX): {user_info} attempted {ctx.prefix}{command_name} in {guild_info} but command is on cooldown ({error.retry_after:.1f}s remaining)')
        else:
            error_logger.error(f'PREFIX COMMAND ERROR: {ctx.prefix}{command_name} by {user_info} in {guild_info} - {type(error).__name__}: {error}')

bot = ModerationBot()

# Help command with pagination
class HelpView(discord.ui.View):
    """Paginated help command view"""
    
    def __init__(self, user: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.user = user
        self.current_page = 0
        self.pages = self.create_pages()
        self.max_pages = len(self.pages)
        self.update_buttons()
    
    def create_pages(self) -> list:
        """Create all help pages"""
        pages = []
        
        # Main overview page
        overview = discord.Embed(
            title="🤖 Discord Moderation Bot",
            description="A comprehensive Discord moderation bot with 100+ commands!",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        overview.add_field(
            name="📊 Command Categories",
            value="🔨 Moderation (13 commands)\n⚙️ Administration (12 commands)\n🔍 Utility (10 commands)\n🎉 Fun & Games (15 commands)\n💰 Economy (12 commands)\n💕 Social (12 commands)\n🖼️ Images & Memes (11 commands)\n🏠 Server Management (8 commands)\n🎵 Music & Entertainment (8 commands)\n⚙️ Settings (4 commands)",
            inline=False
        )
        overview.add_field(
            name="🚀 Getting Started",
            value="• Use `/settings` to configure the bot\n• Set a log channel with `/setlogchannel`\n• Enable automod with `/toggleautomod true`\n• Use the buttons below to browse commands!",
            inline=False
        )
        overview.set_footer(text="Use the buttons below to navigate through command categories")
        pages.append(overview)
        
        # Moderation page
        moderation = discord.Embed(
            title="🔨 Moderation Commands",
            description="Commands for moderating your server and managing users",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        moderation.add_field(
            name="👤 User Management",
            value="• `/ban` - Ban a user from the server\n• `/kick` - Kick a user from the server\n• `/timeout` - Timeout a user\n• `/untimeout` - Remove timeout from user\n• `/unban` - Unban a user",
            inline=False
        )
        moderation.add_field(
            name="⚠️ Warning System",
            value="• `/warn` - Warn a user\n• `/warnings` - View user warnings\n• `/clearwarnings` - Clear user warnings",
            inline=False
        )
        moderation.add_field(
            name="🔐 Advanced Moderation",
            value="• `/softban` - Softban a user (ban + unban)\n• `/massban` - Ban multiple users\n• `/lockdown` - Lock down channels\n• `/mute` - Mute a user\n• `/unmute` - Unmute a user",
            inline=False
        )
        pages.append(moderation)
        
        # Economy page
        economy = discord.Embed(
            title="💰 Economy Commands",
            description="Virtual economy system with money, work, and gambling",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        economy.add_field(
            name="💵 Basic Economy",
            value="• `/balance` - Check your balance\n• `/daily` - Claim daily reward\n• `/work` - Work to earn money\n• `/pay` - Pay another user",
            inline=False
        )
        economy.add_field(
            name="🏦 Banking",
            value="• `/deposit` - Deposit money to bank\n• `/withdraw` - Withdraw from bank\n• `/rob` - Attempt to rob someone",
            inline=False
        )
        economy.add_field(
            name="🎰 Games & Rankings",
            value="• `/gamble` - Gamble your money\n• `/baltop` - View richest users\n• `/addmoney` - Admin: Add money\n• `/removemoney` - Admin: Remove money\n• `/reseteconomy` - Admin: Reset economy",
            inline=False
        )
        pages.append(economy)
        
        # Social page
        social = discord.Embed(
            title="💕 Social Interaction Commands",
            description="Fun social commands to interact with other users",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        social.add_field(
            name="💖 Affection",
            value="• `/hug` - Give someone a hug\n• `/kiss` - Give someone a kiss\n• `/cuddle` - Cuddle with someone\n• `/pat` - Pat someone's head",
            inline=False
        )
        social.add_field(
            name="😄 Playful",
            value="• `/poke` - Poke someone\n• `/tickle` - Tickle someone\n• `/slap` - Playfully slap someone\n• `/bite` - Playfully bite someone\n• `/punch` - Playfully punch someone\n• `/highfive` - Give a high five",
            inline=False
        )
        social.add_field(
            name="💝 Special",
            value="• `/marry` - Propose marriage\n• `/ship` - Check compatibility\n• `/compliment` - Give a compliment\n• `/insult` - Playful roast\n• `/8ball` - Love magic 8-ball",
            inline=False
        )
        pages.append(social)
        
        # Images & Memes page
        images = discord.Embed(
            title="🖼️ Images & Memes Commands",
            description="Image generation, memes, and visual content",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        images.add_field(
            name="🖼️ Images",
            value="• `/avatar` - Display user avatar\n• `/servericon` - Show server icon\n• `/cat` - Random cat image\n• `/dog` - Random dog image\n• `/fox` - Random fox image\n• `/duck` - Random duck image",
            inline=False
        )
        images.add_field(
            name="🎨 Generation",
            value="• `/qr` - Generate QR code\n• `/color` - Color information\n• `/ascii` - Convert text to ASCII art\n• `/emoji` - Emoji information",
            inline=False
        )
        images.add_field(
            name="😂 Fun Content",
            value="• `/meme` - Random meme from Reddit\n• `/joke` - Random clean joke\n• `/fact` - Random fun fact\n• `/quote` - Inspirational quote\n• `/pickup` - Cheesy pickup line",
            inline=False
        )
        pages.append(images)
        
        # Games & Entertainment page
        games = discord.Embed(
            title="🎵 Music & Entertainment Commands",
            description="Interactive games and entertainment features",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        games.add_field(
            name="🧠 Brain Games",
            value="• `/trivia` - Trivia game with difficulty levels\n• `/riddle` - Solve riddles with hints\n• `/hangman` - Classic hangman game",
            inline=False
        )
        games.add_field(
            name="🎯 Party Games",
            value="• `/truth` - Truth questions\n• `/dare` - Dare challenges\n• `/wouldyourather` - Would you rather questions\n• `/wordchain` - Word chain game",
            inline=False
        )
        games.add_field(
            name="🎲 Random Fun",
            value="• `/spinner` - Custom wheel spinner\n• `/bingo` - Generate bingo card\n• `/motivation` - Motivational quotes\n• `/lyrics` - Song lyrics (coming soon)",
            inline=False
        )
        pages.append(games)
        
        # Server Management page
        server = discord.Embed(
            title="🏠 Server Management Commands",
            description="Advanced server administration and management",
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        server.add_field(
            name="📺 Channel Management",
            value="• `/createchannel` - Create new channels\n• `/deletechannel` - Delete channels\n• `/channelinfo` - Channel information",
            inline=False
        )
        server.add_field(
            name="👥 Role Management",
            value="• `/createrole` - Create new roles\n• `/deleterole` - Delete roles\n• `/roleinfo` - Role information",
            inline=False
        )
        server.add_field(
            name="🔧 Server Tools",
            value="• `/cleanup` - Clean bot messages\n• `/viewemojis` - View server emojis\n• `/inviteinfo` - Invite information\n• `/createinvite` - Create invites\n• `/backup` - Backup server settings\n• `/membercount` - Member statistics",
            inline=False
        )
        pages.append(server)
        
        return pages
    
    def update_buttons(self):
        """Update button states"""
        self.first.disabled = self.current_page == 0
        self.previous.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= self.max_pages - 1
        self.last.disabled = self.current_page >= self.max_pages - 1
    
    def get_current_embed(self) -> discord.Embed:
        """Get the current page embed"""
        embed = self.pages[self.current_page]
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{self.max_pages} • Total Commands: 100+ • Requested by {self.user.display_name}",
            icon_url=self.user.display_avatar.url
        )
        return embed
    
    @discord.ui.button(label='⏪', style=discord.ButtonStyle.secondary)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This help menu isn't for you!", ephemeral=True)
            return
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
    
    @discord.ui.button(label='◀️', style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This help menu isn't for you!", ephemeral=True)
            return
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
    
    @discord.ui.button(label='▶️', style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This help menu isn't for you!", ephemeral=True)
            return
        self.current_page = min(self.max_pages - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
    
    @discord.ui.button(label='⏩', style=discord.ButtonStyle.secondary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This help menu isn't for you!", ephemeral=True)
            return
        self.current_page = self.max_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
    
    @discord.ui.button(label='❌ Close', style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This help menu isn't for you!", ephemeral=True)
            return
        await interaction.response.edit_message(content="Help menu closed.", embed=None, view=None)

@bot.tree.command(name="help", description="Get help and information about bot commands")
async def help_command(interaction: discord.Interaction):
    """Comprehensive help command with categorized commands and pagination"""
    view = HelpView(interaction.user)
    embed = view.get_current_embed()
    await interaction.response.send_message(embed=embed, view=view)

# Global error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for slash commands"""
    try:
        # Get command info for logging
        command_name = getattr(interaction.command, 'name', 'unknown') if interaction.command else 'unknown'
        guild_info = f"{interaction.guild.name} ({interaction.guild.id})" if interaction.guild else "DM"
        user_info = f"{interaction.user} ({interaction.user.id})"
        
        if isinstance(error, app_commands.MissingPermissions):
            # Log security violation
            security_logger.warning(f'PERMISSION DENIED: {user_info} attempted to use /{command_name} in {guild_info} without required permissions: {error.missing_permissions}')
            
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have the required permissions to use this command.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Required Permissions", value=", ".join(error.missing_permissions), inline=False)
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        elif isinstance(error, app_commands.CommandOnCooldown):
            # Log cooldown attempt
            bot_logger.info(f'COOLDOWN: {user_info} attempted /{command_name} in {guild_info} but command is on cooldown ({error.retry_after:.1f}s remaining)')
            
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.2f} seconds before using this command again.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        elif isinstance(error, app_commands.BotMissingPermissions):
            # Log when bot lacks permissions
            error_logger.error(f'BOT MISSING PERMISSIONS: /{command_name} failed in {guild_info} - Bot missing: {error.missing_permissions}')
            
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have the required permissions to execute this command.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Required Permissions", value=", ".join(error.missing_permissions), inline=False)
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        else:
            # Don't respond to discord.NotFound errors (expired interactions)
            if isinstance(error.original if hasattr(error, 'original') else error, discord.NotFound):
                error_logger.warning(f"EXPIRED INTERACTION: /{command_name} by {user_info} in {guild_info} - {error}")
                return
            
            # Log all other errors
            error_logger.error(f'COMMAND ERROR: /{command_name} by {user_info} in {guild_info} - {type(error).__name__}: {error}')
            
            embed = discord.Embed(
                title="❌ An Error Occurred",
                description="An unexpected error occurred while processing your command.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            # Add error details for administrators
            if interaction.user.guild_permissions.administrator if interaction.guild else False:
                embed.add_field(name="Error Details", value=f"`{type(error).__name__}: {str(error)[:500]}`", inline=False)
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            
    except discord.NotFound:
        # Interaction has expired, ignore silently but log it
        error_logger.warning(f"INTERACTION EXPIRED: Error handler failed for /{command_name} by {user_info} - {error}")
    except Exception as e:
        # Last resort - just log the error
        error_logger.critical(f"ERROR HANDLER FAILURE: {e}, Original error: {error}, Command: /{command_name}, User: {user_info}")

if __name__ == "__main__":
    if not config.token or config.token == "YOUR_BOT_TOKEN_HERE":
        print("Please configure your bot token in config.json!")
    else:
        bot.run(config.token)
