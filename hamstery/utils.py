import base64
import json
import os
import re
from functools import wraps
from typing import Sequence

import psutil
from django import forms
from django.core.exceptions import ValidationError
from django.http import (HttpResponseBadRequest, HttpResponseNotFound,
                         JsonResponse)
from rest_framework import status
from rest_framework.response import Response


def validate_directory_exist(dir):
    if not os.path.isdir(dir):
        raise ValidationError('directory "%s" does not exist' % dir,
                              params={'dir': dir})


def list_dir(path) -> Sequence[Sequence[str]]:
    for (dirpath, dirnames, _) in os.walk(path):
        return [[dirpath, dir] for dir in dirnames]


def list_file(path) -> Sequence[Sequence[str]]:
    for (dirpath, _, filenames) in os.walk(path):
        return [[dirpath, filename] for filename in filenames]


def make_file_uri_obj(path, name):
    return {
        'key': base64.b64encode(os.path.join(path, name).encode('utf-8')).decode('utf-8'),
        'path': path,
        'title': name
    }


def list_dir_and_file(path):
    for (dirpath, dirnames, filenames) in os.walk(path):
        return {
            'path': [make_file_uri_obj(dirpath, dir) for dir in dirnames],
            'file': [make_file_uri_obj(dirpath, filename) for filename in filenames]
        }


def list_root_storages():
    return [make_file_uri_obj('', x.mountpoint) for x in psutil.disk_partitions() if x.fstype ==
     'ext4' or x.fstype == 'NTFS']


class Result:

    def __init__(self, success, payload=None, multi=False):
        self.success = success
        self.multi = multi
        if payload is not None:
            self.__payload = [payload]
        else:
            self.__payload = None

    def agg(self, result):
        if result.success is False:
            if self.success is True:
                self.success = False
                self.__payload = []
        if result.success is not self.success:
            if self.success is True:
                self.success = False
                self.__payload = []
            else:
                return self
        if self.__payload is None:
            if self.multi:
                self.__payload = [result.data()]
            else:
                self.__payload = result.data()
        else:
            self.multi = True
            self.__payload = self.__payload + result.data()
        return self

    def data(self):
        if not self.multi and self.__payload is not None:
            return self.__payload[0]
        return self.__payload

    def into_response(self):
        if self.success is True:
            return Response(self.data())
        else:
            return Response(self.data(), status=status.HTTP_400_BAD_REQUEST)

    def __str__(self):
        if self.success:
            return 'Ok(%s)' % self.data()
        else:
            return 'Err(%s)' % self.data()


def value_or(dict: dict, key, default):
    value = dict.get(key, default)
    if value is None:
        return default
    return value


def success(data=None, multi=False) -> Result:
    return Result(True, data, multi)


def failure(errors) -> Result:
    return Result(False, errors)


def JSON(api):
    @wraps(api)
    def _wrapped_api(request, *args, **kwargs):
        if request.method == 'POST' and request.content_type == 'application/json':
            request.JSON = json.loads(request.body)
        return api(request, *args, **kwargs)
    return _wrapped_api


def GET(api):
    @wraps(api)
    def _wrapped_api(request, *args, **kwargs):
        if request.method == 'GET':
            return api(request, *args, **kwargs)
        return HttpResponseNotFound()
    return _wrapped_api


def POST(api):
    @wraps(api)
    def _wrapped_api(request, *args, **kwargs):
        if request.method == 'POST':
            return api(request, *args, **kwargs)
        return HttpResponseNotFound()
    return _wrapped_api


def need_authentication(api):
    @wraps(api)
    def _wrapped_api(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseBadRequest('Invalid credentials')
        else:
            return api(request, *args, **kwargs)
    return _wrapped_api


def validate_params(Form: forms.Form):
    def _wrapped_api(api):
        @wraps(api)
        def _wrapped_wrapped_api(request, *args, **kwargs):
            form = None
            if request.method == 'GET':
                form = Form(request.GET)
            elif request.method == 'POST':
                if request.content_type == 'application/json' and request.JSON is not None:
                    form = Form(request.JSON)
                else:
                    form = Form(request.POST)
            if form is None:
                return JsonResponse('No payload', status=400)
            if form.is_valid() is False:
                return JsonResponse(dict(form.errors.items()), status=400)
            request.data = form.cleaned_data
            return api(request, *args, **kwargs)
        return _wrapped_wrapped_api
    return _wrapped_api


VIDEO_FILE_RE = re.compile(r'.*?\.(mp4|mkv|flv|avi|rmvb|m4p|m4v)$')


def is_video_extension(name):
    return VIDEO_FILE_RE.match(name)
