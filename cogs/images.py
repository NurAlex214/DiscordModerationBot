import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import random
import aiohttp
import io
import sys
import os

# Add the parent directory to the path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import EmbedBuilder

class ImagesCog(commands.Cog, name="Images & Memes"):
    """Image and meme related commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    
    @app_commands.command(name="servericon", description="Display the server's icon")
    async def servericon(self, interaction: discord.Interaction):
        """Display the server icon"""
        if not interaction.guild.icon:
            embed = EmbedBuilder.error("No Icon", "This server doesn't have an icon set!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏠 {interaction.guild.name}'s Icon",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_image(url=interaction.guild.icon.url)
        
        # Add download links
        icon_formats = []
        if interaction.guild.icon.is_animated():
            icon_formats.append(f"[GIF]({interaction.guild.icon.with_format('gif').url})")
        icon_formats.extend([
            f"[PNG]({interaction.guild.icon.with_format('png').url})",
            f"[JPG]({interaction.guild.icon.with_format('jpg').url})",
            f"[WEBP]({interaction.guild.icon.with_format('webp').url})"
        ])
        
        embed.add_field(
            name="📥 Download Links",
            value=" • ".join(icon_formats),
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="meme", description="Get a random meme")
    async def meme(self, interaction: discord.Interaction):
        """Get a random meme from Reddit"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try multiple subreddits
                subreddits = ['memes', 'dankmemes', 'wholesomememes', 'programmerhumor', 'funny']
                chosen_sub = random.choice(subreddits)
                
                async with session.get(f'https://www.reddit.com/r/{chosen_sub}/random.json', 
                                     headers={'User-Agent': 'Discord Bot'}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data and len(data) > 0:
                            post = data[0]['data']['children'][0]['data']
                            
                            # Skip NSFW content
                            if post.get('over_18', False):
                                embed = EmbedBuilder.warning("NSFW Content", "Got NSFW content, try again!")
                                await interaction.followup.send(embed=embed, ephemeral=True)
                                return
                            
                            embed = discord.Embed(
                                title=post['title'][:256],  # Discord title limit
                                url=f"https://reddit.com{post['permalink']}",
                                color=discord.Color.orange(),
                                timestamp=datetime.utcnow()
                            )
                            
                            # Check if it's an image
                            if post.get('url', '').endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                embed.set_image(url=post['url'])
                            elif post.get('selftext'):
                                # Text post
                                text = post['selftext'][:1024]  # Discord description limit
                                embed.description = text
                            
                            embed.add_field(
                                name="📊 Stats",
                                value=f"👍 {post.get('ups', 0)} | 💬 {post.get('num_comments', 0)}",
                                inline=True
                            )
                            
                            embed.add_field(
                                name="📍 Source",
                                value=f"r/{chosen_sub}",
                                inline=True
                            )
                            
                            embed.set_footer(
                                text=f"Posted by u/{post.get('author', 'unknown')}",
                                icon_url="https://www.redditstatic.com/shreddit/assets/favicon/192x192.png"
                            )
                            
                            await interaction.followup.send(embed=embed)
                            return
            
            # Fallback if Reddit API fails
            embed = EmbedBuilder.error("Meme Not Found", "Couldn't fetch a meme right now. Try again later!")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = EmbedBuilder.error("Error", "Failed to fetch meme. Please try again!")
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    
    @app_commands.command(name="pickup", description="Get a cheesy pickup line")
    async def pickup(self, interaction: discord.Interaction):
        """Get a random pickup line"""
        pickup_lines = [
            "Are you a magician? Because whenever I look at you, everyone else disappears! ✨",
            "Do you have a map? I keep getting lost in your eyes! 🗺️",
            "Are you a parking ticket? Because you've got FINE written all over you! 🎫",
            "Is your name Google? Because you have everything I've been searching for! 🔍",
            "Are you a time traveler? Because I see you in my future! ⏰",
            "Do you believe in love at first sight, or should I walk by again? 👀",
            "Are you a campfire? Because you're hot and I want s'more! 🔥",
            "Do you have a Band-Aid? Because I just scraped my knee falling for you! 🩹",
            "Are you a WiFi signal? Because I'm feeling a connection! 📶",
            "Is your dad a boxer? Because you're a knockout! 🥊",
            "Are you made of copper and tellurium? Because you're Cu-Te! ⚗️",
            "Do you have a sunburn, or are you always this hot? ☀️",
            "Are you a camera? Because every time I look at you, I smile! 📸",
            "Is your name Chapstick? Because you're da balm! 💋",
            "Are you an interior decorator? Because when I saw you, the room became beautiful! 🏠"
        ]
        
        pickup_line = random.choice(pickup_lines)
        
        embed = discord.Embed(
            title="😏 Pickup Line",
            description=pickup_line,
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⚠️ Warning",
            value="Use at your own risk! Results not guaranteed! 😅",
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="cat", description="Get a random cat image")
    async def cat(self, interaction: discord.Interaction):
        """Get a random cat image"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        cat_url = data[0]['url']
                        
                        embed = discord.Embed(
                            title="🐱 Random Cat",
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
                        
                        embed.set_image(url=cat_url)
                        embed.set_footer(
                            text=f"Meow! Requested by {interaction.user.display_name}",
                            icon_url=interaction.user.display_avatar.url
                        )
                        
                        await interaction.followup.send(embed=embed)
                        return
        except:
            pass
        
        # Fallback if API fails
        embed = EmbedBuilder.error("Cat Error", "Couldn't fetch a cat image right now. The cats are probably napping! 😴")
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="dog", description="Get a random dog image")
    async def dog(self, interaction: discord.Interaction):
        """Get a random dog image"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://dog.ceo/api/breeds/image/random') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data['status'] == 'success':
                            dog_url = data['message']
                            
                            embed = discord.Embed(
                                title="🐶 Random Dog",
                                color=discord.Color.brown(),
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.set_image(url=dog_url)
                            embed.set_footer(
                                text=f"Woof! Requested by {interaction.user.display_name}",
                                icon_url=interaction.user.display_avatar.url
                            )
                            
                            await interaction.followup.send(embed=embed)
                            return
        except:
            pass
        
        # Fallback if API fails
        embed = EmbedBuilder.error("Dog Error", "Couldn't fetch a dog image right now. The dogs are probably playing fetch! 🎾")
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="fox", description="Get a random fox image")
    async def fox(self, interaction: discord.Interaction):
        """Get a random fox image"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://randomfox.ca/floof/') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        fox_url = data['image']
                        
                        embed = discord.Embed(
                            title="🦊 Random Fox",
                            color=discord.Color.orange(),
                            timestamp=datetime.utcnow()
                        )
                        
                        embed.set_image(url=fox_url)
                        embed.set_footer(
                            text=f"What does the fox say? Requested by {interaction.user.display_name}",
                            icon_url=interaction.user.display_avatar.url
                        )
                        
                        await interaction.followup.send(embed=embed)
                        return
        except:
            pass
        
        # Fallback if API fails
        embed = EmbedBuilder.error("Fox Error", "Couldn't fetch a fox image right now. The foxes are being sneaky! 🦊")
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="duck", description="Get a random duck image")
    async def duck(self, interaction: discord.Interaction):
        """Get a random duck image"""
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://random-d.uk/api/random') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        duck_url = data['url']
                        
                        embed = discord.Embed(
                            title="🦆 Random Duck",
                            color=discord.Color.yellow(),
                            timestamp=datetime.utcnow()
                        )
                        
                        embed.set_image(url=duck_url)
                        embed.set_footer(
                            text=f"Quack! Requested by {interaction.user.display_name}",
                            icon_url=interaction.user.display_avatar.url
                        )
                        
                        await interaction.followup.send(embed=embed)
                        return
        except:
            pass
        
        # Fallback if API fails
        embed = EmbedBuilder.error("Duck Error", "Couldn't fetch a duck image right now. The ducks are swimming away! 🏊‍♂️")
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ascii", description="Convert text to ASCII art")
    @app_commands.describe(text="Text to convert to ASCII art (max 10 characters)")
    async def ascii(self, interaction: discord.Interaction, text: str):
        """Convert text to simple ASCII art"""
        if len(text) > 10:
            embed = EmbedBuilder.error("Text Too Long", "Please use 10 characters or less!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Simple ASCII art mapping
        ascii_chars = {
            'A': ['  ▄▀█  ', ' █▀▀█  ', ' █▄▄█  ', ' ▀  ▀  '],
            'B': [' █▀▀▄  ', ' █▀▀▄  ', ' █▄▄▀  ', '       '],
            'C': [' ▄▀█▀▄ ', ' █     ', ' ▀▄█▄▀ ', '       '],
            'D': [' █▀▀▄  ', ' █   █ ', ' █▄▄▀  ', '       '],
            'E': [' █▀▀▀  ', ' █▀▀   ', ' █▄▄▄  ', '       '],
            'H': [' █   █ ', ' █▀▀▀█ ', ' █   █ ', '       '],
            'I': [' ▀█▀   ', '  █    ', ' ▄█▄   ', '       '],
            'L': [' █     ', ' █     ', ' █▄▄▄  ', '       '],
            'O': [' ▄▀█▀▄ ', ' █   █ ', ' ▀▄█▄▀ ', '       '],
            'R': [' █▀▀▄  ', ' █▀▀▄  ', ' █  ▀▄ ', '       '],
            'S': [' ▄▀▀▀▄ ', ' ▀▀▀▄  ', ' ▄▄▄▀  ', '       '],
            'T': [' ▀▀█▀▀ ', '   █   ', '   █   ', '       '],
            'U': [' █   █ ', ' █   █ ', ' ▀▄▄▄▀ ', '       '],
            ' ': ['       ', '       ', '       ', '       ']
        }
        
        text = text.upper()
        ascii_lines = ['', '', '', '']
        
        for char in text:
            if char in ascii_chars:
                for i in range(4):
                    ascii_lines[i] += ascii_chars[char][i]
            else:
                # Use a generic pattern for unsupported characters
                for i in range(4):
                    ascii_lines[i] += ' █████ '
        
        ascii_art = '\\n'.join(ascii_lines)
        
        embed = discord.Embed(
            title="🎨 ASCII Art",
            description=f"```\\n{ascii_art}\\n```",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 Original Text",
            value=f"`{text}`",
            inline=False
        )
        
        embed.set_footer(
            text=f"Generated for {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="color", description="Display information about a color")
    @app_commands.describe(color="Hex color code (e.g., #FF5733 or FF5733)")
    async def color(self, interaction: discord.Interaction, color: str):
        """Display information about a hex color"""
        # Clean the color input
        color = color.strip().replace('#', '')
        
        # Validate hex color
        if len(color) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in color):
            embed = EmbedBuilder.error("Invalid Color", "Please provide a valid hex color code (e.g., #FF5733 or FF5733)")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        color = color.upper()
        
        # Convert hex to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Create embed with the color
        try:
            discord_color = discord.Color(int(color, 16))
        except:
            discord_color = discord.Color.default()
        
        embed = discord.Embed(
            title=f"🎨 Color Information",
            description=f"Color preview for **#{color}**",
            color=discord_color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🔢 Hex", value=f"`#{color}`", inline=True)
        embed.add_field(name="🎯 RGB", value=f"`rgb({r}, {g}, {b})`", inline=True)
        embed.add_field(name="📊 HSL", value=f"`Coming soon...`", inline=True)
        
        # Color brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        if brightness > 128:
            embed.add_field(name="💡 Brightness", value="Light color", inline=True)
        else:
            embed.add_field(name="💡 Brightness", value="Dark color", inline=True)
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Add a color preview (using a 1x1 pixel image with the color)
        embed.set_thumbnail(url=f"https://via.placeholder.com/150x150/{color}/{color}.png")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="qr", description="Generate a QR code for text")
    @app_commands.describe(text="Text to encode in QR code")
    async def qr(self, interaction: discord.Interaction, text: str):
        """Generate a QR code for the given text"""
        if len(text) > 500:
            embed = EmbedBuilder.error("Text Too Long", "Please use 500 characters or less!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # URL encode the text for the QR API
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_text}"
        
        embed = discord.Embed(
            title="📱 QR Code Generator",
            description=f"QR Code for: `{text[:100]}{'...' if len(text) > 100 else ''}`",
            color=discord.Color.dark_grey(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_image(url=qr_url)
        
        embed.add_field(
            name="📋 Instructions",
            value="Scan this QR code with your phone's camera or QR reader app!",
            inline=False
        )
        
        embed.set_footer(
            text=f"Generated for {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="emoji", description="Get information about an emoji")
    @app_commands.describe(emoji="The emoji to get information about")
    async def emoji_info(self, interaction: discord.Interaction, emoji: str):
        """Get information about an emoji"""
        if len(emoji) != 1:
            embed = EmbedBuilder.error("Invalid Emoji", "Please provide a single emoji!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get unicode information
        unicode_name = emoji.encode('unicode_escape').decode('ascii')
        unicode_point = f"U+{ord(emoji):04X}"
        
        embed = discord.Embed(
            title="😀 Emoji Information",
            description=f"Information about: {emoji}",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📝 Character", value=f"`{emoji}`", inline=True)
        embed.add_field(name="🔢 Unicode", value=f"`{unicode_point}`", inline=True)
        embed.add_field(name="💾 Escape", value=f"`{unicode_name}`", inline=True)
        
        # Make the emoji big
        embed.add_field(
            name="🔍 Preview",
            value=emoji * 5,
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ImagesCog(bot))
