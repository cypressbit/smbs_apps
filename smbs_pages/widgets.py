import importlib
import pkgutil

from django.conf import settings


def iter_namespace(ns_pkg):
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def find_widgets():
    widgets = []
    for app in settings.INSTALLED_APPS:
        widget_spec = importlib.util.find_spec('{}.smbs_widgets'.format(app))
        if widget_spec:
            widget_module = importlib.import_module('{}.smbs_widgets'.format(app))
            try:
                found_widgets = [
                    (name, importlib.import_module(name).Widget.NAME) for finder, name, i in iter_namespace(widget_module)
                ]
                widgets.extend(found_widgets)
            except AttributeError:
                continue
    return widgets


def load_widget(name):
    try:
        widget = importlib.import_module(name)
    except AttributeError:
        widget = None
    return widget


discovered_widgets = find_widgets()
