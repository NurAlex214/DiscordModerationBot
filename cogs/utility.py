import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, Union, List
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, PaginationView, format_user_info

class RoleManagementView(discord.ui.View):
    """Interactive role management with dropdowns"""
    
    def __init__(self, target_user: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.target_user = target_user
        
        # Create role dropdown (only roles that can be assigned)
        assignable_roles = [
            role for role in target_user.guild.roles 
            if not role.is_default() and not role.managed and role < target_user.guild.me.top_role
        ]
        
        if assignable_roles:
            self.add_item(RoleDropdown(assignable_roles, target_user))

class RoleDropdown(discord.ui.Select):
    """Dropdown for selecting roles to add/remove"""
    
    def __init__(self, roles: List[discord.Role], target_user: discord.Member):
        self.target_user = target_user
        
        options = []
        for role in roles[:25]:  # Discord limit
            has_role = role in target_user.roles
            options.append(discord.SelectOption(
                label=role.name,
                value=str(role.id),
                description=f"{'Remove' if has_role else 'Add'} this role",
                emoji="➖" if has_role else "➕"
            ))
        
        super().__init__(
            placeholder="Select roles to add/remove...",
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_roles:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Roles' permission.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        changes = []
        errors = []
        
        for role_id in self.values:
            role = interaction.guild.get_role(int(role_id))
            if not role:
                continue
            
            try:
                if role in self.target_user.roles:
                    await self.target_user.remove_roles(role, reason=f"Role removed by {interaction.user}")
                    changes.append(f"➖ Removed {role.mention}")
                else:
                    await self.target_user.add_roles(role, reason=f"Role added by {interaction.user}")
                    changes.append(f"➕ Added {role.mention}")
            except discord.Forbidden:
                errors.append(f"❌ Cannot modify {role.mention}")
            except Exception as e:
                errors.append(f"❌ Error with {role.mention}: {str(e)}")
        
        embed = discord.Embed(
            title="🎭 Role Changes",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        if changes:
            embed.add_field(name="Changes Made", value="\n".join(changes), inline=False)
        
        if errors:
            embed.add_field(name="Errors", value="\n".join(errors), inline=False)
        
        await interaction.response.send_message(embed=embed)

class UtilityCog(commands.Cog, name="Utility"):
    """Utility commands for information and server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="userinfo", description="Get detailed information about a user")
    @app_commands.describe(user="The user to get information about")
    async def userinfo(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display comprehensive user information"""
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"👤 User Information: {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Set user avatar
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="📋 Basic Info",
            value=format_user_info(user),
            inline=False
        )
        
        # Member-specific info
        if isinstance(user, discord.Member):
            # Status and activity
            status_emoji = {
                discord.Status.online: "🟢",
                discord.Status.idle: "🟡", 
                discord.Status.dnd: "🔴",
                discord.Status.offline: "⚫"
            }
            
            embed.add_field(
                name="📱 Status",
                value=f"{status_emoji.get(user.status, '❓')} {user.status.name.title()}",
                inline=True
            )
            
            if user.activity:
                activity_type = {
                    discord.ActivityType.playing: "🎮 Playing",
                    discord.ActivityType.streaming: "📺 Streaming",
                    discord.ActivityType.listening: "🎵 Listening to",
                    discord.ActivityType.watching: "👀 Watching",
                    discord.ActivityType.competing: "🏆 Competing in"
                }
                
                embed.add_field(
                    name="🎯 Activity",
                    value=f"{activity_type.get(user.activity.type, '❓')} {user.activity.name}",
                    inline=True
                )
            
            # Roles (top 10)
            if len(user.roles) > 1:
                roles = [role.mention for role in reversed(user.roles[1:])]  # Exclude @everyone
                role_text = ", ".join(roles[:10])
                if len(roles) > 10:
                    role_text += f" and {len(roles) - 10} more..."
                
                embed.add_field(
                    name=f"🎭 Roles ({len(user.roles) - 1})",
                    value=role_text,
                    inline=False
                )
            
            # Permissions (if user has notable permissions)
            notable_perms = []
            if user.guild_permissions.administrator:
                notable_perms.append("Administrator")
            elif user.guild_permissions.manage_guild:
                notable_perms.append("Manage Server")
            elif user.guild_permissions.manage_channels:
                notable_perms.append("Manage Channels")
            elif user.guild_permissions.ban_members:
                notable_perms.append("Ban Members")
            elif user.guild_permissions.kick_members:
                notable_perms.append("Kick Members")
            elif user.guild_permissions.moderate_members:
                notable_perms.append("Moderate Members")
            
            if notable_perms:
                embed.add_field(
                    name="🔑 Key Permissions",
                    value=", ".join(notable_perms),
                    inline=False
                )
        
        # Add footer with user ID
        embed.set_footer(text=f"User ID: {user.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(user="The user to get the avatar of")
    async def avatar(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display user's avatar with download link"""
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {user.display_name}'s Avatar",
            color=user.color if hasattr(user, 'color') and user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Set the avatar as the main image
        avatar_url = user.display_avatar.url
        embed.set_image(url=avatar_url)
        
        # Add download links
        embed.add_field(
            name="🔗 Links",
            value=f"[PNG]({avatar_url}?format=png) | [JPG]({avatar_url}?format=jpg) | [WEBP]({avatar_url}?format=webp)",
            inline=False
        )
        
        # If it's a member and they have a server-specific avatar
        if isinstance(user, discord.Member) and user.avatar != user.display_avatar:
            embed.add_field(
                name="📝 Note",
                value="This user has a server-specific avatar",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Display comprehensive server information"""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🏰 Server Information: {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Server icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(
            name="📋 Basic Info",
            value=f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                  f"**Created:** {discord.utils.format_dt(guild.created_at, style='F')}\n"
                  f"**ID:** {guild.id}\n"
                  f"**Verification Level:** {guild.verification_level.name.title()}",
            inline=False
        )
        
        # Member statistics
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bots = sum(1 for member in guild.members if member.bot)
        
        embed.add_field(
            name="👥 Members",
            value=f"**Total:** {total_members:,}\n"
                  f"**Online:** {online_members:,}\n"
                  f"**Bots:** {bots:,}\n"
                  f"**Humans:** {total_members - bots:,}",
            inline=True
        )
        
        # Channel statistics
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="📺 Channels",
            value=f"**Text:** {text_channels}\n"
                  f"**Voice:** {voice_channels}\n"
                  f"**Categories:** {categories}\n"
                  f"**Total:** {text_channels + voice_channels}",
            inline=True
        )
        
        # Role and emoji info
        embed.add_field(
            name="🎭 Other",
            value=f"**Roles:** {len(guild.roles)}\n"
                  f"**Emojis:** {len(guild.emojis)}\n"
                  f"**Boost Level:** {guild.premium_tier}\n"
                  f"**Boosts:** {guild.premium_subscription_count}",
            inline=True
        )
        
        # Features
        if guild.features:
            features_text = []
            feature_names = {
                'VERIFIED': '✅ Verified',
                'PARTNERED': '🤝 Partnered',
                'COMMUNITY': '🌐 Community',
                'DISCOVERABLE': '🔍 Discoverable',
                'BANNER': '🖼️ Banner',
                'VANITY_URL': '🔗 Vanity URL',
                'ANIMATED_ICON': '🎬 Animated Icon',
                'INVITE_SPLASH': '🌊 Invite Splash'
            }
            
            for feature in guild.features:
                if feature in feature_names:
                    features_text.append(feature_names[feature])
            
            if features_text:
                embed.add_field(
                    name="⭐ Features",
                    value="\n".join(features_text[:10]),
                    inline=False
                )
        
        # Server banner
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="roles", description="Manage roles for a user")
    @app_commands.describe(user="The user to manage roles for")
    async def roles(self, interaction: discord.Interaction, user: discord.Member):
        """Interactive role management"""
        if not interaction.user.guild_permissions.manage_roles:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Roles' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎭 Role Management: {user.display_name}",
            description="Use the dropdown below to add or remove roles.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Show current roles
        current_roles = [role.mention for role in user.roles if not role.is_default()]
        if current_roles:
            embed.add_field(
                name=f"Current Roles ({len(current_roles)})",
                value=", ".join(current_roles[:10]) + ("..." if len(current_roles) > 10 else ""),
                inline=False
            )
        else:
            embed.add_field(name="Current Roles", value="No roles assigned", inline=False)
        
        view = RoleManagementView(user)
        await interaction.response.send_message(embed=embed, view=view)
    
    
    
    @app_commands.command(name="botinfo", description="Get information about the bot")
    async def botinfo(self, interaction: discord.Interaction):
        """Display bot information and statistics"""
        bot = self.bot
        
        embed = discord.Embed(
            title=f"🤖 Bot Information: {bot.user.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        # Basic bot info
        embed.add_field(
            name="📋 Basic Info",
            value=f"**Version:** discord.py {discord.__version__}\n"
                  f"**Created:** {discord.utils.format_dt(bot.user.created_at, style='F')}\n"
                  f"**ID:** {bot.user.id}",
            inline=False
        )
        
        # Statistics
        total_members = sum(guild.member_count for guild in bot.guilds)
        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {len(bot.guilds):,}\n"
                  f"**Users:** {total_members:,}\n"
                  f"**Commands:** {len(bot.tree.get_commands())}",
            inline=True
        )
        
        # System info (optional psutil)
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            embed.add_field(
                name="⚙️ System",
                value=f"**Memory:** {memory_usage:.1f} MB\n"
                      f"**CPU:** {process.cpu_percent():.1f}%\n"
                      f"**Uptime:** {discord.utils.format_dt(datetime.fromtimestamp(process.create_time()), style='R')}",
                inline=True
            )
        except ImportError:
            embed.add_field(
                name="⚙️ System",
                value="System info unavailable\n(psutil not installed)",
                inline=True
            )
        
        # Permissions in current guild
        bot_member = interaction.guild.me
        important_perms = []
        
        perms_check = {
            'administrator': 'Administrator',
            'manage_guild': 'Manage Server',
            'ban_members': 'Ban Members',
            'kick_members': 'Kick Members',
            'moderate_members': 'Moderate Members',
            'manage_channels': 'Manage Channels',
            'manage_roles': 'Manage Roles',
            'view_audit_log': 'View Audit Log'
        }
        
        for perm, name in perms_check.items():
            if getattr(bot_member.guild_permissions, perm):
                important_perms.append(f"✅ {name}")
            else:
                important_perms.append(f"❌ {name}")
        
        embed.add_field(
            name="🔑 Permissions (This Server)",
            value="\n".join(important_perms),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        """Display bot latency information"""
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        # Websocket latency
        ws_latency = round(self.bot.latency * 1000, 2)
        
        embed.add_field(
            name="📡 WebSocket Latency",
            value=f"{ws_latency}ms",
            inline=True
        )
        
        # API latency (measure response time)
        start_time = datetime.utcnow()
        await interaction.response.send_message(embed=embed)
        end_time = datetime.utcnow()
        
        api_latency = round((end_time - start_time).total_seconds() * 1000, 2)
        
        embed.add_field(
            name="🔗 API Latency",
            value=f"{api_latency}ms",
            inline=True
        )
        
        # Color code based on latency
        avg_latency = (ws_latency + api_latency) / 2
        if avg_latency < 100:
            embed.color = discord.Color.green()
        elif avg_latency < 200:
            embed.color = discord.Color.yellow()
        else:
            embed.color = discord.Color.red()
        
        await interaction.edit_original_response(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
