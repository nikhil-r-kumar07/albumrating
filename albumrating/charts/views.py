from django.shortcuts import render
from django.db.models import Avg, Count
from albums.models import Album

# Albums need at least this many ratings to appear on the chart.
MIN_RATINGS = 2

def index(request):
    template_data = {}
    template_data['title'] = 'Charts'
    template_data['albums'] = (Album.objects
        .annotate(average=Avg('review__rating'), ratings=Count('review__rating'))
        .filter(ratings__gte=MIN_RATINGS)
        .order_by('-average', '-ratings', 'name')[:50])
    template_data['min_ratings'] = MIN_RATINGS
    return render(request, 'charts/index.html', {'template_data': template_data})
