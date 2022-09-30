import binascii
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from hamstery.utils import GET, list_dir_and_file, list_root_storages, need_authentication
import base64
from pathlib import Path


@GET
@need_authentication
def media_list_view(request, path):
    try:
        path = base64.b64decode(path).decode('utf-8')
        path = Path(path)
        if not path.exists():
            return HttpResponseBadRequest('path does not exist')
        return JsonResponse(list_dir_and_file(path))
    except binascii.Error:
        return HttpResponseBadRequest('path is not properly base64 encoded')


@GET
@need_authentication
def media_list_root_view(request):
    return JsonResponse({'path': list_root_storages(), 'file': []})
