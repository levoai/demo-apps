import json
from django.http import JsonResponse
from .encryption import decrypt, encrypt

_HEALTH_PATH = '/payments/api/payments/health'
_PAYMENTS_PATH = '/payments/api/payments/'


class EncryptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith(_PAYMENTS_PATH) or request.path == _HEALTH_PATH:
            return self.get_response(request)

        # Decrypt request body: {"enc_data": "<base64-AES>"} → plain JSON bytes
        if request.method in ('POST', 'PUT', 'PATCH'):
            try:
                raw = request.body
                payload = json.loads(raw)
                enc_data = payload.get('enc_data')
                if enc_data is None:
                    return JsonResponse(
                        {'error': 'missing_enc_data',
                         'detail': "Request body must contain 'enc_data' field"},
                        status=400)
                decrypted = decrypt(enc_data)
                request._body = decrypted.encode('utf-8')
            except (json.JSONDecodeError, KeyError):
                return JsonResponse({'error': 'invalid_request_body'}, status=400)
            except Exception:
                return JsonResponse(
                    {'error': 'decryption_failed',
                     'detail': 'Could not decrypt enc_data'},
                    status=400)

        response = self.get_response(request)

        # Encrypt response body → {"enc_data": "<base64-AES>"}
        try:
            plain = response.content.decode('utf-8')
            enc_data = encrypt(plain)
            return JsonResponse({'enc_data': enc_data}, status=response.status_code)
        except Exception:
            return response
