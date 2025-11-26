from aiogram import Router
from aiogram.types import Message
from database.db import db
from utils.helpers import extract_movie_code

router = Router()

@router.channel_post()
async def channel_post_handler(message: Message):
    """Handle movie posts in channels"""
    if not message.caption and not message.text:
        return
    
    text = message.caption or message.text
    code = extract_movie_code(text)
    
    if code:
        # Save movie to database
        db.add_movie(
            code=code,
            channel_id=message.chat.id,
            message_id=message.message_id,
            caption=text
        )
        print(f"✅ Movie saved with code: {code}")