from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (đăng ký models vào metadata)
from .config import settings
from .database import Base, SessionLocal, engine
from .routers import (
    announcements,
    assets,
    attendance,
    auth,
    dashboard,
    departments,
    employees,
    leaves,
    reports,
    rooms,
    tasks,
)
from .seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tạo bảng còn thiếu (schema chính nằm ở db/init/01_schema.sql)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Hệ thống Quản lý Văn phòng",
    description="API quản lý nhân viên, phòng ban, điểm danh, nghỉ phép, công việc, tài sản, phòng họp, thông báo và báo cáo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    dashboard,
    departments,
    employees,
    attendance,
    leaves,
    tasks,
    assets,
    rooms,
    announcements,
    reports,
):
    app.include_router(module.router)


@app.get("/api/health", tags=["Hệ thống"])
def health():
    return {"status": "ok"}
