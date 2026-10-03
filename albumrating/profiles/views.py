import io
import uuid
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Max
from albums.models import Album, Review
from accounts.forms import CustomErrorList
import datetime
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from albums.models import ArtistReview
from .models import Profile, AlbumList, ListItem, QueueItem, Favorite, DiaryEntry, Follow, Notification
from .notify import notify, unnotify
from .forms import UserDetailsForm

# ---------- helpers for ordered items (list items and queue items) ----------

def next_position(items):
    return (items.aggregate(Max('position'))['position__max'] or 0) + 1

def renumber(items):
    # Close gaps after a removal so positions stay 1, 2, 3...
    for number, item in enumerate(items.order_by('position'), start=1):
        if item.position != number:
            item.position = number
            item.save(update_fields=['position'])

def move(items, item, direction):
    # Swap an item with its neighbour above ('up') or below ('down').
    if direction == 'up':
        neighbour = items.filter(position__lt=item.position).order_by('-position').first()
    else:
        neighbour = items.filter(position__gt=item.position).order_by('position').first()
    if neighbour:
        item.position, neighbour.position = neighbour.position, item.position
        item.save(update_fields=['position'])
        neighbour.save(update_fields=['position'])

def back_to(request, fallback):
    # Return to the page the form was on (e.g. an album page), if it's on this site.
    target = request.POST.get('next', '')
    return redirect(target if target.startswith('/') and not target.startswith('//') else fallback)

# ---------- edit profile ----------

def square_jpeg(upload, size=256):
    # Crop to a centred square, shrink to size x size and save as JPEG, so photos are small and uniform.
    image = ImageOps.exif_transpose(Image.open(upload))
    image = ImageOps.fit(image.convert('RGB'), (size, size), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    return ContentFile(buffer.getvalue())

@login_required
def edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    template_data = {}
    template_data['title'] = 'Edit profile'
    template_data['profile'] = profile
    if request.method == 'POST':
        form = UserDetailsForm(request.POST, request.FILES, instance=request.user, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            profile.bio = form.cleaned_data['bio']
            if form.cleaned_data['avatar'] or form.cleaned_data['remove_avatar']:
                if profile.avatar:
                    profile.avatar.delete(save=False)
            if form.cleaned_data['avatar']:
                profile.avatar.save(str(request.user.id) + '_' + uuid.uuid4().hex[:8] + '.jpg',
                                    square_jpeg(form.cleaned_data['avatar']), save=False)
            profile.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profiles.edit')
    else:
        form = UserDetailsForm(instance=request.user, initial={'bio': profile.bio})
    template_data['form'] = form
    return render(request, 'profiles/edit.html', {'template_data': template_data})

# ---------- my reviewed albums ----------

@login_required
def reviews(request):
    template_data = {}
    template_data['title'] = 'Reviews'
    template_data['reviews'] = (Review.objects.filter(user=request.user)
        .select_related('album', 'album__artist').order_by('-date'))
    return render(request, 'profiles/reviews.html', {'template_data': template_data})

# ---------- lists ----------

@login_required
def lists(request):
    template_data = {}
    template_data['title'] = 'My lists'
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()[:100]
        if title:
            album_list = AlbumList.objects.create(user=request.user, title=title,
                                                  description=request.POST.get('description', '').strip()[:500])
            return redirect('profiles.list', id=album_list.id)
        template_data['error'] = 'Give your list a title.'
    template_data['lists'] = (AlbumList.objects.filter(user=request.user)
        .prefetch_related('items__album').order_by('-updated'))
    return render(request, 'profiles/lists.html', {'template_data': template_data})

def list_detail(request, id):
    # Anyone can view a list (so it can be shared); only its owner can change it.
    album_list = get_object_or_404(AlbumList, id=id)
    template_data = {}
    template_data['title'] = album_list.title
    template_data['list'] = album_list
    template_data['items'] = album_list.items.select_related('album', 'album__artist')
    template_data['is_owner'] = request.user == album_list.user
    return render(request, 'profiles/list_detail.html', {'template_data': template_data})

@login_required
@require_POST
def list_update(request, id):
    album_list = get_object_or_404(AlbumList, id=id, user=request.user)
    title = request.POST.get('title', '').strip()[:100]
    if title:
        album_list.title = title
        album_list.description = request.POST.get('description', '').strip()[:500]
        album_list.save()
        messages.success(request, 'List details saved.')
    return redirect('profiles.list', id=id)

@login_required
@require_POST
def list_delete(request, id):
    album_list = get_object_or_404(AlbumList, id=id, user=request.user)
    album_list.delete()
    messages.success(request, 'List deleted.')
    return redirect('profiles.lists')

@login_required
@require_POST
def list_add(request):
    # The list is picked from a dropdown on the album page, so it comes in the form data.
    album_list = get_object_or_404(AlbumList, id=request.POST.get('list', 0) or 0, user=request.user)
    id = album_list.id
    album = get_object_or_404(Album, id=request.POST.get('album', 0) or 0)
    if album_list.items.filter(album=album).exists():
        messages.success(request, album.name + ' is already in "' + album_list.title + '".')
    else:
        ListItem.objects.create(album_list=album_list, album=album, position=next_position(album_list.items))
        album_list.save()  # bumps "updated"
        messages.success(request, 'Added ' + album.name + ' to "' + album_list.title + '".')
    return back_to(request, '/profile/lists/' + str(id) + '/')

@login_required
@require_POST
def list_item(request, id, item_id):
    # Move an album up/down in a list, or remove it.
    album_list = get_object_or_404(AlbumList, id=id, user=request.user)
    item = get_object_or_404(ListItem, id=item_id, album_list=album_list)
    action = request.POST.get('action')
    if action in ['up', 'down']:
        move(album_list.items.all(), item, action)
    elif action == 'remove':
        item.delete()
        renumber(album_list.items.all())
    album_list.save()
    if action == 'remove':
        return redirect('profiles.list', id=id)
    return redirect('/profile/lists/' + str(id) + '/#item-' + str(item_id))

# ---------- queue ----------

@login_required
def queue(request):
    template_data = {}
    template_data['title'] = 'My queue'
    template_data['items'] = request.user.queue.select_related('album', 'album__artist')
    return render(request, 'profiles/queue.html', {'template_data': template_data})

@login_required
@require_POST
def queue_add(request):
    album = get_object_or_404(Album, id=request.POST.get('album', 0) or 0)
    if not request.user.queue.filter(album=album).exists():
        QueueItem.objects.create(user=request.user, album=album, position=next_position(request.user.queue))
        messages.success(request, 'Added ' + album.name + ' to your queue.')
    return back_to(request, '/profile/queue/')

@login_required
@require_POST
def queue_item(request, item_id):
    # Move an album up/down in the queue, or remove it.
    item = get_object_or_404(QueueItem, id=item_id, user=request.user)
    action = request.POST.get('action')
    if action in ['up', 'down']:
        move(request.user.queue.all(), item, action)
    elif action == 'remove':
        item.delete()
        renumber(request.user.queue.all())
        return back_to(request, '/profile/queue/')
    return redirect('/profile/queue/#item-' + str(item_id))

# ---------- favourites (top 4) ----------

MAX_FAVORITES = 4

@login_required
@require_POST
def favorite_toggle(request):
    album = get_object_or_404(Album, id=request.POST.get('album', 0) or 0)
    favorite = request.user.favorites.filter(album=album).first()
    if favorite:
        favorite.delete()
        renumber(request.user.favorites.all())
        messages.success(request, album.name + ' was removed from your top 4.')
    elif request.user.favorites.count() >= MAX_FAVORITES:
        messages.error(request, 'Your top 4 is full. Remove one from your profile first.')
    else:
        Favorite.objects.create(user=request.user, album=album, position=next_position(request.user.favorites))
        messages.success(request, 'Added ' + album.name + ' to your top 4.')
    return back_to(request, '/profile/u/' + request.user.username + '/')

@login_required
@require_POST
def favorite_item(request, item_id):
    # Move a favourite left/right on your profile, or remove it.
    item = get_object_or_404(Favorite, id=item_id, user=request.user)
    action = request.POST.get('action')
    if action in ['up', 'down']:
        move(request.user.favorites.all(), item, action)
    elif action == 'remove':
        item.delete()
        renumber(request.user.favorites.all())
    return redirect('profiles.public', username=request.user.username)

# ---------- listening diary ----------

@login_required
@require_POST
def log_listen(request):
    album = get_object_or_404(Album, id=request.POST.get('album', 0) or 0)
    try:
        listened_on = datetime.date.fromisoformat(request.POST.get('listened_on', ''))
    except ValueError:
        listened_on = timezone.localdate()
    if listened_on > timezone.localdate():
        listened_on = timezone.localdate()  # no logging listens in the future
    DiaryEntry.objects.create(user=request.user, album=album, listened_on=listened_on,
                              note=request.POST.get('note', '').strip()[:280])
    messages.success(request, 'Logged a listen of ' + album.name + '.')
    return back_to(request, '/profile/diary/')

@login_required
def diary(request):
    template_data = {}
    template_data['title'] = 'Diary'
    template_data['entries'] = request.user.diary.select_related('album', 'album__artist')
    return render(request, 'profiles/diary.html', {'template_data': template_data})

@login_required
@require_POST
def diary_delete(request, entry_id):
    get_object_or_404(DiaryEntry, id=entry_id, user=request.user).delete()
    return back_to(request, '/profile/diary/')

# ---------- public profiles and following ----------

def public(request, username):
    person = get_object_or_404(User, username=username)
    template_data = {}
    template_data['title'] = person.username
    template_data['person'] = person
    template_data['profile'] = Profile.objects.filter(user=person).first()
    template_data['is_me'] = request.user == person
    template_data['is_following'] = request.user.is_authenticated and Follow.objects.filter(follower=request.user, following=person).exists()
    template_data['followers'] = person.follower_set.count()
    template_data['following'] = person.following_set.count()
    template_data['review_count'] = person.review_set.count()
    template_data['favorites'] = person.favorites.select_related('album', 'album__artist')
    template_data['reviews'] = person.review_set.select_related('album', 'album__artist').order_by('-date')[:8]
    template_data['diary'] = person.diary.select_related('album', 'album__artist')[:10]
    template_data['lists'] = person.album_lists.prefetch_related('items__album').order_by('-updated')
    return render(request, 'profiles/public.html', {'template_data': template_data})

@login_required
@require_POST
def follow_toggle(request, username):
    person = get_object_or_404(User, username=username)
    if person != request.user:
        follow = Follow.objects.filter(follower=request.user, following=person).first()
        if follow:
            follow.delete()
            unnotify(person, request.user, 'follow')
        else:
            Follow.objects.create(follower=request.user, following=person)
            notify(person, request.user, 'follow')
    return back_to(request, '/profile/u/' + person.username + '/')

@login_required
def people(request):
    query = request.GET.get('q', '').strip()
    people = (User.objects.exclude(id=request.user.id).select_related('profile')
              .annotate(reviews=Count('review', distinct=True)).order_by('username'))
    if query:
        people = people.filter(username__icontains=query)
    template_data = {}
    template_data['title'] = 'People'
    template_data['query'] = query
    template_data['people'] = people[:100]
    template_data['following_ids'] = set(request.user.following_set.values_list('following_id', flat=True))
    return render(request, 'profiles/people.html', {'template_data': template_data})

@login_required
def feed(request):
    # Recent activity from people you follow: reviews, artist reviews, listens and new lists.
    ids = list(request.user.following_set.values_list('following_id', flat=True))
    events = []
    for review in (Review.objects.filter(user__in=ids).select_related('user', 'user__profile', 'album', 'album__artist')
                   .order_by('-date')[:30]):
        events.append({'kind': 'review', 'when': review.date, 'user': review.user, 'item': review})
    for review in (ArtistReview.objects.filter(user__in=ids).select_related('user', 'user__profile', 'artist')
                   .order_by('-date')[:30]):
        events.append({'kind': 'artist_review', 'when': review.date, 'user': review.user, 'item': review})
    for entry in (DiaryEntry.objects.filter(user__in=ids).select_related('user', 'user__profile', 'album', 'album__artist')
                  .order_by('-created')[:30]):
        events.append({'kind': 'listen', 'when': entry.created, 'user': entry.user, 'item': entry})
    for album_list in (AlbumList.objects.filter(user__in=ids).select_related('user', 'user__profile')
                       .prefetch_related('items__album').order_by('-created')[:30]):
        events.append({'kind': 'list', 'when': album_list.created, 'user': album_list.user, 'item': album_list})
    events.sort(key=lambda event: event['when'], reverse=True)
    template_data = {}
    template_data['title'] = 'Feed'
    template_data['events'] = events[:40]
    template_data['following_count'] = len(ids)
    return render(request, 'profiles/feed.html', {'template_data': template_data})

# ---------- notifications ----------

@login_required
def notifications(request):
    items = list(request.user.notifications.select_related(
        'actor', 'actor__profile', 'review__album', 'artist_review__artist', 'comment')[:50])
    # Opening the page marks everything as read; the list still shows which ones were new.
    request.user.notifications.filter(read=False).update(read=True)
    template_data = {}
    template_data['title'] = 'Notifications'
    template_data['notifications'] = items
    return render(request, 'profiles/notifications.html', {'template_data': template_data})
