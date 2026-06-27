# Test-only settings: SQLite in-memory + LocMemCache, no external deps
from crapi_payments_site.settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

PAYMENTS_ALLOWED_MERCHANT_IDS = 'test_merch_001,test_merch_002'
