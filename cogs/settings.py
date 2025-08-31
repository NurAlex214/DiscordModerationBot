import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional, Dict
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder

class SettingsView(discord.ui.View):
    """Main settings panel with category buttons"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Moderation', style=discord.ButtonStyle.primary, emoji='🔨')
    async def moderation_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔨 Moderation Settings",
            description="Configure moderation-related settings for your server.",
            color=discord.Color.blue()
        )
        view = ModerationSettingsView()
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='AutoMod', style=discord.ButtonStyle.primary, emoji='🤖')
    async def automod_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 AutoMod Settings",
            description="Configure automatic moderation features.",
            color=discord.Color.blue()
        )
        view = AutoModSettingsView()
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='Logging', style=discord.ButtonStyle.primary, emoji='📝')
    async def logging_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📝 Logging Settings",
            description="Configure logging and audit features.",
            color=discord.Color.blue()
        )
        view = LoggingSettingsView()
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label='Back to Main', style=discord.ButtonStyle.secondary, emoji='🏠')
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This would reset to the main settings view
        await interaction.response.edit_message(embed=self.get_main_embed(interaction.guild), view=self)
    
    def get_main_embed(self, guild: discord.Guild) -> discord.Embed:
        """Get the main settings embed"""
        embed = discord.Embed(
            title=f"⚙️ Server Settings: {guild.name}",
            description="Select a category below to configure settings.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🔨 Moderation",
            value="Configure warning limits, actions, and log channels",
            inline=True
        )
        
        embed.add_field(
            name="🤖 AutoMod", 
            value="Set up automatic content filtering and spam detection",
            inline=True
        )
        
        embed.add_field(
            name="📝 Logging",
            value="Configure audit logs and moderation tracking",
            inline=True
        )
        
        return embed

class ModerationSettingsView(discord.ui.View):
    """Moderation-specific settings"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.select(
        placeholder="Set Log Channel...",
        options=[
            discord.SelectOption(label="Select a channel", value="select_channel", emoji="📝")
        ]
    )
    async def set_log_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Create channel dropdown
        channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        
        if not channels:
            embed = EmbedBuilder.error("No Available Channels", "No text channels available for logging.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = ChannelSelectView(channels, "log_channel")
        embed = EmbedBuilder.info("Select Log Channel", "Choose a channel for moderation logs:")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label='Warning Limits', style=discord.ButtonStyle.secondary, emoji='⚠️')
    async def warning_limits(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarningLimitsModal())
    
    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

class AutoModSettingsView(discord.ui.View):
    """AutoMod-specific settings"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Toggle AutoMod', style=discord.ButtonStyle.primary, emoji='🔄')
    async def toggle_automod(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.success("AutoMod Status", "AutoMod has been toggled!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Spam Detection', style=discord.ButtonStyle.secondary, emoji='🚫')
    async def spam_detection(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Spam Detection", "Spam detection settings would be configured here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Content Filters', style=discord.ButtonStyle.secondary, emoji='🔍')
    async def content_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Content Filters", "Content filter settings would be configured here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

class LoggingSettingsView(discord.ui.View):
    """Logging-specific settings"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Audit Log Channel', style=discord.ButtonStyle.primary, emoji='📋')
    async def audit_log_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Audit Logs", "Audit log channel would be set here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Log Events', style=discord.ButtonStyle.secondary, emoji='📅')
    async def log_events(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Log Events", "Log event configuration would be here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

class ChannelSelectView(discord.ui.View):
    """View for selecting channels"""
    
    def __init__(self, channels: list, setting_type: str, *, timeout=180):
        super().__init__(timeout=timeout)
        self.setting_type = setting_type
        
        options = []
        for channel in channels[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=f"#{channel.name}",
                value=str(channel.id),
                description=f"Set as {setting_type.replace('_', ' ')}"
            ))
        
        if options:
            select = discord.ui.Select(
                placeholder=f"Choose a channel for {setting_type.replace('_', ' ')}...",
                options=options
            )
            select.callback = self.channel_selected
            self.add_item(select)
    
    async def channel_selected(self, interaction: discord.Interaction):
        channel_id = int(interaction.data['values'][0])
        channel = interaction.guild.get_channel(channel_id)
        
        if not channel:
            embed = EmbedBuilder.error("Error", "Channel not found.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Update database
        cursor = interaction.client.db.cursor()
        cursor.execute(
            f"UPDATE guild_settings SET {self.setting_type} = ? WHERE guild_id = ?",
            (channel_id, interaction.guild.id)
        )
        interaction.client.db.commit()
        
        embed = EmbedBuilder.success(
            "Channel Set",
            f"{channel.mention} has been set as the {self.setting_type.replace('_', ' ')}."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class WarningLimitsModal(discord.ui.Modal):
    """Modal for setting warning limits"""
    
    def __init__(self):
        super().__init__(title="Configure Warning Limits")
        
        self.max_warnings = discord.ui.TextInput(
            label="Maximum Warnings",
            placeholder="Enter the maximum number of warnings (1-10)",
            required=True,
            max_length=2
        )
        self.add_item(self.max_warnings)
        
        self.warning_action = discord.ui.TextInput(
            label="Action After Max Warnings",
            placeholder="timeout, kick, or ban",
            required=True,
            max_length=10
        )
        self.add_item(self.warning_action)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_warns = int(self.max_warnings.value)
            if not 1 <= max_warns <= 10:
                raise ValueError("Max warnings must be between 1 and 10")
            
            action = self.warning_action.value.lower()
            if action not in ['timeout', 'kick', 'ban']:
                raise ValueError("Action must be 'timeout', 'kick', or 'ban'")
            
            # Update database
            cursor = interaction.client.db.cursor()
            cursor.execute(
                "UPDATE guild_settings SET max_warnings = ?, warning_action = ? WHERE guild_id = ?",
                (max_warns, action, interaction.guild.id)
            )
            interaction.client.db.commit()
            
            embed = EmbedBuilder.success(
                "Warning Settings Updated",
                f"Max warnings set to {max_warns}, action set to {action}."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError as e:
            embed = EmbedBuilder.error("Invalid Input", str(e))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to update settings: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SettingsCog(commands.Cog, name="Settings"):
    """Server configuration and settings management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @property
    def db(self):
        return self.bot.db
    
    @app_commands.command(name="settings", description="Configure server settings")
    async def settings(self, interaction: discord.Interaction):
        """Interactive settings panel"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to access settings.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = SettingsView()
        embed = view.get_main_embed(interaction.guild)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="setlogchannel", description="Set the moderation log channel")
    @app_commands.describe(channel="The channel to use for moderation logs")
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the moderation log channel"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to change settings.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not channel.permissions_for(interaction.guild.me).send_messages:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to send messages in that channel.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Update database
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, log_channel) VALUES (?, ?)",
            (interaction.guild.id, channel.id)
        )
        self.db.commit()
        
        embed = EmbedBuilder.success(
            "Log Channel Set",
            f"Moderation logs will now be sent to {channel.mention}."
        )
        await interaction.response.send_message(embed=embed)
        
        # Send test message to log channel
        test_embed = discord.Embed(
            title="✅ Log Channel Configured",
            description="This channel has been set as the moderation log channel.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        test_embed.add_field(name="Configured By", value=interaction.user.mention, inline=True)
        
        try:
            await channel.send(embed=test_embed)
        except:
            pass
    
    @app_commands.command(name="toggleautomod", description="Enable or disable automoderation")
    @app_commands.describe(enabled="Whether to enable automoderation")
    async def toggleautomod(self, interaction: discord.Interaction, enabled: bool):
        """Toggle automoderation on/off"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to change settings.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Update database
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, automod_enabled) VALUES (?, ?)",
            (interaction.guild.id, enabled)
        )
        self.db.commit()
        
        status = "enabled" if enabled else "disabled"
        embed = EmbedBuilder.success(
            f"AutoMod {status.title()}",
            f"Automoderation has been {status} for this server."
        )
        
        if enabled:
            embed.add_field(
                name="📋 Features",
                value="• Spam detection\n• Invite filtering\n• Content filtering\n• Automatic warnings",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="viewsettings", description="View current server settings")
    async def viewsettings(self, interaction: discord.Interaction):
        """Display current server settings"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (interaction.guild.id,))
        result = cursor.fetchone()
        
        embed = discord.Embed(
            title=f"⚙️ Current Settings: {interaction.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if result:
            log_channel = interaction.guild.get_channel(result[1]) if result[1] else None
            
            embed.add_field(
                name="🔨 Moderation",
                value=f"**Log Channel:** {log_channel.mention if log_channel else 'Not set'}\n"
                      f"**Max Warnings:** {result[4]}\n"
                      f"**Warning Action:** {result[5].title()}",
                inline=False
            )
            
            embed.add_field(
                name="🤖 AutoModeration",
                value=f"**Status:** {'🟢 Enabled' if result[3] else '🔴 Disabled'}",
                inline=True
            )
        else:
            embed.add_field(
                name="📋 Status",
                value="No settings configured yet. Use `/settings` to configure your server.",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

class ModerationSettingsView(discord.ui.View):
    """Moderation settings sub-panel"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Set Log Channel', style=discord.ButtonStyle.primary, emoji='📝')
    async def set_log_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        
        if not channels:
            embed = EmbedBuilder.error("No Available Channels", "No text channels available for logging.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = ChannelSelectView(channels, "log_channel")
        embed = EmbedBuilder.info("Select Log Channel", "Choose a channel for moderation logs:")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label='Warning Settings', style=discord.ButtonStyle.secondary, emoji='⚠️')
    async def warning_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarningLimitsModal())
    
    @discord.ui.button(label='Back to Settings', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back_to_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

class AutoModSettingsView(discord.ui.View):
    """AutoMod settings sub-panel"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Enable/Disable', style=discord.ButtonStyle.danger, emoji='🔄')
    async def toggle_automod(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get current status
        cursor = interaction.client.db.cursor()
        cursor.execute("SELECT automod_enabled FROM guild_settings WHERE guild_id = ?", (interaction.guild.id,))
        result = cursor.fetchone()
        
        current_status = bool(result[0]) if result else False
        new_status = not current_status
        
        # Update database
        cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, automod_enabled) VALUES (?, ?)",
            (interaction.guild.id, new_status)
        )
        interaction.client.db.commit()
        
        status_text = "enabled" if new_status else "disabled"
        embed = EmbedBuilder.success(
            f"AutoMod {status_text.title()}",
            f"Automoderation has been {status_text}."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Filter Settings', style=discord.ButtonStyle.secondary, emoji='🔍')
    async def filter_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Filter Settings", "Content filter configuration would be implemented here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Back to Settings', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back_to_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

class LoggingSettingsView(discord.ui.View):
    """Logging settings sub-panel"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Set Audit Channel', style=discord.ButtonStyle.primary, emoji='📋')
    async def set_audit_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        
        if not channels:
            embed = EmbedBuilder.error("No Available Channels", "No text channels available for audit logs.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = ChannelSelectView(channels, "audit_channel")
        embed = EmbedBuilder.info("Select Audit Channel", "Choose a channel for audit logs:")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label='Log Types', style=discord.ButtonStyle.secondary, emoji='📝')
    async def log_types(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedBuilder.info("Log Types", "Log type configuration would be implemented here.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label='Back to Settings', style=discord.ButtonStyle.secondary, emoji='◀️')
    async def back_to_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_view = SettingsView()
        embed = main_view.get_main_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=main_view)

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
