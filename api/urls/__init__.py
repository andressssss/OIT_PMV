from django.urls import path, include

urlpatterns = [
    path('formacion/', include('api.urls.formacion')),
    path('matricula/', include('api.urls.matricula')),
    path('usuarios/', include('api.urls.usuarios')),
    # Agrega más módulos aquí según crezcan
]
