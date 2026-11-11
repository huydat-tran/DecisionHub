"""Business logic cho items."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.items.models import Item
from app.modules.items.repository import ItemRepository
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemService:
    def __init__(self, db: Session) -> None:
        self.repo = ItemRepository(db)

    def list_items(self, keyword: str | None = None) -> list[Item]:
        return self.repo.get_all(keyword)

    def get_item(self, item_id: int) -> Item:
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy item #{item_id}",
            )
        return item

    def create_item(self, item_in: ItemCreate) -> Item:
        return self.repo.create(item_in)

    def update_item(self, item_id: int, item_in: ItemUpdate) -> Item:
        item = self.get_item(item_id)
        return self.repo.update(item, item_in)

    def delete_item(self, item_id: int) -> None:
        item = self.get_item(item_id)
        self.repo.delete(item)
