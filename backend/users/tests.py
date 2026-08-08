import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    TrainerProfile, CapturedPokemon, TrainerInventory, BattleRecord,
    Mission, MissionProgress, ShopItem, PurchaseHistory, KingdomMap,
    Achievement, TrainerAchievement, BattleStatistics, Notification,
    FriendRequest, Friend, RewardHistory, DailyRewardClaim, LevelRewardClaim,
    Event, EventRewardClaim
)

User = get_user_model()

class PokemonNexusAuthTests(APITestCase):

    def setUp(self):
        # Create test users for each role (username is email for login authentication)
        self.admin_user = User.objects.create_superuser(
            username='admin_test@pokemon.com',
            email='admin_test@pokemon.com',
            password='password123'
        )
        TrainerProfile.objects.create(
            user=self.admin_user,
            role='admin',
            trainer_name='Admin Champion'
        )
        self.trainer_user = User.objects.create_user(
            username='trainer_test@pokemon.com',
            email='trainer_test@pokemon.com',
            password='password123'
        )
        TrainerProfile.objects.create(
            user=self.trainer_user,
            role='trainer',
            trainer_name='Trainer Ash'
        )
        self.player_user = User.objects.create_user(
            username='player_test@pokemon.com',
            email='player_test@pokemon.com',
            password='password123'
        )
        TrainerProfile.objects.create(
            user=self.player_user,
            role='player',
            trainer_name='Player Red'
        )

    def test_registration_validation(self):
        # Test email required
        response = self.client.post('/api/auth/register/', {
            'password': 'password123',
            'confirmPassword': 'password123',
            'trainerName': 'New Trainer'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

        # Test passwords mismatch
        response = self.client.post('/api/auth/register/', {
            'email': 'new@pokemon.com',
            'password': 'password123',
            'confirmPassword': 'wrongpassword',
            'trainerName': 'New Trainer'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Passwords do not match')

        # Test successful registration
        response = self.client.post('/api/auth/register/', {
            'username': 'new_trainer',
            'email': 'new@pokemon.com',
            'password': 'password123',
            'confirmPassword': 'password123',
            'trainerName': 'New Trainer',
            'role': 'player'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'player')
        self.assertEqual(response.data['user']['trainerName'], 'New Trainer')

    def test_login_api(self):
        # Test invalid credentials
        response = self.client.post('/api/auth/login/', {
            'email': 'trainer_test@pokemon.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test successful login
        response = self.client.post('/api/auth/login/', {
            'email': 'trainer_test@pokemon.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'trainer')

    def test_profile_api_protected(self):
        # Test unprotected access
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate player
        self.client.force_authenticate(user=self.player_user)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'player_test@pokemon.com')

    def test_role_based_access_control(self):
        # 1. Admin Dashboards
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/api/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Trainer Dashboards
        self.client.force_authenticate(user=self.trainer_user)
        response = self.client.get('/api/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/api/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Player Dashboards
        self.client.force_authenticate(user=self.player_user)
        response = self.client.get('/api/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/api/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.player_user)
        response = self.client.post('/api/token/refresh/', {
            'refresh': str(refresh)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_management_access_and_crud(self):
        # 1. Non-admin listing users should be denied
        self.client.force_authenticate(user=self.player_user)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin listing users should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # 3. Admin retrieving single user should be allowed
        response = self.client.get(f'/api/users/{self.player_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'player_test@pokemon.com')

        # 4. Admin updating user should be allowed
        response = self.client.put(f'/api/users/{self.player_user.id}/', {
            'username': 'player_updated',
            'email': 'player_updated@pokemon.com',
            'role': 'trainer',
            'trainerName': 'Updated Name',
            'level': 5,
            'coins': 500,
            'is_active': False
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.player_user.refresh_from_db()
        profile = self.player_user.trainer_profile
        self.assertEqual(self.player_user.username, 'player_updated')
        self.assertEqual(profile.role, 'trainer')
        self.assertEqual(self.player_user.is_active, False)
        self.assertEqual(profile.coins, 500)

        # 5. Admin deleting user should be allowed
        response = self.client.delete(f'/api/users/{self.player_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.player_user.id).exists())


class PokemonNexusGameTests(APITestCase):

    def setUp(self):
        from .views_rewards import CONFIG_FILE
        import os
        if os.path.exists(CONFIG_FILE):
            try:
                os.remove(CONFIG_FILE)
            except Exception:
                pass

        # Setup trainer profile
        self.user = User.objects.create_user(
            username='ash@ketchum.com',
            email='ash@ketchum.com',
            password='pikachupower'
        )
        self.profile = TrainerProfile.objects.create(
            user=self.user,
            role='trainer',
            trainer_name='Ash Ketchum',
            coins=1000
        )
        self.client.force_authenticate(user=self.user)

    def test_captured_pokemon_limit_and_actions(self):
        # 1. Try to create a party of 7 pokemon and ensure it fails on the 7th
        for i in range(6):
            response = self.client.post('/api/pokemon/', {
                'pokedex_number': 25,
                'name': f'Pikachu {i}',
                'type1': 'Electric',
                'rarity': 'Common',
                'level': 5,
                'hp': 50,
                'max_hp': 50,
                'attack': 30,
                'defense': 30,
                'speed': 30,
                'special_attack': 30,
                'special_defense': 30,
                'image': 'pikachu.png',
                'is_in_party': True
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 7th party member should fail
        response = self.client.post('/api/pokemon/', {
            'pokedex_number': 6,
            'name': 'Charizard',
            'type1': 'Fire',
            'rarity': 'Rare',
            'level': 36,
            'hp': 150,
            'max_hp': 150,
            'attack': 80,
            'defense': 80,
            'speed': 80,
            'special_attack': 80,
            'special_defense': 80,
            'image': 'charizard.png',
            'is_in_party': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Verify we can add unlimited boxed pokemon (is_in_party=False)
        response = self.client.post('/api/pokemon/', {
            'pokedex_number': 6,
            'name': 'Charizard Boxed',
            'type1': 'Fire',
            'rarity': 'Rare',
            'level': 36,
            'hp': 150,
            'max_hp': 150,
            'attack': 80,
            'defense': 80,
            'speed': 80,
            'special_attack': 80,
            'special_defense': 80,
            'image': 'charizard.png',
            'is_in_party': False
        })
        if response.status_code != status.HTTP_201_CREATED:
            print("DEBUG: Boxed creation failed with:", response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pokemon_id = response.data['id']

        # 3. Test toggle party (remove from party)
        first_party_pokemon = CapturedPokemon.objects.filter(trainer=self.profile, is_in_party=True).first()
        response = self.client.post(f'/api/pokemon/{first_party_pokemon.id}/toggle-party/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CapturedPokemon.objects.get(id=first_party_pokemon.id).is_in_party)

        # 4. Favorite a Pokémon
        response = self.client.post(f'/api/pokemon/{pokemon_id}/toggle-favorite/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CapturedPokemon.objects.get(id=pokemon_id).is_favorite)

    def test_shop_purchase_and_inventory(self):
        # Setup shop item
        item = ShopItem.objects.create(
            item_id=1,
            name='Poke Ball',
            description='Standard ball',
            category='Poké Balls',
            price=200,
            stock=5
        )

        # 1. Purchase item successfully
        response = self.client.post(f'/api/shop/{item.id}/purchase/', {'quantity': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify coins and stock decreased
        self.profile.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(self.profile.coins, 600)  # 1000 - 400
        self.assertEqual(item.stock, 3)

        # Verify inventory item updated
        inv = TrainerInventory.objects.get(trainer=self.profile, item_name='Poke Ball')
        # Signals initialized default quantity to 50 + 2 bought = 52
        self.assertEqual(inv.quantity, 52)

        # 2. Purchase failing due to insufficient coins
        response = self.client.post(f'/api/shop/{item.id}/purchase/', {'quantity': 4})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_battle_record_rewards_and_missions(self):
        # Setup mission
        mission = Mission.objects.create(
            title="Win 1 Battles",
            description="Win one battle",
            type="daily",
            reward_xp=500,
            reward_coins=300
        )
        # Force progress assignment
        progress = MissionProgress.objects.create(
            trainer=self.profile,
            mission=mission,
            current_progress=0,
            required_progress=1
        )

        # 1. Record win battle
        response = self.client.post('/api/battles/', {
            'opponent': 'Gary Oak',
            'arena': 'Grass Arena',
            'weather': 'Clear',
            'battle_type': 'trainer',
            'winner': 'Ash Ketchum',
            'loser': 'Gary Oak',
            'xp_gained': 600,
            'coins_gained': 300,
            'stat_turns': 10,
            'stat_damage_dealt': 300
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('battle_rewards', response.data)
        self.assertEqual(response.data['battle_rewards']['xp'], 600)
        self.assertEqual(response.data['battle_rewards']['coins'], 300)
        self.assertEqual(response.data['battle_rewards']['reward_points'], 30)

        # 1.5 Duplicate log attempt should fail
        response_dup = self.client.post('/api/battles/', {
            'opponent': 'Gary Oak',
            'arena': 'Grass Arena',
            'weather': 'Clear',
            'battle_type': 'trainer',
            'winner': 'Ash Ketchum',
            'loser': 'Gary Oak',
            'xp_gained': 600,
            'coins_gained': 300,
            'stat_turns': 10,
            'stat_damage_dealt': 300,
            'started_at': response.data['battle']['started_at']
        })
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify profile wins, xp, and level
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.wins, 1)
        self.assertEqual(self.profile.xp, 600)
        self.assertEqual(self.profile.coins, 1300) # 1000 + 300 reward

        # Verify battle statistics
        stats = self.profile.battle_stats
        self.assertEqual(stats.turns, 10)
        self.assertEqual(stats.damage_dealt, 300)

        # Verify mission completed
        progress.refresh_from_db()
        self.assertTrue(progress.is_completed)

        # 2. Claim mission reward
        response = self.client.post(f'/api/missions/{progress.id}/claim/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.profile.refresh_from_db()
        progress.refresh_from_db()
        self.assertTrue(progress.claimed)
        self.assertEqual(self.profile.coins, 1600)  # 1300 + 300 reward
        self.assertGreater(self.profile.level, 1)

        # 3. Verify RewardHistory entries created
        self.assertTrue(RewardHistory.objects.filter(trainer=self.profile, reward_type="Coins", earned_from=f"Mission: {mission.title}").exists())
        self.assertTrue(RewardHistory.objects.filter(trainer=self.profile, reward_type="XP", earned_from=f"Mission: {mission.title}").exists())

        # 4. Double claim should fail
        response_dup = self.client.post(f'/api/missions/{progress.id}/claim/')
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leaderboard(self):
        # Create second user
        user2 = User.objects.create_user(username='gary@oak.com', password='pass')
        profile2 = TrainerProfile.objects.create(
            user=user2,
            trainer_name='Gary Oak',
            wins=5,
            level=10
        )
        self.profile.wins = 2
        self.profile.save()

        # Get leaderboard
        response = self.client.get('/api/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Gary Oak should be ranked 1st
        self.assertEqual(response.data[0]['trainer_name'], 'Gary Oak')
        self.assertEqual(response.data[1]['trainer_name'], 'Ash Ketchum')

    def test_friends_system(self):
        # Create user to send request to
        user2 = User.objects.create_user(username='misty@water.com', password='pass')
        profile2 = TrainerProfile.objects.create(user=user2, trainer_name='Misty')

        # 1. Send friend request
        response = self.client.post('/api/friends/send-request/', {'trainer_name': 'Misty'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify request created
        freq = FriendRequest.objects.get(sender=self.profile, receiver=profile2)
        self.assertEqual(freq.status, 'pending')

        # 2. Accept friend request
        self.client.force_authenticate(user=user2)
        response = self.client.post(f'/api/friends/{freq.id}/respond/', {'action': 'accept'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify they are friends
        self.assertTrue(Friend.objects.filter(user1=self.profile, user2=profile2).exists())

    def test_rewards_dashboard(self):
        # 1. Fetch dashboard
        response = self.client.get('/api/rewards/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_collected_rewards'], 0)
        self.assertEqual(response.data['total_coins_earned'], 0)
        self.assertEqual(response.data['total_crystals'], 0)

    def test_daily_login_rewards(self):
        # 1. Get daily rewards config
        response = self.client.get('/api/rewards/daily/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['login_streak'], 0)
        self.assertFalse(response.data['has_claimed_today'])

        # 2. Claim Day 1 reward (100 Coins)
        response = self.client.post('/api/rewards/daily/claim/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reward']['type'], 'Coins')
        self.assertEqual(response.data['reward']['amount'], 100)

        # 3. Verify profile has updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.login_streak, 1)
        self.assertEqual(self.profile.coins, 1100) # 1000 base + 100 reward

        # 4. Try to claim again today (should fail)
        response = self.client.post('/api/rewards/daily/claim/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_level_milestones(self):
        # 1. Get level rewards milestone list
        response = self.client.get('/api/rewards/level/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Try to claim Level 5 reward when level is 1 (should fail)
        response = self.client.post('/api/rewards/level/claim/', {'level': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Elevate trainer level to 5
        self.profile.level = 5
        self.profile.save()

        # 4. Claim Level 5 reward (Potion x5)
        response = self.client.post('/api/rewards/level/claim/', {'level': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reward']['type'], 'Item')
        self.assertEqual(response.data['reward']['item_name'], 'Potion')
        self.assertEqual(response.data['reward']['amount'], 5)

        # 5. Try to claim Level 5 reward again (should fail)
        response = self.client.post('/api/rewards/level/claim/', {'level': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_limited_time_events(self):
        # 1. Create an active event
        exp_date = timezone.now() + datetime.timedelta(days=2)
        event = Event.objects.create(
            title="Fire Type Challenge",
            description="Claim a Fire Stone!",
            event_type="limited",
            reward_type="Item",
            item_name="Fire Stone",
            amount=1,
            expires_at=exp_date
        )

        # 2. Fetch active events
        response = self.client.get('/api/rewards/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Claim event reward
        response = self.client.post('/api/rewards/events/claim/', {'event_id': event.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Check inventory updated
        inv = TrainerInventory.objects.get(trainer=self.profile, item_name="Fire Stone")
        self.assertEqual(inv.quantity, 4)

        # 5. Double claim should fail
        response = self.client.post('/api/rewards/events/claim/', {'event_id': event.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reward_history(self):
        # 1. Add some history records
        RewardHistory.objects.create(
            trainer=self.profile,
            reward_type="Coins",
            amount=500,
            earned_from="Battle Win",
            status="Claimed"
        )
        RewardHistory.objects.create(
            trainer=self.profile,
            reward_type="Crystals",
            amount=20,
            earned_from="Daily Login",
            status="Claimed"
        )

        # 2. Get history log
        response = self.client.get('/api/rewards/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        # 3. Search history
        response = self.client.get('/api/rewards/history/?search=Daily')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['earned_from'], 'Daily Login')

    def test_admin_rewards_management(self):
        # Read initial config so we can restore it at the end
        from .views_rewards import load_rewards_config, save_rewards_config
        original_config = load_rewards_config()
        
        try:
            # 1. Elevate profile to admin
            self.profile.role = 'admin'
            self.profile.save()

            # 2. Test Get Config Settings
            response = self.client.get('/api/admin/rewards/config/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("daily_rewards", response.data)
            
            # 3. Test Update Config Settings
            new_daily = response.data["daily_rewards"]
            new_daily[0]["amount"] = 999
            response = self.client.post('/api/admin/rewards/config/', {"daily_rewards": new_daily}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify changes took effect
            response = self.client.get('/api/admin/rewards/config/')
            self.assertEqual(response.data["daily_rewards"][0]["amount"], 999)

            # 4. Test Event CRUD
            event_payload = {
                "title": "Admin Promo Event",
                "description": "Promo rewards",
                "event_type": "limited",
                "reward_type": "Crystals",
                "amount": 777,
                "expires_at": "2026-12-31T23:59"
            }
            response = self.client.post('/api/admin/rewards/events/', event_payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            event_id = response.data["event"]["id"]
            
            put_payload = {
                "id": event_id,
                "title": "Updated Admin Promo Event",
                "amount": 888
            }
            response = self.client.put('/api/admin/rewards/events/', put_payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response = self.client.delete(f'/api/admin/rewards/events/?id={event_id}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # 5. Test Mission CRUD
            mission_payload = {
                "title": "Admin Created Quest",
                "description": "Solve it!",
                "type": "story",
                "reward_xp": 100,
                "reward_coins": 100,
                "reward_items": {"Great Ball": 1}
            }
            response = self.client.post('/api/admin/rewards/missions/', mission_payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            m_id = response.data["id"]
            
            patch_mission = {
                "title": "Updated Quest Title",
                "reward_xp": 200
            }
            response = self.client.patch(f'/api/admin/rewards/missions/{m_id}/', patch_mission, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            response = self.client.delete(f'/api/admin/rewards/missions/{m_id}/')
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

            # 6. Test Reward History search and filtering
            response = self.client.get('/api/admin/rewards/history/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # 7. Test Analytics
            response = self.client.get('/api/admin/rewards/analytics/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("total_claims", response.data)
            self.assertIn("change_logs", response.data)
        finally:
            save_rewards_config(original_config)


class PokemonNexusAchievementsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='trainer@nexus.com', password='password123', email='trainer@nexus.com')
        self.profile = TrainerProfile.objects.create(
            user=self.user,
            trainer_name="Test Trainer",
            level=1,
            xp=0,
            coins=1000,
            crystals=50,
            wins=0,
            login_streak=5
        )
        self.client.force_authenticate(user=self.user)

        self.ach_victory = Achievement.objects.create(
            title="First Victory",
            description="Win your first battle.",
            category="Battle",
            points=10,
            target_value=1,
            xp_reward=50,
            coins_reward=100,
            crystal_reward=10,
            rarity="Common",
            badge_image="first_victory"
        )
        self.ach_collector = Achievement.objects.create(
            title="Pokémon Collector",
            description="Catch 100 Pokémon.",
            category="Collection",
            points=50,
            target_value=100,
            xp_reward=200,
            coins_reward=500,
            crystal_reward=20,
            rarity="Rare",
            badge_image="pokemon_collector"
        )

    def test_get_achievements_list_and_stats(self):
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('achievements', response.data)
        self.assertIn('stats', response.data)
        self.assertIn('recently_earned', response.data)
        
        stats = response.data['stats']
        self.assertEqual(stats['total_achievements'], 2)
        self.assertEqual(stats['unlocked_count'], 0)
        self.assertEqual(stats['claimed_count'], 0)
        self.assertEqual(stats['completion_pct'], 0)

    def test_claim_achievement_rewards(self):
        response = self.client.post('/api/achievements/', {'achievement_id': self.ach_victory.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Requirements not met for this achievement.')

        self.profile.wins = 1
        self.profile.save()

        response = self.client.post('/api/achievements/', {'achievement_id': self.ach_victory.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Successfully claimed', response.data['message'])

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.xp, 50)
        self.assertEqual(self.profile.coins, 1100)
        self.assertEqual(self.profile.crystals, 60)

        response = self.client.post('/api/achievements/', {'achievement_id': self.ach_victory.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Achievement already claimed.')

    def test_all_achievement_progress_triggers(self):
        # 1. Gym Achievements
        ach_gym = Achievement.objects.create(
            title="Gym Challenger",
            description="Defeat 10 Gym Leaders.",
            category="Gym",
            points=100,
            target_value=10,
            xp_reward=150,
            coins_reward=300,
            crystal_reward=15,
            rarity="Rare"
        )
        self.profile.badges = ["badge1", "badge2", "badge3", "badge4", "badge5", "badge6", "badge7", "badge8", "badge9", "badge10"]
        self.profile.save()

        # 2. Collection Achievements
        ach_collection = Achievement.objects.create(
            title="Pokémon Collector",
            description="Catch 100 Pokémon.",
            category="Collection",
            points=50,
            target_value=100,
            xp_reward=200,
            coins_reward=500,
            crystal_reward=20,
            rarity="Rare"
        )
        pokemon_list = [
            CapturedPokemon(
                trainer=self.profile,
                pokemon_id=i,
                pokedex_number=25,
                name=f"Poke_{i}",
                type1="Electric",
                rarity="Common",
                level=5,
                hp=50,
                max_hp=50,
                attack=30,
                defense=30,
                speed=30,
                special_attack=30,
                special_defense=30,
                image="pikachu.png"
            ) for i in range(100)
        ]
        CapturedPokemon.objects.bulk_create(pokemon_list)

        # 3. Exploration Achievements
        ach_exploration = Achievement.objects.create(
            title="Explorer",
            description="Visit 50 unique locations.",
            category="Exploration",
            points=50,
            target_value=50,
            xp_reward=120,
            coins_reward=250,
            crystal_reward=12,
            rarity="Epic"
        )
        kanto_region = KingdomMap.objects.get(trainer=self.profile, region_id="kanto")
        kanto_region.progress = 50
        kanto_region.save()

        # 4. Legendary Achievements
        ach_legendary = Achievement.objects.create(
            title="Legendary Hunter",
            description="Catch a Legendary Pokémon.",
            category="Legendary",
            points=300,
            target_value=1,
            xp_reward=500,
            coins_reward=1000,
            crystal_reward=50,
            rarity="Legendary"
        )
        CapturedPokemon.objects.create(
            trainer=self.profile,
            pokemon_id=999,
            pokedex_number=150,
            name="Mewtwo",
            type1="Psychic",
            rarity="Legendary",
            level=70,
            hp=200,
            max_hp=200,
            attack=110,
            defense=90,
            speed=130,
            special_attack=154,
            special_defense=90,
            image="mewtwo.png"
        )

        # 5. Login Achievements
        ach_login = Achievement.objects.create(
            title="Daily Login Streak",
            description="Login for 30 consecutive days.",
            category="Login",
            points=150,
            target_value=30,
            xp_reward=300,
            coins_reward=400,
            crystal_reward=20,
            rarity="Legendary"
        )
        self.profile.login_streak = 30
        self.profile.save()

        # 6. Level Achievements
        ach_level = Achievement.objects.create(
            title="Novice Level",
            description="Reach Trainer Level 10.",
            category="Level",
            points=100,
            target_value=10,
            xp_reward=100,
            coins_reward=200,
            crystal_reward=2,
            rarity="Common"
        )
        self.profile.level = 10
        self.profile.save()

        # 7. Rewards Achievements
        ach_rewards = Achievement.objects.create(
            title="Milestone Claimer",
            description="Claim 5 rewards from the Reward Center.",
            category="Rewards",
            points=50,
            target_value=5,
            xp_reward=150,
            coins_reward=300,
            crystal_reward=3,
            rarity="Common"
        )
        for i in range(5):
            RewardHistory.objects.create(trainer=self.profile, reward_type="Coins", amount=100, earned_from=f"Test Reward {i}", status="Claimed")

        # Get Achievements List & Validate Progress Counts
        response = self.client.get('/api/achievements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        ach_map = {a['title']: a for a in response.data['achievements']}
        self.assertTrue(ach_map["Gym Challenger"]['unlocked'])
        self.assertEqual(ach_map["Gym Challenger"]['progress'], 10)
        
        self.assertTrue(ach_map["Pokémon Collector"]['unlocked'])
        self.assertEqual(ach_map["Pokémon Collector"]['progress'], 100)
        
        self.assertTrue(ach_map["Explorer"]['unlocked'])
        self.assertEqual(ach_map["Explorer"]['progress'], 50)
        
        self.assertTrue(ach_map["Legendary Hunter"]['unlocked'])
        self.assertEqual(ach_map["Legendary Hunter"]['progress'], 1)

        self.assertTrue(ach_map["Daily Login Streak"]['unlocked'])
        self.assertEqual(ach_map["Daily Login Streak"]['progress'], 30)

        self.assertTrue(ach_map["Novice Level"]['unlocked'])
        self.assertEqual(ach_map["Novice Level"]['progress'], 10)

        self.assertTrue(ach_map["Milestone Claimer"]['unlocked'])
        self.assertEqual(ach_map["Milestone Claimer"]['progress'], 5)

        # Claim All Rewards
        for ach_obj in [ach_gym, ach_collection, ach_exploration, ach_legendary, ach_login, ach_level, ach_rewards]:
            claim_res = self.client.post('/api/achievements/', {'achievement_id': ach_obj.id})
            self.assertEqual(claim_res.status_code, status.HTTP_200_OK)

