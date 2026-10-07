import bcrypt
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine, get_db
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="change-this-to-something-long-and-random")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")


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