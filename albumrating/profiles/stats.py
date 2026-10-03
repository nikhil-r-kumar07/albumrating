import datetime
from collections import Counter, defaultdict
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from albums.models import Review, ArtistReview, ReviewLike, Track
from .models import DiaryEntry

RATING_STEPS = [Decimal(half) / 2 for half in range(0, 11)]  # 0, 0.5, ... 5

def _album_minutes(album_ids):
    # Running time per album in minutes, for albums whose tracklist has been loaded.
    totals = Track.objects.filter(album_id__in=album_ids).values('album_id').annotate(ms=Sum('length_ms'))
    return {row['album_id']: (row['ms'] or 0) / 60000 for row in totals}

def _hours(entries):
    minutes = _album_minutes({entry.album_id for entry in entries})
    return round(sum(minutes.get(entry.album_id, 0) for entry in entries) / 60, 1)

def _bars(rows):
    # rows: [(label, count)] -> adds each bar's height as a percent of the tallest, and marks the peak.
    peak = max((count for _, count in rows), default=0)
    return [{'label': label, 'count': count, 'height': round(count * 100 / peak) if peak else 0,
             'is_peak': peak > 0 and count == peak} for label, count in rows]

def _rating_label(value):
    return ('%.1f' % value).rstrip('0').rstrip('.')

def user_stats(person):
    reviews = list(Review.objects.filter(user=person).select_related('album', 'album__artist'))
    rated = [r for r in reviews if r.rating is not None]
    diary = list(DiaryEntry.objects.filter(user=person).select_related('album'))
    today = timezone.localdate()

    spread = Counter(r.rating for r in rated)
    rating_bars = _bars([(_rating_label(step), spread.get(step, 0)) for step in RATING_STEPS])

    by_artist = defaultdict(list)
    for r in reviews:
        by_artist[r.album.artist].append(r)
    top_artists = sorted(by_artist.items(), key=lambda item: (-len(item[1]), item[0].name))[:5]
    top_artists = [{'artist': artist, 'count': len(rs),
                    'average': _avg([r.rating for r in rs if r.rating is not None])} for artist, rs in top_artists]

    by_decade = Counter((r.album.year // 10) * 10 for r in reviews if r.album.year)
    decade_bars = _bars([(str(decade) + 's', by_decade[decade]) for decade in sorted(by_decade)])
    favourite_decade = max(by_decade, key=lambda d: (by_decade[d], d)) if by_decade else None

    # Listens per month for the last 12 months, oldest first.
    months = []
    year, month = today.year, today.month
    for _ in range(12):
        months.append((year, month))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    listen_counts = Counter((e.listened_on.year, e.listened_on.month) for e in diary)
    month_bars = _bars([(datetime.date(y, m, 1).strftime('%b'), listen_counts.get((y, m), 0)) for y, m in reversed(months)])
    for bar, (y, m) in zip(month_bars, reversed(months)):
        bar['full_label'] = datetime.date(y, m, 1).strftime('%B %Y')

    return {
        'reviews': len(reviews),
        'rated': len(rated),
        'average': _avg([r.rating for r in rated]),
        'listens': len(diary),
        'hours': _hours(diary),
        'artists': len(by_artist),
        'artist_reviews': ArtistReview.objects.filter(user=person).count(),
        'likes_received': ReviewLike.objects.filter(review__user=person).count() + ReviewLike.objects.filter(artist_review__user=person).count(),
        'rating_bars': rating_bars,
        'top_artists': top_artists,
        'decade_bars': decade_bars,
        'favourite_decade': favourite_decade,
        'month_bars': month_bars,
    }

def year_stats(person, year):
    reviews = list(Review.objects.filter(user=person, date__year=year).select_related('album', 'album__artist'))
    rated = [r for r in reviews if r.rating is not None]
    diary = list(DiaryEntry.objects.filter(user=person, listened_on__year=year).select_related('album', 'album__artist'))

    top_albums = sorted(rated, key=lambda r: (-r.rating, r.date))[:5]

    listens_per_album = Counter(e.album for e in diary)
    most_played = listens_per_album.most_common(1)[0] if listens_per_album else None

    artist_activity = Counter([r.album.artist for r in reviews] + [e.album.artist for e in diary])
    top_artist = artist_activity.most_common(1)[0] if artist_activity else None

    month_activity = Counter([r.date.month for r in reviews] + [e.listened_on.month for e in diary])
    busiest_month = None
    if month_activity:
        month, count = month_activity.most_common(1)[0]
        busiest_month = {'name': datetime.date(year, month, 1).strftime('%B'), 'count': count}

    likes = (ReviewLike.objects.filter(review__user=person, date__year=year).count()
             + ReviewLike.objects.filter(artist_review__user=person, date__year=year).count())

    return {
        'year': year,
        'reviews': len(reviews),
        'listens': len(diary),
        'albums_heard': len({r.album_id for r in reviews} | {e.album_id for e in diary}),
        'average': _avg([r.rating for r in rated]),
        'hours': _hours(diary),
        'top_albums': top_albums,
        'most_played': {'album': most_played[0], 'count': most_played[1]} if most_played else None,
        'top_artist': {'artist': top_artist[0], 'count': top_artist[1]} if top_artist else None,
        'busiest_month': busiest_month,
        'likes': likes,
        'empty': not reviews and not diary,
    }

def _avg(values):
    return round(sum(values) / len(values), 2) if values else None

def year_in_review_open(today=None):
    # Year in review is only available in the last week of the year: December 25-31.
    today = today or timezone.localdate()
    return today.month == 12 and today.day >= 25
