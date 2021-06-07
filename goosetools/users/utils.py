from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from goosetools.users.models import CrudAccessController


def filter_controlled_qs_by(controllable_qs, func, request, return_as_qs=False):
    controllable_qs = controllable_qs.select_related(
        "access_controller"
    ).prefetch_related(
        "access_controller__viewable_by",
        "access_controller__adminable_by",
    )
    valid_items = []
    permissions_id_cache = CrudAccessController.make_permissions_id_cache(
        request.gooseuser
    )
    for f in controllable_qs.all():
        print(f"Checking {func} for {f} for {request.gooseuser}")
        if getattr(f.access_controller, func)(request.gooseuser, permissions_id_cache):
            print(f"Had {func}")
            valid_items.append(f)
        else:
            print("Did not have")

    if return_as_qs:
        return controllable_qs.filter(id__in=[v.id for v in valid_items])
    else:
        return valid_items


def filter_controlled_qs_to_viewable(controllable_qs, request, return_as_qs=False):
    return filter_controlled_qs_by(controllable_qs, "can_view", request, return_as_qs)


def filter_controlled_qs_to_usable(controllable_qs, request, return_as_qs=False):
    return filter_controlled_qs_by(controllable_qs, "can_use", request, return_as_qs)


def can_view(clazz):
    """
    Decorator for views that checks that the user has the specified permission
    otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, pk, *args, **kwargs):
            f = get_object_or_404(clazz, pk=pk)
            if f.access_controller.can_view(request.gooseuser):
                return function(request, pk, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper


def can_admin(clazz):
    """
    Decorator for views that checks that the user has the specified permission
    otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, pk, *args, **kwargs):
            f = get_object_or_404(clazz, pk=pk)
            if f.access_controller.can_admin(request.gooseuser):
                return function(request, pk, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper


def can_edit(clazz):
    """
    Decorator for views that checks that the user has the specified permission
    otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, pk, *args, **kwargs):
            f = get_object_or_404(clazz, pk=pk)
            if f.access_controller.can_edit(request.gooseuser):
                return function(request, pk, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper


def can_delete(clazz):
    """
    Decorator for views that checks that the user has the specified permission
    otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, pk, *args, **kwargs):
            f = get_object_or_404(clazz, pk=pk)
            if f.access_controller.can_delete(request.gooseuser):
                return function(request, pk, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper


def can_use(clazz):
    """
    Decorator for views that checks that the user has the specified permission
    otherwise returning HttpForbidden
    """

    def outer_wrapper(function):
        @wraps(function)
        def wrap(request, pk, *args, **kwargs):
            f = get_object_or_404(clazz, pk=pk)
            if f.access_controller.can_use(request.gooseuser):
                return function(request, pk, *args, **kwargs)
            return HttpResponseForbidden()

        return wrap

    return outer_wrapper
