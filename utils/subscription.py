from typing import List
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.db import db

async def check_subscription(user_id: int, bot: Bot) -> bool:
    """Check if user is subscribed to all channels"""
    channels = db.get_all_channels()
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Error checking subscription for {channel}: {e}")
            return False
    
    return True

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with channel links"""
    channels = db.get_all_channels()
    keyboard = []
    
    for channel in channels:
        channel_username = channel.replace('@', '') if channel.startswith('@') else channel
        keyboard.append([InlineKeyboardButton(
            text=f"📢 Kanalga obuna bo'lish", 
            url=f"https://t.me/{channel_username}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        text="✅ Tekshirish", 
        callback_data="check_subscription"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)