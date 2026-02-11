from fastapi import FastAPI

from app.routers import auth, categories, products, users

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
