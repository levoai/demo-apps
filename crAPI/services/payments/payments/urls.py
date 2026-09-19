from django.urls import path
from . import views

urlpatterns = [
    # Core payment operations
    path('api/payments/auth',                    views.AuthView.as_view()),
    path('api/payments/sale',                    views.SaleView.as_view()),
    path('api/payments/reversal/<str:auth_id>',  views.ReversalView.as_view()),
    path('api/payments/capture',                 views.CaptureView.as_view()),
    path('api/payments/void-capture',            views.VoidCaptureView.as_view()),
    path('api/payments/refund',                  views.RefundView.as_view()),
    path('api/payments/void-refund',             views.VoidRefundView.as_view()),
    path('api/payments/credit',                  views.CreditView.as_view()),
    path('api/payments/health',                  views.HealthView.as_view()),

    # VULNERABILITY [API1-BOLA]: transaction detail/delete — no ownership check
    path('api/payments/transactions',                       views.TransactionListView.as_view()),
    path('api/payments/transactions/<str:transaction_id>',  views.TransactionDetailView.as_view()),

    # VULNERABILITY [API5-BFLA]: admin endpoint with guessable X-Admin-Key
    path('api/payments/admin/transactions',      views.AdminTransactionListView.as_view()),

    # VULNERABILITY [API7-Security Misconfiguration]: unauthenticated debug endpoint
    path('api/payments/debug',                   views.DebugView.as_view()),

    # VULNERABILITY [SSRF]: server fetches caller-supplied URL
    path('api/payments/webhook/test',            views.WebhookTestView.as_view()),

    # VULNERABILITY [API9-Improper Inventory]: deprecated v1 — bypasses PaymentsMiddleware
    # (middleware only guards /payments/api/payments/*, v1 path is /payments/api/v1/*)
    path('api/v1/payments/auth',                 views.LegacyAuthView.as_view()),

    # Dual-token OR-auth fixture (generic multi-token authN pattern): authenticated
    # if EITHER `token` or `stepped-up-token` is valid. Outside /api/payments/, so
    # PaymentsMiddleware's header/replay checks don't apply.
    path('api/dual-auth/sample-token',                views.DualTokenSampleView.as_view()),

    # Header case
    path('api/dual-auth/header-check',                views.DualTokenHeaderView.as_view()),
    path('api/dual-auth/header-check-bearer',          views.DualTokenHeaderBearerView.as_view()),
    path('api/dual-auth/header-check-sensitive-action', views.DualTokenHeaderSensitiveActionView.as_view()),

    # Cookie case
    path('api/dual-auth/cookie-check',                views.DualTokenCookieView.as_view()),
    path('api/dual-auth/cookie-check-noisy',           views.DualTokenCookieNoisyView.as_view()),
    path('api/dual-auth/cookie-check-cross-transport', views.DualTokenCookieCrossTransportView.as_view()),
]
