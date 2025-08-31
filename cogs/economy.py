import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import random
import asyncio
import sys
import os
import logging

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder, PaginationView

# Create logger for economy actions
economy_logger = logging.getLogger('economy_actions')
economy_logger.setLevel(logging.INFO)

# Create logger for security events
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

class EconomyCog(commands.Cog, name="Economy & Leveling"):
    """Economy system with currency, XP, and leveling features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.setup_economy_tables()
    
    def setup_economy_tables(self):
        """Create economy-related database tables"""
        cursor = self.bot.db.cursor()
        
        # User economy data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_economy (
                user_id INTEGER,
                guild_id INTEGER,
                balance INTEGER DEFAULT 0,
                bank_balance INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_daily DATETIME,
                last_work DATETIME,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # Shop items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                name TEXT,
                price INTEGER,
                description TEXT,
                role_id INTEGER
            )
        ''')
        
        self.bot.db.commit()
    
    def get_user_data(self, user_id: int, guild_id: int) -> dict:
        """Get user's economy data"""
        cursor = self.bot.db.cursor()
        cursor.execute(
            "SELECT balance, bank_balance, xp, level, last_daily, last_work FROM user_economy WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = cursor.fetchone()
        
        if not result:
            # Create new user
            cursor.execute(
                "INSERT INTO user_economy (user_id, guild_id) VALUES (?, ?)",
                (user_id, guild_id)
            )
            self.bot.db.commit()
            return {'balance': 0, 'bank': 0, 'xp': 0, 'level': 1, 'last_daily': None, 'last_work': None}
        
        return {
            'balance': result[0],
            'bank': result[1], 
            'xp': result[2],
            'level': result[3],
            'last_daily': result[4],
            'last_work': result[5]
        }
    
    def update_user_data(self, user_id: int, guild_id: int, **kwargs):
        """Update user's economy data"""
        cursor = self.bot.db.cursor()
        
        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        if fields:
            values.extend([user_id, guild_id])
            cursor.execute(
                f"UPDATE user_economy SET {', '.join(fields)} WHERE user_id = ? AND guild_id = ?",
                values
            )
            self.bot.db.commit()
    
    def calculate_level_xp(self, level: int) -> int:
        """Calculate XP needed for a level"""
        return 5 * (level ** 2) + 50 * level + 100
    
    @app_commands.command(name="balance", description="Check your or someone's balance")
    @app_commands.describe(user="The user to check balance for")
    async def balance(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check user's balance and level"""
        target_user = user or interaction.user
        
        # Log balance check
        if user:
            economy_logger.info(f'Balance check: {interaction.user} ({interaction.user.id}) checked balance of {target_user} ({target_user.id}) in guild {interaction.guild.id}')
        else:
            economy_logger.info(f'Balance check: {interaction.user} ({interaction.user.id}) checked own balance in guild {interaction.guild.id}')
        
        data = self.get_user_data(target_user.id, interaction.guild.id)
        
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Profile",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Balance info
        total_money = data['balance'] + data['bank']
        embed.add_field(
            name="💵 Money",
            value=f"**Wallet:** ${data['balance']:,}\n**Bank:** ${data['bank']:,}\n**Total:** ${total_money:,}",
            inline=True
        )
        
        # Level info
        current_xp = data['xp']
        current_level = data['level']
        xp_needed = self.calculate_level_xp(current_level)
        
        embed.add_field(
            name="⭐ Level",
            value=f"**Level:** {current_level}\n**XP:** {current_xp:,}/{xp_needed:,}\n**Progress:** {(current_xp/xp_needed)*100:.1f}%",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily currency reward"""
        data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        # Check if already claimed today
        if data['last_daily']:
            last_daily = datetime.fromisoformat(data['last_daily'])
            if (datetime.utcnow() - last_daily).days < 1:
                time_left = timedelta(days=1) - (datetime.utcnow() - last_daily)
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed = EmbedBuilder.warning(
                    "Already Claimed",
                    f"You've already claimed your daily reward! Try again in {hours}h {minutes}m."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Calculate reward (base + level bonus)
        base_reward = 100
        level_bonus = data['level'] * 10
        total_reward = base_reward + level_bonus
        
        # Add randomness
        total_reward += random.randint(-20, 50)
        
        # Update user data
        new_balance = data['balance'] + total_reward
        self.update_user_data(
            interaction.user.id,
            interaction.guild.id,
            balance=new_balance,
            last_daily=datetime.utcnow().isoformat()
        )
        
        # Log daily claim
        economy_logger.info(f'Daily claimed: {interaction.user} ({interaction.user.id}) received ${total_reward:,} (Level {data["level"]} bonus: +${level_bonus}) in guild {interaction.guild.id}')
        
        embed = EmbedBuilder.success(
            "Daily Reward Claimed!",
            f"You received **${total_reward:,}**!"
        )
        embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        embed.add_field(name="Level Bonus", value=f"+${level_bonus}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="work", description="Work to earn money")
    async def work(self, interaction: discord.Interaction):
        """Work to earn currency"""
        data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        # Check cooldown (1 hour)
        if data['last_work']:
            last_work = datetime.fromisoformat(data['last_work'])
            if (datetime.utcnow() - last_work).total_seconds() < 3600:
                time_left = timedelta(hours=1) - (datetime.utcnow() - last_work)
                minutes = int(time_left.total_seconds() // 60)
                
                embed = EmbedBuilder.warning(
                    "Work Cooldown",
                    f"You're tired! Rest for {minutes} more minutes before working again."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Work jobs and rewards
        jobs = [
            ("worked as a developer", 80, 120),
            ("delivered pizza", 50, 90),
            ("walked dogs", 40, 80),
            ("cleaned houses", 60, 100),
            ("taught coding", 90, 150),
            ("fixed computers", 70, 110),
            ("wrote articles", 65, 95),
            ("streamed games", 45, 85)
        ]
        
        job, min_pay, max_pay = random.choice(jobs)
        earnings = random.randint(min_pay, max_pay)
        
        # Level bonus
        level_bonus = data['level'] * 2
        total_earnings = earnings + level_bonus
        
        # Update user data
        new_balance = data['balance'] + total_earnings
        self.update_user_data(
            interaction.user.id,
            interaction.guild.id,
            balance=new_balance,
            last_work=datetime.utcnow().isoformat()
        )
        
        # Log work action
        economy_logger.info(f'Work completed: {interaction.user} ({interaction.user.id}) {job} and earned ${total_earnings:,} (${earnings} + ${level_bonus} level bonus) in guild {interaction.guild.id}')
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"You {job} and earned **${total_earnings:,}**!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Base Pay", value=f"${earnings:,}", inline=True)
        embed.add_field(name="Level Bonus", value=f"+${level_bonus:,}", inline=True)
        embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rob", description="Attempt to rob another user")
    @app_commands.describe(user="The user to rob")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        """Rob another user (risky!)"""
        if user.bot:
            embed = EmbedBuilder.error("Invalid Target", "You can't rob bots!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            embed = EmbedBuilder.error("Invalid Target", "You can't rob yourself!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        robber_data = self.get_user_data(interaction.user.id, interaction.guild.id)
        victim_data = self.get_user_data(user.id, interaction.guild.id)
        
        # Check if robber has enough money to risk
        if robber_data['balance'] < 100:
            embed = EmbedBuilder.error("Not Enough Money", "You need at least $100 to attempt a robbery!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if victim has money to steal
        if victim_data['balance'] < 50:
            embed = EmbedBuilder.warning("Target Too Poor", f"{user.mention} doesn't have enough money to rob!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 60% success rate
        success = random.randint(1, 100) <= 60
        
        if success:
            # Successful robbery
            stolen_amount = random.randint(10, min(victim_data['balance'], 500))
            
            # Update balances
            new_robber_balance = robber_data['balance'] + stolen_amount
            new_victim_balance = victim_data['balance'] - stolen_amount
            
            self.update_user_data(interaction.user.id, interaction.guild.id, balance=new_robber_balance)
            self.update_user_data(user.id, interaction.guild.id, balance=new_victim_balance)
            
            # Log successful robbery
            economy_logger.info(f'Robbery successful: {interaction.user} ({interaction.user.id}) stole ${stolen_amount:,} from {user} ({user.id}) in guild {interaction.guild.id}')
            
            embed = discord.Embed(
                title="💰 Robbery Successful!",
                description=f"You successfully robbed **${stolen_amount:,}** from {user.mention}!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Your New Balance", value=f"${new_robber_balance:,}", inline=True)
            
        else:
            # Failed robbery - lose money
            fine = random.randint(50, min(robber_data['balance'], 200))
            new_balance = robber_data['balance'] - fine
            
            self.update_user_data(interaction.user.id, interaction.guild.id, balance=new_balance)
            
            # Log failed robbery
            economy_logger.info(f'Robbery failed: {interaction.user} ({interaction.user.id}) failed to rob {user} ({user.id}) and paid ${fine:,} fine in guild {interaction.guild.id}')
            
            embed = discord.Embed(
                title="🚨 Robbery Failed!",
                description=f"You got caught and paid a fine of **${fine:,}**!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Your New Balance", value=f"${new_balance:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="deposit", description="Deposit money into your bank")
    @app_commands.describe(amount="Amount to deposit (or 'all')")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        """Deposit money into bank"""
        data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        if amount.lower() == "all":
            deposit_amount = data['balance']
        else:
            try:
                deposit_amount = int(amount)
            except ValueError:
                embed = EmbedBuilder.error("Invalid Amount", "Please enter a valid number or 'all'.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if deposit_amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "You must deposit a positive amount.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if deposit_amount > data['balance']:
            embed = EmbedBuilder.error("Insufficient Funds", f"You only have ${data['balance']:,} in your wallet.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Update balances
        new_wallet = data['balance'] - deposit_amount
        new_bank = data['bank'] + deposit_amount
        
        self.update_user_data(
            interaction.user.id,
            interaction.guild.id,
            balance=new_wallet,
            bank_balance=new_bank
        )
        
        # Log deposit
        economy_logger.info(f'Bank deposit: {interaction.user} ({interaction.user.id}) deposited ${deposit_amount:,} in guild {interaction.guild.id}')
        
        embed = EmbedBuilder.success(
            "Money Deposited",
            f"Successfully deposited **${deposit_amount:,}** into your bank!"
        )
        embed.add_field(name="Wallet", value=f"${new_wallet:,}", inline=True)
        embed.add_field(name="Bank", value=f"${new_bank:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="withdraw", description="Withdraw money from your bank")
    @app_commands.describe(amount="Amount to withdraw (or 'all')")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        """Withdraw money from bank"""
        data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        if amount.lower() == "all":
            withdraw_amount = data['bank']
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                embed = EmbedBuilder.error("Invalid Amount", "Please enter a valid number or 'all'.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if withdraw_amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "You must withdraw a positive amount.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if withdraw_amount > data['bank']:
            embed = EmbedBuilder.error("Insufficient Funds", f"You only have ${data['bank']:,} in your bank.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Update balances
        new_wallet = data['balance'] + withdraw_amount
        new_bank = data['bank'] - withdraw_amount
        
        self.update_user_data(
            interaction.user.id,
            interaction.guild.id,
            balance=new_wallet,
            bank_balance=new_bank
        )
        
        embed = EmbedBuilder.success(
            "Money Withdrawn",
            f"Successfully withdrew **${withdraw_amount:,}** from your bank!"
        )
        embed.add_field(name="Wallet", value=f"${new_wallet:,}", inline=True)
        embed.add_field(name="Bank", value=f"${new_bank:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="pay", description="Give money to another user")
    @app_commands.describe(
        user="The user to pay",
        amount="Amount to pay"
    )
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Transfer money to another user"""
        if user.bot:
            embed = EmbedBuilder.error("Invalid Target", "You can't pay bots!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            embed = EmbedBuilder.error("Invalid Target", "You can't pay yourself!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "You must pay a positive amount.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        payer_data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        if amount > payer_data['balance']:
            embed = EmbedBuilder.error("Insufficient Funds", f"You only have ${payer_data['balance']:,} in your wallet.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Transfer money
        receiver_data = self.get_user_data(user.id, interaction.guild.id)
        
        new_payer_balance = payer_data['balance'] - amount
        new_receiver_balance = receiver_data['balance'] + amount
        
        self.update_user_data(interaction.user.id, interaction.guild.id, balance=new_payer_balance)
        self.update_user_data(user.id, interaction.guild.id, balance=new_receiver_balance)
        
        # Log payment
        economy_logger.info(f'Payment: {interaction.user} ({interaction.user.id}) paid ${amount:,} to {user} ({user.id}) in guild {interaction.guild.id}')
        
        embed = EmbedBuilder.success(
            "Payment Sent",
            f"You paid **${amount:,}** to {user.mention}!"
        )
        embed.add_field(name="Your New Balance", value=f"${new_payer_balance:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Notify receiver
        try:
            receiver_embed = EmbedBuilder.info(
                "Payment Received",
                f"You received **${amount:,}** from {interaction.user.mention}!"
            )
            await user.send(embed=receiver_embed)
        except:
            pass  # DMs disabled
    
    @app_commands.command(name="gamble", description="Gamble your money")
    @app_commands.describe(amount="Amount to gamble")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        """Gamble money with various outcomes"""
        if amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "You must gamble a positive amount.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        data = self.get_user_data(interaction.user.id, interaction.guild.id)
        
        if amount > data['balance']:
            embed = EmbedBuilder.error("Insufficient Funds", f"You only have ${data['balance']:,} in your wallet.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Gambling outcomes
        roll = random.randint(1, 100)
        
        if roll <= 45:  # 45% chance to lose
            lost = amount
            new_balance = data['balance'] - lost
            result = "lost"
            color = discord.Color.red()
            emoji = "📉"
        elif roll <= 85:  # 40% chance to win small
            won = int(amount * random.uniform(0.5, 1.5))
            new_balance = data['balance'] + won
            result = f"won ${won:,}"
            color = discord.Color.green()
            emoji = "📈"
        else:  # 15% chance to win big
            won = int(amount * random.uniform(2, 3))
            new_balance = data['balance'] + won
            result = f"WON BIG ${won:,}"
            color = discord.Color.gold()
            emoji = "🎉"
        
        self.update_user_data(interaction.user.id, interaction.guild.id, balance=new_balance)
        
        # Log gambling result
        if roll <= 45:
            economy_logger.info(f'Gambling loss: {interaction.user} ({interaction.user.id}) lost ${amount:,} (Roll: {roll}) in guild {interaction.guild.id}')
        elif roll <= 85:
            economy_logger.info(f'Gambling win: {interaction.user} ({interaction.user.id}) won ${won:,} from ${amount:,} bet (Roll: {roll}) in guild {interaction.guild.id}')
        else:
            economy_logger.info(f'Gambling JACKPOT: {interaction.user} ({interaction.user.id}) won BIG ${won:,} from ${amount:,} bet (Roll: {roll}) in guild {interaction.guild.id}')
        
        embed = discord.Embed(
            title=f"{emoji} Gambling Result",
            description=f"You {result}!",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Bet Amount", value=f"${amount:,}", inline=True)
        embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="View the server leaderboard")
    @app_commands.describe(category="What to rank by")
    @app_commands.choices(category=[
        app_commands.Choice(name="💰 Money (Total)", value="money"),
        app_commands.Choice(name="⭐ Level", value="level"),
        app_commands.Choice(name="✨ XP", value="xp")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "money"):
        """Display server leaderboards"""
        cursor = self.bot.db.cursor()
        
        if category == "money":
            cursor.execute(
                "SELECT user_id, balance + bank_balance as total FROM user_economy WHERE guild_id = ? ORDER BY total DESC LIMIT 10",
                (interaction.guild.id,)
            )
            title = "💰 Money Leaderboard"
            value_format = lambda x: f"${x:,}"
        elif category == "level":
            cursor.execute(
                "SELECT user_id, level FROM user_economy WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT 10",
                (interaction.guild.id,)
            )
            title = "⭐ Level Leaderboard"
            value_format = lambda x: f"Level {x}"
        else:  # xp
            cursor.execute(
                "SELECT user_id, xp FROM user_economy WHERE guild_id = ? ORDER BY xp DESC LIMIT 10",
                (interaction.guild.id,)
            )
            title = "✨ XP Leaderboard"
            value_format = lambda x: f"{x:,} XP"
        
        results = cursor.fetchall()
        
        if not results:
            embed = EmbedBuilder.info("No Data", "No economy data available yet!")
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        
        for i, (user_id, value) in enumerate(results):
            user_obj = interaction.guild.get_member(user_id)
            username = user_obj.display_name if user_obj else "Unknown User"
            
            leaderboard_text += f"{medals[i]} **{username}** - {value_format(value)}\n"
        
        embed.add_field(name="Top 10", value=leaderboard_text, inline=False)
        
        # User's position if not in top 10
        cursor.execute(
            f"SELECT COUNT(*) + 1 FROM user_economy WHERE guild_id = ? AND {'balance + bank_balance' if category == 'money' else category} > (SELECT {'balance + bank_balance' if category == 'money' else category} FROM user_economy WHERE user_id = ? AND guild_id = ?)",
            (interaction.guild.id, interaction.user.id, interaction.guild.id)
        )
        user_position = cursor.fetchone()[0]
        
        if user_position > 10:
            embed.set_footer(text=f"Your position: #{user_position}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="addmoney", description="Add money to a user (Admin only)")
    @app_commands.describe(
        user="The user to give money to",
        amount="Amount of money to add"
    )
    async def addmoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add money to a user (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /addmoney in {interaction.guild.name} ({interaction.guild.id}) without Administrator permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "Amount must be positive.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        data = self.get_user_data(user.id, interaction.guild.id)
        new_balance = data['balance'] + amount
        
        self.update_user_data(user.id, interaction.guild.id, balance=new_balance)
        
        # Log admin money addition
        economy_logger.info(f'Admin money added: {interaction.user} ({interaction.user.id}) added ${amount:,} to {user} ({user.id}) in guild {interaction.guild.id}')
        
        embed = EmbedBuilder.success(
            "Money Added",
            f"Added **${amount:,}** to {user.mention}'s wallet!"
        )
        embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        embed.add_field(name="Added By", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="removemoney", description="Remove money from a user (Admin only)")
    @app_commands.describe(
        user="The user to remove money from",
        amount="Amount of money to remove"
    )
    async def removemoney(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Remove money from a user (Admin only)"""
        if not interaction.user.guild_permissions.administrator:
            # Log unauthorized access attempt
            security_logger.warning(f'UNAUTHORIZED ADMIN COMMAND: {interaction.user} ({interaction.user.id}) attempted /removemoney in {interaction.guild.name} ({interaction.guild.id}) without Administrator permission')
            
            embed = EmbedBuilder.error("Missing Permissions", "You need the 'Administrator' permission to use this command.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount <= 0:
            embed = EmbedBuilder.error("Invalid Amount", "Amount must be positive.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        data = self.get_user_data(user.id, interaction.guild.id)
        new_balance = max(0, data['balance'] - amount)
        
        self.update_user_data(user.id, interaction.guild.id, balance=new_balance)
        
        # Log admin money removal
        economy_logger.info(f'Admin money removed: {interaction.user} ({interaction.user.id}) removed ${amount:,} from {user} ({user.id}) in guild {interaction.guild.id}')
        
        embed = EmbedBuilder.success(
            "Money Removed",
            f"Removed **${amount:,}** from {user.mention}'s wallet!"
        )
        embed.add_field(name="New Balance", value=f"${new_balance:,}", inline=True)
        embed.add_field(name="Removed By", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
