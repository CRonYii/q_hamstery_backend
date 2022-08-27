import json
from django import forms
from django.http import JsonResponse, HttpResponseNotFound
from typing import Sequence
from functools import wraps
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
import os
import re


def validate_directory_exist(dir):
    if not os.path.isdir(dir):
        raise ValidationError('directory "%s" does not exist' % dir,
                              params={'dir': dir})


def list_dir(path) -> Sequence[Sequence[str]]:
    for (dirpath, dirnames, _) in os.walk(path):
        return [[dirpath, dir] for dir in dirnames]


class Result:

    def __init__(self, success, payload):
        self.success = success
        self.payload = payload

    def agg(self, result):
        if result.success is False:
            if self.success is True:
                self.success = False
                self.payload = []
            self.payload.append(result.payload)
        return self

    def into_response(self):
        if self.success is True:
            return Response(self.payload)
        else:
            return Response(self.payload, status=status.HTTP_400_BAD_REQUEST)

    def __str__(self):
        if self.success:
            return 'Ok(%s)' % self.payload
        else:
            return 'Err(%s)' % self.payload


def value_or(dict: dict, key, default):
    value = dict.get(key, default)
    if value is None:
        return default
    return value


def success(data) -> Result:
    return Result(True, data)


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