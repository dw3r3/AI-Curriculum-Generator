from django.db import models
from django.contrib.auth.models import User

class Curriculum(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    duration = models.IntegerField()
    goal = models.TextField(null=True, blank=True)
    generated_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic} ({self.duration} weeks)"
