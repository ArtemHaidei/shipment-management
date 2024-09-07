# Senvo API
___
### Overview
The **Senvo API** is the backend service for managing shipments within the Senvo project. 
This API adheres to REST principles, offering a reliable and predictable interface for interacting with shipment data.

### Key Features
- **RESTful Structure**: The API follows a resource-oriented approach, ensuring a consistent and intuitive experience.
- **Standardized Responses**: Requests and responses follow standard HTTP protocols, with responses encoded in JSON format.
- **Error Handling**: API errors are communicated using conventional HTTP response codes for improved reliability.

### Core Functionalities
The Senvo API provides the following key operations:

- **Create Shipments**: Add new shipments entries to the database.
- **Retrieve Shipments**: Fetch a list of shipment records from the database.

### Performance Testing

- **Using locust for performance testing**

### Getting Started
The API is designed to accept form-encoded request bodies, making it easy to interact with using common HTTP methods.
___
# Installation
### For Unix-based systems
* There setup **Mackefile** to install the dependencies and run the server.
* You need to have global Python 3.10 or higher installed on your system.

___

For creating env/ directory:
```bash 
make env
```

Next:
```bash
make install
```
**make install** comand will:
- Install dependencies from requirements.txt
- Create docker container with **POSTGRESQL**
- Create database
- Make migrations
- Create Countreis, States and Cities
- Create Careers
- Run server

---
Other way:
1. Create virtualenv
2. Install dependencies from *requirements.txt*
```zsh
pip install -r requirements.txt
```
3. Create **POSTGRESQL** container
```zsh
docker build -t senvo-dev-db .
```
4. Run container
```zsh
run -d -p 5434:5432 --name senvo-dev-db -v senvo-dev-db-volume:/var/lib/postgresql/data senvo-dev-db
```
5. Create database
```zsh
chmod +x create_db.sh
	./create_db.sh
```
6. Make migrations
```zsh
cd app
alembic upgrade head
```

7. Create Countreis, States and Cities
```zsh
python scripts/countries.py
```
8. Create Careers
```zsh
python scripts/carriers.py
```
9. Run server
```zsh
fastapi run app/main.py
```
___

# Locust
### Run Locust
From the root directory:
```zsh
locust -f performance.py
```

- Open your browser and go to http://localhost:8089/
- Enter the number of users to simulate and the hatch rate, then click "Start swarming".
- For dev HOST enter http://localhost:8000 (or your server address)
- For prod HOST enter https://0.0.0.0:8000 (or your server address)