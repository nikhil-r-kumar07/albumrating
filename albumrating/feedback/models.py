from django.db import models
from django.contrib.auth.models import User

class Request(models.Model):
    CATEGORIES = [
        ('feature', 'Feature idea'),
        ('bug', 'Something is broken'),
        ('album', 'Wrong or missing album info'),
        ('other', 'Other'),
    ]
    STATUSES = [
        ('new', 'New'),
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('declined', "Won't do"),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='feature')
    message = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUSES, default='new')
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.id) + ' - ' + self.get_category_display()
