from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import shipment


description = """
# Senvo API

#### This is the API for the Senvo project. It allows you to manage shipments.

The API is organized around REST. 
It has predictable resource-oriented URLs, accepts form-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes.
The API is designed to have predictable, resource-oriented URLs and to use HTTP response codes to indicate API errors.

#### You will be able to:

* **Create a shipments**: Create a new shipments in the database.
* **Retrieve shipments**: Retrieve a list of shipments from the database.
"""

app = FastAPI(
    title="Senvo API",
    description=description,
    version="0.1",
    contact={"author": "Artiom Gaidei", "email": "gaideiartiom@gmail.com"},
)
app.include_router(shipment.router)


# redirect from main to /docs
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")
