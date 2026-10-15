from django.contrib import admin
from .models import TierList, Tier, TierItem

class TierInline(admin.TabularInline):
    model = Tier
    extra = 0

class TierItemInline(admin.TabularInline):
    model = TierItem
    extra = 0

class TierListAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'updated']
    inlines = [TierInline, TierItemInline]

admin.site.register(TierList, TierListAdmin)
