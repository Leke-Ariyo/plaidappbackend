from django.contrib import admin
from .models import PlaidItem, Transaction, TransactionCategory
# Register your models here.


admin.site.register(PlaidItem)
admin.site.register(Transaction)
admin.site.register(TransactionCategory)
