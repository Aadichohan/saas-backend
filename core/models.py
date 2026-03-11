from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

from django.utils import timezone
from datetime import timedelta

class Business(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=255)
    whatsapp_access_token = models.CharField(max_length=500, blank=True, null=True)
    phone_number_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('Trial', 'Trial'),
        ('Basic', 'Basic'),
        ('Advance', 'Advance'),
        ('Pro', 'Pro'),
    ]
    
    # Plan Configurations (Pricing & Limits)
    PLAN_DATA = {
        'Trial':   {'price': 0,    'text_limit': 100,    'call_limit': 0},
        'Basic':   {'price': 49,   'text_limit': 2000,   'call_limit': 200},
        'Advance': {'price': 149,  'text_limit': 10000,  'call_limit': 1000},
        'Pro':     {'price': 499,  'text_limit': 50000,  'call_limit': 5000},
    }

    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='Trial')
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    trial_start_date = models.DateTimeField(auto_now_add=True)
    
    # Usage Tracking
    text_used = models.IntegerField(default=0)
    call_used = models.IntegerField(default=0) # In minutes or calls

    def __str__(self):
        return f"{self.business.name} - {self.plan_type}"

    @property
    def is_trial_expired(self):
        if self.plan_type == 'Trial':
            return timezone.now() > self.trial_start_date + timedelta(days=7)
        return False

    def check_limit(self, mode):
        """
        Checks if the usage limit for the given mode has been reached.
        """
        plan_config = self.PLAN_DATA.get(self.plan_type)
        if mode == 'Text':
            return self.text_used < plan_config['text_limit']
        elif mode in ['Voice', 'Call']:
            return self.call_used < plan_config['call_limit']
        return False

    def has_access_to_mode(self, mode):
        """
        Enforces plan restrictions and 7-day trial.
        """
        if self.is_trial_expired:
            return False

        # Basic access logic
        restrictions = {
            'Trial': ['Text'],
            'Basic': ['Text', 'Voice'],
            'Advance': ['Text', 'Voice', 'Call'],
            'Pro': ['Text', 'Voice', 'Call'],
        }
        
        if mode not in restrictions.get(self.plan_type, []):
            return False
            
        return self.check_limit(mode)

class ChatLog(models.Model):
    MODE_CHOICES = [
        ('Text', 'Text'),
        ('Voice', 'Voice'),
        ('Call', 'Call'),
    ]
    STATUS_CHOICES = [
        ('DISPATCHED', 'Dispatched'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='chat_logs')
    customer_number = models.CharField(max_length=20, blank=True, null=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISPATCHED')
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict, blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business.name} - {self.mode} - {self.status} - {self.timestamp}"

def deduct_credits(business_id, mode):
    """
    Deducts credits and increments usage counters based on the interaction mode.
    Text: $0.01
    Voice/Call: $0.10
    """
    subscription = Subscription.objects.get(business_id=business_id)
    cost = Decimal('0.01') if mode == 'Text' else Decimal('0.10')
    
    if subscription.credits >= cost:
        # Deduct balance
        subscription.credits -= cost
        
        # Increment usage counter
        if mode == 'Text':
            subscription.text_used += 1
        elif mode in ['Voice', 'Call']:
            subscription.call_used += 1 # Tracking counts/minutes
            
        subscription.save()
        return True, cost
    return False, Decimal('0.00')
