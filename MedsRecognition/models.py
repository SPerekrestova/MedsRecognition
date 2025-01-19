from django.db import models


class UploadedImage(models.Model):
    image = models.ImageField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_path = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "uploaded_images"
        managed = True

    def __str__(self):
        # Use a fallback to avoid AttributeError on missing image or name
        return self.image.name if self.image and hasattr(self.image, "name") else "No Image"


class Profile(models.Model):
    """
    A Django-managed table in the 'public' schema
    that references auth.users (user_id) via a manual FK.
    """

    id = models.BigAutoField(primary_key=True)
    user_id = models.UUIDField()
    display_name = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles"
        managed = True

    def __str__(self):
        return self.display_name or f"Profile {self.id}"


class Medication(models.Model):
    id = models.BigAutoField(primary_key=True)

    profile = models.ForeignKey(
        Profile,  # references the Profile class
        on_delete=models.CASCADE,
        related_name="scanned_medications",
    )
    medication_name = models.CharField(max_length=255, blank=True, null=True)
    scan_date = models.DateTimeField(auto_now_add=True)
    active_ingredients = models.JSONField(blank=True, null=True)
    scanned_text = models.TextField(blank=True, null=True)
    dosage = models.CharField(max_length=255, blank=True, null=True)
    prescription_details = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "scanned_medication"
        managed = True

    def __str__(self):
        # Use getattr to safely access the user's username
        username = getattr(self.profile, "username", "Unknown User")
        return f"{self.medication_name} - {username}"
