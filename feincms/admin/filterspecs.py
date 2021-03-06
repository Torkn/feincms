# encoding=utf-8
# Thanks to http://www.djangosnippets.org/snippets/1051/
#
# Authors: Marinho Brandao <marinho at gmail.com>
#          Guilherme M. Gondim (semente) <semente at taurinus.org>

try:
    from django.contrib.admin.filters import FieldListFilter, ChoicesFieldListFilter
    legacy = False
except ImportError: # Django up to 1.3
    from django.contrib.admin.filterspecs import (
        FilterSpec as FieldListFilter,
        ChoicesFilterSpec as ChoicesFieldListFilter)
    legacy = True

from django.contrib.sites.models import Site
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings


class ParentFieldListFilter(ChoicesFieldListFilter):
    """
    Improved list_filter display for parent Pages by nicely indenting hierarchy

    In theory this would work with any mptt model which uses a "title" attribute.

    my_model_field.page_parent_filter = True
    """

    def __init__(self, f, request, params, model, model_admin, field_path=None):
        from feincms.utils import shorten_string

        try:
            super(ParentFieldListFilter, self).__init__(f, request, params, model, model_admin, field_path)
        except TypeError: # Django 1.2
            super(ParentFieldListFilter, self).__init__(f, request, params, model, model_admin)

        # If the sites extension is installed, only show the parents of this site
        if hasattr(Site, 'page_set'):
            # What site is the admin displaying?
            if request.GET.has_key('site__id__exact'):
                admin_site = request.GET['site__id__exact']
            else:
                # No site filtered in admin, so show current site
                admin_site = django_settings.SITE_ID

            parent_ids = model.objects.filter(site__id__exact=admin_site).exclude(parent=None).values_list("parent__id", flat=True).order_by("parent__id").distinct()
        else:
            parent_ids = model.objects.exclude(parent=None).values_list("parent__id", flat=True).order_by("parent__id").distinct()

        parents = model.objects.filter(pk__in=parent_ids).values_list("pk", "title", "level")
        self.lookup_choices = [(pk, "%s%s" % ("&nbsp;" * level, shorten_string(title, max_length=25))) for pk, title, level in parents]

    def choices(self, cl):
        yield {
            'selected':     self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display':      _('All')
        }

        for pk, title in self.lookup_choices:
            yield {
                'selected':     pk == int(self.lookup_val or '0'),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display':      mark_safe(smart_unicode(title))
            }

    def title(self):
        return _('Parent')

class CategoryFieldListFilter(ChoicesFieldListFilter):
    """
    Customization of ChoicesFilterSpec which sorts in the user-expected format

    my_model_field.category_filter = True
    """

    def __init__(self, f, request, params, model, model_admin, field_path=None):
        try:
            super(CategoryFieldListFilter, self).__init__(f, request, params, model, model_admin, field_path)
        except TypeError: # Django 1.2
            super(CategoryFieldListFilter, self).__init__(f, request, params, model, model_admin)

        # Restrict results to categories which are actually in use:
        self.lookup_choices = [
            (i.pk, unicode(i)) for i in f.related.parent_model.objects.exclude(**{
                f.related.var_name: None
            })
        ]
        self.lookup_choices.sort(key=lambda i: i[1])

    def choices(self, cl):
        yield {
            'selected':     self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display':      _('All')
        }

        for pk, title in self.lookup_choices:
            yield {
                'selected':     pk == int(self.lookup_val or '0'),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display':      mark_safe(smart_unicode(title))
            }

    def title(self):
        return _('Category')


if legacy:
    # registering the filter
    FieldListFilter.filter_specs.insert(0,
        (lambda f: getattr(f, 'parent_filter', False), ParentFieldListFilter)
    )

    FieldListFilter.filter_specs.insert(1,
        (lambda f: getattr(f, 'category_filter', False), CategoryFieldListFilter)
    )
else:
    FieldListFilter.register(lambda f: getattr(f, 'parent_filter', False),
        ParentFieldListFilter,
        take_priority=True)
    FieldListFilter.register(lambda f: getattr(f, 'category_filter', False),
        CategoryFieldListFilter,
        take_priority=True)
