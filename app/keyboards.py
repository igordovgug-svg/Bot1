from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category


main_reply_kb = ReplyKeyboardBuilder().add(
    KeyboardButton(text="🏠 Меню")
).as_markup(resize_keyboard=True)


async def get_cats(callback: CallbackQuery, session: AsyncSession) -> InlineKeyboardMarkup:
    result = await session.execute(
        select(Category.id, Category.name).where(Category.user_id == callback.from_user.id )
        )
    
    cats = result.all()  

    if not cats:
        return None

    builder = InlineKeyboardBuilder()

    for cat_id, cat_name in cats:
        builder.add(InlineKeyboardButton(text=cat_name, callback_data=f"product:{cat_id}"))
    
    return builder.adjust(2).as_markup()


start_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Меню', callback_data='/menu')],   
])


menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Витрати', callback_data='menu:profile')],[InlineKeyboardButton(text='Додати нові розходи', callback_data="menu:new")]
    ])


profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='З початку місяця', callback_data="menu:mounth")],[InlineKeyboardButton(text='За минулий тиждень', callback_data="menu:week")],
    [InlineKeyboardButton(text='По карегоріям за місяць', callback_data='mounth:category')],[InlineKeyboardButton(text='По категоріям за минулий тиждень', callback_data='week:category')],
    [InlineKeyboardButton(text='Продукти за минулий місяць', callback_data='mounth:product')], [InlineKeyboardButton(text='Продукти за минулий тиждень', callback_data='week:product')],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="/menu")]
])


chose = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Існуючі категорії', callback_data="exist:cat")],[InlineKeyboardButton(text="Введіть нову категорію", callback_data="new:cat")], 
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="/menu")]
])


confirm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Підтвердити', callback_data="data:confirm")],
    [InlineKeyboardButton(text="Спочатку",callback_data="menu:new")]
])

async def back_button(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data))
    return builder.as_markup()