from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import hashlib

from database import engine, get_db
import models


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

models.Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# APP
# --------------------------------------------------

app = FastAPI(
    title="Digital Product Store API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# JWT SETTINGS
# --------------------------------------------------

SECRET_KEY = "digital-product-store-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict):
    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = db.query(models.User).filter(
        models.User.id == int(user_id)
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProductRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


class OrderRequest(BaseModel):
    user_id: int
    product_id: int


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Digital Product Store API"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post("/auth/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = models.User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/auth/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if user.hashed_password != hash_password(data.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# --------------------------------------------------
# PROFILE - PROTECTED
# --------------------------------------------------

@app.get("/profile")
def get_profile(
    current_user=Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }


# --------------------------------------------------
# CREATE PRODUCT - PROTECTED
# --------------------------------------------------

@app.post("/products")
def create_product(
    data: ProductRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    product = models.Product(
        name=data.name,
        description=data.description or "",
        price=data.price
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# --------------------------------------------------
# GET PRODUCTS + PAGINATION + SEARCH
# --------------------------------------------------

@app.get("/products")
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if search:
        query = query.filter(
            models.Product.name.contains(search)
        )

    total = query.count()

    products = query.offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "products": products
    }


# --------------------------------------------------
# GET PRODUCT
# --------------------------------------------------

@app.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# --------------------------------------------------
# UPDATE PRODUCT - PROTECTED
# --------------------------------------------------

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    data: ProductRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.name = data.name
    product.description = data.description or ""
    product.price = data.price

    db.commit()
    db.refresh(product)

    return product


# --------------------------------------------------
# DELETE PRODUCT - PROTECTED
# --------------------------------------------------

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }


# --------------------------------------------------
# CREATE ORDER - PROTECTED
# --------------------------------------------------

@app.post("/orders")
def create_order(
    data: OrderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    new_order = models.Order(
        user_id=current_user.id,
        product_id=data.product_id,
        amount=product.price,
        status="pending"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order


# --------------------------------------------------
# GET ORDERS - PROTECTED
# --------------------------------------------------

@app.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(models.Order).filter(
        models.Order.user_id == current_user.id
    ).all()


# --------------------------------------------------
# GET ORDER
# --------------------------------------------------

@app.get("/orders/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


# --------------------------------------------------
# CHECKOUT PLACEHOLDER
# --------------------------------------------------

@app.post("/orders/{order_id}/checkout")
def checkout(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order.status = "payment_pending"

    db.commit()
    db.refresh(order)

    return {
        "message": "Checkout ready",
        "order_id": order.id,
        "amount": order.amount,
        "status": order.status
    }


# --------------------------------------------------
# STRIPE WEBHOOK PLACEHOLDER
# --------------------------------------------------

@app.post("/stripe/webhook")
def stripe_webhook():
    return {
        "message": "Stripe webhook endpoint working"
    }