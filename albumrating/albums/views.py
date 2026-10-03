from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .models import Album, Review, Artist
from . import musicbrainz
from django.db.models import Avg, Count

def index(request):
    search_term = request.GET.get('search')
    template_data = {}
    template_data['title'] = 'Albums'
    if search_term:
        template_data['results'] = musicbrainz.search_albums(search_term)
    else:
        template_data['albums'] = Album.objects.all()
    return render(request, 'albums/index.html',
                  {'template_data': template_data})
@login_required
def open_album(request, mbid):
    mbid = str(mbid)
    album = Album.objects.filter(mbid=mbid).first()
    if album is None:
        data = musicbrainz.get_album(mbid)
        if data is None:
            raise Http404
        artist, created = Artist.objects.get_or_create(
            mbid=data['artist_mbid'], defaults={'name': data['artist_name']})
        album = Album.objects.create(name=data['name'], artist=artist, year=data['year'],
                                     cover_url=data['cover_url'], mbid=mbid)
    return redirect('albums.show', id=album.id)
def show(request, id):
    album = get_object_or_404(Album, id=id)
    reviews = Review.objects.filter(album=album)
    template_data = {}
    template_data['title'] = album.name
    template_data['album'] = album
    template_data['reviews'] = reviews
    stats = reviews.aggregate(average = Avg('rating'), count = Count('rating'))
    template_data['average'] = stats['average']
    template_data['rating_count'] = stats['count']
    return render(request, 'albums/show.html', {'template_data': template_data})
@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        album = get_object_or_404(Album, id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.album = album
        review.user = request.user
        rating = request.POST.get('rating', '')
        if rating in ['0', '1', '2', '3', '4', '5']:
            review.rating = int(rating)
        else:
            review.rating = None
        review.save()
    return redirect('albums.show', id=id)
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('albums.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'albums/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review.comment = request.POST['comment']
        rating = request.POST.get('rating', '')
        if rating in ['0', '1', '2', '3', '4', '5']:
            review.rating = int(rating)
        else:
            review.rating = None
        review.save()
        return redirect('albums.show', id=id)
    else:
        return redirect('albums.show', id=id)
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('albums.show', id=id)
def artist(request, id):
    artist = get_object_or_404(Artist, id=id)
    albums = Album.objects.filter(artist=artist).annotate(average=Avg('review__rating')).order_by('year')
    template_data = {}
    template_data['title'] = artist.name
    template_data['artist'] = artist
    template_data['albums'] = albums
    return render(request, 'albums/artist.html', {'template_data': template_data})
