from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import TrainerProfile

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
        # Admin can access admin-dashboard
        response = self.client.get('/api/auth/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin cannot access trainer-dashboard or player-dashboard
        response = self.client.get('/api/auth/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/auth/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Trainer Dashboards
        self.client.force_authenticate(user=self.trainer_user)
        # Trainer can access trainer-dashboard
        response = self.client.get('/api/auth/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Trainer cannot access admin-dashboard or player-dashboard
        response = self.client.get('/api/auth/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/auth/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Player Dashboards
        self.client.force_authenticate(user=self.player_user)
        # Player can access player-dashboard
        response = self.client.get('/api/auth/player-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Player cannot access admin-dashboard or trainer-dashboard
        response = self.client.get('/api/auth/admin-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.get('/api/auth/trainer-dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh(self):
        # Generate token pair for player
        refresh = RefreshToken.for_user(self.player_user)
        
        response = self.client.post('/api/auth/token/refresh/', {
            'refresh': str(refresh)
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_management_access_and_crud(self):
        # 1. Non-admin listing users should be denied
        self.client.force_authenticate(user=self.player_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin listing users should be allowed
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # admin_test, trainer_test, player_test

        # 3. Admin retrieving single user should be allowed
        response = self.client.get(f'/api/auth/users/{self.player_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'player_test@pokemon.com')

        # 4. Admin updating user should be allowed
        response = self.client.put(f'/api/auth/users/{self.player_user.id}/', {
            'username': 'player_updated',
            'email': 'player_updated@pokemon.com',
            'role': 'trainer',
            'trainerName': 'Updated Name',
            'level': 5,
            'coins': 500,
            'is_active': False
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes in DB
        self.player_user.refresh_from_db()
        profile = self.player_user.trainer_profile
        self.assertEqual(self.player_user.username, 'player_updated')
        self.assertEqual(profile.role, 'trainer')
        self.assertEqual(self.player_user.is_active, False)
        self.assertEqual(profile.coins, 500)

        # 5. Admin deleting user should be allowed
        response = self.client.delete(f'/api/auth/users/{self.player_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.player_user.id).exists())

