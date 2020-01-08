from django.urls import path
from .views import (current_user, UserList,
                    LinkBankAccount, GetAuth
                    )

urlpatterns = [
    path('current_user/', current_user),
    path('users/', UserList.as_view()),
    path('link-bank-account/', LinkBankAccount.as_view()),
    path('get-auth/', GetAuth.as_view())
]