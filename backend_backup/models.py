from django.db import models
from django.contrib.auth.models import User

class TrainerProfile(models.Model):
    ROLE_CHOICES = (
        ('trainer', 'Trainer'),
        ('player', 'Player'),
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    trainer_name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.trainer_name} ({self.role})"
