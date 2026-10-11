"""
main.py - The Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.models import User, Product, Order, OrderItem, Delivery
from app.routers import auth, products, orders, admin, logistics, forecasts, mandi
from app.services.auth import hash_password

# Create the FastAPI application
app = FastAPI(
    title="Farmer Marketplace API",
    description="AI-Powered Direct Farmer-to-Consumer Digital Marketplace",
    version="1.0.0",
)

# ----- CORS MIDDLEWARE -----
# Allows localhost as well as ANY Vercel production or preview deployment URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://kisan-mu.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- INCLUDE ROUTERS -----
# Mounted both with and without "/api" so neither the frontend nor external requests hit 404 Not Found
routers = [
    auth.router,
    products.router,
    orders.router,
    admin.router,
    logistics.router,
    forecasts.router,
    mandi.router,
]

for router in routers:
    app.include_router(router)
    # If the router doesn't already have an /api prefix, alias it under /api too
    if not (router.prefix and router.prefix.startswith("/api")):
        app.include_router(router, prefix="/api")


# ----- STARTUP EVENT -----
@app.on_event("startup")
def on_startup():
    """
    Creates tables and seeds demo products if the database is newly initialized.
    """
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create default admin account
        existing_admin = db.query(User).filter(User.email == "admin@marketplace.com").first()
        if not existing_admin:
            admin_user = User(
                email="admin@marketplace.com",
                hashed_password=hash_password("admin123"),
                full_name="Platform Administrator",
                role="admin",
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            print("[OK] Default admin account created: admin@marketplace.com / admin123")

        # Auto-seed demo catalog if empty
        product_count = db.query(Product).count()
        if product_count == 0:
            print("[INFO] Database empty - auto-seeding produce catalog...")
            try:
                from app.seed import seed_database
                seed_database()
            except ImportError:
                print("[WARNING] app.seed module not found, skipping automatic seed.")
    except Exception as e:
        print(f"[STARTUP WARNING] Database startup check: {e}")
    finally:
        db.close()


# ----- ROOT & HEALTH CHECK ENDPOINTS -----
@app.get("/")
def root():
    return {
        "message": "🌾 Farmer Marketplace API is running!",
        "docs": "Visit /docs for interactive API documentation",
        "version": "1.0.0",
    }


@app.get("/api/health")
@app.get("/health")
def health_check():
    return {"status": "healthy"}