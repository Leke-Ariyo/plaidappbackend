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


class TransactionCategory(models.Model):
    title = models.CharField(max_length=400)

    def __str__(self):
        return self.title


class Transaction(models.Model):
    item = models.ForeignKey(PlaidItem, on_delete=models.DO_NOTHING)
    transaction_id = models.CharField(max_length=400, primary_key=True)
    account_id = models.CharField(max_length=400)
    amount = models.DecimalField(max_digits=200, decimal_places=2)
    iso_currency_code = models.CharField(max_length=10)
    categories = models.ManyToManyField(TransactionCategory)
    date = models.DateField()
    address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=10, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=100, decimal_places=10, blank=True, null=True)
    longitude = models.DecimalField(max_digits=100, decimal_places=10, blank=True, null=True)
    store_number = models.CharField(max_length=200, blank=True, null=True)
    store_name = models.TextField(blank=True, null=True)
    payment_channel = models.CharField(max_length=400)

    def __str__(self):
        return self.item.user.username + ' - ' + self.transaction_id

"""
a = {'account_id': 'ANEyKz43pxiXV6e6eWVAc86g39Ne6qu17RQXe', 'account_owner': None, 'amount': 12, 'authorized_date': None, 'category': ['Food and Drink', 'Restaurants'], 'category_id': '13005000', 'date': '2020-01-13', 'iso_currency_code': 'USD', 'location': {'address': None, 'city': None, 'country': None, 'lat': None, 'lon': None, 'postal_code': None, 'region': None, 'store_number': '3322'}, 'name': "McDonald's", 'paymen
t_channel': 'in store', 'payment_meta': {'by_order_of': None, 'payee': None, 'payer': None, 'payment_method': None, 'payment_processor': None, 'ppd_id': None, 'reason': None, 'reference_number': None}, 'pending
': False, 'pending_transaction_id': None, 'transaction_id': '31AkJELgdGcPgLBLBKgPiNekaxw5mRuqqlR34', 'transaction_type': 'place', 'unofficial_currency_code': None}
"""