from fastapi import FastAPI
from app.routes import auth_routes, workflow_routes, execute_routes

app = FastAPI(
    title="Workflow Assessment API",
    description="A FastAPI project for workflow management with authentication and permissions",
    version="1.0.0"
)


app.include_router(auth_routes.router)
app.include_router(workflow_routes.router)
app.include_router(execute_routes.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Workflow Assessment API!",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/api/authenticate",
            "workflows": "/api/workflows",
            "execution": "/api/workflows/{id}/execute",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }
