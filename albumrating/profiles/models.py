from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from albums.models import Album

class Profile(models.Model):
    # Extra details for a user. Created the first time someone edits their profile.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=300, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    def __str__(self):
        return self.user.username

@receiver(post_delete, sender=Profile)
def delete_avatar_file(sender, instance, **kwargs):
    # When a profile is deleted (e.g. the account is deleted), remove the photo file too.
    if instance.avatar:
        instance.avatar.delete(save=False)

class AlbumList(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='album_lists')
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

class ListItem(models.Model):
    id = models.AutoField(primary_key=True)
    album_list = models.ForeignKey(AlbumList, on_delete=models.CASCADE, related_name='items')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    class Meta:
        ordering = ['position']
        constraints = [models.UniqueConstraint(fields=['album_list', 'album'], name='album_once_per_list')]

class QueueItem(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queue')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    added = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['position']
        constraints = [models.UniqueConstraint(fields=['user', 'album'], name='album_once_per_queue')]

class Favorite(models.Model):
    # A user's top 4 albums, shown on their profile.
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['position']
        constraints = [models.UniqueConstraint(fields=['user', 'album'], name='album_once_per_favorites')]

class DiaryEntry(models.Model):
    # One listen of an album. People can log the same album many times (relistens).
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    listened_on = models.DateField()
    note = models.CharField(max_length=280, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-listened_on', '-created']

class Follow(models.Model):
    id = models.AutoField(primary_key=True)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_set')
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['follower', 'following'], name='follow_once')]

class Notification(models.Model):
    KINDS = [('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow')]
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    kind = models.CharField(max_length=20, choices=KINDS)
    # What it's about. Deleting the review or comment deletes the notification too.
    review = models.ForeignKey('albums.Review', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    artist_review = models.ForeignKey('albums.ArtistReview', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    comment = models.ForeignKey('albums.Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    created = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    class Meta:
        ordering = ['-created']
