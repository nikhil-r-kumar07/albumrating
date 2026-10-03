from django.utils import timezone
from .stats import year_in_review_open

def unread_notifications(request):
    # Makes {{ unread_notifications }} available in every template, for the navbar badge,
    # and {{ year_in_review_open }} for the Dec 25-31 year-in-review banner.
    context = {'unread_notifications': 0, 'year_in_review_open': year_in_review_open(timezone.localdate())}
    if request.user.is_authenticated:
        context['unread_notifications'] = request.user.notifications.filter(read=False).count()
    return context
