from fastapi import FastAPI

app = FastAPI(title="Workspace Reservation API")


@app.get("/health")
def health():
    return {"status": "ok"}