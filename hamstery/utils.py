from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
import os


def validate_directory_exist(dir):
    if not os.path.isdir(dir):
        raise ValidationError('directory "%s" does not exist' % dir,
                              params={'dir': dir})


def success(data):
    return [True, data]


def failure(errors):
    return [False, errors]


def HamsteryResponse(result):
    [succeed, payload] = result
    if succeed is True:
        return Response(payload)
    else:
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)
