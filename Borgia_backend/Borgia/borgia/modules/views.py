from users.serializers import LoginSerializer as LoginSerializer
from . import serializers
from rest_framework.response import Response
from rest_framework import views
from rest_framework import status
from rest_framework import permissions
from rest_framework import generics
from django.contrib.auth import login, logout
from .serializers import CategorySerializer, CategoryProductSerializer
from .models import Category, CategoryProduct
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from functools import partial, wraps
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.forms.formsets import formset_factory
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from borgia.views import BorgiaFormView, BorgiaView
from configurations.utils import configuration_get
from modules.forms import (ModuleCategoryCreateForm,
                           ModuleCategoryCreateNameForm, ShopModuleConfigForm,
                           ShopModuleSaleForm)
from modules.mixins import ShopModuleCategoryMixin, ShopModuleMixin
from modules.models import Category, CategoryProduct, SelfSaleModule
from sales.models import Sale, SaleProduct
from shops.models import Product, Shop
from users.models import User

logger = logging.getLogger(__name__)


class ShopModuleSaleView(ShopModuleMixin, BorgiaFormView):
    """
    Generic FormView for handling invoice concerning product bases through a
    shop.

    :param self.template_name: template, mandatory.
    :param self.form_class: form class, mandatory.
    :param self.permission_required_selfsale: permission to check for self sale
    :param self.permission_required_operatorsale: permission to check for operator sale
    :type self.template_name: string
    :type self.form_class: Form class object
    :type self.permission_required_selfsale: string
    :type self.permission_required_operatorsale: string
    """
    permission_required_self = 'modules.use_selfsalemodule'
    permission_required_operator = 'modules.use_operatorsalemodule'
    template_name = 'modules/shop_module_sale.html'
    form_class = ShopModuleSaleForm

    def has_permission(self):
        if self.kwargs['module_class'] == 'self_sales':
            has_perms = self.has_permission_selfsales()
        else:
            has_perms = super().has_permission()
        if not has_perms:
            return False
        else:
            if self.module.state is False:
                raise Http404
            else:
                return True

    def has_permission_selfsales(self):
        """
        Customized permission for self_sale in shops. 
        The user still need the use_selfsalemodule permission
        """
        self.add_context_objects()
        return PermissionRequiredMixin.has_permission(self)

    def get_menu_type(self):
        if self.module_class == "self_sales":
            return 'members'
        elif self.module_class == "operator_sales":
            return 'shops'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['module_class'] = self.module_class
        kwargs['module'] = self.module
        kwargs['balance_threshold_purchase'] = configuration_get(
            'BALANCE_THRESHOLD_PURCHASE')

        if self.module_class == "self_sales":
            kwargs['client'] = self.request.user
        elif self.module_class == "operator_sales":
            kwargs['client'] = None
        else:
            self.handle_unexpected_module_class()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.module.categories.all().order_by('order')
        return context

    #! Module de paiement
    def form_valid(self, form):
        """
        Create a sale and like all products via SaleProduct objects.
        """
        if self.module_class == "self_sales":
            client = self.request.user
        elif self.module_class == "operator_sales":
            client = form.cleaned_data['client']
        else:
            self.handle_unexpected_module_class()

        sale = Sale.objects.create(
            operator=self.request.user,
            sender=client,
            recipient=User.objects.get(pk=1),
            module=self.module,
            shop=self.shop
        )
        for field in form.cleaned_data:
            if field != 'client' and form.cleaned_data[field] != '':
                invoice = int(form.cleaned_data[field])
                if invoice > 0:
                    try:
                        category_product = CategoryProduct.objects.get(
                            pk=field.split('-')[0])
                    except ObjectDoesNotExist:
                        pass
                    else:
                        SaleProduct.objects.create(
                            sale=sale,
                            product=category_product.product,
                            quantity=category_product.quantity * invoice,
                            price=category_product.get_price() * invoice
                        )
        sale.pay()

        context = self.get_context_data()

        if self.module.logout_post_purchase:
            success_url = reverse('url_logout') + \
                '?next=' + self.get_success_url()
        else:
            success_url = self.get_success_url()
        context['sale'] = sale
        context['delay'] = self.module.delay_post_purchase
        context['success_url'] = success_url

        return sale_shop_module_resume(
            self.request, context
        )

    def get_success_url(self):
        return reverse(
            'url_shop_module_sale',
            kwargs={'shop_pk': self.shop.pk, 'module_class': self.module_class}
        )


def sale_shop_module_resume(request, context):
    """
    Display shop module resume after a sale
    """
    template_name = 'modules/shop_module_sale_resume.html'
    return render(request, template_name, context=context)


class ShopModuleConfigView(ShopModuleMixin, BorgiaView):
    """
    ConfigView for a shopModule.
    """
    permission_required_self = 'modules.view_config_selfsalemodule'
    permission_required_operator = 'modules.view_config_operatorsalemodule'
    menu_type = 'shops'
    template_name = 'modules/shop_module_config.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['type'] = "self_sale"
        return render(request, self.template_name, context=context)


class ShopModuleConfigUpdateView(ShopModuleMixin, BorgiaFormView):
    """
    View to manage config of a self shop module.
    """
    permission_required_self = 'modules.change_config_selfsalemodule'
    permission_required_operator = 'modules.change_config_operatorsalemodule'
    menu_type = 'shops'
    template_name = 'modules/shop_module_config_update.html'
    form_class = ShopModuleConfigForm

    def get_initial(self):
        initial = super(ShopModuleConfigUpdateView, self).get_initial()
        initial['state'] = self.module.state
        initial['logout_post_purchase'] = self.module.logout_post_purchase
        initial['limit_purchase'] = self.module.limit_purchase
        if self.module.delay_post_purchase:
            initial['infinite_delay_post_purchase'] = False
        else:
            initial['infinite_delay_post_purchase'] = True
        initial['delay_post_purchase'] = self.module.delay_post_purchase
        return initial

    def form_valid(self, form):
        self.module.state = form.cleaned_data['state']
        self.module.logout_post_purchase = form.cleaned_data['logout_post_purchase']
        self.module.limit_purchase = form.cleaned_data['limit_purchase']
        if form.cleaned_data['infinite_delay_post_purchase'] is True:
            self.module.delay_post_purchase = None
        else:
            self.module.delay_post_purchase = form.cleaned_data['delay_post_purchase']
        self.module.save()
        return super(ShopModuleConfigUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('url_shop_module_config',
                       kwargs={'shop_pk': self.shop.pk, 'module_class': self.module_class})


#!!!!!!!!!!!!!!!
class ShopModuleCategoryCreateView(ShopModuleMixin, BorgiaView):
    """
    """

    permission_required_self = 'modules.change_config_selfsalemodule'
    permission_required_operator = 'modules.change_config_operatorsalemodule'
    menu_type = 'shops'
    template_name = 'modules/shop_module_category_create.html'

    def __init__(self):
        #logger.error(' __init__')
        super().__init__()
        self.shop = None
        self.module_class = None
        self.form_class = None

    def has_permission(self):
        has_perms = super().has_permission()
        if not has_perms:
            return False
        else:
            self.form_class = formset_factory(wraps(ModuleCategoryCreateForm)(
                partial(ModuleCategoryCreateForm, shop=self.shop)), extra=1)
            return True

    def get(self, request, *args, **kwargs):
        """
        permet d'afficher la page de vente
        """
        logger.error('get')
        context = self.get_context_data(**kwargs)
        context['cat_form'] = self.form_class()
        context['cat_name_form'] = ModuleCategoryCreateNameForm(
            initial={'order': self.module.categories.all().count()})
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        """
        Permet de publier la creation d'une nouvele catgerorie

        cat_name_form => renvoie une objet from avec le nom et l'ordre entr??
        self.module => Module de vente en libre service du magasin Pi
        """
        logger.error(' post')

        cat_name_form = ModuleCategoryCreateNameForm(request.POST)

        if cat_name_form.is_valid():
            category = Category.objects.create(
                name=cat_name_form.cleaned_data['name'],
                order=cat_name_form.cleaned_data['order'],
                module=self.module,
                shop_id=self.shop.pk,
                category_image=cat_name_form.cleaned_data['category_image'],

            )
            logger.error(self.shop.id)

        cat_form = self.form_class(request.POST)
        for product_form in cat_form.cleaned_data:
            try:
                product = Product.objects.get(
                    pk=product_form['product'].split('/')[0])
                if product.unit:
                    quantity = int(product_form['quantity'])
                else:
                    quantity = 1
                CategoryProduct.objects.create(
                    category=category,
                    product=product,
                    quantity=quantity
                )
            except ObjectDoesNotExist:
                pass
            except KeyError:
                pass
        return redirect(self.get_success_url())

    def get_success_url(self):
        """
        Permet de ...

        self.module_class => self_sales
        self.shop.pk => affiche bien la pk du shop en question 
        """
        #logger.error(' get_success_url')
        # logger.error(self.shop.pk)
        return reverse('url_shop_module_config',
                       kwargs={'shop_pk': self.shop.pk, 'module_class': self.module_class})


class ShopModuleCategoryUpdateView(ShopModuleCategoryMixin, BorgiaView):
    """
    """
    permission_required_self = 'modules.change_config_selfsalemodule'
    permission_required_operator = 'modules.change_config_operatorsalemodule'
    menu_type = 'shops'
    template_name = 'modules/shop_module_category_update.html'

    def __init__(self):
        super().__init__()
        self.shop = None
        self.module_class = None
        self.form_class = None

    def has_permission(self):
        has_perms = super().has_permission()
        if not has_perms:
            return False
        else:
            self.form_class = formset_factory(wraps(ModuleCategoryCreateForm)(
                partial(ModuleCategoryCreateForm, shop=self.shop)), extra=1)
            return True

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        cat_form_data = [{'product': str(category_product.product.pk) + '/' +
                          str(category_product.product.get_unit_display()),
                          'quantity': category_product.quantity}
                         for category_product in self.category.categoryproduct_set.all()]
        context['cat_form'] = self.form_class(initial=cat_form_data)
        context['cat_name_form'] = ModuleCategoryCreateNameForm(
            initial={'name': self.category.name, 'order': self.category.order})
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        cat_name_form = ModuleCategoryCreateNameForm(request.POST)
        if cat_name_form.is_valid():
            self.category.name = cat_name_form.cleaned_data['name']
            if cat_name_form.cleaned_data['order'] != self.category.order:
                shift_category_orders(
                    self.category, cat_name_form.cleaned_data['order'])
            self.category.save()

        cat_form = self.form_class(request.POST)
        CategoryProduct.objects.filter(category=self.category).delete()
        for product_form in cat_form.cleaned_data:
            try:
                product = Product.objects.get(
                    pk=product_form['product'].split('/')[0])
                if product.unit:
                    quantity = int(product_form['quantity'])
                else:
                    quantity = 1
                CategoryProduct.objects.create(
                    category=self.category,
                    product=product,
                    quantity=quantity
                )
            except ObjectDoesNotExist:
                pass
            except KeyError:
                pass
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('url_shop_module_config',
                       kwargs={'shop_pk': self.shop.pk, 'module_class': self.module_class})


class ShopModuleCategoryDeleteView(ShopModuleCategoryMixin, BorgiaView):
    """
    """
    permission_required_self = 'modules.change_config_selfsalemodule'
    permission_required_operator = 'modules.change_config_operatorsalemodule'
    menu_type = 'shops'
    template_name = 'modules/shop_module_category_delete.html'

    def __init__(self):
        super().__init__()
        self.shop = None
        self.module_class = None

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        CategoryProduct.objects.filter(category=self.category).delete()
        self.category.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('url_shop_module_config',
                       kwargs={'shop_pk': self.shop.pk, 'module_class': self.module_class})


def shift_category_orders(category, new_order):
    module_id = category.module_id
    content_type_id = category.content_type_id
    order = category.order
    if new_order < order:
        categories = Category.objects.filter(content_type_id=content_type_id,
                                             module_id=module_id,
                                             order__gte=new_order, order__lt=order)
        if categories:
            for cat in categories:
                cat.order += 1
                cat.save()
    elif new_order > order:
        categories = Category.objects.filter(content_type_id=content_type_id,
                                             module_id=module_id,
                                             order__lte=new_order, order__gt=order)
        if categories:
            for cat in categories:
                cat.order -= 1
                cat.save()
    category.order = int(new_order)
    category.save()


# partie API

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module_id', 'shop_id']


class ProductFromCategoryViewSet(viewsets.ModelViewSet):
    queryset = CategoryProduct.objects.all()
    serializer_class = CategoryProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'product']


def api_create_sale_view(saleMap, api_user):
    """
    API permettant d'acheter un produit

    """

    api_operator = api_user
    api_sender = api_operator
    api_recipient = User.objects.get(pk=1)
    api_module = SelfSaleModule.objects.get(pk=saleMap['api_module_pk'])
    api_shop = Shop.objects.get(pk=saleMap['api_shop_pk'])
    api_ordered_quantity = saleMap['api_ordered_quantity']
    api_category_product_id = saleMap['api_category_product_id']

    sale = Sale.objects.create(
        operator=api_operator,
        sender=api_sender,
        recipient=api_recipient,
        module=api_module,
        shop=api_shop
    )

    category_product = CategoryProduct.objects.get(
        pk=api_category_product_id)

    SaleProduct.objects.create(
        sale=sale,
        product=category_product.product,
        #! category_product.quantity = volume ou poids par item |  ordered quantity
        quantity=category_product.quantity * api_ordered_quantity,

        price=category_product.get_price() * api_ordered_quantity
    )
    sale.pay()


class SelfSaleView(views.APIView):

    # This view should be accessible also for unauthenticated users.
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):

        serializerLogin = LoginSerializer(
            data=self.request.data, context={'request': self.request})
        serializerLogin.is_valid(raise_exception=True)
        user = serializerLogin.validated_data['user']
        login(request, user)
        api_user = self.request.user
        serializerSale = serializers.SelfSaleSerializer(
            data=self.request.data, context={'request': self.request})
        serializerSale.is_valid(raise_exception=True)
        saleMap = serializerSale.validated_data
        logger.error(saleMap)
        

        api_create_sale_view(saleMap, api_user)
        return Response(None, status=status.HTTP_202_ACCEPTED)
