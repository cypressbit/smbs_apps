from django.contrib import admin

from smbs_apps.smbs_base.admin import SettingsAdmin
from smbs_apps.smbs_accounts.models import AccountSettings


class AccountSettingsAdmin(SettingsAdmin):
    pass


admin.site.register(AccountSettings, AccountSettingsAdmin)
