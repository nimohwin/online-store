import sys

import bcrypt

from database import SessionLocal
from models import User

email = sys.argv[1]
new_password = sys.argv[2]

db = SessionLocal()
user = db.query(User).filter(User.email == email).first()

if user:
    user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    print(f"Password updated for {user.email}.")
else:
    print("No user found with that email.")