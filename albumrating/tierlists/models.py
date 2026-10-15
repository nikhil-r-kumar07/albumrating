from django.db import models
from django.contrib.auth.models import User
from albums.models import Album

DEFAULT_TIERS = ['S', 'A', 'B', 'C', 'D']

class TierList(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tier_lists')
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title

class Tier(models.Model):
    # One row of a tier list (S, A, B...). Owners can rename, add and remove rows.
    id = models.AutoField(primary_key=True)
    tier_list = models.ForeignKey(TierList, on_delete=models.CASCADE, related_name='tiers')
    label = models.CharField(max_length=20)
    position = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['position']
    def __str__(self):
        return self.label

class TierItem(models.Model):
    # An album on a tier list. tier is empty while the album waits in the "unranked" tray.
    id = models.AutoField(primary_key=True)
    tier_list = models.ForeignKey(TierList, on_delete=models.CASCADE, related_name='items')
    tier = models.ForeignKey(Tier, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['position']
        constraints = [models.UniqueConstraint(fields=['tier_list', 'album'], name='album_once_per_tier_list')]
