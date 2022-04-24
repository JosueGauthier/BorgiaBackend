from rest_framework import serializers

from .models import User



class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id','username', 'last_name','first_name','password','email','surname','family','balance','year','campus','phone','avatar','theme')


