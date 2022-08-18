from typing import Sequence
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
import os


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


def success(data):
    return Result(True, data)


def failure(errors):
    return Result(False, errors)
