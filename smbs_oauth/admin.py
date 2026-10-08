from django.contrib import admin

from smbs_apps.smbs_oauth.models import GoogleAccount, GoogleOAuthSettings


@admin.register(GoogleAccount)
class GoogleAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'google_sub', 'created_at')
    search_fields = ('user__username', 'user__email', 'email', 'google_sub')
    autocomplete_fields = ('user',)


@admin.register(GoogleOAuthSettings)
class GoogleOAuthSettingsAdmin(admin.ModelAdmin):
    list_display = ('site', 'client_id', 'updated')
