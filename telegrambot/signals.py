from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CompletedWork, Stage, Construction, Object

@receiver(post_save, sender=CompletedWork)
@receiver(post_delete, sender=CompletedWork)
def update_stage_completion_status(sender, instance, **kwargs):
    stage = instance.stage
    total_completed_volume = sum(work.volume for work in stage.completed_works.all())
    stage.completed = total_completed_volume >= stage.volume
    stage.save()

    update_construction_completion_status(stage.construction)

def update_construction_completion_status(construction):
    all_stages_completed = all(stage.completed for stage in construction.stages.all())
    construction.completed = all_stages_completed
    construction.save()

    update_object_completion_status(construction.object)

def update_object_completion_status(obj):
    all_constructions_completed = all(construction.completed for construction in obj.constructions.all())
    obj.completed = all_constructions_completed
    obj.save()



