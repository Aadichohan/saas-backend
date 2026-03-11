import requests

def send_whatsapp_message(business, customer_number, message):
    """
    Sends a WhatsApp message using Meta's Cloud API.
    Uses the business's own phone_number_id and whatsapp_access_token.
    """
    if not business.phone_number_id or not business.whatsapp_access_token:
        print(f"Business {business.id} is missing WhatsApp credentials.")
        return False

    url = f"https://graph.facebook.com/v17.0/{business.phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {business.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_number,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {e}")
        return False
