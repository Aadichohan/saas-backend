from django.db import models
from django.contrib.auth.models import User

class Business(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=255)
    whatsapp_access_token = models.CharField(max_length=500, blank=True, null=True)
    phone_number_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.IntegerField(default=1) # For soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name