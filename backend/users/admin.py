from django.contrib import admin
from .models import (
    TrainerProfile, CapturedPokemon, TrainerInventory, BattleRecord,
    Mission, MissionProgress, ShopItem, PurchaseHistory, KingdomMap,
    Achievement, TrainerAchievement, BattleStatistics, Notification,
    FriendRequest, Friend, AdminAnnouncement, AnalyticsLog,
    RewardHistory, DailyRewardClaim, LevelRewardClaim, Event, EventRewardClaim
)

@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ('trainer_name', 'user', 'role', 'level', 'xp', 'coins', 'wins', 'losses', 'current_rank')
    list_filter = ('role', 'current_rank', 'created_at')
    search_fields = ('trainer_name', 'user__email', 'user__username')

@admin.register(CapturedPokemon)
class CapturedPokemonAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'pokemon_id', 'pokedex_number', 'level', 'rarity', 'is_in_party', 'is_favorite', 'captured_at')
    list_filter = ('rarity', 'is_in_party', 'is_favorite', 'type1')
    search_fields = ('name', 'trainer__trainer_name')

@admin.register(TrainerInventory)
class TrainerInventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'trainer', 'category', 'quantity', 'max_stack')
    list_filter = ('category',)
    search_fields = ('item_name', 'trainer__trainer_name')

@admin.register(BattleRecord)
class BattleRecordAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'opponent', 'arena', 'winner', 'coins_gained', 'xp_gained', 'started_at')
    list_filter = ('arena', 'battle_type', 'started_at')
    search_fields = ('trainer__trainer_name', 'opponent')

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'reward_xp', 'reward_coins')
    list_filter = ('type',)
    search_fields = ('title', 'description')

@admin.register(MissionProgress)
class MissionProgressAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'mission', 'current_progress', 'required_progress', 'is_completed', 'claimed')
    list_filter = ('is_completed', 'claimed')
    search_fields = ('trainer__trainer_name', 'mission__title')

@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_id', 'category', 'price', 'stock', 'rarity')
    list_filter = ('category', 'rarity')
    search_fields = ('name',)

@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'item', 'quantity', 'coins_spent', 'purchase_date')
    list_filter = ('purchase_date',)
    search_fields = ('trainer__trainer_name', 'item__name')

@admin.register(KingdomMap)
class KingdomMapAdmin(admin.ModelAdmin):
    list_display = ('name', 'trainer', 'region_id', 'status', 'progress')
    list_filter = ('status',)
    search_fields = ('name', 'trainer__trainer_name')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'points')
    list_filter = ('category',)
    search_fields = ('title',)

@admin.register(TrainerAchievement)
class TrainerAchievementAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'achievement', 'unlocked_at')
    search_fields = ('trainer__trainer_name', 'achievement__title')

@admin.register(BattleStatistics)
class BattleStatisticsAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'critical_hits', 'super_effective', 'damage_dealt', 'damage_taken', 'turns')
    search_fields = ('trainer__trainer_name',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'trainer', 'category', 'is_read', 'created_at')
    list_filter = ('category', 'is_read')
    search_fields = ('title', 'trainer__trainer_name')

@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__trainer_name', 'receiver__trainer_name')

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    search_fields = ('user1__trainer_name', 'user2__trainer_name')

@admin.register(AdminAnnouncement)
class AdminAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(AnalyticsLog)
class AnalyticsLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'trainer', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('event_type', 'trainer__trainer_name')

@admin.register(RewardHistory)
class RewardHistoryAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'reward_type', 'item_name', 'amount', 'earned_from', 'date', 'status')
    list_filter = ('reward_type', 'earned_from', 'status', 'date')
    search_fields = ('trainer__trainer_name', 'item_name', 'earned_from')

@admin.register(DailyRewardClaim)
class DailyRewardClaimAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'day_number', 'claimed_at')
    list_filter = ('day_number', 'claimed_at')
    search_fields = ('trainer__trainer_name',)

@admin.register(LevelRewardClaim)
class LevelRewardClaimAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'level', 'claimed_at')
    list_filter = ('level', 'claimed_at')
    search_fields = ('trainer__trainer_name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'reward_type', 'item_name', 'amount', 'expires_at')
    list_filter = ('event_type', 'expires_at')
    search_fields = ('title', 'description')

@admin.register(EventRewardClaim)
class EventRewardClaimAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'event', 'claimed_at')
    search_fields = ('trainer__trainer_name', 'event__title')
