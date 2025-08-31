import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Union, List
import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, ConfirmationView, PaginationView, PermissionChecker

# Create loggers
admin_logger = logging.getLogger('admin_actions')
admin_logger.setLevel(logging.INFO)

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

class PurgeView(discord.ui.View):
    """Interactive purge confirmation with options"""
    
    def __init__(self, amount: int, *, timeout=180):
        super().__init__(timeout=timeout)
        self.amount = amount
        self.value = None
        self.filter_bots = False
        self.filter_embeds = False
    
    @discord.ui.button(label=f'Purge Messages', style=discord.ButtonStyle.danger, emoji='🗑️')
    async def confirm_purge(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary, emoji='❌')
    async def cancel_purge(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
    
    @discord.ui.button(label='Filter: Bots Only', style=discord.ButtonStyle.secondary, emoji='🤖')
    async def toggle_bot_filter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.filter_bots = not self.filter_bots
        button.style = discord.ButtonStyle.primary if self.filter_bots else discord.ButtonStyle.secondary
        button.label = 'Filter: Bots Only ✓' if self.filter_bots else 'Filter: Bots Only'
        await interaction.response.edit_message(view=self)
    
    @discord.ui.button(label='Filter: Embeds Only', style=discord.ButtonStyle.secondary, emoji='📋')
    async def toggle_embed_filter(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.filter_embeds = not self.filter_embeds
        button.style = discord.ButtonStyle.primary if self.filter_embeds else discord.ButtonStyle.secondary
        button.label = 'Filter: Embeds Only ✓' if self.filter_embeds else 'Filter: Embeds Only'
        await interaction.response.edit_message(view=self)

class ChannelManagerView(discord.ui.View):
    """Interactive channel management interface"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
    
    @discord.ui.button(label='Create Text Channel', style=discord.ButtonStyle.primary, emoji='💬')
    async def create_text_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateChannelModal('text'))
    
    @discord.ui.button(label='Create Voice Channel', style=discord.ButtonStyle.primary, emoji='🔊')
    async def create_voice_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateChannelModal('voice'))
    
    @discord.ui.button(label='Create Category', style=discord.ButtonStyle.primary, emoji='📁')
    async def create_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreateChannelModal('category'))

class CreateChannelModal(discord.ui.Modal):
    """Modal for creating channels"""
    
    def __init__(self, channel_type: str):
        super().__init__(title=f"Create {channel_type.title()} Channel")
        self.channel_type = channel_type
        
        self.channel_name = discord.ui.TextInput(
            label="Channel Name",
            placeholder="Enter the channel name...",
            required=True,
            max_length=100
        )
        self.add_item(self.channel_name)
        
        if channel_type in ['text', 'voice']:
            self.channel_topic = discord.ui.TextInput(
                label="Topic/Description" if channel_type == 'text' else "Description",
                placeholder="Enter a topic or description...",
                required=False,
                style=discord.TextStyle.paragraph,
                max_length=1024
            )
            self.add_item(self.channel_topic)
    
    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted channel creation in {interaction.guild.name} ({interaction.guild.id}) without Manage Channels permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Channels' permission.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            name = self.channel_name.value.lower().replace(' ', '-')
            topic = getattr(self, 'channel_topic', None)
            topic_value = topic.value if topic and topic.value else None
            
            if self.channel_type == 'text':
                channel = await interaction.guild.create_text_channel(
                    name=name,
                    topic=topic_value,
                    reason=f"Channel created by {interaction.user}"
                )
            elif self.channel_type == 'voice':
                channel = await interaction.guild.create_voice_channel(
                    name=name,
                    reason=f"Channel created by {interaction.user}"
                )
            else:  # category
                channel = await interaction.guild.create_category(
                    name=name,
                    reason=f"Category created by {interaction.user}"
                )
            
            embed = EmbedBuilder.success(
                f"{self.channel_type.title()} Channel Created",
                f"Successfully created {channel.mention if hasattr(channel, 'mention') else channel.name}!"
            )
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to create channels.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to create channel: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminCog(commands.Cog, name="Administration"):
    """Administrative commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="purge", description="Delete multiple messages from a channel")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        user="Only delete messages from this user"
    )
    async def purge(
        self, 
        interaction: discord.Interaction, 
        amount: app_commands.Range[int, 1, 100],
        user: Optional[discord.Member] = None
    ):
        """Purge messages with interactive filters"""
        if not interaction.user.guild_permissions.manage_messages:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /purge in {interaction.guild.name} ({interaction.guild.id}) without Manage Messages permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Messages' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create confirmation embed
        embed = discord.Embed(
            title="🗑️ Confirm Purge",
            description=f"Are you sure you want to delete {amount} messages?",
            color=discord.Color.orange()
        )
        
        if user:
            embed.add_field(name="Target User", value=user.mention, inline=True)
        
        embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
        embed.add_field(
            name="Options",
            value="Use the buttons below to apply filters before confirming.",
            inline=False
        )
        
        view = PurgeView(amount)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Purge confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Purge has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Execute purge with filters
        def check(message):
            if user and message.author != user:
                return False
            if view.filter_bots and not message.author.bot:
                return False
            if view.filter_embeds and not message.embeds:
                return False
            return True
        
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = EmbedBuilder.success(
                "Messages Purged",
                f"Successfully deleted {len(deleted)} message(s)."
            )
            
            # Add filter info
            filters = []
            if user:
                filters.append(f"User: {user.mention}")
            if view.filter_bots:
                filters.append("Bots only")
            if view.filter_embeds:
                filters.append("Embeds only")
            
            if filters:
                embed.add_field(name="Filters Applied", value=", ".join(filters), inline=False)
            
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Delete confirmation message after a delay
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except:
                pass
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to delete messages.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="slowmode", description="Set slowmode for the current channel")
    @app_commands.describe(
        seconds="Slowmode duration in seconds (0-21600)",
        reason="Reason for setting slowmode"
    )
    async def slowmode(
        self, 
        interaction: discord.Interaction, 
        seconds: app_commands.Range[int, 0, 21600],
        reason: str = "No reason provided"
    ):
        """Set channel slowmode"""
        if not interaction.user.guild_permissions.manage_channels:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /slowmode in {interaction.guild.name} ({interaction.guild.id}) without Manage Channels permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Channels' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await interaction.channel.edit(
                slowmode_delay=seconds,
                reason=f"Slowmode set by {interaction.user} | {reason}"
            )
            
            if seconds == 0:
                embed = EmbedBuilder.success(
                    "Slowmode Disabled",
                    f"Slowmode has been disabled in {interaction.channel.mention}."
                )
            else:
                embed = EmbedBuilder.success(
                    "Slowmode Set",
                    f"Slowmode set to {seconds} second(s) in {interaction.channel.mention}."
                )
            
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to edit this channel.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="lock", description="Lock a channel to prevent users from sending messages")
    @app_commands.describe(
        channel="The channel to lock",
        reason="Reason for locking the channel"
    )
    async def lock(
        self, 
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        reason: str = "No reason provided"
    ):
        """Lock a channel"""
        if not interaction.user.guild_permissions.manage_channels:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /lock in {interaction.guild.name} ({interaction.guild.id}) without Manage Channels permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Channels' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        try:
            # Remove send message permission from @everyone
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"Channel locked by {interaction.user} | {reason}"
            )
            
            embed = EmbedBuilder.success(
                "Channel Locked",
                f"{channel.mention} has been locked."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Send lock message to the channel if it's not the current channel
            if channel != interaction.channel:
                lock_embed = EmbedBuilder.warning(
                    "Channel Locked",
                    f"This channel has been locked by {interaction.user.mention}.\n**Reason:** {reason}"
                )
                await channel.send(embed=lock_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to edit channel permissions.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unlock", description="Unlock a previously locked channel")
    @app_commands.describe(
        channel="The channel to unlock",
        reason="Reason for unlocking the channel"
    )
    async def unlock(
        self, 
        interaction: discord.Interaction, 
        channel: Optional[discord.TextChannel] = None,
        reason: str = "No reason provided"
    ):
        """Unlock a channel"""
        if not interaction.user.guild_permissions.manage_channels:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /unlock in {interaction.guild.name} ({interaction.guild.id}) without Manage Channels permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Channels' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        try:
            # Restore send message permission for @everyone
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = None  # Reset to default
            await channel.set_permissions(
                interaction.guild.default_role,
                overwrite=overwrite,
                reason=f"Channel unlocked by {interaction.user} | {reason}"
            )
            
            embed = EmbedBuilder.success(
                "Channel Unlocked",
                f"{channel.mention} has been unlocked."
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Send unlock message to the channel if it's not the current channel
            if channel != interaction.channel:
                unlock_embed = EmbedBuilder.success(
                    "Channel Unlocked",
                    f"This channel has been unlocked by {interaction.user.mention}.\n**Reason:** {reason}"
                )
                await channel.send(embed=unlock_embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to edit channel permissions.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="channels", description="Manage server channels")
    async def channels(self, interaction: discord.Interaction):
        """Interactive channel management"""
        if not interaction.user.guild_permissions.manage_channels:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Channels' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📺 Channel Management",
            description="Use the buttons below to create new channels.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        guild = interaction.guild
        embed.add_field(
            name="Current Channels",
            value=f"**Text:** {len(guild.text_channels)}\n"
                  f"**Voice:** {len(guild.voice_channels)}\n"
                  f"**Categories:** {len(guild.categories)}",
            inline=True
        )
        
        view = ChannelManagerView()
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="createrole", description="Create a new role")
    @app_commands.describe(
        name="Name of the role",
        color="Hex color code (e.g., #ff0000)",
        mentionable="Whether the role should be mentionable",
        hoisted="Whether the role should be displayed separately"
    )
    async def createrole(
        self,
        interaction: discord.Interaction,
        name: str,
        color: Optional[str] = None,
        mentionable: bool = False,
        hoisted: bool = False
    ):
        """Create a new role with customization options"""
        if not interaction.user.guild_permissions.manage_roles:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /createrole in {interaction.guild.name} ({interaction.guild.id}) without Manage Roles permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Roles' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse color
        role_color = discord.Color.default()
        if color:
            try:
                if color.startswith('#'):
                    color = color[1:]
                role_color = discord.Color(int(color, 16))
            except ValueError:
                embed = EmbedBuilder.error("Invalid Color", "Please provide a valid hex color code (e.g., #ff0000).")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        try:
            role = await interaction.guild.create_role(
                name=name,
                color=role_color,
                mentionable=mentionable,
                hoist=hoisted,
                reason=f"Role created by {interaction.user}"
            )
            
            embed = EmbedBuilder.success(
                "Role Created",
                f"Successfully created role {role.mention}!"
            )
            embed.add_field(name="Name", value=role.name, inline=True)
            embed.add_field(name="Color", value=f"#{role.color.value:06x}" if role.color.value else "Default", inline=True)
            embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
            embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
            embed.add_field(name="Created By", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to create roles.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to create role: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="deleterole", description="Delete a role")
    @app_commands.describe(
        role="The role to delete",
        reason="Reason for deleting the role"
    )
    async def deleterole(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        reason: str = "No reason provided"
    ):
        """Delete a role with confirmation"""
        if not interaction.user.guild_permissions.manage_roles:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /deleterole in {interaction.guild.name} ({interaction.guild.id}) without Manage Roles permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Roles' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.error("Role Hierarchy", "You cannot delete a role higher than or equal to your highest role.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if role.managed:
            embed = EmbedBuilder.error("Managed Role", "Cannot delete managed roles (bot roles, booster roles, etc.).")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation dialog
        embed = discord.Embed(
            title="🗑️ Confirm Role Deletion",
            description=f"Are you sure you want to delete the role {role.mention}?",
            color=discord.Color.red()
        )
        embed.add_field(name="Role Name", value=role.name, inline=True)
        embed.add_field(name="Members with Role", value=str(len(role.members)), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        view = ConfirmationView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.warning("Timed Out", "Role deletion confirmation timed out.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        if not view.value:
            embed = EmbedBuilder.info("Cancelled", "Role deletion has been cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        try:
            role_name = role.name
            member_count = len(role.members)
            await role.delete(reason=f"Role deleted by {interaction.user} | {reason}")
            
            embed = EmbedBuilder.success(
                "Role Deleted",
                f"Successfully deleted role **{role_name}**."
            )
            embed.add_field(name="Affected Members", value=str(member_count), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.edit_original_response(embed=embed, view=None)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to delete this role.")
            await interaction.edit_original_response(embed=embed, view=None)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="nick", description="Change a user's nickname")
    @app_commands.describe(
        user="The user to change nickname for",
        nickname="New nickname (leave empty to reset)",
        reason="Reason for nickname change"
    )
    async def nick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        nickname: Optional[str] = None,
        reason: str = "No reason provided"
    ):
        """Change a user's nickname"""
        if not interaction.user.guild_permissions.manage_nicknames:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /nick in {interaction.guild.name} ({interaction.guild.id}) without Manage Nicknames permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Nicknames' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not PermissionChecker.can_moderate(interaction.user, user):
            embed = EmbedBuilder.error("Cannot Moderate", "You cannot modify this user's nickname due to role hierarchy.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        old_nick = user.display_name
        
        try:
            await user.edit(nickname=nickname, reason=f"Nickname changed by {interaction.user} | {reason}")
            
            action = "reset" if nickname is None else "changed"
            new_display = user.display_name
            
            embed = EmbedBuilder.success(
                f"Nickname {action.title()}",
                f"{user.mention}'s nickname has been {action}."
            )
            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Nickname", value=new_display, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to change this user's nickname.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="announcement", description="Create a styled announcement")
    @app_commands.describe(
        title="Title of the announcement",
        message="Content of the announcement",
        channel="Channel to send the announcement to",
        ping_everyone="Whether to ping @everyone"
    )
    async def announcement(
        self,
        interaction: discord.Interaction,
        title: str,
        message: str,
        channel: Optional[discord.TextChannel] = None,
        ping_everyone: bool = False
    ):
        """Create a styled announcement"""
        if not interaction.user.guild_permissions.manage_messages:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /announcement in {interaction.guild.name} ({interaction.guild.id}) without Manage Messages permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Messages' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        # Create announcement embed
        embed = discord.Embed(
            title=f"📢 {title}",
            description=message,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text=f"Announcement by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        try:
            content = "@everyone" if ping_everyone else None
            await channel.send(content=content, embed=embed)
            
            confirm_embed = EmbedBuilder.success(
                "Announcement Sent",
                f"Your announcement has been sent to {channel.mention}."
            )
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to send messages in that channel.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
