from django.contrib import admin
from .models import ActivityType, CarbonLog, EcoGoal

admin.site.register(ActivityType)
admin.site.register(CarbonLog)
admin.site.register(EcoGoal)