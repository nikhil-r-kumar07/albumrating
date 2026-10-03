from django.shortcuts import render
from django.db.models import Avg, Count
from albums.models import Album, Artist

# Albums and artists need at least this many ratings to appear on a chart.
MIN_RATINGS = 2

def index(request):
    chart = request.GET.get('chart', 'albums')
    if chart not in ['albums', 'artists']:
        chart = 'albums'
    template_data = {}
    template_data['title'] = 'Charts'
    template_data['chart'] = chart
    template_data['min_ratings'] = MIN_RATINGS
    if chart == 'artists':
        template_data['artists'] = (Artist.objects
            .annotate(average=Avg('artistreview__rating'), ratings=Count('artistreview__rating'))
            .filter(ratings__gte=MIN_RATINGS)
            .order_by('-average', '-ratings', 'name')[:50])
    else:
        albums = (Album.objects
            .annotate(average=Avg('review__rating'), ratings=Count('review__rating'))
            .filter(ratings__gte=MIN_RATINGS))
        year = request.GET.get('year', '')
        if year.isdigit():
            albums = albums.filter(year=int(year))
            template_data['year'] = year
        template_data['albums'] = albums.order_by('-average', '-ratings', 'name')[:50]
        # Only offer years that have at least one rated album.
        template_data['years'] = (Album.objects
            .filter(year__isnull=False, review__rating__isnull=False)
            .values_list('year', flat=True).distinct().order_by('-year'))
    return render(request, 'charts/index.html', {'template_data': template_data})
