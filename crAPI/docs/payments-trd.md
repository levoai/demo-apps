# crAPI Payments Simulation Service — Technical Requirements Document

**Document:** TRD-PAYMENTS-001  
**Version:** 1.0  
**Status:** Draft  
**Service:** `crapi-payments`  
**Port:** 8001  
**Image:** `levoai/crapi-payments:latest`

---

## Table of Contents

1. [Architecture Decision Records](#1-architecture-decision-records)
2. [Service Profile](#2-service-profile)
3. [Network Topology](#3-network-topology)
4. [Source File Tree](#4-source-file-tree)
5. [Django Project Files](#5-django-project-files)
6. [Middleware](#6-middleware)
7. [Models](#7-models)
8. [Views](#8-views)
9. [Dockerfile, Runner & Build](#9-dockerfile-runner--build)
10. [Environment Variables](#10-environment-variables)
11. [Database Schema & Migration](#11-database-schema--migration)
12. [Docker Compose Changes](#12-docker-compose-changes)
13. [Nginx Changes](#13-nginx-changes)
14. [Kubernetes Manifests](#14-kubernetes-manifests)
15. [Build & Publish Procedure](#15-build--publish-procedure)
16. [Transaction State Machine](#16-transaction-state-machine)
17. [Verification Checklist](#17-verification-checklist)

---

## 1. Architecture Decision Records

### ADR-001 — Standalone microservice, not embedded in Workshop

**Status:** Accepted

| | |
|---|---|
| **Context** | Workshop runs Django 2.2 with a fixed set of migrations under the `crapi` app label. Embedding payments there couples release cycles and risks migration conflicts. |
| **Decision** | New standalone Docker image `levoai/crapi-payments`, its own Django project, own port (8001), own K8s Deployment and Service. Follows the established crAPI pattern where every service is its own image. |
| **Consequence** | Requires a new `/payments/` nginx location block and a rebuild of `levoai/crapi-web`. Existing services are not modified beyond Docker Compose and K8s config additions. |

> **Note on PRD §02:** The Goals section says "live inside the Workshop service" — that is stale. §08 of the PRD correctly describes standalone. This TRD reflects the standalone decision.

---

### ADR-002 — Django 3.2 LTS on Python 3.8-alpine

**Status:** Accepted

| | |
|---|---|
| **Context** | Workshop pins Django 2.2 (EOL). A new service has no reason to inherit that constraint. |
| **Decision** | Django 3.2 LTS — last LTS before 4.x, stable, well-understood. Python 3.8-alpine3.15 matches the Workshop base image so the CI build cache is shared. `JSONField` (available since 3.1) lets views store raw request payloads without a separate Mongo dependency. |
| **Consequence** | PyJWT must be ≥ 2.4 (Django 3.2 compatible). Workshop's PyJWT 1.7.1 is not reused. |

---

### ADR-003 — No JWT authentication on payment endpoints

**Status:** Accepted

| | |
|---|---|
| **Context** | Payment gateways authenticate via their own credential scheme (API keys / merchant headers), not user session JWTs. Requiring a JWT would force Levo's load generator to maintain a login session before every payment call. |
| **Decision** | Access control is enforced entirely through the custom header set: merchant allowlist (`x-levo-merchant-id`), request ID uniqueness, timestamp replay protection, and idempotency — all validated in middleware. No Bearer token required by default. |
| **Escape hatch** | Set `PAYMENTS_REQUIRE_JWT=true` to enable JWT validation using the shared `JWT_SECRET`. Default: disabled. |

---

### ADR-004 — Django LocMemCache — no Redis dependency

**Status:** Accepted

| | |
|---|---|
| **Context** | `X-RequestID` uniqueness (10-min TTL) and idempotency keys (5-min TTL) require a fast cache. The crAPI stack has no Redis. |
| **Decision** | Use Django's built-in `LocMemCache`. With `runserver` (single process), LocMemCache is process-safe and zero-dependency. Acceptable for a test target. |
| **Limitation** | Cache does not survive a container restart. For load testing across restarts, set `PAYMENTS_CACHE_BACKEND=django.core.cache.backends.db.DatabaseCache` and run `createcachetable`. |

---

### ADR-005 — Django development server (runserver)

**Status:** Accepted

| | |
|---|---|
| **Decision** | Use `manage.py runserver` for parity with the Workshop service. crAPI is a demo target. Gunicorn adds worker concurrency that would invalidate LocMemCache cross-process and complicate the dev setup. |

---

## 2. Service Profile

| Property | Value | Notes |
|---|---|---|
| Service name | `crapi-payments` | Docker Compose key, K8s Deployment name |
| Docker image | `levoai/crapi-payments:latest` | Built from `services/payments/` |
| Port | 8001 | Internal; exposed via nginx at `:8888/payments/` |
| Runtime | Python 3.8-alpine3.15 | Matches Workshop base image |
| Framework | Django 3.2 LTS + DRF 3.14 | |
| Database | PostgreSQL 14 (shared) | Same `postgresdb` container, db=crapi, user=admin |
| Cache | LocMemCache (default) | See ADR-004 |
| App label | `payments` | Separate from Workshop's `crapi` label |
| URL prefix | `/payments/` | nginx routes this prefix to `crapi-payments:8001` |
| Endpoints | 8 POST operations | auth, sale, reversal/{auth_id}, capture, void-capture, refund, void-refund, credit |
| Auth scheme | Header-based (merchant allowlist) | No JWT; see ADR-003 |

---

## 3. Network Topology

```
Levo Load Generator / curl
        │
        ▼ :8888
  crapi-web (OpenResty/nginx, port 80)
        │
  location /payments/
        │
        ▼ :8001
  crapi-payments (Django runserver)
        │
        ▼ :5432
  postgresdb (PostgreSQL, db=crapi)
```

`crapi-payments` is a leaf node — it reads/writes PostgreSQL and does not call any other crAPI service at runtime.

### URL Mapping

| External URL (via nginx :8888) | Internal URL | Operation |
|---|---|---|
| `POST /payments/api/payments/auth` | `crapi-payments:8001/payments/api/payments/auth` | Authorize |
| `POST /payments/api/payments/sale` | `crapi-payments:8001/payments/api/payments/sale` | Sale |
| `POST /payments/api/payments/reversal/{auth_id}` | `crapi-payments:8001/payments/api/payments/reversal/{auth_id}` | Reversal |
| `POST /payments/api/payments/capture` | `crapi-payments:8001/payments/api/payments/capture` | Capture |
| `POST /payments/api/payments/void-capture` | `crapi-payments:8001/payments/api/payments/void-capture` | Void Capture |
| `POST /payments/api/payments/refund` | `crapi-payments:8001/payments/api/payments/refund` | Refund |
| `POST /payments/api/payments/void-refund` | `crapi-payments:8001/payments/api/payments/void-refund` | Void Refund |
| `POST /payments/api/payments/credit` | `crapi-payments:8001/payments/api/payments/credit` | Credit |

---

## 4. Source File Tree

```
crAPI/
├── services/
│   ├── payments/                          # NEW service root
│   │   ├── Dockerfile
│   │   ├── runner.sh
│   │   ├── build-image.sh                 # auto-discovered by build-all.sh
│   │   ├── requirements.txt
│   │   ├── manage.py
│   │   ├── crapi_payments_site/           # Django project
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   └── wsgi.py
│   │   └── payments/                      # Django app
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       ├── middleware.py
│   │       ├── models.py
│   │       ├── urls.py
│   │       ├── views.py
│   │       └── migrations/
│   │           ├── __init__.py
│   │           └── 0001_initial.py
│   └── web/
│       ├── nginx.conf.template            # MODIFIED: +location /payments/
│       └── nginx-wrapper.sh              # MODIFIED: +${PAYMENTS_SERVICE} in envsubst
└── deploy/
    ├── docker/
    │   └── docker-compose.yml            # MODIFIED: +crapi-payments service block
    └── k8s/base/
        ├── deploy.sh                     # MODIFIED: +kubectl apply ./payments
        ├── payments/                     # NEW
        │   ├── config.yaml
        │   ├── deployment.yaml
        │   └── service.yaml
        └── web/
            └── configmap.yaml            # MODIFIED: +PAYMENTS_SERVICE
```

---

## 5. Django Project Files

### `services/payments/requirements.txt`

```
Django==3.2.25
djangorestframework==3.14.0
psycopg2-binary==2.9.9
PyJWT==2.8.0
requests==2.31.0
```

### `services/payments/crapi_payments_site/settings.py`

```python
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY  = os.environ.get('DJANGO_KEY', 'payments-insecure-dev-key-change-in-prod')
DEBUG       = True
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',       # required by contenttypes
    'rest_framework',
    'payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'payments.middleware.PaymentsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'crapi_payments_site.urls'
WSGI_APPLICATION = 'crapi_payments_site.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'crapi'),
        'USER': os.environ.get('DB_USER', 'admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'crapisecretpassword'),
        'HOST': os.environ.get('DB_HOST', 'postgresdb'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        'BACKEND': os.environ.get(
            'PAYMENTS_CACHE_BACKEND',
            'django.core.cache.backends.locmem.LocMemCache',
        ),
        'LOCATION': 'payments-cache',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES':    [],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True
```

### `services/payments/crapi_payments_site/urls.py`

```python
from django.urls import path, include

urlpatterns = [
    path('payments/', include('payments.urls')),
]
```

### `services/payments/payments/apps.py`

```python
from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    name = 'payments'
    default_auto_field = 'django.db.models.UUIDField'
```

### `services/payments/payments/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('api/payments/auth',                   views.AuthView.as_view()),
    path('api/payments/sale',                   views.SaleView.as_view()),
    path('api/payments/reversal/<str:auth_id>', views.ReversalView.as_view()),
    path('api/payments/capture',                views.CaptureView.as_view()),
    path('api/payments/void-capture',           views.VoidCaptureView.as_view()),
    path('api/payments/refund',                 views.RefundView.as_view()),
    path('api/payments/void-refund',            views.VoidRefundView.as_view()),
    path('api/payments/credit',                 views.CreditView.as_view()),
]
```

### `services/payments/manage.py`

```python
#!/usr/bin/env python3
import os, sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crapi_payments_site.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

---

## 6. Middleware

All validation runs in `PaymentsMiddleware` before any view is called. The order is strict:
**presence → merchant → timestamp → replay → idempotency**. A failure at any step short-circuits with the appropriate error response.

### `services/payments/payments/middleware.py`

```python
import os, re, json, hashlib, time
from datetime import datetime, timezone, timedelta
from django.core.cache import cache
from django.http import JsonResponse

# Allowlist loaded once at startup
_raw = os.environ.get('PAYMENTS_ALLOWED_MERCHANT_IDS', '')
ALLOWED_MERCHANTS = frozenset(m.strip() for m in _raw.split(',') if m.strip())

# Required headers: (META key, display name)
REQUIRED_HEADERS = [
    ('HTTP_X_REQUESTID',              'X-RequestID'),
    ('HTTP_X_LEVO_MERCHANT_ID',       'x-levo-merchant-id'),
    ('HTTP_X_LEVO_TERMINAL_ID',       'x-levo-terminal-id'),
    ('HTTP_X_LEVO_REQUEST_TIMESTAMP', 'x-levo-request-timestamp'),
    ('HTTP_X_LEVO_IDEMPOTENCY_KEY',   'x-levo-idempotency-key'),
]

_TS_RE         = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$')
_REPLAY_WINDOW = timedelta(minutes=5)
_RID_TTL       = 600   # 10 min — X-RequestID uniqueness window
_IDEM_TTL      = 300   # 5 min  — idempotency key window
_PAYMENTS_PATH = '/payments/api/payments/'

# Optional JWT enforcement (disabled by default; see ADR-003)
_REQUIRE_JWT = os.environ.get('PAYMENTS_REQUIRE_JWT', 'false').lower() == 'true'
if _REQUIRE_JWT:
    import jwt as _jwt
    _JWT_SECRET    = os.environ.get('JWT_SECRET', 'crapi')
    _JWT_ALGORITHM = 'HS256'


class PaymentsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(_PAYMENTS_PATH):
            return self.get_response(request)

        request._pay_start = time.monotonic()

        # 0. Optional JWT guard
        if _REQUIRE_JWT:
            auth = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth.startswith('Bearer '):
                return JsonResponse({'error': 'unauthorized'}, status=401)
            try:
                _jwt.decode(auth[7:], _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
            except _jwt.PyJWTError:
                return JsonResponse({'error': 'unauthorized'}, status=401)

        # 1. Required header presence
        for meta_key, display in REQUIRED_HEADERS:
            if not request.META.get(meta_key):
                return JsonResponse(
                    {'error': 'missing_header', 'header': display}, status=400)

        # 2. Merchant allowlist
        merchant_id = request.META['HTTP_X_LEVO_MERCHANT_ID']
        if merchant_id not in ALLOWED_MERCHANTS:
            return JsonResponse(
                {'error': 'merchant_not_authorized', 'merchant_id': merchant_id},
                status=403)

        # 3. Timestamp: format + 5-min replay window
        ts_str = request.META['HTTP_X_LEVO_REQUEST_TIMESTAMP']
        if not _TS_RE.match(ts_str):
            return JsonResponse(
                {'error': 'invalid_timestamp',
                 'detail': 'must match ISO 8601 UTC e.g. 2026-06-24T10:30:00.000Z'},
                status=400)
        try:
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            if abs(datetime.now(tz=timezone.utc) - ts) > _REPLAY_WINDOW:
                return JsonResponse(
                    {'error': 'timestamp_out_of_window',
                     'detail': 'timestamp must be within 5 minutes of server time'},
                    status=400)
        except ValueError:
            return JsonResponse({'error': 'invalid_timestamp'}, status=400)

        # 4. X-RequestID uniqueness (10-min window)
        request_id = request.META['HTTP_X_REQUESTID']
        rid_key = f'pay:rid:{request_id}'
        if cache.get(rid_key):
            return JsonResponse({'error': 'duplicate_request_id'}, status=409)
        cache.set(rid_key, 1, _RID_TTL)

        # 5. Idempotency
        idem_key = request.META['HTTP_X_LEVO_IDEMPOTENCY_KEY']
        _ = request.body  # force body read so cache hash is stable
        body_hash = hashlib.sha256(request.body).hexdigest()
        idem_cache_key = f'pay:idem:{idem_key}'
        cached = cache.get(idem_cache_key)
        if cached:
            if cached['hash'] == body_hash:
                r = JsonResponse(cached['response'], status=cached['status'])
                r['X-Idempotency-Hit'] = 'true'
                return r
            return JsonResponse(
                {'error': 'idempotency_conflict',
                 'detail': 'same key submitted with a different request body'},
                status=409)

        request._idem_cache_key = idem_cache_key
        request._body_hash = body_hash

        response = self.get_response(request)

        # Cache successful responses under idempotency key
        if response.status_code == 200 and hasattr(request, '_idem_cache_key'):
            try:
                cache.set(request._idem_cache_key, {
                    'hash': request._body_hash,
                    'response': json.loads(response.content),
                    'status': response.status_code,
                }, _IDEM_TTL)
            except (json.JSONDecodeError, Exception):
                pass

        return response
```

---

## 7. Models

One table: `payment_transaction`. Uses `app_label = 'payments'` — no collision with Workshop's `crapi` app.

### `services/payments/payments/models.py`

```python
import uuid
from django.db import models


class TransactionOperation(models.TextChoices):
    AUTH         = 'auth',         'Authorize'
    SALE         = 'sale',         'Sale'
    REVERSAL     = 'reversal',     'Reversal'
    CAPTURE      = 'capture',      'Capture'
    VOID_CAPTURE = 'void-capture', 'Void Capture'
    REFUND       = 'refund',       'Refund'
    VOID_REFUND  = 'void-refund',  'Void Refund'
    CREDIT       = 'credit',       'Credit'


class TransactionStatus(models.TextChoices):
    AUTHORIZED        = 'authorized',            'Authorized'
    SETTLED           = 'settled',               'Settled'
    REVERSED          = 'reversed',              'Reversed'
    CAPTURED          = 'captured',              'Captured'
    VOID_CAPTURE_DONE = 'void_capture_complete', 'Void Capture Complete'
    REFUNDED          = 'refunded',              'Refunded'
    VOID_REFUND_DONE  = 'void_refund_complete',  'Void Refund Complete'
    CREDITED          = 'credited',              'Credited'


class PaymentTransaction(models.Model):
    transaction_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    auth_id        = models.CharField(max_length=32, blank=True, default='')
    operation      = models.CharField(
        max_length=16, choices=TransactionOperation.choices)
    status         = models.CharField(
        max_length=32, choices=TransactionStatus.choices)
    # Amount stored in minor units (cents) to avoid float precision issues
    amount_value   = models.BigIntegerField(default=0)
    currency       = models.CharField(max_length=3, default='USD')
    merchant_id    = models.CharField(max_length=64)
    request_id     = models.CharField(max_length=64, db_index=True)
    original_transaction = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='derived')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'payments'
        db_table  = 'payment_transaction'
        indexes   = [
            models.Index(fields=['auth_id']),
            models.Index(fields=['merchant_id', 'created_at']),
            models.Index(fields=['original_transaction', 'operation']),
        ]

    def __str__(self):
        return f'{self.operation}:{self.transaction_id} [{self.status}]'
```

---

## 8. Views

All views follow the Workshop pattern: `APIView` subclass with `@csrf_exempt`. Middleware has already validated all headers — views focus on: parse body → state-machine check → DB write → return rich response.

### `services/payments/payments/views.py`

```python
import uuid, json, time, random, string
from datetime import datetime, timezone, timedelta

from django.db import models as db_models
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView

from .models import PaymentTransaction, TransactionOperation, TransactionStatus

# ── Shared helpers ─────────────────────────────────────────────────────────────

def _rand_digits(n):
    return ''.join(random.choices(string.digits, k=n))

def _rand_hex(n):
    return ''.join(random.choices('0123456789ABCDEF', k=n))

def _auth_id():    return f'AUTH-{_rand_digits(4)}'
def _aprv(pfx):    return f'{pfx}-{_rand_digits(4)}'
def _net_txn(op):  return f'NTX-SIM-{op}-{_rand_hex(12)}'

def _network(op_code):
    return {
        'acquirer_id':            'ACQ-SIM-001',
        'network_transaction_id': _net_txn(op_code),
        'response_code':          '00',
        'response_message':       'Approved',
        'processing_host':        'PAY-SIM-GW-1',
        'round_trip_ms':          random.randint(120, 380),
    }

def _meta(request):
    elapsed = int((time.monotonic() - getattr(request, '_pay_start', time.monotonic())) * 1000)
    return {
        'request_id':         request.META.get('HTTP_X_REQUESTID', ''),
        'processing_time_ms': elapsed,
        'api_version':        '2026-06',
        'scenario':           request.META.get('HTTP_X_LEVO_TEST_SCENARIO', ''),
        'gateway_node':       'pay-sim-node-1',
        'correlation_id':     request.META.get('HTTP_X_LEVO_CORRELATION_ID'),
    }

def _isodate(dt):
    return dt.isoformat().replace('+00:00', 'Z')

def _settle_date(dt, days=2):
    return (dt + timedelta(days=days)).strftime('%Y-%m-%d')

def _body(request):
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, ValueError) as e:
        return None, JsonResponse({'error': 'invalid_json', 'detail': str(e)}, status=400)

def _lookup(original_transaction_id, required_op, required_status):
    """Resolve original_transaction_id and validate state. Returns (txn, err_response)."""
    if not original_transaction_id:
        return None, JsonResponse(
            {'error': 'missing_field', 'field': 'original_transaction_id'}, status=400)
    try:
        uid = uuid.UUID(str(original_transaction_id))
    except ValueError:
        return None, JsonResponse(
            {'error': 'invalid_field', 'field': 'original_transaction_id',
             'detail': 'must be a valid UUID'}, status=400)
    try:
        txn = PaymentTransaction.objects.get(transaction_id=uid)
    except PaymentTransaction.DoesNotExist:
        return None, JsonResponse(
            {'error': 'transaction_not_found',
             'original_transaction_id': str(uid)}, status=404)
    if txn.operation != required_op:
        return None, JsonResponse(
            {'error': 'invalid_state',
             'detail': f'referenced transaction is {txn.operation!r}, expected {required_op!r}'},
            status=422)
    if txn.status != required_status:
        return None, JsonResponse(
            {'error': 'invalid_state',
             'current_status': txn.status,
             'detail': f'cannot perform operation on a transaction in state {txn.status!r}'},
            status=422)
    return txn, None

def _create(operation, status, amount_value, currency, merchant_id, request_id,
            auth_id='', original_txn=None):
    return PaymentTransaction.objects.create(
        operation=operation, status=status,
        amount_value=amount_value, currency=currency,
        auth_id=auth_id, merchant_id=merchant_id, request_id=request_id,
        original_transaction=original_txn,
    )


# ── 1. AUTH ────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class AuthView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn_data    = body.get('transaction', {})
        amt         = txn_data.get('amount', {})
        amount_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        aid = _auth_id()
        txn = _create(TransactionOperation.AUTH, TransactionStatus.AUTHORIZED,
                      amount_val, currency, merchant_id, request_id, auth_id=aid)
        created = _isodate(txn.created_at)
        expires = _isodate(txn.created_at + timedelta(hours=24))
        line_items = txn_data.get('order', {}).get('line_items', [])
        mcc = line_items[0].get('merchant_category_code', '5999') if line_items else '5999'

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'auth_id':        txn.auth_id,
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'expires_at':     expires,
                'idempotency_hit': False,
            },
            'authorization': {
                'authorized_amount': {'value': amount_val, 'currency': currency},
                'approval_code': _aprv('APR'),
                'hold_type': 'pre-authorization',
                'avs_result': {'code': 'Y', 'address_match': True,
                               'postal_code_match': True,
                               'description': 'Address and postal code match'},
                'cvv_result': {'code': 'M', 'match': True, 'description': 'CVV match'},
                'network': _network('AUTH'),
                'risk': {
                    'score': random.randint(5, 25), 'band': 'low',
                    'signals': ['velocity_ok', 'device_known', 'billing_match'],
                    'decision': 'approve', 'model_version': 'risk-v4.2.1',
                },
            },
            'settlement_routing': {
                'acquirer': 'Sim Paymentech', 'mcc': mcc, 'batch_id': None,
                'settlement_currency': currency,
                'interchange_category': 'CPS/Retail',
                'estimated_settlement_date': _settle_date(txn.created_at),
            },
            'meta': _meta(request),
        })


# ── 2. SALE ────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class SaleView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn_data    = body.get('transaction', {})
        amt         = txn_data.get('amount', {})
        amount_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        aid = _auth_id()
        txn = _create(TransactionOperation.SALE, TransactionStatus.SETTLED,
                      amount_val, currency, merchant_id, request_id, auth_id=aid)
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'auth_id':        txn.auth_id,
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'settled_at':     created,
                'idempotency_hit': False,
            },
            'authorization': {
                'authorized_amount': {'value': amount_val, 'currency': currency},
                'captured_amount':   {'value': amount_val, 'currency': currency},
                'approval_code': _aprv('APR'),
                'avs_result': {'code': 'Z', 'address_match': False,
                               'postal_code_match': True, 'description': 'Postal code match only'},
                'cvv_result': {'code': 'M', 'match': True, 'description': 'CVV match'},
                'network': _network('SALE'),
            },
            'settlement': {
                'batch_id':       f'BATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}',
                'settlement_date': txn.created_at.strftime('%Y-%m-%d'),
                'net_amount':     {'value': amount_val, 'currency': currency},
                'interchange_fee': {'value': int(amount_val * 0.02), 'currency': currency, 'rate_bps': 200},
                'processing_fee': {'value': 25, 'currency': currency},
                'funding_date':   _settle_date(txn.created_at, days=1),
            },
            'meta': _meta(request),
        })


# ── 3. REVERSAL ────────────────────────────────────────────────────────────────
# auth_id comes from URL path param, not request body.

@method_decorator(csrf_exempt, name='dispatch')
class ReversalView(APIView):
    def post(self, request, auth_id):
        body, err = _body(request)
        if err: return err

        try:
            auth_txn = PaymentTransaction.objects.get(
                auth_id=auth_id, operation=TransactionOperation.AUTH)
        except PaymentTransaction.DoesNotExist:
            return JsonResponse(
                {'error': 'transaction_not_found', 'auth_id': auth_id}, status=404)

        if auth_txn.status != TransactionStatus.AUTHORIZED:
            return JsonResponse(
                {'error': 'invalid_state',
                 'detail': f'auth {auth_id} is in state {auth_txn.status!r}, cannot reverse'},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.REVERSAL, TransactionStatus.REVERSED,
                      auth_txn.amount_value, auth_txn.currency,
                      merchant_id, request_id, original_txn=auth_txn)
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(auth_txn.transaction_id),
                'auth_id':                 auth_id,
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'reversal': {
                'reversed_amount': {'value': auth_txn.amount_value, 'currency': auth_txn.currency},
                'full_reversal':   True,
                'void_approval_code': _aprv('VD'),
                'network':         _network('REV'),
                'hold_released':   True,
                'hold_release_timestamp': created,
            },
            'settlement_impact': {
                'batch_id': None, 'was_in_open_batch': False,
                'settlement_adjustment_required': False,
                'estimated_funds_available_at': _isodate(
                    txn.created_at + timedelta(minutes=30)),
            },
            'audit_trail': {
                'operator_id':  request.META.get('HTTP_X_LEVO_TERMINAL_ID', ''),
                'terminal_id':  request.META.get('HTTP_X_LEVO_TERMINAL_ID', ''),
                'reason_code':  body.get('reversal', {}).get('reason', {}).get('code', 'UNSPECIFIED'),
                'confirmed_by': 'network_ack',
            },
            'meta': _meta(request),
        })


# ── 4. CAPTURE ─────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CaptureView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        auth_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.AUTH, TransactionStatus.AUTHORIZED)
        if err: return err

        capture_data = body.get('capture', {})
        amt          = capture_data.get('amount', {})
        cap_val      = amt.get('value', auth_txn.amount_value)
        currency     = amt.get('currency', auth_txn.currency)

        if cap_val > auth_txn.amount_value:
            return JsonResponse(
                {'error': 'capture_exceeds_authorized',
                 'detail': f'capture {cap_val} exceeds authorized {auth_txn.amount_value}'},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.CAPTURE, TransactionStatus.CAPTURED,
                      cap_val, currency, merchant_id, request_id,
                      auth_id=auth_txn.auth_id, original_txn=auth_txn)
        created  = _isodate(txn.created_at)
        batch_id = f'BATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}'

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(auth_txn.transaction_id),
                'auth_id':                 auth_txn.auth_id,
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'capture': {
                'captured_amount':            {'value': cap_val, 'currency': currency},
                'original_authorized_amount': {'value': auth_txn.amount_value, 'currency': auth_txn.currency},
                'delta': {'value': cap_val - auth_txn.amount_value, 'currency': currency,
                          'direction': 'under_capture' if cap_val < auth_txn.amount_value else 'full_capture'},
                'approval_code': _aprv('CAP'),
                'network': _network('CAP'),
            },
            'settlement_schedule': {
                'batch_id':                 batch_id,
                'batch_close_time':         txn.created_at.strftime('%Y-%m-%dT23:59:00Z'),
                'expected_settlement_date': _settle_date(txn.created_at, days=1),
                'interchange_category':     'CPS/Retail',
                'net_amount':               {'value': cap_val, 'currency': currency},
                'fees': {
                    'interchange': {'value': int(cap_val * 0.018), 'currency': currency},
                    'processing':  {'value': 29, 'currency': currency},
                },
            },
            'meta': _meta(request),
        })


# ── 5. VOID-CAPTURE ────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class VoidCaptureView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        cap_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.CAPTURE, TransactionStatus.CAPTURED)
        if err: return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.VOID_CAPTURE, TransactionStatus.VOID_CAPTURE_DONE,
                      cap_txn.amount_value, cap_txn.currency,
                      merchant_id, request_id, original_txn=cap_txn)
        created  = _isodate(txn.created_at)
        auth_txn = cap_txn.original_transaction

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(cap_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'void_capture': {
                'voided_amount': {'value': cap_txn.amount_value, 'currency': cap_txn.currency},
                'approval_code': _aprv('VDC'),
                'network':       _network('VDC'),
                'batch_status': {
                    'batch_id':           body.get('void', {}).get('timing', {}).get('batch_id', ''),
                    'removed_from_batch': True,
                    'batch_rebalanced':   True,
                },
            },
            'auth_status': {
                'auth_transaction_id':   str(auth_txn.transaction_id) if auth_txn else None,
                'auth_id':               cap_txn.auth_id,
                'auth_status_post_void': 'authorized',
                're_capturable':         True,
                'auth_expires_at':       _isodate(txn.created_at + timedelta(hours=24)),
            },
            'meta': _meta(request),
        })


# ── 6. REFUND ──────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class RefundView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        cap_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.CAPTURE, TransactionStatus.CAPTURED)
        if err: return err

        refund_data = body.get('refund', {})
        amt         = refund_data.get('amount', {})
        ref_val     = amt.get('value', cap_txn.amount_value)
        currency    = amt.get('currency', cap_txn.currency)

        already_refunded = PaymentTransaction.objects.filter(
            original_transaction=cap_txn,
            operation=TransactionOperation.REFUND,
            status=TransactionStatus.REFUNDED,
        ).aggregate(total=db_models.Sum('amount_value'))['total'] or 0

        if already_refunded + ref_val > cap_txn.amount_value:
            return JsonResponse(
                {'error': 'refund_exceeds_captured',
                 'detail': f'refund {ref_val} + already refunded {already_refunded} '
                           f'exceeds captured {cap_txn.amount_value}'},
                status=422)

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.REFUND, TransactionStatus.REFUNDED,
                      ref_val, currency, merchant_id, request_id, original_txn=cap_txn)
        created   = _isodate(txn.created_at)
        remaining = cap_txn.amount_value - already_refunded - ref_val

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(cap_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'refund': {
                'refunded_amount':       {'value': ref_val, 'currency': currency},
                'remaining_refundable':  {'value': remaining, 'currency': currency},
                'approval_code':         _aprv('RFD'),
                'network':               _network('RFD'),
                'customer_notification': {
                    'sent': True, 'channel': 'email', 'template_id': 'REFUND_CONF_V2'},
            },
            'settlement': {
                'credit_batch_id':       f'CRBATCH-{txn.created_at.strftime("%Y%m%d")}-{_rand_digits(4)}',
                'expected_credit_date':  _settle_date(txn.created_at, days=2),
                'business_days_to_credit': 2,
                'interchange_recovery':  {'value': int(ref_val * 0.015), 'currency': currency},
            },
            'meta': _meta(request),
        })


# ── 7. VOID-REFUND ─────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class VoidRefundView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        ref_txn, err = _lookup(
            body.get('original_transaction_id'),
            TransactionOperation.REFUND, TransactionStatus.REFUNDED)
        if err: return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        txn = _create(TransactionOperation.VOID_REFUND, TransactionStatus.VOID_REFUND_DONE,
                      ref_txn.amount_value, ref_txn.currency,
                      merchant_id, request_id, original_txn=ref_txn)
        created  = _isodate(txn.created_at)
        cap_txn  = ref_txn.original_transaction

        remaining = 0
        if cap_txn:
            still_refunded = PaymentTransaction.objects.filter(
                original_transaction=cap_txn,
                operation=TransactionOperation.REFUND,
                status=TransactionStatus.REFUNDED,
            ).exclude(transaction_id=ref_txn.transaction_id
            ).aggregate(total=db_models.Sum('amount_value'))['total'] or 0
            remaining = cap_txn.amount_value - still_refunded

        return JsonResponse({
            'transaction': {
                'transaction_id':          str(txn.transaction_id),
                'original_transaction_id': str(ref_txn.transaction_id),
                'status':                  txn.status,
                'operation':               txn.operation,
                'created_at':              created,
                'idempotency_hit':         False,
            },
            'void_refund': {
                'voided_refund_amount': {'value': ref_txn.amount_value, 'currency': ref_txn.currency},
                'approval_code': _aprv('VDR'),
                'network':       _network('VDR'),
                'credit_batch_status': {
                    'removed_from_batch': True,
                    'batch_id': body.get('void', {}).get('timing', {}).get('credit_batch_id', ''),
                },
            },
            'capture_status': {
                'capture_transaction_id':  str(cap_txn.transaction_id) if cap_txn else None,
                'status_post_void_refund': 'captured',
                'remaining_refundable':    {'value': remaining, 'currency': ref_txn.currency},
            },
            'meta': _meta(request),
        })


# ── 8. CREDIT ──────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CreditView(APIView):
    def post(self, request):
        body, err = _body(request)
        if err: return err

        merchant_id = request.META.get('HTTP_X_LEVO_MERCHANT_ID', '')
        request_id  = request.META.get('HTTP_X_REQUESTID', '')
        credit_data = body.get('credit', {})
        amt         = credit_data.get('amount', {})
        credit_val  = amt.get('value', 0)
        currency    = amt.get('currency', 'USD')

        txn = _create(TransactionOperation.CREDIT, TransactionStatus.CREDITED,
                      credit_val, currency, merchant_id, request_id)
        created = _isodate(txn.created_at)

        return JsonResponse({
            'transaction': {
                'transaction_id': str(txn.transaction_id),
                'status':         txn.status,
                'operation':      txn.operation,
                'created_at':     created,
                'idempotency_hit': False,
            },
            'credit': {
                'credited_amount': {'value': credit_val, 'currency': currency},
                'approval_code':   _aprv('CRD'),
                'network':         _network('CRD'),
                'recipient_notification': {
                    'sent': True, 'channel': 'email', 'template_id': 'LOYALTY_CREDIT_V3'},
            },
            'funding': {
                'funding_source_id':  credit_data.get('funding_source', {}).get('account_id', ''),
                'debit_confirmation': f'DCF-{_rand_digits(8)}',
                'gl_posted':          True,
                'gl_post_timestamp':  created,
            },
            'compliance': {
                'reporting_triggered': False, 'aml_clear': True, 'sanctions_clear': True},
            'meta': _meta(request),
        })
```

---

## 9. Dockerfile, Runner & Build

### `services/payments/Dockerfile`

```dockerfile
FROM python:3.8-alpine3.15 AS builder
WORKDIR /build
COPY requirements.txt .
RUN apk add --no-cache build-base libffi-dev postgresql-dev \
 && pip install --no-cache-dir wheel \
 && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.8-alpine3.15
WORKDIR /opt/crapi-payments
RUN apk add --no-cache libpq
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["/bin/sh", "runner.sh"]
```

### `services/payments/runner.sh`

```sh
#!/bin/sh
set -e
echo "[payments] running migrations..."
python3 manage.py migrate --noinput
echo "[payments] starting server on port ${SERVER_PORT:-8001}..."
exec python3 manage.py runserver 0.0.0.0:${SERVER_PORT:-8001}
```

### `services/payments/build-image.sh`

```bash
#!/bin/bash
# Auto-discovered by deploy/k8s/base/build-all.sh:
#   find ../../../services/ -name 'build-image*' -exec bash {} \;
set -e
cd "$(dirname "$0")"
docker build -t levoai/crapi-payments:latest .
```

---

## 10. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PAYMENTS_ALLOWED_MERCHANT_IDS` | **required** | — | Comma-separated allowed merchant IDs. Empty = every request returns 403 (fail-safe). |
| `DB_HOST` | **required** | `postgresdb` | PostgreSQL hostname. |
| `DB_PORT` | | `5432` | PostgreSQL port. |
| `DB_NAME` | | `crapi` | Database name (shared with other services). |
| `DB_USER` | | `admin` | PostgreSQL user. |
| `DB_PASSWORD` | **required** | `crapisecretpassword` | PostgreSQL password. |
| `DJANGO_KEY` | | `payments-insecure-…` | Django `SECRET_KEY`. Change for non-local deploys. |
| `SERVER_PORT` | | `8001` | Port Django listens on inside the container. |
| `ALLOWED_HOSTS` | | `*` | Comma-separated Django `ALLOWED_HOSTS`. |
| `PAYMENTS_REQUIRE_JWT` | | `false` | Set `true` to require a valid crAPI JWT Bearer token (see ADR-003). |
| `JWT_SECRET` | | `crapi` | Shared JWT secret — only needed when `PAYMENTS_REQUIRE_JWT=true`. |
| `PAYMENTS_CACHE_BACKEND` | | `LocMemCache` | Override Django cache backend. Use `django.core.cache.backends.db.DatabaseCache` for persistence across restarts. |

---

## 11. Database Schema & Migration

### `services/payments/payments/migrations/0001_initial.py`

```python
import uuid
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('transaction_id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True)),
                ('auth_id',    models.CharField(blank=True, default='', max_length=32)),
                ('operation',  models.CharField(max_length=16, choices=[
                    ('auth','Authorize'), ('sale','Sale'), ('reversal','Reversal'),
                    ('capture','Capture'), ('void-capture','Void Capture'),
                    ('refund','Refund'), ('void-refund','Void Refund'), ('credit','Credit'),
                ])),
                ('status',     models.CharField(max_length=32, choices=[
                    ('authorized','Authorized'), ('settled','Settled'),
                    ('reversed','Reversed'), ('captured','Captured'),
                    ('void_capture_complete','Void Capture Complete'),
                    ('refunded','Refunded'), ('void_refund_complete','Void Refund Complete'),
                    ('credited','Credited'),
                ])),
                ('amount_value', models.BigIntegerField(default=0)),
                ('currency',    models.CharField(default='USD', max_length=3)),
                ('merchant_id', models.CharField(max_length=64)),
                ('request_id',  models.CharField(db_index=True, max_length=64)),
                ('original_transaction', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='derived', to='payments.paymenttransaction')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'payment_transaction', 'app_label': 'payments'},
        ),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['auth_id'], name='pay_auth_id_idx')),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(fields=['merchant_id', 'created_at'], name='pay_merch_date_idx')),
        migrations.AddIndex(
            model_name='paymenttransaction',
            index=models.Index(
                fields=['original_transaction', 'operation'], name='pay_orig_op_idx')),
    ]
```

---

## 12. Docker Compose Changes

Two edits to `deploy/docker/docker-compose.yml`:

```diff
   crapi-workshop:
     image: levoai/crapi-workshop:${VERSION:-latest}
     ...

+  crapi-payments:
+    image: levoai/crapi-payments:${VERSION:-latest}
+    environment:
+      - DB_HOST=postgresdb
+      - DB_NAME=crapi
+      - DB_USER=admin
+      - DB_PASSWORD=crapisecretpassword
+      - DB_PORT=5432
+      - SERVER_PORT=8001
+      - ALLOWED_HOSTS=*
+      - DJANGO_KEY=payments-insecure-dev-key-00001
+      - PAYMENTS_ALLOWED_MERCHANT_IDS=merch_7f2a91,merch_4b8c12,merch_0d3e55,merch_load01
+    depends_on: [postgresdb, crapi-identity]
+    ports:
+      - "127.0.0.1:8001:8001"

   crapi-web:
     image: levoai/crapi-web:${VERSION:-latest}
     environment:
       - JAVA_SERVICE=crapi-identity:8080
       - PYTHON_SERVICE=crapi-workshop:8000
       - GO_SERVICE=crapi-community:8087
       - MAILHOG_UI=mailhog:8025
+      - PAYMENTS_SERVICE=crapi-payments:8001
```

---

## 13. Nginx Changes

> **Rebuild required.** Both nginx files are baked into `levoai/crapi-web` at image build time. After these edits, run `docker build -t levoai/crapi-web:latest services/web/` and restart the web container.

### `services/web/nginx.conf.template` — add location block

```diff
     location /workshop/ {
         proxy_pass http://${PYTHON_SERVICE};
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         rewrite_by_lua_block {
             local body = ngx.req.get_body_data()
             if body then
                 ngx.req.set_body_data(
                     string.gsub(body, "://" .. ngx.var.host, "://" .. ngx.var.proxy_host))
             end
         }
     }

+    location /payments/ {
+        proxy_pass http://${PAYMENTS_SERVICE};
+        proxy_set_header Host $host;
+        proxy_set_header X-Real-IP $remote_addr;
+        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
+        proxy_pass_request_headers on;
+        rewrite_by_lua_block {
+            ngx.req.read_body()
+            local body = ngx.req.get_body_data()
+            if body then
+                ngx.req.set_body_data(
+                    string.gsub(body, "://" .. ngx.var.host, "://" .. ngx.var.proxy_host))
+            end
+        }
+    }
```

### `services/web/nginx-wrapper.sh` — add `${PAYMENTS_SERVICE}` to envsubst

```diff
-envsubst '${MAILHOG_UI} ${GO_SERVICE} ${JAVA_SERVICE} ${PYTHON_SERVICE}' \
+envsubst '${MAILHOG_UI} ${GO_SERVICE} ${JAVA_SERVICE} ${PYTHON_SERVICE} ${PAYMENTS_SERVICE}' \
   < /etc/nginx/conf.d/default.conf.template \
   > /etc/nginx/conf.d/default.conf
 openresty -g 'daemon off;'
```

> **Why the explicit list matters.** OpenResty's `envsubst` without an explicit variable list substitutes every `${VAR}` in the template — including nginx variables like `${uri}` — breaking the config. Every service variable added to the template must appear in this list.

---

## 14. Kubernetes Manifests

### `deploy/k8s/base/payments/config.yaml` (new)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: crapi-payments-configmap
data:
  DB_HOST:     postgresdb
  DB_NAME:     crapi
  DB_USER:     admin
  DB_PASSWORD: crapisecretpassword
  DB_PORT:     "5432"
  SERVER_PORT: "8001"
  ALLOWED_HOSTS: "*"
  DJANGO_KEY:  payments-insecure-dev-key-00001
  PAYMENTS_ALLOWED_MERCHANT_IDS: "merch_7f2a91,merch_4b8c12,merch_0d3e55,merch_load01"
```

### `deploy/k8s/base/payments/deployment.yaml` (new)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crapi-payments
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crapi-payments
  template:
    metadata:
      labels:
        app: crapi-payments
    spec:
      initContainers:
        - name: wait-for-postgres
          image: busybox
          command:
            - sh
            - -c
            - until nc -z postgresdb 5432; do echo "waiting for postgres"; sleep 2; done
      containers:
        - name: crapi-payments
          image: levoai/crapi-payments:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8001
          envFrom:
            - configMapRef:
                name: crapi-payments-configmap
          readinessProbe:
            tcpSocket:
              port: 8001
            initialDelaySeconds: 10
            periodSeconds: 10
            failureThreshold: 5
```

### `deploy/k8s/base/payments/service.yaml` (new)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: crapi-payments
spec:
  selector:
    app: crapi-payments
  ports:
    - protocol: TCP
      port: 8001
      targetPort: 8001
      name: payments
```

### `deploy/k8s/base/web/configmap.yaml` (modified)

```diff
 data:
   GO_SERVICE:       crapi-community:8087
   JAVA_SERVICE:     crapi-identity:8080
   PYTHON_SERVICE:   crapi-workshop:8000
   MAILHOG_UI:       mailhog-web:8025
+  PAYMENTS_SERVICE: crapi-payments:8001
```

### `deploy/k8s/base/deploy.sh` (modified)

```diff
 kubectl apply -n ${NAMESPACE} -f ./workshop
+kubectl apply -n ${NAMESPACE} -f ./payments
 kubectl apply -n ${NAMESPACE} -f ./web
```

---

## 15. Build & Publish Procedure

### Local Docker Compose (first-time setup)

```bash
# 1. Build the payments image
docker build -t levoai/crapi-payments:latest crAPI/services/payments/

# 2. Rebuild the web image (nginx changes baked in)
docker build -t levoai/crapi-web:latest crAPI/services/web/

# 3. Bring up the full stack
cd crAPI/deploy/docker
docker compose up -d

# 4. Verify migrations and startup
docker compose logs crapi-payments --tail=30

# 5. Smoke test — update timestamp to current time
curl -s -X POST http://localhost:8888/payments/api/payments/auth \
  -H "Content-Type: application/json" \
  -H "X-RequestID: $(date +%s%3N | tail -c 12)$(shuf -i 1000000000-9999999999 -n1)" \
  -H "x-levo-merchant-id: merch_7f2a91" \
  -H "x-levo-terminal-id: term_00042" \
  -H "x-levo-request-timestamp: $(date -u +%Y-%m-%dT%H:%M:%S.000Z)" \
  -H "x-levo-idempotency-key: idem-$(uuidgen | tr -d -)" \
  -d '{"card":{"pan":"4111111111111111"},"transaction":{"amount":{"value":10000,"currency":"USD"}}}' \
  | python3 -m json.tool
```

### Kubernetes

```bash
# 1. Build and push both images
docker build -t levoai/crapi-payments:latest crAPI/services/payments/
docker build -t levoai/crapi-web:latest crAPI/services/web/
docker push levoai/crapi-payments:latest
docker push levoai/crapi-web:latest

# 2. Deploy (deploy.sh now includes ./payments)
cd crAPI/deploy/k8s/base
./deploy.sh crapi-namespace

# 3. Rolling restart of web (picks up new configmap + new nginx)
kubectl rollout restart deployment/crapi-web -n crapi-namespace

# 4. Verify
kubectl rollout status deployment/crapi-payments -n crapi-namespace
kubectl rollout status deployment/crapi-web      -n crapi-namespace
```

---

## 16. Transaction State Machine

Each view validates the referenced transaction's `operation` and `status` before proceeding. Invalid transitions return `422 Unprocessable Entity`.

| Operation | Input: must reference | Input: status must be | Output status |
|---|---|---|---|
| **auth** | — | — | `authorized` |
| **sale** | — | — | `settled` |
| **reversal** | `auth_id` (URL path) | AUTH / `authorized` | `reversed` |
| **capture** | `original_transaction_id` | AUTH / `authorized` | `captured` |
| **void-capture** | `original_transaction_id` | CAPTURE / `captured` | `void_capture_complete` |
| **refund** | `original_transaction_id` | CAPTURE / `captured` | `refunded` |
| **void-refund** | `original_transaction_id` | REFUND / `refunded` | `void_refund_complete` |
| **credit** | — | — | `credited` |

### Error Codes

| HTTP | Condition |
|---|---|
| 400 | Missing required header, invalid JSON, malformed or expired timestamp |
| 403 | Merchant ID not in `PAYMENTS_ALLOWED_MERCHANT_IDS` |
| 404 | `original_transaction_id` or `auth_id` does not exist |
| 409 | Duplicate `X-RequestID` within 10 min, or idempotency key replayed with different body |
| 422 | State violation: wrong operation type or wrong status; refund exceeds captured amount |

### Additional Guards

- **Partial capture:** `capture.amount.value` must be ≤ authorized amount or 422 is returned.
- **Cumulative refunds:** sum of all REFUNDED transactions against a capture must not exceed `captured.amount_value`. The refund view queries all prior refunds and rejects if adding the new one would exceed the cap.

---

## 17. Verification Checklist

| Test | Expected Result |
|---|---|
| Auth with valid merchant headers | 200 — body contains `auth_id` like `AUTH-XXXX` and `transaction_id` UUID |
| Auth → Reversal (path param `auth_id`) | 200 — `reversal.hold_released: true` |
| Auth → Capture | 200 — `capture.approval_code` present, `captured_amount` ≤ authorized |
| Capture → Refund | 200 — `refund.remaining_refundable` decreases correctly |
| Refund exceeding captured amount | 422 — `error: refund_exceeds_captured` |
| Capture → Void-Capture | 200 — `auth_status.re_capturable: true` |
| Refund → Void-Refund | 200 — `capture_status.remaining_refundable` restored |
| Unknown merchant ID | 403 — `error: merchant_not_authorized` |
| Missing `x-levo-terminal-id` | 400 — `error: missing_header` |
| Malformed timestamp | 400 — `error: invalid_timestamp` |
| Timestamp > 5 min old | 400 — `error: timestamp_out_of_window` |
| Duplicate `X-RequestID` within 10 min | 409 — `error: duplicate_request_id` |
| Same idempotency key + same body | 200 — response header `X-Idempotency-Hit: true` |
| Same idempotency key + different body | 409 — `error: idempotency_conflict` |
| Reversal on already-reversed auth | 422 — `error: invalid_state` |
| `docker compose up --build` cold start | All services healthy; payments logs show "running migrations" then "starting server on port 8001" |
| Payments logs after auth request | No errors; `[25/Jun/2026 ... POST /payments/api/payments/auth HTTP/1.1" 200` |
