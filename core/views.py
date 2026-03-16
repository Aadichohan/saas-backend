import requests
import uuid
from decimal import Decimal
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Business, Subscription, ChatLog, deduct_credits
from .utils import send_whatsapp_message

class DispatchView(APIView):
    """
    Endpoint: /api/v1/agent/dispatch/
    Receives customer message, checks plan/credits, and forwards to n8n.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business_id = request.data.get('business_id')
        customer_number = request.data.get('customer_number')
        mode = request.data.get('mode', 'Text')  # Text, Voice, Call
        message = request.data.get('message')

        if not all([business_id, customer_number, message]):
            return Response({'error': 'business_id, customer_number, and message are required'}, status=400)

        # 1. Gatekeeper Check
        try:
            subscription = Subscription.objects.get(business_id=business_id)
            cost = Decimal('0.01') if mode == 'Text' else Decimal('0.10')
            
            error_reason = None
            if not subscription.is_active:
                error_reason = "Subscription is inactive."
            elif subscription.is_trial_expired:
                error_reason = "Your 7-day trial has expired. Please upgrade to a paid plan."
            elif not subscription.has_access_to_mode(mode):
                error_reason = f"Plan {subscription.plan_type} does not support {mode} mode or you have reached your plan limit."
            elif not subscription.check_limit(mode):
                error_reason = f"You have reached the {mode} limit for your {subscription.plan_type} plan."
            elif subscription.credits < cost:
                error_reason = "Insufficient credits."

            if error_reason:
                # Log Failure
                ChatLog.objects.create(
                    business_id=business_id,
                    customer_number=customer_number,
                    mode=mode,
                    status='FAILED',
                    request_data={'message': message},
                    error_message=error_reason
                )
                return Response({'error': error_reason}, status=402)

        except Subscription.DoesNotExist:
            return Response({'error': 'Subscription not found'}, status=404)

        # 2. Forward to n8n
        session_id = str(uuid.uuid4())
        callback_url = request.build_absolute_uri(
            reverse('agent-callback', kwargs={'session_id': session_id})
        )

        n8n_payload = {
            'business_id': business_id,
            'customer_number': customer_number,
            'mode': mode,
            'message': message,
            'callback_url': callback_url,
            'whatsapp_token': subscription.business.whatsapp_access_token,
            'phone_id': subscription.business.phone_number_id,
        }

        # n8n_url = getattr(settings, 'N8N_WEBHOOK_URL', 'https://n8n.yourdomain.com/webhook/agent-dispatch')
        n8n_url = getattr(settings, 'N8N_WEBHOOK_URL', 'http://localhost:5678/webhook-test/whatsapp-gateway')

        # Log Dispatch
        ChatLog.objects.create(
            business_id=business_id,
            customer_number=customer_number,
            mode=mode,
            status='DISPATCHED',
            request_data=n8n_payload
        )

        try:
            requests.post(n8n_url, json=n8n_payload, timeout=5)
        except requests.exceptions.RequestException as e:
            print(f"Error forwarding to n8n: {e}")

        return Response({
            'status': 'dispatched',
            'session_id': session_id
        })

class CallbackView(APIView):
    """
    Endpoint: /api/v1/agent/callback/<session_id>/
    Receives response from n8n, logs it, deducts credits, and responds to customer.
    """
    permission_classes = [] 

    def post(self, request, session_id):
        business_id = request.data.get('business_id')
        customer_number = request.data.get('customer_number')
        mode = request.data.get('mode', 'Text')
        response_text = request.data.get('response')

        if not all([business_id, customer_number, response_text]):
            return Response({'error': 'Missing required fields'}, status=400)

        # 1. Deduct credits
        success, cost = deduct_credits(business_id, mode)

        if not success:
            # This shouldn't happen usually because of DispatchView check, but for safety:
            ChatLog.objects.create(
                business_id=business_id,
                customer_number=customer_number,
                mode=mode,
                status='FAILED',
                error_message="Insufficient credits during callback processing"
            )
            return Response({'error': 'Insufficient credits'}, status=402)

        # 2. Log Success
        log = ChatLog.objects.create(
            business_id=business_id,
            customer_number=customer_number,
            mode=mode,
            status='SUCCESS',
            response_data={'response': response_text},
            cost=cost
        )

        # 3. Respond to Customer
        business = Business.objects.get(id=business_id)
        delivery_success = send_whatsapp_message(business, customer_number, response_text)

        if not delivery_success:
            log.error_message = "n8n processed but WhatsApp delivery failed."
            log.save()

        return Response({
            'status': 'processed',
            'delivery': 'success' if delivery_success else 'failed'
        })
