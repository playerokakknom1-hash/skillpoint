from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Team(models.Model):
    name = models.CharField('Название команды', max_length=100, unique=True)
    captain = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='captained_teams',
        db_index=True,
    )
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['captain'], name='idx_team_captain'),
        ]

    def __str__(self):
        return self.name


class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_requests',
        db_index=True,
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_requests',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['from_user', 'to_user', 'is_accepted'],
                         name='idx_friendreq_users_accepted'),
            models.Index(fields=['to_user', 'is_accepted'],
                         name='idx_friendreq_to_accepted'),
        ]

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
    status = models.CharField(
        'Статус', max_length=20, choices=STATUS_CHOICES,
        default='registration', db_index=True,
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_tournaments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    registration_deadline = models.DateTimeField(
        'Регистрация до', null=True, blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at'],
                         name='idx_tournament_status_created'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def current_teams_count(self):
        if hasattr(self, '_teams_count'):
            return self._teams_count
        return self.registered_teams.count()

    def is_full(self):
        return self.current_teams_count() >= self.max_teams

    def is_registration_closed(self):
        if self.registration_deadline:
            return timezone.now() > self.registration_deadline
        return False


class Match(models.Model):
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name='matches',
        db_index=True,
    )
    team1 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='team1_matches',
        null=True, blank=True,
    )
    team2 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='team2_matches',
        null=True, blank=True,
    )
    team1_score = models.IntegerField(default=0)
    team2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='won_matches',
        null=True, blank=True,
    )
    round_number = models.IntegerField(default=1)
    match_order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['tournament', 'round_number', 'match_order'],
                         name='idx_match_tourn_round_order'),
        ]
        ordering = ['round_number', 'match_order']

    def __str__(self):
        t1 = self.team1.name if self.team1_id else 'TBD'
        t2 = self.team2.name if self.team2_id else 'TBD'
        return f"{t1} vs {t2}"