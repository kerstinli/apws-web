# Source - https://stackoverflow.com/a/79515165
# Posted by Genarito
# Retrieved 2026-07-05, License - CC BY-SA 4.0

from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """
    Replaces the native django-admin makemessages command to add the --no-fuzzy-matching option.
    Taken from https://github.com/speedy-net/speedy-net/blob/staging/speedy/core/base/management/commands/make_messages.py
    (referenced in https://code.djangoproject.com/ticket/10852#comment:19)
    """

    msgmerge_options = makemessages.Command.msgmerge_options + ["--no-fuzzy-matching"]
