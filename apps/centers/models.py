from django.db import models


class Center(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام')
    english_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام انگلیسی')
    logo = models.ImageField(upload_to='centers/logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
