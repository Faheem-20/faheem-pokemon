from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import TrainerProfile
from .permissions import IsAdminRole, IsTrainerRole, IsPlayerRole
from .serializers import RegisterSerializer, LoginSerializer, user_payload, make_jwt_pair


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


class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'message': 'User dashboard access granted',
            'user': user_payload(request.user),
            'missions': [
                {'title': 'Catch 5 Pokémon', 'reward': '+500 XP'},
                {'title': 'Win 3 Battles', 'reward': '+800 XP'},
            ]
        })


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        total_users = User.objects.count()
        admins = TrainerProfile.objects.filter(role='admin').count() + User.objects.filter(is_superuser=True).count()
        return Response({
            'message': 'Admin access granted',
            'stats': {
                'totalUsers': total_users,
                'adminUsers': admins,
                'normalUsers': max(total_users - admins, 0),
                'totalCoins': sum(p.coins for p in TrainerProfile.objects.all()),
            }
        })

import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

# Simple in-memory OTP store
OTP_STORE = {}

def check_and_correct_email_typo(identifier):
    """
    Checks if the identifier is an email containing common typos in the domain
    and returns the corrected email.
    """
    if not identifier or '@' not in identifier:
        return identifier
    
    parts = identifier.split('@')
    domain = parts[-1].strip().lower()
    local = '@'.join(parts[:-1]).strip()
    
    # Common typos for gmail.com
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
        
        # Look up by email or username
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
            
        # Try correcting common domain typos
        if not user:
            corrected = check_and_correct_email_typo(identifier)
            if corrected != identifier:
                user = User.objects.filter(email__iexact=corrected).first()
            
        if not user:
            return Response({'message': 'No account found with this email or username'}, status=status.HTTP_404_NOT_FOUND)
        
        email = user.email.lower().strip()
        
        # Generate 6-digit OTP
        otp_code = f"{random.randint(100000, 999999)}"
        expiry = timezone.now() + timedelta(minutes=10)
        
        OTP_STORE[email] = {
            'otp': otp_code,
            'expiry': expiry
        }
        
        # Print for terminal debugging
        print("\n" + "="*50)
        print(f" OTP CODE GENERATED FOR {email}: {otp_code} ")
        print("="*50 + "\n")
        
        # Send actual email to Trainer using Django send_mail
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
        
        # We try to send if password is set and not the placeholder
        host_pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        if host_pw and host_pw != 'your-google-app-password-here':
            try:
                send_mail(subject, message, from_email, [email], fail_silently=False)
                email_sent = True
                print(f"DEBUG: Successfully sent OTP email to {email}", flush=True)
            except Exception as e:
                email_error = str(e)
                print(f"ERROR: Failed to send email to {email}: {email_error}", flush=True)
        else:
            print("DEBUG: Email was not sent because EMAIL_HOST_PASSWORD is still set to placeholder.", flush=True)
            email_error = "Email SMTP not configured (needs App Password in settings.py)."
            
        return Response({
            'message': 'OTP sent successfully' if email_sent else f'OTP generated. {email_error}',
            'email': email,  # Return the actual email in case they entered username
            'otp': otp_code,  # Returned for easy testing
            'email_sent': email_sent
        }, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp', '').strip()
        
        if not identifier or not otp:
            return Response({'message': 'Email/Username and OTP code are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Find user email first
        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=identifier).first()
            
        # Try correcting common domain typos
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
            
        # Try correcting common domain typos
        if not user:
            corrected = check_and_correct_email_typo(identifier)
            if corrected != identifier:
                user = User.objects.filter(email__iexact=corrected).first()
                
        if not user:
            return Response({'message': 'No account found'}, status=status.HTTP_404_NOT_FOUND)
            
        email = user.email.lower().strip()
            
        stored = OTP_STORE.get(email)
        if not stored or stored['otp'] != otp or timezone.now() > stored['expiry']:
            return Response({'message': 'Invalid or expired OTP. Please verify again'}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        # Clear the OTP
        OTP_STORE.pop(email, None)
        
        return Response({
            'message': 'Your Account Password Has Been Reset Successfully'
        }, status=status.HTTP_200_OK)


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
            
            # Update user fields
            if 'username' in data:
                user.username = data['username']
            if 'email' in data:
                user.email = data['email']
            if 'is_active' in data:
                val = data['is_active']
                if isinstance(val, str):
                    user.is_active = val.lower() in ('true', '1')
                else:
                    user.is_active = bool(val)
            user.save()
            
            # Update trainer profile fields
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
