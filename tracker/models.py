from django.db import models
from django.contrib.auth.models import User


class ActivityType(models.Model):
    CATEGORY_CHOICES = [
        ('transport', 'Транспорт'),
        ('energy', 'Энергия'),
        ('food', 'Питание'),
        ('shopping', 'Покупки'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название активности")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория")
    co2_factor = models.FloatField(verbose_name="Коэффициент выбросов (кг CO₂ на ед.)")
    unit = models.CharField(max_length=20, verbose_name="Единица измерения (км, кВт·ч, кг)")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Тип активности"
        verbose_name_plural = "Типы активностей"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class CarbonLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carbon_logs', verbose_name="Пользователь")
    activity = models.ForeignKey(ActivityType, on_delete=models.PROTECT, verbose_name="Тип активности")
    value = models.FloatField(verbose_name="Количество")
    date = models.DateField(verbose_name="Дата активности")
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Город")  # ← НОВОЕ ПОЛЕ
    notes = models.CharField(max_length=200, blank=True, null=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")

    class Meta:
        verbose_name = "Запись об активности"
        verbose_name_plural = "Записи об активностях"
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.activity.name} ({self.date})"

    @property
    def co2_emission(self):
        return round(self.value * self.activity.co2_factor, 2)


class EcoGoal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='eco_goal', verbose_name="Пользователь")
    monthly_limit = models.FloatField(verbose_name="Лимит кг CO₂ в месяц")
    start_date = models.DateField(verbose_name="Дата начала отслеживания")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Эко-цель"
        verbose_name_plural = "Эко-цели"

    def __str__(self):
        return f"Цель {self.user.username}: {self.monthly_limit} кг/мес"

    @property
    def current_month_total(self):
        from django.utils import timezone
        now = timezone.now()
        logs = self.user.carbon_logs.filter(date__year=now.year, date__month=now.month)
        return sum(log.co2_emission for log in logs)

    @property
    def progress_percent(self):
        if self.monthly_limit == 0:
            return 0
        percent = (self.current_month_total / self.monthly_limit) * 100
        return round(min(percent, 100), 1)