from rest_framework.routers import DefaultRouter
from api.views.notificaciones import NotificacionesViewSet

router = DefaultRouter()
router.register(r'', NotificacionesViewSet, basename='notificaciones')

urlpatterns = router.urls
