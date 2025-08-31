@echo off
echo Discord Moderation Bot Starter
echo ================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if dependencies are installed
echo Checking dependencies...
python -c "import discord, aiohttp, psutil" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Check if config is set up
python -c "import json; config = json.load(open('config.json')); assert config['token'] != 'YOUR_BOT_TOKEN_HERE'" >nul 2>&1
if errorlevel 1 (
    echo Error: Please configure your bot token in config.json
    pause
    exit /b 1
)

:: Run the bot
echo Starting Discord Moderation Bot...
python main.py

pause
