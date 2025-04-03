import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token='8184529898:AAFzV70_b9F4RN5ql2n9fcoHMM8ffQkPheY')
dp = Dispatcher(storage=MemoryStorage())
router = Router()

carts = {}

@router.message(Command(commands=["help", "start"]))
async def send_welcome(message: Message):

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🧀 Сир', callback_data='cheese')],
        [InlineKeyboardButton(text='🥩 Ковбаса', callback_data='sausage')],
        [InlineKeyboardButton(text='🍬 Цукерки', callback_data='candies')]
    ])
    
    await message.answer(
        f"Привіт {message.from_user.first_name}, я допоможу тобі з вибором продуктів."
    )
    
    await message.answer(
        'Вибери категорію товару:',
        reply_markup=markup
    )

async def send_products_list(chat_id: int, category: str):

    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, weight, price, image_url FROM products WHERE category = ?", (category,))
    products = cursor.fetchall()
    conn.close()

    await bot.send_message(chat_id, "🛍 Вот такі є товари в цій категорії:")

    total_products = len(products)

    for index, product in enumerate(products):
        name, weight, price, image_url = product

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Додати в кошик", callback_data=f"add_{name}")]
        ])

        await bot.send_photo(
            chat_id, 
            photo=image_url, 
            caption=f"🔹 Назва: {name}\n📦 Вага: {weight}\n💰 Ціна: {price} грн.",
            reply_markup=markup
        )

        if index == total_products - 1:
            await bot.send_message(
                chat_id, 
                "Також ви можете перейти одразу до інших категорій ввівши відповідні команди:"
                "/cheese, /sausage, /candies. Щоб перейти до кошика, введіть команду /cart."
            )

@router.message(Command(commands=["cheese", "sausage", "candies"]))
async def handle_category_command(message: Message):

    category = message.text[1:]
    await send_products_list(message.chat.id, category)

@router.callback_query(lambda c: c.data in ["cheese", "sausage", "candies"])
async def handle_category_callback(callback_query: CallbackQuery):

    await callback_query.answer() 
    await send_products_list(callback_query.message.chat.id, callback_query.data)

@router.callback_query(lambda c: c.data.startswith("add_"))
async def handle_add_to_cart(callback_query: CallbackQuery):

    user_id = callback_query.from_user.id
    product_name = callback_query.data[4:]
    
    if user_id not in carts:
        carts[user_id] = {}

    if product_name in carts[user_id]:
        carts[user_id][product_name] += 1
    else:
        carts[user_id][product_name] = 1
    
    await callback_query.answer(
        text=f"Продукт {product_name} додано до кошика (x{carts[user_id][product_name]})."
    )

@router.message(Command(commands=["cart"]))
async def view_cart(message: Message):

    user_id = message.chat.id
    
    if user_id not in carts or not carts[user_id]:
        await message.answer("🛒 Ваш кошик порожній.")
    else:
        cart_items = "\n".join([f"🔹 {item} {count} шт." for item, count in carts[user_id].items()])
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Оформити замовлення", callback_data="order")],
            [InlineKeyboardButton(text="🗑 Очистити кошик", callback_data="clear_cart")]
        ])
        
        await message.answer(f"🛒 Ваш кошик:\n\n{cart_items}", reply_markup=markup)

@router.callback_query(lambda c: c.data == "order")
async def order_cart(callback_query: CallbackQuery):

    user_id = callback_query.from_user.id
    
    if user_id not in carts or not carts[user_id]:
        await callback_query.answer(text="Ваш кошик порожній!")
        return
    
    cart_summary = "\n".join([f"🔹 {item} {count} шт." for item, count in carts[user_id].items()])
    
    await bot.send_message(
        user_id, 
        f"✅ Замовлення оформлене! Дякую за покупку!\n\nВаше замовлення:\n{cart_summary}"
    )
    
    carts[user_id] = {}
    await callback_query.answer()

@router.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback_query: CallbackQuery):

    user_id = callback_query.from_user.id

    if user_id in carts:
        carts[user_id] = {}

    await callback_query.answer(text="🗑 Кошик очищено!")
    await bot.send_message(user_id, "Ваш кошик порожній.")

dp.include_router(router)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())