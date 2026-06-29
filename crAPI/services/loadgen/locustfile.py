import base64
import json
import time
import random
import string
import uuid
from locust import HttpUser, task, between

MERCHANT_IDS = ["merch_7f2a91", "merch_4b8c12", "merch_0d3e55", "merch_load01"]

class QuickstartUser(HttpUser):
    letters = string.ascii_lowercase
    funds = 1
    password = ""
    name = ""
    email = ""
    number = ""
    token = 0
    post_id = ""
    host = "http://localhost:8888"
    wait_time = between(1, 5)
    merchant_id = ""
    known_transaction_ids = []

    def set_name(self):
        self.name = ''.join(random.choice(self.letters) for i in range(8))
    
    def set_password(self):
        self.password = self.name + "A1!"
    
    def set_number(self):
        for i in range(10):
            self.number += str(random.randint(0, 9))

    def set_email(self):
        self.email = self.name + "@example.com"

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
        #mirror endpoint
        original_payload = {
            "request_id": f"mirror-{int(time.time() * 1000)}",
            "metadata": {
                "source": "locust-loadgen",
                "scenario": "default-user-journey",
            },
            "data": {
                "message": "Mirror endpoint payload",
                "timestamp": int(time.time()),
            },
        }
        encoded_payload = base64.b64encode(json.dumps(original_payload).encode("utf-8")).decode("utf-8")
        payload = {"payload": encoded_payload}
        with self.client.post("/identity/api/mirror", json=payload, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Mirror endpoint failed: response {response.status_code}")
            else:
                try:
                    echoed = response.json()
                    if echoed != payload:
                        print(f"Unexpected mirror response: {response.text}")
                    else:
                        decoded = json.loads(base64.b64decode(echoed["payload"]).decode("utf-8"))
                        if decoded != original_payload:
                            print(f"Decoded mirror payload mismatch: {decoded}")
                except ValueError:
                    print(f"Mirror endpoint returned non-JSON: {response.text}")
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
                    self.token = response.json()["id"]
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
            with self.client.post(f"/workshop/api/shop/orders/return_order?token={self.token}", catch_response = True) as response:
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
        #get specific post
        if self.post_id != "":
            with self.client.get(f"/community/api/v2/community/posts/{self.post_id}",
             catch_response = True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't get post {self.post_id}: response {response.status_code}")
        #getting QR code to return
        with self.client.get(f"/workshop/api/shop/return_qr_code", json={"accept":"*/*"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get QR code: response {response.status_code}")
                
    def _payment_headers(self):
        return {
            "X-Levo-Merchant-ID": self.merchant_id,
            "X-RequestID": str(uuid.uuid4()),
        }

    @task
    def payments_auth_capture_refund(self):
        """AUTH → CAPTURE → REFUND happy path"""
        amount = random.randint(100, 5000)
        headers = self._payment_headers()

        # AUTH
        with self.client.post("/payments/api/payments/auth", json={
            "transaction": {
                "amount": {"value": amount, "currency": "USD"},
                "order": {"line_items": [{"merchant_category_code": "5411"}]},
            },
            "card": {
                "card_number": "4111111111111111",
                "bin": "411111",
                "expiry": "12/27",
                "holder_name": self.name,
                "last4": "1111",
            },
        }, headers=headers, catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"AUTH failed: {r.status_code}")
                return
            auth_txn_id = r.json()["transaction"]["transaction_id"]
            if auth_txn_id:
                self.known_transaction_ids.append(auth_txn_id)

        # CAPTURE
        with self.client.post("/payments/api/payments/capture", json={
            "original_transaction_id": auth_txn_id,
            "capture": {"amount": {"value": amount, "currency": "USD"}},
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"CAPTURE failed: {r.status_code}")
                return
            cap_txn_id = r.json()["transaction"]["transaction_id"]

        # REFUND
        with self.client.post("/payments/api/payments/refund", json={
            "original_transaction_id": cap_txn_id,
            "refund": {"amount": {"value": amount, "currency": "USD"}},
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"REFUND failed: {r.status_code}")

    @task
    def payments_auth_reversal(self):
        """AUTH → REVERSAL"""
        amount = random.randint(100, 3000)
        with self.client.post("/payments/api/payments/auth", json={
            "transaction": {"amount": {"value": amount, "currency": "USD"}},
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"AUTH failed: {r.status_code}")
                return
            auth_id = r.json()["transaction"]["auth_id"]

        with self.client.post(f"/payments/api/payments/reversal/{auth_id}", json={
            "reversal": {"reason": {"code": "CUSTOMER_REQUEST"}},
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"REVERSAL failed: {r.status_code}")

    @task
    def payments_sale(self):
        """Standalone SALE"""
        with self.client.post("/payments/api/payments/sale", json={
            "transaction": {"amount": {"value": random.randint(50, 2000), "currency": "USD"}},
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"SALE failed: {r.status_code}")
            else:
                self.known_transaction_ids.append(r.json()["transaction"]["transaction_id"])

    @task
    def payments_credit(self):
        """Standalone CREDIT (loyalty/goodwill)"""
        with self.client.post("/payments/api/payments/credit", json={
            "credit": {
                "amount": {"value": random.randint(10, 500), "currency": "USD"},
                "funding_source": {"account_id": "LOYALTY-POOL"},
            },
        }, headers=self._payment_headers(), catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"CREDIT failed: {r.status_code}")

    @task
    def payments_list_transactions(self):
        """List own transactions"""
        with self.client.get("/payments/api/payments/transactions",
                             headers=self._payment_headers(),
                             catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"LIST transactions failed: {r.status_code}")

    @task
    def payments_transaction_detail_bola(self):
        """Fetch a transaction by ID — exercises BOLA (no ownership check)"""
        if not self.known_transaction_ids:
            return
        txn_id = random.choice(self.known_transaction_ids)
        with self.client.get(f"/payments/api/payments/transactions/{txn_id}",
                             headers=self._payment_headers(),
                             catch_response=True) as r:
            if r.status_code >= 400:
                r.failure(f"GET transaction failed: {r.status_code}")

    #initializing user (logging in/applying coupon)
    def on_start(self):

        self.client.verify = False
        
        self.merchant_id = random.choice(MERCHANT_IDS)
        self.known_transaction_ids = []

        self.set_name()
        self.set_password()
        self.set_number()
        self.set_email()

        with self.client.post("/identity/api/auth/signup", json={"email":self.email, "password":self.password, "name":self.name, "number":self.number}, catch_response=True) as response:
            if response.status_code >= 400:
                raise Exception("Could not sign up")
        with self.client.post("/identity/api/auth/login", json={"email":self.email, "password":self.password}, catch_response = True) as response:
            if response.status_code >= 400:
                raise Exception(f"Could not log in")
            else:
                login = response.json()
        self.client.headers["Authorization"] = login["type"] + " " + login["token"]
        
        #one-time API calls
        #apply coupon
        with self.client.post("/workshop/api/shop/apply_coupon", json={"amount":75, "coupon_code": "TRAC075"}, catch_response = True) as response:
            if response.status_code >= 400:
                print(f"Couldn't apply coupon: response {response.status_code}")
