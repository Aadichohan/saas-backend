from django.http import JsonResponse
from django.urls import resolve
from .models import Subscription

class CheckBalanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only care about the dispatcher endpoint
        if request.path == '/api/v1/agent/dispatch/':
            business_id = request.headers.get('X-Business-ID') or request.GET.get('business_id')
            
            if not business_id:
                return JsonResponse({'error': 'business_id is required'}, status=400)
            
            try:
                subscription = Subscription.objects.get(business_id=business_id)
                # Minimum cost is 0.01 for text
                if subscription.credits < 0.01:
                    return JsonResponse({'error': 'Insufficient credits. Please top up.'}, status=402)
                
                if not subscription.is_active:
                    return JsonResponse({'error': 'Subscription is inactive.'}, status=403)
                    
            except Subscription.DoesNotExist:
                return JsonResponse({'error': 'Subscription not found for this business.'}, status=404)

        response = self.get_response(request)
        return response
