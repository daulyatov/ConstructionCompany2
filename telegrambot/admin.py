from django.contrib import admin
from .models import TelegramUser, Object, Construction, Stage

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'department', 'created_at')
    list_filter = ('department',)
    search_fields = ('username', 'first_name', 'last_name', 'user_id')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('user_id', 'username', 'first_name', 'last_name', 'department')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )
    ordering = ['-created_at']

    def get_name(self, obj):
        return obj.get_name()

    get_name.short_description = 'Name'
    get_name.admin_order_field = 'username'

@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'responsible_person']

@admin.register(Construction)
class ConstructionAdmin(admin.ModelAdmin):
    list_display = ['name', 'object', 'area']

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['name', 'construction', 'volume']

