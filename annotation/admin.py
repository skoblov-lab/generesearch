from django.contrib import admin

# Register your models here.

from .models import MutagenesisRecord, Annotator


admin.site.register(Annotator)


@admin.register(MutagenesisRecord)
class MutagenesisAdmin(admin.ModelAdmin):
    list_display = ('prot', 'sub', 'description', 'completed')
    search_fields = ('name', 'description', 'completed')
    list_filter = ('completed', 'by')


if __name__ == '__main__':
    raise RuntimeError
