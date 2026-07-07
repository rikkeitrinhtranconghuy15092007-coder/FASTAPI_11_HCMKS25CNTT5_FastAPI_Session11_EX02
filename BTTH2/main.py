import uvicorn
from fastapi import FastAPI, status, HTTPException, Depends, Request
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ecommerce_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SmartHomePlanModel(Base):
    __tablename__ = "smart_home_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    device_quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Smart Home Plans Management API")

class SmartHomePlanCreate(BaseModel):
    plan_code: str = Field(..., min_length=1)
    plan_name: str = Field(..., min_length=1)
    device_quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0.0)

class APIStandardResponse(BaseModel):
    statusCode: int
    message: str
    error: Optional[str] = None
    data: Optional[dict] = None
    path: str
    timestamp: str

class APIListStandardResponse(BaseModel):
    statusCode: int
    message: str
    error: Optional[str] = None
    data: List[dict]
    path: str
    timestamp: str

@app.post("/smart-home-plans", status_code=status.HTTP_201_CREATED, response_model=APIStandardResponse)
async def create_smart_home_plan(request: Request, payload: SmartHomePlanCreate, db: Session = Depends(get_db)):
    
    existing_plan = db.query(SmartHomePlanModel).filter(
        SmartHomePlanModel.plan_code == payload.plan_code.strip()
    ).first()
    
    if existing_plan:
        return APIStandardResponse(
            statusCode=400,
            message="Plan code already exists",
            error="Bad Request",
            data=None,
            path=str(request.url.path),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    new_plan = SmartHomePlanModel(
        plan_code=payload.plan_code.strip(),
        plan_name=payload.plan_name.strip(),
        device_quantity=payload.device_quantity,
        price=payload.price
    )
    
    try:
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        return APIStandardResponse(
            statusCode=201,
            message="Thêm gói thiết bị mới thành công",
            error=None,
            data={
                "id": new_plan.id,
                "plan_code": new_plan.plan_code,
                "plan_name": new_plan.plan_name,
                "device_quantity": new_plan.device_quantity,
                "price": new_plan.price
            },
            path=str(request.url.path),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    except Exception as e:
        db.rollback()
        return APIStandardResponse(
            statusCode=500,
            message="Lỗi hệ thống khi lưu trữ dữ liệu",
            error=str(e),
            data=None,
            path=str(request.url.path),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

@app.get("/smart-home-plans", status_code=status.HTTP_200_OK, response_model=APIListStandardResponse)
async def get_all_smart_home_plans(request: Request, db: Session = Depends(get_db)):
    plans = db.query(SmartHomePlanModel).all()
    
    data_list = [
        {
            "id": plan.id,
            "plan_code": plan.plan_code,
            "plan_name": plan.plan_name,
            "device_quantity": plan.device_quantity,
            "price": plan.price
        } for plan in plans
    ]
    
    return APIListStandardResponse(
        statusCode=200,
        message="Lấy danh sách thành công",
        error=None,
        data=data_list,
        path=str(request.url.path),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

@app.get("/smart-home-plans/{plan_id}", status_code=status.HTTP_200_OK, response_model=APIStandardResponse)
async def get_smart_home_plan_detail(plan_id: int, request: Request, db: Session = Depends(get_db)):
    plan = db.query(SmartHomePlanModel).filter(SmartHomePlanModel.id == plan_id).first()
    
    if not plan:
        return APIStandardResponse(
            statusCode=404,
            message="Plan not found",
            error="Not Found",
            data=None,
            path=str(request.url.path),
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    return APIStandardResponse(
        statusCode=200,
        message="Lấy thông tin chi tiết gói thiết bị thành công",
        error=None,
        data={
            "id": plan.id,
            "plan_code": plan.plan_code,
            "plan_name": plan.plan_name,
            "device_quantity": plan.device_quantity,
            "price": plan.price
        },
        path=str(request.url.path),
        timestamp=datetime.utcnow().isoformat() + "Z"
    )