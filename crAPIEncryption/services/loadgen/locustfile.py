import base64
import json
import time
import random
import string
from locust import HttpUser, task, between
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class EncryptionUser(HttpUser):
    letters = string.ascii_lowercase
    password = ""
    name = ""
    email = ""
    number = ""
    token = ""
    jwt_token = ""
    car_id = ""
    video_id = ""
    wait_time = between(1, 5)
    host = "http://localhost:8888"
    
    # AES encryption key matching Java implementation
    SECRET_KEY = b"MySecretKey12345"  # 16 bytes for AES-128
    
    def set_name(self):
        self.name = ''.join(random.choice(self.letters) for i in range(8))
    
    def set_password(self):
        self.password = self.name + "A1!"
    
    def set_number(self):
        self.number = ''.join([str(random.randint(0, 9)) for _ in range(10)])

    def set_email(self):
        self.email = self.name + "@example.com"
    
    def encrypt_data(self, plaintext):
        """Encrypt data using AES/ECB/PKCS5Padding matching Java implementation"""
        try:
            cipher = AES.new(self.SECRET_KEY, AES.MODE_ECB)
            # Pad the plaintext to be a multiple of 16 bytes (AES block size)
            padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            # Return base64 encoded string
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            raise
    
    def decrypt_data(self, encrypted_text):
        """Decrypt data using AES/ECB/PKCS5Padding matching Java implementation"""
        try:
            cipher = AES.new(self.SECRET_KEY, AES.MODE_ECB)
            encrypted_bytes = base64.b64decode(encrypted_text)
            decrypted = cipher.decrypt(encrypted_bytes)
            # Unpad the decrypted data
            unpadded = unpad(decrypted, AES.block_size)
            return unpadded.decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            raise
    
    def encrypt_and_wrap(self, data):
        """Encrypt data and wrap in enc_data format"""
        if isinstance(data, dict):
            json_str = json.dumps(data)
        else:
            json_str = data
        encrypted = self.encrypt_data(json_str)
        return {"enc_data": encrypted}
    
    def decrypt_response(self, response):
        """Decrypt response that has enc_data field"""
        try:
            response_json = response.json()
            if "enc_data" in response_json:
                decrypted = self.decrypt_data(response_json["enc_data"])
                return json.loads(decrypted)
            return response_json
        except Exception as e:
            print(f"Response decryption error: {e}")
            return response.json()

    '''
    Main action for each user. Stresses endpoints that 
    an average user might exercise.
    '''
    @task
    def start_user_action(self):
        # Dashboard - GET
        with self.client.get("/identity/api/v2/user/dashboard", 
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get dashboard: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Dashboard data: {decrypted}")
                except Exception as e:
                    print(f"Dashboard decryption failed: {e}")
        
        # Get vehicles - GET
        with self.client.get("/identity/api/v2/vehicle/vehicles",
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get vehicles: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    if decrypted and isinstance(decrypted, list) and len(decrypted) > 0:
                        self.car_id = decrypted[0].get("id", "")
                except Exception as e:
                    print(f"Vehicles decryption failed: {e}")
        
        # Get vehicle location - GET
        if self.car_id:
            with self.client.get(f"/identity/api/v2/vehicle/{self.car_id}/location",
                                headers={"Authorization": f"Bearer {self.jwt_token}"},
                                catch_response=True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't get vehicle location: response {response.status_code}")
                else:
                    try:
                        decrypted = self.decrypt_response(response)
                    except Exception as e:
                        print(f"Vehicle location decryption failed: {e}")
        
        # Mirror endpoint - POST
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
        encrypted_payload = self.encrypt_and_wrap(original_payload)
        with self.client.post("/identity/api/mirror",
                            json=encrypted_payload,
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Mirror endpoint failed: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Mirror response: {decrypted}")
                except Exception as e:
                    print(f"Mirror decryption failed: {e}")
        
        # Get profile video - GET
        if self.video_id:
            with self.client.get(f"/identity/api/v2/user/videos/{self.video_id}",
                                headers={"Authorization": f"Bearer {self.jwt_token}"},
                                catch_response=True) as response:
                if response.status_code >= 400:
                    print(f"Couldn't get profile video: response {response.status_code}")
                else:
                    try:
                        decrypted = self.decrypt_response(response)
                    except Exception as e:
                        print(f"Profile video decryption failed: {e}")
        
        # List sample videos - GET
        with self.client.get("/identity/api/v2/user/videos/list_sample_videos",
                            params={"number": "5"},
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get sample videos: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                except Exception as e:
                    print(f"Sample videos decryption failed: {e}")
        
        # Reset password - POST
        reset_password_data = {
            "email": self.email,
            "password": self.password + "New"
        }
        encrypted_reset = self.encrypt_and_wrap(reset_password_data)
        with self.client.post("/identity/api/v2/user/reset-password",
                            json=encrypted_reset,
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't reset password: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                except Exception as e:
                    print(f"Reset password decryption failed: {e}")
        
        # Resend vehicle email - POST
        with self.client.post("/identity/api/v2/vehicle/resend_email",
                            json={"enc_data": ""},  # Empty body, just needs auth
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't resend vehicle email: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                except Exception as e:
                    print(f"Resend email decryption failed: {e}")

    # Initializing user (signup and login)
    def on_start(self):
        self.client.verify = False
        
        self.set_name()
        self.set_password()
        self.set_number()
        self.set_email()

        # Signup - POST
        signup_data = {
            "email": self.email,
            "password": self.password,
            "name": self.name,
            "number": self.number
        }
        encrypted_signup = self.encrypt_and_wrap(signup_data)
        with self.client.post("/identity/api/auth/signup",
                            json=encrypted_signup,
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Signup failed: {response.status_code}, {response.text}")
                raise Exception("Could not sign up")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Signup successful: {decrypted}")
                except Exception as e:
                    print(f"Signup response decryption failed: {e}")
        
        # Login - POST
        login_data = {
            "email": self.email,
            "password": self.password
        }
        encrypted_login = self.encrypt_and_wrap(login_data)
        with self.client.post("/identity/api/auth/login",
                            json=encrypted_login,
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Login failed: {response.status_code}, {response.text}")
                raise Exception("Could not log in")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    if decrypted and "token" in decrypted:
                        self.jwt_token = decrypted["token"]
                        self.client.headers["Authorization"] = f"Bearer {self.jwt_token}"
                        print(f"Login successful, token: {self.jwt_token[:20]}...")
                    else:
                        raise Exception("No token in login response")
                except Exception as e:
                    print(f"Login response decryption failed: {e}")
                    raise
        
        # Add vehicle - POST
        vehicle_data = {
            "pincode": str(random.randint(100000, 999999)),
            "vin": ''.join([random.choice(string.ascii_uppercase + string.digits) for _ in range(17)])
        }
        encrypted_vehicle = self.encrypt_and_wrap(vehicle_data)
        with self.client.post("/identity/api/v2/vehicle/add_vehicle",
                            json=encrypted_vehicle,
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't add vehicle: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Vehicle added: {decrypted}")
                except Exception as e:
                    print(f"Add vehicle decryption failed: {e}")
        
        # Change email request - POST
        change_email_data = {
            "old_email": self.email,
            "new_email": self.name + "new@example.com"
        }
        encrypted_change_email = self.encrypt_and_wrap(change_email_data)
        with self.client.post("/identity/api/v2/user/change-email",
                            json=encrypted_change_email,
                            headers={"Authorization": f"Bearer {self.jwt_token}"},
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't change email: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Change email response: {decrypted}")
                except Exception as e:
                    print(f"Change email decryption failed: {e}")
        
        # Forget password - POST
        forget_password_data = {
            "email": self.email
        }
        encrypted_forget = self.encrypt_and_wrap(forget_password_data)
        with self.client.post("/identity/api/auth/forget-password",
                            json=encrypted_forget,
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't request password reset: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"Forget password response: {decrypted}")
                except Exception as e:
                    print(f"Forget password decryption failed: {e}")
        
        # Privacy - Get user agent - GET
        with self.client.get("/identity/privacy/user_agent",
                            catch_response=True) as response:
            if response.status_code >= 400:
                print(f"Couldn't get user agent: response {response.status_code}")
            else:
                try:
                    decrypted = self.decrypt_response(response)
                    print(f"User agent: {decrypted}")
                except Exception as e:
                    print(f"User agent decryption failed: {e}")
