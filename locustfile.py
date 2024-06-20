import json
import uuid
import random
import gevent
from locust import HttpUser, task, between, tag
from faker import Faker

from models import Box

fake = Faker()

CONNECTED_CHANNEL = "819cd41f-2847-45d9-b9b9-ea16dfb73e46"
CONNECTED_CHANNEL = "cbcc9b65-814b-4de6-8ada-5a20726e4947"


def load_users():
    users = []
    with open("usernames.txt") as usernames:
        users = list(usernames.read().splitlines())
    return users

users = load_users()

class EnquiryboxUser(HttpUser):
    def on_start(self):
        self.login()
        self.initial_tasks()

    def initial_tasks(self): ...

    def get_auth_header(self):
        return {"Authorization": f"Bearer {self.token}"}

    def login(self):
        self.username = random.choice(users)
        users.remove(self.username)
        response = self.client.post(
            f"{self.host}/api/login/",
            json={"username": self.username, "password": "password"},
        )
        if response.status_code == 200:
            self.token = response.json().get("access")
            self.sub_org_id = response.json().get("sub_org_id")


class LeadGenerationUser(EnquiryboxUser):
    wait_time = between(1, 5)

    dental_messages = [
        "I need a dental cleaning and would like to book an appointment in Mumbai, India.",
        "I have a cavity that needs filling and I need it done as soon as possible in London, United Kingdom.",
        "My gums are bleeding, and I need an appointment to check for gum disease in Cape Town, South Africa.",
        "I need a consultation for braces to correct my teeth alignment in Bangalore, India.",
        "I am experiencing severe tooth pain and need to see a dentist immediately in Manchester, United Kingdom.",
        "I want to whiten my teeth for an upcoming event in Johannesburg, South Africa.",
        "I need to fix a broken tooth that occurred during an accident in Delhi, India.",
        "I am looking for a new dentist in my area who accepts my insurance in Liverpool, United Kingdom.",
        "I have sensitive teeth and need advice on how to manage the sensitivity in Durban, South Africa.",
        "I need a root canal treatment for my infected tooth in Kolkata, India.",
        "Can you recommend a good pediatric dentist for my child in Glasgow, United Kingdom?",
        "I am looking for an emergency dental service in Cape Town, South Africa.",
        "I need a second opinion on a dental procedure recommended by my dentist in Chennai, India.",
        "I have a dental implant that needs to be checked in Birmingham, United Kingdom.",
        "I want to schedule a routine dental check-up for my family in Pretoria, South Africa.",
        "I am interested in getting veneers for my teeth in Hyderabad, India.",
        "My dental crown is loose and I need it fixed in Edinburgh, United Kingdom.",
        "I need a dentist who specializes in treating TMJ disorders in Durban, South Africa.",
        "I am looking for a clinic that offers laser dentistry in Pune, India.",
        "I need advice on the best dental hygiene practices in Leeds, United Kingdom.",
    ]

    form_ids = [
        "ecc48495-4fc6-4fd6-a855-02b8f57ca8b8",
    ]

    @task
    def create_lead(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "connected_channel_id": CONNECTED_CHANNEL,
            # "eb_form_id": random.choice(self.form_ids),
            "eb_form_id": str(uuid.uuid4()),
            "data": {
                "entryPoint": "localhost:9000/api",
                "title": "three piece",
                "formName": "new webform",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone_number": "6309091410",
                "email": "payaltesting03@gmail.com",
                "url": fake.url(),
                "message": random.choice(self.dental_messages),
            },
        }
        try:
            self.client.post(
                f"{self.host}/api/webforms/webform_webhook",
                json=payload,
                headers=headers,
            )
        except Exception as ex:
            print("Exception:", ex)


class LeadListViewUser(EnquiryboxUser):
    wait_time = between(1, 3)

    def initial_tasks(self):
        self.get_user_info()

    def get_user_info(self):
        response = self.client.get(
            f"{self.host}/api/users/my_info",
            headers=self.get_auth_header(),
        )
        if response.status_code == 200:
            response_json = response.json()
            self.user_id = response_json.get("id")

    @task(1)
    def things_to_do_list(self):
        with self.client.rename_request("/api/leads/sub_organizations/:sub_org_id/leads"):
            self.client.get(
                f"{self.host}/api/leads/sub_organizations/{self.sub_org_id}/leads",
                headers=self.get_auth_header(),
                params={
                    "page": 1,
                    "filter_by": 1,
                    "assigned_to": self.user_id,
                },
            )

    def get_all_boxes(self):
        with self.client.rename_request("/api/box/get_all_box/:sub_org_id"):
            response = self.client.get(
                f"{self.host}/api/box/get_all_box/{self.sub_org_id}",
                headers=self.get_auth_header(),
            )
        if response.status_code == 200:
            response_json = response.json()
            results = response_json.get("results", [])
            self.boxes = [Box(**result) for result in results]

    def fetch_stage_leads(self, stage_id):
        with self.client.rename_request("/api/leads/list_lead_in_stage/:stage_id"):
            self.client.get(
                f"{self.host}/api/leads/list_lead_in_stage/{stage_id}",
                headers=self.get_auth_header(),
                params={
                    "page": 1,
                    "filter_by": 1,
                }
            )

    @task(2)
    def list_leads_in_stage(self):
        if not hasattr(self, "boxes"):
            self.get_all_boxes()

        box = random.choice(self.boxes)

        # Spawn greenlets to make requests in parallel
        greenlets = [
            gevent.spawn(self.fetch_stage_leads, stage.id)
            for stage in box.boxstage_set
        ]
        gevent.joinall(greenlets)
    
    @task(3)
    def list_lead_in_single_stage(self):
        if not hasattr(self, "boxes"):
            self.get_all_boxes()
        
        box = random.choice(self.boxes)
        stage = random.choice(box.boxstage_set)

        self.fetch_stage_leads(stage.id)
