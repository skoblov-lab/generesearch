from django.contrib import admin

# Register your models here.

from .models import Submission


admin.site.register(Submission)


if __name__ == '__main__':
    raise RuntimeError
