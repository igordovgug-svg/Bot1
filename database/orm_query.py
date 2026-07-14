from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category, Product

from aiogram.types import Message, CallbackQuery


async def orm_succesfull(message: Message, session: AsyncSession, data: dict):
    obj = Category(
        user_id=message.from_user.id,
        name=data['name']
    )
    session.add(obj)
    await session.commit()


async def orm_confirm_product(callback: CallbackQuery, session: AsyncSession, data: dict):
    obj = Product(
        name=data['name'],
        user_id=callback.from_user.id,
        price=data['price'],
        category_id=data['category_id']
    )

    session.add(obj)
    await session.commit()


async def orm_mounth_or_week(callback: CallbackQuery, session: AsyncSession, time):
    data = await session.execute(
        select(func.sum(Product.price)).where(
            Product.created_at >= time, 
            Product.user_id == callback.from_user.id
        )
    )
    return data


async def orm_cat_mounth_or_week(callback: CallbackQuery, session: AsyncSession, time):
    data = await session.execute(
        select(
            Category.name,
            func.sum(Product.price)
        )
        .join(Product, Product.category_id == Category.id)
        .where(
            Category.user_id == callback.from_user.id, 
            Product.created_at >= time)
        .group_by(Category.name)
        .order_by(func.sum(Product.price).desc())
    )

    return data


async def orm_get_m_or_w_product(callback: CallbackQuery, session: AsyncSession, time):
    data = await session.execute(
        select(
            Product.name, 
            Product.price,
            func.date(Product.created_at)
        )
        .where(
            Product.user_id == callback.from_user.id,
            Product.created_at >= time)
        
        .order_by(Product.created_at.desc())
    )

    return data