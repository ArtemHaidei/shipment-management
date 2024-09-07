import json
from locust import HttpUser, task, between


def get_shipments():
    with open("data/shipments.json") as file:
        return json.load(file)


shipments: dict = get_shipments()


class WebsiteSenvo(HttpUser):
    wait_time = between(1, 2)

    @task(2)
    def get_items(self):
        self.client.get("/shipment/")

    @task(1)
    def create_items(self):
        self.client.post("/shipment/", json=shipments)
