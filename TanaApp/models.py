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


class DbElevatorExtra(models.Model):
    """Elevator-scoped extra for the elevator invoice modal.

    This is intentionally separate from DbExtra/DbDiscount (contract-scoped) so
    we do not break the existing contract payment/totals system.
    """

    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    elevator = models.ForeignKey('DbElevator', on_delete=models.CASCADE, related_name='elevator_extra')

    # Legacy absolute amount
    money = models.FloatField(default=0.0)

    # Optional percentage-based amount control (applied on top of elevator base)
    percentage = models.FloatField(null=True, blank=True)

    discription = models.TextField(blank=True, default='')
    discription1 = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'elevator_extra'


class DbElevatorDiscount(models.Model):
    """Elevator-scoped discount for the elevator invoice modal."""

    id = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    elevator = models.ForeignKey('DbElevator', on_delete=models.CASCADE, related_name='elevator_discount')

    # Legacy absolute amount
    discount_money = models.FloatField(default=0.0)

    # Optional percentage-based amount control (applied on top of elevator base)
    percentage = models.FloatField(null=True, blank=True)

    description = models.TextField(blank=True, default='')
    description2 = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'elevator_discount'




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

    # Hybrid deletion (soft delete): deleted contracts are hidden but their history can remain.
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'contract'

    def __str__(self):
        building_name = self.building.name if self.building_id else 'No building'
        return f"Contract #{self.id} - {building_name}"


class DbContractScar(models.Model):
    """Audit reminder created when a contract is deleted while customer has paid."""

    id = models.AutoField(primary_key=True)
    contract = models.ForeignKey('DbContract', on_delete=models.CASCADE, related_name='scars')
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='contract_deletions',
    )

    # Admin-only resolution (hard removal is also allowed)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='resolved_contract_deletions',
    )

    note = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'contract_scar'
        indexes = [
            models.Index(fields=['contract', 'deleted_at']),
        ]


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


class TotalCorrectionLog(models.Model):
    """Audit row written every time a contract's persisted net total is recomputed.

    Records both the previous and new totals, what triggered the change, and a
    short human-readable detail. Used by:
      - the live write-path (POST/PUT/DELETE for elevators, contracts, extras, discounts, partials)
      - the background 30-minute auditor thread
      - the in-app notifications page (joined into the existing DbMessage feed)
    """

    REASON_MANUAL = 'manual'
    REASON_AUTO_AUDIT = 'auto_audit'
    REASON_ELEVATOR_CHANGED = 'elevator_changed'
    REASON_CONTRACT_CHANGED = 'contract_changed'
    REASON_EXTRAS_CHANGED = 'extras_changed'
    REASON_DISCOUNTS_CHANGED = 'discounts_changed'
    REASON_PARTIAL_CHANGED = 'partial_changed'
    REASON_CHOICES = [
        (REASON_MANUAL, 'Manual / user action'),
        (REASON_AUTO_AUDIT, 'Background audit'),
        (REASON_ELEVATOR_CHANGED, 'Elevator created/updated/deleted'),
        (REASON_CONTRACT_CHANGED, 'Contract created/elevator attached'),
        (REASON_EXTRAS_CHANGED, 'Extra added/updated/deleted'),
        (REASON_DISCOUNTS_CHANGED, 'Discount added/updated/deleted'),
        (REASON_PARTIAL_CHANGED, 'Partial payment added/updated/deleted'),
    ]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    contract = models.ForeignKey(
        'DbContract', on_delete=models.CASCADE, related_name='total_logs'
    )
    reason = models.CharField(max_length=40, choices=REASON_CHOICES, default=REASON_MANUAL)
    previous_total = models.FloatField(null=True, blank=True)
    new_total = models.FloatField()
    delta = models.FloatField(default=0.0)
    detail = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'total_correction_log'
        indexes = [
            models.Index(fields=['contract', 'created_at']),
            models.Index(fields=['reason', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'Contract #{self.contract_id} {self.previous_total} -> {self.new_total} ({self.reason})'

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
    company_name = models.CharField(max_length=100, blank=True, default='')
    default_currency = models.CharField(max_length=3, blank=True, default='ETB')
    notifications_enabled = models.BooleanField(default=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
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
    items_per_page = models.PositiveIntegerField(default=25)
    font_size = models.PositiveIntegerField(default=14)
    density = models.CharField(
        max_length=10,
        choices=[("compact", "Compact"), ("normal", "Normal"), ("comfort", "Comfort")],
        default="normal"
    )


class AuditLog(models.Model):
    """Database logging model for system events and actions"""
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    extra_data = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'level']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.action} - {self.timestamp}"

