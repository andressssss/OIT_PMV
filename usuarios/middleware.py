from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect
import logging
from django.template.base import VariableDoesNotExist
from asgiref.sync import iscoroutinefunction

logger = logging.getLogger('django')


class ExpiredSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            sesion_expira = request.session.get_expiry_date()
            if sesion_expira <= now():
                print("La sesión ha expirado")
                messages.error(request, "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
                return redirect('login')
        return self.get_response(request)


class TemplateDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._is_async = iscoroutinefunction(get_response)

    def __call__(self, request):
        if self._is_async:
            return self.__acall__(request)
        return self.__scall__(request)

    def __scall__(self, request):
        try:
            response = self.get_response(request)
        except Exception as e:
            logger.error(f"[MIDDLEWARE ERROR - sync] Error general: {repr(e)}")
            raise

        return self._post_process(response)

    async def __acall__(self, request):
        try:
            response = await self.get_response(request)
        except Exception as e:
            logger.error(f"[MIDDLEWARE ERROR - async] Error general: {repr(e)}")
            raise

        return await self._apost_process(response)

    def _post_process(self, response):
        if (
            hasattr(response, "template_name") and
            hasattr(response, "context_data") and
            hasattr(response, "render") and
            callable(response.render) and
            response.status_code < 400  # 🚫 solo renderiza si no es error
        ):
            template_names = (
                response.template_name
                if isinstance(response.template_name, list)
                else [response.template_name]
            )
            logger.info(f"[MIDDLEWARE DEBUG] Plantillas usadas: {template_names}")

            for name in template_names:
                try:
                    response.render()
                except VariableDoesNotExist as ve:
                    logger.warning(f"[MIDDLEWARE WARNING] VariableDoesNotExist en '{name}': {ve}")
                except Exception as ex:
                    logger.warning(f"[MIDDLEWARE WARNING] Otro error al renderizar '{name}': {ex}")

        return response

    async def _apost_process(self, response):
        if (
            hasattr(response, "template_name") and
            hasattr(response, "context_data") and
            hasattr(response, "render") and
            callable(response.render) and
            response.status_code < 400  # 🚫 solo renderiza si no es error
        ):
            template_names = (
                response.template_name
                if isinstance(response.template_name, list)
                else [response.template_name]
            )
            logger.info(f"[MIDDLEWARE DEBUG] Plantillas usadas: {template_names}")

            for name in template_names:
                try:
                    await response.render()
                except VariableDoesNotExist as ve:
                    logger.warning(f"[MIDDLEWARE WARNING] VariableDoesNotExist en '{name}': {ve}")
                except Exception as ex:
                    logger.warning(f"[MIDDLEWARE WARNING] Otro error al renderizar '{name}': {ex}")

        return response
