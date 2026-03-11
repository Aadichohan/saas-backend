from django.urls import path
from .views import DispatchView, CallbackView

urlpatterns = [
    path('agent/dispatch/', DispatchView.as_view(), name='agent-dispatch'),
    path('agent/callback/<uuid:session_id>/', CallbackView.as_view(), name='agent-callback'),
]
