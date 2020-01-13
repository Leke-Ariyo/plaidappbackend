from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets, authentication
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (UserSerializer,
                          UserSerializerWithToken,
                          LinkBankAccountSerializer,
                          TransactionSerializer)
from plaid import Client
from .models import PlaidItem, Transaction, TransactionCategory
from django.conf import settings
import datetime

client = Client(
        client_id=settings.PLAID_CLIENT_ID,
        secret=settings.PLAID_SECRET,
        public_key=settings.PLAID_PUBLIC_KEY,
        environment=settings.PLAID_ENV
    )

@api_view(['GET'])
def current_user(request):
    """
    Determine the current user by their token, and return their data
    """

    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserList(APIView):
    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = UserSerializerWithToken(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkBankAccount(APIView):

    def get(self, request):
        response = []
        items = PlaidItem.objects.all()
        for item in items:
            res = {
                'item_id': item.item_id,
                'user_id': item.user.pk,
                'username': item.user.username,
                'access_token': item.access_token,
                'request_id': item.request_id
            }
            response.append(res)

        return Response(response, status=status.HTTP_200_OK)

    def post(self, request):
        print(request.data)
        serializer = LinkBankAccountSerializer(data=request.data)
        if serializer.is_valid():

            res = client.Item.public_token.exchange(serializer.data['public_token'])
            user = request.user

            item = PlaidItem.objects.create(
                item_id=res['item_id'],
                access_token=res['access_token'],
                request_id=res['request_id'],
                user=user
            )
            # save all transactions for the item
            response = client.Transactions.get(item.access_token, start_date='1990-01-01',
                                               end_date=str(datetime.date.today()))
            transactions = response['transactions']

            while len(transactions) < response['total_transactions']:
                response = client.Transactions.get(item.access_token, start_date='1990-01-01',
                                                   end_date=str(datetime.date.today()),
                                                   offset=len(transactions)
                                                   )
                transactions.extend(response['transactions'])
            for transaction in transactions:
                transaction_obj = Transaction.objects.create(
                    item=item,
                    transaction_id=transaction['transaction_id'],
                    account_id=transaction['account_id'],
                    amount=transaction['amount'],
                    iso_currency_code=transaction['iso_currency_code'],
                    date=transaction['date'],
                    address=transaction['location']['address'],
                    city=transaction['location']['city'],
                    region=transaction['location']['region'],
                    postal_code=transaction['location']['postal_code'],
                    country=transaction['location']['country'],
                    latitude=transaction['location']['lat'],
                    longitude=transaction['location']['lon'],
                    store_number=transaction['location']['store_number'],
                    store_name=transaction['name'],
                    payment_channel=transaction['payment_channel']
                )

                for category in transaction['category']:
                    category_obj = TransactionCategory.objects.get_or_create(
                        title=category
                    )[0]
                    transaction_obj.categories.add(category_obj)
                    transaction_obj.save()
            # web hook
            client.Item.webhook.update(item.access_token,
                                       'http://localhost:8000/core/transactions/')
            response = {
                'message': 'bank linked successful'
            }
            return Response(response, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors)


class GetAuth(APIView):
    def post(self, request):
        auth_responses = []
        user = User.objects.first()
        if request.user.is_authenticated:
            # user = request.user
            pass
        items = PlaidItem.objects.filter(user=user)
        print(items)
        for item in items:
            auth_response = client.Auth.get(item.access_token)
            auth_responses = auth_responses + auth_response['accounts']
            print(auth_responses)
        return Response({
            'accounts': auth_responses
        }, status=status.HTTP_200_OK)


class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = Transaction.objects.all()
        return queryset

    def post(self, request):
        item = request.data.get('item_id')


class TransactionWebHook(APIView):

    def post(self, request):
        webhook_type = request.data.get("webhook_type")
        webhook_code = request.data.get("webhook_code")
        item_id = request.data.get("item_id")
        new_transaction = request.data.get("new_transaction")

        if webhook_type and (webhook_type == 'TRANSACTIONS'):
            if webhook_code and (webhook_code == 'DEFAULT_UPDATE'):
                item_obj = PlaidItem.objects.get(
                    item_id=item_id
                )

                response = client.Transactions.get(item_obj.access_token,
                                                   start_date=datetime.date.today(),
                                                   end_date=str(datetime.date.today()))
                transactions = response['transactions']
                while len(transactions) < response['total_transactions']:
                    response = client.Transactions.get(item_obj.access_token,
                                                       start_date=datetime.date.today(),
                                                       end_date=str(datetime.date.today()),
                                                       offset=len(transactions)
                                                       )
                    transactions.extend(response['transactions'])

                for transaction in transactions:
                    if not Transaction.objects.filter(pk=transaction['transaction_id']).first():

                        transaction_obj = Transaction.objects.create(
                            item=item_obj,
                            transaction_id=transaction['transaction_id'],
                            account_id=transaction['account_id'],
                            amount=transaction['amount'],
                            iso_currency_code=transaction['iso_currency_code'],
                            date=transaction['date'],
                            address=transaction['location']['address'],
                            city=transaction['location']['city'],
                            region=transaction['location']['region'],
                            postal_code=transaction['location']['postal_code'],
                            country=transaction['location']['country'],
                            latitude=transaction['location']['lat'],
                            longitude=transaction['location']['lon'],
                            store_number=transaction['location']['store_number'],
                            store_name=transaction['name'],
                            payment_channel=transaction['payment_channel']
                        )

                        for category in transaction['category']:
                            category_obj = TransactionCategory.objects.get_or_create(
                                title=category
                            )[0]
                            transaction_obj.categories.add(category_obj)
                            transaction_obj.save()

            if webhook_code and (webhook_code == 'TRANSACTIONS_REMOVED'):
                removed_transactions = request.data.get("removed_transactions")
                for transaction in removed_transactions:
                    try:
                        t = Transaction.objects.get(pk=transaction)
                        t.delete()
                    except:
                        pass

        return Response({"message": "successfully added new transaction"}, status=status.HTTP_200_OK)
