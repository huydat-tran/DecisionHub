"""Router cho items API."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.modules.items.service import ItemService

router = APIRouter()


def get_item_service(db: Session = Depends(get_db)) -> ItemService:
    return ItemService(db)


@router.get("", response_model=list[ItemResponse], summary="Lấy danh sách items")
def list_items(
    q: str | None = Query(None, description="Từ khóa tìm kiếm theo tên"),
    service: ItemService = Depends(get_item_service),
):
    return service.list_items(keyword=q)


@router.get("/{item_id}", response_model=ItemResponse, summary="Lấy chi tiết item")
def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
):
    return service.get_item(item_id)


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo item mới",
)
def create_item(
    item_in: ItemCreate,
    service: ItemService = Depends(get_item_service),
):
    return service.create_item(item_in)


@router.put("/{item_id}", response_model=ItemResponse, summary="Cập nhật item")
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    service: ItemService = Depends(get_item_service),
):
    return service.update_item(item_id, item_in)


@router.delete("/{item_id}", status_code=status.HTTP_200_OK, summary="Xóa item")
def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
):
    service.delete_item(item_id)
    return {"success": True, "message": f"Đã xoá item #{item_id}"}
