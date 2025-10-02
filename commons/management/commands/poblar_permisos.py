from django.core.management.base import BaseCommand, CommandError
from commons.models import T_permi, T_perfil


class Command(BaseCommand):
    help = "Pobla los permisos predeterminados de cada usuario, solo usar con la salida del modulo de permisos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--id_perfil",
            type=int,
            help="Crea los permisos de un solo perfil"
        )

    def handle(self, *args, **options):
        perfil_id = options["id_perfil"]

        if perfil_id:
            perfiles = T_perfil.objects.filter(id=perfil_id)
            if not perfiles.exists():
                self.stdout.write(self.style.ERROR(
                    f"No se encontro el perfil con el ID = {perfil_id}"
                ))
                return
        else:
            perfiles = T_perfil.objects.all()

        self.stdout.write(self.style.WARNING(
            f"Iniciando carga de permisos para {len(perfiles)} perfiles"
        ))

        for p in perfiles:
            if not p.rol:
                self.stdout.write(self.style.WARNING(
                    f"El perfil {p} no tiene rol asociado, se omite"
                ))
                continue

            try:
                crear_permisos(p)
                self.stdout.write(self.style.SUCCESS(
                    f"Permisos creados para el perfil {p.id}"))

            except Exception as e:
                raise CommandError(f"Error ejecutando: {e}")
        self.stdout.write(self.style.SUCCESS("Carga finalizada con éxito"))


def crear_permisos(perfil):

    T_permi.objects.filter(perfil=perfil).delete()

    permisos = PERMISOS_ROL.get(perfil.rol, [])

    for modu, acci in permisos:
        T_permi.objects.get_or_create(
            modu=modu,
            acci=acci,
            filtro=None,
            perfil=perfil
        )


PERMISOS_ROL = {
    "admin": [
        ("departamentos", "ver"),
        ("departamentos", "editar"),
        ("municipios", "ver"),
        ("municipios", "editar"),
        ("usuarios", "ver"),
        ("usuarios", "editar"),
        ("instructores", "ver"),
        ("instructores", "editar"),
        ("aprendices", "ver"),
        ("aprendices", "editar"),
        ("admin", "ver"),
        ("admin", "editar"),
        ("lideres", "ver"),
        ("lideres", "editar"),
        ("cuentas", "ver"),
        ("cuentas", "editar"),
        ("gestores", "ver"),
        ("gestores", "editar"),
        ("fichas", "ver"),
        ("fichas", "editar"),
        ("portafolios", "ver"),
        ("portafolios", "editar"),
        ("instituciones", "ver"),
        ("instituciones", "editar"),
        ("centros", "ver"),
        ("centros", "editar"),
        ("programas", "ver"),
        ("programas", "editar"),
        ("competencias", "ver"),
        ("competencias", "editar"),
        ("raps", "ver"),
        ("raps", "editar"),
        ("dashboard", "ver")
    ],
    "instructor": [
        ("fichas", "ver"),
        ("fichas", "editar"),
        ("portafolios", "ver"),
        ("portafolios", "editar"),
    ],
    "aprendiz": [],
    "lider": [
        ("aprendices", "ver"),
        ("aprendices", "editar"),
        ("gestores", "ver"),
        ("gestores", "editar"),
        ("fichas", "ver"),
        ("fichas", "editar"),
        ("portafolios", "ver"),
        ("portafolios", "editar"),
        ("instituciones", "ver"),
        ("instituciones", "editar"),
        ("centros", "ver"),
        ("centros", "editar")
    ],
    "gestor": [
        ("aprendices", "ver"),
        ("aprendices", "editar")
    ],
    "cuentas": [],
    "consulta": [
        ("usuarios", "ver"),
        ("instructores", "ver"),
        ("aprendices", "ver"),
        ("lideres", "ver"),
        ("cuentas", "ver"),
        ("gestores", "ver"),
        ("fichas", "ver"),
        ("portafolios", "ver"),
        ("instituciones", "ver"),
        ("centros", "ver"),
        ("competencias", "ver"),
        ("raps", "ver"),
    ],
}
