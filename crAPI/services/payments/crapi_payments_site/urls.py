from django.urls import path, include

urlpatterns = [
    path('payments/', include('payments.urls')),
]
