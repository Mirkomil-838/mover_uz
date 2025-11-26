from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot

from database.db import db
from admin_ids import ADMINS

router = Router()

# Admin filter
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# States
class AdminStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_channel_remove = State()
    waiting_for_broadcast = State()

# Admin keyboard
def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="🗑 Kanal o'chirish")],
            [KeyboardButton(text="📃 Kanallar ro'yxati"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Xabar yuborish")]
        ],
        resize_keyboard=True
    )

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return
    
    await message.answer(
        "👨‍💻 Admin Panelga xush kelibsiz!",
        reply_markup=admin_keyboard()
    )

@router.message(F.text == "➕ Kanal qo'shish")
async def add_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📝 Kanal ID yoki username yuboring:\n\n"
        "Misol: @channel_username yoki -100123456789\n\n"
        "⚠️ Eslatma: Bot kanalda admin bo'lishi va 'Postlarni joylashtirish' ruxsati bo'lishi kerak!"
    )
    await state.set_state(AdminStates.waiting_for_channel)

@router.message(AdminStates.waiting_for_channel)
async def add_channel_finish(message: Message, state: FSMContext, bot: Bot):
    channel_id = message.text.strip()
    
    # Kanal mavjudligini tekshiramiz
    try:
        chat = await bot.get_chat(channel_id)
        print(f"✅ Kanal topildi: {chat.title} (ID: {chat.id})")
        
        # Bot kanalda adminligini tekshiramiz
        bot_member = await bot.get_chat_member(chat.id, (await bot.get_me()).id)
        if bot_member.status != 'administrator':
            await message.answer(
                "❌ Bot bu kanalda admin emas!\n"
                "Iltimos, botni kanalga admin qiling va 'Postlarni joylashtirish' ruxsatini bering.",
                reply_markup=admin_keyboard()
            )
            await state.clear()
            return
            
    except Exception as e:
        await message.answer(
            f"❌ Kanal topilmadi yoki botda xatolik: {e}\n"
            "Kanal ID yoki username ni tekshiring.",
            reply_markup=admin_keyboard()
        )
        await state.clear()
        return
    
    if db.add_channel(channel_id):
        await message.answer(f"✅ Kanal muvaffaqiyatli qo'shildi!\n\n📢 Kanal: {chat.title}", reply_markup=admin_keyboard())
    else:
        await message.answer("❌ Kanal qo'shishda xatolik!", reply_markup=admin_keyboard())
    
    await state.clear()

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
        f"📝 O'chirish uchun kanal ID yoki username yuboring:\n\n{channels_text}"
    )
    await state.set_state(AdminStates.waiting_for_channel_remove)

@router.message(AdminStates.waiting_for_channel_remove)
async def remove_channel_finish(message: Message, state: FSMContext):
    channel_id = message.text.strip()
    
    if db.remove_channel(channel_id):
        await message.answer("✅ Kanal muvaffaqiyatli o'chirildi!", reply_markup=admin_keyboard())
    else:
        await message.answer("❌ Kanal topilmadi yoki o'chirishda xatolik!", reply_markup=admin_keyboard())
    
    await state.clear()

@router.message(F.text == "📃 Kanallar ro'yxati")
async def list_channels(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    channels = db.get_all_channels()
    if not channels:
        await message.answer("❌ Kanallar topilmadi!")
        return
    
    channels_text = "\n".join([f"{i+1}. {channel}" for i, channel in enumerate(channels)])
    await message.answer(f"📢 Kanallar ro'yxati:\n\n{channels_text}")

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    stats = db.get_stats()
    await message.answer(
        f"📊 Bot statistikasi:\n\n"
        f"👥 Foydalanuvchilar: {stats['users']}\n"
        f"📢 Kanallar: {stats['channels']}\n"
        f"🎬 Kinolar: {stats['movies']}"
    )

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
    
    # Xabar yuborishni boshlash
    progress_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{total_users}")
    
    for i, user_id in enumerate(users):
        try:
            await bot.send_message(user_id, message.text)
            success += 1
        except Exception as e:
            failed += 1
        
        # Har 10 ta xabardan keyin progress yangilash
        if (i + 1) % 10 == 0 or (i + 1) == total_users:
            await progress_msg.edit_text(
                f"📤 Xabar yuborilmoqda... {i + 1}/{total_users}\n"
                f"✅ Muvaffaqiyatli: {success}\n"
                f"❌ Xatolik: {failed}"
            )
    
    # Yakuniy natija
    await message.answer(
        f"📊 Xabar yuborish natijasi:\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_keyboard()
    )
    
    # Progress xabarini o'chirish
    await progress_msg.delete()
    await state.clear()