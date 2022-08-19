from django import forms

class TMDBForm(forms.Form):
    tmdb_id = forms.IntegerField()

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
