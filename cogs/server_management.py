import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Literal
import asyncio
import sys
import os
import io

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, ConfirmationView, time_to_seconds

class ServerManagementCog(commands.Cog, name="Server Management"):
    """Advanced server management and administration commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="createchannel", description="Create a new channel")
    @app_commands.describe(
        name="Channel name",
        channel_type="Type of channel to create",
        category="Category to create the channel in",
        reason="Reason for creating the channel"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="Text Channel", value="text"),
        app_commands.Choice(name="Voice Channel", value="voice"),
        app_commands.Choice(name="Forum Channel", value="forum"),
        app_commands.Choice(name="Stage Channel", value="stage")
    ])
    async def create_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        channel_type: Literal["text", "voice", "forum", "stage"],
        category: Optional[discord.CategoryChannel] = None,
        reason: Optional[str] = None
    ):
        """Create a new channel"""
        if not interaction.user.guild_permissions.manage_channels:
            embed = EmbedBuilder.no_permission("You need the **Manage Channels** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            if channel_type == "text":
                channel = await interaction.guild.create_text_channel(
                    name=name,
                    category=category,
                    reason=reason or f"Channel created by {interaction.user}"
                )
            elif channel_type == "voice":
                channel = await interaction.guild.create_voice_channel(
                    name=name,
                    category=category,
                    reason=reason or f"Channel created by {interaction.user}"
                )
            elif channel_type == "forum":
                channel = await interaction.guild.create_forum_channel(
                    name=name,
                    category=category,
                    reason=reason or f"Channel created by {interaction.user}"
                )
            elif channel_type == "stage":
                channel = await interaction.guild.create_stage_channel(
                    name=name,
                    category=category,
                    reason=reason or f"Channel created by {interaction.user}"
                )
            
            embed = EmbedBuilder.success(
                "Channel Created",
                f"Successfully created {channel_type} channel {channel.mention}"
            )
            
            if category:
                embed.add_field(name="📁 Category", value=category.name, inline=True)
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to create channels!")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to create channel: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="deletechannel", description="Delete a channel")
    @app_commands.describe(
        channel="Channel to delete",
        reason="Reason for deleting the channel"
    )
    async def delete_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel,
        reason: Optional[str] = None
    ):
        """Delete a channel with confirmation"""
        if not interaction.user.guild_permissions.manage_channels:
            embed = EmbedBuilder.no_permission("You need the **Manage Channels** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚠️ Confirm Channel Deletion",
            description=f"Are you sure you want to delete {channel.mention}?\\n\\n**This action cannot be undone!**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        if reason:
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        
        view = ConfirmationView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.error("Timeout", "Channel deletion cancelled due to timeout.")
            await interaction.edit_original_response(embed=embed, view=None)
        elif view.value:
            try:
                channel_name = channel.name
                await channel.delete(reason=reason or f"Channel deleted by {interaction.user}")
                
                embed = EmbedBuilder.success(
                    "Channel Deleted",
                    f"Successfully deleted channel **#{channel_name}**"
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
            except discord.Forbidden:
                embed = EmbedBuilder.error("Permission Error", "I don't have permission to delete that channel!")
                await interaction.edit_original_response(embed=embed, view=None)
            except Exception as e:
                embed = EmbedBuilder.error("Error", f"Failed to delete channel: {str(e)}")
                await interaction.edit_original_response(embed=embed, view=None)
        else:
            embed = EmbedBuilder.warning("Cancelled", "Channel deletion cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="newrole", description="Create a new role")
    @app_commands.describe(
        name="Role name",
        color="Role color (hex code)",
        hoist="Whether the role should be displayed separately",
        mentionable="Whether the role should be mentionable",
        reason="Reason for creating the role"
    )
    async def create_role(
        self,
        interaction: discord.Interaction,
        name: str,
        color: Optional[str] = None,
        hoist: Optional[bool] = False,
        mentionable: Optional[bool] = False,
        reason: Optional[str] = None
    ):
        """Create a new role"""
        if not interaction.user.guild_permissions.manage_roles:
            embed = EmbedBuilder.no_permission("You need the **Manage Roles** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Parse color if provided
        role_color = discord.Color.default()
        if color:
            color = color.strip().replace('#', '')
            if len(color) == 6 and all(c in '0123456789ABCDEFabcdef' for c in color):
                try:
                    role_color = discord.Color(int(color, 16))
                except:
                    pass
        
        try:
            role = await interaction.guild.create_role(
                name=name,
                color=role_color,
                hoist=hoist,
                mentionable=mentionable,
                reason=reason or f"Role created by {interaction.user}"
            )
            
            embed = EmbedBuilder.success(
                "Role Created",
                f"Successfully created role {role.mention}"
            )
            
            embed.add_field(name="🎨 Color", value=f"`#{role.color.value:06x}`", inline=True)
            embed.add_field(name="📋 Hoist", value="Yes" if hoist else "No", inline=True)
            embed.add_field(name="💬 Mentionable", value="Yes" if mentionable else "No", inline=True)
            
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to create roles!")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to create role: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="removerole", description="Delete a role")
    @app_commands.describe(
        role="Role to delete",
        reason="Reason for deleting the role"
    )
    async def delete_role(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        reason: Optional[str] = None
    ):
        """Delete a role with confirmation"""
        if not interaction.user.guild_permissions.manage_roles:
            embed = EmbedBuilder.no_permission("You need the **Manage Roles** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            embed = EmbedBuilder.error("Permission Error", "You can only delete roles lower than your highest role!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if role.is_default():
            embed = EmbedBuilder.error("Invalid Role", "You cannot delete the @everyone role!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚠️ Confirm Role Deletion",
            description=f"Are you sure you want to delete {role.mention}?\\n\\n**This action cannot be undone!**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="👥 Members", value=f"{len(role.members)} members have this role", inline=True)
        
        if reason:
            embed.add_field(name="📝 Reason", value=reason, inline=False)
        
        view = ConfirmationView(interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        await view.wait()
        
        if view.value is None:
            embed = EmbedBuilder.error("Timeout", "Role deletion cancelled due to timeout.")
            await interaction.edit_original_response(embed=embed, view=None)
        elif view.value:
            try:
                role_name = role.name
                await role.delete(reason=reason or f"Role deleted by {interaction.user}")
                
                embed = EmbedBuilder.success(
                    "Role Deleted",
                    f"Successfully deleted role **{role_name}**"
                )
                await interaction.edit_original_response(embed=embed, view=None)
                
            except discord.Forbidden:
                embed = EmbedBuilder.error("Permission Error", "I don't have permission to delete that role!")
                await interaction.edit_original_response(embed=embed, view=None)
            except Exception as e:
                embed = EmbedBuilder.error("Error", f"Failed to delete role: {str(e)}")
                await interaction.edit_original_response(embed=embed, view=None)
        else:
            embed = EmbedBuilder.warning("Cancelled", "Role deletion cancelled.")
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name="cleanup", description="Clean up bot messages")
    @app_commands.describe(
        amount="Number of messages to check (max 100)",
        user="Only delete messages from this user"
    )
    async def cleanup(
        self,
        interaction: discord.Interaction,
        amount: int = 10,
        user: Optional[discord.Member] = None
    ):
        """Clean up bot messages"""
        if not interaction.user.guild_permissions.manage_messages:
            embed = EmbedBuilder.no_permission("You need the **Manage Messages** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount > 100:
            embed = EmbedBuilder.error("Invalid Amount", "You can only check up to 100 messages at once!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            messages_to_delete = []
            async for message in interaction.channel.history(limit=amount):
                if user and message.author != user:
                    continue
                if message.author.bot:
                    messages_to_delete.append(message)
            
            if not messages_to_delete:
                embed = EmbedBuilder.warning("No Messages", "No bot messages found to delete!")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Delete messages
            if len(messages_to_delete) == 1:
                await messages_to_delete[0].delete()
            else:
                await interaction.channel.delete_messages(messages_to_delete)
            
            embed = EmbedBuilder.success(
                "Messages Cleaned",
                f"Successfully deleted {len(messages_to_delete)} bot message(s)"
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to delete messages!")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to clean up messages: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="viewemojis", description="View all server emojis")
    async def view_emojis(self, interaction: discord.Interaction):
        """View all server emojis in a paginated embed"""
        if not interaction.guild.emojis:
            embed = EmbedBuilder.warning("No Emojis", "This server doesn't have any custom emojis!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create paginated view
        view = EmojiPaginationView(interaction.guild.emojis, interaction.user)
        embed = view.create_embed()
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="roleinfo", description="Get detailed information about a role")
    @app_commands.describe(role="The role to get information about")
    async def role_info(self, interaction: discord.Interaction, role: discord.Role):
        """Get detailed information about a role"""
        embed = discord.Embed(
            title=f"📋 Role Information: {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="🆔 ID", value=f"`{role.id}`", inline=True)
        embed.add_field(name="🎨 Color", value=f"`#{role.color.value:06x}`", inline=True)
        embed.add_field(name="📍 Position", value=f"{role.position}", inline=True)
        
        # Role properties
        embed.add_field(name="📋 Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="💬 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="🤖 Bot Role", value="Yes" if role.is_bot_managed() else "No", inline=True)
        
        # Members
        embed.add_field(name="👥 Members", value=f"{len(role.members)}", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🔧 Managed", value="Yes" if role.managed else "No", inline=True)
        
        # Permissions
        key_perms = []
        if role.permissions.administrator:
            key_perms.append("Administrator")
        if role.permissions.manage_guild:
            key_perms.append("Manage Server")
        if role.permissions.manage_roles:
            key_perms.append("Manage Roles")
        if role.permissions.manage_channels:
            key_perms.append("Manage Channels")
        if role.permissions.ban_members:
            key_perms.append("Ban Members")
        if role.permissions.kick_members:
            key_perms.append("Kick Members")
        
        if key_perms:
            embed.add_field(
                name="🔑 Key Permissions",
                value="\\n".join(f"• {perm}" for perm in key_perms[:10]),
                inline=False
            )
        
        # Show some members if any
        if role.members:
            member_list = [member.mention for member in role.members[:5]]
            if len(role.members) > 5:
                member_list.append(f"... and {len(role.members) - 5} more")
            
            embed.add_field(
                name="👥 Some Members",
                value="\\n".join(member_list),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="channelinfo", description="Get detailed information about a channel")
    @app_commands.describe(channel="The channel to get information about")
    async def channel_info(self, interaction: discord.Interaction, channel: Optional[discord.abc.GuildChannel] = None):
        """Get detailed information about a channel"""
        target_channel = channel or interaction.channel
        
        embed = discord.Embed(
            title=f"📺 Channel Information: #{target_channel.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Basic info
        embed.add_field(name="🆔 ID", value=f"`{target_channel.id}`", inline=True)
        embed.add_field(name="🏷️ Type", value=str(target_channel.type).title(), inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(target_channel.created_at.timestamp())}:R>", inline=True)
        
        # Category
        if hasattr(target_channel, 'category') and target_channel.category:
            embed.add_field(name="📁 Category", value=target_channel.category.name, inline=True)
        
        # Position
        if hasattr(target_channel, 'position'):
            embed.add_field(name="📍 Position", value=f"{target_channel.position}", inline=True)
        
        # Text channel specific info
        if isinstance(target_channel, discord.TextChannel):
            embed.add_field(name="🔞 NSFW", value="Yes" if target_channel.nsfw else "No", inline=True)
            
            if target_channel.topic:
                embed.add_field(name="📝 Topic", value=target_channel.topic[:100], inline=False)
            
            if target_channel.slowmode_delay:
                embed.add_field(name="⏱️ Slowmode", value=f"{target_channel.slowmode_delay}s", inline=True)
        
        # Voice channel specific info
        elif isinstance(target_channel, discord.VoiceChannel):
            embed.add_field(name="👥 User Limit", value=f"{target_channel.user_limit or 'No limit'}", inline=True)
            embed.add_field(name="🔊 Bitrate", value=f"{target_channel.bitrate // 1000}kbps", inline=True)
            
            if target_channel.members:
                embed.add_field(name="🎧 Connected", value=f"{len(target_channel.members)} members", inline=True)
        
        # Permission overwrites
        overwrites = len(target_channel.overwrites)
        if overwrites > 0:
            embed.add_field(name="🔒 Permission Overwrites", value=f"{overwrites}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="inviteinfo", description="Get information about an invite")
    @app_commands.describe(invite="The invite code or URL")
    async def invite_info(self, interaction: discord.Interaction, invite: str):
        """Get information about a Discord invite"""
        await interaction.response.defer()
        
        try:
            # Clean the invite code
            invite_code = invite.split('/')[-1]
            discord_invite = await self.bot.fetch_invite(invite_code)
            
            embed = discord.Embed(
                title="📨 Invite Information",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            # Server info
            embed.add_field(name="🏠 Server", value=discord_invite.guild.name, inline=True)
            embed.add_field(name="🆔 Server ID", value=f"`{discord_invite.guild.id}`", inline=True)
            embed.add_field(name="👥 Members", value=f"~{discord_invite.approximate_member_count}", inline=True)
            
            # Channel info
            embed.add_field(name="📺 Channel", value=f"#{discord_invite.channel.name}", inline=True)
            embed.add_field(name="🏷️ Channel Type", value=str(discord_invite.channel.type).title(), inline=True)
            embed.add_field(name="🟢 Online", value=f"~{discord_invite.approximate_presence_count}", inline=True)
            
            # Invite details
            if discord_invite.inviter:
                embed.add_field(name="👤 Inviter", value=discord_invite.inviter.mention, inline=True)
            
            if discord_invite.created_at:
                embed.add_field(name="📅 Created", value=f"<t:{int(discord_invite.created_at.timestamp())}:R>", inline=True)
            
            if discord_invite.expires_at:
                embed.add_field(name="⏰ Expires", value=f"<t:{int(discord_invite.expires_at.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="⏰ Expires", value="Never", inline=True)
            
            if discord_invite.max_uses:
                embed.add_field(name="🔢 Max Uses", value=f"{discord_invite.uses}/{discord_invite.max_uses}", inline=True)
            else:
                embed.add_field(name="🔢 Uses", value=f"{discord_invite.uses or 0}/∞", inline=True)
            
            # Server icon
            if discord_invite.guild.icon:
                embed.set_thumbnail(url=discord_invite.guild.icon.url)
            
            await interaction.followup.send(embed=embed)
            
        except discord.NotFound:
            embed = EmbedBuilder.error("Invalid Invite", "The invite code is invalid or has expired!")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to fetch invite information: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="createinvite", description="Create an invite for the current channel")
    @app_commands.describe(
        max_age="How long the invite should last (e.g., '1h', '30m', '1d')",
        max_uses="Maximum number of uses (0 for unlimited)",
        temporary="Whether members should be kicked when they disconnect if they have no roles",
        reason="Reason for creating the invite"
    )
    async def create_invite(
        self,
        interaction: discord.Interaction,
        max_age: Optional[str] = None,
        max_uses: Optional[int] = 0,
        temporary: Optional[bool] = False,
        reason: Optional[str] = None
    ):
        """Create an invite for the current channel"""
        if not interaction.user.guild_permissions.create_instant_invite:
            embed = EmbedBuilder.no_permission("You need the **Create Instant Invite** permission to use this command!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse max_age
        age_seconds = 0  # 0 means never expires
        if max_age:
            try:
                age_seconds = time_to_seconds(max_age)
                if age_seconds > 604800:  # Discord's max is 7 days
                    age_seconds = 604800
            except:
                embed = EmbedBuilder.error("Invalid Time", "Invalid time format! Use formats like '1h', '30m', '1d'")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        try:
            invite = await interaction.channel.create_invite(
                max_age=age_seconds,
                max_uses=max_uses or 0,
                temporary=temporary,
                reason=reason or f"Invite created by {interaction.user}"
            )
            
            embed = discord.Embed(
                title="📨 Invite Created",
                description=f"**Invite URL:** {invite.url}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="📺 Channel", value=interaction.channel.mention, inline=True)
            embed.add_field(name="🔢 Max Uses", value=f"{max_uses or 'Unlimited'}", inline=True)
            
            if age_seconds > 0:
                expires_at = datetime.utcnow() + timedelta(seconds=age_seconds)
                embed.add_field(name="⏰ Expires", value=f"<t:{int(expires_at.timestamp())}:R>", inline=True)
            else:
                embed.add_field(name="⏰ Expires", value="Never", inline=True)
            
            embed.add_field(name="🔄 Temporary", value="Yes" if temporary else "No", inline=True)
            
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to create invites!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"Failed to create invite: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="backup", description="Create a backup of server settings")
    async def backup_server(self, interaction: discord.Interaction):
        """Create a backup of server settings (channels, roles, etc.)"""
        if not interaction.user.guild_permissions.administrator:
            embed = EmbedBuilder.no_permission("You need **Administrator** permissions to backup server settings!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild = interaction.guild
            backup_data = {
                "server_name": guild.name,
                "server_id": guild.id,
                "backup_time": datetime.utcnow().isoformat(),
                "channels": [],
                "roles": [],
                "categories": []
            }
            
            # Backup categories
            for category in guild.categories:
                backup_data["categories"].append({
                    "name": category.name,
                    "position": category.position,
                    "id": category.id
                })
            
            # Backup channels
            for channel in guild.channels:
                channel_data = {
                    "name": channel.name,
                    "type": str(channel.type),
                    "position": getattr(channel, 'position', 0),
                    "id": channel.id,
                    "category": channel.category.name if hasattr(channel, 'category') and channel.category else None
                }
                
                if isinstance(channel, discord.TextChannel):
                    channel_data.update({
                        "topic": channel.topic,
                        "nsfw": channel.nsfw,
                        "slowmode": channel.slowmode_delay
                    })
                elif isinstance(channel, discord.VoiceChannel):
                    channel_data.update({
                        "bitrate": channel.bitrate,
                        "user_limit": channel.user_limit
                    })
                
                backup_data["channels"].append(channel_data)
            
            # Backup roles (excluding @everyone and bot roles)
            for role in guild.roles:
                if not role.is_default() and not role.is_bot_managed():
                    backup_data["roles"].append({
                        "name": role.name,
                        "color": role.color.value,
                        "hoist": role.hoist,
                        "mentionable": role.mentionable,
                        "position": role.position,
                        "permissions": role.permissions.value
                    })
            
            # Create backup file
            import json
            backup_json = json.dumps(backup_data, indent=2)
            backup_file = discord.File(
                io.StringIO(backup_json),
                filename=f"backup_{guild.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            embed = EmbedBuilder.success(
                "Backup Created",
                f"Server backup created successfully!\\n\\n"
                f"📊 **Backed up:**\\n"
                f"• {len(backup_data['channels'])} channels\\n"
                f"• {len(backup_data['roles'])} roles\\n"
                f"• {len(backup_data['categories'])} categories"
            )
            
            embed.add_field(
                name="⚠️ Note",
                value="This backup contains server structure only. Messages, members, and permissions are not included.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, file=backup_file, ephemeral=True)
            
        except Exception as e:
            embed = EmbedBuilder.error("Backup Failed", f"Failed to create backup: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="serverstats", description="Show detailed member statistics")
    async def member_count(self, interaction: discord.Interaction):
        """Show detailed member statistics"""
        guild = interaction.guild
        
        # Count members by status
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # Count bots vs humans
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Member Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Total members
        embed.add_field(
            name="👥 Total Members",
            value=f"**{guild.member_count}**",
            inline=True
        )
        
        # Member types
        embed.add_field(
            name="🤖 Breakdown",
            value=f"👤 Humans: **{humans}**\\n🤖 Bots: **{bots}**",
            inline=True
        )
        
        # Status breakdown
        embed.add_field(
            name="📶 Status",
            value=f"🟢 Online: **{online}**\\n🟡 Idle: **{idle}**\\n🔴 DND: **{dnd}**\\n⚫ Offline: **{offline}**",
            inline=True
        )
        
        # Server boost info
        if guild.premium_subscription_count > 0:
            embed.add_field(
                name="💎 Server Boosts",
                value=f"**{guild.premium_subscription_count}** boosts\\nTier **{guild.premium_tier}**",
                inline=True
            )
        
        # Member milestones
        milestones = []
        if guild.member_count >= 1000:
            milestones.append("🎉 1K+ Members!")
        if guild.member_count >= 5000:
            milestones.append("🚀 5K+ Members!")
        if guild.member_count >= 10000:
            milestones.append("⭐ 10K+ Members!")
        
        if milestones:
            embed.add_field(name="🏆 Milestones", value="\\n".join(milestones), inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await interaction.response.send_message(embed=embed)

class EmojiPaginationView(discord.ui.View):
    """Pagination view for server emojis"""
    
    def __init__(self, emojis: list, user: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.emojis = emojis
        self.user = user
        self.current_page = 0
        self.per_page = 20
        self.max_pages = (len(emojis) - 1) // self.per_page + 1
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= self.max_pages - 1
    
    def create_embed(self) -> discord.Embed:
        """Create embed for current page"""
        start_idx = self.current_page * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.emojis))
        page_emojis = self.emojis[start_idx:end_idx]
        
        embed = discord.Embed(
            title=f"😀 Server Emojis ({len(self.emojis)} total)",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        # Create emoji display
        emoji_text = ""
        for i, emoji in enumerate(page_emojis):
            emoji_text += f"{emoji} `:{emoji.name}:` (ID: {emoji.id})\\n"
        
        if emoji_text:
            embed.description = emoji_text
        
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{self.max_pages} • Requested by {self.user.display_name}",
            icon_url=self.user.display_avatar.url
        )
        
        return embed
    
    @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.grey)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            embed = EmbedBuilder.error("Not For You", "This pagination is not for you!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.current_page -= 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='▶️ Next', style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            embed = EmbedBuilder.error("Not For You", "This pagination is not for you!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.current_page += 1
        self.update_buttons()
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(ServerManagementCog(bot))
