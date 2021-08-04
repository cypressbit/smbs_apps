from django.contrib import admin

from smbs_alerts.models import Alert


class AlertAdmin(admin.ModelAdmin):
    list_display = ('created', 'alert_type', 'position', 'title')


admin.site.register(Alert, AlertAdmin)
