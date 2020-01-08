from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, UserSerializerWithToken, LinkBankAccountSerializer
from plaid import Client
from .models import PlaidItem
from django.conf import settings

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
            user = User.objects.first()
            if request.user.is_authenticated:
                user = request.user
            item = PlaidItem.objects.create(
                item_id=res['item_id'],
                access_token=res['access_token'],
                request_id=res['request_id'],
                user=user
            )
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
