from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Album(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    year = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='album_image/')
    def __str__(self):
        return str(self.id) + ' - ' + self.name
class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(null = True, blank = True)
    def __str__(self):
        return str(self.id) + ' - ' + self.album.name