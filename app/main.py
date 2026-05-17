from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, transactions, savings, credit, admin, qr

app = FastAPI(
    title="La Billetera API",
    description="API financiera con microahorros, historial crediticio y panel admin",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(savings.router)
app.include_router(credit.router)
app.include_router(admin.router)
app.include_router(qr.router)


@app.get("/")
def root():
    return {"message": "La Billetera API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
