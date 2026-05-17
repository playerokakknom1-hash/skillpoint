from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import models
from django.utils import timezone
from .models import Team, Tournament, Match, FriendRequest
import random
import math

def home(request):
    tournaments = Tournament.objects.filter(status='registration').order_by('-created_at')[:5]
    return render(request, 'tournaments/home.html', {'tournaments': tournaments})

def tournaments_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})

def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = tournament.matches.all().order_by('round_number', 'match_order')
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'matches': matches,
    })

@login_required
def create_tournament(request):
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'Только администраторы могут создавать турниры')
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        max_teams = request.POST.get('max_teams')
        team_size = request.POST.get('team_size')
        registration_deadline = request.POST.get('registration_deadline')
        
        if registration_deadline:
            registration_deadline = timezone.datetime.fromisoformat(registration_deadline)
        else:
            registration_deadline = None
        
        tournament = Tournament.objects.create(
            name=name,
            description=description,
            max_teams=int(max_teams),
            team_size=int(team_size),
            created_by=request.user,
            status='registration',
            registration_deadline=registration_deadline
        )
        messages.success(request, f'Турнир "{name}" создан!')
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    return render(request, 'tournaments/create_tournament.html')

@login_required
def create_team(request):
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        
        if Team.objects.filter(captain=request.user).exists():
            messages.error(request, 'У вас уже есть команда!')
            return redirect('my_team')
        
        team = Team.objects.create(name=team_name, captain=request.user)
        messages.success(request, f'Команда "{team_name}" создана!')
        return redirect('my_team')
    
    return render(request, 'tournaments/create_team.html')

@login_required
def my_team(request):
    try:
        team = Team.objects.get(captain=request.user)
        return render(request, 'tournaments/my_team.html', {'team': team})
    except Team.DoesNotExist:
        return redirect('create_team')

@login_required
def join_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Проверка, что регистрация ещё открыта
    if tournament.is_registration_closed():
        messages.error(request, 'Регистрация на этот турнир закрыта!')
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    try:
        team = Team.objects.get(captain=request.user)
        
        if team in tournament.registered_teams.all():
            messages.error(request, 'Вы уже зарегистрированы!')
        elif tournament.registered_teams.count() >= tournament.max_teams:
            messages.error(request, 'Турнир заполнен!')
        else:
            tournament.registered_teams.add(team)
            messages.success(request, f'Команда "{team.name}" зарегистрирована!')
    except Team.DoesNotExist:
        messages.error(request, 'Сначала создайте команду!')
        return redirect('create_team')
    
    return redirect('tournament_detail', tournament_id=tournament.id)

@login_required
def leave_team(request):
    try:
        team = Team.objects.get(captain=request.user)
        messages.error(request, 'Вы капитан. Чтобы выйти, сначала передайте капитанство или удалите команду')
    except Team.DoesNotExist:
        team = request.user.teams.first()
        if team:
            team.members.remove(request.user)
            messages.success(request, f'Вы вышли из команды "{team.name}"')
        else:
            messages.error(request, 'Вы не состоите в команде')
    
    return redirect('my_team')

@login_required
def disband_team(request):
    try:
        team = Team.objects.get(captain=request.user)
        team.delete()
        messages.success(request, 'Команда распущена')
    except Team.DoesNotExist:
        messages.error(request, 'У вас нет команды')
    
    return redirect('home')

@login_required
def generate_bracket(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.user != tournament.created_by and not request.user.is_superuser:
        messages.error(request, 'Только создатель турнира может генерировать сетку')
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    teams = list(tournament.registered_teams.all())
    num_teams = len(teams)
    
    if num_teams < 2:
        messages.error(request, 'Недостаточно команд для генерации сетки')
        return redirect('tournament_detail', tournament_id=tournament.id)
    
    tournament.matches.all().delete()
    
    random.shuffle(teams)
    
    next_power = 2 ** math.ceil(math.log2(num_teams))
    while len(teams) < next_power:
        teams.append(None)
    
    round_num = 1
    current_round_teams = teams
    match_order = 0
    
    while len(current_round_teams) >= 2:
        next_round_teams = []
        for i in range(0, len(current_round_teams), 2):
            team1 = current_round_teams[i]
            team2 = current_round_teams[i+1] if i+1 < len(current_round_teams) else None
            
            Match.objects.create(
                tournament=tournament,
                team1=team1,
                team2=team2,
                round_number=round_num,
                match_order=match_order
            )
            match_order += 1
            next_round_teams.append(None)
        
        current_round_teams = next_round_teams
        round_num += 1
    
    tournament.status = 'in_progress'
    tournament.save()
    
    messages.success(request, 'Турнирная сетка сгенерирована!')
    return redirect('tournament_detail', tournament_id=tournament.id)

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'tournaments/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь уже существует')
            return render(request, 'tournaments/register.html')
        
        user = User.objects.create_user(username=username, password=password1)
        login(request, user)
        messages.success(request, 'Регистрация успешна!')
        return redirect('home')
    
    return render(request, 'tournaments/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя или пароль')
    return render(request, 'tournaments/login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def friends_list(request):
    sent_requests = FriendRequest.objects.filter(from_user=request.user, is_accepted=False)
    received_requests = FriendRequest.objects.filter(to_user=request.user, is_accepted=False)
    
    friends = User.objects.filter(
        models.Q(sent_requests__to_user=request.user, sent_requests__is_accepted=True) |
        models.Q(received_requests__from_user=request.user, received_requests__is_accepted=True)
    ).distinct()
    
    all_users = User.objects.exclude(id=request.user.id).exclude(id__in=friends)
    
    return render(request, 'tournaments/friends.html', {
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'friends': friends,
        'all_users': all_users
    })

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if request.user == to_user:
        messages.error(request, 'Нельзя добавить самого себя')
    elif FriendRequest.objects.filter(from_user=request.user, to_user=to_user, is_accepted=False).exists():
        messages.error(request, 'Заявка уже отправлена')
    else:
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, f'Заявка отправлена {to_user.username}')
    return redirect('friends_list')

@login_required
def accept_friend_request(request, request_id):
    friend_req = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_req.is_accepted = True
    friend_req.save()
    messages.success(request, f'{friend_req.from_user.username} теперь в друзьях')
    return redirect('friends_list')

@login_required
def add_friend_to_team(request, user_id):
    team = get_object_or_404(Team, captain=request.user)
    friend = get_object_or_404(User, id=user_id)
    
    is_friend = FriendRequest.objects.filter(
        models.Q(from_user=request.user, to_user=friend, is_accepted=True) |
        models.Q(from_user=friend, to_user=request.user, is_accepted=True)
    ).exists()
    
    if not is_friend:
        messages.error(request, 'Этот пользователь не в друзьях')
    elif team.members.filter(id=friend.id).exists():
        messages.error(request, 'Уже в команде')
    else:
        team.members.add(friend)
        messages.success(request, f'{friend.username} добавлен в команду {team.name}')
    
    return redirect('my_team')

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    friend_req = FriendRequest.objects.filter(
        models.Q(from_user=request.user, to_user=friend) | models.Q(from_user=friend, to_user=request.user),
        is_accepted=True
    ).first()
    
    if friend_req:
        friend_req.delete()
        messages.success(request, f'{friend.username} удалён из друзей')
    
    return redirect('friends_list')

from django.views.decorators.csrf import csrf_exempt
import json
import smtplib
from email.mime.text import MIMEText

@csrf_exempt
def support_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            message = data.get('message')
            
            # Отправка на email администратора (настройте под себя)
            # Пока просто сохраняем в лог
            with open('/tmp/support_messages.log', 'a') as f:
                f.write(f"{timezone.now()} | {email} | {message}\n")
            
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=500)
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def admin_panel(request):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только у главного администратора')
        return redirect('home')
    
    users = User.objects.all().order_by('id')
    return render(request, 'tournaments/admin_panel.html', {'users': users})

@login_required
def toggle_staff(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Доступ только у главного администратора')
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    
    if user == request.user:
        messages.error(request, 'Вы не можете изменить свой собственный статус')
        return redirect('admin_panel')
    
    user.is_staff = not user.is_staff
    user.save()
    
    status = "назначен staff" if user.is_staff else "снят со staff"
    messages.success(request, f'Пользователь {user.username} {status}')
    return redirect('admin_panel')