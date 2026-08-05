from fastapi import FastAPI

app = FastAPI(title="Barber Booking System")

@app.get("/")
def read_root():
    return {"message": "Barber Booking System API"}
