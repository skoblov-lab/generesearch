from django.contrib import admin

# Register your models here.

from .models import MutagenesisRecord


admin.site.register(MutagenesisRecord)


if __name__ == '__main__':
    raise RuntimeError
