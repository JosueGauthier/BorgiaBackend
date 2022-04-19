from . import views
from rest_framework import routers
from django.urls import include, path


from shops.views import (ProductCreate, ProductDeactivate, ProductList,
                         ProductRemove, ProductRetrieve, ProductUpdate,
                         ProductUpdatePrice, ShopCheckup, ShopCreate, ShopList,
                         ShopUpdate, ShopWorkboard)


# partie api

router = routers.DefaultRouter()
router.register(r'shops', views.ShopViewSet)
router.register(r'products', views.ProductViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.



shops_patterns = [
          #API 
     path('api-links/', include(router.urls)),
     path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # SHOPS
    path('shops/', include([
        path('', ShopList.as_view(), name='url_shop_list'),
        path('create/', ShopCreate.as_view(), name='url_shop_create'),
        path('<int:shop_pk>/', include([
            path('update/', ShopUpdate.as_view(), name='url_shop_update'),
            path('checkup/', ShopCheckup.as_view(), name='url_shop_checkup'),
            path('workboard/', ShopWorkboard.as_view(),
                 name='url_shop_workboard'),

            # PRODUCTS
            path('products/', include([
                path('', ProductList.as_view(), name='url_product_list'),
                path('create/', ProductCreate.as_view(),
                     name='url_product_create'),
                path('<int:product_pk>/', include([
                    path('', ProductRetrieve.as_view(),
                         name='url_product_retrieve'),
                    path('update/', ProductUpdate.as_view(),
                         name='url_product_update'),
                    path('update/price/', ProductUpdatePrice.as_view(),
                         name='url_product_update_price'),
                    path('deactivate/', ProductDeactivate.as_view(),
                         name='url_product_deactivate'),
                    path('remove/', ProductRemove.as_view(),
                         name='url_product_remove')
                ]))
            ]))
        ]))
    ]))
]
