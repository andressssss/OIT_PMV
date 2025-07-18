from rest_framework.routers import DefaultRouter
from api.views.usuarios import PerfilViewSet

router = DefaultRouter()
router.register(r'perfiles', PerfilViewSet, basename='perfiles')

urlpatterns = router.urls
