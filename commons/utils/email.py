from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

def enviar_correo(destinatarios, asunto, mensaje, mensaje_html=None):
    """
    Envía un correo con soporte HTML y texto plano.
    """

    if mensaje_html is None:
        # Plantilla base institucional
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f7; margin: 0; padding: 0;">
          <table align="center" width="600" style="background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <tr style="background-color: #1E2DBE;">
              <td style="padding: 20px; text-align: center;">
                <img src="https://adminsenatic.formacionprofesional-oit.org/static/images/ilo_white.png" alt="OIT" width="120">
              </td>
            </tr>
            <tr>
              <td style="padding: 30px;">
                <h2 style="color: #1E2DBE;">{asunto}</h2>
                <p style="font-size: 15px; color: #333;">{mensaje}</p>
                <hr style="border:none; border-top:1px solid #eee; margin: 20px 0;">
                <p style="font-size: 13px; color: #888;">
                  Este mensaje fue generado automáticamente por la plataforma institucional de Formación Profesional OIT.<br>
                  Por favor, no responda a este correo.
                </p>
              </td>
            </tr>
            <tr style="background-color: #f4f4f7;">
              <td style="text-align:center; padding:15px; font-size:12px; color:#777;">
                &copy; {timezone.now().year} Formación Profesional OIT
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

    # Cuerpo alternativo (texto plano)
    mensaje = mensaje.replace('<br>', '\n').replace('<br/>', '\n')

    # Construcción del correo
    email = EmailMultiAlternatives(
        subject=asunto,
        body=mensaje,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply-senatic@formacionprofesional-oit.org'),
        to=destinatarios
    )
    email.attach_alternative(mensaje_html, "text/html")
    email.send()
