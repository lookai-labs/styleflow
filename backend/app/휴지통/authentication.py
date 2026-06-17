from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import User


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken('token에 user_id가 없습니다.')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidToken('사용자를 찾을 수 없습니다.')
