# Smart Cart: Crochet Online Store

A full-stack web application for a handmade crochet business. Customers can browse the work, create an account, and place orders with their own colors, sizes, personalization and inspiration photos. The shop owner manages the catalogue through a private admin area.

Built as a portfolio project with **FastAPI**, **SQLite** and **Docker**.

<!-- Add screenshots here, for example:
![Home page](docs/home.png)
![Order form](docs/order-form.png)
-->

## Features

- **Product gallery:** the home page shows every product as a card with photo, category, description and price.
- **User accounts:** registration and login with securely hashed passwords (bcrypt) and cookie-based sessions.
- **Personalized orders:** customers choose colors, size and yarn type, add a name or initials, write notes, and upload up to 5 inspiration photos.
- **Custom orders:** customers can request something that is not in the gallery by describing it and sharing inspiration images.
- **My Orders page:** customers can see all their orders, with details, photos and status.
- **Admin area:** the shop owner can add products with photo upload (admin accounts only).

## Tech Stack

| Layer      | Technology                                  |
|------------|---------------------------------------------|
| Back end   | Python, FastAPI, SQLAlchemy                 |
| Database   | SQLite                                      |
| Front end  | HTML, CSS, JavaScript, Jinja2 templates     |
| Auth       | bcrypt password hashing, Starlette sessions |
| Deployment | Docker and Docker Compose                   |

## Project Structure

```
online-store/
├── main.py                  # FastAPI app and all routes
├── models.py                # SQLAlchemy models (User, Product, Order, OrderImage)
├── database.py              # Database engine and session setup
├── make_admin.py            # Script to promote a user to admin
├── reset_password.py        # Script to reset a user's password
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── templates/               # Jinja2 HTML pages
│   ├── home.html
│   ├── register.html
│   ├── login.html
│   ├── order_form.html
│   ├── my_orders.html
│   └── admin_add_product.html
└── static/
    └── uploads/             # Product and inspiration images
```

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

### Run the project

```bash
git clone https://github.com/nimohwin/online-store.git
cd online-store
docker compose up --build
```

Then open:

- **Store:** http://localhost:8000
- **API docs (auto-generated):** http://localhost:8000/docs

The SQLite database (`store.db`) is created automatically on first run. Stop the app with `Ctrl+C`.

### Create an admin account

1. Register a normal account at http://localhost:8000/register.
2. Promote it to admin (use your own email):

```bash
docker compose run --rm web python make_admin.py your@email.com
```

3. Log in. An **Add product** link now appears in the navigation bar.

### Reset a forgotten password

```bash
docker compose run --rm web python reset_password.py your@email.com NewPassword123
```

## Main Routes

| Route                  | Method   | Description                              |
|------------------------|----------|------------------------------------------|
| `/`                    | GET      | Home page with product gallery           |
| `/register`            | GET/POST | Create an account                        |
| `/login`               | GET/POST | Log in                                   |
| `/logout`              | GET      | Log out                                  |
| `/order/new`           | GET      | Order form (for a product or custom)     |
| `/orders`              | POST     | Submit an order with inspiration photos  |
| `/my-orders`           | GET      | The logged-in customer's orders          |
| `/admin/products/new`  | GET      | Add-product form (admin only)            |
| `/admin/products`      | POST     | Create a product (admin only)            |

## Roadmap

- [ ] Admin page to view all orders and update their status
- [ ] Edit and delete products
- [ ] Product detail pages
- [ ] Change password from the site
- [ ] M-Pesa payment integration
- [ ] Deployment to a live URL

## Security Notes

- Passwords are hashed with bcrypt and never stored in plain text.
- Uploads are restricted to `.jpg`, `.jpeg`, `.png` and `.webp`, and are saved under random file names.
- Change the session `secret_key` in `main.py` to a long random value before deploying publicly.

## Author

Your Name: [GitHub](https://github.com/nimohwin)
