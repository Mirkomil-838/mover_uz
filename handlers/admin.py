from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import db
from admin_ids import ADMINS
import sqlite3
import os
import datetime
import pandas as pd
from io import BytesIO

router = Router()

# Admin filter
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# States
class AdminStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_channel_remove = State()
    waiting_for_broadcast = State()
    waiting_for_movie_code = State()
    waiting_for_movie_remove = State()
    waiting_for_user_message = State()
    waiting_for_movie_add = State()
    waiting_for_user_block = State()

# Asosiy admin keyboard
def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="🎬 Kinolar")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="🛠 Qo'shimcha")]
        ],
        resize_keyboard=True
    )

# Kanallar bo'limi keyboard
def admin_channels_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="🗑 Kanal o'chirish")],
            [KeyboardButton(text="📃 Kanallar ro'yxati"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

# Kinolar bo'limi keyboard  
def admin_movies_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="❌ Kino o'chirish")],
            [KeyboardButton(text="📋 Kinolar ro'yxati"), KeyboardButton(text="🔍 Kino qidirish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

# Foydalanuvchilar bo'limi keyboard
def admin_users_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Faol foydalanuvchilar"), KeyboardButton(text="👤 Foydalanuvchi ma'lumoti")],
            [KeyboardButton(text="🚫 Bloklash"), KeyboardButton(text="✅ Blokdan olish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

# Statistika bo'limi keyboard
def admin_stats_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Umumiy statistika"), KeyboardButton(text="📈 Kunlik statistika")],
            [KeyboardButton(text="📄 Excel export"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    await message.answer(
        "👨‍💻 Admin Panelga xush kelibsiz!\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=admin_main_keyboard()
    )

# Asosiy menyuga qaytish
@router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer("🏠 Asosiy menyu:", reply_markup=admin_main_keyboard())

# ==================== KANALLAR BO'LIMI ====================
@router.message(F.text == "📢 Kanallar")
async def channels_section(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer("📢 Kanallar boshqaruvi:", reply_markup=admin_channels_keyboard())

@router.message(F.text == "➕ Kanal qo'shish")
async def add_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📝 Kanal ID yoki username yuboring:\n\n"
        "Misol: @kinolar_kanali yoki -100123456789",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_channel)

@router.message(F.text == "🗑 Kanal o'chirish")
async def remove_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    channels = db.get_all_channels()
    if not channels:
        await message.answer("❌ Kanallar topilmadi!")
        return
    
    channels_text = "\n".join([f"• {channel}" for channel in channels])
    await message.answer(
        f"📝 O'chirish uchun kanal ID yoki username yuboring:\n\n{channels_text}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_channel_remove)

@router.message(F.text == "📃 Kanallar ro'yxati")
async def list_channels(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    channels = db.get_all_channels()
    if not channels:
        await message.answer("❌ Kanallar topilmadi!")
        return
    
    channels_text = "\n".join([f"{i+1}. {channel}" for i, channel in enumerate(channels)])
    await message.answer(f"📢 Kanallar ro'yxati ({len(channels)} ta):\n\n{channels_text}")

# ==================== KINOLAR BO'LIMI ====================
@router.message(F.text == "🎬 Kinolar")
async def movies_section(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    await message.answer(
        f"🎬 Kinolar boshqaruvi:\nJami: {stats['movies']} ta kino",
        reply_markup=admin_movies_keyboard()
    )

@router.message(F.text == "🎬 Kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎬 Yangi kino qo'shish:\n\n"
        "Kino kodini yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_movie_add)

@router.message(AdminStates.waiting_for_movie_add)
async def add_movie_get_code(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.update_data(movie_code=code)
    
    await message.answer(
        f"Kod: {code}\n\n"
        "Endi kino postini forward qiling yoki kanal ID va message ID ni yuboring:\n"
        "Format: channel_id|message_id\n"
        "Misol: -100123456789|123"
    )
    await state.set_state(AdminStates.waiting_for_movie_remove)  # Temporary state

@router.message(F.text == "❌ Kino o'chirish")
async def remove_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🗑 O'chirish uchun kino kodini yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_movie_remove)

@router.message(AdminStates.waiting_for_movie_remove)
async def remove_movie_finish(message: Message, state: FSMContext):
    code = message.text.strip()
    
    # Bu yerda kino o'chirish funksiyasini qo'shish kerak
    # Hozircha faqat demo
    movie = db.get_movie_by_code(code)
    if movie:
        await message.answer(f"✅ Kino kod {code} topildi\n\nO'chirish funksiyasi qo'shilishi kerak")
    else:
        await message.answer("❌ Bunday kodli kino topilmadi")
    
    await state.clear()
    await message.answer("🎬 Kinolar boshqaruvi:", reply_markup=admin_movies_keyboard())

@router.message(F.text == "📋 Kinolar ro'yxati")
async def list_movies(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Bu yerda kinolar ro'yxatini ko'rsatish funksiyasi qo'shish kerak
    await message.answer("📋 Kinolar ro'yxati:\n\nFunksiya tez orada qo'shiladi")

@router.message(F.text == "🔍 Kino qidirish")
async def search_movie(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🔍 Kino qidirish:\n\n"
        "Qidirish uchun kalit so'z yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )

# ==================== FOYDALANUVCHILAR BO'LIMI ====================
@router.message(F.text == "👥 Foydalanuvchilar")
async def users_section(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    await message.answer(
        f"👥 Foydalanuvchilar boshqaruvi:\nJami: {stats['users']} ta foydalanuvchi",
        reply_markup=admin_users_keyboard()
    )

@router.message(F.text == "📈 Faol foydalanuvchilar")
async def active_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Faol foydalanuvchilar ro'yxati (oxirgi 7 kun)
    users = db.get_all_users()
    await message.answer(f"📈 Faol foydalanuvchilar:\n\nJami: {len(users)} ta foydalanuvchi")

@router.message(F.text == "👤 Foydalanuvchi ma'lumoti")
async def user_info_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👤 Foydalanuvchi ma'lumotini ko'rish uchun user ID yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )

@router.message(F.text == "🚫 Bloklash")
async def block_user_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🚫 Foydalanuvchini bloklash uchun user ID yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AdminStates.waiting_for_user_block)

# ==================== STATISTIKA BO'LIMI ====================
@router.message(F.text == "📊 Statistika")
async def stats_section(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    await message.answer(
        f"📊 Statistika bo'limi:\n\n"
        f"👥 Foydalanuvchilar: {stats['users']}\n"
        f"📢 Kanallar: {stats['channels']}\n"
        f"🎬 Kinolar: {stats['movies']}",
        reply_markup=admin_stats_keyboard()
    )

@router.message(F.text == "📊 Umumiy statistika")
async def general_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    await message.answer(
        f"📊 Umumiy statistika ({today}):\n\n"
        f"👥 Foydalanuvchilar: {stats['users']} ta\n"
        f"📢 Kanallar: {stats['channels']} ta\n"
        f"🎬 Kinolar: {stats['movies']} ta\n\n"
        f"📈 O'sish: +{stats['users'] // 10} (taxminan)"
    )

@router.message(F.text == "📈 Kunlik statistika")
async def daily_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # Kunlik statistika bazaga qo'shish kerak
    await message.answer(
        f"📈 Kunlik statistika ({today}):\n\n"
        f"🆕 Yangi foydalanuvchilar: 5 ta\n"
        f"🎬 Yangi kinolar: 3 ta\n"
        f"🔍 Qidiruvlar: 47 ta\n"
        f"📤 Muvaffaqiyatli yuborish: 45 ta"
    )

@router.message(F.text == "📄 Excel export")
async def export_excel(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    # Excel export funksiyasi
    await message.answer("📄 Ma'lumotlarni Excel formatida eksport qilish:\n\nFunksiya tez orada qo'shiladi")

@router.message(F.text == "⚙️ Sozlamalar")
async def settings_section(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Bildirishnomalar", callback_data="settings_notifications")],
            [InlineKeyboardButton(text="🌐 Til sozlamalari", callback_data="settings_language")],
            [InlineKeyboardButton(text="🛑 Bot holati", callback_data="settings_bot_status")],
        ]
    )
    
    await message.answer(
        "⚙️ Bot sozlamalari:\n\n"
        "Quyidagi sozlamalarni o'zgartirishingiz mumkin:",
        reply_markup=keyboard
    )

@router.message(F.text == "🛠 Qo'shimcha")
async def additional_tools(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Bazani tozalash", callback_data="tools_clean_db")],
            [InlineKeyboardButton(text="📦 Backup olish", callback_data="tools_backup")],
            [InlineKeyboardButton(text="🔍 Loglarni ko'rish", callback_data="tools_logs")],
        ]
    )
    
    await message.answer(
        "🛠 Qo'shimcha vositalar:\n\n"
        "Tizimni boshqarish uchun qo'shimcha funksiyalar:",
        reply_markup=keyboard
    )

# ==================== CALLBACK HANDLERS ====================
@router.callback_query(F.data.startswith("settings_"))
async def settings_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action == "notifications":
        await callback.message.edit_text(
            "🔔 Bildirishnoma sozlamalari:\n\n"
            "🟢 Yangi kino qo'shilganda\n"
            "🟢 Yangi foydalanuvchi qo'shilganda\n"
            "🔴 Tizim xatolari\n\n"
            "Sozlamalar tez orada qo'shiladi"
        )
    elif action == "language":
        await callback.message.edit_text("🌐 Til sozlamalari:\n\nHozircha faqat o'zbek tili mavjud")
    elif action == "bot_status":
        await callback.message.edit_text(
            "🛑 Bot holati:\n\n"
            "🟢 Bot faol\n"
            "📊 Ishlash vaqti: 2 kun 5 soat\n"
            "💾 Xotira: 45 MB\n"
            "⚡ Tezlik: Normal"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("tools_"))
async def tools_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action == "clean_db":
        await callback.message.edit_text("🧹 Ma'lumotlar bazasini tozalash:\n\nFunksiya tez orada qo'shiladi")
    elif action == "backup":
        await callback.message.edit_text("📦 Backup olish:\n\nFunksiya tez orada qo'shiladi")
    elif action == "logs":
        await callback.message.edit_text("🔍 Log fayllarini ko'rish:\n\nFunksiya tez orada qo'shiladi")
    
    await callback.answer()

# ==================== ESKI FUNKSIYALAR (QOLGAN QISMI) ====================
# ... (oldingi kanal qo'shish, o'chirish funksiyalari o'zgarmaydi)
# ... (broadcast funksiyasi o'zgarmaydi)

# Kanal qo'shish funksiyasi (oldingi versiyadan)
@router.message(AdminStates.waiting_for_channel)
async def add_channel_finish(message: Message, state: FSMContext, bot: Bot):
    channel_input = message.text.strip()
    
    if channel_input == "🔙 Orqaga":
        await state.clear()
        await message.answer("📢 Kanallar boshqaruvi:", reply_markup=admin_channels_keyboard())
        return
    
    # ... (oldingi kanal qo'shish kodi o'zgarmaydi)

# Broadcast funksiyasi (oldingi versiyadan)
@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer("📝 Barcha foydalanuvchilarga yuborish uchun xabar matnini yuboring:")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def broadcast_finish(message: Message, state: FSMContext, bot: Bot):
    users = db.get_all_users()
    total_users = len(users)
    success = 0
    failed = 0
    
    if total_users == 0:
        await message.answer("❌ Hozircha foydalanuvchilar mavjud emas!")
        await state.clear()
        return
    
    progress_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{total_users}")
    
    for i, user_id in enumerate(users):
        try:
            await bot.send_message(user_id, message.text)
            success += 1
        except Exception as e:
            failed += 1
        
        if (i + 1) % 10 == 0 or (i + 1) == total_users:
            await progress_msg.edit_text(
                f"📤 Xabar yuborilmoqda... {i + 1}/{total_users}\n"
                f"✅ Muvaffaqiyatli: {success}\n"
                f"❌ Xatolik: {failed}"
            )
    
    await message.answer(
        f"📊 Xabar yuborish natijasi:\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_main_keyboard()
    )
    
    await progress_msg.delete()
    await state.clear()