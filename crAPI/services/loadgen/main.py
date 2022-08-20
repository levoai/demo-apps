import time
import random
import string
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    letters = string.ascii_lowercase
    funds = 1
    password = "Victim1One"
    name = "Victim One"
    email = "victim.one@example.com"
    number = "4156895423"
    order_id = 0
    post_id = ""
    host = "http://localhost:8888"
    wait_time = between(1, 5)

    # defunct
    # def set_name(self):
    #     self.name = ''.join(random.choice(self.letters) for i in range(8))
    
    # def set_password(self):
    #     self.password = self.name + "A1!"
    
    # def set_number(self):
    #     for i in range(10):
    #         self.number += str(random.randint(0, 9))

    # def set_email(self):
    #     self.email = self.name + "@example.com"

    '''
    Main action for each user. Stresses endpoints that 
    an average user might exercise.
    '''
    @task
    def start_user_action(self):
        #homepage
        with self.client.get("/", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get homepage: response {response.status_code}")
        #dashboard
        with self.client.get("/identity/api/v2/user/dashboard", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get dashboard: response {response.status_code}")
        #get vehicle
        with self.client.get("/identity/api/v2/vehicle/vehicles", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get vehicle: response {response.status_code}")
        #get mechanics
        with self.client.get("/workshop/api/mechanic", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get all mechanics: response {response.status_code}")
        #post mechanic request
        with self.client.post("/workshop/api/merchant/contact_mechanic", json={"mechanic_api": "http://localhost:8888/workshop/api/mechanic/receive_report",
            "mechanic_code": "TRAC_MECH1",
            "number_of_repeats": 0,
            "repeat_request_if_failed": False,
            "problem_details": "My car has engine trouble, and I need urgent help!",
            "vin": "0BZCX25UTBJ987271"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't contact mechanic: response {response.status_code}")
        #get mechanic reports
        with self.client.get("/workshop/api/mechanic/user_reports", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get all service reports: response {response.status_code}")
        #get products
        self.client.get("/workshop/api/shop/products", catch_response = True)
        if self.funds:
            #create order (if enough funds)
            with self.client.post("/workshop/api/shop/orders", json={"product_id": random.randint(1, 2), "quantity": 1}, catch_response = True) as response:
                if response.status_code > 400:
                    print(f"Couldn't create order: response {response.status_code}")
                elif response.status_code == 400:
                    self.funds = -1
                    print("Insufficient funds")
                else:
                    self.order_id = response.json()["id"]
        #validate coupon
        with self.client.post("/community/api/v2/coupon/validate-coupon", json={"coupon_code": "TRAC075"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't validate coupon: response {response.status_code}")
        #get past orders
        with self.client.get("/workshop/api/shop/orders/all", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get all orders: response {response.status_code}")
        if self.funds:
            #return order (if one exists)
            with self.client.post(f"/workshop/api/shop/orders/return_order?order_id={self.order_id}", catch_response = True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't return order: response {response.status_code}")
            if self.funds == -1:
                self.funds = 0
        #get posts on community
        with self.client.get(f"/community/api/v2/community/posts/recent", catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get posts: response {response.status_code}")
        #return order
        with self.client.post("/community/api/v2/community/posts",
        json={"content":"I especially love the community feature. It makes getting all my passwords stolen more engaging!",
         "title":"This API is great!"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't create post: response {response.status_code}")
            else:
                self.post_id = response.json()["id"]
        #comment on post (if it exists)
        if self.post_id != "":
            with self.client.post(f"/community/api/v2/community/posts/{self.post_id}/comment",
            json={"content":"I know, right? I love identity fraud!"}, catch_response = True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't create post: response {response.status_code}")
        #create new mechanic
        with self.client.post("/workshop/api/mechanic/signup", 
        json={"name":f"{''.join(random.choice(self.letters) for i in range(8))}",
        "email":f"{''.join(random.choice(self.letters) for i in range(8))}@example.com",
        "number":random.randint(1, 1000000),
        "password":f"{''.join(random.choice(self.letters) for i in range(8))}A1!",
        "mechanic_code":''.join(random.choice(self.letters) for i in range(8))},
         catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't add mechanic: response {response.status_code}")
        #get specific post
        if self.post_id != "":
            with self.client.get(f"/community/api/v2/community/posts/{self.post_id}",
             catch_response = True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't get post {self.post_id}: response {response.status_code}")
                
    #initializing user (logging in/applying coupon)
    def on_start(self):
        with self.client.post("/identity/api/auth/login", json={"email":self.email, "password":self.password}, catch_response = True) as response:
            if response.status_code >= 400:
                print(response.json())
                raise Exception(f"Could not log in")
            else:
                login = response.json()
        self.client.headers["Authorization"] = login["type"] + " " + login["token"]
        #apply coupon
        with self.client.post("/workshop/api/shop/apply_coupon", json={"amount":75, "coupon_code": "TRAC075"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't validate coupon: response {response.status_code}")
