from django import forms


class TMDBForm(forms.Form):
    tmdb_id = forms.IntegerField()


class DownloadForm(forms.Form):
    url = forms.CharField()


class ImportForm(forms.Form):
    path = forms.CharField()


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
