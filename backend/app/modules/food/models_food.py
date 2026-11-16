from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any

from sqlalchemy import ( Integer,String,Text,Numeric,Boolean,DateTime,ForeignKey,JSON,CheckConstraint,func,)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 1. Bảng trung gian: FOOD_Ingredients (Association Model)
class FoodIngredient(Base):
    __tablename__ = "food_ingredients"

    food_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("foods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ingredients_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        primary_key=True,
    )


# 2. Bảng FOODS
class Food(Base):
    __tablename__ = "foods"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Lưu trữ mảng/object dạng JSON (VD: ["spicy", "vegan"])
    tags: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Ràng buộc kiểm tra giá trị hợp lệ ở tầng Database
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_food_price_non_negative"),
        CheckConstraint("prep_time >= 0", name="check_prep_time_non_negative"),
    )

    # Quan hệ Many-to-Many tới bảng Ingredients
    ingredients: Mapped[List["Ingredient"]] = relationship(
        "Ingredient",
        secondary="food_ingredients",
        back_populates="foods",
        lazy="selectin",  # Tối ưu truy vấn bất đồng bộ/FastAPI tránh lỗi N+1 query
    )


# 3. Bảng INGREDIENTS
class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    foods: Mapped[List["Food"]] = relationship(
        "Food",
        secondary="food_ingredients",
        back_populates="ingredients",
    )