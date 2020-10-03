from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializer_auth_token import AuthTokenSerializer
from .serializers import UserSerializer
from .models import User


class AuthTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user_data = User.objects.get(id=user.pk)
        user_serializer = UserSerializer(instance=user_data, context={
            'request': request})
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': user_serializer.data,
        })
