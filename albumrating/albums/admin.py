from django.contrib import admin
from .models import Album, Review, Artist, ArtistReview, Comment, CommentReport

class AlbumAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Album, AlbumAdmin)
admin.site.register(Review)
admin.site.register(Artist)
admin.site.register(ArtistReview)

class CommentReportInline(admin.TabularInline):
    model = CommentReport
    extra = 0
    readonly_fields = ['user', 'date']

class CommentAdmin(admin.ModelAdmin):
    # Hidden comments (auto-hidden after reports) show first. Untick "hidden" to restore one.
    list_display = ['date', 'user', 'text', 'reports', 'hidden']
    list_filter = ['hidden']
    list_editable = ['hidden']
    search_fields = ['text', 'user__username']
    ordering = ['-hidden', '-date']
    inlines = [CommentReportInline]
    def reports(self, obj):
        return obj.commentreport_set.count()
admin.site.register(Comment, CommentAdmin)
