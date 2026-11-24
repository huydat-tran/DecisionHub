"""Router API cho module Auth."""

from fastapi import APIRouter, Body, Depends, status
from fastapi.openapi.models import Example
from sqlalchemy.orm import Session

from app.common.openapi import ResponsesDict, error_example, error_response
from app.core.database import get_db
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.modules.auth.service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])

REGISTER_REQUEST_EXAMPLE = Example(
    summary="Ví dụ đăng ký hợp lệ",
    description="Tài khoản mới với mật khẩu 8 ký tự, có chữ hoa và ký tự đặc biệt.",
    value={
        "username": "nguyenvanan",
        "email": "nguyenvanan@example.com",
        "password": "Abcd@1234",
    },
)

LOGIN_REQUEST_EXAMPLE = Example(
    summary="Ví dụ đăng nhập hợp lệ",
    description="Dùng email và mật khẩu đã đăng ký.",
    value={
        "email": "nguyenvanan@example.com",
        "password": "Abcd@1234",
    },
)

REGISTER_DESCRIPTION = """
Tạo tài khoản người dùng mới trong hệ thống DecisionHub.

**Quy tắc dữ liệu**

* `username`: bắt buộc, duy nhất, từ 5 đến 50 ký tự.
* `email`: bắt buộc, định dạng email hợp lệ, duy nhất trong hệ thống.
* `password`: bắt buộc, tối thiểu 8 ký tự, phải có ít nhất 1 chữ cái in hoa
  và 1 ký tự đặc biệt, tối đa 72 byte khi mã hóa UTF-8 (giới hạn của bcrypt).

Mật khẩu được lưu dưới dạng hash bcrypt, không bao giờ trả về mật khẩu gốc.
Tài khoản mới luôn được cấp vai trò mặc định `USER`, client không tự chọn vai trò.

**Lưu ý**: API này không yêu cầu xác thực. Sau khi đăng ký thành công,
client dùng endpoint `POST /auth/login` để lấy access token.
"""

LOGIN_DESCRIPTION = """
Xác thực tài khoản bằng email và mật khẩu, trả về access token JWT.

**Cách dùng token**

Lấy giá trị `data.access_token` trong response và gửi kèm header
`Authorization: Bearer <access_token>` cho mọi API cần đăng nhập
(ví dụ `GET /users/me`). Trên Swagger UI, dán token vào ô **Authorize** đã
được cấu hình sẵn cho scheme `HTTPBearer`.

Token mặc định hết hạn sau 60 phút (`ACCESS_TOKEN_EXPIRE_MINUTES`).

**Lưu ý**: thông báo lỗi luôn giống nhau cho cả trường hợp email không tồn tại
và mật khẩu sai, để không tiết lộ email nào đã được đăng ký.
"""

REGISTER_RESPONSES: ResponsesDict = {
    409: error_response(
        "Email hoặc username đã tồn tại trong hệ thống.",
        error_example(
            message="Email đã được đăng ký.",
            error_code="CONFLICT",
            path="/auth/register",
        ),
    ),
    422: error_response(
        "Dữ liệu đầu vào không hợp lệ: thiếu trường bắt buộc, sai định dạng email, "
        "mật khẩu quá ngắn, thiếu chữ hoa hoặc thiếu ký tự đặc biệt.",
        error_example(
            message="Dữ liệu đầu vào không hợp lệ",
            error_code="VALIDATION_ERROR",
            path="/auth/register",
            errors=[
                {
                    "field": "body.password",
                    "message": "Value error, Mật khẩu phải có ít nhất 1 chữ cái in hoa.",
                }
            ],
        ),
    ),
    500: error_response(
        "Lỗi hệ thống, ví dụ thiếu dữ liệu seed vai trò `USER`.",
        error_example(
            message=(
                "Không tìm thấy vai trò 'USER'. "
                "Vui lòng kiểm tra dữ liệu seed."
            ),
            error_code="INTERNAL_SERVER_ERROR",
            path="/auth/register",
        ),
    ),
}

LOGIN_RESPONSES: ResponsesDict = {
    401: error_response(
        "Email không tồn tại hoặc mật khẩu không đúng.",
        error_example(
            message="Email hoặc mật khẩu không đúng.",
            error_code="UNAUTHORIZED",
            path="/auth/login",
        ),
    ),
    422: error_response(
        "Dữ liệu đầu vào không hợp lệ: thiếu email/mật khẩu hoặc sai định dạng email.",
        error_example(
            message="Dữ liệu đầu vào không hợp lệ",
            error_code="VALIDATION_ERROR",
            path="/auth/login",
            errors=[
                {
                    "field": "body.email",
                    "message": "value is not a valid email address: An email address must have an @-sign.",
                }
            ],
        ),
    ),
}


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description=REGISTER_DESCRIPTION,
    responses=REGISTER_RESPONSES,
)
def register(
    data: RegisterRequest = Body(
        ...,
        openapi_examples={"register": REGISTER_REQUEST_EXAMPLE},
    ),
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """Đăng ký tài khoản mới, mặc định được cấp role USER."""
    user = register_user(db, data)
    return RegisterResponse(message="Đăng ký thành công.", data=user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Đăng nhập và nhận access token",
    description=LOGIN_DESCRIPTION,
    responses=LOGIN_RESPONSES,
)
def login(
    data: LoginRequest = Body(
        ...,
        openapi_examples={"login": LOGIN_REQUEST_EXAMPLE},
    ),
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Đăng nhập bằng email và mật khẩu, trả về access token."""
    token_data = login_user(db, data)
    return LoginResponse(message="Đăng nhập thành công.", data=token_data)
