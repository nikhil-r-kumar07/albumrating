from django import forms
from django.utils import timezone
from .models import Concert

class ConcertForm(forms.ModelForm):
    # The star rating comes from the shared star picker, so it's read separately in the view.
    class Meta:
        model = Concert
        fields = ['artist_name', 'tour', 'venue', 'city', 'date', 'how', 'review']
        labels = {
            'artist_name': 'Artist',
            'tour': 'Tour or event',
            'how': 'How did you see it?',
            'review': 'Your review',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'how': forms.RadioSelect,
            'review': forms.Textarea(attrs={'rows': 6}),
            'artist_name': forms.TextInput(attrs={'list': 'artist-names', 'autocomplete': 'off'}),
        }

    def clean_artist_name(self):
        return self.cleaned_data['artist_name'].strip()

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.localdate():
            raise forms.ValidationError("That date hasn't happened yet. Log the show after you've seen it.")
        return date
