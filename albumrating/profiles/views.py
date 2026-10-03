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
from .models import Profile, AlbumList, ListItem, QueueItem
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
