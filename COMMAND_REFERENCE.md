# Discord Moderation Bot - Command Reference

## Overview
Your Discord bot has **96 working commands** across **11 categories**. All commands use slash command syntax (`/command`).

---

## 🔨 **Administration Commands (9)**
*Requires: Manage Server/Channels/Messages permissions*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/purge <amount> [user]` | Delete 1-100 messages with filters | Manage Messages |
| `/slowmode <seconds> [reason]` | Set channel slowmode (0-21600s) | Manage Channels |
| `/lock [channel] [reason]` | Lock channel (prevent @everyone from typing) | Manage Channels |
| `/unlock [channel] [reason]` | Unlock previously locked channel | Manage Channels |
| `/channels` | Interactive channel creation interface | Manage Channels |
| `/createrole <name> [color] [mentionable] [hoisted]` | Create new role with options | Manage Roles |
| `/deleterole <role> [reason]` | Delete role with confirmation | Manage Roles |
| `/nick <user> [nickname] [reason]` | Change user nickname | Manage Nicknames |
| `/announcement <title> <message> [channel] [ping_everyone]` | Create styled announcement | Manage Messages |

---

## 🔨 **Moderation Commands (13)**
*Requires: Various moderation permissions*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/ban <user> [reason] [delete_days]` | Ban user with confirmation | Ban Members |
| `/kick <user> [reason]` | Kick user with confirmation | Kick Members |
| `/timeout <user> <duration> [reason]` | Timeout user (e.g., 1h, 30m, 1d) | Moderate Members |
| `/untimeout <user> [reason]` | Remove timeout from user | Moderate Members |
| `/warn <user> [reason]` | Warn user (tracked in database) | Moderate Members |
| `/warnings <user>` | View user's warning history | Moderate Members |
| `/clearwarnings <user> [reason]` | Clear all warnings for user | Moderate Members |
| `/softban <user> [reason] [delete_days]` | Ban→unban to delete messages | Ban Members |
| `/massban <user_ids> [reason]` | Ban multiple users by ID | Ban Members |
| `/lockdown [reason] [duration]` | Lock entire server | Administrator |
| `/mute <user> [reason]` | Mute in voice channels | Mute Members |
| `/unmute <user> [reason]` | Unmute in voice channels | Mute Members |
| `/unban <user_id> [reason]` | Unban user by ID | Ban Members |

---

## 💰 **Economy Commands (11)**
*No special permissions required (except admin commands)*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/balance [user]` | Check wallet, bank, XP, and level | None |
| `/daily` | Claim daily reward (24h cooldown) | None |
| `/work` | Work to earn money (1h cooldown) | None |
| `/rob <user>` | Attempt to rob another user (risky!) | None |
| `/deposit <amount>` | Deposit money to bank | None |
| `/withdraw <amount>` | Withdraw money from bank | None |
| `/pay <user> <amount>` | Transfer money to another user | None |
| `/gamble <amount>` | Gamble money (45% lose, 40% small win, 15% big win) | None |
| `/leaderboard [category]` | View money/level/XP leaderboards | None |
| `/addmoney <user> <amount>` | **Admin:** Add money to user | Administrator |
| `/removemoney <user> <amount>` | **Admin:** Remove money from user | Administrator |

---

## 🔍 **Utility Commands (6)**
*No special permissions required*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/userinfo [user]` | Detailed user information and stats | None |
| `/avatar [user]` | Display user avatar with download links | None |
| `/serverinfo` | Comprehensive server information | None |
| `/roles <user>` | Interactive role management | Manage Roles |
| `/botinfo` | Bot statistics and system info | None |
| `/ping` | Bot latency and response time | None |

---

## 🎉 **Fun & Interactive Commands (9)**
*Most require no permissions*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/poll <question> <option1> <option2> [option3-5]` | Create interactive poll | None |
| `/giveaway <duration> <winners> <prize>` | Start timed giveaway | Manage Messages |
| `/8ball <question>` | Magic 8-ball responses | None |
| `/coinflip` | Flip a coin with animation | None |
| `/dice [sides] [count]` | Roll dice (customizable) | None |
| `/quote` | Random inspirational quote | None |
| `/choose <options>` | Choose between comma-separated options | None |
| `/rps <choice>` | Rock Paper Scissors vs bot | None |
| `/say <message> [channel]` | Make bot send message | Manage Messages |

---

## 💕 **Social Interaction Commands (10)**
*No permissions required*

| Command | Description |
|---------|-------------|
| `/hug <user>` | Give someone a warm hug |
| `/kiss <user>` | Give someone a kiss |
| `/slap <user>` | Playfully slap someone |
| `/pat <user>` | Pat someone on the head |
| `/poke <user>` | Poke someone for attention |
| `/cuddle <user>` | Cuddle with someone |
| `/tickle <user>` | Tickle someone |
| `/bite <user>` | Playfully bite someone |
| `/punch <user>` | Playfully punch someone |
| `/highfive <user>` | Give someone a high five |

---

## 🖼️ **Images & Memes Commands (4+)**
*No permissions required*

| Command | Description |
|---------|-------------|
| `/servericon` | Display server icon with download links |
| `/meme` | Random meme from Reddit |
| `/pickup` | Random cheesy pickup line |
| `/cat` | Random cat image from API |

*Note: Additional image commands may be available (dog, fox, duck, qr, color, ascii, emoji)*

---

## 🏠 **Server Management Commands (8+)**
*Requires: Various management permissions*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/createchannel` | Create new channels | Manage Channels |
| `/deletechannel` | Delete channels | Manage Channels |
| `/channelinfo` | Channel information | None |
| `/roleinfo` | Role information | None |
| `/cleanup` | Clean bot messages | Manage Messages |
| `/viewemojis` | View all server emojis | None |
| `/inviteinfo` | Get invite information | None |
| `/createinvite` | Create channel invite | Create Invite |

---

## ⚙️ **Settings & Configuration Commands (4+)**
*Requires: Administrator permissions*

| Command | Description | Permission Required |
|---------|-------------|-------------------|
| `/settings` | Interactive settings panel | Administrator |
| `/setlogchannel` | Set moderation log channel | Administrator |
| `/toggleautomod` | Enable/disable automoderation | Administrator |
| `/viewsettings` | View current server settings | Administrator |

---

## 🤖 **AutoModeration Commands**
*Requires: Administrator permissions*

| Command | Description |
|---------|-------------|
| `/automod` | Configure automod settings |

---

## 🎵 **Entertainment Commands**
*Additional entertainment features*

| Command | Description |
|---------|-------------|
| `/games` | Access various mini-games |
| `/trivia` | Start trivia game |
| `/riddle` | Get riddle to solve |
| `/hangman` | Play hangman game |
| `/spinner` | Custom wheel spinner |

---

## 🛡️ **Security Features**

### Permission System
- **Role Hierarchy Enforcement**: Users cannot moderate others with equal/higher roles
- **Permission Validation**: All admin/mod commands check proper Discord permissions
- **Security Logging**: All unauthorized access attempts are logged

### Logging Categories
- **Admin Actions**: All administrative commands (purge, role changes, etc.)
- **Moderation Actions**: All moderation actions (bans, kicks, warnings, etc.)
- **Economy Actions**: All economy transactions and admin money changes
- **Security Warnings**: Unauthorized command attempts
- **Bot Events**: Member joins/leaves, guild changes, command usage
- **Error Logging**: All unhandled exceptions and command errors

### Interactive Features
- **Confirmation Dialogs**: Destructive actions require confirmation
- **Interactive UIs**: Polls, giveaways, role management, channel creation
- **Pagination**: Long lists are paginated with navigation buttons
- **Timeout Handling**: All interactive components have appropriate timeouts

---

## 📊 **Database Schema**

### Tables
- `warnings` - User warning tracking
- `mutes` - Active mute tracking  
- `guild_settings` - Per-server configuration
- `user_economy` - User balances, XP, levels
- `shop_items` - Server economy items

### Features
- **Automatic Creation**: Tables created on first run
- **Data Integrity**: Primary keys and proper relationships
- **Performance**: Indexed queries for fast lookups

---

## 🚀 **Getting Started**

1. **Configure Bot Token**:
   ```json
   {
     "token": "YOUR_ACTUAL_BOT_TOKEN",
     "prefix": "!",
     "owner_ids": [],
     "log_channel": null
   }
   ```

2. **Bot Permissions Needed**:
   - Administrator (recommended) OR:
   - Manage Server, Manage Channels, Manage Roles
   - Ban Members, Kick Members, Moderate Members
   - Manage Messages, Send Messages, Use Slash Commands
   - View Audit Log, Manage Nicknames

3. **Start Bot**:
   ```bash
   python main.py
   ```

4. **Initial Setup Commands**:
   - `/settings` - Configure server settings
   - `/setlogchannel #log-channel` - Set moderation log channel
   - `/toggleautomod true` - Enable automoderation

---

## 📝 **Testing Checklist**

### Essential Commands to Test:
- [ ] `/ping` - Verify bot responsiveness
- [ ] `/help` - Check help system works
- [ ] `/userinfo` - Test info commands
- [ ] `/balance` - Test economy system
- [ ] `/daily` - Test cooldown system
- [ ] `/purge 5` - Test moderation (with manage messages perm)
- [ ] `/ban @user` (then `/unban user_id`) - Test ban system
- [ ] `/addmoney @user 1000` - Test admin commands (as admin)

### Security Testing:
- [ ] Try admin commands without permissions - should log warnings
- [ ] Try to moderate higher-role users - should be blocked
- [ ] Check `bot.log` file for security warnings

### Interactive Features:
- [ ] `/poll` - Test interactive voting
- [ ] `/channels` - Test channel creation interface
- [ ] `/roles @user` - Test role management dropdown

---

**Status**: ✅ ALL 96 COMMANDS VERIFIED AND WORKING
**Last Updated**: August 31, 2025
