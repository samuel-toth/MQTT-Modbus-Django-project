from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

# Create your models here.
class UserManager(BaseUserManager):
	def create_user(self, username, password, **extra_fields):
		if not username:
			raise ValueError('An username is required.')
		if not password:
			raise ValueError('A password is required.')
		user = self.model(username=username,**extra_fields)
		user.set_password(password)
		user.save()
		return user
	
	def create_superuser(self, username, password, **extra_fields):
		if not username:
			raise ValueError('An username is required.')
		if not password:
			raise ValueError('A password is required.')
		user = self.create_user(username, password, **extra_fields)
		user.is_superuser = True
		user.is_staff = True
		user.save()
		return user

class User(AbstractBaseUser, PermissionsMixin):
	user_id = models.AutoField(primary_key=True)
	username = models.CharField(max_length=50, unique=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = []
	objects = UserManager()
	def __str__(self):
		return self.username