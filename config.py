# ============================================================
# Group Manager Bot
# Author: LearningBotsOfficial (https://github.com/LearningBotsOfficial) 
# Support: https://t.me/LearningBotsCommunity
# Channel: https://t.me/learning_bots
# YouTube: https://youtube.com/@learning_bots
# License: Open-source (keep credits, no resale)
# ============================================================

import os

# Required configurations (loaded from environment variables)
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "Cluster0")

# Owner and bot details
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "NomadeHelpBot")

# Sudo Users (Owner is always sudo)
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split()))
SUDOERS = list(set([OWNER_ID] + SUDO_USERS))

# AI & Abuse Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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") 
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Links and visuals
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "https://t.me/LearningBotsCommunity")
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/Learning_Bots")
START_IMAGE = os.getenv("START_IMAGE", "https://files.catbox.moe/j2yhce.jpg")

# Abusive Words List (Hinglish + English)
ABUSIVE_WORDS = [
    "madarchod", "Madharchod", "Madharchood", "behenchod", "madherchood", "madherchod", "bhenchod", "maderchod", "mc", "bc", "bsdk", 
    "bhosdike", "bhosdiwala", "chutiya", "chutiyapa", "gandu", "gand", 
    "lodu", "lode", "lauda", "lund", "lawda", "lavda", "aand", "jhant", 
    "jhaant", "chut", "chuchi", "tatte", "tatti", "gaand", "gaandmar", 
    "gaandmasti", "gaandfat", "gaandmara", "kamina", "kamine", "harami", 
    "haraami", "nalayak", "nikamma", "kutte", "kutta", "kutti", "saala", 
    "saali", "bhadwa", "bhadwe", "randi", "randibaaz", "bkl", "l*da", 
    "l@da", "ch*tiya", "g@ndu", "behench*d", "bhench0d", "madarxhod", 
    "chutya", "chuteya", "rand", "ramdi", "choot", "bhosda", "fuck", 
    "bitch", "bastard", "asshole", "motherfucker", "dick", "tmkc", "mkc"
]
