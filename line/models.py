from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class User(models.Model):
    user_id = models.CharField(_('User id'), primary_key=True, max_length=50, help_text=_("User id"))
    follow_date = models.DateTimeField(_('Follow date'), auto_now_add=True, help_text=_("Follow date"))

    COMMAND_STATES = (
        ('0', _('Free')),  # 還沒進入任何命令狀態
        ('1', _('Subscribing')),  # 正在輸入關鍵字
        ('2', _('Confirming')),  # 正在確認關鍵字
    )
    state = models.CharField(
        _('state'), max_length=2, choices=COMMAND_STATES, default='0', help_text=_('Typing state'))
    class Meta():
        ordering = ['follow_date']

    def __str__(self):
        return f'{self.user_id}, follow date {self.follow_date}'


    def display_keyword(self):
        return ','.join([id for key in self.keyword.all()])
    display_keyword.short_description = _('Subscribe keyword')

class Keyword(models.Model):
    keyword = models.CharField(_('Keyword'), max_length=15, help_text=_("keyword"), unique=True, null=False, blank=False)
    create_time = models.DateTimeField(_("Create time"), auto_now_add=True)
    users = models.ManyToManyField(User, verbose_name=_('User'), blank=True)

    class Meta():
        ordering = ['create_time']

    def __str__(self):
        return f'{self.keyword}, create date {self.create_time}'

    def display_users(self):
        return ','.join([id for id in self.users.all()])
    display_users.short_description = _('Subscribe users')
