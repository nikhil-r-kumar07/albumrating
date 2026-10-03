from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Artist(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    mbid = models.CharField(max_length=36, unique=True, null=True, blank=True)
    def __str__(self):
        return self.name

class Album(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='album_image/', blank=True)
    cover_url = models.URLField(blank=True, default='')
    mbid = models.CharField(max_length=36, unique=True, null=True, blank=True)
    def __str__(self):
        return str(self.id) + ' - ' + self.name

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(null = True, blank = True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['album', 'user'], name='one_review_per_user_per_album')]
    def __str__(self):
        return str(self.id) + ' - ' + self.album.name

class ArtistReview(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(null = True, blank = True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['artist', 'user'], name='one_review_per_user_per_artist')]
    def __str__(self):
        return str(self.id) + ' - ' + self.artist.name