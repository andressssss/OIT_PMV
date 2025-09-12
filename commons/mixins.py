from django.db.models import Q
from commons.models import T_perfil, T_permi

FILTER_FIELD_MAPPINGS = {
    "fichas": {
        "depa": "insti__muni__nom_departa__nom_departa",
        "muni": "insti__muni__nom_muni",
        "programa": "progra__nom",
    },
    "aprendices": {
        "depa": "ficha__insti__muni__nom_departa__nom_departa",
        "muni": "ficha__insti__muni__nom_muni",
    },
    "instructores": {
        "depa": "centro__muni__nom_departa__nom_departa",
    },
}


class PermisosMixin:
    modulo = None
    accion = "ver"

    def get_perfil(self, request):
        return T_perfil.objects.get(user=request.user)

    def get_permission_filters(self, request):
        """Obtiene los filtros para el módulo/acción definidos en la clase."""
        return self.get_permission_filters_for(request, self.modulo, self.accion)

    def get_permission_filters_for(self, request, modulo, accion="ver"):
        """Obtiene los filtros para un módulo/acción específico."""
        perfil = self.get_perfil(request)
        try:
            permiso = T_permi.objects.get(
                perfil=perfil,
                modu=modulo,
                acci=accion
            )
            return permiso.filtro or {}
        except T_permi.DoesNotExist:
            return None  # 🔑 None = sin permiso

    def apply_permission_filters(self, queryset, request):
        """Aplica permisos usando self.modulo y self.accion."""
        return self.apply_permission_filters_for(queryset, request, self.modulo, self.accion)

    def apply_permission_filters_for(self, queryset, request, modulo, accion="ver"):
        """Aplica permisos a un queryset para un módulo/acción específico."""
        filtros = self.get_permission_filters_for(request, modulo, accion)

        if filtros is None:  # 🚫 sin permiso
            return queryset.none()

        if not filtros:  # ✅ permiso total
            return queryset

        field_map = FILTER_FIELD_MAPPINGS.get(modulo, {})
        q_obj = Q()
        for campo, valor in filtros.items():
            if campo in field_map:
                q_obj &= Q(**{field_map[campo]: valor})

        return queryset.filter(q_obj)

    def get_permission_actions(self, request):
        """Devuelve las acciones del módulo actual (self.modulo)."""
        return self.get_permission_actions_for(request, self.modulo)

    def get_permission_actions_for(self, request, modulo):
        """Devuelve las acciones disponibles para un módulo específico."""
        perfil = self.get_perfil(request)
        permisos = T_permi.objects.filter(perfil=perfil, modu=modulo)

        acciones = {}
        for p in permisos:
            acciones[p.acci] = True
        return acciones

    def get_all_permissions(self, request):
        """Devuelve {modulo: {accion: True}} para TODOS los módulos."""
        perfil = self.get_perfil(request)
        permisos = T_permi.objects.filter(perfil=perfil)

        acciones_por_modulo = {}
        for p in permisos:
            if p.modu not in acciones_por_modulo:
                acciones_por_modulo[p.modu] = {}
            acciones_por_modulo[p.modu][p.acci] = True

        return acciones_por_modulo
