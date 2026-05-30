from django import template
from tournaments.models import Team

register = template.Library()


@register.simple_tag
def get_user_team(user):
    """Return the team where user is captain, or first team as member."""
    team = Team.objects.filter(captain=user).select_related('captain').prefetch_related('members').first()
    if team is None:
        team = Team.objects.filter(members=user).select_related('captain').prefetch_related('members').first()
    return team


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
