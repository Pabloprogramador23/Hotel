from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to='reports/')

    def __str__(self):
        return f"Report {self.name} generated on {self.generated_at}"
