from django.contrib import admin

# Register your models here.

from .models import Event, Employee, Publication


admin.site.register(Event)
admin.site.register(Employee)
admin.site.register(Publication)


if __name__ == '__main__':
    raise RuntimeError
