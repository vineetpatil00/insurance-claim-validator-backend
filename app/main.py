import os
from dotenv import load_dotenv
from fastapi import FastAPI
from app.helpers.Database import MongoDB
from app.config.CustomSwagger import generate_swagger
from app.middleware.Cors import add_cors_middleware
from app.middleware.GlobalErrorHandling import GlobalErrorHandlingMiddleware
from app.controllers import Claim

load_dotenv()

app = FastAPI(
    title="Insurance Claim Validator API",
    description="AI-powered insurance claim validation system that automatically validates car insurance claims by extracting data from documents, validating consistency, and analyzing damage images.",
    version=os.getenv('VERSION', '1.0.0'),
    docs_url="/swagger",
    redoc_url="/api-redoc"
)
app.openapi = generate_swagger(app)

# Middleware
app.add_middleware(GlobalErrorHandlingMiddleware)
add_cors_middleware(app)

# Routes
app.include_router(Claim.router)

@app.on_event("startup")
async def startup_event():
    connection_string = os.getenv("ATLAS_URL")
    db_name = os.getenv("DB_NAME", "dev")
    if connection_string:
        await MongoDB.connect(connection_string, db_name)
        status = await MongoDB.connection_status()
        print(f"MongoDB Connection: {status}")
    else:
        print("Warning: ATLAS_URL not set. Database connection skipped.")

@app.on_event("shutdown")
async def shutdown_event():
    await MongoDB.disconnect()

@app.get("/")
def read_root():
    version = os.getenv('VERSION', '1.0.0')
    build = os.getenv('BUILD', 'dev')
    return {
        "message": "Welcome to Insurance Claim Validator API",
        "version": version,
        "build": build,
        "description": "AI-powered insurance claim validation system"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = await MongoDB.connection_status()
    return {
        "status": "healthy" if status["status"] == "connected" else "unhealthy",
        "database": status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=4111, reload=True)
