from aiogram import F, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


from database.models import Category, Product
from database.orm_query import orm_cat_mounth_or_week, orm_confirm_product, orm_get_m_or_w_product, orm_mounth_or_week, orm_succesfull


from app import keyboards as kb


from datetime import datetime, timedelta


router = Router()


@router.message(F.text == "🏠 Меню")
async def go_home(message: Message, state: FSMContext):
    await state.clear()  # скидаємо будь-який незавершений сценарій (додавання товару, категорії тощо)
    await message.answer("Це ваше меню, виберіть що вас цікавить", reply_markup=kb.menu)


@router.message(Command("Cat"))
async def cat(message: Message, session: AsyncSession):
    await message.answer(text="Категорії", reply_markup=await kb.get_cats(session=session))

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Вітаю, цей бот допоможе тобі в введені твоїх щомісячних витрат', reply_markup=kb.start_menu)
    await message.answer("Кнопка нижче поверне тебе в меню з будь-якого місця 👇", reply_markup=kb.main_reply_kb)

  
@router.callback_query(F.data == '/menu')
async def menu(callback: CallbackQuery):
    await callback.answer('----')
    await callback.message.edit_text("Це ваше меню виберіть що вас цікавить", reply_markup=kb.menu)


@router.callback_query(F.data == 'menu:profile')
async def profile(callback: CallbackQuery):
    await callback.answer(text='----')
    await callback.message.edit_text(text='Мої витрати', reply_markup=kb.profile)
    

@router.callback_query(F.data =="menu:new")
async def new_spent(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer(text="Введіть/Виберіть категорію товару")
    await callback.message.edit_text(text="Введіть/Виберіть категорію товару", reply_markup=kb.chose)


@router.callback_query(F.data =="exist:cat")
async def exist_cat(callback: CallbackQuery, session: AsyncSession):
    keyboard = await kb.get_cats(callback=callback, session=session)

    if keyboard is None:
        await callback.answer('Категорій ще немає')
        await callback.message.edit_text(
            text='У вас ще немає жодної категорії. Створіть нову:', 
            reply_markup=await kb.back_button(callback_data="menu:new")
        )
        return
    
    await callback.answer(text='Категорії')
    await callback.message.edit_text(text="Категорії", reply_markup=keyboard)


class AddProducntCategory(StatesGroup):
    name = State()


@router.callback_query(StateFilter(None), F.data =="new:cat")
async def new_cat(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Введіть назву нової категорії")
    await state.set_state(AddProducntCategory.name)



@router.message(AddProducntCategory.name, F.text)
async def succesfull(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(name=message.text)
    await message.answer("Нова категорія добавленна", reply_markup=kb.chose)

    data = await state.get_data()
    
    await orm_succesfull(message=message, session=session, data=data)

    await state.clear()
    

class AddProduct(StatesGroup):
    category_id = State()
    name = State()
    price = State()


@router.callback_query(StateFilter(None), F.data.startswith("product:"))
async def add(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])

    await state.update_data(category_id=category_id)

    await callback.answer(text='Ви вибрали категрію')
    await callback.message.edit_text(text="Введіть назву товару")
    await state.set_state(AddProduct.name)


@router.message(AddProduct.name, F.text)
async def add_name_product(message: Message, state: FSMContext,):
    await state.update_data(name=message.text.title())
    await message.answer('Введіть ціну в грн')
    await state.set_state(AddProduct.price)


@router.message(AddProduct.price, F.text)
async def add_price_product(message: Message, state: FSMContext, session: AsyncSession):
    price_text = message.text.replace(",", ".")  # заміняємо кому на крапку
    
    try:
        price = float(price_text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Невірний формат ціни. Введіть число, наприклад: 150 або 99.99")
        return  
    
    await state.update_data(price=price)

    data = await state.get_data()

    await message.answer(f"Назва: {data['name']} \nЦіна: {data['price']}", reply_markup=kb.confirm)


@router.callback_query(F.data =='data:confirm')
async def confirm_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    data = await state.get_data()

    await orm_confirm_product(callback, session, data)

    await state.clear()

    await callback.message.edit_text("Товар додано до витрат", reply_markup=kb.profile)


@router.callback_query(F.data == "menu:mounth")
async def mounth(callback: CallbackQuery, session: AsyncSession):
    now = datetime.now()
    start_of_mounth = now.replace(day=1, hour=0)

    result = await orm_mounth_or_week(callback, session, start_of_mounth)
    
    total = result.scalar() or 0
    
    await callback.answer("Витрати за місяць")
    await callback.message.edit_text(f"Витрати за місяць, {total:.2f} грн", reply_markup=await kb.back_button(callback_data="menu:profile"))


@router.callback_query(F.data == "menu:week")
async def week(callback: CallbackQuery, session: AsyncSession):
    one_week = datetime.now() - timedelta(days=7)
    result = await orm_mounth_or_week(callback, session, one_week)

    total = result.scalar() or 0

    await callback.answer("Витрати за останні 7 днів")
    await callback.message.edit_text(f"Витрати за останні 7 днів, {total:.2f} грн", reply_markup=await kb.back_button(callback_data="menu:profile"))


@router.callback_query(F.data == 'mounth:category')
async def cat_mounth(callback: CallbackQuery, session: AsyncSession):
    now = datetime.now()
    start_of_mounth = now.replace(day=1, hour=0)
    
    result = await orm_cat_mounth_or_week(callback, session, start_of_mounth)

    rows = result.all()

    await callback.answer("Витрати по категоріям за останій місяць")


    if not rows:
        await callback.message.edit_text("Витрат ще немає.")
        return
    
    
    lines = [f"{name}: {total:.2f} грн  " for name, total in rows]
    text = "Витрати по категоріям за останній місяць:\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=await kb.back_button(callback_data="menu:profile"))

@router.callback_query(F.data == 'week:category')
async def cat_week(callback: CallbackQuery, session: AsyncSession):
    one_week = datetime.now() - timedelta(days=7)
    
    result = await orm_cat_mounth_or_week(callback, session, one_week)
    rows = result.all()

    await callback.answer("Витрати по категоріям за остані 7 днів")


    if not rows:
        await callback.message.edit_text("Витрат ще немає.")
        return
    
    
    lines = [f"{name}: {total:.2f} грн  " for name, total in rows]
    text = "Витрати по категоріям за останній 7 днів:\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=await kb.back_button(callback_data="menu:profile"))


@router.callback_query(F.data == 'mounth:product')
async def get_m_product(callback: CallbackQuery, session: AsyncSession):
    now = datetime.now()
    start_of_mounth = now.replace(day=1, hour=0)
   
    result = await orm_get_m_or_w_product(callback, session, start_of_mounth)
    
    rows = result.all()

    if not rows:
        await callback.message.edit_text("Витрат ще немає.")
        return
    
    lines = [f"{name}:  {total:.2f} грн  -> {time}" for name, total, time in rows]
    text = 'Продукти за останій місяць:\n\n' + "\n".join(lines)
    
    await callback.answer("Продукти за місяць")
    await callback.message.edit_text(text, reply_markup=await kb.back_button(callback_data="menu:profile"))


@router.callback_query(F.data == 'week:product')
async def get_w_product(callback: CallbackQuery, session: AsyncSession):
    one_week = datetime.now() - timedelta(days=7)
   
    result = await orm_get_m_or_w_product(callback, session, one_week)

    rows = result.all()

    if not rows:
        await callback.message.edit_text("Витрат ще немає.")
        return
    

    lines = [f"{name}:  {total:.2f} грн -> {time}" for name, total, time in rows]
    text = 'Продукти за остані 7 днів:\n\n' + "\n".join(lines)

    await callback.answer("Продукти за тиждень")
    await callback.message.edit_text(text, reply_markup=await kb.back_button(callback_data="menu:profile"))   