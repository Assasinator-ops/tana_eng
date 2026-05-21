from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

class UserType(models.IntegerChoices):
    ONE = 1, 'one'
    TWO = 2, 'two'

class DbUser(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, unique=True)
    usertype = models.IntegerField(choices=UserType.choices)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    status = models.BooleanField()

    class Meta:
        db_table = 'employee'

class DbOwner(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField()

    class Meta:
        db_table = 'owner'

    def __str__(self):
        return self.name

class DbBuilding(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone1 = models.CharField(max_length=25)
    phone2 = models.CharField(max_length=25, null=True, blank=True)
    phone3 = models.CharField(max_length=25, null=True, blank=True)
    email1 = models.CharField(max_length=50)
    email2 = models.CharField(max_length=50, null=True, blank=True)
    rep_name = models.CharField(max_length=100, null=True, blank=True)
    rep_phone = models.CharField(max_length=100, null=True, blank=True)
    owner = models.ForeignKey(DbOwner, on_delete=models.CASCADE, related_name='building', null=True, blank=True)

    class Meta:
        db_table = 'building'

    def __str__(self):
        return self.name

class ElevatorStatus(models.IntegerChoices):
    ONE = 1, 'one'
    TWO = 2, 'two'
    THREE = 3, 'three'

class DbElevator(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    commissionnumber = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    number_of_stops = models.IntegerField()
    landing_door_unit = models.IntegerField()
    landing_door_quantity = models.IntegerField()
    drive_unit = models.IntegerField()
    drive_quantity = models.IntegerField()
    car = models.IntegerField()
    car_quantity = models.IntegerField()
    shaft_pit = models.IntegerField()
    shaft_quantity = models.IntegerField()
    Total = models.FloatField()
    registerd_date = models.DateTimeField()
    started_date = models.DateTimeField()
    building = models.ForeignKey(DbBuilding, on_delete=models.CASCADE, related_name='elevator_id')

    class Meta:
        db_table = 'elevator'

    def __str__(self):
        return self.name

class DbBuildingManager(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20, null=True, blank=True)
    building = models.ForeignKey(DbBuilding, on_delete=models.CASCADE, related_name='manager')

    class Meta:
        db_table = 'manager'

class DiscountType(models.IntegerChoices):
    ONE = 1, 'contract time'
    TWO = 2, 'discount by problem'

class DbDiscount(models.Model):
    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)
    discount_type = models.IntegerField(choices=DiscountType.choices)

    # Legacy absolute amount
    discount_money = models.FloatField()

    # New percentage-based amount control (applied to running net total)
    percentage = models.FloatField(null=True, blank=True)

    description = models.TextField()

    description2 = models.TextField()
    carry = models.TextField(blank=True, null=True)
    contract = models.ForeignKey('DbContract', on_delete=models.CASCADE, related_name='discount')

    class Meta:
        db_table = 'discount'

class DbExtra(models.Model):
    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    # Legacy absolute amount
    money = models.FloatField()

    # New percentage-based amount control (applied to running net total)
    percentage = models.FloatField(null=True, blank=True)

    discription = models.TextField()
    discription1 = models.TextField()
    contract = models.ForeignKey('DbContract', on_delete=models.CASCADE, related_name='extra')

    class Meta:
        db_table = 'extra'



class DbMessage(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=50)
    detail = models.TextField()
    employee = models.ForeignKey(DbUser, on_delete=models.CASCADE, related_name='message')

    class Meta:
        db_table = 'message'

class DbWarranty(models.Model):
    id = models.AutoField(primary_key=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    elevator = models.ForeignKey(DbElevator, on_delete=models.CASCADE, related_name='warranty')

    class Meta:
        db_table = 'warranty'

class ContratE(models.IntegerChoices):
    ONE = 1, 'Not paid'
    TWO = 2, 'Fully paid'
    THREE = 3, 'Partial paid'

class DbContract(models.Model):
    id = models.AutoField(primary_key=True)
    building = models.ForeignKey(DbBuilding, on_delete=models.CASCADE, related_name='contract')
    start_date = models.DateTimeField(verbose_name="Starting Date")
    end_date = models.DateTimeField()
    paytime = models.IntegerField(verbose_name="Payment Duration (months)")
    payed = models.IntegerField(choices=ContratE.choices, default=ContratE.ONE)
    elevators = models.ManyToManyField('DbElevator', related_name='contracts', blank=True)

    class Meta:
        db_table = 'contract'

    def __str__(self):
        building_name = self.building.name if self.building_id else 'No building'
        return f"Contract #{self.id} - {building_name}"

class DbBuildingStatus(models.Model):
    id = models.AutoField(primary_key=True)
    building_status = models.BooleanField()
    building = models.OneToOneField(DbBuilding, on_delete=models.CASCADE, related_name='status')

    class Meta:
        db_table = 'buildingstatus'

class DBPartialPyment(models.Model):
    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)
    amount = models.FloatField(verbose_name="Amount paid (Not Total)")
    total = models.FloatField(verbose_name="Total payment expected")
    contract = models.ForeignKey(DbContract, on_delete=models.CASCADE, related_name='partial')

    class Meta:
        db_table = 'partailpayment'

class DbTotal(models.Model):
    id = models.AutoField(primary_key=True)
    total = models.FloatField()
    is_Actiave = models.BooleanField()
    contract = models.ForeignKey(DbContract, on_delete=models.CASCADE, related_name='total')

    class Meta:
        db_table = 'total'

class DbExpense(models.Model):
    id = models.AutoField(primary_key=True)
    capacity = models.IntegerField()
    number_of_stops = models.IntegerField()
    item = models.CharField(max_length=50)
    unit = models.FloatField()
    quantity = models.IntegerField()
    shaft = models.IntegerField()
    total = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'expense'

class DbTimer(models.Model):
    id = models.IntegerField(primary_key=True)
    status = models.IntegerField()
    started = models.DateTimeField(auto_now_add=True)
    expire = models.DateTimeField(auto_now_add=True)
    payment_time = models.IntegerField()
    payed = models.BooleanField(default=False)
    elevator = models.ForeignKey(DbElevator, on_delete=models.CASCADE, null=True, blank=True)
    building = models.ForeignKey(DbBuilding, on_delete=models.CASCADE, null=True, blank=True)
    discount = models.ForeignKey(DbDiscount, on_delete=models.SET_NULL, null=True, blank=True)
    extra = models.ForeignKey(DbExtra, on_delete=models.SET_NULL, null=True, blank=True)
    expense = models.ForeignKey(DbExpense, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'timer'


class GlobalSettings(models.Model):
    company_name = models.CharField(max_length=100)
    default_currency = models.CharField(max_length=3)
    notifications_enabled = models.BooleanField(default=True)
    # Additional fields
    maintenance_mode = models.BooleanField(default=False)
    default_timezone = models.CharField(max_length=50, default="UTC")
    session_timeout = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(1440)]
    )
    max_upload_size = models.PositiveIntegerField(default=10)  # MB
    theme_color = models.CharField(max_length=7, default="#3b82f6")
    date_format = models.CharField(max_length=20, default="YYYY-MM-DD")
    backup_frequency = models.CharField(
        max_length=10,
        choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
        default="weekly"
    )
    smtp_server = models.CharField(max_length=100, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    require_2fa = models.BooleanField(default=False)
    password_expiry_days = models.PositiveIntegerField(default=90)
    login_attempts_limit = models.PositiveIntegerField(default=5)
    privacy_policy_url = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Global Settings"

    def __str__(self):
        return f"Global Settings #{self.id}"


class PersonalizedSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notifications_enabled = models.BooleanField(default=True)
    messages_enabled = models.BooleanField(default=True)
    # Additional fields
    preferred_language = models.CharField(max_length=10, default="en")
    dark_mode = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    inbox_organization = models.CharField(
        max_length=20,
        choices=[("chrono", "Chronological"), ("priority", "Priority")],
        default="chrono"
    )
    auto_archive = models.BooleanField(default=False)
    signature = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    daily_summary_time = models.TimeField(default="09:00")
    show_online_status = models.BooleanField(default=True)
    keyboard_shortcuts = models.BooleanField(default=False)
    font_size = models.PositiveIntegerField(default=14)
    density = models.CharField(
        max_length=10,
        choices=[("compact", "Compact"), ("normal", "Normal"), ("comfort", "Comfort")],
        default="normal"
    )

    class Meta:
        verbose_name_plural = "Personalized Settings"

    def __str__(self):
        return f"{self.user.username}'s Settings"