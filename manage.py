#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cropsight_backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your "
<<<<<<< HEAD
            "PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
=======
            "PYTHONPATH environment variable?"
>>>>>>> 08430856d59c2322acb2d319a146251f0b5a370d
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
