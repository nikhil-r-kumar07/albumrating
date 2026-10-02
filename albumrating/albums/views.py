from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Album, Review
from django.db.models import Avg, Count

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        albums = Album.objects.filter(name__icontains=search_term)
    else:
        albums = Album.objects.all()
    template_data = {}
    template_data['title'] = 'Albums'
    template_data['albums'] = albums
    return render(request, 'albums/index.html',
                  {'template_data': template_data})
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