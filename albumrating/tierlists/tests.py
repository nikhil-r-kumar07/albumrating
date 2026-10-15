import json
from django.test import TestCase
from django.contrib.auth.models import User
from albums.models import Artist, Album, Review
from .models import TierList, TierItem

class TierListTests(TestCase):
    def setUp(self):
        self.me = User.objects.create_user('me', password='pw')
        self.other = User.objects.create_user('other', password='pw')
        artist = Artist.objects.create(name='Kanye West')
        self.album1 = Album.objects.create(name='Late Registration', artist=artist)
        self.album2 = Album.objects.create(name='Graduation', artist=artist)
        self.client.login(username='me', password='pw')

    def make_list(self):
        self.client.post('/tierlists/', {'title': 'Kanye ranked'})
        return TierList.objects.get(user=self.me)

    def test_new_tier_list_gets_default_rows(self):
        tier_list = self.make_list()
        self.assertEqual([tier.label for tier in tier_list.tiers.all()], ['S', 'A', 'B', 'C', 'D'])

    def test_add_from_album_page_goes_to_unranked(self):
        tier_list = self.make_list()
        self.client.post('/tierlists/add/', {'tier_list': tier_list.id, 'album': self.album1.id})
        self.assertIsNone(tier_list.items.get().tier)

    def test_add_reviewed_albums(self):
        tier_list = self.make_list()
        Review.objects.create(user=self.me, album=self.album1, comment='great')
        Review.objects.create(user=self.me, album=self.album2, comment='also great')
        self.client.post('/tierlists/' + str(tier_list.id) + '/add-reviewed/')
        self.assertEqual(tier_list.items.count(), 2)

    def test_arrange_moves_albums_into_tiers(self):
        tier_list = self.make_list()
        s_tier, a_tier = tier_list.tiers.all()[:2]
        first = TierItem.objects.create(tier_list=tier_list, album=self.album1)
        second = TierItem.objects.create(tier_list=tier_list, album=self.album2)
        rows = [{'tier': s_tier.id, 'items': [second.id]}, {'tier': a_tier.id, 'items': [first.id]}, {'tier': None, 'items': []}]
        response = self.client.post('/tierlists/' + str(tier_list.id) + '/arrange/', json.dumps({'rows': rows}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        second.refresh_from_db()
        first.refresh_from_db()
        self.assertEqual(second.tier, s_tier)
        self.assertEqual(first.tier, a_tier)

    def test_arrange_rejects_bad_data(self):
        tier_list = self.make_list()
        response = self.client.post('/tierlists/' + str(tier_list.id) + '/arrange/', 'nonsense', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_only_owner_can_arrange(self):
        tier_list = self.make_list()
        self.client.login(username='other', password='pw')
        response = self.client.post('/tierlists/' + str(tier_list.id) + '/arrange/', json.dumps({'rows': []}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_deleting_a_row_sends_albums_back_to_unranked(self):
        tier_list = self.make_list()
        s_tier = tier_list.tiers.first()
        item = TierItem.objects.create(tier_list=tier_list, album=self.album1, tier=s_tier)
        self.client.post('/tierlists/' + str(tier_list.id) + '/tier/' + str(s_tier.id) + '/delete/')
        item.refresh_from_db()
        self.assertIsNone(item.tier)
        self.assertEqual([tier.position for tier in tier_list.tiers.all()], [1, 2, 3, 4])

    def test_pages_render(self):
        tier_list = self.make_list()
        TierItem.objects.create(tier_list=tier_list, album=self.album1, tier=tier_list.tiers.first())
        for url in ['/tierlists/', '/tierlists/' + str(tier_list.id) + '/', '/albums/' + str(self.album1.id) + '/',
                    '/profile/u/me/', '/profile/feed/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.logout()
        response = self.client.get('/tierlists/' + str(tier_list.id) + '/')
        self.assertContains(response, 'Late Registration')
        self.assertNotContains(response, 'Unranked')
