from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database.db import db
from utils.subscription import check_subscription, create_subscription_keyboard
from utils.helpers import extract_movie_code

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message, bot):
    user_id = message.from_user.id
    db.add_user(user_id)
    
    # Check subscription
    is_subscribed = await check_subscription(user_id, bot)
    
    if not is_subscribed:
        await message.answer(
            "🤖 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
            "Obuna bo'lgach, «✅ Tekshirish» tugmasini bosing.",
            reply_markup=create_subscription_keyboard()
        )
        return
    
    await message.answer(
        "🎬 Kino Botiga xush kelibsiz!\n\n"
        "Kino kodini yuboring va kino oling.\n"
        "Misol: 123"
    )

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        await callback.message.edit_text(
            "✅ Siz barcha kanallarga obuna bo'lgansiz!\n\n"
            "Endi kino kodini yuboring va kino oling.\n"
            "Misol: 123"
        )
    else:
        await callback.answer(
            "❌ Hali barcha kanallarga obuna bo'lmagansiz!", 
            show_alert=True
        )

@router.message(F.text)
async def movie_code_handler(message: Message, bot):
    user_id = message.from_user.id
    
    # Check subscription first
    is_subscribed = await check_subscription(user_id, bot)
    if not is_subscribed:
        await message.answer(
            "❌ Botdan foydalanish uchun barcha kanallarga obuna bo'ling!",
            reply_markup=create_subscription_keyboard()
        )
        return
    
    # Process movie code
    code = message.text.strip()
    
    # Try to extract code if user sends full text
    extracted_code = extract_movie_code(code)
    if extracted_code:
        code = extracted_code
    
    # Search for movie
    movie = db.get_movie_by_code(code)
    
    if movie:
        try:
            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=movie.channel_id,
                message_id=movie.message_id
            )
        except Exception as e:
            await message.answer("❌ Kinoni yuborishda xatolik yuz berdi.")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi.")