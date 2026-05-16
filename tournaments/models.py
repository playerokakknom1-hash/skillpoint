from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField('Название команды', max_length=100, unique=True)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captained_teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.from_user} -> {self.to_user}"

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('registration', '📢 Регистрация открыта'),
        ('in_progress', '⚔️ Идёт турнир'),
        ('finished', '🏆 Завершён'),
    ]
    
    TEAM_SIZE_CHOICES = [
        (1, '1x1 (одиночки)'),
        (2, '2x2'),
        (5, '5x5'),
    ]
    
    name = models.CharField('Название турнира', max_length=200)
    description = models.TextField('Описание', blank=True)
    max_teams = models.IntegerField('Максимум команд', default=8)
    team_size = models.IntegerField('Формат', choices=TEAM_SIZE_CHOICES, default=5)
    registered_teams = models.ManyToManyField(Team, blank=True, related_name='tournaments')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='registration')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tournaments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def current_teams_count(self):
        return self.registered_teams.count()

class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1_matches', null=True, blank=True)
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2_matches', null=True, blank=True)
    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='won_matches', null=True, blank=True)
    round_number = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.team1.name if self.team1 else 'TBD'} vs {self.team2.name if self.team2 else 'TBD'}"