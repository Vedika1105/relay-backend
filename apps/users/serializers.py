from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
import os



# regex pattern for username
# ^[a-zA-Z]     → must START with a letter
# [a-zA-Z0-9_-] → can contain letters, numbers, underscore, hyphen
# {2,29}$       → followed by 2 to 29 more characters (total 3-30)
username_validator = RegexValidator(
    regex=r'^[a-zA-Z][a-zA-Z0-9_-]{2,29}$',
    message='Username must be 3-30 characters, start with a letter, and contain only letters, numbers, underscores or hyphens.'
)


MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

class RegisterSerializer(serializers.ModelSerializer):
    # extra fields not in model — only for registration input
    password         = serializers.CharField(write_only=True)  # write_only → never returned in response
    confirm_password = serializers.CharField(write_only=True)  # only used for validation, not saved
    username         = serializers.CharField(validators=[username_validator]) # ← add validator here

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password']

    def validate_email(self, value):
        # check if email already exists in database
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate(self, data):
        # check passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})

        # check password strength using Django's built-in validators
        validate_password(data['password'])

        return data

    def create(self, validated_data):
        # remove confirm_password — not needed for creating user
        validated_data.pop('confirm_password')

        # create_user → hashes password automatically
        # NEVER use User.objects.create() for users → stores plain text password
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    # used for returning user data in responses
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'display_name', 'bio', 'avatar', 'status']
        read_only_fields = ['id']  # id should never be changed by user

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email    = data.get('email')
        password = data.get('password')

        # check if user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with this email.')

        # authenticate → checks password against stored hash
        # returns user if correct, None if wrong
        authenticated_user = authenticate(username=user.username, password=password)

        if not authenticated_user:
            raise serializers.ValidationError('Incorrect password.')

        if not authenticated_user.is_active:
            raise serializers.ValidationError('This account has been disabled.')

        # attach user to validated data so view can access it
        data['user'] = authenticated_user
        return data
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'display_name', 'bio', 'avatar', 'status']
        read_only_fields = ['id', 'username', 'email']

    def validate_avatar(self, value):
        if value.name.count('.') != 1:
            raise serializers.ValidationError('Filename must have exactly one extension.')
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_AVATAR_EXTENSIONS:
            raise serializers.ValidationError('Only JPG, JPEG, or PNG images are allowed.')
        if value.size > MAX_AVATAR_SIZE:
            raise serializers.ValidationError('Image must be smaller than 2MB.')
        return value

    def update(self, instance, validated_data):
        instance.display_name = validated_data.get('display_name', instance.display_name)
        instance.bio          = validated_data.get('bio', instance.bio)
        instance.avatar       = validated_data.get('avatar', instance.avatar)
        instance.status       = validated_data.get('status', instance.status)
        instance.save()
        return instance

    
class ChangePasswordSerializer(serializers.Serializer):
    old_password         = serializers.CharField(write_only=True)
    new_password         = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        # self.context['request'].user → logged in user
        # check_password → compares plain text with stored hash
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({'confirm_new_password': 'Passwords do not match.'})
        validate_password(data['new_password'])
        return data

    def save(self):
        # set_password → hashes new password and saves
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user