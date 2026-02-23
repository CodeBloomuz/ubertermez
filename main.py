import logging
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)

# =============================================
# SOZLAMALAR
# =============================================
TOKEN = "8020803338:AAGOesGlRBDLJj8aWCmpdo18WApmRTsxcCY"
ADMIN_ID = 6551375195
FAYL = "ustalar.json"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
logging.basicConfig(level=logging.INFO)

# =============================================
# FSM — USTA RO'YXATDAN O'TISH BOSQICHLARI
# =============================================
class UstaRoyxat(StatesGroup):
    ism = State()
    telefon = State()
    xizmat = State()
    haqida = State()

# =============================================
# USTALAR FAYLI
# =============================================
def ustalar_olish():
    if os.path.exists(FAYL):
        with open(FAYL, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def usta_saqlash(usta: dict):
    ustalar = ustalar_olish()
    ustalar.append(usta)
    with open(FAYL, "w", encoding="utf-8") as f:
        json.dump(ustalar, f, ensure_ascii=False, indent=2)

def usta_tasdiqlash(telegram_id: int, tasdiqlash: bool):
    ustalar = ustalar_olish()
    for u in ustalar:
        if u.get("telegram_id") == telegram_id and not u.get("tasdiqlangan"):
            u["tasdiqlangan"] = tasdiqlash
            break
    with open(FAYL, "w", encoding="utf-8") as f:
        json.dump(ustalar, f, ensure_ascii=False, indent=2)

def get_ustalar(xizmat_turi: str) -> list:
    ustalar = ustalar_olish()
    mos = [u for u in ustalar if u.get("xizmat") == xizmat_turi and u.get("tasdiqlangan") == True]
    return mos[:5]

# =============================================
# BOSH MENYU KLAVIATURASI
# =============================================
def bosh_menyu_klaviatura():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Usta qidirish", callback_data="usta_qidirish")],
        [InlineKeyboardButton(text="👷 Usta sifatida qo'shilish", callback_data="usta_qoshilish")],
    ])

def xizmatlar_klaviatura():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚿 Santexnik", callback_data="xizmat:Santexnik"),
            InlineKeyboardButton(text="⚡ Elektrik", callback_data="xizmat:Elektrik"),
        ],
        [
            InlineKeyboardButton(text="🔥 Gaz ustasi", callback_data="xizmat:Gaz ustasi"),
            InlineKeyboardButton(text="🪑 Mebel ustasi", callback_data="xizmat:Mebel ustasi"),
        ],
        [
            InlineKeyboardButton(text="🎨 Oboychi", callback_data="xizmat:Oboychi"),
            InlineKeyboardButton(text="📦 Labo / Yuk", callback_data="xizmat:Labo"),
        ],
        [
            InlineKeyboardButton(text="🛵 Yetkazib berish", callback_data="xizmat:Yetkazib berish"),
        ],
        [
            InlineKeyboardButton(text="🏠 Orqaga", callback_data="bosh_menyu"),
        ],
    ])

# =============================================
# /start
# =============================================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>UBER TERMEZ</b> botiga xush kelibsiz!\n\n"
        "🏙 Termiz shahri uchun usta va xizmatlar platformasi.\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=bosh_menyu_klaviatura(),
        parse_mode="HTML"
    )

# =============================================
# BOSH MENYU (callback)
# =============================================
@dp.callback_query(F.data == "bosh_menyu")
async def bosh_menyu_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "🏠 <b>Bosh menyu</b>\n\nQuyidagilardan birini tanlang:",
        reply_markup=bosh_menyu_klaviatura(),
        parse_mode="HTML"
    )
    await callback.answer()

# =============================================
# USTA QIDIRISH
# =============================================
@dp.callback_query(F.data == "usta_qidirish")
async def usta_qidirish(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔍 <b>Qaysi xizmat kerak?</b>",
        reply_markup=xizmatlar_klaviatura(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("xizmat:"))
async def xizmat_tanlandi(callback: types.CallbackQuery):
    xizmat = callback.data.split(":")[1]
    await callback.message.answer(
        f"⏳ <b>Termiz shahridagi {xizmat} ustalar qidirilmoqda...</b>",
        parse_mode="HTML"
    )

    ustalar = get_ustalar(xizmat)

    if not ustalar:
        await callback.message.answer(
            f"😔 Hozircha <b>{xizmat}</b> bo'yicha usta topilmadi.\n\n"
            "🔄 Tez orada ustalar qo'shiladi!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="bosh_menyu")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.answer(
        f"✅ <b>Termiz shahridagi {xizmat} ustalar:</b>\n{'━' * 28}",
        parse_mode="HTML"
    )

    for u in ustalar:
        matn = (
            f"👷 <b>{u['ism']}</b>\n"
            f"📍 Termiz shahri\n"
            f"⭐ {u['reyting']} ({u['sharhlar']} ta sharh)\n"
            f"💰 Narx: Kelishilgan holda\n"
            f"📞 {u['telefon']}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Qo'ng'iroq qilish", url=f"tel:{u['telefon']}")]
        ])
        await callback.message.answer(matn, reply_markup=keyboard, parse_mode="HTML")

    await callback.message.answer(
        "☝️ Yuqoridagi ustalardan biriga qo'ng'iroq qiling.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Boshqa xizmat", callback_data="usta_qidirish")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="bosh_menyu")],
        ])
    )
    await callback.answer()

# =============================================
# USTA QO'SHILISH — RO'YXATDAN O'TISH
# =============================================
@dp.callback_query(F.data == "usta_qoshilish")
async def usta_qoshilish(callback: types.CallbackQuery, state: FSMContext):
    # Avval bu usta allaqachon ro'yxatda ekanini tekshirish
    ustalar = ustalar_olish()
    mavjud = [u for u in ustalar if u.get("telegram_id") == callback.from_user.id]
    if mavjud:
        u = mavjud[0]
        holat = "✅ Tasdiqlangan" if u.get("tasdiqlangan") else "⏳ Tasdiq kutilmoqda"
        await callback.message.answer(
            f"ℹ️ Siz allaqachon ro'yxatdasiz!\n\n"
            f"👷 <b>{u['ism']}</b>\n"
            f"🔧 {u['xizmat']}\n"
            f"📞 {u['telefon']}\n"
            f"Holat: {holat}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="bosh_menyu")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await state.set_state(UstaRoyxat.ism)
    await callback.message.answer(
        "📝 <b>Usta sifatida ro'yxatdan o'tish</b>\n\n"
        "1️⃣ Ism va Familiyangizni yozing:\n"
        "<i>Misol: Jasur Toshmatov</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()

# ISM
@dp.message(UstaRoyxat.ism)
async def ism_kiritish(message: types.Message, state: FSMContext):
    await state.update_data(ism=message.text.strip())
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await state.set_state(UstaRoyxat.telefon)
    await message.answer(
        f"✅ Ism: <b>{message.text}</b>\n\n"
        "2️⃣ Telefon raqamingizni yuboring:",
        reply_markup=keyboard, parse_mode="HTML"
    )

# TELEFON
@dp.message(UstaRoyxat.telefon, F.contact)
async def telefon_kiritish(message: types.Message, state: FSMContext):
    telefon = message.contact.phone_number
    if not telefon.startswith("+"):
        telefon = "+" + telefon
    await state.update_data(telefon=telefon)
    await state.set_state(UstaRoyxat.xizmat)
    await message.answer(
        f"✅ Telefon: <b>{telefon}</b>\n\n"
        "3️⃣ Qaysi xizmat turisiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚿 Santexnik", callback_data="rk:Santexnik"),
                InlineKeyboardButton(text="⚡ Elektrik", callback_data="rk:Elektrik"),
            ],
            [
                InlineKeyboardButton(text="🔥 Gaz ustasi", callback_data="rk:Gaz ustasi"),
                InlineKeyboardButton(text="🪑 Mebel ustasi", callback_data="rk:Mebel ustasi"),
            ],
            [
                InlineKeyboardButton(text="🎨 Oboychi", callback_data="rk:Oboychi"),
                InlineKeyboardButton(text="📦 Labo / Yuk", callback_data="rk:Labo"),
            ],
            [
                InlineKeyboardButton(text="🛵 Yetkazib berish", callback_data="rk:Yetkazib berish"),
            ],
        ]),
        parse_mode="HTML"
    )

@dp.message(UstaRoyxat.telefon)
async def telefon_xato(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("⚠️ Iltimos, tugmani bosib raqamingizni yuboring:", reply_markup=keyboard)

# XIZMAT
@dp.callback_query(UstaRoyxat.xizmat, F.data.startswith("rk:"))
async def xizmat_tanlash(callback: types.CallbackQuery, state: FSMContext):
    xizmat = callback.data.split(":")[1]
    await state.update_data(xizmat=xizmat)
    await state.set_state(UstaRoyxat.haqida)
    await callback.message.answer(
        f"✅ Xizmat: <b>{xizmat}</b>\n\n"
        "4️⃣ O'zingiz haqingizda qisqacha yozing:\n"
        "<i>Misol: 10 yillik tajriba, sifatli ish kafolati</i>",
        parse_mode="HTML", reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()

# HAQIDA — YAKUNLASH
@dp.message(UstaRoyxat.haqida)
async def haqida_kiritish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    usta = {
        "telegram_id": message.from_user.id,
        "ism": data["ism"],
        "telefon": data["telefon"],
        "xizmat": data["xizmat"],
        "haqida": message.text,
        "reyting": 5.0,
        "sharhlar": 0,
        "tasdiqlangan": False
    }
    usta_saqlash(usta)

    # Ustaga xabar
    await message.answer(
        "✅ <b>Arizangiz qabul qilindi!</b>\n\n"
        f"👷 Ism: {usta['ism']}\n"
        f"📞 Telefon: {usta['telefon']}\n"
        f"🔧 Xizmat: {usta['xizmat']}\n"
        f"📝 Haqida: {usta['haqida']}\n\n"
        "⏳ Admin tasdiqlashini kuting. Odatda 1-2 soat ichida tasdiqlanadi.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="bosh_menyu")]
        ]),
        parse_mode="HTML"
    )

    # Adminga xabar
    admin_matn = (
        f"🆕 <b>Yangi usta arizasi!</b>\n\n"
        f"👷 Ism: {usta['ism']}\n"
        f"📞 Telefon: {usta['telefon']}\n"
        f"🔧 Xizmat: {usta['xizmat']}\n"
        f"📝 Haqida: {usta['haqida']}\n"
        f"🆔 Telegram ID: {usta['telegram_id']}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tasdiq:{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rad:{message.from_user.id}"),
        ]
    ])
    try:
        await bot.send_message(ADMIN_ID, admin_matn, reply_markup=keyboard, parse_mode="HTML")
    except:
        pass

# =============================================
# ADMIN: TASDIQLASH / RAD ETISH
# =============================================
@dp.callback_query(F.data.startswith("tasdiq:"))
async def tasdiqlash(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Siz admin emassiz!")
        return
    usta_id = int(callback.data.split(":")[1])
    usta_tasdiqlash(usta_id, True)
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>TASDIQLANDI</b>", parse_mode="HTML"
    )
    try:
        await bot.send_message(
            usta_id,
            "🎉 <b>Tabriklaymiz!</b>\n\n"
            "Arizangiz tasdiqlandi! Endi mijozlar sizni <b>UBER TERMEZ</b> botida ko'rishi mumkin. ✅",
            parse_mode="HTML"
        )
    except:
        pass
    await callback.answer("✅ Tasdiqlandi!")

@dp.callback_query(F.data.startswith("rad:"))
async def rad_etish(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Siz admin emassiz!")
        return
    usta_id = int(callback.data.split(":")[1])
    usta_tasdiqlash(usta_id, False)
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>RAD ETILDI</b>", parse_mode="HTML"
    )
    try:
        await bot.send_message(usta_id, "😔 Afsuski, arizangiz rad etildi.\n\nQo'shimcha ma'lumot: @UberTermezAdmin")
    except:
        pass
    await callback.answer("❌ Rad etildi!")

# =============================================
# ADMIN: USTALAR RO'YXATI
# =============================================
@dp.message(Command("ustalar"))
async def ustalar_royxati(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    ustalar = ustalar_olish()
    if not ustalar:
        await message.answer("📭 Hozircha usta yo'q.")
        return
    matn = f"👷 <b>Jami ustalar: {len(ustalar)}</b>\n\n"
    for i, u in enumerate(ustalar, 1):
        holat = "✅" if u.get("tasdiqlangan") else "⏳"
        matn += f"{i}. {holat} {u['ism']} — {u['xizmat']} — {u['telefon']}\n"
    await message.answer(matn, parse_mode="HTML")

# =============================================
# ISHGA TUSHIRISH
# =============================================
async def main():
    print("✅ UBER TERMEZ boti ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
