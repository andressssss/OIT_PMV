from rest_framework.routers import DefaultRouter
from api.views.usuarios import PerfilViewSet, CentroFormacionViewSet, DepartamentoViewSet, MunicipioViewSet, InstitucionViewSet, AprendizViewSet, PermisoViewSet

router = DefaultRouter()
router.register(r'perfiles', PerfilViewSet, basename='perfiles')
router.register(r'centros', CentroFormacionViewSet, basename='centro')
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'municipios', MunicipioViewSet, basename='municipio')
router.register(r'instituciones', InstitucionViewSet, basename='institucion')
router.register(r'aprendices', AprendizViewSet, basename='aprendiz')
router.register(r'permisos', PermisoViewSet, basename='permiso')

urlpatterns = router.urls
