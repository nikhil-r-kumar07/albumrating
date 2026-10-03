def unread_notifications(request):
    # Makes {{ unread_notifications }} available in every template, for the navbar badge.
    if request.user.is_authenticated:
        return {'unread_notifications': request.user.notifications.filter(read=False).count()}
    return {'unread_notifications': 0}
