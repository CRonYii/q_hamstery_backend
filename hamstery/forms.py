from django import forms


class TMDBForm(forms.Form):
    tmdb_id = forms.IntegerField()


class DownloadForm(forms.Form):
    url = forms.CharField(required=False)
    torrent = forms.FileField(required=False)

class ImportForm(forms.Form):
    path = forms.CharField()


class SeasonSearchForm(forms.Form):
    query = forms.CharField()
    indexer_id = forms.CharField()
    offset = forms.IntegerField(required=False)
    exclude = forms.CharField(required=False)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
