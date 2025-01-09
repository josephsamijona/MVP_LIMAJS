from django.shortcuts import redirect
from django.contrib.auth import logout

class PassengerAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.path.startswith('/passenger/'):
            if request.user.user_type != 'PASSENGER':
                logout(request)
                return redirect('passenger_login')
        return self.get_response(request)