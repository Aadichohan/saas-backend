from rest_framework import serializers
from .models import Business

class BusinessSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Business
        fields = ['id', 'user', 'username', 'name', 'whatsapp_access_token', 'phone_number_id', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'whatsapp_access_token': {'write_only': True} # Security: Token response mein nahi jayega
        }