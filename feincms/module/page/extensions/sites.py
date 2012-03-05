from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site

try:
    from django.contrib.admin.filters import FieldListFilter, ChoicesFieldListFilter
    legacy = False
except ImportError: # Django up to 1.3
    from django.contrib.admin.filterspecs import (
        FilterSpec as FieldListFilter,
        ChoicesFilterSpec as ChoicesFieldListFilter)
    legacy = True

from feincms.module.page.models import PageManager

class SiteForeignKey(models.ForeignKey):
    description = 'A ForeignKey for Site with a custom admin filter'

class SiteFieldListFilter(ChoicesFieldListFilter):
    "Custom admin filter for Page.site"

    def __init__(self, f, request, params, model, model_admin, field_path=None):
        super(SiteFieldListFilter, self).__init__(f, request, params, model, model_admin)

        self.lookup_kwarg = '%s__id__exact' % getattr(self, 'field_path', f.name)
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)

        self.lookup_choices = [(i.pk, unicode(i))
                               for i in Site.objects.all()]
        self.lookup_choices.sort(key=lambda i: i[1])


    def choices(self, cl):
        for pk, title in self.lookup_choices:
            yield {
                'selected':     pk == int(self.lookup_val or settings.SITE_ID),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display':      title,
            }

    def title(self):
        return _('Site')

# Register the custom admin filter
if legacy:
    FieldListFilter.filter_specs.insert(0,
                                         (lambda f: isinstance(f, SiteForeignKey), SiteFieldListFilter))
else:
    FieldListFilter.register(lambda f: getattr(f, 'site_filter', False),
                             SiteFieldListFilter,
                             take_priority=True)

def register(cls, admin_cls):
    "Add a foreign key on Site to the Page model"
    cls.add_to_class('site',
                     SiteForeignKey(Site,
                                    verbose_name=_('Site'),
                                    default=settings.SITE_ID,
                                    ))

    PageManager.add_to_active_filters(current_site, key='current_site')

    # Show the site on the admin list
    admin_cls.list_display.extend(['site'])

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[], patterns=["^feincms\.module\.page\.extensions\.sites\.SiteForeignKey"])
except ImportError:
    pass
