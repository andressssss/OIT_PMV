from rest_framework.routers import DefaultRouter
from api.views.formacion import RapsViewSet, CompetenciasViewSet, FichasViewSet

router = DefaultRouter()
router.register(r'raps', RapsViewSet, basename='raps')
router.register(r'competencias', CompetenciasViewSet, basename='competencias')
router.register(r'fichas', FichasViewSet, basename='fichas')

urlpatterns = router.urls
