HOST=$(shell hostname)

path:
	@echo "Export PYTHONPATH"

	export PYTHONPATH=PWD

install:
	@echo "Creating virtual environment"
	python3 -m venv env
	@echo "Installing python dependencies"
	. env/bin/activate && python  -m pip install --upgrade pip
	. env/bin/activate && pip install -r requirements.txt
	make docker-db
	make migration+
	make dummy-data

# ---------------------- Bash ----------------------
db:
	@echo "Creating database"
	chmod +x create_db.sh
	./create_db.sh

# ---------------------- Docker commands ----------------------
build:
	docker build -t senvo-dev-db .

run:
	docker run -d -p 5434:5432 --name senvo-dev-db -v senvo-dev-db-volume:/var/lib/postgresql/data senvo-dev-db

docker-db:
	@echo "Create and run the database container"
	make build
	make run
	@echo "Waiting for the database container to start"
	sleep 5
	make db

# ---------------------- Migrations ----------------------
migration+:
	@echo "Create and Upgrading database with message: $(m)"
	make migration m="init db"
	make migrate

migration:
	@echo "Create migrations with message: $(m)"
	. env/bin/activate && cd app && alembic revision --autogenerate -m "${m}"

migrate:
	@echo "Upgrading database"
	. env/bin/activate && cd app && alembic upgrade head

# ---------------------- Server ----------------------
dev:
	@echo "Running uvicorn server"
	. env/bin/activate && fastapi dev app/main.py

prod:
	@echo "Running uvicorn server"
	. env/bin/activate && fastapi run app/main.py

# ---------------------- Scripts ----------------------
countries:
	@echo "Running script to create countries"
	. env/bin/activate && python scripts/countries.py

shipments:
	@echo "Running script to create shipments"
	. env/bin/activate && python scripts/carriers.py

dummy-data:
	@echo "Running script to create dummy data"
	make shipments
	make countries
