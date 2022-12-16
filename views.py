
from django.http import  JsonResponse
from django.utils.translation import gettext as _
from django.views import View
from django.db.models import Q
from rest_framework import serializers, permissions
from django_filters import rest_framework as rest_filters

from InvenTree.helpers import DownloadFile, str2bool
from InvenTree.admin import InvenTreeResource
from import_export.fields import Field
import import_export.widgets as widgets
from django.contrib.auth.models import User

import datetime
import pytz
from dateutil.relativedelta import relativedelta

from part.models import PartTestTemplate
from stock.models import StockItem, StockItemTestResult, StockLocation
from InvenTree.serializers import InvenTreeDecimalField, InvenTreeModelSerializer,UserSerializer
from stock.serializers import LocationBriefSerializer



### ------------------------------------------- Serializers Class ------------------------------------------------ ###
class STP_StockItemTestResultSerializer(InvenTreeModelSerializer):
    user_detail = UserSerializer(source='user', many=False, read_only=True)
    class Meta:
        """Metaclass options."""

        model = StockItemTestResult
        fields = [
            'test',
            'result',
            'value',
            'attachment',
            'notes',
            'user',
            'user_detail',
            'date',
        ]
class STP_PartTestTemplateSerializer(InvenTreeModelSerializer):
    result=serializers.SerializerMethodField('get_testResult')
    
    def get_testResult(self,obj):
        si= self.context.get("stockItem")
        
        sit=StockItemTestResult.objects.filter(stock_item=si.pk, test=obj.test_name).first()
        return STP_StockItemTestResultSerializer(sit, many=False).data
    
    class Meta:
        """Metaclass options."""

        model = PartTestTemplate
        fields = [
            'test_name',
            'description',
            'required',
            'requires_value',
            'requires_attachment',
            'result',
        ]
        
        
class STP_StockItemSerializer(InvenTreeModelSerializer):
    part_name = serializers.CharField(source='part.full_name', read_only=True)
    quantity = InvenTreeDecimalField()
    location_detail = LocationBriefSerializer(source='location', many=False, read_only=True)
    unit = serializers.SerializerMethodField()
    testItem=serializers.SerializerMethodField('get_testItem')
    
    
    def get_unit(self,obj):
        return obj.part.units
    
    def get_testItem(self,obj):
        pt=PartTestTemplate.objects.filter(part=obj.part)
        return STP_PartTestTemplateSerializer(pt, many=True, context={'stockItem': obj}).data
    
    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'part',
            'part_name',
            'updated',
            'pk',
            'location',
            'location_detail',
            'quantity',
            'unit',
            'batch',
            'required_test_count',
            'testItem',
        ]
    
### ------------------------------------------- Resource Class ------------------------------------------------ ###
class TestWidgets(widgets.CharWidget):
     def render(self, value, obj=None):
        pt=PartTestTemplate.objects.filter(part=obj.part)
        return STP_PartTestTemplateSerializer(pt, many=True, context={'stockItem':obj}).data
    
class STPTestResource(InvenTreeResource):
    itemName = Field(
        column_name=_('Item'),
        attribute='part__name', 
        widget=widgets.CharWidget(), readonly=True
        ) 
    location = Field(
        column_name=_('location'),
        attribute='location', 
        widget=widgets.ForeignKeyWidget(StockLocation, 'name'), readonly=True
        )   
    testsReport=Field(
        column_name=_('Tests'),
        attribute='pk', 
        widget=TestWidgets(), readonly=True,      
        
    )
    def export(self, queryset=None):
        fetched_queryset = list(queryset)
        return super().export(fetched_queryset)
    class Meta:
        """Metaclass"""
        model = StockItem
        skip_unchanged = False
        clean_model_instances = False
        exclude = [
            'id',
            'metadata',
            'barcode_data',
            'barcode_hash',
            'parent',
            'part',
            'supplier_part',
            'packaging',
            'belongs_to',
            'customer',
            'serial_int',
            'link',
            'build',
            'is_building',
            'purchase_order',
            'sales_order',
            'stocktake_date',
            'stocktake_user',
            'review_needed',
            'delete_on_deplete',
            'status',
            'notes',
            'purchase_price_currency',
            'purchase_price',
            'owner',
            'lft',
            'rght',
            'tree_id',
            'level',

        ]
        export_order=['itemName', 'batch', 'serial', 'expiry_date', 'quantity', 'location' ,'quantity', 'updated', 'testsReport', ]
   
### ------------------------------------------- View Class ------------------------------------------------ ###
   
class STPtestViewSet(View):
    permission_classes = [permissions.IsAuthenticated]

    http_method_names=['get'] 
    request = None
    
    def filter_queryset(self, queryset):
        params = self.request.GET
        
        teststatus = params.get('teststatus', None)
        if teststatus is not None:
            teststatus=int(teststatus)
            if teststatus == 2:
                sitested=StockItemTestResult.objects.all().values('stock_item')
                queryset = queryset.filter(~Q(pk__in=sitested))
            elif teststatus == 0:  # OK
                sitested=StockItemTestResult.objects.filter(result=True).values('stock_item')
                queryset = queryset.filter(pk__in=sitested)
            else: # == 1 => KO
                sitested=StockItemTestResult.objects.filter(result=False).values('stock_item')
                queryset = queryset.filter(pk__in=sitested)
                
        dategte = params.get('date_greater', None)
        if dategte is not None:
            date_gte = datetime.datetime.strptime(dategte, '%Y-%m-%d')
            date_gte = date_gte.replace(tzinfo=pytz.UTC)
            queryset = queryset.filter(updated__gte=date_gte)
        
        datelte = params.get('date_lesser', None)
        if datelte is not None:
            date_lte = datetime.datetime.strptime(datelte, '%Y-%m-%d')
            date_lte = date_lte.replace(tzinfo=pytz.UTC)
            queryset = queryset.filter(updated__lte=date_lte)
                
        lastdate = params.get('lastdate', None)
        if str2bool(lastdate) :
            last_date = queryset.latest('updated').updated
            if not last_date:
                last_date= datetime.datetime.now()
            max_date=datetime.datetime(last_date.year, last_date.month, last_date.day)
            queryset = queryset.filter(updated__gte=max_date)
        
        return queryset
    
    def get_queryset(self, loc=None):
        
        params = self.request.GET
        locs=None
        if loc is not None:
            locItem= StockLocation.objects.get(pk=loc)
            if loc:
                locs = locItem.getUniqueChildren(True).values("pk") 
        
        name = params.get('testname', None)
        if name is not None:
            tests=PartTestTemplate.objects.filter(test_name=name).values('part')
        else:
            tests=PartTestTemplate.objects.all().values('part')
        
        query = Q(part__in=tests)
        if locs is not None:
            query = query & Q(location__in = locs)
            
        SI = StockItem.objects.filter(query)
        
        return SI
    
    def download_queryset(self, queryset, export_format):
        """Download the filtered queryset as a data file"""
        dataset = STPTestResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = f"StockTest.{export_format}"

        return DownloadFile(filedata, filename)
    
    def get_track(request,*args, **kwargs):
        return STPtestViewSet().get(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        self.request = request
        loc = kwargs.get('loc', None)
        trackObj = self.filter_queryset(self.get_queryset(loc))
        
        export = request.GET.get('export', None)
        if export is not None:
            return self.download_queryset(trackObj, export)
        
        return  JsonResponse(STP_StockItemSerializer(trackObj, many=True).data, safe=False)
    