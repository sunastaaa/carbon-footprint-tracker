from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from django.db.models import Sum, F
from .models import ActivityType, CarbonLog, EcoGoal
from datetime import timedelta
import json


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('tracker:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})


@login_required
def dashboard(request):
    now = timezone.now()

    # Получаем все записи пользователя за текущий месяц
    month_logs = CarbonLog.objects.filter(
        user=request.user,
        date__year=now.year,
        date__month=now.month
    ).annotate(
        emission=F('value') * F('activity__co2_factor')
    )

    # Общий выброс за месяц
    total_emission = month_logs.aggregate(total=Sum('emission'))['total'] or 0

    # Группировка по категориям для круговой диаграммы
    by_category = month_logs.values(
        'activity__category',
        'activity__name'
    ).annotate(
        category_total=Sum('emission')
    ).order_by('-category_total')

    # Динамика по дням (последние 30 дней)
    thirty_days_ago = now - timedelta(days=30)
    daily_logs = CarbonLog.objects.filter(
        user=request.user,
        date__gte=thirty_days_ago
    ).annotate(
        emission=F('value') * F('activity__co2_factor')
    ).values('date').annotate(
        daily_total=Sum('emission')
    ).order_by('date')

    # Получаем или создаём цель пользователя
    goal, created = EcoGoal.objects.get_or_create(
        user=request.user,
        defaults={
            'monthly_limit': 150.0,
            'start_date': now.date()
        }
    )

    # Прогресс выполнения цели
    progress_percent = goal.progress_percent if goal.monthly_limit > 0 else 0

    trees_equivalent = round(total_emission * 12 / 22, 1)

    context = {
        'total_emission': round(total_emission, 2),
        'goal': goal,
        'progress_percent': progress_percent,
        'trees_equivalent': trees_equivalent,
        'category_labels': json.dumps([item['activity__name'] for item in by_category]),
        'category_values': json.dumps([round(item['category_total'], 2) for item in by_category]),
        'daily_labels': json.dumps([item['date'].strftime('%d.%m') for item in daily_logs]),
        'daily_values': json.dumps([round(item['daily_total'], 2) for item in daily_logs]),
    }

    return render(request, 'tracker/dashboard.html', context)


@login_required
def add_carbon_log(request):
    if request.method == 'POST':
        activity_id = request.POST.get('activity')
        value = float(request.POST.get('value'))
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')

        activity = get_object_or_404(ActivityType, id=activity_id)

        CarbonLog.objects.create(
            user=request.user,
            activity=activity,
            value=value,
            date=date,
            notes=notes
        )

        return redirect('tracker:dashboard')

    activities = ActivityType.objects.all().order_by('category', 'name')
    return render(request, 'tracker/add_log.html', {'activities': activities})


@login_required
def set_goal(request):
    goal, created = EcoGoal.objects.get_or_create(
        user=request.user,
        defaults={'monthly_limit': 150.0, 'start_date': timezone.now().date()}
    )

    if request.method == 'POST':
        goal.monthly_limit = float(request.POST.get('monthly_limit'))
        goal.save()
        return redirect('tracker:dashboard')

    return render(request, 'tracker/set_goal.html', {'goal': goal})


@login_required
def history(request):
    logs = CarbonLog.objects.filter(
        user=request.user
    ).annotate(
        emission=F('value') * F('activity__co2_factor')
    ).order_by('-date')

    return render(request, 'tracker/history.html', {'logs': logs})


@login_required
def delete_log(request, log_id):
    log = get_object_or_404(CarbonLog, id=log_id, user=request.user)
    log.delete()
    return redirect('tracker:history')