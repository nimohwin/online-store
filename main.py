import os
import uuid

import bcrypt
from fastapi import FastAPI, Request, Form, Depends, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine, get_db
from models import User, Product

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="change-this-to-something-long-and-random")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")
    return db.get(User, user_id) if user_id else None


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

    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return templates.TemplateResponse(
            request=request,
            name="admin_add_product.html",
            context={"user": user, "error": "Please upload a .jpg, .png or .webp image."},
        )

    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(await image.read())

    db.add(Product(
        name=name,
        description=description,
        price=price,
        category=category,
        image_path=f"/static/uploads/{filename}",
    ))
    db.commit()
    return RedirectResponse(url="/", status_code=303)