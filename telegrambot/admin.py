from django.contrib import admin
from .models import Object, Construction, Stage

@admin.register(Object)
class ObjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Construction)
class ConstructionAdmin(admin.ModelAdmin):
    list_display = ('name', 'object', 'area')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'construction', 'volume')
