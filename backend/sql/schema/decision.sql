-- =====================================================================
-- DecisionHub - SQL DDL tạo bảng cho module Decision
--
-- Lưu ý chuẩn dự án:
--   - Nguồn quản lý schema chính thức là SQLAlchemy models
--     (app/modules/decision/models.py) và Alembic migrations (alembic/versions/).
--   - File này cung cấp DDL SQL thuần đồng bộ 1:1 với Alembic để tham khảo,
--     kiểm tra hoặc chạy thủ công khi cần.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

CREATE TABLE IF NOT EXISTS decision_criteria (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    weight NUMERIC(5, 4) NOT NULL,
    CONSTRAINT pk_decision_criteria PRIMARY KEY (id),
    CONSTRAINT ck_decision_criteria_direction CHECK (direction IN ('min', 'max')),
    CONSTRAINT ck_decision_criteria_weight CHECK (weight >= 0 AND weight <= 1),
    CONSTRAINT uq_decision_criteria_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS hard_constraints (
    id BIGINT NOT NULL AUTO_INCREMENT,
    domain VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    operator VARCHAR(20) NOT NULL,
    description VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    CONSTRAINT pk_hard_constraints PRIMARY KEY (id),
    CONSTRAINT ck_hard_constraints_domain CHECK (domain IN ('food', 'travel')),
    CONSTRAINT ck_hard_constraints_operator CHECK (operator IN ('<=', '>=', '=', '!=', 'in', 'not_in')),
    CONSTRAINT uq_hard_constraints_domain_name UNIQUE (domain, name),
    INDEX idx_hard_constraints_domain_active (domain, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
