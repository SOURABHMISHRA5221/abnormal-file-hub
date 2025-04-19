from django.apps import AppConfig


class FilesConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "files"

  def ready(self):
    """Run when the app is ready to ensure deduplication is working correctly"""
    # Don't run this when running management commands
    import sys
    if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv and 'collectstatic' not in sys.argv:
      # Import here to avoid circular imports
      from .utils import verify_duplicates
      try:
        # Verify and fix duplicates on startup
        print("Verifying file duplicate consistency...")
        results = verify_duplicates()
        if results['fixed_count'] > 0:
          print(f"Fixed {results['fixed_count']} inconsistencies in file duplicates")
          print(f"Current duplicates: {results['current_duplicates']}")
          print(f"Current references: {results['current_references']}")
        else:
          print("No inconsistencies found in file duplicates.")
      except Exception as e:
        print(f"Error verifying duplicates: {e}")
