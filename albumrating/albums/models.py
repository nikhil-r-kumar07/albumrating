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
    rating = models.DecimalField(max_digits=2, decimal_places=1, null = True, blank = True)  # 0 to 5 in half steps
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
    rating = models.DecimalField(max_digits=2, decimal_places=1, null = True, blank = True)  # 0 to 5 in half steps
    class Meta:
        constraints = [models.UniqueConstraint(fields=['artist', 'user'], name='one_review_per_user_per_artist')]
    def __str__(self):
        return str(self.id) + ' - ' + self.artist.name

class Comment(models.Model):
    # A comment belongs to either an album review or an artist review.
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    artist_review = models.ForeignKey(ArtistReview, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    text = models.CharField(max_length=500)
    date = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    def parent(self):
        return self.review or self.artist_review
    def __str__(self):
        return str(self.id) + ' - ' + self.text[:40]

class CommentReport(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['comment', 'user'], name='one_report_per_user_per_comment')]
class ReviewLike(models.Model):
    # A like on either an album review or an artist review. One like per person per review.
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    artist_review = models.ForeignKey(ArtistReview, on_delete=models.CASCADE, null=True, blank=True, related_name='likes')
    date = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'review'], name='one_like_per_user_per_review'),
            models.UniqueConstraint(fields=['user', 'artist_review'], name='one_like_per_user_per_artist_review'),
        ]
