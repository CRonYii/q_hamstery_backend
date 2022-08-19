from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

from ..forms import LoginForm

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            print(form.errors.items())
            return JsonResponse(dict(form.errors.items()), status=400)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse('Ok')
        else:
            return HttpResponseBadRequest('Invalid credentials')
    return HttpResponseNotFound()


def logout_view(request):
    logout(request)
    return HttpResponse('Ok')