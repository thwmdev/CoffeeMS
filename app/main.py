from fastapi import FastAPI

from app.database import engine, Base

from app.routers import auth
from app.routers import food

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(food.router)

@app.get("/")
def root():

    return {
        "message": "CoffeeMS API"
    }