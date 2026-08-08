from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    TrainerProfile, CapturedPokemon, TrainerInventory, BattleRecord,
    Mission, MissionProgress, ShopItem, PurchaseHistory, KingdomMap,
    Achievement, TrainerAchievement, BattleStatistics, Notification,
    FriendRequest, Friend, AdminAnnouncement
)

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
    
    wins = profile.wins if profile else 0
    losses = profile.losses if profile else 0
    level = profile.level if profile else 1
    xp = profile.xp if profile else 0
    coins = profile.coins if profile else 100
    badges = profile.badges if profile else []
    
    return {
        'id': user.id,
        'username': user.username,
        'trainerName': profile.trainer_name if profile else user.first_name,
        'email': user.email,
        'role': role,
        'isAdmin': role == 'admin' or user.is_staff or user.is_superuser,
        'level': level,
        'xp': xp,
        'coins': coins,
        'avatar': profile.avatar if profile else '',
        'region': profile.region if profile else 'Kanto',
        'badges': badges,
        'wins': wins,
        'losses': losses,
        'battles_played': profile.battles_played if profile else 0,
        'current_rank': profile.current_rank if profile else 'Bronze',
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'is_active': user.is_active,
    }

class TrainerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerProfile
        fields = '__all__'

class CapturedPokemonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapturedPokemon
        fields = '__all__'
        read_only_fields = ('trainer',)

class TrainerInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerInventory
        fields = '__all__'
        read_only_fields = ('trainer',)

class BattleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BattleRecord
        fields = '__all__'
        read_only_fields = ('trainer',)

class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = '__all__'

class MissionProgressSerializer(serializers.ModelSerializer):
    mission_detail = MissionSerializer(source='mission', read_only=True)
    
    class Meta:
        model = MissionProgress
        fields = '__all__'
        read_only_fields = ('trainer', 'mission')

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        mission = instance.mission
        if mission:
            rep['title'] = mission.title
            rep['description'] = mission.description
            rep['mission_type'] = mission.type
            rep['reward_xp'] = mission.reward_xp
            rep['reward_coins'] = mission.reward_coins
            rep['reward_items'] = mission.reward_items
            rep['reward_pokemon'] = mission.reward_pokemon
        rep['claimable'] = instance.is_completed and not instance.claimed
        return rep

class ShopItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = '__all__'

class PurchaseHistorySerializer(serializers.ModelSerializer):
    item_detail = ShopItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = PurchaseHistory
        fields = '__all__'
        read_only_fields = ('trainer', 'item')

class KingdomMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = KingdomMap
        fields = '__all__'
        read_only_fields = ('trainer',)

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'

class TrainerAchievementSerializer(serializers.ModelSerializer):
    achievement_detail = AchievementSerializer(source='achievement', read_only=True)
    
    class Meta:
        model = TrainerAchievement
        fields = '__all__'
        read_only_fields = ('trainer', 'achievement')

class BattleStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BattleStatistics
        fields = '__all__'
        read_only_fields = ('trainer',)

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('trainer',)

class FriendRequestSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.trainer_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.trainer_name', read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = '__all__'
        read_only_fields = ('sender', 'receiver')

class FriendSerializer(serializers.ModelSerializer):
    user1_name = serializers.CharField(source='user1.trainer_name', read_only=True)
    user2_name = serializers.CharField(source='user2.trainer_name', read_only=True)
    
    class Meta:
        model = Friend
        fields = '__all__'
        read_only_fields = ('user1', 'user2')

class AdminAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAnnouncement
        fields = '__all__'
