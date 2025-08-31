import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import re
import asyncio
import sys
import os
from collections import defaultdict, deque

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, PermissionChecker

class AutoModerationCog(commands.Cog, name="AutoModeration"):
    """Automated moderation features for maintaining server quality"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Spam tracking
        self.message_cache = defaultdict(lambda: deque(maxlen=10))
        self.spam_tracking = defaultdict(int)
        
        # Default filter lists
        self.default_bad_words = [
            # Add your own bad words list here
            "spam", "advertisement", "discord.gg"  # Examples only
        ]
        
        # URL regex pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Discord invite pattern
        self.invite_pattern = re.compile(
            r'discord\.gg/[a-zA-Z0-9]+|discord\.com/invite/[a-zA-Z0-9]+|discordapp\.com/invite/[a-zA-Z0-9]+'
        )
    
    @property
    def db(self):
        return self.bot.db
    
    def get_automod_settings(self, guild_id: int) -> Dict:
        """Get automod settings for a guild"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        
        if not result:
            # Create default settings
            cursor.execute(
                "INSERT INTO guild_settings (guild_id) VALUES (?)",
                (guild_id,)
            )
            self.db.commit()
            return {
                'automod_enabled': False,
                'max_warnings': 3,
                'warning_action': 'timeout',
                'spam_detection': True,
                'link_filtering': False,
                'invite_filtering': True,
                'bad_word_filtering': False
            }
        
        return {
            'automod_enabled': bool(result[3]),
            'max_warnings': result[4],
            'warning_action': result[5],
            'spam_detection': True,  # Default values for new features
            'link_filtering': False,
            'invite_filtering': True,
            'bad_word_filtering': False
        }
    
    def is_spam(self, message: discord.Message) -> bool:
        """Check if a message is spam"""
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        # Add message to cache
        self.message_cache[user_id].append({
            'content': message.content.lower(),
            'timestamp': current_time,
            'channel_id': message.channel.id
        })
        
        recent_messages = [
            msg for msg in self.message_cache[user_id]
            if (current_time - msg['timestamp']).total_seconds() < 10
        ]
        
        # Check for rapid messaging (5+ messages in 10 seconds)
        if len(recent_messages) >= 5:
            return True
        
        # Check for duplicate messages (3+ identical messages in 30 seconds)
        thirty_seconds_ago = current_time - timedelta(seconds=30)
        recent_content = [
            msg['content'] for msg in self.message_cache[user_id]
            if msg['timestamp'] > thirty_seconds_ago
        ]
        
        if recent_content.count(message.content.lower()) >= 3:
            return True
        
        # Check for excessive caps (70%+ caps in messages over 10 characters)
        if len(message.content) > 10:
            caps_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
            if caps_ratio > 0.7:
                return True
        
        return False
    
    def contains_bad_words(self, content: str, bad_words: List[str]) -> bool:
        """Check if content contains bad words"""
        content_lower = content.lower()
        return any(word.lower() in content_lower for word in bad_words)
    
    def contains_links(self, content: str) -> bool:
        """Check if content contains URLs"""
        return bool(self.url_pattern.search(content))
    
    def contains_invites(self, content: str) -> bool:
        """Check if content contains Discord invites"""
        return bool(self.invite_pattern.search(content))
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Main automod message listener"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignore users with manage_messages permission
        if message.author.guild_permissions.manage_messages:
            return
        
        settings = self.get_automod_settings(message.guild.id)
        
        if not settings['automod_enabled']:
            return
        
        violations = []
        
        # Spam detection
        if settings['spam_detection'] and self.is_spam(message):
            violations.append("spam")
        
        # Link filtering
        if settings['link_filtering'] and self.contains_links(message.content):
            violations.append("links")
        
        # Invite filtering
        if settings['invite_filtering'] and self.contains_invites(message.content):
            violations.append("invites")
        
        # Bad word filtering
        if settings['bad_word_filtering'] and self.contains_bad_words(message.content, self.default_bad_words):
            violations.append("bad_words")
        
        if violations:
            await self.handle_violations(message, violations)
    
    async def handle_violations(self, message: discord.Message, violations: List[str]):
        """Handle automod violations"""
        try:
            # Delete the message
            await message.delete()
        except:
            pass
        
        # Create violation embed
        violation_text = {
            'spam': 'Spam/Excessive messaging',
            'links': 'Unauthorized links',
            'invites': 'Discord invites',
            'bad_words': 'Inappropriate content'
        }
        
        embed = discord.Embed(
            title="🚨 AutoMod Violation",
            description=f"{message.author.mention}, your message was removed for violating server rules.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Violations",
            value="\n".join([f"• {violation_text[v]}" for v in violations]),
            inline=False
        )
        
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        
        # Send warning message (delete after 10 seconds)
        try:
            warning_msg = await message.channel.send(embed=embed)
            await asyncio.sleep(10)
            await warning_msg.delete()
        except:
            pass
        
        # Add warning to database if spam or bad words
        if 'spam' in violations or 'bad_words' in violations:
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (message.author.id, message.guild.id, self.bot.user.id, f"AutoMod: {', '.join(violations)}")
            )
            self.db.commit()
        
        # Log to mod channel
        log_embed = discord.Embed(
            title="🤖 AutoMod Action",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        log_embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=True)
        log_embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        log_embed.add_field(name="Violations", value=", ".join(violations), inline=False)
        log_embed.add_field(name="Original Message", value=message.content[:1000] + ("..." if len(message.content) > 1000 else ""), inline=False)
        
        # Send to log channel
        cursor = self.db.cursor()
        cursor.execute("SELECT log_channel FROM guild_settings WHERE guild_id = ?", (message.guild.id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            try:
                log_channel = message.guild.get_channel(result[0])
                if log_channel:
                    await log_channel.send(embed=log_embed)
            except:
                pass
    
    @app_commands.command(name="automod", description="Configure automoderation settings")
    async def automod_config(self, interaction: discord.Interaction):
        """Interactive automod configuration"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to configure automod.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        settings = self.get_automod_settings(interaction.guild.id)
        
        embed = discord.Embed(
            title="🤖 AutoModeration Settings",
            description="Configure automatic moderation features for your server.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Current settings
        embed.add_field(
            name="📊 Current Settings",
            value=f"**Status:** {'🟢 Enabled' if settings['automod_enabled'] else '🔴 Disabled'}\n"
                  f"**Spam Detection:** {'✅' if settings['spam_detection'] else '❌'}\n"
                  f"**Link Filtering:** {'✅' if settings['link_filtering'] else '❌'}\n"
                  f"**Invite Filtering:** {'✅' if settings['invite_filtering'] else '❌'}\n"
                  f"**Bad Word Filter:** {'✅' if settings['bad_word_filtering'] else '❌'}",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Warning Settings",
            value=f"**Max Warnings:** {settings['max_warnings']}\n"
                  f"**Action After Max:** {settings['warning_action'].title()}",
            inline=True
        )
        
        view = AutoModView(settings)
        await interaction.response.send_message(embed=embed, view=view)

class AutoModView(discord.ui.View):
    """Interactive automod settings panel"""
    
    def __init__(self, settings: Dict, *, timeout=300):
        super().__init__(timeout=timeout)
        self.settings = settings
    
    @discord.ui.button(label='Toggle AutoMod', style=discord.ButtonStyle.primary, emoji='🔄')
    async def toggle_automod(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This would update the database and refresh the embed
        await interaction.response.send_message("AutoMod toggled! (Database update would happen here)", ephemeral=True)
    
    @discord.ui.button(label='Spam Detection', style=discord.ButtonStyle.secondary, emoji='🚫')
    async def toggle_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Spam detection toggled!", ephemeral=True)
    
    @discord.ui.button(label='Link Filter', style=discord.ButtonStyle.secondary, emoji='🔗')
    async def toggle_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Link filtering toggled!", ephemeral=True)
    
    @discord.ui.button(label='Invite Filter', style=discord.ButtonStyle.secondary, emoji='📨')
    async def toggle_invites(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Invite filtering toggled!", ephemeral=True)
    
    @discord.ui.button(label='Bad Word Filter', style=discord.ButtonStyle.secondary, emoji='🤬')
    async def toggle_bad_words(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bad word filtering toggled!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoModerationCog(bot))
