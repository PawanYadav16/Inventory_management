# Inventory Management System

A professional, clean, beginner-friendly **Inventory Management System** web application built with **Python Flask**, **Flask-SQLAlchemy**, **Flask-Login**, **Flask-WTF**, **Flask-Migrate**, **Bootstrap 5**, and **Chart.js**.

---

## 🌟 Features

* **Public Landing Page (`/`)**: Hero section, system features, workflow overview, live dashboard interface preview, call-to-action, and responsive footer.
* **Secure Authentication (`/login`, `/register`, `/logout`)**:
  * Werkzeug password hashing
  * Session management via Flask-Login
  * CSRF token protection on all forms via Flask-WTF
  * Strict per-user data isolation (users can only view/edit/delete their own inventory).
* **Interactive Dashboard (`/dashboard`)**:
  * Dynamic summary cards: Total Products, Total Quantity, Low Stock Alerts, Out of Stock, Category Count.
  * Real-time search by product name or SKU.
  * Multi-category filtering, stock status filtering, and multi-field sorting (Name A-Z/Z-A, Quantity Low/High, Price Low/High).
  * Direct POST-based **`[ − ] quantity [ + ]`** quick controls.
* **Product CRUD Operations (`/items/add`, `/items/<id>`, `/items/<id>/edit`, `/items/<id>/delete`)**:
  * Product specifications: Name, Description, Category, Quantity, Minimum Alert Quantity, Price, Supplier, SKU, Storage Location.
  * Per-user unique SKU validation.
  * Quantity validation: integers $\ge 0$ allowed (`0` represents Out of Stock).
* **Automatic Stock Status Detection**:
  * **Out of Stock**: `quantity == 0`
  * **Low Stock**: `0 < quantity <= minimum_quantity`
  * **In Stock**: `quantity > minimum_quantity`
* **Stock History Audit Trail (`/items/<id>/history`)**:
  * Tracks every quantity modification (+1, -1, initial stock, manual edit diffs).
* **Visual Analytics (`/analytics`)**:
  * Chart.js Doughnut chart for Stock Status Distribution.
  * Chart.js Bar chart for Category Valuation ($).
  * Category breakdown summary table and top stock highlights.
* **User Profile & Password Management (`/profile`)**:
  * Displays user profile details, member registration date, total managed products, and secure password update form.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.10+, Flask 3.x
* **ORM & Database**: Flask-SQLAlchemy, SQLite (Development DB)
* **Authentication**: Flask-Login, Werkzeug Security
* **Form Handling & Validation**: Flask-WTF, WTForms, email-validator
* **Database Migrations**: Flask-Migrate (Alembic)
* **Frontend**: HTML5, CSS3, Jinja2 Templates, Bootstrap 5, Bootstrap Icons, Chart.js

---

## 📁 Project Structure

```text
inventory_management/
│
├── app/
│   ├── __init__.py          # Flask Application Factory (create_app)
│   ├── models.py            # User, Item, StockTransaction SQLAlchemy models
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Registration, Login, Logout
│   │   ├── dashboard.py     # Home landing page & Dashboard
│   │   ├── inventory.py     # Add, Edit, Delete, Adjust Qty, Item Detail, Stock History
│   │   ├── analytics.py     # Analytics & Chart metrics
│   │   └── profile.py       # Profile & Password change
│   │
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── auth_forms.py    # RegistrationForm, LoginForm
│   │   ├── item_forms.py    # ItemForm
│   │   └── profile_forms.py # ChangePasswordForm
│   │
│   ├── templates/
│   │   ├── base.html        # Main Jinja2 layout template
│   │   ├── home.html        # Public landing page
│   │   ├── auth/            # login.html, register.html
│   │   ├── dashboard/       # index.html
│   │   ├── inventory/       # add_item.html, edit_item.html, item_detail.html, stock_history.html
│   │   ├── analytics/       # analytics.html
│   │   ├── profile/         # profile.html
│   │   └── errors/          # 404.html, 403.html, 500.html
│   │
│   └── static/
│       ├── css/style.css    # Custom CSS styles
│       └── js/main.js       # Client scripts
│
├── migrations/              # Database migration scripts
├── config.py                # Configuration module
├── run.py                   # Main application runner
├── init_db.py               # Database initialization & seeding script
├── requirements.txt         # Project dependencies
├── .env                     # Local environment variables
└── README.md                # Documentation
```

---

## 🚀 Installation & Setup

### 1. Clone or Open Project
Navigate to the project root directory in your terminal:
```bash
cd "c:\Users\PAWAN\Desktop\Pep project"
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Ensure a `.env` file exists in the root directory:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-inventory-mgmt-system-2026-super-secure
DATABASE_URL=sqlite:///inventory.db
```

### 5. Initialize Database & Run Migrations
Run the database setup script to create tables and optionally seed demo sample data:
```bash
python init_db.py
```
*(Demo Account created: Email: `demo@example.com` | Password: `password123`)*

Or manage via **Flask-Migrate**:
```bash
flask db upgrade
```

---

## 💻 Running the Application

Start the local Flask development server:
```bash
python run.py
```
or:
```bash
flask run
```

Open your browser and navigate to:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 🗺️ Main Application Routes

| Endpoint | Method | Authentication | Description |
| :--- | :--- | :--- | :--- |
| `/` | GET | Public | Landing / Home page with feature breakdown & CTA |
| `/register` | GET, POST | Public | User registration form |
| `/login` | GET, POST | Public | User login form |
| `/logout` | GET | Required | Logs out current user session |
| `/dashboard` | GET | Required | Main inventory table, search, filters, and summary stats |
| `/items/add` | GET, POST | Required | Add a new inventory product |
| `/items/<id>` | GET | Required | Detailed product view |
| `/items/<id>/edit` | GET, POST | Required | Edit existing product details & log quantity diffs |
| `/items/<id>/delete` | POST | Required | Delete product and associated history |
| `/items/<id>/adjust-quantity`| POST | Required | Standard form POST to increase (+1) or decrease (-1) quantity |
| `/items/<id>/history` | GET | Required | Stock transaction audit log |
| `/analytics` | GET | Required | Visual Chart.js charts & category valuation metrics |
| `/profile` | GET, POST | Required | User profile & password update form |

---

## 🗄️ Future PostgreSQL Migration Notes

When transitioning from local SQLite to PostgreSQL in production:
1. Install PostgreSQL driver: `pip install psycopg2-binary`
2. Update `DATABASE_URL` in `.env`:
   ```ini
   DATABASE_URL=postgresql://username:password@localhost:5432/inventory_db
   ```
3. Run migrations to create database tables on PostgreSQL:
   ```bash
   flask db upgrade
   ```
4. The SQLAlchemy models (`User`, `Item`, `StockTransaction`) are already fully compatible with PostgreSQL.
