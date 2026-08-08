from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, ProfileView, ForgotPasswordView, VerifyOTPView, ResetPasswordView,
    UserListView, UserDetailView, AdminDashboardView, TrainerDashboardView, PlayerDashboardView,
    AdminStatsView, AdminAnnouncementView, LeaderboardView, AchievementView,
    CapturedPokemonViewSet, TrainerInventoryViewSet, BattleRecordViewSet,
    MissionProgressViewSet, ShopItemViewSet, KingdomMapViewSet, NotificationViewSet, FriendViewSet
)
from .views_rewards import (
    RewardsDashboardView, DailyRewardView, DailyRewardClaimView,
    LevelRewardView, LevelRewardClaimView, EventRewardView,
    EventRewardClaimView, RewardHistoryView, AdminEventConfigView,
    AdminRewardsConfigView, AdminRewardHistoryView, AdminRewardsAnalyticsView,
    AdminMissionViewSet
)

router = DefaultRouter()
router.register(r'pokemon', CapturedPokemonViewSet, basename='pokemon')
router.register(r'inventory', TrainerInventoryViewSet, basename='inventory')
router.register(r'battles', BattleRecordViewSet, basename='battles')
router.register(r'missions', MissionProgressViewSet, basename='missions')
router.register(r'shop', ShopItemViewSet, basename='shop')
router.register(r'regions', KingdomMapViewSet, basename='regions')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'friends', FriendViewSet, basename='friends')
router.register(r'admin/rewards/missions', AdminMissionViewSet, basename='admin-rewards-missions')

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),

    # Authentication Endpoints
    path('auth/register', RegisterView.as_view()),
    path('auth/register/', RegisterView.as_view()),
    path('auth/login', LoginView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/profile', ProfileView.as_view()),
    path('auth/profile/', ProfileView.as_view()),
    
    # Forgot Password Flow
    path('auth/forgot-password', ForgotPasswordView.as_view()),
    path('auth/forgot-password/', ForgotPasswordView.as_view()),
    path('auth/verify-otp', VerifyOTPView.as_view()),
    path('auth/verify-otp/', VerifyOTPView.as_view()),
    path('auth/reset-password', ResetPasswordView.as_view()),
    path('auth/reset-password/', ResetPasswordView.as_view()),
    
    # JWT Token Refresh
    path('token/refresh', TokenRefreshView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    
    # User Management Endpoints (Admin)
    path('users', UserListView.as_view()),
    path('users/', UserListView.as_view()),
    path('users/<int:pk>', UserDetailView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view()),
    path('auth/users', UserListView.as_view()),
    path('auth/users/', UserListView.as_view()),
    path('auth/users/<int:pk>', UserDetailView.as_view()),
    path('auth/users/<int:pk>/', UserDetailView.as_view()),
    
    # Dashboard Endpoints
    path('admin-dashboard', AdminDashboardView.as_view()),
    path('admin-dashboard/', AdminDashboardView.as_view()),
    path('trainer-dashboard', TrainerDashboardView.as_view()),
    path('trainer-dashboard/', TrainerDashboardView.as_view()),
    path('player-dashboard', PlayerDashboardView.as_view()),
    path('player-dashboard/', PlayerDashboardView.as_view()),
    
    # Admin Stats & Announcement
    path('admin/stats', AdminStatsView.as_view()),
    path('admin/stats/', AdminStatsView.as_view()),
    path('admin/announcement', AdminAnnouncementView.as_view()),
    path('admin/announcement/', AdminAnnouncementView.as_view()),
    
    # Game Info Endpoints
    path('leaderboard', LeaderboardView.as_view()),
    path('leaderboard/', LeaderboardView.as_view()),
    path('achievements', AchievementView.as_view()),
    path('achievements/', AchievementView.as_view()),
    
    # Rewards Endpoints
    path('rewards/dashboard', RewardsDashboardView.as_view()),
    path('rewards/dashboard/', RewardsDashboardView.as_view()),
    path('rewards/daily', DailyRewardView.as_view()),
    path('rewards/daily/', DailyRewardView.as_view()),
    path('rewards/daily/claim', DailyRewardClaimView.as_view()),
    path('rewards/daily/claim/', DailyRewardClaimView.as_view()),
    path('rewards/level', LevelRewardView.as_view()),
    path('rewards/level/', LevelRewardView.as_view()),
    path('rewards/level/claim', LevelRewardClaimView.as_view()),
    path('rewards/level/claim/', LevelRewardClaimView.as_view()),
    path('rewards/events', EventRewardView.as_view()),
    path('rewards/events/', EventRewardView.as_view()),
    path('rewards/events/claim', EventRewardClaimView.as_view()),
    path('rewards/events/claim/', EventRewardClaimView.as_view()),
    path('rewards/history', RewardHistoryView.as_view()),
    path('rewards/history/', RewardHistoryView.as_view()),
    path('admin/rewards/config', AdminRewardsConfigView.as_view()),
    path('admin/rewards/config/', AdminRewardsConfigView.as_view()),
    path('admin/rewards/events', AdminEventConfigView.as_view()),
    path('admin/rewards/events/', AdminEventConfigView.as_view()),
    path('admin/rewards/history', AdminRewardHistoryView.as_view()),
    path('admin/rewards/history/', AdminRewardHistoryView.as_view()),
    path('admin/rewards/analytics', AdminRewardsAnalyticsView.as_view()),
    path('admin/rewards/analytics/', AdminRewardsAnalyticsView.as_view()),
]
