from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TrainerProfile(models.Model):
    ROLE_CHOICES = (
        ('trainer', 'Trainer'),
        ('player', 'Player'),
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    trainer_name = models.CharField(max_length=120)
    avatar = models.CharField(max_length=255, default='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=100)
    region = models.CharField(max_length=100, default='Kanto')
    badges = models.JSONField(default=list, blank=True)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    battles_played = models.PositiveIntegerField(default=0)
    current_rank = models.CharField(max_length=50, default='Bronze')
    crystals = models.PositiveIntegerField(default=0)
    reward_points = models.PositiveIntegerField(default=0)
    login_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
    battle_pass_level = models.PositiveIntegerField(default=1)
    battle_pass_xp = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trainer_name} ({self.role})"

class CapturedPokemon(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='captured_pokemons')
    pokemon_id = models.CharField(max_length=50, blank=True, default='')  # Can store unique identifier or default to pk
    pokedex_number = models.PositiveIntegerField()
    name = models.CharField(max_length=100)
    type1 = models.CharField(max_length=50)
    type2 = models.CharField(max_length=50, blank=True, null=True)
    rarity = models.CharField(max_length=50)
    level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    hp = models.PositiveIntegerField()
    max_hp = models.PositiveIntegerField()
    attack = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    speed = models.PositiveIntegerField()
    special_attack = models.PositiveIntegerField()
    special_defense = models.PositiveIntegerField()
    nature = models.CharField(max_length=50, default='Hardy')
    ability = models.CharField(max_length=50, default='Overgrow')
    moves = models.JSONField(default=list, blank=True)
    image = models.CharField(max_length=255)
    shiny = models.BooleanField(default=False)
    is_in_party = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    captured_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.pokemon_id:
            self.pokemon_id = str(self.id)
            super().save(update_fields=['pokemon_id'])

    def __str__(self):
        return f"{self.name} (Lvl {self.level}) - Trainer: {self.trainer.trainer_name}"

class TrainerInventory(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='inventory')
    item_id = models.PositiveIntegerField()
    item_name = models.CharField(max_length=120)
    category = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    max_stack = models.PositiveIntegerField(default=99)

    class Meta:
        unique_together = ('trainer', 'item_name')

    def __str__(self):
        return f"{self.item_name} x{self.quantity} - {self.trainer.trainer_name}"

class BattleRecord(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='battle_records')
    opponent = models.CharField(max_length=120)
    arena = models.CharField(max_length=120)
    weather = models.CharField(max_length=120)
    battle_type = models.CharField(max_length=50, default='wild')
    winner = models.CharField(max_length=120)
    loser = models.CharField(max_length=120)
    xp_gained = models.PositiveIntegerField(default=0)
    coins_gained = models.PositiveIntegerField(default=0)
    battle_duration = models.PositiveIntegerField(default=0)  # In seconds
    pokemon_used = models.JSONField(default=list, blank=True)
    moves_used = models.JSONField(default=list, blank=True)
    items_used = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Battle vs {self.opponent} - Winner: {self.winner}"

class Mission(models.Model):
    TYPE_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('special', 'Special'),
        ('story', 'Story'),
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    reward_xp = models.PositiveIntegerField(default=0)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_items = models.JSONField(default=dict, blank=True)  # Format: {"Poke Ball": 5, "Potion": 2}
    reward_pokemon = models.JSONField(default=dict, blank=True) # Format: {"pokedex_number": 25, "name": "Pikachu", "level": 15}

    def __str__(self):
        return f"[{self.type.upper()}] {self.title}"

class MissionProgress(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='mission_progress')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    current_progress = models.PositiveIntegerField(default=0)
    required_progress = models.PositiveIntegerField(default=1)
    is_completed = models.BooleanField(default=False)
    claimed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trainer', 'mission')

    def __str__(self):
        return f"{self.trainer.trainer_name} - {self.mission.title} ({self.current_progress}/{self.required_progress})"

class ShopItem(models.Model):
    item_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    stock = models.IntegerField(default=-1)  # -1 for infinite stock
    rarity = models.CharField(max_length=50, default='Common')
    image = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - Price: {self.price} coins"

class PurchaseHistory(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='purchases')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    coins_spent = models.PositiveIntegerField()
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainer.trainer_name} bought {self.quantity}x {self.item.name}"

class KingdomMap(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='regions')
    region_id = models.CharField(max_length=50)  # e.g., 'kanto'
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='locked')  # locked / unlocked
    progress = models.PositiveIntegerField(default=0)
    gyms = models.PositiveIntegerField(default=0)
    legendary_count = models.PositiveIntegerField(default=0)
    completed_gyms = models.JSONField(default=list, blank=True)
    story_progress = models.JSONField(default=dict, blank=True)
    hidden_locations = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ('trainer', 'region_id')

    def __str__(self):
        return f"{self.name} ({self.status}) - {self.trainer.trainer_name}"

class Achievement(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=50)  # Battle, Collection, Exploration, Special
    points = models.PositiveIntegerField(default=10)
    badge_image = models.CharField(max_length=255, blank=True, null=True)
    target_value = models.PositiveIntegerField(default=1)
    xp_reward = models.PositiveIntegerField(default=0)
    coins_reward = models.PositiveIntegerField(default=0)
    crystal_reward = models.PositiveIntegerField(default=0)
    rarity = models.CharField(max_length=50, default='Common')  # Common, Rare, Epic, Legendary, Mythic

    def __str__(self):
        return self.title

class TrainerAchievement(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('trainer', 'achievement')

    def __str__(self):
        return f"{self.trainer.trainer_name} unlocked {self.achievement.title} (Claimed: {self.claimed})"

class BattleStatistics(models.Model):
    trainer = models.OneToOneField(TrainerProfile, on_delete=models.CASCADE, related_name='battle_stats')
    critical_hits = models.PositiveIntegerField(default=0)
    super_effective = models.PositiveIntegerField(default=0)
    accuracy_hits = models.PositiveIntegerField(default=0)
    accuracy_total_shots = models.PositiveIntegerField(default=0)
    damage_dealt = models.PositiveIntegerField(default=0)
    damage_taken = models.PositiveIntegerField(default=0)
    healing = models.PositiveIntegerField(default=0)
    pokemon_fainted = models.PositiveIntegerField(default=0)
    items_used = models.PositiveIntegerField(default=0)
    turns = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stats for {self.trainer.trainer_name}"

class Notification(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    category = models.CharField(max_length=50)  # Rewards, Mission Complete, Level Up, Shop Purchase, Admin Announcement, Battle Result
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] {self.title} - Read: {self.is_read}"

class FriendRequest(models.Model):
    sender = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='sent_friend_requests')
    receiver = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=20, default='pending')  # pending, accepted, rejected
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.trainer_name} -> {self.receiver.trainer_name} ({self.status})"

class Friend(models.Model):
    user1 = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='friends_as_user1')
    user2 = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='friends_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1.trainer_name} <-> {self.user2.trainer_name}"

class AdminAnnouncement(models.Model):
    title = models.CharField(max_length=150)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AnalyticsLog(models.Model):
    event_type = models.CharField(max_length=100)  # login, battle, purchase, etc.
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"

class RewardHistory(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='reward_history')
    reward_type = models.CharField(max_length=100)  # Coins, Crystals, Item, Badge, Title, etc.
    item_name = models.CharField(max_length=120, blank=True, null=True)
    amount = models.PositiveIntegerField(default=0)
    earned_from = models.CharField(max_length=120)  # Daily Login, Level Milestone, Event, Mission, Battle
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Claimed')

    def __str__(self):
        return f"{self.trainer.trainer_name} - {self.reward_type} x{self.amount} from {self.earned_from}"

class DailyRewardClaim(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='daily_claims')
    day_number = models.PositiveIntegerField()  # 1 to 30
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainer', 'day_number')

    def __str__(self):
        return f"{self.trainer.trainer_name} claimed Day {self.day_number}"

class LevelRewardClaim(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='level_claims')
    level = models.PositiveIntegerField()  # 5, 10, 15, etc.
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainer', 'level')

    def __str__(self):
        return f"{self.trainer.trainer_name} claimed Level {self.level} reward"

class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ('weekly', 'Weekly'),
        ('seasonal', 'Seasonal'),
        ('limited', 'Limited-Time'),
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, default='limited')
    reward_type = models.CharField(max_length=100)  # Coins, Crystals, Item, etc.
    item_name = models.CharField(max_length=120, blank=True, null=True)
    amount = models.PositiveIntegerField(default=0)
    image = models.CharField(max_length=255, default='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.event_type.upper()}] {self.title}"

class EventRewardClaim(models.Model):
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='event_claims')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='claims')
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainer', 'event')

    def __str__(self):
        return f"{self.trainer.trainer_name} claimed event: {self.event.title}"
