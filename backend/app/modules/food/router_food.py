"""Router API cho module Food (CRUD món ăn cho người dùng và trang Admin)."""

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.food.schemas_food import (
    FoodCreate,
    FoodDeletedData,
    FoodDeleteResponse,
    FoodDetailResponse,
    FoodListResponse,
    FoodUpdate,
)
from app.modules.food.services import (
    create_food,
    delete_food,
    get_all_foods,
    get_food_detail,
    update_food,
)

router = APIRouter(prefix="/api/v1/food", tags=["Food"])


@router.get(
    "",
    response_model=FoodListResponse,
    summary="Lấy danh sách món ăn",
)
def list_foods(
    include_inactive: bool = Query(
        default=False,
        description="Bao gồm cả món ăn tạm ngưng (dùng cho trang quản trị)",
    ),
    db: Session = Depends(get_db),
) -> FoodListResponse:
    """Trả về danh sách món ăn (mặc định chỉ lấy món đang hoạt động)."""
    foods = get_all_foods(db=db, include_inactive=include_inactive)
    return FoodListResponse(message="Lấy danh sách món ăn thành công.", data=foods)


@router.get(
    "/{food_id}",
    response_model=FoodDetailResponse,
    summary="Xem chi tiết món ăn",
)
def get_food(
    food_id: int = Path(..., gt=0, description="ID món ăn"),
    include_inactive: bool = Query(
        default=False,
        description="Cho phép xem cả món ăn tạm ngưng (dùng cho trang quản trị)",
    ),
    db: Session = Depends(get_db),
) -> FoodDetailResponse:
    """Trả về thông tin chi tiết của một món ăn theo ID."""
    food = get_food_detail(db=db, food_id=food_id, include_inactive=include_inactive)
    return FoodDetailResponse(message="Lấy thông tin món ăn thành công.", data=food)


# shortcut: chưa gắn Depends kiểm tra JWT role ADMIN cho POST/PUT/DELETE do Admin Console
# chưa nối luồng đăng nhập; bổ sung phân quyền ADMIN khi trang admin tích hợp auth.
@router.post(
    "",
    response_model=FoodDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm món ăn mới (Admin)",
)
def create_food_endpoint(
    payload: FoodCreate,
    db: Session = Depends(get_db),
) -> FoodDetailResponse:
    """Tạo mới món ăn kèm danh sách nhãn và nguyên liệu."""
    food = create_food(db=db, payload=payload)
    return FoodDetailResponse(message="Thêm món ăn thành công.", data=food)


@router.put(
    "/{food_id}",
    response_model=FoodDetailResponse,
    summary="Cập nhật món ăn (Admin)",
)
def update_food_endpoint(
    payload: FoodUpdate,
    food_id: int = Path(..., gt=0, description="ID món ăn"),
    db: Session = Depends(get_db),
) -> FoodDetailResponse:
    """Cập nhật thông tin món ăn theo ID."""
    food = update_food(db=db, food_id=food_id, payload=payload)
    return FoodDetailResponse(message="Cập nhật món ăn thành công.", data=food)


@router.delete(
    "/{food_id}",
    response_model=FoodDeleteResponse,
    summary="Xoá món ăn (Admin)",
)
def delete_food_endpoint(
    food_id: int = Path(..., gt=0, description="ID món ăn"),
    db: Session = Depends(get_db),
) -> FoodDeleteResponse:
    """Xoá món ăn theo ID khỏi hệ thống."""
    deleted_id = delete_food(db=db, food_id=food_id)
    return FoodDeleteResponse(
        message="Xoá món ăn thành công.",
        data=FoodDeletedData(id=deleted_id),
    )
