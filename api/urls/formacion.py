from rest_framework.routers import DefaultRouter
from api.views.formacion import RapsViewSet, CompetenciasViewSet, FichasViewSet, ProgramasViewSet, FasesViewSet

router = DefaultRouter()
router.register(r'raps', RapsViewSet, basename='raps')
router.register(r'competencias', CompetenciasViewSet, basename='competencias')
router.register(r'fichas', FichasViewSet, basename='fichas')
router.register(r'programas', ProgramasViewSet, basename='programa')
router.register(r'fases', FasesViewSet, basename='fases')

urlpatterns = router.urls
