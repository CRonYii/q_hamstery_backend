from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from hamstery.utils import JSON, POST, need_authentication, validate_params

from ..forms import LoginForm


@csrf_exempt
@POST
@JSON
@validate_params(LoginForm)
def login_view(request):
    username = request.data['username']
    password = request.data['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponse('Ok')
    else:
        return HttpResponseBadRequest('Invalid credentials')


def logout_view(request):
    logout(request)
    return HttpResponse('Ok')


@need_authentication
def test_auth_view(request):
    return JsonResponse({'id': request.user.id, 'username': request.user.username})
