import uuid
import random
import gevent
from locust import HttpUser, task, between
from faker import Faker
from requests import Response
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

    def get(self, url: str, fields: dict = None, params: dict = None):
        format_dict = self.__dict__.copy()
        if fields:
            format_dict.update(**fields)

        final_url = f"{self.host}/api/{url.format(**format_dict)}"
        response: Response = self.client.get(
            final_url,
            headers=self.get_auth_header(),
            name=url,
        )
        response.raise_for_status()
        return response

    def login(self):
        self.username = random.choice(users)
        users.remove(self.username)
        # self.username = "tejesh.kaliki+test@gmail.com"
        response = self.client.post(
            f"{self.host}/api/login/",
            json={"username": self.username, "password": "password"},
            # json={"username": self.username, "password": "Tejesh@2003"},
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
    wait_time = between(4, 6)

    def initial_tasks(self):
        self.get_user_info()
        gevent.joinall(
            [
                gevent.spawn(self.get_all_boxes),
                gevent.spawn(self.get_organization_users),
                gevent.spawn(self.get_channels),
                gevent.spawn(self.get_or_create_nudges),
                gevent.spawn(self.get_reply_templates),
                gevent.spawn(self.get_plans),
                gevent.spawn(self.get_countries),
                gevent.spawn(self.get_lead_counts),
                gevent.spawn(self.things_to_do_list),
            ]
        )

    def get_user_info(self):
        response = self.get("users/my_info")
        if response.status_code == 200:
            response_json = response.json()
            self.user_id = response_json.get("id")

    def get_organization_users(self):
        self.get("organization/sub_organizations/{sub_org_id}/organization_users")

    def get_channels(self):
        self.get("channels/get_all_global_channels")
        self.get("channels/{sub_org_id}/get_all_pending_channels")
        self.get("channels/{sub_org_id}/get_all_connected_channels")

    def get_or_create_nudges(self):
        self.get("organization/get_or_create_nudges", params={"user_id": self.user_id})

    def get_reply_templates(self):
        self.get("reply_templates/sub_organizations/{sub_org_id}/templates/")

    def get_plans(self):
        self.get("plans/get_plans/{sub_org_id}")

    def get_countries(self):
        self.get("countries/get_countries_list")

    def get_lead_counts(self):
        self.get(
            "leads/get_all_lead_count",
            params={"sub_organization_id": self.sub_org_id},
        )
        self.get(
            "leads/sub_organizations/{sub_org_id}/things_to_do/get_the_count_enquiry_and_task",
            params={"assigned_to": self.user_id},
        )

    def get_all_boxes(self):
        response = self.get("box/get_all_box/{sub_org_id}")
        if response.status_code == 200:
            response_json = response.json()
            results = response_json.get("results", [])
            self.boxes = [Box(**result) for result in results]

    def fetch_stage_leads(self, stage_id):
        self.get(
            "leads/list_lead_in_stage/{stage_id}",
            fields={"stage_id": stage_id},
            params={"page": 1, "filter_by": 1},
        )

    @task(1)
    def things_to_do_list(self):
        self.get(
            "leads/sub_organizations/{sub_org_id}/leads",
            params={"page": 1, "filter_by": 1, "assigned_to": self.user_id},
        )

    @task(2)
    def list_leads_in_stage(self):
        box = random.choice(self.boxes)

        # Spawn greenlets to make requests in parallel
        greenlets = [
            gevent.spawn(self.fetch_stage_leads, stage.id) for stage in box.boxstage_set
        ]
        gevent.joinall(greenlets)

    @task(3)
    def list_lead_in_single_stage(self):
        box = random.choice(self.boxes)
        stage = random.choice(box.boxstage_set)

        self.fetch_stage_leads(stage.id)
