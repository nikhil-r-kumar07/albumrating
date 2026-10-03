from django import forms
from django.contrib.auth.models import User

MAX_AVATAR_MB = 5

class UserDetailsForm(forms.ModelForm):
    # Username uniqueness and allowed characters are checked by Django automatically.
    avatar = forms.ImageField(required=False, label='Profile picture',
                              widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp,image/gif'}))
    remove_avatar = forms.BooleanField(required=False, label='Remove current picture')
    bio = forms.CharField(max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 3}))
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_avatar(self):
        # forms.ImageField already rejects files that aren't real images.
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > MAX_AVATAR_MB * 1024 * 1024:
            raise forms.ValidationError('That picture is too big. Please use one under ' + str(MAX_AVATAR_MB) + ' MB.')
        return avatar
