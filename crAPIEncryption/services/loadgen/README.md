# Load Generator for crAPIEncryption

This ['Locust'](https://locust.io/) based load generator will exercise various APIs of crAPIEncryption with encryption/decryption support.

## Prerequisites

1. A working installation of ['Locust'](https://locust.io/)
2. Python dependencies: `pip install -r requirements.txt`

## Features

- **AES Encryption/Decryption**: All requests are encrypted and wrapped in `{"enc_data": "..."}` format
- **Response Decryption**: All responses are automatically decrypted from `{"enc_data": "..."}` format
- **Comprehensive API Coverage**: Tests all Identity service APIs including:
  - Authentication (signup, login, forget password, OTP)
  - User management (dashboard, reset password)
  - Vehicle management (add vehicle, get vehicles, get location)
  - Profile management (videos, pictures)
  - Email management (change email, verify email)
  - Privacy endpoints
  - Admin endpoints

## Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Execute this command in terminal/console:
```bash
locust -f locustfile.py
```

3. Go to http://0.0.0.0:8089/ on your browser to access Locust's UI. If the locustfile is running, Locust will ask you for the number of users, spawn rate, and the host. By default, the host is set to `http://localhost:8888`. If crAPIEncryption is running somewhere else, point Locust to the correct host.

> You may set the number of users and spawn rate to whatever values you wish, but be aware that too many requests may raise a 429 error.

## Encryption Details

The load generator uses AES-128 encryption with ECB mode and PKCS5 padding, matching the Java implementation:
- **Algorithm**: AES/ECB/PKCS5Padding
- **Key**: "MySecretKey12345" (16 bytes)
- **Request Format**: `{"enc_data": "<base64_encrypted_json>"}`
- **Response Format**: `{"enc_data": "<base64_encrypted_json>"}`

## API Endpoints Tested

### Authentication APIs
- `POST /identity/api/auth/signup` - User registration
- `POST /identity/api/auth/login` - User login
- `POST /identity/api/auth/forget-password` - Request password reset
- `POST /identity/api/auth/v2/check-otp` - Validate OTP
- `POST /identity/api/auth/v3/check-otp` - Secure OTP validation

### User APIs
- `GET /identity/api/v2/user/dashboard` - Get user dashboard
- `POST /identity/api/v2/user/reset-password` - Reset password

### Vehicle APIs
- `POST /identity/api/v2/vehicle/add_vehicle` - Add vehicle
- `GET /identity/api/v2/vehicle/vehicles` - Get all vehicles
- `GET /identity/api/v2/vehicle/{carId}/location` - Get vehicle location
- `POST /identity/api/v2/vehicle/resend_email` - Resend vehicle email

### Profile APIs
- `GET /identity/api/v2/user/videos/{video_id}` - Get profile video
- `POST /identity/api/v2/user/pictures` - Upload profile picture
- `POST /identity/api/v2/user/videos` - Upload profile video
- `PUT /identity/api/v2/user/videos/{video_id}` - Update profile video
- `DELETE /identity/api/v2/user/videos/{video_id}` - Delete profile video
- `GET /identity/api/v2/user/videos/list_sample_videos` - List sample videos

### Email APIs
- `POST /identity/api/v2/user/change-email` - Request email change
- `POST /identity/api/v2/user/verify-email-token` - Verify email token

### Other APIs
- `POST /identity/api/mirror` - Echo/mirror endpoint
- `GET /identity/privacy/user_agent` - Get user agent
