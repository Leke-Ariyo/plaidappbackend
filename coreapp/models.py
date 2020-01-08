from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class PlaidItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    item_id = models.CharField(max_length=400, primary_key=True)
    access_token = models.CharField(max_length=400)
    request_id = models.CharField(max_length=200)

    def __str__(self):
        return '{}-{}'.format(self.user.username, self.item_id)

