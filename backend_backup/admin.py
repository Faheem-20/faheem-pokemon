from django.contrib import admin
from .models import TrainerProfile

@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ('trainer_name', 'user', 'role', 'level', 'xp', 'coins', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('trainer_name', 'user__email')
