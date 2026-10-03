from django.contrib import admin
from .models import Request

class RequestAdmin(admin.ModelAdmin):
    list_display = ['date', 'user', 'category', 'short_message', 'status']
    list_filter = ['status', 'category']
    list_editable = ['status']
    search_fields = ['message']
    ordering = ['-date']
    def short_message(self, obj):
        return obj.message[:80]
admin.site.register(Request, RequestAdmin)
