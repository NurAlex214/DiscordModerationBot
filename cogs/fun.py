import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import random
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, TimeConverter, format_duration

class PollView(discord.ui.View):
    """Interactive poll with buttons"""
    
    def __init__(self, question: str, options: List[str], *, timeout=None):
        super().__init__(timeout=timeout)
        self.question = question
        self.options = options
        self.votes = {i: set() for i in range(len(options))}
        
        # Add buttons for each option (max 5)
        for i, option in enumerate(options[:5]):
            button = discord.ui.Button(
                label=f"{option} (0)",
                style=discord.ButtonStyle.secondary,
                emoji=["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][i],
                custom_id=f"poll_option_{i}"
            )
            button.callback = self.make_vote_callback(i)
            self.add_item(button)
        
        # Add results button
        results_button = discord.ui.Button(
            label="View Results",
            style=discord.ButtonStyle.primary,
            emoji="📊",
            custom_id="poll_results"
        )
        results_button.callback = self.show_results
        self.add_item(results_button)
    
    def make_vote_callback(self, option_index: int):
        async def vote_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            
            # Remove user from all other options
            for votes in self.votes.values():
                votes.discard(user_id)
            
            # Add user to selected option
            self.votes[option_index].add(user_id)
            
            # Update button labels with vote counts
            for i, button in enumerate(self.children[:-1]):  # Exclude results button
                if isinstance(button, discord.ui.Button):
                    vote_count = len(self.votes[i])
                    button.label = f"{self.options[i]} ({vote_count})"
            
            await interaction.response.edit_message(view=self)
        
        return vote_callback
    
    async def show_results(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"📊 Poll Results: {self.question}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        total_votes = sum(len(votes) for votes in self.votes.values())
        
        for i, option in enumerate(self.options):
            vote_count = len(self.votes[i])
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            # Create progress bar
            bar_length = 20
            filled_length = int(bar_length * percentage / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            embed.add_field(
                name=f"{['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][i]} {option}",
                value=f"`{bar}` {vote_count} votes ({percentage:.1f}%)",
                inline=False
            )
        
        embed.set_footer(text=f"Total votes: {total_votes}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GiveawayView(discord.ui.View):
    """Interactive giveaway with entry button"""
    
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.entries = set()
    
    @discord.ui.button(label='Enter Giveaway 🎉', style=discord.ButtonStyle.primary, emoji='🎉')
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in self.entries:
            self.entries.remove(user_id)
            embed = EmbedBuilder.warning("Left Giveaway", "You have left the giveaway.")
            button.label = f'Enter Giveaway 🎉 ({len(self.entries)})'
        else:
            self.entries.add(user_id)
            embed = EmbedBuilder.success("Entered Giveaway", "You have entered the giveaway! Good luck! 🍀")
            button.label = f'Enter Giveaway 🎉 ({len(self.entries)})'
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.edit_original_response(view=self)

class FunCog(commands.Cog, name="Fun & Interactive"):
    """Fun and interactive commands for entertainment"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}
    
    @app_commands.command(name="poll", description="Create an interactive poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: Optional[str] = None,
        option4: Optional[str] = None,
        option5: Optional[str] = None
    ):
        """Create an interactive poll with up to 5 options"""
        options = [option1, option2]
        for opt in [option3, option4, option5]:
            if opt:
                options.append(opt)
        
        embed = discord.Embed(
            title=f"📊 Poll: {question}",
            description="Click the buttons below to vote!",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Add options to embed
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][i]} {option}",
                value="0 votes (0%)",
                inline=False
            )
        
        embed.set_footer(
            text=f"Poll created by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        view = PollView(question, options)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(
        duration="Duration of the giveaway (e.g., 1h, 30m, 1d)",
        winners="Number of winners",
        prize="What is being given away"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: app_commands.Range[int, 1, 20],
        prize: str
    ):
        """Start an interactive giveaway"""
        if not interaction.user.guild_permissions.manage_messages:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Messages' permission to create giveaways.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Parse duration
        time_delta = TimeConverter.convert(duration)
        if not time_delta:
            embed = EmbedBuilder.error("Invalid Duration", "Please provide a valid duration (e.g., 1h, 30m, 1d)")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if time_delta > timedelta(days=30):
            embed = EmbedBuilder.error("Duration Too Long", "Giveaway duration cannot exceed 30 days.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        end_time = datetime.utcnow() + time_delta
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** {discord.utils.format_dt(end_time, style='R')}",
            color=discord.Color.gold(),
            timestamp=end_time
        )
        
        embed.add_field(
            name="How to Enter",
            value="Click the 🎉 button below to enter!",
            inline=False
        )
        
        embed.set_footer(
            text=f"Hosted by {interaction.user.display_name} • Ends at",
            icon_url=interaction.user.display_avatar.url
        )
        
        view = GiveawayView()
        await interaction.response.send_message(embed=embed, view=view)
        
        # Store giveaway info for ending later
        message = await interaction.original_response()
        self.active_giveaways[message.id] = {
            'end_time': end_time,
            'winners': winners,
            'prize': prize,
            'host': interaction.user,
            'view': view
        }
        
        # Schedule giveaway end
        await asyncio.sleep(time_delta.total_seconds())
        await self.end_giveaway(message.id, interaction.channel)
    
    async def end_giveaway(self, message_id: int, channel: discord.TextChannel):
        """End a giveaway and pick winners"""
        if message_id not in self.active_giveaways:
            return
        
        giveaway_data = self.active_giveaways[message_id]
        entries = list(giveaway_data['view'].entries)
        
        try:
            message = await channel.fetch_message(message_id)
        except:
            return
        
        if not entries:
            embed = EmbedBuilder.warning(
                "Giveaway Ended",
                f"**Prize:** {giveaway_data['prize']}\n\nNo one entered the giveaway! 😢"
            )
            await message.edit(embed=embed, view=None)
            return
        
        # Pick winners
        winner_count = min(giveaway_data['winners'], len(entries))
        winners = random.sample(entries, winner_count)
        
        # Get winner objects
        winner_mentions = []
        for winner_id in winners:
            user = self.bot.get_user(winner_id)
            if user:
                winner_mentions.append(user.mention)
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY ENDED 🎉",
            description=f"**Prize:** {giveaway_data['prize']}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name=f"🏆 Winner{'s' if len(winners) > 1 else ''}",
            value="\n".join(winner_mentions) if winner_mentions else "No valid winners",
            inline=False
        )
        
        embed.add_field(name="Total Entries", value=str(len(entries)), inline=True)
        
        embed.set_footer(
            text=f"Hosted by {giveaway_data['host'].display_name}",
            icon_url=giveaway_data['host'].display_avatar.url
        )
        
        await message.edit(embed=embed, view=None)
        
        # Announce winners
        if winner_mentions:
            winner_embed = EmbedBuilder.success(
                "🎉 Congratulations!",
                f"You won **{giveaway_data['prize']}**!\n\nContact {giveaway_data['host'].mention} to claim your prize."
            )
            
            content = f"🎉 Giveaway Winners: {', '.join(winner_mentions)}"
            await channel.send(content=content, embed=winner_embed)
        
        # Remove from active giveaways
        del self.active_giveaways[message_id]
    
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question for the 8-ball")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Magic 8-ball responses"""
        responses = [
            "🎱 It is certain.",
            "🎱 It is decidedly so.",
            "🎱 Without a doubt.",
            "🎱 Yes definitely.",
            "🎱 You may rely on it.",
            "🎱 As I see it, yes.",
            "🎱 Most likely.",
            "🎱 Outlook good.",
            "🎱 Yes.",
            "🎱 Signs point to yes.",
            "🎱 Reply hazy, try again.",
            "🎱 Ask again later.",
            "🎱 Better not tell you now.",
            "🎱 Cannot predict now.",
            "🎱 Concentrate and ask again.",
            "🎱 Don't count on it.",
            "🎱 My reply is no.",
            "🎱 My sources say no.",
            "🎱 Outlook not so good.",
            "🎱 Very doubtful."
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        
        embed.set_footer(
            text=f"Asked by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        """Flip a coin with animation"""
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description="Flipping coin...",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Add some suspense
        await asyncio.sleep(1)
        
        result = random.choice(["Heads", "Tails"])
        emoji = "🟡" if result == "Heads" else "⚪"
        
        embed = discord.Embed(
            title="🪙 Coin Flip Result",
            description=f"{emoji} **{result}**!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text=f"Flipped by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="dice", description="Roll dice")
    @app_commands.describe(
        sides="Number of sides on the dice",
        count="Number of dice to roll"
    )
    async def dice(
        self,
        interaction: discord.Interaction,
        sides: app_commands.Range[int, 2, 100] = 6,
        count: app_commands.Range[int, 1, 10] = 1
    ):
        """Roll dice with customizable sides and count"""
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if count == 1:
            embed.add_field(
                name=f"Rolling 1d{sides}",
                value=f"🎲 **{rolls[0]}**",
                inline=False
            )
        else:
            embed.add_field(
                name=f"Rolling {count}d{sides}",
                value=" + ".join([f"**{roll}**" for roll in rolls]) + f" = **{total}**",
                inline=False
            )
            
            embed.add_field(name="Individual Rolls", value=", ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=True)
            embed.add_field(name="Average", value=f"{total/count:.1f}", inline=True)
        
        embed.set_footer(
            text=f"Rolled by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="quote", description="Get an inspirational quote")
    async def quote(self, interaction: discord.Interaction):
        """Get a random inspirational quote"""
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Don't let yesterday take up too much of today.", "Will Rogers"),
            ("You learn more from failure than from success.", "Unknown"),
            ("If you are working on something that you really care about, you don't have to be pushed.", "Steve Jobs"),
            ("Experience is the teacher of all things.", "Julius Caesar")
        ]
        
        quote_text, author = random.choice(quotes)
        
        embed = discord.Embed(
            title="💭 Inspirational Quote",
            description=f"*\"{quote_text}\"*\n\n— **{author}**",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="choose", description="Let the bot choose between options")
    @app_commands.describe(options="Options separated by commas")
    async def choose(self, interaction: discord.Interaction, options: str):
        """Choose randomly between provided options"""
        option_list = [opt.strip() for opt in options.split(',') if opt.strip()]
        
        if len(option_list) < 2:
            embed = EmbedBuilder.error("Not Enough Options", "Please provide at least 2 options separated by commas.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        choice = random.choice(option_list)
        
        embed = discord.Embed(
            title="🤔 The Choice Is...",
            description=f"I choose: **{choice}**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Options",
            value=", ".join(option_list),
            inline=False
        )
        
        embed.set_footer(
            text=f"Chosen for {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="🪨 Rock", value="rock"),
        app_commands.Choice(name="📄 Paper", value="paper"),
        app_commands.Choice(name="✂️ Scissors", value="scissors")
    ])
    async def rock_paper_scissors(self, interaction: discord.Interaction, choice: str):
        """Play Rock Paper Scissors against the bot"""
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
            color = discord.Color.green()
        else:
            result = "I win! 🤖"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=f"**{result}**",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Your Choice",
            value=f"{emojis[choice]} {choice.title()}",
            inline=True
        )
        
        embed.add_field(
            name="My Choice",
            value=f"{emojis[bot_choice]} {bot_choice.title()}",
            inline=True
        )
        
        embed.set_footer(
            text=f"Played by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="say", description="Make the bot say something")
    @app_commands.describe(
        message="The message to send",
        channel="Channel to send the message to"
    )
    async def say(
        self,
        interaction: discord.Interaction,
        message: str,
        channel: Optional[discord.TextChannel] = None
    ):
        """Make the bot send a message"""
        if not interaction.user.guild_permissions.manage_messages:
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Manage Messages' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        # Check for mentions and prevent abuse
        if "@everyone" in message or "@here" in message:
            if not interaction.user.guild_permissions.mention_everyone:
                embed = EmbedBuilder.error("Permission Error", "You cannot use @everyone or @here mentions.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        try:
            await channel.send(message)
            embed = EmbedBuilder.success("Message Sent", f"Your message has been sent to {channel.mention}.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = EmbedBuilder.error("Permission Error", "I don't have permission to send messages in that channel.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(FunCog(bot))
