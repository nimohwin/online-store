import os
import uuid
from typing import List

import bcrypt
from fastapi import FastAPI, Request, Form, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload, selectinload
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine, get_db
from models import User, Product, Order, OrderImage

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_INSPO_IMAGES = 5
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="change-this-to-something-long-and-random")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    return db.get(User, user_id) if user_id else None


async def save_upload(file: UploadFile):
    """Saves an uploaded image and returns its web path, or None if invalid."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(await file.read())
    return f"/static/uploads/{filename}"


# ---------- Home ----------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"user": get_current_user(request, db), "products": products},
    )


# ---------- Auth ----------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "That email is already registered."},
        )
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.add(User(name=fullname, email=email, address=address, phone=phone, password_hash=hashed))
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Wrong email or password."},
        )
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ---------- Admin: add products ----------

@app.get("/admin/products/new", response_class=HTMLResponse)
def new_product_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request=request, name="admin_add_product.html", context={"user": user}
    )


@app.post("/admin/products", response_class=HTMLResponse)
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    price: int = Form(...),
    category: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/login", status_code=303)

    image_path = await save_upload(image)
    if not image_path:
        return templates.TemplateResponse(
            request=request,
            name="admin_add_product.html",
            context={"user": user, "error": "Please upload a .jpg, .png or .webp image."},
        )

    db.add(Product(
        name=name,
        description=description,
        price=price,
        category=category,
        image_path=image_path,
    ))
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# ---------- Orders ----------

@app.get("/order/new", response_class=HTMLResponse)
def order_page(request: Request, product_id: int | None = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    product = db.get(Product, product_id) if product_id else None
    return templates.TemplateResponse(
        request=request,
        name="order_form.html",
        context={"user": user, "product": product},
    )


@app.post("/orders", response_class=HTMLResponse)
async def create_order(
    request: Request,
    product_id: str = Form(""),
    color: str = Form(""),
    size: str = Form(""),
    yarn: str = Form(""),
    personalization: str = Form(""),
    notes: str = Form(""),
    inspo: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    product = db.get(Product, int(product_id)) if product_id.isdigit() else None

    if not product and not notes.strip():
        return templates.TemplateResponse(
            request=request,
            name="order_form.html",
            context={
                "user": user,
                "product": None,
                "error": "For a custom order, please describe what you want in the notes.",
            },
        )

    order = Order(
        user_id=user.id,
        product_id=product.id if product else None,
        color=color,
        size=size,
        yarn=yarn,
        personalization=personalization,
        notes=notes,
    )
    db.add(order)
    db.flush()  # gives the order an id before we attach images

    files = [f for f in inspo if f.filename][:MAX_INSPO_IMAGES]
    for f in files:
        path = await save_upload(f)
        if path:
            db.add(OrderImage(order_id=order.id, image_path=path))

    db.commit()
    return RedirectResponse(url="/my-orders", status_code=303)


@app.get("/my-orders", response_class=HTMLResponse)
def my_orders(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    orders = (
        db.query(Order)
        .options(joinedload(Order.product), selectinload(Order.images))
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="my_orders.html",
        context={"user": user, "orders": orders},
    )