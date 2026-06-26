from django.urls import path
from . import views

urlpatterns = [
    path('api/payments/auth',                    views.AuthView.as_view()),
    path('api/payments/sale',                    views.SaleView.as_view()),
    path('api/payments/reversal/<str:auth_id>',  views.ReversalView.as_view()),
    path('api/payments/capture',                 views.CaptureView.as_view()),
    path('api/payments/void-capture',            views.VoidCaptureView.as_view()),
    path('api/payments/refund',                  views.RefundView.as_view()),
    path('api/payments/void-refund',             views.VoidRefundView.as_view()),
    path('api/payments/credit',                  views.CreditView.as_view()),
    path('api/payments/health',                  views.HealthView.as_view()),
]
