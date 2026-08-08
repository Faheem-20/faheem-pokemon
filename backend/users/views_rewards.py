import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Q

from .models import (
    TrainerProfile, CapturedPokemon, TrainerInventory, BattleRecord,
    RewardHistory, DailyRewardClaim, LevelRewardClaim, Event, EventRewardClaim
)

# Helper to grant items to the inventory
def grant_item(trainer, item_name, quantity=1):
    item_catalog = {
        "Master Ball": (1, "Poké Balls"),
        "Ultra Ball": (2, "Poké Balls"),
        "Great Ball": (3, "Poké Balls"),
        "Poke Ball": (4, "Poké Balls"),
        "Max Potion": (7, "Potions"),
        "Hyper Potion": (8, "Potions"),
        "Super Potion": (9, "Potions"),
        "Potion": (10, "Potions"),
        "Rare Candy": (14, "Battle Items"),
        "Fire Stone": (16, "Evolution Stones"),
        "Water Stone": (17, "Evolution Stones"),
        "Thunder Stone": (18, "Evolution Stones"),
    }
    
    if item_name in item_catalog:
        item_id, category = item_catalog[item_name]
        inv, created = TrainerInventory.objects.get_or_create(
            trainer=trainer,
            item_name=item_name,
            defaults={
                'item_id': item_id,
                'category': category,
                'quantity': 0,
                'max_stack': 99
            }
        )
        inv.quantity = min(inv.quantity + quantity, inv.max_stack)
        inv.save()
        return True
    return False

import os
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'rewards_config.json')

DEFAULT_CONFIG = {
    "daily_rewards": [
        {"day": 1, "type": "Coins", "amount": 100, "item_name": None},
        {"day": 2, "type": "Item", "amount": 1, "item_name": "Potion"},
        {"day": 3, "type": "Item", "amount": 2, "item_name": "Great Ball"},
        {"day": 4, "type": "XP", "amount": 200, "item_name": None},
        {"day": 5, "type": "Item", "amount": 1, "item_name": "Rare Candy"},
        {"day": 6, "type": "Item", "amount": 1, "item_name": "Ultra Ball"},
        {"day": 7, "type": "Crystals", "amount": 50, "item_name": None},
        {"day": 8, "type": "Coins", "amount": 200, "item_name": None},
        {"day": 9, "type": "Item", "amount": 1, "item_name": "Super Potion"},
        {"day": 10, "type": "Item", "amount": 3, "item_name": "Great Ball"},
        {"day": 11, "type": "XP", "amount": 300, "item_name": None},
        {"day": 12, "type": "Item", "amount": 2, "item_name": "Rare Candy"},
        {"day": 13, "type": "Item", "amount": 2, "item_name": "Ultra Ball"},
        {"day": 14, "type": "Crystals", "amount": 100, "item_name": None},
        {"day": 15, "type": "Coins", "amount": 300, "item_name": None},
        {"day": 16, "type": "Item", "amount": 1, "item_name": "Hyper Potion"},
        {"day": 17, "type": "Item", "amount": 5, "item_name": "Great Ball"},
        {"day": 18, "type": "XP", "amount": 400, "item_name": None},
        {"day": 19, "type": "Item", "amount": 3, "item_name": "Rare Candy"},
        {"day": 20, "type": "Item", "amount": 3, "item_name": "Ultra Ball"},
        {"day": 21, "type": "Crystals", "amount": 150, "item_name": None},
        {"day": 22, "type": "Coins", "amount": 500, "item_name": None},
        {"day": 23, "type": "Item", "amount": 1, "item_name": "Max Potion"},
        {"day": 24, "type": "Item", "amount": 5, "item_name": "Ultra Ball"},
        {"day": 25, "type": "XP", "amount": 500, "item_name": None},
        {"day": 26, "type": "Item", "amount": 5, "item_name": "Rare Candy"},
        {"day": 27, "type": "Item", "amount": 1, "item_name": "Master Ball"},
        {"day": 28, "type": "Crystals", "amount": 250, "item_name": None},
        {"day": 29, "type": "Coins", "amount": 1000, "item_name": None},
        {"day": 30, "type": "Crystals", "amount": 500, "item_name": None}
    ],
    "level_rewards": [
        {"level": 5, "type": "Item", "amount": 5, "item_name": "Potion"},
        {"level": 10, "type": "Item", "amount": 10, "item_name": "Great Ball"},
        {"level": 15, "type": "Item", "amount": 3, "item_name": "Rare Candy"},
        {"level": 20, "type": "Crystals", "amount": 100, "item_name": None},
        {"level": 25, "type": "Item", "amount": 10, "item_name": "Ultra Ball"},
        {"level": 30, "type": "Item", "amount": 5, "item_name": "Rare Candy"},
        {"level": 35, "type": "Crystals", "amount": 200, "item_name": None},
        {"level": 40, "type": "Item", "amount": 1, "item_name": "Master Ball"},
        {"level": 50, "type": "Crystals", "amount": 500, "item_name": None},
        {"level": 60, "type": "Item", "amount": 10, "item_name": "Rare Candy"},
        {"level": 70, "type": "Crystals", "amount": 1000, "item_name": None},
        {"level": 80, "type": "Item", "amount": 3, "item_name": "Master Ball"},
        {"level": 90, "type": "Crystals", "amount": 2000, "item_name": None},
        {"level": 100, "type": "Crystals", "amount": 5000, "item_name": None}
    ],
    "battle_rewards": {
        "win_xp": 450,
        "win_coins": 150,
        "win_points": 30,
        "item_chance": 0.60,
        "item_weights": [
            {"name": "Poke Ball", "weight": 35},
            {"name": "Great Ball", "weight": 25},
            {"name": "Ultra Ball", "weight": 15},
            {"name": "Potion", "weight": 15},
            {"name": "Rare Candy", "weight": 8},
            {"name": "Fire Stone", "weight": 2}
        ]
    },
    "settings": {
        "streak_multiplier_enabled": True,
        "weekend_xp_boost_enabled": False
    }
}

import copy

def load_rewards_config():
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return copy.deepcopy(DEFAULT_CONFIG)

def save_rewards_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

class DynamicDailyRewardsList:
    def __iter__(self):
        return iter(load_rewards_config()["daily_rewards"])
    
    def __getitem__(self, index):
        return load_rewards_config()["daily_rewards"][index]

    def __len__(self):
        return len(load_rewards_config()["daily_rewards"])

DAILY_REWARDS_LIST = DynamicDailyRewardsList()

class DynamicLevelRewardsMap:
    def items(self):
        config = load_rewards_config()
        return {item["level"]: {"type": item["type"], "amount": item["amount"], "item_name": item["item_name"]} for item in config["level_rewards"]}.items()

    def __contains__(self, key):
        config = load_rewards_config()
        levels = [item["level"] for item in config["level_rewards"]]
        try:
            return int(key) in levels
        except Exception:
            return False

    def __getitem__(self, key):
        config = load_rewards_config()
        level_map = {item["level"]: {"type": item["type"], "amount": item["amount"], "item_name": item["item_name"]} for item in config["level_rewards"]}
        return level_map[int(key)]

LEVEL_REWARDS_MAP = DynamicLevelRewardsMap()

# --- VIEW CLASSES ---

# GET /api/rewards/dashboard/
class RewardsDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        
        # Calculate totals from history
        total_collected = RewardHistory.objects.filter(trainer=profile).count()
        total_coins = RewardHistory.objects.filter(trainer=profile, reward_type='Coins').aggregate(sum=Sum('amount'))['sum'] or 0
        total_xp = RewardHistory.objects.filter(trainer=profile, reward_type='XP').aggregate(sum=Sum('amount'))['sum'] or 0

        data = {
            "total_collected_rewards": total_collected,
            "total_coins_earned": total_coins,
            "total_xp_earned": total_xp,
            "total_crystals": profile.crystals,
            "login_streak": profile.login_streak,
            "battle_pass_level": profile.battle_pass_level,
            "reward_points": profile.reward_points
        }
        return Response(data, status=status.HTTP_200_OK)

# GET /api/rewards/daily/
class DailyRewardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        today = timezone.now().date()
        
        # Check if claimed today
        has_claimed_today = (profile.last_login_date == today)
        
        # Cooldown calculation (seconds remaining until next calendar day starts)
        if has_claimed_today:
            tomorrow = today + datetime.timedelta(days=1)
            midnight = datetime.datetime.combine(tomorrow, datetime.time.min)
            tz = timezone.get_current_timezone()
            midnight_tz = timezone.make_aware(midnight, tz)
            cooldown_seconds = int((midnight_tz - timezone.now()).total_seconds())
        else:
            cooldown_seconds = 0

        # Retrieve all claimed days in this cycle (1 to 30)
        claimed_days = list(DailyRewardClaim.objects.filter(trainer=profile).values_list('day_number', flat=True))

        # Check if they have reached the end of cycle and need reset
        if len(claimed_days) >= 30 and not has_claimed_today:
            # Automatic cycle reset
            DailyRewardClaim.objects.filter(trainer=profile).delete()
            profile.login_streak = 0
            profile.save()
            claimed_days = []

        # Populate rewards state
        rewards = []
        next_claimable_day = profile.login_streak + 1
        if next_claimable_day > 30:
            next_claimable_day = 1

        for r in DAILY_REWARDS_LIST:
            day = r["day"]
            claimed = day in claimed_days
            claimable = (day == next_claimable_day and not has_claimed_today)
            locked = (day > next_claimable_day) or (day == next_claimable_day and has_claimed_today)

            rewards.append({
                "day": day,
                "reward_type": r["type"],
                "amount": r["amount"],
                "item_name": r["item_name"],
                "claimed": claimed,
                "claimable": claimable,
                "locked": locked
            })

        return Response({
            "login_streak": profile.login_streak,
            "has_claimed_today": has_claimed_today,
            "cooldown_seconds": max(0, cooldown_seconds),
            "rewards": rewards
        }, status=status.HTTP_200_OK)

# POST /api/rewards/daily/claim/
class DailyRewardClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.trainer_profile
        today = timezone.now().date()

        if profile.last_login_date == today:
            return Response({"message": "You have already claimed today's reward. Please return tomorrow."}, status=status.HTTP_400_BAD_REQUEST)

        # Get next day number
        next_day = profile.login_streak + 1
        if next_day > 30:
            # Cycle reset
            DailyRewardClaim.objects.filter(trainer=profile).delete()
            profile.login_streak = 0
            next_day = 1

        # Look up reward configuration
        reward_config = next(r for r in DAILY_REWARDS_LIST if r["day"] == next_day)
        
        # Grant reward
        reward_type = reward_config["type"]
        amount = reward_config["amount"]
        item_name = reward_config["item_name"]

        if reward_type == "Coins":
            profile.coins += amount
        elif reward_type == "Crystals":
            profile.crystals += amount
        elif reward_type == "XP":
            profile.xp += amount
            # Level up check (1000 XP per level simple logic)
            new_level = (profile.xp // 1000) + 1
            if new_level > profile.level:
                profile.level = new_level
        elif reward_type == "Item":
            grant_item(profile, item_name, amount)

        # Update profile stats
        profile.login_streak = next_day
        profile.last_login_date = today
        profile.reward_points += 50  # 50 points per check-in
        profile.save()

        # Save claim records
        DailyRewardClaim.objects.create(trainer=profile, day_number=next_day)
        
        RewardHistory.objects.create(
            trainer=profile,
            reward_type=reward_type,
            item_name=item_name,
            amount=amount,
            earned_from="Daily Login",
            status="Claimed"
        )

        return Response({
            "message": f"Day {next_day} claimed successfully!",
            "reward": {
                "type": reward_type,
                "amount": amount,
                "item_name": item_name
            },
            "profile": {
                "coins": profile.coins,
                "crystals": profile.crystals,
                "xp": profile.xp,
                "level": profile.level,
                "login_streak": profile.login_streak
            }
        }, status=status.HTTP_200_OK)

# GET /api/rewards/level/
class LevelRewardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        claimed_levels = list(LevelRewardClaim.objects.filter(trainer=profile).values_list('level', flat=True))

        milestones = []
        for lvl, reward in LEVEL_REWARDS_MAP.items():
            claimed = lvl in claimed_levels
            claimable = (profile.level >= lvl and not claimed)
            locked = (profile.level < lvl)

            milestones.append({
                "level": lvl,
                "reward_type": reward["type"],
                "amount": reward["amount"],
                "item_name": reward["item_name"],
                "claimed": claimed,
                "claimable": claimable,
                "locked": locked
            })

        return Response({
            "current_level": profile.level,
            "milestones": milestones
        }, status=status.HTTP_200_OK)

# POST /api/rewards/level/claim/
class LevelRewardClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.trainer_profile
        level = request.data.get("level")

        if not level:
            return Response({"message": "Milestone level parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            level = int(level)
        except ValueError:
            return Response({"message": "Invalid level parameter format."}, status=status.HTTP_400_BAD_REQUEST)

        if level not in LEVEL_REWARDS_MAP:
            return Response({"message": "No reward configured for this level milestone."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.level < level:
            return Response({"message": "Your level is insufficient to claim this reward."}, status=status.HTTP_400_BAD_REQUEST)

        # Check double claims
        if LevelRewardClaim.objects.filter(trainer=profile, level=level).exists():
            return Response({"message": "This level milestone has already been claimed."}, status=status.HTTP_400_BAD_REQUEST)

        reward = LEVEL_REWARDS_MAP[level]
        reward_type = reward["type"]
        amount = reward["amount"]
        item_name = reward["item_name"]

        # Grant reward
        if reward_type == "Coins":
            profile.coins += amount
        elif reward_type == "Crystals":
            profile.crystals += amount
        elif reward_type == "Item":
            grant_item(profile, item_name, amount)

        profile.reward_points += 100  # 100 points per milestone claim
        profile.save()

        # Save logs
        LevelRewardClaim.objects.create(trainer=profile, level=level)
        
        RewardHistory.objects.create(
            trainer=profile,
            reward_type=reward_type,
            item_name=item_name,
            amount=amount,
            earned_from=f"Level {level} Milestone",
            status="Claimed"
        )

        return Response({
            "message": f"Level {level} milestone claimed successfully!",
            "reward": {
                "type": reward_type,
                "amount": amount,
                "item_name": item_name
            },
            "profile": {
                "coins": profile.coins,
                "crystals": profile.crystals,
                "reward_points": profile.reward_points
            }
        }, status=status.HTTP_200_OK)

# GET /api/rewards/events/
class EventRewardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        now = timezone.now()
        
        # Load active events
        active_events = Event.objects.filter(expires_at__gt=now)
        
        # Fallback to default mock events if DB contains no events
        if active_events.count() == 0:
            exp_date = now + datetime.timedelta(days=7)
            # Create a couple of events in database for immediate visual preview
            Event.objects.create(
                title="Weekly Arena Brawl",
                description="Complete 5 battles in the volcano arena this week.",
                event_type="weekly",
                reward_type="Crystals",
                amount=150,
                image="https://archives.bulbagarden.net/media/upload/7/79/Dream_Pok%C3%A9_Ball_Sprite.png",
                expires_at=exp_date
            )
            Event.objects.create(
                title="Summer Solstice Festival",
                description="Claim seasonal special reward to beat the heat.",
                event_type="seasonal",
                reward_type="Item",
                item_name="Master Ball",
                amount=1,
                image="https://archives.bulbagarden.net/media/upload/9/95/Dream_Master_Ball_Sprite.png",
                expires_at=exp_date + datetime.timedelta(days=15)
            )
            active_events = Event.objects.filter(expires_at__gt=now)

        claimed_events = list(EventRewardClaim.objects.filter(trainer=profile).values_list('event_id', flat=True))

        events = []
        for ev in active_events:
            claimed = ev.id in claimed_events
            cooldown_seconds = int((ev.expires_at - now).total_seconds())

            events.append({
                "id": ev.id,
                "title": ev.title,
                "description": ev.description,
                "event_type": ev.get_event_type_display(),
                "reward_type": ev.reward_type,
                "amount": ev.amount,
                "item_name": ev.item_name,
                "image": ev.image,
                "cooldown_seconds": max(0, cooldown_seconds),
                "claimed": claimed,
                "claimable": not claimed
            })

        return Response(events, status=status.HTTP_200_OK)

# POST /api/rewards/events/claim/
class EventRewardClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.trainer_profile
        event_id = request.data.get("event_id")

        if not event_id:
            return Response({"message": "Event ID parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"message": "Event not found or invalid ID."}, status=status.HTTP_404_NOT_FOUND)

        if event.expires_at <= timezone.now():
            return Response({"message": "This limited-time event has already expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Check double claims
        if EventRewardClaim.objects.filter(trainer=profile, event=event).exists():
            return Response({"message": "This event reward has already been claimed."}, status=status.HTTP_400_BAD_REQUEST)

        reward_type = event.reward_type
        amount = event.amount
        item_name = event.item_name

        # Grant reward
        if reward_type == "Coins":
            profile.coins += amount
        elif reward_type == "Crystals":
            profile.crystals += amount
        elif reward_type == "Item":
            grant_item(profile, item_name, amount)

        profile.reward_points += 200  # 200 points per event claim
        profile.save()

        # Save logs
        EventRewardClaim.objects.create(trainer=profile, event=event)
        
        RewardHistory.objects.create(
            trainer=profile,
            reward_type=reward_type,
            item_name=item_name,
            amount=amount,
            earned_from=f"Event: {event.title}",
            status="Claimed"
        )

        return Response({
            "message": f"Event '{event.title}' reward claimed successfully!",
            "reward": {
                "type": reward_type,
                "amount": amount,
                "item_name": item_name
            },
            "profile": {
                "coins": profile.coins,
                "crystals": profile.crystals,
                "reward_points": profile.reward_points
            }
        }, status=status.HTTP_200_OK)

# GET /api/rewards/history/
class RewardHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        
        # Filtering & Search queries
        search_query = request.query_params.get('search', '').strip()
        filter_category = request.query_params.get('category', '').strip()

        history_qs = RewardHistory.objects.filter(trainer=profile).order_by('-date')

        if search_query:
            history_qs = history_qs.filter(
                Q(reward_type__icontains=search_query) |
                Q(earned_from__icontains=search_query) |
                Q(item_name__icontains=search_query)
            )

        if filter_category:
            history_qs = history_qs.filter(earned_from__icontains=filter_category)

        # Pagination setup
        paginator = PageNumberPagination()
        paginator.page_size = 8
        page = paginator.paginate_queryset(history_qs, request, view=self)

        results = []
        for log in (page if page is not None else history_qs):
            results.append({
                "id": log.id,
                "reward": f"{log.reward_type}" if not log.item_name else f"{log.item_name}",
                "category": "Item" if log.item_name else log.reward_type,
                "amount": log.amount,
                "earned_from": log.earned_from,
                "date": log.date.strftime("%Y-%m-%d %H:%M:%S"),
                "status": log.status
            })

        if page is not None:
            return paginator.get_paginated_response(results)

        return Response(results, status=status.HTTP_200_OK)

# GET /api/admin/rewards/config/ (and CRUD endpoints if required)
from .models import AnalyticsLog, Mission, MissionProgress
from .serializers import MissionSerializer
from rest_framework import viewsets

class AdminRewardsConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        config = load_rewards_config()
        return Response(config, status=status.HTTP_200_OK)

    def post(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        config = load_rewards_config()
        
        daily_rewards = request.data.get("daily_rewards")
        level_rewards = request.data.get("level_rewards")
        battle_rewards = request.data.get("battle_rewards")
        general_settings = request.data.get("settings")
        
        if daily_rewards is not None:
            config["daily_rewards"] = daily_rewards
        if level_rewards is not None:
            config["level_rewards"] = level_rewards
        if battle_rewards is not None:
            config["battle_rewards"] = battle_rewards
        if general_settings is not None:
            config["settings"] = general_settings
            
        save_rewards_config(config)
        
        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "update_rewards_config", "updated_keys": list(request.data.keys())}
        )
        
        return Response({"message": "Rewards configuration updated successfully!"}, status=status.HTTP_200_OK)

class AdminEventConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        events = Event.objects.all().order_by('-created_at')
        results = []
        for ev in events:
            results.append({
                "id": ev.id,
                "title": ev.title,
                "description": ev.description,
                "event_type": ev.event_type,
                "reward_type": ev.reward_type,
                "item_name": ev.item_name,
                "amount": ev.amount,
                "expires_at": ev.expires_at.strftime("%Y-%m-%dT%H:%M"),
                "image": ev.image
            })
        return Response(results, status=status.HTTP_200_OK)

    def post(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get("title")
        description = request.data.get("description")
        event_type = request.data.get("event_type", "limited")
        reward_type = request.data.get("reward_type")
        item_name = request.data.get("item_name")
        amount = request.data.get("amount", 0)
        expires_at_str = request.data.get("expires_at")
        image = request.data.get("image", "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png")

        if not title or not reward_type or not expires_at_str:
            return Response({"message": "Title, reward type, and expiration date are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = int(amount)
            expires_at = datetime.datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M")
            tz = timezone.get_current_timezone()
            expires_at = timezone.make_aware(expires_at, tz)
        except (ValueError, TypeError):
            return Response({"message": "Invalid format for amount or expiration date."}, status=status.HTTP_400_BAD_REQUEST)

        event = Event.objects.create(
            title=title,
            description=description,
            event_type=event_type,
            reward_type=reward_type,
            item_name=item_name,
            amount=amount,
            image=image,
            expires_at=expires_at
        )

        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "create_event", "event_id": event.id, "title": event.title}
        )

        return Response({
            "message": "Event created successfully!",
            "event": {
                "id": event.id,
                "title": event.title
            }
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        event_id = request.data.get("id")
        if not event_id:
            return Response({"message": "Event ID is required for editing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        event.title = request.data.get("title", event.title)
        event.description = request.data.get("description", event.description)
        event.event_type = request.data.get("event_type", event.event_type)
        event.reward_type = request.data.get("reward_type", event.reward_type)
        event.item_name = request.data.get("item_name", event.item_name)
        event.image = request.data.get("image", event.image)

        amount = request.data.get("amount")
        if amount is not None:
            try:
                event.amount = int(amount)
            except ValueError:
                return Response({"message": "Amount must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        expires_at_str = request.data.get("expires_at")
        if expires_at_str:
            try:
                expires_at = datetime.datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M")
                tz = timezone.get_current_timezone()
                event.expires_at = timezone.make_aware(expires_at, tz)
            except ValueError:
                return Response({"message": "Invalid expiration date format."}, status=status.HTTP_400_BAD_REQUEST)

        event.save()

        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "update_event", "event_id": event.id, "title": event.title}
        )

        return Response({"message": "Event updated successfully!"}, status=status.HTTP_200_OK)

    def delete(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get("id")
        if not event_id:
            return Response({"message": "Event ID is required for deletion."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id)
            event_title = event.title
            event.delete()

            AnalyticsLog.objects.create(
                event_type="admin_change",
                trainer=profile,
                metadata={"action": "delete_event", "event_id": event_id, "title": event_title}
            )

            return Response({"message": "Event deleted successfully!"}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"message": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

class AdminRewardHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        search_query = request.query_params.get('search', '').strip()
        filter_category = request.query_params.get('category', '').strip()
        export_format = request.query_params.get('export', '').strip()

        history_qs = RewardHistory.objects.all().order_by('-date')

        if search_query:
            history_qs = history_qs.filter(
                Q(trainer__user__username__icontains=search_query) |
                Q(trainer__trainer_name__icontains=search_query) |
                Q(reward_type__icontains=search_query) |
                Q(earned_from__icontains=search_query) |
                Q(item_name__icontains=search_query)
            )

        if filter_category:
            history_qs = history_qs.filter(earned_from__icontains=filter_category)

        if export_format in ['csv', 'excel']:
            import csv
            from django.http import HttpResponse
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reward_history.{export_format == "excel" and "xlsx" or "csv"}"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Trainer', 'Reward Type', 'Item Name', 'Amount', 'Earned From', 'Date', 'Status'])
            
            for log in history_qs:
                writer.writerow([
                    log.id,
                    log.trainer.trainer_name,
                    log.reward_type,
                    log.item_name or '',
                    log.amount,
                    log.earned_from,
                    log.date.strftime("%Y-%m-%d %H:%M:%S"),
                    log.status
                ])
            return response

        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(history_qs, request, view=self)

        results = []
        for log in (page if page is not None else history_qs):
            results.append({
                "id": log.id,
                "trainer": log.trainer.trainer_name,
                "reward": f"{log.reward_type}" if not log.item_name else f"{log.item_name}",
                "category": "Item" if log.item_name else log.reward_type,
                "amount": log.amount,
                "earned_from": log.earned_from,
                "date": log.date.strftime("%Y-%m-%d %H:%M:%S"),
                "status": log.status
            })

        if page is not None:
            return paginator.get_paginated_response(results)

        return Response(results, status=status.HTTP_200_OK)

class AdminRewardsAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.trainer_profile
        if profile.role != 'admin' and not request.user.is_staff:
            return Response({"message": "Access Denied: Admin privileges required."}, status=status.HTTP_403_FORBIDDEN)
            
        total_claims = RewardHistory.objects.count()
        
        from django.db.models import Count
        most_claimed_qs = RewardHistory.objects.values('reward_type').annotate(count=Count('id')).order_by('-count')
        most_claimed = most_claimed_qs[0]['reward_type'] if most_claimed_qs else "None"
        
        total_coins = RewardHistory.objects.filter(reward_type="Coins").aggregate(total=Sum('amount'))['total'] or 0
        total_xp = RewardHistory.objects.filter(reward_type="XP").aggregate(total=Sum('amount'))['total'] or 0
        total_crystals = RewardHistory.objects.filter(reward_type="Crystals").aggregate(total=Sum('amount'))['total'] or 0
        
        daily_claims = RewardHistory.objects.filter(earned_from__icontains="Daily").count()
        mission_claims = RewardHistory.objects.filter(earned_from__icontains="Mission").count()
        battle_claims = RewardHistory.objects.filter(earned_from__icontains="Battle").count()
        
        logs_qs = AnalyticsLog.objects.filter(event_type="admin_change").order_by('-timestamp')[:20]
        change_logs = []
        for log in logs_qs:
            change_logs.append({
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "admin": log.trainer.trainer_name if log.trainer else "System",
                "action": log.metadata.get("action", "unknown"),
                "details": str(log.metadata)
            })
            
        return Response({
            "total_claims": total_claims,
            "most_claimed": most_claimed,
            "total_coins": total_coins,
            "total_xp": total_xp,
            "total_crystals": total_crystals,
            "daily_claims": daily_claims,
            "mission_claims": mission_claims,
            "battle_claims": battle_claims,
            "change_logs": change_logs
        }, status=status.HTTP_200_OK)

class AdminMissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all().order_by('id')
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.trainer_profile
        if profile.role != 'admin' and not self.request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Access Denied: Admin privileges required.")
        return super().get_queryset()

    def perform_create(self, serializer):
        profile = self.request.user.trainer_profile
        mission = serializer.save()
        
        all_trainers = TrainerProfile.objects.all()
        for t in all_trainers:
            MissionProgress.objects.get_or_create(
                trainer=t,
                mission=mission,
                defaults={'required_progress': 3 if 'win' in mission.title.lower() else (5 if 'catch' in mission.title.lower() else 1)}
            )
            
        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "create_mission", "mission_id": mission.id, "title": mission.title}
        )

    def perform_update(self, serializer):
        profile = self.request.user.trainer_profile
        mission = serializer.save()
        
        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "update_mission", "mission_id": mission.id, "title": mission.title}
        )

    def perform_destroy(self, instance):
        profile = self.request.user.trainer_profile
        mission_id = instance.id
        title = instance.title
        
        instance.delete()
        
        AnalyticsLog.objects.create(
            event_type="admin_change",
            trainer=profile,
            metadata={"action": "delete_mission", "mission_id": mission_id, "title": title}
        )
