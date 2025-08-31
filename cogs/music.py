import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
import random
import asyncio
import math
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder

class EntertainmentCog(commands.Cog, name="Entertainment"):
    """Core entertainment commands for server fun"""
    
    def __init__(self, bot):
        self.bot = bot
        self.trivia_sessions = {}
        self.word_games = {}
    
    @app_commands.command(name="trivia", description="Start a trivia game")
    @app_commands.describe(difficulty="Difficulty level of the trivia")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard")
    ])
    async def trivia(self, interaction: discord.Interaction, difficulty: str = "medium"):
        """Start a trivia game"""
        if interaction.channel.id in self.trivia_sessions:
            embed = EmbedBuilder.warning("Game Active", "There's already a trivia game running in this channel!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Sample trivia questions (you can expand this or use an API)
        trivia_questions = {
            "easy": [
                {
                    "question": "What is the capital of France?",
                    "answers": ["Paris", "London", "Berlin", "Madrid"],
                    "correct": 0
                },
                {
                    "question": "How many legs does a spider have?",
                    "answers": ["6", "8", "10", "12"],
                    "correct": 1
                },
                {
                    "question": "What color do you get when you mix red and white?",
                    "answers": ["Pink", "Purple", "Orange", "Yellow"],
                    "correct": 0
                }
            ],
            "medium": [
                {
                    "question": "Which planet is known as the Red Planet?",
                    "answers": ["Venus", "Mars", "Jupiter", "Saturn"],
                    "correct": 1
                },
                {
                    "question": "What is the largest mammal in the world?",
                    "answers": ["Elephant", "Blue Whale", "Giraffe", "Hippo"],
                    "correct": 1
                },
                {
                    "question": "In what year did World War II end?",
                    "answers": ["1944", "1945", "1946", "1947"],
                    "correct": 1
                }
            ],
            "hard": [
                {
                    "question": "What is the smallest country in the world?",
                    "answers": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"],
                    "correct": 1
                },
                {
                    "question": "Which chemical element has the symbol 'Au'?",
                    "answers": ["Silver", "Gold", "Aluminum", "Argon"],
                    "correct": 1
                },
                {
                    "question": "Who painted 'The Starry Night'?",
                    "answers": ["Pablo Picasso", "Claude Monet", "Vincent van Gogh", "Leonardo da Vinci"],
                    "correct": 2
                }
            ]
        }
        
        question_data = random.choice(trivia_questions[difficulty])
        
        # Create trivia embed
        embed = discord.Embed(
            title=f"🧠 Trivia Time! ({difficulty.title()})",
            description=question_data["question"],
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        # Add answer options
        for i, answer in enumerate(question_data["answers"]):
            embed.add_field(
                name=f"{chr(65+i)}) {answer}",
                value="​",  # Zero-width space
                inline=True
            )
        
        embed.add_field(
            name="⏰ Time Limit",
            value="You have 30 seconds to answer!",
            inline=False
        )
        
        embed.set_footer(
            text=f"React with 🇦, 🇧, 🇨, or 🇩 to answer!",
            icon_url=interaction.user.display_avatar.url
        )
        
        view = TriviaView(question_data, interaction.user, difficulty)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Store the session
        self.trivia_sessions[interaction.channel.id] = {
            "question": question_data,
            "started_by": interaction.user.id,
            "start_time": datetime.utcnow()
        }
        
        # Auto-end after timeout
        await asyncio.sleep(30)
        if interaction.channel.id in self.trivia_sessions:
            del self.trivia_sessions[interaction.channel.id]
    
    @app_commands.command(name="riddle", description="Get a riddle to solve")
    async def riddle(self, interaction: discord.Interaction):
        """Get a random riddle"""
        riddles = [
            {
                "riddle": "I have keys but no locks. I have space but no room. You can enter, but you can't go outside. What am I?",
                "answer": "keyboard",
                "hint": "It's something you use with a computer!"
            },
            {
                "riddle": "The more you take, the more you leave behind. What am I?",
                "answer": "footsteps",
                "hint": "Think about walking!"
            },
            {
                "riddle": "I'm tall when I'm young, and short when I'm old. What am I?",
                "answer": "candle",
                "hint": "It provides light and melts!"
            },
            {
                "riddle": "What has hands but cannot clap?",
                "answer": "clock",
                "hint": "It tells time!"
            },
            {
                "riddle": "What gets wet while drying?",
                "answer": "towel",
                "hint": "You use it after a shower!"
            }
        ]
        
        riddle_data = random.choice(riddles)
        
        embed = discord.Embed(
            title="🤔 Riddle Time!",
            description=riddle_data["riddle"],
            color=discord.Color.dark_purple(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="💡 Need a hint?",
            value="Click the button below for a hint!",
            inline=False
        )
        
        embed.set_footer(
            text=f"Riddle for {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        view = RiddleView(riddle_data, interaction.user)
        await interaction.response.send_message(embed=embed, view=view)
    
    
    
    
    
    
    
    @app_commands.command(name="hangman", description="Start a hangman game")
    @app_commands.describe(custom_word="Custom word to use (optional)")
    async def hangman(self, interaction: discord.Interaction, custom_word: Optional[str] = None):
        """Start a hangman game"""
        if interaction.channel.id in self.word_games:
            embed = EmbedBuilder.warning("Game Active", "There's already a word game running in this channel!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Word list
        words = [
            "python", "discord", "computer", "elephant", "rainbow", "wizard", "castle", "dragon",
            "adventure", "mystery", "treasure", "journey", "magic", "forest", "mountain", "ocean"
        ]
        
        word = custom_word.lower() if custom_word else random.choice(words)
        
        if custom_word and (len(word) < 3 or len(word) > 15 or not word.isalpha()):
            embed = EmbedBuilder.error("Invalid Word", "Custom word must be 3-15 letters and contain only letters!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Initialize game
        guessed_letters = set()
        wrong_guesses = 0
        max_wrong = 6
        
        embed = discord.Embed(
            title="🎪 Hangman Game Started!",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        view = HangmanView(word, interaction.user)
        embed.description = view.get_display()
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="spinner", description="Spin a custom wheel")
    @app_commands.describe(options="Comma-separated list of options to spin for")
    async def spinner(self, interaction: discord.Interaction, options: str):
        """Spin a wheel with custom options"""
        option_list = [opt.strip() for opt in options.split(',')]
        
        if len(option_list) < 2:
            embed = EmbedBuilder.error("Not Enough Options", "Please provide at least 2 options separated by commas!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if len(option_list) > 20:
            embed = EmbedBuilder.error("Too Many Options", "Please provide 20 options or fewer!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create spinning animation
        embed = discord.Embed(
            title="🎰 Spinning the Wheel...",
            description="🔄 *The wheel is spinning...*",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎯 Options",
            value="\\n".join(f"• {opt}" for opt in option_list),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Wait for dramatic effect
        await asyncio.sleep(2)
        
        # Choose winner
        winner = random.choice(option_list)
        
        embed = discord.Embed(
            title="🎉 Wheel Result",
            description=f"🎊 **The wheel has chosen:** {winner}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎯 All Options",
            value="\\n".join(f"{'🏆 ' if opt == winner else '• '}{opt}" for opt in option_list),
            inline=False
        )
        
        embed.set_footer(
            text=f"Spun by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="games", description="Get a variety of fun mini-games and entertainment")
    @app_commands.describe(game_type="Choose a game or entertainment option")
    @app_commands.choices(game_type=[
        app_commands.Choice(name="Truth or Dare", value="truthdare"),
        app_commands.Choice(name="Would You Rather", value="wyr"),
        app_commands.Choice(name="Bingo Card", value="bingo"),
        app_commands.Choice(name="Motivational Quote", value="motivation"),
        app_commands.Choice(name="Word Chain", value="wordchain")
    ])
    async def games(self, interaction: discord.Interaction, game_type: str):
        """Unified entertainment command with multiple game options"""
        
        if game_type == "truthdare":
            # Truth or Dare combined
            choice = random.choice(["truth", "dare"])
            
            if choice == "truth":
                truth_questions = [
                    "What's the most embarrassing thing that's ever happened to you?",
                    "What's a secret you've never told anyone?",
                    "Who was your first crush?",
                    "What's the weirdest dream you've ever had?",
                    "What's something you've done that you're proud of but never talk about?",
                    "If you could change one thing about yourself, what would it be?",
                    "What's the last lie you told?",
                    "What's your biggest fear?",
                    "Who in this server would you want to be stuck on a deserted island with?",
                    "What's the most trouble you've ever been in?"
                ]
                
                truth = random.choice(truth_questions)
                
                embed = discord.Embed(
                    title="💬 Truth Question",
                    description=truth,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
            else:
                dares = [
                    "Send a message using only emojis for the next 5 minutes",
                    "Change your nickname to something funny for 10 minutes",
                    "Sing happy birthday in voice chat",
                    "Write a short poem about someone in the server",
                    "Share an embarrassing story from your childhood",
                    "Talk in a funny accent for the next 10 minutes",
                    "Draw something with your non-dominant hand and post it",
                    "Do your best impression of a celebrity"
                ]
                
                dare = random.choice(dares)
                
                embed = discord.Embed(
                    title="🎯 Dare Challenge",
                    description=dare,
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="⚠️ Safety First",
                    value="Only do dares that are safe and appropriate! Skip if uncomfortable.",
                    inline=False
                )
        
        elif game_type == "wyr":
            wyr_questions = [
                "Would you rather have the ability to fly or be invisible?",
                "Would you rather live in the past or the future?",
                "Would you rather have super strength or super speed?",
                "Would you rather be able to read minds or see the future?",
                "Would you rather never have to sleep or never have to eat?",
                "Would you rather be really good at singing or really good at dancing?",
                "Would you rather have unlimited money or unlimited time?",
                "Would you rather be famous or be anonymous?",
                "Would you rather live underwater or in space?",
                "Would you rather have a rewind button or a pause button for your life?"
            ]
            
            question = random.choice(wyr_questions)
            
            embed = discord.Embed(
                title="🤷 Would You Rather?",
                description=question,
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💭 Think About It",
                value="Share your choice and reasoning in chat!",
                inline=False
            )
        
        elif game_type == "bingo":
            # Generate random bingo numbers
            b_numbers = random.sample(range(1, 16), 5)
            i_numbers = random.sample(range(16, 31), 5)
            n_numbers = random.sample(range(31, 46), 4)  # 4 because center is FREE
            g_numbers = random.sample(range(46, 61), 5)
            o_numbers = random.sample(range(61, 76), 5)
            
            # Insert FREE space in the middle of N column
            n_numbers.insert(2, "FREE")
            
            embed = discord.Embed(
                title="🎯 Your Bingo Card",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            # Create the bingo card display
            card_display = "```\n"
            card_display += " B  |  I  |  N  |  G  |  O \n"
            card_display += "----+-----+-----+-----+----\n"
            
            for row in range(5):
                row_numbers = [
                    f"{b_numbers[row]:2d}",
                    f"{i_numbers[row]:2d}",
                    f"{n_numbers[row]:>4}" if isinstance(n_numbers[row], str) else f"{n_numbers[row]:2d}",
                    f"{g_numbers[row]:2d}",
                    f"{o_numbers[row]:2d}"
                ]
                card_display += " | ".join(row_numbers) + "\n"
            
            card_display += "```"
            
            embed.description = card_display
            
            embed.add_field(
                name="🎮 How to Play",
                value="Use this card for bingo games! Cross off numbers as they're called.",
                inline=False
            )
        
        elif game_type == "motivation":
            motivational_quotes = [
                ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
                ("The only way to do great work is to love what you do.", "Steve Jobs"),
                ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
                ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
                ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
                ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
                ("The only impossible journey is the one you never begin.", "Tony Robbins"),
                ("Success is not the key to happiness. Happiness is the key to success.", "Albert Schweitzer")
            ]
            
            quote_text, author = random.choice(motivational_quotes)
            
            embed = discord.Embed(
                title="💪 Daily Motivation",
                description=f"*\"{quote_text}\"",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="✨ Author",
                value=f"— {author}",
                inline=False
            )
            
            embed.add_field(
                name="🌟 Remember",
                value="You've got this! Keep pushing forward! 🚀",
                inline=False
            )
        
        elif game_type == "wordchain":
            if interaction.channel.id in self.word_games:
                embed = EmbedBuilder.warning("Game Active", "There's already a word game running in this channel!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            starting_words = ["apple", "banana", "computer", "dragon", "elephant", "forest", "guitar", "happy"]
            starting_word = random.choice(starting_words)
            
            embed = discord.Embed(
                title="🔗 Word Chain Game Started!",
                description=f"**Starting word:** {starting_word}\n\nNext word must start with **'{starting_word[-1].upper()}'**",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📋 Rules",
                value="• Next word must start with the last letter of the previous word\n• No repeating words\n• Must be a real English word\n• Type your word in chat!",
                inline=False
            )
            
            embed.add_field(
                name="⏰ Time Limit",
                value="Game ends after 5 minutes of inactivity",
                inline=False
            )
            
            # Initialize game session
            self.word_games[interaction.channel.id] = {
                "current_word": starting_word,
                "used_words": {starting_word},
                "players": {},
                "last_player": None,
                "started_by": interaction.user.id,
                "start_time": datetime.utcnow()
            }
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

class TriviaView(discord.ui.View):
    """Interactive trivia view with answer buttons"""
    
    def __init__(self, question_data: dict, user: discord.Member, difficulty: str, *, timeout=30):
        super().__init__(timeout=timeout)
        self.question_data = question_data
        self.user = user
        self.difficulty = difficulty
        self.answered = False
    
    async def on_timeout(self):
        """Called when the view times out"""
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        return True  # Allow anyone to answer trivia
    
    @discord.ui.button(label='A', style=discord.ButtonStyle.primary, emoji='🇦')
    async def answer_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 0)
    
    @discord.ui.button(label='B', style=discord.ButtonStyle.primary, emoji='🇧')
    async def answer_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 1)
    
    @discord.ui.button(label='C', style=discord.ButtonStyle.primary, emoji='🇨')
    async def answer_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 2)
    
    @discord.ui.button(label='D', style=discord.ButtonStyle.primary, emoji='🇩')
    async def answer_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 3)
    
    async def process_answer(self, interaction: discord.Interaction, answer_index: int):
        try:
            if self.answered:
                embed = EmbedBuilder.warning("Already Answered", "This trivia question has already been answered!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            self.answered = True
            correct_answer = self.question_data["correct"]
            is_correct = answer_index == correct_answer
            
            embed = discord.Embed(
                title="🧠 Trivia Result",
                color=discord.Color.green() if is_correct else discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            if is_correct:
                embed.description = f"🎉 Correct! {interaction.user.mention} got it right!"
                embed.add_field(
                    name="✅ Answer",
                    value=f"{chr(65+correct_answer)}) {self.question_data['answers'][correct_answer]}",
                    inline=False
                )
            else:
                embed.description = f"❌ Wrong answer! Better luck next time, {interaction.user.mention}!"
                embed.add_field(
                    name="❌ Your Answer",
                    value=f"{chr(65+answer_index)}) {self.question_data['answers'][answer_index]}",
                    inline=True
                )
                embed.add_field(
                    name="✅ Correct Answer",
                    value=f"{chr(65+correct_answer)}) {self.question_data['answers'][correct_answer]}",
                    inline=True
                )
            
            # Points system
            points = {"easy": 10, "medium": 20, "hard": 30}
            if is_correct:
                embed.add_field(
                    name="🏆 Points Earned",
                    value=f"+{points[self.difficulty]} points!",
                    inline=False
                )
            
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            # Interaction expired, ignore gracefully
            pass
        except Exception as e:
            # Log other errors but don't crash
            print(f"Error in trivia answer processing: {e}")

class RiddleView(discord.ui.View):
    """Interactive riddle view with hint and answer reveal"""
    
    def __init__(self, riddle_data: dict, user: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.riddle_data = riddle_data
        self.user = user
        self.hint_used = False
        self.revealed = False
    
    async def on_timeout(self):
        """Called when the view times out"""
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        return interaction.user.id == self.user.id
    
    @discord.ui.button(label='💡 Get Hint', style=discord.ButtonStyle.secondary)
    async def get_hint(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.hint_used:
                embed = EmbedBuilder.warning("Hint Used", "You've already used your hint!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            self.hint_used = True
            button.disabled = True
            
            embed = discord.Embed(
                title="💡 Hint",
                description=self.riddle_data["hint"],
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.NotFound:
            # Interaction expired, ignore gracefully
            pass
        except Exception as e:
            print(f"Error in riddle hint: {e}")
    
    @discord.ui.button(label='🔍 Reveal Answer', style=discord.ButtonStyle.danger)
    async def reveal_answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.revealed:
                embed = EmbedBuilder.warning("Already Revealed", "The answer has already been revealed!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            self.revealed = True
            
            embed = discord.Embed(
                title="🔍 Riddle Answer",
                description=f"**Answer:** {self.riddle_data['answer'].title()}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🤔 The Riddle",
                value=self.riddle_data["riddle"],
                inline=False
            )
            
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(embed=embed)
        except discord.NotFound:
            # Interaction expired, ignore gracefully
            pass
        except Exception as e:
            print(f"Error in riddle answer reveal: {e}")

class HangmanView(discord.ui.View):
    """Interactive hangman game view"""
    
    def __init__(self, word: str, user: discord.Member, *, timeout=300):
        super().__init__(timeout=timeout)
        self.word = word.lower()
        self.user = user
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong = 6
        self.game_over = False
    
    async def on_timeout(self):
        """Called when the view times out"""
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user can interact with this view"""
        return interaction.user.id == self.user.id
    
    def get_display(self) -> str:
        """Get the current display state of the word"""
        display = ""
        for letter in self.word:
            if letter in self.guessed_letters:
                display += letter + " "
            else:
                display += "_ "
        return display.strip()
    
    def get_hangman_art(self) -> str:
        """Get hangman ASCII art based on wrong guesses"""
        stages = [
            "```\\n      \\n      \\n      \\n      \\n      \\n=========```",
            "```\\n  |   \\n  |   \\n  |   \\n  |   \\n  |   \\n=========```",
            "```\\n  +---+\\n  |   |\\n      |\\n      |\\n      |\\n=========```",
            "```\\n  +---+\\n  |   |\\n  O   |\\n      |\\n      |\\n=========```",
            "```\\n  +---+\\n  |   |\\n  O   |\\n  |   |\\n      |\\n=========```",
            "```\\n  +---+\\n  |   |\\n  O   |\\n /|   |\\n      |\\n=========```",
            "```\\n  +---+\\n  |   |\\n  O   |\\n /|\\\\  |\\n      |\\n=========```",
            "```\\n  +---+\\n  |   |\\n  O   |\\n /|\\\\  |\\n /    |\\n=========```"
        ]
        return stages[min(self.wrong_guesses, len(stages) - 1)]
    
    def create_embed(self) -> discord.Embed:
        """Create the hangman game embed"""
        if self.game_over:
            if set(self.word) <= self.guessed_letters:
                # Won
                embed = discord.Embed(
                    title="🎉 Hangman - You Won!",
                    description=f"Congratulations! The word was: **{self.word.upper()}**",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
            else:
                # Lost
                embed = discord.Embed(
                    title="💀 Hangman - Game Over",
                    description=f"You lost! The word was: **{self.word.upper()}**",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
        else:
            embed = discord.Embed(
                title="🎪 Hangman Game",
                description=f"**Word:** `{self.get_display()}`",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
        
        embed.add_field(
            name="🎨 Hangman",
            value=self.get_hangman_art(),
            inline=False
        )
        
        if self.guessed_letters:
            embed.add_field(
                name="📝 Guessed Letters",
                value=" ".join(sorted(self.guessed_letters)).upper(),
                inline=False
            )
        
        embed.add_field(
            name="❌ Wrong Guesses",
            value=f"{self.wrong_guesses}/{self.max_wrong}",
            inline=True
        )
        
        embed.set_footer(
            text=f"Game for {self.user.display_name}",
            icon_url=self.user.display_avatar.url
        )
        
        return embed
    
    @discord.ui.button(label='Guess Letter', style=discord.ButtonStyle.primary, emoji='🔤')
    async def guess_letter(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.user.id:
                embed = EmbedBuilder.error("Not Your Game", "This hangman game isn't for you!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if self.game_over:
                embed = EmbedBuilder.warning("Game Over", "This game has already ended!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            modal = HangmanModal(self)
            await interaction.response.send_modal(modal)
        except discord.NotFound:
            # Interaction expired, ignore gracefully
            pass
        except Exception as e:
            print(f"Error in hangman guess: {e}")

class HangmanModal(discord.ui.Modal, title="Guess a Letter"):
    """Modal for guessing letters in hangman"""
    
    def __init__(self, hangman_view):
        super().__init__()
        self.hangman_view = hangman_view
    
    letter = discord.ui.TextInput(
        label="Enter a letter",
        placeholder="Type a single letter...",
        min_length=1,
        max_length=1
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            guess = self.letter.value.lower()
            
            if not guess.isalpha():
                embed = EmbedBuilder.error("Invalid Input", "Please enter only letters!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if guess in self.hangman_view.guessed_letters:
                embed = EmbedBuilder.warning("Already Guessed", f"You've already guessed the letter '{guess.upper()}'!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            self.hangman_view.guessed_letters.add(guess)
            
            if guess in self.hangman_view.word:
                # Correct guess
                embed = EmbedBuilder.success("Correct!", f"Good guess! The letter '{guess.upper()}' is in the word!")
            else:
                # Wrong guess
                self.hangman_view.wrong_guesses += 1
                embed = EmbedBuilder.error("Wrong!", f"Sorry! The letter '{guess.upper()}' is not in the word.")
            
            # Check win/lose conditions
            if set(self.hangman_view.word) <= self.hangman_view.guessed_letters:
                # Won
                self.hangman_view.game_over = True
                for item in self.hangman_view.children:
                    item.disabled = True
            elif self.hangman_view.wrong_guesses >= self.hangman_view.max_wrong:
                # Lost
                self.hangman_view.game_over = True
                for item in self.hangman_view.children:
                    item.disabled = True
            
            game_embed = self.hangman_view.create_embed()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.edit_original_response(embed=game_embed, view=self.hangman_view)
        except discord.NotFound:
            # Interaction expired, ignore gracefully
            pass
        except Exception as e:
            print(f"Error in hangman modal submit: {e}")

async def setup(bot):
    await bot.add_cog(EntertainmentCog(bot))
