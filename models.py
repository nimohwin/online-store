from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    address = Column(String)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer, nullable=False)  # in KES
    category = Column(String)
    image_path = Column(String)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # empty = custom order
    color = Column(String)
    size = Column(String)
    yarn = Column(String)
    personalization = Column(String)
    notes = Column(String)
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product")
    images = relationship("OrderImage", back_populates="order")


class OrderImage(Base):
    __tablename__ = "order_images"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    image_path = Column(String, nullable=False)

    order = relationship("Order", back_populates="images")