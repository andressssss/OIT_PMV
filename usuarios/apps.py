from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        # Importar las signals para que Django las registre al arrancar.
        from usuarios import signals  # noqa: F401