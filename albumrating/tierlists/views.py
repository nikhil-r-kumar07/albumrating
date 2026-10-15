import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db.models import Max
from albums.models import Album
from profiles.views import back_to
from .models import TierList, Tier, TierItem, DEFAULT_TIERS

MAX_TIERS = 10

def next_tray_position(tier_list):
    return (tier_list.items.filter(tier=None).aggregate(Max('position'))['position__max'] or 0) + 1

def rows_for(tier_list):
    # [(tier, [items...]), ...] followed by (None, [unranked items...]) for the template.
    items = list(tier_list.items.select_related('album', 'album__artist'))
    rows = [(tier, [item for item in items if item.tier_id == tier.id]) for tier in tier_list.tiers.all()]
    tray = [item for item in items if item.tier_id is None]
    return rows, tray

@login_required
def index(request):
    template_data = {}
    template_data['title'] = 'My tier lists'
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()[:100]
        if title:
            tier_list = TierList.objects.create(user=request.user, title=title,
                                                description=request.POST.get('description', '').strip()[:500])
            Tier.objects.bulk_create([Tier(tier_list=tier_list, label=label, position=number)
                                      for number, label in enumerate(DEFAULT_TIERS, start=1)])
            return redirect('tierlists.show', id=tier_list.id)
        template_data['error'] = 'Give your tier list a title.'
    template_data['tier_lists'] = (TierList.objects.filter(user=request.user)
        .prefetch_related('items__album').order_by('-updated'))
    return render(request, 'tierlists/index.html', {'template_data': template_data})

def show(request, id):
    # Anyone can view a tier list (so it can be shared); only its owner can change it.
    tier_list = get_object_or_404(TierList.objects.select_related('user'), id=id)
    rows, tray = rows_for(tier_list)
    template_data = {}
    template_data['title'] = tier_list.title
    template_data['tier_list'] = tier_list
    template_data['rows'] = rows
    template_data['tray'] = tray
    template_data['item_count'] = len(tray) + sum(len(items) for tier, items in rows)
    template_data['is_owner'] = request.user == tier_list.user
    if template_data['is_owner']:
        template_data['can_add_tier'] = len(rows) < MAX_TIERS
        on_list = tier_list.items.values('album_id')
        template_data['reviewed_left'] = (request.user.review_set.exclude(album_id__in=on_list).count())
    return render(request, 'tierlists/show.html', {'template_data': template_data})

@login_required
@require_POST
def arrange(request, id):
    # Saves the whole board at once. The page sends {"rows": [{"tier": 3, "items": [7, 9]}, {"tier": null, "items": [...]}]}
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    try:
        rows = [(row.get('tier'), list(row['items'])) for row in json.loads(request.body)['rows']]
    except (ValueError, KeyError, TypeError, AttributeError):
        return HttpResponseBadRequest('Bad data')
    tiers = {tier.id: tier for tier in tier_list.tiers.all()}
    items = {item.id: item for item in tier_list.items.all()}
    changed = []
    for tier_id, item_ids in rows:
        tier = tiers.get(tier_id) if isinstance(tier_id, int) else None
        if tier_id is not None and tier is None:
            return HttpResponseBadRequest('Unknown tier')
        for position, item_id in enumerate(item_ids, start=1):
            item = items.get(item_id) if isinstance(item_id, int) else None
            if item is None:
                continue  # removed in another tab; ignore it
            item.tier = tier
            item.position = position
            changed.append(item)
    TierItem.objects.bulk_update(changed, ['tier', 'position'])
    tier_list.save()  # bumps "updated"
    return JsonResponse({'ok': True})

@login_required
@require_POST
def add(request):
    # The tier list is picked from a dropdown on the album page. New albums wait in the unranked tray.
    tier_list = get_object_or_404(TierList, id=request.POST.get('tier_list', 0) or 0, user=request.user)
    album = get_object_or_404(Album, id=request.POST.get('album', 0) or 0)
    if tier_list.items.filter(album=album).exists():
        messages.success(request, album.name + ' is already on "' + tier_list.title + '".')
    else:
        TierItem.objects.create(tier_list=tier_list, album=album, position=next_tray_position(tier_list))
        tier_list.save()
        messages.success(request, 'Added ' + album.name + ' to "' + tier_list.title + '". Rank it on the tier list page.')
    return back_to(request, '/tierlists/' + str(tier_list.id) + '/')

@login_required
@require_POST
def add_reviewed(request, id):
    # Drop every album you've reviewed (and that isn't on the list yet) into the unranked tray.
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    on_list = tier_list.items.values('album_id')
    album_ids = (request.user.review_set.exclude(album_id__in=on_list)
                 .order_by('-rating', 'album__name').values_list('album_id', flat=True))
    start = next_tray_position(tier_list)
    TierItem.objects.bulk_create([TierItem(tier_list=tier_list, album_id=album_id, position=start + number)
                                  for number, album_id in enumerate(album_ids)])
    tier_list.save()
    messages.success(request, 'Added ' + str(len(album_ids)) + ' album' + ('' if len(album_ids) == 1 else 's') + ' to the unranked tray.')
    return redirect('tierlists.show', id=id)

@login_required
@require_POST
def remove_item(request, id, item_id):
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    get_object_or_404(TierItem, id=item_id, tier_list=tier_list).delete()
    tier_list.save()
    if request.headers.get('X-Requested-With') == 'fetch':
        return JsonResponse({'ok': True})
    return redirect('tierlists.show', id=id)

@login_required
@require_POST
def update(request, id):
    # Title, description and tier names, all from the "Edit tier list" form.
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    title = request.POST.get('title', '').strip()[:100]
    if title:
        tier_list.title = title
        tier_list.description = request.POST.get('description', '').strip()[:500]
        tier_list.save()
    for tier in tier_list.tiers.all():
        label = request.POST.get('tier-' + str(tier.id), '').strip()[:20]
        if label and label != tier.label:
            tier.label = label
            tier.save(update_fields=['label'])
    messages.success(request, 'Tier list saved.')
    return redirect('tierlists.show', id=id)

@login_required
@require_POST
def add_tier(request, id):
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    if tier_list.tiers.count() < MAX_TIERS:
        position = (tier_list.tiers.aggregate(Max('position'))['position__max'] or 0) + 1
        label = request.POST.get('label', '').strip()[:20] or 'New'
        Tier.objects.create(tier_list=tier_list, label=label, position=position)
    return redirect('tierlists.show', id=id)

@login_required
@require_POST
def delete_tier(request, id, tier_id):
    # Albums in the deleted row go back to the unranked tray.
    tier_list = get_object_or_404(TierList, id=id, user=request.user)
    tier = get_object_or_404(Tier, id=tier_id, tier_list=tier_list)
    start = next_tray_position(tier_list)
    for number, item in enumerate(tier.items.all()):
        item.tier = None
        item.position = start + number
        item.save(update_fields=['tier', 'position'])
    tier.delete()
    for number, remaining in enumerate(tier_list.tiers.all(), start=1):
        if remaining.position != number:
            remaining.position = number
            remaining.save(update_fields=['position'])
    messages.success(request, 'Removed the "' + tier.label + '" row.')
    return redirect('tierlists.show', id=id)

@login_required
@require_POST
def delete(request, id):
    get_object_or_404(TierList, id=id, user=request.user).delete()
    messages.success(request, 'Tier list deleted.')
    return redirect('tierlists.index')
