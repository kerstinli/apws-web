import sys

from django.shortcuts import render


def custom_500(request, *args, **kwargs):
    """
    Custom 500 error handler to provide the exception to the template.
    """
    exc_info = sys.exc_info()
    exception = exc_info[1]
    return render(request, "500.html", {"exception": exception}, status=500)
