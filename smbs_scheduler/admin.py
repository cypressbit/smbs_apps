from django.contrib import admin

from smbs_apps.smbs_scheduler.models import (Booking, ExternalCalendar, SchedulerSettings, Service, StaffMember,
                                             TimeOff, WeeklyHours)


class WeeklyHoursInline(admin.TabularInline):
    model = WeeklyHours
    extra = 0


class TimeOffInline(admin.TabularInline):
    model = TimeOff
    extra = 0


class ExternalCalendarInline(admin.TabularInline):
    model = ExternalCalendar
    extra = 0
    fields = ['label', 'url', 'fetched_at', 'error']
    readonly_fields = ['fetched_at', 'error']


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'active', 'order']
    inlines = [WeeklyHoursInline, TimeOffInline, ExternalCalendarInline]
    exclude = ['site']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'price_cents', 'payment', 'active']
    filter_horizontal = ['staff']
    exclude = ['site']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['reference', 'start', 'service_name', 'staff', 'name', 'status']
    list_filter = ['status', 'staff']
    search_fields = ['reference', 'name', 'email']
    readonly_fields = ['reference', 'cancel_token_hash', 'created', 'updated']
    exclude = ['site']


admin.site.register(SchedulerSettings)
