from django.contrib import admin
from .models import TelegramUser, Object, Construction, Stage, CompletedWork, DailyReport, Underperformance

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'get_name', 'department', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'department')
    list_filter = ('department', 'created_at')
    ordering = ('-created_at',)

@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'responsible_person', 'completed')
    search_fields = ('name', 'responsible_person__username', 'responsible_person__first_name', 'responsible_person__last_name')
    list_filter = ('completed', 'responsible_person')

@admin.register(Construction)
class ConstructionAdmin(admin.ModelAdmin):
    list_display = ('name', 'object', 'area', 'completed')
    search_fields = ('name', 'object__name')
    list_filter = ('completed', 'object')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'construction', 'volume', 'start_date', 'end_date', 'number_of_workers', 'completed')
    search_fields = ('name', 'construction__name', 'construction__object__name')
    list_filter = ('completed', 'start_date', 'end_date', 'construction__object')
    filter_horizontal = ('workers_assigned',)

@admin.register(CompletedWork)
class CompletedWorkAdmin(admin.ModelAdmin):
    list_display = ('stage', 'volume', 'date')
    search_fields = ('stage__name', 'stage__construction__name', 'stage__construction__object__name')
    list_filter = ('date', 'stage__construction__object')

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('stage', 'date', 'number_of_workers', 'completed_volume')
    search_fields = ('stage__name', 'stage__construction__name', 'stage__construction__object__name')
    list_filter = ('date', 'stage__construction__object')

@admin.register(Underperformance)
class UnderperformanceAdmin(admin.ModelAdmin):
    list_display = ('stage', 'date', 'reason', 'deficit_volume', 'deficit_workers')
    search_fields = ('stage__name', 'stage__construction__name', 'stage__construction__object__name')
    list_filter = ('date', 'reason', 'stage__construction__object')
