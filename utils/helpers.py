import discord
from datetime import datetime, timedelta
import re
from typing import Optional, Union

class EmbedBuilder:
    """Helper class for creating consistent embeds"""
    
    @staticmethod
    def success(title: str, description: str = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def error(title: str, description: str = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def warning(title: str, description: str = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def info(title: str, description: str = None) -> discord.Embed:
        embed = discord.Embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def no_permission(description: str) -> discord.Embed:
        embed = discord.Embed(
            title="❌ Missing Permissions",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        return embed
    
    @staticmethod
    def moderation_log(action: str, target: Union[discord.Member, discord.User], 
                      moderator: Union[discord.Member, discord.User], 
                      reason: str = "No reason provided") -> discord.Embed:
        embed = discord.Embed(
            title=f"🔨 Moderation Action: {action.title()}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Target",
            value=f"{target.mention} ({target.id})",
            inline=True
        )
        
        embed.add_field(
            name="Moderator",
            value=f"{moderator.mention} ({moderator.id})",
            inline=True
        )
        
        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )
        
        if hasattr(target, 'avatar') and target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        return embed

class ConfirmationView(discord.ui.View):
    """Interactive confirmation dialog with buttons"""
    
    def __init__(self, user: Optional[discord.Member] = None, *, timeout=180):
        super().__init__(timeout=timeout)
        self.value = None
        self.user = user
    
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.danger, emoji='✅')
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.secondary, emoji='❌')
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

class PaginationView(discord.ui.View):
    """Pagination system for long lists"""
    
    def __init__(self, embeds: list, *, timeout=300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.max_pages = len(embeds)
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        self.first_page.disabled = self.current_page == 0
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == self.max_pages - 1
        self.last_page.disabled = self.current_page == self.max_pages - 1
    
    @discord.ui.button(label='⏪', style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label='◀️', style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label='▶️', style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label='⏩', style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.max_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

class TimeConverter:
    """Convert time strings to timedelta objects"""
    
    time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d|w|y))+?")
    time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400, "w": 604800, "y": 31536000}
    
    @classmethod
    def convert(cls, time_str: str) -> Optional[timedelta]:
        """Convert time string like '1d2h30m' to timedelta"""
        try:
            matches = cls.time_regex.findall(time_str.lower())
            if not matches:
                return None
            
            total_seconds = 0
            for value, unit in matches:
                total_seconds += int(value) * cls.time_dict[unit]
            
            return timedelta(seconds=total_seconds)
        except:
            return None

class PermissionChecker:
    """Helper class for checking permissions"""
    
    @staticmethod
    def can_moderate(member: discord.Member, target: discord.Member) -> bool:
        """Check if member can moderate target"""
        if member.guild_permissions.administrator:
            return True
        
        if member.top_role <= target.top_role:
            return False
        
        return member.guild_permissions.moderate_members
    
    @staticmethod
    def can_ban(member: discord.Member) -> bool:
        """Check if member can ban"""
        return member.guild_permissions.ban_members or member.guild_permissions.administrator
    
    @staticmethod
    def can_kick(member: discord.Member) -> bool:
        """Check if member can kick"""
        return member.guild_permissions.kick_members or member.guild_permissions.administrator
    
    @staticmethod
    def can_manage_roles(member: discord.Member) -> bool:
        """Check if member can manage roles"""
        return member.guild_permissions.manage_roles or member.guild_permissions.administrator
    
    @staticmethod
    def can_manage_channels(member: discord.Member) -> bool:
        """Check if member can manage channels"""
        return member.guild_permissions.manage_channels or member.guild_permissions.administrator

def format_duration(duration: timedelta) -> str:
    """Format timedelta to human readable string"""
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = total_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"

def format_user_info(user: Union[discord.Member, discord.User]) -> str:
    """Format user information for embeds"""
    info = f"**Username:** {user.name}\n"
    info += f"**ID:** {user.id}\n"
    info += f"**Created:** {discord.utils.format_dt(user.created_at, style='F')}\n"
    
    if isinstance(user, discord.Member):
        info += f"**Joined:** {discord.utils.format_dt(user.joined_at, style='F')}\n"
        if user.premium_since:
            info += f"**Boosting Since:** {discord.utils.format_dt(user.premium_since, style='F')}\n"
    
    return info

def time_to_seconds(time_str: str) -> int:
    """Convert time string like '1h30m' to seconds"""
    time_regex = re.compile(r'(?:(\d{1,5})(h|s|m|d|w|y))+?')
    time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400, "w": 604800, "y": 31536000}
    
    matches = time_regex.findall(time_str.lower())
    if not matches:
        raise ValueError("Invalid time format")
    
    total_seconds = 0
    for value, unit in matches:
        total_seconds += int(value) * time_dict[unit]
    
    return total_seconds
