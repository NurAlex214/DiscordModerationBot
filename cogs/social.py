import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import random
import aiohttp
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder

class SocialCog(commands.Cog, name="Social Interactions"):
    """Social interaction commands for fun user interactions"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # GIF URLs for different actions (you can replace these with your own API)
        self.action_gifs = {
            'hug': [
                "https://tenor.com/view/hug-anime-gif-9158549",
                "https://tenor.com/view/anime-hug-gif-14918285",
                "https://tenor.com/view/hug-anime-wholesome-gif-17194395"
            ],
            'kiss': [
                "https://tenor.com/view/anime-kiss-gif-13314327",
                "https://tenor.com/view/kiss-anime-cute-gif-12644561"
            ],
            'slap': [
                "https://tenor.com/view/anime-slap-mad-gif-17544936",
                "https://tenor.com/view/slap-anime-angry-gif-15789123"
            ],
            'pat': [
                "https://tenor.com/view/anime-pat-head-gif-14358509",
                "https://tenor.com/view/pat-anime-wholesome-gif-16789234"
            ],
            'poke': [
                "https://tenor.com/view/anime-poke-cute-gif-13456789",
                "https://tenor.com/view/poke-anime-playful-gif-15678901"
            ]
        }
    
    async def create_interaction_embed(self, action: str, user: discord.Member, target: discord.Member) -> discord.Embed:
        """Create an embed for social interactions"""
        action_messages = {
            'hug': f"{user.mention} hugs {target.mention}! 🤗",
            'kiss': f"{user.mention} kisses {target.mention}! 😘",
            'slap': f"{user.mention} slaps {target.mention}! 👋",
            'pat': f"{user.mention} pats {target.mention}! 😊",
            'poke': f"{user.mention} pokes {target.mention}! 👉",
            'cuddle': f"{user.mention} cuddles with {target.mention}! 🥰",
            'tickle': f"{user.mention} tickles {target.mention}! 😆",
            'bite': f"{user.mention} bites {target.mention}! 😈",
            'punch': f"{user.mention} punches {target.mention}! 👊",
            'highfive': f"{user.mention} high-fives {target.mention}! ✋"
        }
        
        embed = discord.Embed(
            title=f"💫 {action.title()} Interaction",
            description=action_messages.get(action, f"{user.mention} {action}s {target.mention}!"),
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text=f"Interaction by {user.display_name}",
            icon_url=user.display_avatar.url
        )
        
        # Set random GIF if available
        if action in self.action_gifs:
            gif_url = random.choice(self.action_gifs[action])
            embed.set_image(url=gif_url)
        
        return embed
    
    @app_commands.command(name="hug", description="Give someone a warm hug")
    @app_commands.describe(user="The user to hug")
    async def hug(self, interaction: discord.Interaction, user: discord.Member):
        """Give someone a hug"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="🤗 Self Hug",
                description=f"{interaction.user.mention} hugs themselves! Everyone needs self-love! 💕",
                color=discord.Color.pink(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("hug", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="kiss", description="Give someone a kiss")
    @app_commands.describe(user="The user to kiss")
    async def kiss(self, interaction: discord.Interaction, user: discord.Member):
        """Give someone a kiss"""
        if user.id == interaction.user.id:
            embed = EmbedBuilder.warning("Self Kiss", "You can't kiss yourself! Find someone else! 😅")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = await self.create_interaction_embed("kiss", interaction.user, user)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="slap", description="Slap someone (playfully)")
    @app_commands.describe(user="The user to slap")
    async def slap(self, interaction: discord.Interaction, user: discord.Member):
        """Playfully slap someone"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="🤔 Self Slap",
                description=f"{interaction.user.mention} slaps themselves! That's... unusual! 😵",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("slap", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pat", description="Pat someone on the head")
    @app_commands.describe(user="The user to pat")
    async def pat(self, interaction: discord.Interaction, user: discord.Member):
        """Pat someone on the head"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="😊 Self Pat",
                description=f"{interaction.user.mention} pats themselves! Good job! 👏",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("pat", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="poke", description="Poke someone to get their attention")
    @app_commands.describe(user="The user to poke")
    async def poke(self, interaction: discord.Interaction, user: discord.Member):
        """Poke someone"""
        if user.id == interaction.user.id:
            embed = EmbedBuilder.warning("Self Poke", "Poking yourself won't get anyone's attention! 😄")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = await self.create_interaction_embed("poke", interaction.user, user)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="cuddle", description="Cuddle with someone")
    @app_commands.describe(user="The user to cuddle with")
    async def cuddle(self, interaction: discord.Interaction, user: discord.Member):
        """Cuddle with someone"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="🥰 Self Cuddle",
                description=f"{interaction.user.mention} cuddles with a pillow! So cozy! 🛋️",
                color=discord.Color.pink(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("cuddle", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="tickle", description="Tickle someone")
    @app_commands.describe(user="The user to tickle")
    async def tickle(self, interaction: discord.Interaction, user: discord.Member):
        """Tickle someone"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="😆 Self Tickle",
                description=f"{interaction.user.mention} tries to tickle themselves! It doesn't work the same way! 🤭",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("tickle", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="bite", description="Playfully bite someone")
    @app_commands.describe(user="The user to bite")
    async def bite(self, interaction: discord.Interaction, user: discord.Member):
        """Playfully bite someone"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="😈 Self Bite",
                description=f"{interaction.user.mention} bites themselves! Ouch! 🩹",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("bite", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="punch", description="Punch someone (playfully)")
    @app_commands.describe(user="The user to punch")
    async def punch(self, interaction: discord.Interaction, user: discord.Member):
        """Playfully punch someone"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="👊 Self Punch",
                description=f"{interaction.user.mention} punches themselves! Why would you do that?! 😵",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("punch", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="highfive", description="Give someone a high five")
    @app_commands.describe(user="The user to high five")
    async def highfive(self, interaction: discord.Interaction, user: discord.Member):
        """Give someone a high five"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="✋ Self High Five",
                description=f"{interaction.user.mention} high-fives the air! *whoosh* 💨",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = await self.create_interaction_embed("highfive", interaction.user, user)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="marry", description="Propose marriage to someone")
    @app_commands.describe(user="The user to propose to")
    async def marry(self, interaction: discord.Interaction, user: discord.Member):
        """Propose marriage to someone"""
        if user.bot:
            embed = EmbedBuilder.error("Invalid Target", "You can't marry bots! They don't have feelings! 🤖")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            embed = EmbedBuilder.warning("Self Marriage", "You can't marry yourself! That's not how it works! 😅")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💒 Marriage Proposal",
            description=f"{interaction.user.mention} proposes to {user.mention}! 💍\\n\\nWill you accept?",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        
        view = MarriageProposalView(interaction.user, user)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="compliment", description="Give someone a compliment")
    @app_commands.describe(user="The user to compliment")
    async def compliment(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Give someone a random compliment"""
        target = user or interaction.user
        
        compliments = [
            "You're absolutely amazing!",
            "You light up every room you enter!",
            "You have the best laugh!",
            "You're incredibly thoughtful!",
            "You're one of a kind!",
            "You have amazing energy!",
            "You're so creative!",
            "You make everything better!",
            "You're such a good friend!",
            "You're absolutely brilliant!",
            "You have a beautiful soul!",
            "You're incredibly talented!",
            "You make the world brighter!",
            "You're truly special!",
            "You have such a kind heart!"
        ]
        
        compliment = random.choice(compliments)
        
        embed = discord.Embed(
            title="✨ Compliment",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text=f"Compliment from {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        if target != interaction.user:
            embed.set_thumbnail(url=target.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="insult", description="Playfully insult someone (family-friendly)")
    @app_commands.describe(user="The user to playfully insult")
    async def insult(self, interaction: discord.Interaction, user: discord.Member):
        """Give someone a playful, family-friendly insult"""
        if user.id == interaction.user.id:
            embed = EmbedBuilder.warning("Self Insult", "Don't be mean to yourself! You're awesome! 😊")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        insults = [
            "You're as sharp as a bowling ball!",
            "You're not stupid, you just have bad luck thinking!",
            "You're like a cloud - when you disappear, it's a beautiful day!",
            "You have the perfect face for radio!",
            "You're about as useful as a chocolate teapot!",
            "You're so slow, you'd lose a race to a turtle!",
            "You have all the grace of a reversing dump truck!",
            "You're like a human version of autocorrect - mostly wrong!",
            "You couldn't pour water out of a boot with instructions on the heel!",
            "You're proof that evolution can go in reverse!"
        ]
        
        insult = random.choice(insults)
        
        embed = discord.Embed(
            title="🎭 Playful Roast",
            description=f"{user.mention}, {insult}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="💡 Remember",
            value="This is all in good fun! We're just playing around! 😄",
            inline=False
        )
        
        embed.set_footer(
            text=f"Roasted by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ship", description="See how compatible two users are")
    @app_commands.describe(
        user1="First user",
        user2="Second user (optional - defaults to you)"
    )
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: Optional[discord.Member] = None):
        """Calculate compatibility between two users"""
        if user2 is None:
            user2 = interaction.user
        
        # Generate "random" compatibility based on user IDs (consistent results)
        compatibility = (user1.id + user2.id) % 101
        
        # Create ship name
        ship_name = user1.display_name[:len(user1.display_name)//2] + user2.display_name[len(user2.display_name)//2:]
        
        # Determine compatibility level
        if compatibility >= 90:
            level = "Perfect Match"
            color = discord.Color.pink()
            emoji = "💖"
        elif compatibility >= 75:
            level = "Great Match"
            color = discord.Color.red()
            emoji = "❤️"
        elif compatibility >= 50:
            level = "Good Match"
            color = discord.Color.orange()
            emoji = "🧡"
        elif compatibility >= 25:
            level = "Okay Match"
            color = discord.Color.yellow()
            emoji = "💛"
        else:
            level = "Not Compatible"
            color = discord.Color.blue()
            emoji = "💙"
        
        # Create progress bar
        bar_length = 20
        filled = int(bar_length * compatibility / 100)
        bar = "💖" * filled + "🤍" * (bar_length - filled)
        
        embed = discord.Embed(
            title=f"💕 Compatibility Check",
            description=f"**{user1.display_name}** × **{user2.display_name}**",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Ship Name", value=f"✨ **{ship_name}** ✨", inline=False)
        embed.add_field(name="Compatibility", value=f"{bar}\\n{emoji} **{compatibility}%** - {level}", inline=False)
        
        if compatibility >= 75:
            embed.add_field(name="💫 Special Message", value="You two are meant to be together! 🥰", inline=False)
        elif compatibility <= 25:
            embed.add_field(name="😅 Don't Worry", value="Sometimes opposites attract! Or maybe just stay friends! 😊", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="love8ball", description="Ask the magic 8-ball a question about love")
    @app_commands.describe(question="Your love/relationship question")
    async def love_8ball(self, interaction: discord.Interaction, question: str):
        """Ask the magic 8-ball about love and relationships"""
        responses = [
            "💕 Love is definitely in the air!",
            "💖 The stars align for romance!",
            "💘 Cupid says yes!",
            "💝 Your heart knows the answer!",
            "💗 Follow your feelings!",
            "💓 Love will find a way!",
            "💞 It's written in the stars!",
            "💕 Trust your heart!",
            "❤️ Love conquers all!",
            "💔 Maybe it's not meant to be...",
            "💭 Only time will tell!",
            "🤔 Ask your heart, not me!",
            "💫 The universe is uncertain!",
            "🔮 The future is unclear!",
            "💭 Think with your heart!"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="💖 Love Magic 8-Ball",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="💕 Question", value=question, inline=False)
        embed.add_field(name="💫 Answer", value=response, inline=False)
        
        embed.set_footer(
            text=f"Asked by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

class MarriageProposalView(discord.ui.View):
    """Marriage proposal with accept/decline buttons"""
    
    def __init__(self, proposer: discord.Member, target: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.proposer = proposer
        self.target = target
    
    @discord.ui.button(label='Accept 💍', style=discord.ButtonStyle.success, emoji='✅')
    async def accept_proposal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            embed = EmbedBuilder.error("Not For You", "This proposal isn't for you!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💒 Marriage Accepted!",
            description=f"🎉 {self.target.mention} said YES to {self.proposer.mention}!\\n\\nCongratulations to the happy couple! 💕",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="💖 Wedding Bells",
            value="You are now virtually married! May your union be filled with love and laughter! 🥰",
            inline=False
        )
        
        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Decline 💔', style=discord.ButtonStyle.danger, emoji='❌')
    async def decline_proposal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            embed = EmbedBuilder.error("Not For You", "This proposal isn't for you!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💔 Marriage Declined",
            description=f"{self.target.mention} declined {self.proposer.mention}'s proposal.\\n\\nBetter luck next time! 😢",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="💙 Don't Give Up",
            value="There are plenty of fish in the sea! Keep trying! 🐟",
            inline=False
        )
        
        self.disable_all_items()
        await interaction.response.edit_message(embed=embed, view=self)

async def setup(bot):
    await bot.add_cog(SocialCog(bot))
