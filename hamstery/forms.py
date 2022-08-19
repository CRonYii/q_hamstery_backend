from django import forms

class TMDBForm(forms.Form):
    tmdb_id = forms.IntegerField()
