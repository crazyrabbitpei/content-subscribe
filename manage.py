#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import logging
import logging.config

logging.config.fileConfig(os.path.dirname(os.path.abspath(__file__))+'/'+os.environ.get('LOG_SETTING', 'logging.ini'))
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

from dotenv import load_dotenv
load_dotenv()


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pttcontent.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
