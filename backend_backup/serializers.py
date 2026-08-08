from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import TrainerProfile


def make_jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    profile = getattr(user, 'trainer_profile', None)
    role = profile.role if profile else ('admin' if user.is_staff else 'user')
    refresh['email'] = user.email
    refresh['role'] = role
    refresh['trainerName'] = profile.trainer_name if profile else user.first_name
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterSerializer(serializers.Serializer):
    trainerName = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True)
    role = serializers.CharField(max_length=20, required=False, default='trainer')

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError({'message': 'Passwords do not match'})
        email = data['email'].lower().strip()
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise serializers.ValidationError({'message': 'Email already registered'})
        data['email'] = email
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['trainerName']
        )
        # Default role is normal user. Admin role can be changed in Django admin panel.
        role = validated_data.get('role', 'trainer').lower().strip()
        TrainerProfile.objects.create(user=user, trainer_name=validated_data['trainerName'], role=role)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'].lower().strip(), password=data['password'])
        if not user:
            raise serializers.ValidationError({'message': 'Invalid email or password'})
        if not user.is_active:
            raise serializers.ValidationError({'message': 'Account is disabled'})
        data['user'] = user
        return data


def user_payload(user):
    profile = getattr(user, 'trainer_profile', None)
    role = profile.role if profile else ('admin' if user.is_staff else 'user')
    return {
        'id': user.id,
        'username': user.username,
        'trainerName': profile.trainer_name if profile else user.first_name,
        'email': user.email,
        'role': role,
        'isAdmin': role == 'admin' or user.is_staff or user.is_superuser,
        'level': profile.level if profile else 1,
        'xp': profile.xp if profile else 0,
        'coins': profile.coins if profile else 100,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'is_active': user.is_active,
    }
