from django.db import models
from django.contrib.auth.models import User
from albums.models import Artist

class Concert(models.Model):
    # A show someone went to, or watched (livestream, TV, concert film), with a rating and review.
    HOW_CHOICES = [('live', 'Went in person'), ('watched', 'Watched it (stream, TV, film)')]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='concerts')
    artist_name = models.CharField(max_length=255)
    # Linked when the name matches an artist already on the site, so it shows on their page.
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True, related_name='concerts')
    tour = models.CharField(max_length=150, blank=True)
    venue = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    how = models.CharField(max_length=10, choices=HOW_CHOICES, default='live')
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)  # 0 to 5 in half steps
    review = models.TextField(max_length=5000, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-date', '-created']
    def place(self):
        # "Madison Square Garden, New York", or whichever half is filled in.
        return ', '.join(part for part in [self.venue, self.city] if part)
    def __str__(self):
        return self.artist_name + ' - ' + str(self.date)
