import base64
import json
import os
import re
from functools import wraps
from pathlib import Path
from typing import Sequence

import cn2an
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

def tree_media(path):
    all_dirs = []
    all_files = []
    for (dirpath, dirnames, filenames) in os.walk(os.path.abspath(path)):
        dirs = [[dirpath, dir] for dir in dirnames]
        files = [[dirpath, filename] for filename in filenames]
        all_dirs = all_dirs + dirs
        all_files = all_files + files
    return {
        'dirs': all_dirs,
        'files': all_files,
    }


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
            'ext4' or x.fstype == 'NTFS' or x.fstype == 'btrfs']


def is_subdirectory(parent: str, child: str):
    parent = Path(parent)
    child = Path(child)
    return parent in child.parents


class Result:

    def __init__(self, success, payload=None):
        self.success = success
        self.multi = False
        self.__payload = payload

    def agg(self, result):
        if result.success is not self.success:
            if self.success is True:
                self.success = False
                self.__payload = None
            else:
                return self
        if self.__payload is None:
            self.__payload = result.data()
        else:
            if self.multi is True:
                self.__payload = self.__payload + result.data()
            else:
                self.multi = True
                self.__payload = [self.__payload, result.data()]
        return self

    def data(self):
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


def success(data=None) -> Result:
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


SUPPLEMENTAL_FILE_RE = re.compile(r'.*?\.(ass|srt)$')


def is_supplemental_file_extension(name):
    return SUPPLEMENTAL_FILE_RE.match(name)


EPISODE_NUMBER_RE = re.compile(
    r'(?:[Ee][Pp]|[ E第【[])(\d{2,4}|[零一二三四五六七八九十百千]{1,6})(v\d)?[ 話话回集\].】]')


def get_episode_number_from_title(title: str) -> int:
    try:
        ep = int(title)
        return ep
    except ValueError:
        pass

    match = EPISODE_NUMBER_RE.search(title)
    if not match:
        return None

    ep = match.group(1)
    try:
        ep = int(ep)
        return ep
    except ValueError:
        pass

    return cn2an.cn2an(ep, mode='smart')


def get_valid_filename(s: str) -> str:
    return re.sub(r"(?u)[^-\w.]", "", s)
