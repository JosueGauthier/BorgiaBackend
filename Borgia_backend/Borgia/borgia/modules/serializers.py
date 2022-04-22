from rest_framework import serializers

from .models import CategoryProduct,Category



class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id','name','module_id','products','order','category_image')



class CategoryProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CategoryProduct
        fields = ('id','category', 'product','quantity')


