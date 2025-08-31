import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Union
import sqlite3
import sys
import os
import logging

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, ConfirmationView, TimeConverter, PermissionChecker, format_duration

# Create logger for moderation actions
mod_logger = logging.getLogger('moderation_actions')
mod_logger.setLevel(logging.INFO)

# Create logger for security events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

class ModerationCog(commands.Cog, name="Moderation"):
    """Core moderation commands for managing users and maintaining order"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @property
    def db(self):
        return self.bot.db
    
    async def log_action(self, guild: discord.Guild, embed: discord.Embed):
        """Send moderation log to the configured log channel"""
        cursor = self.db.cursor()
        cursor.execute("SELECT log_channel FROM guild_settings WHERE guild_id = ?", (guild.id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            try:
                channel = guild.get_channel(result[0])
                if channel:
                    await channel.send(embed=embed)
            except:
                pass  # Silently fail if we can't log
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        user="The user to ban",
        reason="Reason for the ban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    async def ban(
        self, 
        interaction: discord.Interaction, 
        user: Union[discord.Member, discord.User],
        reason: str = "No reason provided",
        delete_days: app_commands.Range[int, 0, 7] = 0
    ):
        """Ban a user with confirmation dialog"""
        if not PermissionChecker.can_ban(interaction.user):
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED MODERATION: {interaction.user} ({interaction.user.id}) attempted /ban in {interaction.guild.name} ({interaction.guild.id}) without Ban Members permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Ban Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if isinstance(user, discord.Member):
            if not PermissionChecker.can_moderate(interaction.user, user):
                embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="🔨 Confirm Ban",
            description=f"Are you sure you want to ban {user.mention}?",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Messages to Delete", value=f"{delete_days} day(s)", inline=True)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Ban confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Ban has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute ban
        try:
            await interaction.guild.ban(
                user, 
                reason=f"Banned by {interaction.user} | {reason}",
                delete_message_days=delete_days
            )
            
            # Success embed
            embed = EmbedBuilder.success(
                "User Banned",
                f"{user.mention} has been banned from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Ban", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
            # Log to console
            mod_logger.info(f'User banned: {user} ({user.id}) by {interaction.user} ({interaction.user.id}) in {interaction.guild.name} ({interaction.guild.id}) - Reason: {reason}')
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Ban", "I don't have permission to ban this user.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        user="The user to kick",
        reason="Reason for the kick"
    )
    async def kick(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Kick a user with confirmation dialog"""
        if not PermissionChecker.can_kick(interaction.user):
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED MODERATION: {interaction.user} ({interaction.user.id}) attempted /kick in {interaction.guild.name} ({interaction.guild.id}) without Kick Members permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Kick Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not PermissionChecker.can_moderate(interaction.user, user):
            embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="👢 Confirm Kick",
            description=f"Are you sure you want to kick {user.mention}?",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Kick confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Kick has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute kick
        try:
            await user.kick(reason=f"Kicked by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "User Kicked",
                f"{user.mention} has been kicked from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Kick", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
            # Log to console
            mod_logger.info(f'User kicked: {user} ({user.id}) by {interaction.user} ({interaction.user.id}) in {interaction.guild.name} ({interaction.guild.id}) - Reason: {reason}')
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Kick", "I don't have permission to kick this user.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="timeout", description="Timeout a user for a specified duration")
    @app_commands.describe(
        user="The user to timeout",
        duration="Duration of timeout (e.g., 1h, 30m, 1d)",
        reason="Reason for the timeout"
    )
    async def timeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        duration: str,
        reason: str = "No reason provided"
    ):
        """Timeout a user with duration parsing"""
        if not interaction.user.guild_permissions.moderate_members:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED MODERATION: {interaction.user} ({interaction.user.id}) attempted /timeout in {interaction.guild.name} ({interaction.guild.id}) without Moderate Members permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Moderate Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not PermissionChecker.can_moderate(interaction.user, user):
            embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse duration
        time_delta = TimeConverter.convert(duration)
        if not time_delta:
            embed = EmbedBuilder.error("Invalid Duration", "Please provide a valid duration (e.g., 1h, 30m, 1d)")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if time_delta > timedelta(days=28):
            embed = EmbedBuilder.error("Duration Too Long", "Timeout duration cannot exceed 28 days.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="⏰ Confirm Timeout",
            description=f"Are you sure you want to timeout {user.mention}?",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Duration", value=format_duration(time_delta), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Timeout confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Timeout has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute timeout
        try:
            until = datetime.utcnow() + time_delta
            await user.timeout(until, reason=f"Timed out by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "User Timed Out",
                f"{user.mention} has been timed out for {format_duration(time_delta)}."
            )
            embed.add_field(name="Until", value=discord.utils.format_dt(until, style='F'), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Timeout", user, interaction.user, reason)
            log_embed.add_field(name="Duration", value=format_duration(time_delta), inline=True)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Timeout", "I don't have permission to timeout this user.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="untimeout", description="Remove timeout from a user")
    @app_commands.describe(
        user="The user to remove timeout from",
        reason="Reason for removing timeout"
    )
    async def untimeout(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Remove timeout from a user"""
        if not interaction.user.guild_permissions.moderate_members:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED MODERATION: {interaction.user} ({interaction.user.id}) attempted /untimeout in {interaction.guild.name} ({interaction.guild.id}) without Moderate Members permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Moderate Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not user.is_timed_out():
            embed = EmbedBuilder.warning("Not Timed Out", "This user is not currently timed out.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await user.timeout(None, reason=f"Timeout removed by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "Timeout Removed",
                f"Timeout has been removed from {user.mention}."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Timeout Removed", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Remove Timeout", "I don't have permission to modify this user's timeout.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    async def warn(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Warn a user and track warnings in database"""
        if not interaction.user.guild_permissions.moderate_members:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED MODERATION: {interaction.user} ({interaction.user.id}) attempted /warn in {interaction.guild.name} ({interaction.guild.id}) without Moderate Members permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Moderate Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not PermissionChecker.can_moderate(interaction.user, user):
            embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add warning to database
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (user.id, interaction.guild.id, interaction.user.id, reason)
        )
        self.db.commit()
        
        # Get warning count
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?",
            (user.id, interaction.guild.id)
        )
        warning_count = cursor.fetchone()[0]
        
        # Create warning embed
        embed = EmbedBuilder.warning(
            "User Warned",
            f"{user.mention} has been warned."
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Warning Count", value=f"{warning_count}", inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        # Check if auto-action should be taken
        cursor.execute(
            "SELECT max_warnings, warning_action FROM guild_settings WHERE guild_id = ?",
            (interaction.guild.id,)
        )
        settings = cursor.fetchone()
        
        if settings and warning_count >= settings[0]:
            action = settings[1]
            if action == "timeout":
                await user.timeout(
                    datetime.utcnow() + timedelta(hours=1),
                    reason=f"Auto-timeout after {warning_count} warnings"
                )
                embed.add_field(
                    name="Auto-Action",
                    value="User has been automatically timed out for 1 hour.",
                    inline=False
                )
            elif action == "kick":
                await user.kick(reason=f"Auto-kick after {warning_count} warnings")
                embed.add_field(
                    name="Auto-Action",
                    value="User has been automatically kicked.",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
        
        # Log the action
        log_embed = EmbedBuilder.moderation_log("Warn", user, interaction.user, reason)
        log_embed.add_field(name="Warning Count", value=str(warning_count), inline=True)
        await self.log_action(interaction.guild, log_embed)
    
    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="The user to check warnings for")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """Display user's warning history"""
        if not interaction.user.guild_permissions.moderate_members:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Moderate Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT id, moderator_id, reason, timestamp 
               FROM warnings 
               WHERE user_id = ? AND guild_id = ? 
               ORDER BY timestamp DESC""",
            (user.id, interaction.guild.id)
        )
        warnings = cursor.fetchall()
        
        if not warnings:
            embed = EmbedBuilder.info("No Warnings", f"{user.mention} has no warnings on record.")
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {user.display_name}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=True)
        
        # Show recent warnings
        for i, (warn_id, mod_id, warn_reason, timestamp) in enumerate(warnings[:5]):
            moderator = interaction.guild.get_member(mod_id)
            mod_name = moderator.display_name if moderator else "Unknown"
            
            # Parse timestamp
            warn_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            embed.add_field(
                name=f"Warning #{warn_id}",
                value=f"**Moderator:** {mod_name}\n**Reason:** {warn_reason}\n**Date:** {discord.utils.format_dt(warn_time, style='R')}",
                inline=False
            )
        
        if len(warnings) > 5:
            embed.set_footer(text=f"Showing 5 of {len(warnings)} warnings")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @app_commands.describe(
        user="The user to clear warnings for",
        reason="Reason for clearing warnings"
    )
    async def clearwarnings(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Clear all warnings for a user"""
        if not interaction.user.guild_permissions.moderate_members:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Moderate Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?",
            (user.id, interaction.guild.id)
        )
        warning_count = cursor.fetchone()[0]
        
        if warning_count == 0:
            embed = EmbedBuilder.info("No Warnings", f"{user.mention} has no warnings to clear.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="🗑️ Confirm Clear Warnings",
            description=f"Are you sure you want to clear {warning_count} warning(s) for {user.mention}?",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Clear warnings confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Clear warnings has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Clear warnings
        cursor.execute(
            "DELETE FROM warnings WHERE user_id = ? AND guild_id = ?",
            (user.id, interaction.guild.id)
        )
        self.db.commit()
        
        embed = EmbedBuilder.success(
            "Warnings Cleared",
            f"Cleared {warning_count} warning(s) for {user.mention}."
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        await interaction.edit_original_response(embed=embed, view=None)
        
        # Log the action
        log_embed = EmbedBuilder.moderation_log("Clear Warnings", user, interaction.user, reason)
        log_embed.add_field(name="Warnings Cleared", value=str(warning_count), inline=True)
        await self.log_action(interaction.guild, log_embed)
    
    @app_commands.command(name="softban", description="Softban a user (ban then immediately unban to delete messages)")
    @app_commands.describe(
        user="The user to softban",
        reason="Reason for the softban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    async def softban(
        self,
        interaction: discord.Interaction,
        user: Union[discord.Member, discord.User],
        reason: str = "No reason provided",
        delete_days: app_commands.Range[int, 0, 7] = 1
    ):
        """Softban a user (ban then unban to clean messages)"""
        if not PermissionChecker.can_ban(interaction.user):
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Ban Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if isinstance(user, discord.Member):
            if not PermissionChecker.can_moderate(interaction.user, user):
                embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="⚡ Confirm Softban",
            description=f"Are you sure you want to softban {user.mention}?\n\n**Note:** This will ban and immediately unban to delete their messages.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Messages to Delete", value=f"{delete_days} day(s)", inline=True)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Softban confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Softban has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        try:
            # Execute softban
            await interaction.guild.ban(
                user,
                reason=f"Softbanned by {interaction.user} | {reason}",
                delete_message_days=delete_days
            )
            await interaction.guild.unban(user, reason=f"Softban unban by {interaction.user}")
            
            embed = EmbedBuilder.success(
                "User Softbanned",
                f"{user.mention} has been softbanned (messages deleted, user not banned)."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Messages Deleted", value=f"{delete_days} day(s)", inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Softban", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Softban", "I don't have permission to ban/unban this user.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="massban", description="Ban multiple users by ID")
    @app_commands.describe(
        user_ids="User IDs separated by spaces or commas",
        reason="Reason for the mass ban"
    )
    async def massban(
        self,
        interaction: discord.Interaction,
        user_ids: str,
        reason: str = "Mass ban"
    ):
        """Ban multiple users by their IDs"""
        if not PermissionChecker.can_ban(interaction.user):
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Ban Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse user IDs
        id_list = re.split(r'[\s,]+', user_ids.strip())
        valid_ids = []
        
        for user_id in id_list:
            try:
                valid_ids.append(int(user_id))
            except ValueError:
                continue
        
        if not valid_ids:
            embed = EmbedBuilder.error("Invalid Input", "Please provide valid user IDs separated by spaces or commas.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if len(valid_ids) > 10:
            embed = EmbedBuilder.error("Too Many Users", "Mass ban is limited to 10 users at once for safety.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="⚡ Confirm Mass Ban",
            description=f"Are you sure you want to ban {len(valid_ids)} users?",
            color=discord.Color.red()
        )
        embed.add_field(name="User Count", value=str(len(valid_ids)), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Mass ban confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Mass ban has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute mass ban
        banned_count = 0
        failed_bans = []
        
        for user_id in valid_ids:
            try:
                user = discord.Object(user_id)
                await interaction.guild.ban(user, reason=f"Mass ban by {interaction.user} | {reason}")
                banned_count += 1
            except Exception as e:
                failed_bans.append(f"{user_id}: {str(e)[:50]}")
        
        embed = EmbedBuilder.success(
            "Mass Ban Complete",
            f"Successfully banned {banned_count}/{len(valid_ids)} users."
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        if failed_bans:
            embed.add_field(
                name="Failed Bans",
                value="\n".join(failed_bans[:5]) + ("\n..." if len(failed_bans) > 5 else ""),
                inline=False
            )
        
        await interaction.edit_original_response(embed=embed, view=None)
        
        # Log the action
        log_embed = EmbedBuilder.moderation_log("Mass Ban", discord.Object(0), interaction.user, reason)
        log_embed.add_field(name="Users Banned", value=str(banned_count), inline=True)
        await self.log_action(interaction.guild, log_embed)
    
    @app_commands.command(name="lockdown", description="Lock down the entire server")
    @app_commands.describe(
        reason="Reason for the lockdown",
        duration="Duration of lockdown (optional)"
    )
    async def lockdown(
        self,
        interaction: discord.Interaction,
        reason: str = "Server lockdown",
        duration: Optional[str] = None
    ):
        """Lock down the entire server"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse duration if provided
        end_time = None
        if duration:
            time_delta = TimeConverter.convert(duration)
            if time_delta:
                end_time = datetime.utcnow() + time_delta
        
        # Confirmation dialog
        embed = discord.Embed(
            title="🚨 Confirm Server Lockdown",
            description="Are you sure you want to lock down the entire server?",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        if end_time:
            embed.add_field(name="Duration", value=format_duration(time_delta), inline=True)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Lockdown confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Server lockdown has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute lockdown
        locked_channels = 0
        failed_channels = []
        
        for channel in interaction.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(
                    interaction.guild.default_role,
                    overwrite=overwrite,
                    reason=f"Server lockdown by {interaction.user} | {reason}"
                )
                locked_channels += 1
            except Exception:
                failed_channels.append(channel.name)
        
        embed = EmbedBuilder.success(
            "Server Locked Down",
            f"Locked {locked_channels} text channels."
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        if end_time:
            embed.add_field(name="Ends", value=discord.utils.format_dt(end_time, style='R'), inline=True)
        
        if failed_channels:
            embed.add_field(name="Failed Channels", value=", ".join(failed_channels[:5]), inline=False)
        
        await interaction.edit_original_response(embed=embed, view=None)
        
        # Schedule unlock if duration provided
        if end_time:
            await asyncio.sleep(time_delta.total_seconds())
            await self.auto_unlock_server(interaction.guild, interaction.user, reason)
    
    async def auto_unlock_server(self, guild: discord.Guild, moderator: discord.Member, original_reason: str):
        """Automatically unlock server after lockdown duration"""
        unlocked_channels = 0
        
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(
                    guild.default_role,
                    overwrite=overwrite,
                    reason=f"Auto-unlock after lockdown by {moderator}"
                )
                unlocked_channels += 1
            except Exception:
                continue
        
        # Log auto-unlock
        log_embed = EmbedBuilder.moderation_log("Auto Server Unlock", discord.Object(0), moderator, "Lockdown duration expired")
        log_embed.add_field(name="Channels Unlocked", value=str(unlocked_channels), inline=True)
        await self.log_action(guild, log_embed)
    
    @app_commands.command(name="mute", description="Mute a user (remove their ability to speak in voice channels)")
    @app_commands.describe(
        user="The user to mute",
        reason="Reason for the mute"
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Mute a user in voice channels"""
        if not interaction.user.guild_permissions.mute_members:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Mute Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not PermissionChecker.can_moderate(interaction.user, user):
            embed = EmbedBuilder.error("Cannot Moderate", "You cannot moderate this user due to role hierarchy.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await user.edit(mute=True, reason=f"Muted by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "User Muted",
                f"{user.mention} has been muted in voice channels."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Voice Mute", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Mute", "I don't have permission to mute this user.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unmute", description="Unmute a user in voice channels")
    @app_commands.describe(
        user="The user to unmute",
        reason="Reason for unmuting"
    )
    async def unmute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided"
    ):
        """Unmute a user in voice channels"""
        if not interaction.user.guild_permissions.mute_members:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Mute Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await user.edit(mute=False, reason=f"Unmuted by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "User Unmuted",
                f"{user.mention} has been unmuted in voice channels."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Voice Unmute", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Unmute", "I don't have permission to unmute this user.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="Reason for the unban"
    )
    async def unban(
        self, 
        interaction: discord.Interaction, 
        user_id: str,
        reason: str = "No reason provided"
    ):
        """Unban a user by ID"""
        if not PermissionChecker.can_ban(interaction.user):
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Ban Members' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            user_id = int(user_id)
        except ValueError:
            embed = EmbedBuilder.error("Invalid User ID", "Please provide a valid user ID.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if user is actually banned
        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(user_id))
            user = ban_entry.user
        except discord.NotFound:
            embed = EmbedBuilder.error("User Not Banned", "This user is not banned from the server.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except discord.Forbidden:
            embed = EmbedBuilder.error("Cannot Access Ban List", "I don't have permission to view the ban list.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="🔓 Confirm Unban",
            description=f"Are you sure you want to unban {user.mention}?",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Unban confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Unban has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute unban
        try:
            await interaction.guild.unban(user, reason=f"Unbanned by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "User Unbanned",
                f"{user.mention} has been unbanned from the server."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log the action
            log_embed = EmbedBuilder.moderation_log("Unban", user, interaction.user, reason)
            await self.log_action(interaction.guild, log_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Failed to Unban", "I don't have permission to unban users.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
