from django.shortcuts import render
from django.db.models import Avg, Max
from albums.models import Album, Review

# Create your views here.
def index(request):
    template_data = {}
    template_data['title'] = 'Improve Ya Music'
    if request.user.is_authenticated:
        template_data['my_reviews'] = (Review.objects
            .filter(user=request.user)
            .select_related('album', 'album__artist')
            .order_by('-date')[:8])
    template_data['albums'] = (Album.objects
        .annotate(last_review=Max('review__date'), average=Avg('review__rating'))
        .filter(last_review__isnull=False)
        .order_by('-last_review')[:8])
    return render(request, 'home/index.html', {'template_data' : template_data})
def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html', {'template_data' : template_data})