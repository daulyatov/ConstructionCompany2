from django.db import models

class TelegramUser(models.Model):
    DEPARTMENT_CHOICES = [
        ('contract', 'Договорной отдел'),
        ('project_manager', 'Руководитель проекта'),
        ('work', 'Бригадир'),
        ('director', 'Директор'),
    ]

    user_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID пользователя",
        help_text="Уникальный идентификатор пользователя в Telegram.",
    )
    username = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Имя пользователя",
        help_text="Имя пользователя в Telegram.",
    )
    first_name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Имя",
        help_text="Имя пользователя в Telegram.",
    )
    last_name = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Фамилия",
        help_text="Фамилия пользователя в Telegram.",
    )
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True,
        verbose_name="Отдел",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создан",
        help_text="Временная метка, указывающая, когда был создан пользователь.",
    )

    def get_name(self):
        if self.username:
            return self.username
        elif self.last_name:
            return self.last_name
        elif self.first_name:
            return self.first_name
        else:
            return "Пользователь"

    def __str__(self):
        return f"{self.user_id}: {self.get_name()}"

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
        ordering = ["-created_at"]

class Object(models.Model):
    name = models.CharField(max_length=255)
    responsible_person = models.ForeignKey(TelegramUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='responsible_for_objects')
    completed = models.BooleanField(default=False, verbose_name="Выполнен")

    def __str__(self):
        return self.name

class Construction(models.Model):
    object = models.ForeignKey(Object, related_name='constructions', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    area = models.BigIntegerField()  # площадь конструкции в м2
    completed = models.BooleanField(default=False, verbose_name="Выполнен")

    def __str__(self):
        return f"{self.name} - {self.object.name}"

class Stage(models.Model):
    construction = models.ForeignKey(Construction, related_name='stages', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    volume = models.BigIntegerField()  # объем этапа в м2
    workers_assigned = models.ManyToManyField(TelegramUser, related_name='assigned_stages', blank=True)
    start_date = models.DateField(null=True, blank=True, verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    number_of_workers = models.IntegerField(default=0, verbose_name="Количество рабочих")
    completed = models.BooleanField(default=False, verbose_name="Выполнен")

    def __str__(self):
        return f"{self.name} - {self.construction.name} - {self.construction.object.name}"

class CompletedWork(models.Model):
    stage = models.ForeignKey('Stage', related_name='completed_works', on_delete=models.CASCADE)
    volume = models.FloatField()  # объем выполненной работы в м2
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.stage.name} - {self.volume} м2 - {self.date}"

class DailyReport(models.Model):
    stage = models.ForeignKey(Stage, related_name='daily_reports', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    number_of_workers = models.IntegerField()
    completed_volume = models.FloatField()

    def __str__(self):
        return f"{self.date} - {self.stage.name} - {self.completed_volume} м2 - {self.number_of_workers} рабочих"


class Underperformance(models.Model):
    REASON_CHOICES = [
        ('volume', 'Объем'),
        ('workers', 'Количество рабочих'),
        ('both', 'Объем и количество рабочих'),
    ]

    stage = models.ForeignKey(Stage, related_name='underperformances', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=7, choices=REASON_CHOICES)  # 'volume', 'workers', 'both'
    deficit_volume = models.FloatField(null=True, blank=True)  # Volume deficit
    deficit_workers = models.IntegerField(null=True, blank=True)  # Worker deficit

    def __str__(self):
        return f"{self.stage} - {self.date} - {self.reason}"
