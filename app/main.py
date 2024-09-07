from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import shipment


description = """
# Senvo API

### Overview
The **Senvo API** is the backend service for managing shipments within the Senvo project. This API adheres to REST principles, offering a reliable and predictable interface for interacting with shipment data.

### Key Features
- **RESTful Structure**: The API follows a resource-oriented approach, ensuring a consistent and intuitive experience.
- **Standardized Responses**: Requests and responses follow standard HTTP protocols, with responses encoded in JSON format.
- **Error Handling**: API errors are communicated using conventional HTTP response codes for improved reliability.

### Core Functionalities
The Senvo API provides the following key operations:

- **Create Shipments**: Add new shipment entries to the database.
- **Retrieve Shipments**: Fetch a list of shipment records from the database.

### Getting Started
The API is designed to accept form-encoded request bodies, making it easy to interact with using common HTTP methods.
"""

app = FastAPI(
    title="Senvo API",
    description=description,
    version="0.1",
    contact={"author": "Artiom Gaidei", "email": "gaideiartiom@gmail.com"},
)
app.include_router(shipment.router)

Instrumentator().instrument(app).expose(app)


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")
