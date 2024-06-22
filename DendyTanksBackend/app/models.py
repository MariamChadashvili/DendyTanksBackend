import uuid
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class PlayerManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not name:
            raise ValueError('Users must have a name')

        player = self.model(
            email=self.normalize_email(email),
            name=name,
        )
        player.set_password(password)
        player.save(using=self._db)
        return player

    def create_superuser(self, email, name, password=None):
        player = self.create_user(
            email,
            password=password,
            name=name,
        )
        player.is_admin = True
        player.save(using=self._db)
        return player


class Player(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    name = models.CharField(max_length=100)
    joined_game_at = models.DateTimeField(null=True, blank=True)
    joined_room_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    password = models.CharField(max_length=128)

    objects = PlayerManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Map(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    width = models.FloatField()
    height = models.FloatField()
    block_size = models.FloatField()
    bullet_size = models.FloatField()
    bases = JSONField(default=list)
    walls = JSONField(default=list)
    objects = models.Manager()
    # bases = models.ManyToManyField(Base)
    # walls = models.ManyToManyField(Wall)


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=2)
    status = models.CharField(max_length=20, choices=[
        ('waiting', 'Waiting'),
        ('full', 'Full'),
        ('game started', 'Game started'),
        ('closed', 'Closed')
    ], default='waiting')
    created_by = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True)
    players = models.ManyToManyField(Player, blank=True, related_name='rooms_playing_in')
    creation_date = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()

    def add_player(self, player):
        if self.players.count() >= self.capacity:
            raise ValueError("Room is full")
        self.players.add(player)
        if self.players.count() == self.capacity:
            self.status = 'full'
            self.save()

    def remove_player(self, player):
        self.players.remove(player)
        if self.players.count() < self.capacity:
            self.status = 'waiting'
            self.save()
