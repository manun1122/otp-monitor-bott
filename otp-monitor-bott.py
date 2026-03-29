#!/usr/bin/env python3
"""
OTP Monitor - Full Script (Static Cookie, No Auto-Refresh)
Updated with proper channel & bot links
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

# HTTP লাইব্রেরি (aiohttp পছন্দনীয়, না থাকলে requests)
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    import requests
    import urllib3
    urllib3.disable_warnings()

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

# =================== কনফিগারেশন (আপনার তথ্য) ===================
TELEGRAM_BOT_TOKEN = "5929619535:AAGsgoN5pYczsKWOGqVWTrslk0qJr2jJVYA"
GROUP_CHAT_ID = "-1001153782407"
TARGET_URL = "http://147.135.212.148/ints/agent/res/data_smscdr.php"
SESSKEY = "Q05RR0FRUURCUA=="          # আপনার sesskey
PHPSESSID = "7f70515fb8926e045e42d5df285e8154"   # আপনার কুকি

# লিংক
MAIN_CHANNEL = "https://t.me/updaterange"
NUMBER_BOT = "https://t.me/Updateotpnew_bot"
DEVELOPER = "https://t.me/rana1132"
# ====================================================================

# টেম্প ফাইল (Railway তে রিস্টার্টে রিসেট হবে)
import tempfile
TEMP_DIR = tempfile.gettempdir()
PROCESSED_FILE = os.path.join(TEMP_DIR, "sent_otps.json")

# লগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("OTPMonitor")

# OTP শনাক্ত করার প্যাটার্ন (বাংলা + ইংরেজি)
OTP_PATTERNS = [
    r"\b\d{3}-\d{3}\b",          # 123-456
    r"\b\d{5}\b",                # 12345
    r"\b\d{6}\b",                # 123456
    r"\b\d{4}\b",                # 1234
    r"code\s*:?\s*\d+",         # code 12345
    r"OTP\s*:?\s*\d+",          # OTP: 123456
    r"verification code:?\s*\d+",
    r"Your WhatsApp code \d+-\d+",
    r"Telegram code \d+",
    r"কোড\s*\d+",               # কোড ১২৩৪৫৬
]
otp_regex = re.compile("|".join(OTP_PATTERNS), re.IGNORECASE)

# =================== হেল্পার ফাংশন ===================
def extract_otp(message):
    """মেসেজ থেকে OTP বের করে"""
    if not message:
        return None
    match = otp_regex.search(message)
    return match.group(0) if match else None

def hide_phone(phone):
    """ফোন নাম্বার মাঝামাঝি লুকান"""
    p = str(phone)
    if len(p) >= 8:
        return p[:4] + "****" + p[-4:]
    elif len(p) >= 4:
        return p[:2] + "***" + p[-2:]
    return p

def get_flag(country):
    """দেশ অনুযায়ী ফ্লাগ ইমোজি"""
    flags = {
        "Bangladesh": "🇧🇩", "India": "🇮🇳", "Pakistan": "🇵🇰",
        "Saudi": "🇸🇦", "UAE": "🇦🇪", "USA": "🇺🇸", "UK": "🇬🇧",
        "Turkey": "🇹🇷", "Egypt": "🇪🇬", "Malaysia": "🇲🇾",
        "Indonesia": "🇮🇩", "Thailand": "🇹🇭", "Vietnam": "🇻🇳",
        "Philippines": "🇵🇭", "Brazil": "🇧🇷", "Argentina": "🇦🇷",
        "Mexico": "🇲🇽", "Spain": "🇪🇸", "France": "🇫🇷",
        "Germany": "🇩🇪", "Italy": "🇮🇹", "Netherlands": "🇳🇱",
        "Venezuela": "🇻🇪", "Algeria": "🇩🇿", "Honduras": "🇭🇳",
        "Morocco": "🇲🇦", "Tunisia": "🇹🇳", "Libya": "🇱🇾",
        "Jordan": "🇯🇴", "Kuwait": "🇰🇼", "Oman": "🇴🇲",
        "Qatar": "🇶🇦", "Bahrain": "🇧🇭", "Iran": "🇮🇷",
        "Iraq": "🇮🇶", "Afghanistan": "🇦🇫", "Russia": "🇷🇺",
        "China": "🇨🇳", "South Africa": "🇿🇦", "Nigeria": "🇳🇬"
    }
    for k, v in flags.items():
        if k in country:
            return v
    return "🌍"

def format_telegram_message(sms):
    """SMS ডেটা থেকে সুন্দর টেলিগ্রাম মেসেজ তৈরি করে"""
    if len(sms) < 6:
        return "⚠️ অকার্যকর SMS ডেটা"
    
    timestamp = sms[0] if len(sms) > 0 else "N/A"
    operator = sms[1] if len(sms) > 1 else "N/A"
    phone = sms[2] if len(sms) > 2 else "N/A"
    platform = sms[3] if len(sms) > 3 else "N/A"
    message = sms[5] if len(sms) > 5 else "N/A"
    
    # দেশের নাম বের করা
    country = operator.split('_')[0] if '_' in operator else operator.split()[0]
    flag = get_flag(country)
    hidden_phone = hide_phone(phone)
    otp_code = extract_otp(message) or "???"
    
    # সময় শুধু ঘণ্টা:মিনিট:সেকেন্ড
    try:
        time_part = timestamp.split()[1] if ' ' in timestamp else timestamp[:8]
    except:
        time_part = timestamp
    
    return f"""
{flag} **{country}** #{platform}
📱 `{hidden_phone}`
⏰ `{time_part}`

📨 {message}

🔐 **OTP:** `{otp_code}`

➖➖➖➖➖➖➖➖
🤖 @OTPMonitorBot
"""

# =================== টেলিগ্রাম পাঠানো (আপডেটেড লিংক) ===================
async def send_to_telegram(text):
    """টেলিগ্রাম গ্রুপে মেসেজ পাঠায়"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        keyboard = [
            [InlineKeyboardButton("📢 মেইন চ্যানেল", url=MAIN_CHANNEL)],
            [InlineKeyboardButton("🤖 নাম্বার বট", url=NUMBER_BOT)],
            [InlineKeyboardButton("👨‍💻 ডেভেলপার", url=DEVELOPER)],
        ]
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        return True
    except TelegramError as e:
        logger.error(f"টেলিগ্রাম এরর: {e}")
        return False
    except Exception as e:
        logger.error(f"পাঠাতে ব্যর্থ: {e}")
        return False

# =================== প্রসেসড OTP সংরক্ষণ ===================
def load_processed_otps():
    """২৪ ঘণ্টার মধ্যে পাঠানো OTP গুলো লোড করে"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
        cutoff = datetime.now() - timedelta(hours=24)
        valid = {otp_id for otp_id, ts in data.items() if datetime.fromisoformat(ts) > cutoff}
        logger.info(f"📂 {len(valid)} টি পুরনো OTP লোড হয়েছে")
        return valid
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_processed_otps(processed_set):
    """পাঠানো OTP গুলো ফাইলে সেভ করে"""
    data = {otp_id: datetime.now().isoformat() for otp_id in processed_set}
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f)
    logger.debug(f"💾 {len(processed_set)} টি OTP সেভ করা হয়েছে")

# =================== API থেকে ডাটা আনা (স্ট্যাটিক কুকি) ===================
async def fetch_sms_data():
    """শুধু PHPSESSID ব্যবহার করে API কল করে"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://147.135.212.148/ints/agent/SMSCDRStats",
        "Cookie": f"PHPSESSID={PHPSESSID}",
        "Connection": "keep-alive",
    }
    
    today = time.strftime("%Y-%m-%d")
    params = {
        "fdate1": f"{today} 00:00:00",
        "fdate2": f"{today} 23:59:59",
        "frange": "",
        "fclient": "",
        "fnum": "",
        "fcli": "",
        "fgdate": "",
        "fgmonth": "",
        "fgrange": "",
        "fgclient": "",
        "fgnumber": "",
        "fgcli": "",
        "fg": "0",
        "sesskey": SESSKEY,
        "sEcho": "1",
        "iColumns": "9",
        "sColumns": ",,,,,,,,",
        "iDisplayStart": "0",
        "iDisplayLength": "25",
        "sSearch": "",
        "bRegex": "false",
        "iSortCol_0": "0",
        "sSortDir_0": "desc",
        "iSortingCols": "1",
        "_": str(int(time.time() * 1000)),
    }
    # কলাম সেটিংস
    for i in range(9):
        params[f"mDataProp_{i}"] = str(i)
        params[f"sSearch_{i}"] = ""
        params[f"bRegex_{i}"] = "false"
        params[f"bSearchable_{i}"] = "true"
        params[f"bSortable_{i}"] = "true" if i != 8 else "false"
    
    try:
        if HAS_AIOHTTP:
            async with aiohttp.ClientSession() as session:
                async with session.get(TARGET_URL, headers=headers, params=params, timeout=15, ssl=False) as resp:
                    text = await resp.text()
                    logger.info(f"📡 HTTP {resp.status}, রেসপন্স সাইজ: {len(text)} বাইট")
                    if resp.status == 200 and text.strip():
                        return json.loads(text)
                    else:
                        logger.warning(f"খারাপ রেসপন্স: {resp.status} - {text[:200]}")
                        return None
        else:
            resp = requests.get(TARGET_URL, headers=headers, params=params, timeout=15, verify=False)
            logger.info(f"📡 HTTP {resp.status_code}, রেসপন্স সাইজ: {len(resp.text)} বাইট")
            if resp.status_code == 200 and resp.text.strip():
                return resp.json()
            else:
                logger.warning(f"খারাপ রেসপন্স: {resp.status_code} - {resp.text[:200]}")
                return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON পার্সিং এরর: {e}")
        return None
    except Exception as e:
        logger.error(f"ফেচ এরর: {e}")
        return None

# =================== মূল মনিটর লুপ ===================
async def monitor_loop():
    logger.info("="*50)
    logger.info("🚀 OTP মনিটর বট চালু হচ্ছে (স্ট্যাটিক কুকি মোড)")
    logger.info(f"🔑 PHPSESSID: {PHPSESSID[:10]}...")
    logger.info("="*50)
    
    processed = load_processed_otps()
    total_sent = 0
    
    # স্টার্টআপ মেসেজ গ্রুপে পাঠাও
    await send_to_telegram(f"""
✅ **OTP মনিটর বট চালু হয়েছে**
⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
🔑 কুকি: `{PHPSESSID[:10]}...`
📡 মোড: স্ট্যাটিক (কোনো অটো রিফ্রেশ নেই)

🎯 **প্রতিটি OTP শুধু একবার ফরওয়ার্ড হবে**
➖➖➖➖➖➖➖➖
""")
    
    consecutive_errors = 0
    
    while True:
        try:
            data = await fetch_sms_data()
            
            if data and "aaData" in data:
                consecutive_errors = 0
                sms_list = data["aaData"]
                # বৈধ SMS যাদের টাইমস্ট্যাম্প আছে
                valid_sms = [s for s in sms_list if len(s) >= 6 and isinstance(s[0], str) and ":" in s[0]]
                
                if valid_sms:
                    # নতুন থেকে পুরনো ক্রমে প্রসেস করতে reverse
                    valid_sms.reverse()
                    found_new = False
                    
                    for sms in valid_sms:
                        timestamp = sms[0]
                        phone = sms[2]
                        message = sms[5]
                        otp = extract_otp(message) or ""
                        otp_id = f"{timestamp}_{phone}_{otp}"
                        
                        if otp_id not in processed:
                            logger.info(f"🚨 নতুন OTP সনাক্ত! ফোন: {phone}")
                            formatted = format_telegram_message(sms)
                            success = await send_to_telegram(formatted)
                            
                            if success:
                                processed.add(otp_id)
                                total_sent += 1
                                save_processed_otps(processed)
                                logger.info(f"✅ OTP ফরওয়ার্ড করা হয়েছে (মোট: {total_sent})")
                                found_new = True
                                break  # শুধু প্রথম OTP পাঠাবে
                    
                    if not found_new:
                        logger.debug("ℹ️ কোনো নতুন OTP নেই")
                else:
                    logger.debug("📭 কোনো বৈধ SMS নেই")
            else:
                consecutive_errors += 1
                logger.warning(f"⚠️ API থেকে ভুল ডাটা (ক্রমিক ব্যর্থতা: {consecutive_errors})")
                if consecutive_errors > 10:
                    logger.error("অনেক বার ব্যর্থ – কুকি কি মেয়াদোত্তীর্ণ?")
                    await send_to_telegram("⚠️ *সতর্কতা:* API ক্রমাগত ভুল ডাটা দিচ্ছে। কুকি চেক করুন।")
                    consecutive_errors = 0
            
            # ১ সেকেন্ড অপেক্ষা (চেক ইন্টারভাল)
            await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            logger.info("🛑 বন্ধ করার নির্দেশ পাওয়া গেছে")
            break
        except Exception as e:
            logger.exception(f"❌ লুপে অপ্রত্যাশিত ত্রুটি: {e}")
            await asyncio.sleep(5)

# =================== মেইন ===================
async def main():
    try:
        await monitor_loop()
    except KeyboardInterrupt:
        logger.info("👋 ব্যবহারকারী বন্ধ করেছেন। আল্লাহ হাফেজ!")

if __name__ == "__main__":
    asyncio.run(main())