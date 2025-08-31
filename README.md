# 🤖 Advanced Discord Moderation Bot

**Developed by alexistcooked**

<div align="center">

![Discord Bot](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Commands](https://img.shields.io/badge/Commands-96-orange?style=for-the-badge)

**A comprehensive Discord moderation bot with 96+ commands, economy system, interactive games, and advanced security features!**

[Features](#-features) • [Installation](#-installation) • [Commands](#-commands) • [Documentation](#-documentation)

</div>

---

## 🌟 Features

### 🔨 **Advanced Moderation System**
- **User Management**: Ban, kick, timeout, warn with confirmation dialogs
- **Warning System**: Track warnings with auto-actions (timeout/kick after X warnings)
- **Mass Moderation**: Mass ban, server lockdown, bulk message deletion
- **Role Hierarchy**: Enforced permission hierarchy - can't moderate higher roles
- **Audit Logging**: All moderation actions logged with detailed information

### 💰 **Complete Economy System**
- **Virtual Currency**: Wallet and bank system with interest
- **Income Sources**: Daily rewards, work commands, gambling
- **User Interaction**: Pay other users, robbery mechanics (with risk/reward)
- **Leveling System**: XP and levels with progression rewards
- **Leaderboards**: Server rankings for money, levels, and XP
- **Admin Controls**: Add/remove money with full audit trails

### 🎮 **Interactive Entertainment**
- **Games**: Trivia, riddles, hangman, rock-paper-scissors
- **Social Commands**: Hug, kiss, pat, slap with animated GIFs
- **Polls & Giveaways**: Interactive voting and timed giveaways
- **Random Generators**: Dice, coin flip, magic 8-ball, quotes
- **Image APIs**: Random cats, dogs, memes from Reddit

### ⚙️ **Server Management Tools**
- **Channel Management**: Create, delete, lock/unlock channels with UI
- **Role Management**: Interactive role assignment with dropdowns
- **Server Info**: Detailed server statistics and member analytics
- **Utility Commands**: User info, avatars, bot statistics
- **Announcement System**: Styled announcements with @everyone options

### 🛡️ **Security & Logging**
- **Comprehensive Logging**: All actions logged to console and `bot.log`
- **Security Monitoring**: Unauthorized access attempts logged
- **Permission Enforcement**: Role hierarchy and Discord permission validation
- **Error Handling**: Global error handlers with user-friendly messages
- **Admin Command Protection**: All admin functions require proper permissions

### 🎯 **Advanced Features**
- **Interactive UI**: Buttons, modals, dropdowns for user-friendly experience
- **Confirmation Systems**: Destructive actions require explicit confirmation
- **Cooldown Management**: Prevents spam with smart cooldown systems
- **Database Integration**: SQLite for persistent data with automatic schema management
- **Auto-Moderation**: Configurable content filtering and spam detection

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/discord-moderation-bot.git
   cd discord-moderation-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   - Edit `config.json` with your bot token:
   ```json
   {
       "token": "YOUR_BOT_TOKEN_HERE",
       "prefix": "!",
       "owner_ids": [YOUR_USER_ID],
       "log_channel": null
   }
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```
   
   *Or on Windows, double-click `start_bot.bat`*

### Discord Bot Setup

1. **Create Bot Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application → Bot → Copy token

2. **Bot Permissions**:
   - **Recommended**: Administrator permission (simplest setup)
   - **Minimum Required**:
     - Manage Server, Manage Channels, Manage Roles
     - Ban Members, Kick Members, Moderate Members
     - Manage Messages, Send Messages, Use Slash Commands
     - View Audit Log, Manage Nicknames

3. **Invite Bot**:
   - Use Discord's OAuth2 URL generator
   - Select "bot" and "applications.commands" scopes
   - Choose permissions and invite to your server

---

## 🎯 Commands Overview

### 📊 **Command Statistics**
- **Total Commands**: 96 slash commands
- **Categories**: 11 different command categories
- **Interactive Elements**: 20+ UI components (buttons, modals, dropdowns)
- **Permission Levels**: From public to administrator-only

### 🗂️ **Command Categories**

| Category | Commands | Description |
|----------|----------|-------------|
| 🔨 **Moderation** | 13 | Ban, kick, warn, timeout, mass moderation |
| ⚙️ **Administration** | 9 | Purge, slowmode, roles, channels, announcements |
| 💰 **Economy** | 11 | Currency, banking, work, gambling, leaderboards |
| 🔍 **Utility** | 6 | User info, server info, bot stats, ping |
| 🎉 **Fun & Interactive** | 9 | Polls, giveaways, games, 8-ball, dice |
| 💕 **Social** | 10 | Hug, kiss, pat, social interactions |
| 🖼️ **Images & Memes** | 4+ | Random images, memes, server icons |
| 🏠 **Server Management** | 8+ | Channel/role management, cleanup |
| 🎵 **Entertainment** | 5+ | Trivia, riddles, mini-games |
| ⚙️ **Settings** | 4+ | Bot configuration, automod settings |
| 🤖 **AutoMod** | 1+ | Automatic moderation configuration |

> 📋 **See [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md) for complete command list with syntax and permissions**

---

## 🚀 Quick Start Guide

### First Time Setup
1. **Start the bot** → Slash commands auto-sync
2. **Run `/settings`** → Configure server settings
3. **Run `/setlogchannel #mod-logs`** → Set moderation log channel
4. **Run `/toggleautomod true`** → Enable automatic moderation
5. **Test with `/ping`** → Verify bot is responsive

### Essential Commands to Try
```
/help              → Interactive help system
/ping              → Check bot latency  
/serverinfo        → Server statistics
/balance           → Check your economy profile
/daily             → Claim daily reward
/poll "Question?" Option1 Option2  → Create interactive poll
```

### Admin Commands (Require Permissions)
```
/purge 10          → Delete 10 messages
/ban @user spam    → Ban user for spam
/createrole MyRole #ff0000  → Create red role
/channels          → Interactive channel manager
```

---

## 🏗️ Project Structure

```
discord-moderation-bot/
├── main.py                 # Main bot file and startup logic
├── config.json            # Bot configuration (token, settings)
├── requirements.txt       # Python dependencies
├── start_bot.bat         # Windows startup script
├── test_all_commands.py  # Comprehensive testing script
├── COMMAND_REFERENCE.md  # Complete command documentation
├── cogs/                 # Command modules (11 cogs)
│   ├── admin.py          # Administrative commands
│   ├── moderation.py     # Moderation and user management
│   ├── economy.py        # Economy and leveling system
│   ├── utility.py        # Information and utility commands
│   ├── fun.py            # Interactive games and entertainment
│   ├── social.py         # Social interaction commands
│   ├── images.py         # Image and meme commands
│   ├── server_management.py  # Server management tools
│   ├── settings.py       # Bot configuration commands
│   ├── automod.py        # Auto-moderation features
│   └── music.py          # Entertainment and music features
└── utils/
    ├── __init__.py       # Package initializer
    └── helpers.py        # Utility classes and functions
```

---

## 🔧 Configuration

### Database
- **Type**: SQLite (automatic setup)
- **Location**: `moderation.db` (auto-created)
- **Tables**: warnings, mutes, guild_settings, user_economy, shop_items

### Logging
- **Console Output**: Real-time colored logging
- **File Output**: `bot.log` with detailed information
- **Categories**: Admin actions, moderation, economy, security, errors

### Auto-Moderation
- **Content Filtering**: Configurable word filters
- **Spam Detection**: Rate limiting and duplicate message detection
- **Link Filtering**: Block or allow specific domains
- **Auto-Actions**: Warn, timeout, or ban based on violations

---

## 🧪 Testing

Run the included test script to verify all functionality:

```bash
python test_all_commands.py
```

This will verify:
- ✅ All 11 cogs load correctly
- ✅ All 96 commands register properly
- ✅ Database schema is correct
- ✅ Permission system works
- ✅ Import dependencies are satisfied

---

## 📚 Documentation

- **[COMMAND_REFERENCE.md](COMMAND_REFERENCE.md)** - Complete list of all 96 commands
- **[Installation Guide](#-installation)** - Step-by-step setup instructions
- **[Permission Guide](#discord-bot-setup)** - Required Discord permissions
- **Inline Help** - Use `/help` in Discord for interactive command browser

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📋 Roadmap

- [ ] Web dashboard for server configuration
- [ ] Custom command creation system
- [ ] Advanced economy features (shops, items)
- [ ] Music playback capabilities
- [ ] Integration with external APIs
- [ ] Multi-language support

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⭐ Support

If this bot helped you, consider:
- ⭐ Starring this repository
- 🐛 Reporting bugs via Issues
- 💡 Suggesting features via Issues
- 🤝 Contributing code via Pull Requests

---

<div align="center">

**Made with ❤️ for the Discord community**

*Last Updated: August 2025*

</div>
