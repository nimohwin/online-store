import sys
from database import SessionLocal
from models import User

db = SessionLocal()
user = db.query(User).filter(User.email == sys.argv[1]).first()
if user:
    user.role = "admin"
    db.commit()
    print(f"{user.email} is now an admin.")
else:
    print("No user found with that email.")