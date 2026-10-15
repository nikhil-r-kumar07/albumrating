import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from albums.models import Artist
from profiles.models import Follow
from .models import Concert

class ConcertTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user('me', password='pw')
        self.artist = Artist.objects.create(name='Kendrick Lamar')
        self.client.login(username='me', password='pw')

    def log(self, **extra):
        data = {'artist_name': 'kendrick lamar', 'venue': 'The Forum', 'city': 'Inglewood',
                'date': '2025-06-01', 'how': 'live', 'rating': '4.5', 'review': 'Unreal.'}
        data.update(extra)
        return self.client.post('/concerts/new/', data)

    def test_log_concert_links_artist_and_rating(self):
        self.log()
        concert = Concert.objects.get()
        self.assertEqual(concert.artist, self.artist)
        self.assertEqual(str(concert.rating), '4.5')
        self.assertContains(self.client.get('/albums/artist/' + str(self.artist.id) + '/'), 'The Forum')

    def test_future_date_is_rejected(self):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        response = self.log(date=tomorrow.isoformat())
        self.assertEqual(Concert.objects.count(), 0)
        self.assertContains(response, 'happened yet')

    def test_unknown_artist_still_saves(self):
        self.log(artist_name='Some Local Band')
        self.assertIsNone(Concert.objects.get().artist)

    def test_only_owner_can_edit(self):
        self.log()
        concert = Concert.objects.get()
        User.objects.create_user('other', password='pw')
        self.client.login(username='other', password='pw')
        self.assertEqual(self.client.get('/concerts/' + str(concert.id) + '/edit/').status_code, 404)
        self.assertEqual(self.client.get('/concerts/' + str(concert.id) + '/').status_code, 200)

    def test_pages_render(self):
        self.log()
        concert = Concert.objects.get()
        friend = User.objects.create_user('friend', password='pw')
        Follow.objects.create(follower=friend, following=self.me)
        for url in ['/concerts/new/', '/concerts/new/?artist=' + str(self.artist.id), '/concerts/u/me/',
                    '/concerts/' + str(concert.id) + '/', '/concerts/' + str(concert.id) + '/edit/', '/profile/u/me/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertRedirects(self.client.get('/concerts/'), '/concerts/u/me/')
        self.client.login(username='friend', password='pw')
        self.assertContains(self.client.get('/profile/feed/'), 'live at The Forum')
