# Contributing to Discord Moderation Bot

**Developed by alexistcooked**

Thank you for your interest in contributing to this Discord bot! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Basic understanding of Discord.py
- Familiarity with async/await programming
- Discord bot development experience (recommended)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/discord-moderation-bot.git
   cd discord-moderation-bot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up test bot**
   - Create a test Discord server
   - Create a separate bot application for testing
   - Configure `config.json` with test bot token

5. **Run tests**
   ```bash
   python test_all_commands.py
   ```

## 📝 Code Style

### Python Style Guidelines
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write descriptive docstrings for all functions and classes
- Keep functions focused and single-purpose

### Discord.py Best Practices
- Always use slash commands (`app_commands`) for new features
- Include proper error handling with user-friendly messages
- Use embeds for rich message formatting
- Implement confirmation dialogs for destructive actions
- Add logging for all significant actions

### Code Organization
```python
# Standard imports first
import discord
from discord.ext import commands

# Third-party imports
import aiohttp
import asyncio

# Local imports last
from utils.helpers import EmbedBuilder
```

### Example Command Structure
```python
@app_commands.command(name="example", description="Example command")
@app_commands.describe(
    user="The user to target",
    reason="Reason for the action"
)
async def example(
    self, 
    interaction: discord.Interaction, 
    user: discord.Member,
    reason: str = "No reason provided"
):
    """Example command with proper structure"""
    # Permission check
    if not interaction.user.guild_permissions.manage_messages:
        embed = EmbedBuilder.error("Missing Permissions", "You need Manage Messages permission.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Action logic
    try:
        # Do something
        embed = EmbedBuilder.success("Success", f"Action completed for {user.mention}")
        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden:
        embed = EmbedBuilder.error("Permission Error", "Bot lacks necessary permissions.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = EmbedBuilder.error("Error", f"An error occurred: {str(e)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
```

## 🛠️ Making Contributions

### Types of Contributions
- 🐛 **Bug Fixes**: Fix existing issues
- ✨ **New Features**: Add new commands or functionality
- 📚 **Documentation**: Improve README, comments, or guides
- 🎨 **UI/UX**: Improve embed designs or interactive elements
- ⚡ **Performance**: Optimize code or database queries
- 🔒 **Security**: Enhance security or permission systems

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add or update tests as needed
   - Update documentation if necessary

3. **Test your changes**
   ```bash
   python test_all_commands.py
   ```

4. **Commit with descriptive messages**
   ```bash
   git commit -m "Add: New moderation command for bulk user management"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines
- **Clear Title**: Describe what the PR does
- **Detailed Description**: Explain the changes and why they're needed
- **Testing**: Confirm all tests pass
- **Documentation**: Update relevant docs
- **No Breaking Changes**: Unless discussed in an issue first

## 🐛 Reporting Issues

### Bug Reports
Include the following information:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: How to trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python version, OS, Discord.py version
- **Logs**: Relevant error messages or logs

### Feature Requests
- **Description**: Clear description of the feature
- **Use Case**: Why this feature would be useful
- **Implementation Ideas**: Suggestions for how it could work
- **Alternatives**: Other solutions considered

## 📋 Coding Standards

### Required for All Contributions
- ✅ Code must pass the test suite
- ✅ New features must include tests
- ✅ All functions must have docstrings
- ✅ Error handling must be implemented
- ✅ Logging must be added for significant actions
- ✅ Permission checks must be included for admin commands

### Security Requirements
- 🔒 All admin commands must check permissions
- 🔒 User input must be validated
- 🔒 Sensitive information must never be logged
- 🔒 Rate limiting should be considered for resource-intensive commands

### Database Guidelines
- Use parameterized queries to prevent SQL injection
- Include proper error handling for database operations
- Update schema documentation if adding new tables/columns
- Test database migrations thoroughly

## 🔄 Development Workflow

### Adding a New Command
1. **Choose the appropriate cog** (or create new one if needed)
2. **Implement the command** following the established patterns
3. **Add permission checks** and error handling
4. **Include logging** for the action
5. **Test thoroughly** with different permission levels
6. **Update documentation** as needed

### Adding a New Cog
1. **Create the cog file** in the `cogs/` directory
2. **Follow the established structure** (see existing cogs)
3. **Add the cog** to the load list in `main.py`
4. **Include proper imports** and error handling
5. **Add comprehensive tests**
6. **Document all commands**

## 🎯 Code Review Process

### What We Look For
- **Functionality**: Does the code work as intended?
- **Security**: Are permissions and validation proper?
- **Performance**: Is the code efficient?
- **Maintainability**: Is the code clean and well-documented?
- **Testing**: Are there adequate tests?

### Common Issues to Avoid
- Missing permission checks on admin commands
- Inadequate error handling
- Lack of user input validation
- Missing logging for security-relevant actions
- Blocking operations without proper async handling

## 🙋‍♂️ Getting Help

- **Discord Server**: Join our development Discord (if available)
- **Issues**: Open an issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check existing docs and command reference

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

**Thank you for contributing to make this Discord bot better! 🚀**
