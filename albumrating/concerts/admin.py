from django.contrib import admin
from .models import Concert

class ConcertAdmin(admin.ModelAdmin):
    list_display = ['artist_name', 'user', 'date', 'venue', 'rating']

admin.site.register(Concert, ConcertAdmin)
