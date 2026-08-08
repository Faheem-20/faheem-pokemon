import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Count, Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination

from .models import (
    TrainerProfile, CapturedPokemon, TrainerInventory, BattleRecord,
    Mission, MissionProgress, ShopItem, PurchaseHistory, KingdomMap,
    Achievement, TrainerAchievement, BattleStatistics, Notification,
    FriendRequest, Friend, AdminAnnouncement, AnalyticsLog, RewardHistory
)
from .permissions import IsAdminRole, IsTrainerRole, IsPlayerRole
from .serializers import (
    RegisterSerializer, LoginSerializer, user_payload, make_jwt_pair,
    TrainerProfileSerializer, CapturedPokemonSerializer, TrainerInventorySerializer,
    BattleRecordSerializer, MissionSerializer, MissionProgressSerializer,
    ShopItemSerializer, PurchaseHistorySerializer, KingdomMapSerializer,
    AchievementSerializer, TrainerAchievementSerializer, BattleStatisticsSerializer,
    NotificationSerializer, FriendRequestSerializer, FriendSerializer,
    AdminAnnouncementSerializer
)

# Standard pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

def first_error(serializer):
    errors = serializer.errors
    if isinstance(errors, dict):
        if 'message' in errors:
            value = errors['message']
            return value[0] if isinstance(value, list) else str(value)
        for value in errors.values():
            if isinstance(value, list) and value:
                return str(value[0])
    return 'Something went wrong'

# AUTHENTICATION & PROFILE VIEWS

class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = make_jwt_pair(user)
            return Response({
                'message': 'Account created successfully',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'token': tokens['access'],
                'user': user_payload(user)
            }, status=status.HTTP_201_CREATED)
        return Response({'message': first_error(serializer)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = make_jwt_pair(user)
            
            # Log login event
            profile = getattr(user, 'trainer_profile', None)
            AnalyticsLog.objects.create(
                event_type='login',
                trainer=profile,
                metadata={'ip': request.META.get('REMOTE_ADDR', '')}
            )
            
            # Update user last_login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'message': 'Login successful',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'token': tokens['access'],
                'user': user_payload(user)
            })
        return Response({'message': first_error(serializer)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': user_payload(request.user)})

    def put(self, request):
        user = request.user
        profile = getattr(user, 'trainer_profile', None)
        if not profile:
            return Response({'message': 'Trainer profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        if 'trainerName' in data:
            profile.trainer_name = data['trainerName']
        if 'avatar' in data:
            profile.avatar = data['avatar']
        if 'region' in data:
            profile.region = data['region']
        profile.save()
        
        return Response({'user': user_payload(user)})

# FORGOT PASSWORD SYSTEM

OTP_STORE = {}

def check_and_correct_email_typo(identifier):
    if not identifier or '@' not in identifier:
        return identifier
    parts = identifier.split('@')
    domain = parts[-1].strip().lower()
    local = '@'.join(parts[:-1]).strip()
    typos = ['gamil.com', 'gmaill.com', 'gmal.com', 'gmeil.com', 'gimail.com', 'gamil.co', 'gamil.con']
    if domain in typos:
        return f"{local}@gmail.com"
    return identifier

class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('email', '').strip().lower()
        if not identifier:
            return Response({'message': 'Email or Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            corrected = check_and_correct_email_typo(identifier)
            if corrected != identifier:
                user = User.objects.filter(email__iexact=corrected).first()
            
        if not user:
            return Response({'message': 'No account found with this email or username'}, status=status.HTTP_404_NOT_FOUND)
        
        email = user.email.lower().strip()
        otp_code = f"{random.randint(100000, 999999)}"
        expiry = timezone.now() + timedelta(minutes=10)
        
        OTP_STORE[email] = {
            'otp': otp_code,
            'expiry': expiry
        }
        
        print("\n" + "="*50)
        print(f" OTP CODE GENERATED FOR {email}: {otp_code} ")
        print("="*50 + "\n")
        
        subject = 'Pokémon Nexus - Your Trainer Verification Code'
        message = f"""Dear Trainer,

We received a request to reset the password for your Pokémon Nexus account.

Your 6-digit Trainer Verification Code is:
=========================
        {otp_code}
=========================

This code will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

Best regards,
The Pokémon Nexus Team
"""
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'simhamshashank18@gmail.com')
        email_sent = False
        email_error = None
        
        host_pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        if host_pw and host_pw != 'your-google-app-password-here' and host_pw != 'yhwitesqmqbayfgm':
            try:
                send_mail(subject, message, from_email, [email], fail_silently=False)
                email_sent = True
            except Exception as e:
                email_error = str(e)
        else:
            # For testing with the user's gmail SMTP credentials if valid
            try:
                send_mail(subject, message, from_email, [email], fail_silently=False)
                email_sent = True
            except Exception as e:
                email_error = str(e)
            
        return Response({
            'message': 'OTP sent successfully' if email_sent else f'OTP generated. {email_error}',
            'email': email,
            'otp': otp_code,
            'email_sent': email_sent
        }, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp', '').strip()
        
        if not identifier or not otp:
            return Response({'message': 'Email/Username and OTP code are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            corrected = check_and_correct_email_typo(identifier)
            if corrected != identifier:
                user = User.objects.filter(email__iexact=corrected).first()
                
        if not user:
            return Response({'message': 'No account found'}, status=status.HTTP_404_NOT_FOUND)
            
        email = user.email.lower().strip()
        stored = OTP_STORE.get(email)
        
        if not stored:
            return Response({'message': 'OTP not requested or expired'}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.now() > stored['expiry']:
            OTP_STORE.pop(email, None)
            return Response({'message': 'OTP has expired. Please request a new one'}, status=status.HTTP_400_BAD_REQUEST)
        if stored['otp'] != otp:
            return Response({'message': 'Invalid OTP code'}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'message': 'OTP verified successfully',
            'email': email
        }, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')
        
        if not identifier or not otp or not new_password:
            return Response({'message': 'Email/Username, OTP, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            corrected = check_and_correct_email_typo(identifier)
            if corrected != identifier:
                user = User.objects.filter(email__iexact=corrected).first()
                
        if not user:
            return Response({'message': 'No account found'}, status=status.HTTP_444_NOT_FOUND)
            
        email = user.email.lower().strip()
        stored = OTP_STORE.get(email)
        
        if not stored or stored['otp'] != otp or timezone.now() > stored['expiry']:
            return Response({'message': 'Invalid or expired OTP. Please verify again'}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        OTP_STORE.pop(email, None)
        
        return Response({'message': 'Your Account Password Has Been Reset Successfully'}, status=status.HTTP_200_OK)

# USER MANAGEMENT (ADMIN ONLY)

class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        users = User.objects.all().order_by('id')
        payload = [user_payload(u) for u in users]
        return Response(payload, status=status.HTTP_200_OK)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            return Response(user_payload(user), status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            data = request.data
            
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'is_active' in data:
                val = data['is_active']
                user.is_active = val.lower() in ('true', '1') if isinstance(val, str) else bool(val)
            user.save()
            
            profile, created = TrainerProfile.objects.get_or_create(user=user)
            if 'trainerName' in data:
                profile.trainer_name = data['trainerName']
            if 'role' in data:
                profile.role = data['role']
            if 'level' in data:
                profile.level = int(data['level'])
            if 'xp' in data:
                profile.xp = int(data['xp'])
            if 'coins' in data:
                profile.coins = int(data['coins'])
            profile.save()
            
            return Response(user_payload(user), status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# GAME SYSTEMS VIEWS

class CapturedPokemonViewSet(viewsets.ModelViewSet):
    serializer_class = CapturedPokemonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        queryset = CapturedPokemon.objects.filter(trainer=profile)
        
        # Searching, Filtering and Ordering
        is_party = self.request.query_params.get('is_in_party')
        if is_party is not None:
            queryset = queryset.filter(is_in_party=is_party.lower() == 'true')
            
        is_fav = self.request.query_params.get('is_favorite')
        if is_fav is not None:
            queryset = queryset.filter(is_favorite=is_fav.lower() == 'true')
            
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(type1__icontains=search_query) | Q(type2__icontains=search_query))
            
        ordering = self.request.query_params.get('ordering')
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-captured_at')
            
        return queryset

    def perform_create(self, serializer):
        profile = self.request.user.trainer_profile
        # If is_in_party is True, check party limit
        is_in_party = serializer.validated_data.get('is_in_party', False)
        if is_in_party:
            party_count = CapturedPokemon.objects.filter(trainer=profile, is_in_party=True).count()
            if party_count >= 6:
                raise serializers.ValidationError({"message": "Party full. Maximum 6 Pokémon allowed in party."})
        pokemon = serializer.save(trainer=profile)
        
        # Progress mission for catching pokemon
        self._progress_missions(profile, "Catch")

    @action(detail=True, methods=['post'], url_path='toggle-party')
    def toggle_party(self, request, pk=None):
        pokemon = self.get_object()
        profile = request.user.trainer_profile
        
        if pokemon.is_in_party:
            pokemon.is_in_party = False
            pokemon.save()
            return Response({'message': f'{pokemon.name} removed from party.', 'pokemon': CapturedPokemonSerializer(pokemon).data})
        else:
            party_count = CapturedPokemon.objects.filter(trainer=profile, is_in_party=True).count()
            if party_count >= 6:
                return Response({'message': 'Your party is full! (Max 6)'}, status=status.HTTP_400_BAD_REQUEST)
            pokemon.is_in_party = True
            pokemon.save()
            return Response({'message': f'{pokemon.name} added to party.', 'pokemon': CapturedPokemonSerializer(pokemon).data})

    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        pokemon = self.get_object()
        pokemon.is_favorite = not pokemon.is_favorite
        pokemon.save()
        return Response({'message': f'Favorite updated for {pokemon.name}.', 'pokemon': CapturedPokemonSerializer(pokemon).data})

    def _progress_missions(self, trainer, keyword):
        progresses = MissionProgress.objects.filter(
            trainer=trainer,
            is_completed=False,
            mission__title__icontains=keyword
        )
        for p in progresses:
            p.current_progress += 1
            if p.current_progress >= p.required_progress:
                p.is_completed = True
                Notification.objects.create(
                    trainer=trainer,
                    title="Mission Completed!",
                    message=f"You completed the mission: {p.mission.title}!",
                    category="Mission Complete"
                )
            p.save()

class TrainerInventoryViewSet(viewsets.ModelViewSet):
    serializer_class = TrainerInventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        queryset = TrainerInventory.objects.filter(trainer=profile)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
            
        return queryset.order_by('item_id')

    def perform_create(self, serializer):
        serializer.save(trainer=self.request.user.trainer_profile)


    @action(detail=False, methods=['post'], url_path='sync')
    def sync_inventory(self, request):
        profile = request.user.trainer_profile
        items = request.data.get('items', [])
        
        if not isinstance(items, list):
            return Response({'message': 'Items must be a list'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            for item_data in items:
                name = item_data.get('name')
                qty = item_data.get('qty', 0)
                category = item_data.get('category', 'General')
                item_id = item_data.get('id', 99)
                max_stk = 1 if category == 'Key Items' else 99
                
                if not name:
                    continue
                    
                inv_item, created = TrainerInventory.objects.get_or_create(
                    trainer=profile,
                    item_name=name,
                    defaults={'item_id': item_id, 'category': category, 'quantity': qty, 'max_stack': max_stk}
                )
                if not created:
                    inv_item.quantity = qty
                    inv_item.save()
                    
        return Response({'message': 'Inventory synced successfully.'})

class BattleRecordViewSet(viewsets.ModelViewSet):
    serializer_class = BattleRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        return BattleRecord.objects.filter(trainer=profile).order_by('-started_at')

    def create(self, request, *args, **kwargs):
        profile = request.user.trainer_profile
        data = request.data.copy()
        
        # Check for duplicates (same opponent and started_at within 2 seconds)
        started_at_str = data.get('started_at')
        if started_at_str:
            try:
                from django.utils.dateparse import parse_datetime
                started_at = parse_datetime(started_at_str)
                if started_at:
                    duplicate_exists = BattleRecord.objects.filter(
                        trainer=profile,
                        opponent=data.get('opponent'),
                        started_at__range=(started_at - timedelta(seconds=2), started_at + timedelta(seconds=2))
                    ).exists()
                    if duplicate_exists:
                        return Response({'message': 'This battle has already been recorded.'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                pass

        # Start transaction
        with transaction.atomic():
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return Response({'message': first_error(serializer)}, status=status.HTTP_400_BAD_REQUEST)
                
            battle = serializer.save(trainer=profile)
            
            # Apply rewards / stats updates
            is_win = (
                str(data.get('is_win')).lower() in ['true', '1'] or
                battle.winner.lower() == 'trainer' or
                (profile.trainer_name and battle.winner.lower() == profile.trainer_name.lower())
            )
            
            battle_rewards = {
                'xp': 0,
                'coins': 0,
                'reward_points': 0,
                'item': None
            }
            
            from .views_rewards import load_rewards_config, grant_item
            rewards_cfg = load_rewards_config().get("battle_rewards", {})
            
            if is_win:
                profile.wins += 1
                
                # Add reward points dynamically
                win_pts = rewards_cfg.get("win_points", 30)
                profile.reward_points += win_pts
                battle_rewards['reward_points'] = win_pts
                
                # Roll a chance-based item reward dynamically
                item_chance = rewards_cfg.get("item_chance", 0.60)
                if random.random() < item_chance:
                    weights_list = rewards_cfg.get("item_weights", [])
                    if weights_list:
                        choices = [w["name"] for w in weights_list]
                        weights = [w["weight"] for w in weights_list]
                        import random as py_random
                        item_name = py_random.choices(choices, weights=weights, k=1)[0]
                    else:
                        item_name = "Poke Ball"
                    
                    amount = 1
                    grant_item(profile, item_name, amount)
                    battle_rewards['item'] = {
                        'name': item_name,
                        'amount': amount
                    }
                    
                    # Log item reward in history
                    RewardHistory.objects.create(
                        trainer=profile,
                        reward_type="Item",
                        item_name=item_name,
                        amount=amount,
                        earned_from=f"Battle Victory vs {battle.opponent}",
                        status="Claimed"
                    )
            else:
                profile.losses += 1
                
            profile.battles_played += 1
            
            # Add rewards dynamically using config win values if victory and not overridden
            if is_win:
                xp_gained = int(data.get('xp_gained')) if 'xp_gained' in data else rewards_cfg.get("win_xp", 450)
                coins_gained = int(data.get('coins_gained')) if 'coins_gained' in data else rewards_cfg.get("win_coins", 150)
            else:
                xp_gained = int(data.get('xp_gained', 0))
                coins_gained = int(data.get('coins_gained', 0))
                
            profile.xp += xp_gained
            profile.coins += coins_gained
            
            battle_rewards['xp'] = xp_gained
            battle_rewards['coins'] = coins_gained
            
            # Log coins and XP in history
            if xp_gained > 0:
                RewardHistory.objects.create(
                    trainer=profile,
                    reward_type="XP",
                    amount=xp_gained,
                    earned_from=f"Battle vs {battle.opponent}",
                    status="Claimed"
                )
            if coins_gained > 0:
                RewardHistory.objects.create(
                    trainer=profile,
                    reward_type="Coins",
                    amount=coins_gained,
                    earned_from=f"Battle vs {battle.opponent}",
                    status="Claimed"
                )
            if battle_rewards['reward_points'] > 0:
                RewardHistory.objects.create(
                    trainer=profile,
                    reward_type="Reward Points",
                    amount=battle_rewards['reward_points'],
                    earned_from=f"Battle Victory vs {battle.opponent}",
                    status="Claimed"
                )
            
            # Calculate rank
            if profile.wins >= 50:
                profile.current_rank = 'Master'
            elif profile.wins >= 25:
                profile.current_rank = 'Diamond'
            elif profile.wins >= 10:
                profile.current_rank = 'Gold'
            elif profile.wins >= 5:
                profile.current_rank = 'Silver'
            else:
                profile.current_rank = 'Bronze'
                
            # Cumulative level calculation: level increases every 1000 XP
            new_level = (profile.xp // 1000) + 1
            level_ups = 0
            if new_level > profile.level:
                level_ups = new_level - profile.level
                profile.level = new_level
            profile.save()
            
            # Trigger notifications
            if level_ups > 0:
                Notification.objects.create(
                    trainer=profile,
                    title="Trainer Level Up!",
                    message=f"Congratulations! You leveled up to Level {profile.level}!",
                    category="Level Up"
                )
            
            Notification.objects.create(
                trainer=profile,
                title="Battle Finished",
                message=f"Battle completed with {battle.opponent}. XP +{xp_gained}, Coins +{coins_gained}.",
                category="Battle Result"
            )
            
            # Update BattleStatistics
            stats, _ = BattleStatistics.objects.get_or_create(trainer=profile)
            if data.get('stat_critical_hits'):
                stats.critical_hits += int(data.get('stat_critical_hits'))
            if data.get('stat_super_effective'):
                stats.super_effective += int(data.get('stat_super_effective'))
            if data.get('stat_damage_dealt'):
                stats.damage_dealt += int(data.get('stat_damage_dealt'))
            if data.get('stat_damage_taken'):
                stats.damage_taken += int(data.get('stat_damage_taken'))
            if data.get('stat_healing'):
                stats.healing += int(data.get('stat_healing'))
            if data.get('stat_pokemon_fainted'):
                stats.pokemon_fainted += int(data.get('stat_pokemon_fainted'))
            if data.get('stat_turns'):
                stats.turns += int(data.get('stat_turns'))
            stats.save()
            
            # Progress battle missions
            self._progress_battle_missions(profile, is_win)
            
            # Record analytics log
            AnalyticsLog.objects.create(
                event_type='battle',
                trainer=profile,
                metadata={'winner': battle.winner, 'xp': xp_gained, 'coins': coins_gained}
            )
            
        return Response({
            'message': 'Battle recorded successfully',
            'battle': BattleRecordSerializer(battle).data,
            'trainer': user_payload(request.user),
            'battle_rewards': battle_rewards
        }, status=status.HTTP_201_CREATED)

    def _progress_battle_missions(self, trainer, is_win):
        progresses = MissionProgress.objects.filter(trainer=trainer, is_completed=False)
        for p in progresses:
            m = p.mission
            # Check keywords in title
            if "battle" in m.title.lower() or "win" in m.title.lower():
                if "win" in m.title.lower() and not is_win:
                    continue  # Needs a win
                p.current_progress += 1
                if p.current_progress >= p.required_progress:
                    p.is_completed = True
                    Notification.objects.create(
                        trainer=trainer,
                        title="Mission Completed!",
                        message=f"You completed the mission: {m.title}!",
                        category="Mission Complete"
                    )
                p.save()

class LeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Sort by wins DESC, level DESC, xp DESC
        profiles = TrainerProfile.objects.all().order_by('-wins', '-level', '-xp')
        
        data = []
        for rank, p in enumerate(profiles, start=1):
            data.append({
                'rank': rank,
                'trainer_name': p.trainer_name,
                'avatar': p.avatar,
                'level': p.level,
                'xp': p.xp,
                'coins': p.coins,
                'wins': p.wins,
                'losses': p.losses,
                'badges_count': len(p.badges),
                'current_rank': p.current_rank
            })
        return Response(data, status=status.HTTP_200_OK)

class MissionProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MissionProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        # Make sure missions are generated for this trainer
        self._ensure_missions_assigned(profile)
        return MissionProgress.objects.filter(trainer=profile).order_by('mission__type')

    def _ensure_missions_assigned(self, trainer):
        # Check all available missions
        all_missions = Mission.objects.all()
        for m in all_missions:
            MissionProgress.objects.get_or_create(trainer=trainer, mission=m, defaults={'required_progress': 3 if 'win' in m.title.lower() else (5 if 'catch' in m.title.lower() else 1)})

    @action(detail=True, methods=['post'], url_path='claim')
    def claim_reward(self, request, pk=None):
        progress = self.get_object()
        if not progress.is_completed:
            return Response({'message': 'Mission is not completed yet.'}, status=status.HTTP_400_BAD_REQUEST)
        if progress.claimed:
            return Response({'message': 'Rewards already claimed.'}, status=status.HTTP_400_BAD_REQUEST)
            
        trainer = request.user.trainer_profile
        mission = progress.mission
        
        with transaction.atomic():
            # Add coins & XP
            trainer.coins += mission.reward_coins
            trainer.xp += mission.reward_xp
            
            # Cumulative level calculation: level increases every 1000 XP
            new_level = (trainer.xp // 1000) + 1
            if new_level > trainer.level:
                level_ups = new_level - trainer.level
                trainer.level = new_level
                Notification.objects.create(
                    trainer=trainer,
                    title="Trainer Level Up!",
                    message=f"Congratulations! You leveled up to Level {trainer.level}!",
                    category="Level Up"
                )
            trainer.save()
            
            # Add reward items
            reward_items = mission.reward_items or {}
            for item_name, qty in reward_items.items():
                if item_name.lower() == 'crystals':
                    trainer.crystals += qty
                elif item_name.lower() in ['reward points', 'reward_points']:
                    trainer.reward_points += qty
                else:
                    category = "Poké Balls" if "Ball" in item_name else ("Potions" if "Potion" in item_name else "Battle Items")
                    inv_item, _ = TrainerInventory.objects.get_or_create(
                        trainer=trainer,
                        item_name=item_name,
                        defaults={'item_id': random.randint(100, 999), 'category': category, 'quantity': 0}
                    )
                    inv_item.quantity += qty
                    inv_item.save()
                
            # Add reward Pokémon
            reward_pkmn = mission.reward_pokemon or {}
            if reward_pkmn and 'pokedex_number' in reward_pkmn:
                CapturedPokemon.objects.create(
                    trainer=trainer,
                    pokedex_number=reward_pkmn['pokedex_number'],
                    name=reward_pkmn.get('name', 'Pikachu'),
                    type1=reward_pkmn.get('type1', 'Electric'),
                    type2=reward_pkmn.get('type2'),
                    rarity=reward_pkmn.get('rarity', 'Rare'),
                    level=reward_pkmn.get('level', 15),
                    hp=80, max_hp=80, attack=50, defense=50, speed=50,
                    special_attack=50, special_defense=50,
                    image=reward_pkmn.get('image', 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png')
                )
                
            # Log rewards in RewardHistory
            if mission.reward_coins > 0:
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type="Coins",
                    amount=mission.reward_coins,
                    earned_from=f"Mission: {mission.title}",
                    status="Claimed"
                )
            if mission.reward_xp > 0:
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type="XP",
                    amount=mission.reward_xp,
                    earned_from=f"Mission: {mission.title}",
                    status="Claimed"
                )
            for item_name, qty in reward_items.items():
                if item_name.lower() == 'crystals':
                    r_type = "Crystals"
                elif item_name.lower() in ['reward points', 'reward_points']:
                    r_type = "Reward Points"
                else:
                    r_type = "Item"
                
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type=r_type,
                    item_name=item_name if r_type == "Item" else "",
                    amount=qty,
                    earned_from=f"Mission: {mission.title}",
                    status="Claimed"
                )

            progress.claimed = True
            progress.save()
            
            # Notification
            Notification.objects.create(
                trainer=trainer,
                title="Rewards Claimed",
                message=f"Claimed rewards for '{mission.title}'.",
                category="Rewards"
            )
            
        return Response({
            'message': 'Rewards claimed successfully.',
            'trainer': user_payload(request.user),
            'rewards': {
                'xp': mission.reward_xp,
                'coins': mission.reward_coins,
                'items': reward_items,
                'pokemon': reward_pkmn
            }
        })

class ShopItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShopItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ShopItem.objects.all().order_by('price')
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)
            
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
            
        return queryset

    @action(detail=True, methods=['post'], url_path='purchase')
    def purchase_item(self, request, pk=None):
        shop_item = self.get_object()
        trainer = request.user.trainer_profile
        qty = int(request.data.get('quantity', 1))
        
        if qty <= 0:
            return Response({'message': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)
            
        total_price = shop_item.price * qty
        if trainer.coins < total_price:
            return Response({'message': 'Insufficient coins.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if shop_item.stock != -1 and shop_item.stock < qty:
            return Response({'message': 'Not enough stock available.'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            # Deduct coins
            trainer.coins -= total_price
            trainer.save()
            
            # Update stock
            if shop_item.stock != -1:
                shop_item.stock -= qty
                shop_item.save()
                
            # Log purchase history
            PurchaseHistory.objects.create(
                trainer=trainer,
                item=shop_item,
                quantity=qty,
                coins_spent=total_price
            )
            
            # Update Inventory
            inv_item, _ = TrainerInventory.objects.get_or_create(
                trainer=trainer,
                item_name=shop_item.name,
                defaults={'item_id': shop_item.item_id, 'category': shop_item.category, 'quantity': 0}
            )
            inv_item.quantity += qty
            inv_item.save()
            
            # Notification
            Notification.objects.create(
                trainer=trainer,
                title="Purchase Complete",
                message=f"Purchased {qty}x {shop_item.name} for {total_price} coins.",
                category="Shop Purchase"
            )
            
            # Analytics
            AnalyticsLog.objects.create(
                event_type='shop_purchase',
                trainer=trainer,
                metadata={'item': shop_item.name, 'qty': qty, 'price': total_price}
            )
            
        return Response({
            'message': f'Successfully purchased {qty}x {shop_item.name}!',
            'trainer': user_payload(request.user),
            'inventory_item': TrainerInventorySerializer(inv_item).data
        })

class KingdomMapViewSet(viewsets.ModelViewSet):
    serializer_class = KingdomMapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        return KingdomMap.objects.filter(trainer=profile).order_by('id')

    @action(detail=True, methods=['post'], url_path='unlock')
    def unlock_region(self, request, pk=None):
        region = self.get_object()
        trainer = request.user.trainer_profile
        
        if region.status == 'unlocked':
            return Response({'message': 'Region is already unlocked.'}, status=status.HTTP_400_BAD_REQUEST)
            
        cost = 500  # Cost to unlock a region
        if trainer.coins < cost:
            return Response({'message': 'Insufficient coins to unlock region. Requires 500 coins.'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            trainer.coins -= cost
            trainer.save()
            
            region.status = 'unlocked'
            region.save()
            
            # Add notification
            Notification.objects.create(
                trainer=trainer,
                title="Region Unlocked!",
                message=f"You unlocked the {region.name} region! Explore now.",
                category="Rewards"
            )
            
            # Analytics log
            AnalyticsLog.objects.create(
                event_type='region_unlock',
                trainer=trainer,
                metadata={'region': region.name}
            )
            
        return Response({
            'message': f'Successfully unlocked {region.name} region!',
            'region': KingdomMapSerializer(region).data,
            'trainer': user_payload(request.user)
        })

    @action(detail=False, methods=['post'], url_path='sync')
    def sync_map(self, request):
        profile = request.user.trainer_profile
        regions = request.data.get('regions', [])
        
        if not isinstance(regions, list):
            return Response({'message': 'Regions must be a list'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            for reg_data in regions:
                reg_id = reg_data.get('id')
                status_str = reg_data.get('status', 'locked')
                prog = reg_data.get('progress', 0)
                gyms_val = reg_data.get('gyms', 0)
                
                if not reg_id:
                    continue
                    
                reg_item, created = KingdomMap.objects.get_or_create(
                    trainer=profile,
                    region_id=reg_id,
                    defaults={'name': reg_data.get('name', reg_id.capitalize()), 'status': status_str, 'progress': prog, 'gyms': gyms_val}
                )
                if not created:
                    reg_item.status = status_str
                    reg_item.progress = prog
                    reg_item.gyms = gyms_val
                    reg_item.save()
                    
        return Response({'message': 'Kingdom Map synced successfully.'})

class AchievementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trainer = request.user.trainer_profile
        achievements = Achievement.objects.all()
        trainer_achievements = TrainerAchievement.objects.filter(trainer=trainer)
        claimed_map = {ta.achievement_id: ta for ta in trainer_achievements}
        
        def get_trainer_achievement_progress(ach, trainer):
            category = ach.category
            title = ach.title
            
            if category == 'Battle':
                if title == "First Victory" or title == "Battle Master":
                    return trainer.wins
                elif title == "Ultimate Champion":
                    return 1 if trainer.wins >= 50 else 0
                return trainer.wins
            elif category == 'Collection':
                return CapturedPokemon.objects.filter(trainer=trainer).count()
            elif category == 'Gym':
                return len(trainer.badges)
            elif category == 'Exploration':
                return sum(r.progress for r in KingdomMap.objects.filter(trainer=trainer))
            elif category == 'Legendary':
                return CapturedPokemon.objects.filter(trainer=trainer, rarity='Legendary').count()
            elif category == 'Login':
                return trainer.login_streak
            elif category == 'Level':
                return trainer.level
            elif category == 'Rewards':
                return RewardHistory.objects.filter(trainer=trainer).count()
            return 0

        data = []
        for ach in achievements:
            progress = get_trainer_achievement_progress(ach, trainer)
            
            ta = claimed_map.get(ach.id)
            claimed = ta.claimed if ta else False
            unlocked_at = ta.unlocked_at if ta else None
            
            unlocked = (progress >= ach.target_value) or (ta is not None)
            
            data.append({
                'id': ach.id,
                'title': ach.title,
                'description': ach.description,
                'category': ach.category,
                'points': ach.points,
                'badge_image': ach.badge_image or 'default_badge',
                'target_value': ach.target_value,
                'xp_reward': ach.xp_reward,
                'coins_reward': ach.coins_reward,
                'crystal_reward': ach.crystal_reward,
                'rarity': ach.rarity,
                'progress': min(progress, ach.target_value),
                'unlocked': unlocked,
                'claimed': claimed,
                'unlocked_at': unlocked_at.strftime("%d %b, %Y") if unlocked_at else None
            })

        # Calculate Stats Dashboard
        total_achievements = len(achievements)
        unlocked_count = sum(1 for a in data if a['unlocked'])
        claimed_count = sum(1 for a in data if a['claimed'])
        in_progress_count = sum(1 for a in data if not a['unlocked'] and a['progress'] > 0)
        locked_count = sum(1 for a in data if not a['unlocked'] and a['progress'] == 0)
        
        completion_pct = round((unlocked_count / total_achievements) * 100) if total_achievements > 0 else 0
        
        total_xp = sum(a['xp_reward'] for a in data if a['claimed'])
        total_coins = sum(a['coins_reward'] for a in data if a['claimed'])
        total_crystals = sum(a['crystal_reward'] for a in data if a['claimed'])

        # Recently Earned (unlocked/claimed in TrainerAchievement)
        recently_earned = []
        recent_tas = TrainerAchievement.objects.filter(trainer=trainer).order_by('-unlocked_at')[:5]
        for ta in recent_tas:
            recently_earned.append({
                'id': ta.achievement.id,
                'badge_image': ta.achievement.badge_image or 'default_badge',
                'title': ta.achievement.title,
                'unlocked_at': ta.unlocked_at.strftime("%d %b, %Y"),
                'xp_reward': ta.achievement.xp_reward,
                'coins_reward': ta.achievement.coins_reward,
                'crystal_reward': ta.achievement.crystal_reward,
                'rarity': ta.achievement.rarity
            })

        return Response({
            'achievements': data,
            'stats': {
                'total_achievements': total_achievements,
                'unlocked_count': unlocked_count,
                'claimed_count': claimed_count,
                'in_progress_count': in_progress_count,
                'locked_count': locked_count,
                'completion_pct': completion_pct,
                'total_xp': total_xp,
                'total_coins': total_coins,
                'total_crystals': total_crystals,
            },
            'recently_earned': recently_earned
        }, status=status.HTTP_200_OK)

    def post(self, request):
        trainer = request.user.trainer_profile
        achievement_id = request.data.get('achievement_id')
        if not achievement_id:
            return Response({'message': 'Achievement ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            achievement = Achievement.objects.get(id=achievement_id)
        except Achievement.DoesNotExist:
            return Response({'message': 'Achievement not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if already claimed
        try:
            ta = TrainerAchievement.objects.get(trainer=trainer, achievement=achievement)
            if ta.claimed:
                return Response({'message': 'Achievement already claimed.'}, status=status.HTTP_400_BAD_REQUEST)
        except TrainerAchievement.DoesNotExist:
            ta = None

        # Verify dynamic progress is sufficient
        def get_trainer_achievement_progress(ach, trainer):
            category = ach.category
            title = ach.title
            if category == 'Battle':
                if title == "First Victory" or title == "Battle Master":
                    return trainer.wins
                elif title == "Ultimate Champion":
                    return 1 if trainer.wins >= 50 else 0
                return trainer.wins
            elif category == 'Collection':
                return CapturedPokemon.objects.filter(trainer=trainer).count()
            elif category == 'Gym':
                return len(trainer.badges)
            elif category == 'Exploration':
                return sum(r.progress for r in KingdomMap.objects.filter(trainer=trainer))
            elif category == 'Legendary':
                return CapturedPokemon.objects.filter(trainer=trainer, rarity='Legendary').count()
            elif category == 'Login':
                return trainer.login_streak
            elif category == 'Level':
                return trainer.level
            elif category == 'Rewards':
                return RewardHistory.objects.filter(trainer=trainer).count()
            return 0

        progress = get_trainer_achievement_progress(achievement, trainer)
        if progress < achievement.target_value:
            return Response({'message': 'Requirements not met for this achievement.'}, status=status.HTTP_400_BAD_REQUEST)

        # Claim the achievement
        with transaction.atomic():
            if ta:
                ta.claimed = True
                ta.save()
            else:
                ta = TrainerAchievement.objects.create(trainer=trainer, achievement=achievement, claimed=True)

            # Grant rewards
            if achievement.xp_reward > 0:
                trainer.xp += achievement.xp_reward
                new_level = (trainer.xp // 1000) + 1
                if new_level > trainer.level:
                    trainer.level = new_level

            if achievement.coins_reward > 0:
                trainer.coins += achievement.coins_reward

            if achievement.crystal_reward > 0:
                trainer.crystals += achievement.crystal_reward

            trainer.save()

            # Save reward history logs
            if achievement.xp_reward > 0:
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type="XP",
                    amount=achievement.xp_reward,
                    earned_from=f"Achievement: {achievement.title}",
                    status="Claimed"
                )
            if achievement.coins_reward > 0:
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type="Coins",
                    amount=achievement.coins_reward,
                    earned_from=f"Achievement: {achievement.title}",
                    status="Claimed"
                )
            if achievement.crystal_reward > 0:
                RewardHistory.objects.create(
                    trainer=trainer,
                    reward_type="Crystals",
                    amount=achievement.crystal_reward,
                    earned_from=f"Achievement: {achievement.title}",
                    status="Claimed"
                )

            # Notification
            Notification.objects.create(
                trainer=trainer,
                title="Achievement Claimed!",
                message=f"You claimed rewards for '{achievement.title}': +{achievement.xp_reward} XP, +{achievement.coins_reward} Coins, +{achievement.crystal_reward} Crystals!",
                category="Rewards"
            )

        return Response({
            'message': f"Successfully claimed '{achievement.title}'!",
            'trainer': user_payload(request.user)
        }, status=status.HTTP_200_OK)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        return Notification.objects.filter(trainer=profile).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'message': 'Notification marked as read.'})

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        profile = request.user.trainer_profile
        Notification.objects.filter(trainer=profile, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read.'})

class FriendViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        profile = request.user.trainer_profile
        
        # Get friends list
        friends = Friend.objects.filter(Q(user1=profile) | Q(user2=profile))
        friends_data = []
        for f in friends:
            friend_profile = f.user2 if f.user1 == profile else f.user1
            friends_data.append({
                'id': friend_profile.id,
                'trainer_name': friend_profile.trainer_name,
                'avatar': friend_profile.avatar,
                'level': friend_profile.level,
                'current_rank': friend_profile.current_rank,
                'online': True  # Mock status
            })
            
        # Get pending friend requests
        requests = FriendRequest.objects.filter(receiver=profile, status='pending')
        requests_data = FriendRequestSerializer(requests, many=True).data
        
        return Response({
            'friends': friends_data,
            'requests': requests_data
        })

    @action(detail=False, methods=['post'], url_path='send-request')
    def send_request(self, request):
        sender = request.user.trainer_profile
        receiver_name = request.data.get('trainer_name', '').strip()
        
        receiver = TrainerProfile.objects.filter(trainer_name__iexact=receiver_name).first()
        if not receiver:
            return Response({'message': 'Trainer not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if sender == receiver:
            return Response({'message': 'You cannot send a friend request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if already friends
        exists = Friend.objects.filter(
            (Q(user1=sender) & Q(user2=receiver)) | (Q(user1=receiver) & Q(user2=sender))
        ).exists()
        if exists:
            return Response({'message': 'You are already friends.'}, status=status.HTTP_400_BAD_REQUEST)
            
        req, created = FriendRequest.objects.get_or_create(
            sender=sender,
            receiver=receiver,
            defaults={'status': 'pending'}
        )
        if not created and req.status == 'pending':
            return Response({'message': 'Friend request already sent.'}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({'message': f'Friend request sent to {receiver.trainer_name}!'})

    @action(detail=True, methods=['post'], url_path='respond')
    def respond_to_request(self, request, pk=None):
        receiver = request.user.trainer_profile
        action_val = request.data.get('action', '').strip().lower()  # accept / reject
        
        try:
            freq = FriendRequest.objects.get(pk=pk, receiver=receiver, status='pending')
        except FriendRequest.DoesNotExist:
            return Response({'message': 'Friend request not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if action_val == 'accept':
            with transaction.atomic():
                freq.status = 'accepted'
                freq.save()
                
                Friend.objects.get_or_create(user1=freq.sender, user2=receiver)
                Notification.objects.create(
                    trainer=freq.sender,
                    title="Friend Request Accepted",
                    message=f"{receiver.trainer_name} accepted your friend request!",
                    category="Friends"
                )
            return Response({'message': 'Friend request accepted.'})
        elif action_val == 'reject':
            freq.status = 'rejected'
            freq.save()
            return Response({'message': 'Friend request rejected.'})
            
        return Response({'message': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

# ADMIN DASHBOARD & ANALYTICS VIEWS

class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        total_users = User.objects.count()
        admins = TrainerProfile.objects.filter(role='admin').count() + User.objects.filter(is_superuser=True).count()
        total_coins = sum(p.coins for p in TrainerProfile.objects.all())
        
        # Additional analytics data
        total_battles = BattleRecord.objects.count()
        total_captured = CapturedPokemon.objects.count()
        active_users_today = AnalyticsLog.objects.filter(
            event_type='login',
            timestamp__gte=timezone.now() - timedelta(days=1)
        ).values('trainer').distinct().count()
        
        # Pokemon popularity
        pokemon_popularity = CapturedPokemon.objects.values('name').annotate(count=Count('name')).order_by('-count')[:5]
        pokemon_stats = {item['name']: item['count'] for item in pokemon_popularity}
        
        # Item popularity
        item_sales = PurchaseHistory.objects.values('item__name').annotate(qty=Count('id')).order_by('-qty')[:5]
        item_stats = {item['item__name']: item['qty'] for item in item_sales}
        
        return Response({
            'message': 'Admin access granted',
            'stats': {
                'totalUsers': total_users,
                'adminUsers': admins,
                'normalUsers': max(total_users - admins, 0),
                'totalCoins': total_coins,
                'totalBattles': total_battles,
                'totalCapturedPokemon': total_captured,
                'activeUsersToday': active_users_today
            },
            'analytics': {
                'pokemon_usage': pokemon_stats,
                'item_usage': item_stats
            }
        })

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        return Response({'message': 'Admin dashboard access granted'})

class TrainerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsTrainerRole]

    def get(self, request):
        return Response({'message': 'Trainer dashboard access granted'})

class PlayerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsPlayerRole]

    def get(self, request):
        return Response({'message': 'Player dashboard access granted'})

class AdminAnnouncementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        
        if not title or not content:
            return Response({'message': 'Title and content are required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            ann = AdminAnnouncement.objects.create(title=title, content=content)
            
            # Send Notification to every Trainer
            trainers = TrainerProfile.objects.all()
            notifications = [
                Notification(
                    trainer=t,
                    title=f"Announcement: {title}",
                    message=content,
                    category="Admin Announcement"
                ) for t in trainers
            ]
            Notification.objects.bulk_create(notifications)
            
        return Response({'message': 'Announcement published to all trainers.'}, status=status.HTTP_201_CREATED)
