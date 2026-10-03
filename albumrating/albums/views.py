from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Album, Review, Artist, ArtistReview, Comment, CommentReport, ReviewLike
from . import musicbrainz, moderation
from profiles.models import AlbumList, QueueItem
from django.db.models import Avg, Count, Prefetch

def rating_from(request):
    # The star picker sends '0'-'5', or '' when left unrated.
    rating = request.POST.get('rating', '')
    if rating in ['0', '1', '2', '3', '4', '5']:
        return int(rating)
    return None

def with_comments(reviews):
    # Attach each review's visible comments as review.visible_comments, and its like count as review.like_count.
    visible = Comment.objects.filter(hidden=False).select_related('user', 'user__profile').order_by('date')
    return reviews.select_related('user', 'user__profile').annotate(like_count=Count('likes', distinct=True)).prefetch_related(
        Prefetch('comments', queryset=visible, to_attr='visible_comments'))

def my_likes(request, field):
    # IDs of the reviews the current user has liked; field is 'review' or 'artist_review'.
    if not request.user.is_authenticated:
        return set()
    return set(ReviewLike.objects.filter(user=request.user, **{field + '__isnull': False}).values_list(field + '_id', flat=True))

def my_reports(request):
    if not request.user.is_authenticated:
        return set()
    return set(CommentReport.objects.filter(user=request.user).values_list('comment_id', flat=True))

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
    all_reviews = Review.objects.filter(album=album)
    reviews = with_comments(all_reviews)
    template_data = {}
    template_data['my_reports'] = my_reports(request)
    template_data['my_likes'] = my_likes(request, 'review')
    template_data['title'] = album.name
    template_data['album'] = album
    template_data['reviews'] = reviews
    stats = all_reviews.aggregate(average = Avg('rating'), count = Count('rating'))
    template_data['average'] = stats['average']
    template_data['rating_count'] = stats['count']
    if request.user.is_authenticated:
        template_data['my_review'] = reviews.filter(user=request.user).first()
        template_data['my_lists'] = AlbumList.objects.filter(user=request.user).order_by('title')
        template_data['queue_item'] = QueueItem.objects.filter(user=request.user, album=album).first()
    return render(request, 'albums/show.html', {'template_data': template_data})
@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        album = get_object_or_404(Album, id=id)
        review = Review.objects.filter(album=album, user=request.user).first()
        if review is None:
            review = Review(album=album, user=request.user)
        review.comment = request.POST['comment']
        review.rating = rating_from(request)
        review.save()
        # Reviewing an album takes it off your queue.
        if QueueItem.objects.filter(user=request.user, album=album).delete()[0]:
            for number, item in enumerate(request.user.queue.order_by('position'), start=1):
                if item.position != number:
                    item.position = number
                    item.save(update_fields=['position'])
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
        review.rating = rating_from(request)
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
    all_reviews = ArtistReview.objects.filter(artist=artist)
    reviews = with_comments(all_reviews.order_by('-date'))
    template_data['reviews'] = reviews
    template_data['my_reports'] = my_reports(request)
    template_data['my_likes'] = my_likes(request, 'artist_review')
    stats = all_reviews.aggregate(average = Avg('rating'), count = Count('rating'))
    template_data['average'] = stats['average']
    template_data['rating_count'] = stats['count']
    if request.user.is_authenticated:
        template_data['my_review'] = reviews.filter(user=request.user).first()
    return render(request, 'albums/artist.html', {'template_data': template_data})
@login_required
def create_artist_review(request, id):
    if request.method == 'POST' and request.POST.get('comment', '') != '':
        artist = get_object_or_404(Artist, id=id)
        review = ArtistReview.objects.filter(artist=artist, user=request.user).first()
        if review is None:
            review = ArtistReview(artist=artist, user=request.user)
        review.comment = request.POST['comment']
        review.rating = rating_from(request)
        review.save()
    return redirect('albums.artist', id=id)
@login_required
def edit_artist_review(request, id, review_id):
    review = get_object_or_404(ArtistReview, id=review_id, user=request.user)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'albums/edit_artist_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST.get('comment', '') != '':
        review.comment = request.POST['comment']
        review.rating = rating_from(request)
        review.save()
    return redirect('albums.artist', id=id)
@login_required
def delete_artist_review(request, id, review_id):
    if request.method == 'POST':
        review = get_object_or_404(ArtistReview, id=review_id, user=request.user)
        review.delete()
    return redirect('albums.artist', id=id)

def save_comment(request, **parent):
    text = request.POST.get('text', '').strip()[:500]
    if not text:
        return
    if moderation.is_blocked(text):
        messages.error(request, "Your comment wasn't posted because it contains language that isn't allowed here.")
        return
    Comment.objects.create(user=request.user, text=text, **parent)

def comment_page(comment):
    # Where to send someone after they act on a comment: the review it belongs to.
    if comment.review_id:
        return reverse('albums.show', args=[comment.review.album_id]) + '#review-' + str(comment.review_id)
    return reverse('albums.artist', args=[comment.artist_review.artist_id]) + '#artist-review-' + str(comment.artist_review_id)

@login_required
@require_POST
def add_comment(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    save_comment(request, review=review)
    return redirect(reverse('albums.show', args=[review.album_id]) + '#review-' + str(review.id))
@login_required
@require_POST
def add_artist_comment(request, review_id):
    review = get_object_or_404(ArtistReview, id=review_id)
    save_comment(request, artist_review=review)
    return redirect(reverse('albums.artist', args=[review.artist_id]) + '#artist-review-' + str(review.id))
@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    page = comment_page(comment)
    # The commenter, the person whose review it's on, and admins can remove a comment.
    if request.user in (comment.user, comment.parent().user) or request.user.is_staff:
        comment.delete()
    return redirect(page)
@login_required
@require_POST
def report_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.user:
        CommentReport.objects.get_or_create(comment=comment, user=request.user)
        if CommentReport.objects.filter(comment=comment).count() >= moderation.HIDE_AFTER_REPORTS:
            comment.hidden = True
            comment.save()
        messages.success(request, 'Thanks for reporting that comment. It will be reviewed.')
    return redirect(comment_page(comment))
@login_required
@require_POST
def like_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    toggle_like(request.user, review=review)
    return redirect(reverse('albums.show', args=[review.album_id]) + '#review-' + str(review.id))
@login_required
@require_POST
def like_artist_review(request, review_id):
    review = get_object_or_404(ArtistReview, id=review_id)
    toggle_like(request.user, artist_review=review)
    return redirect(reverse('albums.artist', args=[review.artist_id]) + '#artist-review-' + str(review.id))

def toggle_like(user, **target):
    # Like if not liked yet, unlike if already liked. People can't like their own reviews.
    review = target.get('review') or target.get('artist_review')
    if review.user == user:
        return
    like = ReviewLike.objects.filter(user=user, **target).first()
    if like:
        like.delete()
    else:
        ReviewLike.objects.create(user=user, **target)
