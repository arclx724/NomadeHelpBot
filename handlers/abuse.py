import asyncio
import re
import aiohttp
from hydrogram import Client, filters
from hydrogram.enums import ChatMemberStatus, ParseMode
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Aapke config aur db se imports
from config import SUDOERS, OPENROUTER_API_KEY, API_URL, ABUSIVE_WORDS
from db import (
    is_abuse_enabled, set_abuse_status,
    is_user_whitelisted, add_whitelist, remove_whitelist,
    get_whitelisted_users, remove_all_whitelist
)

# --- HELPER FUNCTIONS ---

async def get_target_user(c: Client, m: Message):
    if m.reply_to_message:
        return m.reply_to_message.from_user
    if len(m.command) > 1:
        try:
            return await c.get_users(m.command[1])
        except:
            return None
    return None

async def check_admin(m: Message):
    # Check if user is Admin or Sudo
    if m.from_user.id in SUDOERS:
        return True
    member = await m.chat.get_member(m.from_user.id)
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

# --- AI LOGIC ---

async def check_toxicity_ai(text: str) -> bool:
    if not text:
        return False
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org", 
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-exp:free", # Free model used
        "messages": [
            {
                "role": "system", 
                "content": "You are a content filter. Reply ONLY with 'YES' if the message contains hate speech, severe abuse, or extreme profanity. Reply 'NO' if safe."
            },
            {"role": "user", "content": text}
        ],
        "temperature": 0.1,
        "max_tokens": 5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    answer = data['choices'][0]['message']['content'].strip().upper()
                    return "YES" in answer
    except Exception as e:
        print(f"AI Error: {e}")
    return False

# --- COMMAND HANDLERS ---

@Client.on_message(filters.command("abuse") & filters.group)
async def toggle_abuse_handler(c: Client, m: Message):
    if not await check_admin(m):
        return await m.reply_text("❌ Sirf Admins ye command use kar sakte hain.")

    if len(m.command) > 1:
        arg = m.command[1].lower()
        if arg in ["on", "enable", "yes"]:
            new_status = True
        elif arg in ["off", "disable", "no"]:
            new_status = False
        else:
            await m.reply_text("Use: `/abuse on` or `/abuse off`")
            return
    else:
        current_status = await is_abuse_enabled(m.chat.id)
        new_status = not current_status

    await set_abuse_status(m.chat.id, new_status)
    
    status_text = "Enabled ✅" if new_status else "Disabled ❌"
    await m.reply_text(f"Abuse protection is now {status_text}")


@Client.on_message(filters.command(["auth", "promote"]) & filters.group)
async def auth_user_handler(c: Client, m: Message):
    # Sirf Sudo users kisi ko gaali dene ki permission de sakte hain (Auth)
    if m.from_user.id not in SUDOERS:
        return await m.reply_text("❌ Ye command sirf Sudo users ke liye hai.")

    target_user = await get_target_user(c, m)
    if not target_user:
        return await m.reply_text("❌ User ko reply karein ya username dein.")

    await add_whitelist(m.chat.id, target_user.id)
    await m.reply_text(f"✅ [{target_user.first_name}](tg://user?id={target_user.id}) is now Authorized to use abusive language.")


@Client.on_message(filters.command("unauth") & filters.group)
async def unauth_user_handler(c: Client, m: Message):
    if m.from_user.id not in SUDOERS:
        return await m.reply_text("❌ Ye command sirf Sudo users ke liye hai.")

    target_user = await get_target_user(c, m)
    if not target_user:
        return await m.reply_text("❌ User ko reply karein ya username dein.")

    await remove_whitelist(m.chat.id, target_user.id)
    await m.reply_text(f"🚫 [{target_user.first_name}](tg://user?id={target_user.id}) is now Un-Authorized.")


@Client.on_message(filters.command("authlist") & filters.group)
async def authlist_handler(c: Client, m: Message):
    if m.from_user.id not in SUDOERS and not await check_admin(m):
        return await m.reply_text("❌ Admin only.")

    cursor = await get_whitelisted_users(m.chat.id)
    users = []
    async for doc in cursor:
        try:
            user = await c.get_users(doc["user_id"])
            users.append(f"• [{user.first_name}](tg://user?id={user.id})")
        except:
            users.append(f"• ID: {doc['user_id']}")
    
    if not users:
        await m.reply_text("📂 Auth list is empty.")
    else:
        await m.reply_text("**Authorized Users:**\n" + "\n".join(users))


# --- MAIN WATCHER (FILTER) ---

@Client.on_message(filters.text & filters.group & ~filters.bot & ~filters.service, group=10)
async def abuse_watcher(c: Client, m: Message):
    # 1. Check if Abuse Filter is ON in database
    if not await is_abuse_enabled(m.chat.id):
        return

    # 2. Skip if user is Admin, Owner or Whitelisted (Auth)
    if await check_admin(m) or await is_user_whitelisted(m.chat.id, m.from_user.id):
        return

    text = m.text or ""
    censored_text = text
    detected_abuse = False
    
    # 3. Check Local Word List (Fast)
    for word in ABUSIVE_WORDS:
        # Regex to match whole words only (case insensitive)
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        if pattern.search(censored_text):
            detected_abuse = True
            # Replace word with spoiler ||word||
            censored_text = pattern.sub(lambda match: f"||{match.group(0)}||", censored_text)
    
    # 4. Check AI (Slow, acts as backup if local list misses)
    if not detected_abuse:
        if await check_toxicity_ai(text):
            detected_abuse = True
            censored_text = f"||{text}||"

    # 5. Take Action
    if detected_abuse:
        try:
            await m.delete()

            # Create warning message
            user_link = f"[{m.from_user.first_name}](tg://user?id={m.from_user.id})"
            warning_text = (
                f"🚫 Hey {user_link}, gaali dena mana hai!\n\n"
                f"🔍 **Message:** {censored_text}\n"
            )

            sent_msg = await m.reply_text(warning_text, parse_mode=ParseMode.MARKDOWN)
            
            # Delete warning after 10 seconds to keep chat clean
            await asyncio.sleep(10)
            await sent_msg.delete()

        except Exception as e:
            print(f"Abuse Handle Error: {e}")
  
