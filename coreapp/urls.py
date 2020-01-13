from django.urls import path, include
from .views import (current_user, UserList,
                    LinkBankAccount, GetAuth,
                    TransactionViewSet
                    )
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('transactions', TransactionViewSet, basename='transactions')

urlpatterns = [
    path('current_user/', current_user),
    path('users/', UserList.as_view()),
    path('link-bank-account/', LinkBankAccount.as_view()),
    path('get-auth/', GetAuth.as_view()),
    path('', include(router.urls))
]

