from django.contrib import admin
from .models import TelegramUser, Object, Construction, Stage

@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Construction)
class ConstructionAdmin(admin.ModelAdmin):
    list_display = ('name', 'object', 'area')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'construction', 'volume')


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'first_name', 'last_name', 'created_at')
    list_filter = ('username', 'created_at')
    search_fields = ('user_id', 'username', 'first_name', 'last_name')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('User Information', {
            'fields': ('user_id', 'username', 'first_name', 'last_name', 'created_at')
        }),
    )
    ordering = ['-created_at']

    def get_name(self, obj):
        return obj.get_name()

    get_name.short_description = 'Name'
    get_name.admin_order_field = 'username'