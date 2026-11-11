"""Truy vấn database cho items."""

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.modules.items.models import Item
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self, keyword: str | None = None) -> list[Item]:
        query = select(Item).order_by(Item.id.asc())
        if keyword:
            query = query.where(Item.name.ilike(f"%{keyword}%"))
        return list(self.db.scalars(query).all())

    def get_by_id(self, item_id: int) -> Item | None:
        return self.db.get(Item, item_id)

    def create(self, item_in: ItemCreate) -> Item:
        # Lấy ID kế tiếp dựa trên MAX(id) hiện tại để ID luôn liên tục
        max_id = self.db.scalar(select(func.max(Item.id))) or 0
        next_id = max_id + 1

        item = Item(
            id=next_id,
            name=item_in.name,
            description=item_in.description,
            price=item_in.price,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        # Đồng bộ lại AUTO_INCREMENT của MySQL
        self.db.execute(text(f"ALTER TABLE items AUTO_INCREMENT = {next_id + 1}"))
        self.db.commit()
        return item

    def update(self, item: Item, item_in: ItemUpdate) -> Item:
        update_data = item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: Item) -> None:
        deleted_id = item.id
        self.db.delete(item)
        self.db.commit()

        # Dồn các ID phía sau giảm đi 1 để danh sách ID luôn liên tục (1, 2, 3...)
        self.db.execute(
            text("UPDATE items SET id = id - 1 WHERE id > :deleted_id ORDER BY id ASC"),
            {"deleted_id": deleted_id},
        )
        self.db.commit()

        # Reset lại AUTO_INCREMENT của MySQL
        max_id = self.db.scalar(select(func.max(Item.id))) or 0
        self.db.execute(text(f"ALTER TABLE items AUTO_INCREMENT = {max_id + 1}"))
        self.db.commit()
