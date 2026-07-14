from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Category(Base):
    __tablename__ = 'Categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(75), nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates='category')


class Product(Base):
    __tablename__ = "Products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(75), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)

    category_id: Mapped[int] = mapped_column(ForeignKey('Categories.id'), nullable=False)

    category: Mapped["Category"] = relationship(back_populates='products', lazy='selectin')

