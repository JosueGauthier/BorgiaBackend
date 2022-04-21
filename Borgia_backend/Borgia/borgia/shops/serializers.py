"""
?Sérialisation d’objets Django
L’infrastructure de sérialisation de Django fournit un mécanisme pour « traduire » 
les modèles Django en d’autres formats. En général, ces autres formats sont basés 
sur du texte et utilisés pour envoyer des données de Django à travers le réseau, 
mais il est possible qu’un sérialiseur prenne en charge n’importe quel 
format (basé sur du texte ou non).

Remember, serialization is the process of converting a Model to JSON. Using a serializer,
 we can specify what fields should be present in the JSON representation of the model. """

"""La HyperlinkedModelSerializerclasse est similaire à la
 ModelSerializerclasse sauf qu'elle utilise des liens hypertexte 
pour représenter les relations, plutôt que des clés primaires."""


from rest_framework import serializers

from .models import Shop,Product



class ShopSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Shop
        fields = ('id','name', 'description','color','image')


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'unit','shop','is_manual','manual_price','correcting_factor','is_active','is_removed','product_image')


