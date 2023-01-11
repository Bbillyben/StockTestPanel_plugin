from plugin import InvenTreePlugin
from plugin.mixins import PanelMixin, SettingsMixin
from plugin.base.integration.mixins import UrlsMixin
from django.core.validators import  MinValueValidator
from stock.views import StockLocationDetail, StockIndex
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.translation import gettext as _


from plugins.StockTestPanel_plugin import views as STPviews
from part.models import PartTestTemplate
### ------------------------------------------- Plugin Class ------------------------------------------------ ###

class StockTestPanel(PanelMixin, UrlsMixin, InvenTreePlugin):

    NAME = "StockTestPanel"
    SLUG = "stocktest"
    TITLE = "StockTest panel"
    AUTHOR = "Bbillyben"
    DESCRIPTION = "A plugin to visualize last stock test item by location"
    VERSION = "0.1"

    # SETTINGS = {
    #     'MONTH_FOLLOW': {
    #         'name': 'Number of Month to follow',
    #         'description': 'number ofmonth from last entry to display in Stock Track Panel',
    #         'default': 1,
    #         'validator': MinValueValidator(1),
    #     },
    # }

    def get_panel_context(self, view, request, context):
        """Returns enriched context."""
        ctx = super().get_panel_context(view, request, context)

        return ctx

    def get_custom_panels(self, view, request):
        if isinstance(view, StockIndex) or isinstance(view, StockLocationDetail):
            
            if isinstance(view, StockLocationDetail):
                loc=view.get_object()
                urlTrac=reverse('plugin:stocktest:test-location', kwargs={'loc': loc.pk})
            else:
                urlTrac=reverse('plugin:stocktest:test-list')
                
            context={'dataUrl':urlTrac}
            
            # Test Names 
            tNames = PartTestTemplate.objects.all().values('test_name').distinct()
            context['testName']=tNames
            
            tmpRend = render_to_string(template_name='stocktestpanel/STP_panel.html',context=context)

            panels = [
                {
                    # Simple panel without any actual content
                    'title': 'Stock Test',
                    'content': tmpRend,
                    'icon' : 'fa-vial', 
                    'javascript': 'STP_initPanel',
                    'javascript_template': 'stocktestpanel/STP_panel.js'
                }
            ]
            return panels
        return []

    def setup_urls(self):
        # """Urls that are exposed by this plugin."""
    
        SMP_URL=[
            path('test/', STPviews.STPtestViewSet.get_track, name='test-list'),
            path('test/location/<loc>/', STPviews.STPtestViewSet.get_track, name='test-location'),      
        ]
        return SMP_URL
