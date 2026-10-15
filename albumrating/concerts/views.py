from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count
from albums.models import Artist
from albums.views import rating_from
from accounts.forms import CustomErrorList
from .forms import ConcertForm
from .models import Concert

def link_artist(concert):
    # Connect the concert to an artist already on the site with the same name (any capitalisation).
    concert.artist = Artist.objects.filter(name__iexact=concert.artist_name).first()

def form_page(request, form, concert=None):
    template_data = {}
    template_data['title'] = 'Edit concert' if concert else 'Log a concert'
    template_data['form'] = form
    template_data['concert'] = concert
    # Keep the stars someone picked if the form comes back with an error.
    template_data['rating'] = rating_from(request) if request.method == 'POST' else (concert.rating if concert else None)
    template_data['artist_names'] = Artist.objects.order_by('name').values_list('name', flat=True)[:500]
    return render(request, 'concerts/form.html', {'template_data': template_data})

@login_required
def index(request):
    return redirect('concerts.user', username=request.user.username)

def user_concerts(request, username):
    person = get_object_or_404(User, username=username)
    concerts = person.concerts.select_related('artist')
    template_data = {}
    template_data['title'] = person.username + "'s concerts"
    template_data['person'] = person
    template_data['is_me'] = request.user == person
    template_data['concerts'] = concerts
    template_data['summary'] = concerts.aggregate(count=Count('id'), average=Avg('rating'),
                                                  artists=Count('artist_name', distinct=True))
    return render(request, 'concerts/user.html', {'template_data': template_data})

@login_required
def create(request):
    if request.method == 'POST':
        form = ConcertForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            concert = form.save(commit=False)
            concert.user = request.user
            concert.rating = rating_from(request)
            link_artist(concert)
            concert.save()
            messages.success(request, 'Logged ' + concert.artist_name + '.')
            return redirect('concerts.show', id=concert.id)
    else:
        # Coming from an artist page (?artist=12) fills in their name.
        artist_id = request.GET.get('artist', '')
        artist = Artist.objects.filter(id=artist_id).first() if artist_id.isdigit() else None
        form = ConcertForm(initial={'artist_name': artist.name if artist else '', 'how': 'live'})
    return form_page(request, form)

def show(request, id):
    concert = get_object_or_404(Concert.objects.select_related('user', 'user__profile', 'artist'), id=id)
    template_data = {}
    template_data['title'] = concert.artist_name + ' live'
    template_data['concert'] = concert
    template_data['is_owner'] = request.user == concert.user
    # Other people who logged the same artist on the same day were probably at the same show.
    template_data['also_there'] = (Concert.objects.filter(artist_name__iexact=concert.artist_name, date=concert.date)
                                   .exclude(id=concert.id).select_related('user', 'user__profile'))
    return render(request, 'concerts/show.html', {'template_data': template_data})

@login_required
def edit(request, id):
    concert = get_object_or_404(Concert, id=id, user=request.user)
    if request.method == 'POST':
        form = ConcertForm(request.POST, instance=concert, error_class=CustomErrorList)
        if form.is_valid():
            concert = form.save(commit=False)
            concert.rating = rating_from(request)
            link_artist(concert)
            concert.save()
            messages.success(request, 'Concert saved.')
            return redirect('concerts.show', id=concert.id)
    else:
        form = ConcertForm(instance=concert)
    return form_page(request, form, concert)

@login_required
@require_POST
def delete(request, id):
    get_object_or_404(Concert, id=id, user=request.user).delete()
    messages.success(request, 'Concert deleted.')
    return redirect('concerts.user', username=request.user.username)
