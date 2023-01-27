import base64
from pathlib import Path

from django.http import HttpResponseBadRequest, JsonResponse

from hamstery.forms import ListMediaForm
from hamstery.utils import (GET, list_dir_and_file, list_root_storages,
                            need_authentication, validate_params)


@GET
@need_authentication
@validate_params(ListMediaForm)
def media_list_root_view(request):
    if request.data['path'] != '':
        path = base64.b64decode(request.data['path']).decode('utf-8')
        path = Path(path)
        if not path.exists():
            return HttpResponseBadRequest('path does not exist')
        return JsonResponse(list_dir_and_file(path))
    else:
        return JsonResponse({'path': list_root_storages(), 'file': []})
