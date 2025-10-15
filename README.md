# Plataforma de Gestión Institucional – OIT (Proyecto SENATIC)

Sistema integral desarrollado en **Django** para la **Organización Internacional del Trabajo (OIT)** en el marco del proyecto **SENATIC**, orientado a la **gestión documental, control de procesos y métricas institucionales**.  
Diseñado para atender más de **1.500 usuarios concurrentes**, con infraestructura distribuida, módulos personalizados y balanceo de servicios en producción.

---

## Características principales

- **Arquitectura distribuida** de aplicación y base de datos (MySQL + ProxySQL).  
- **Módulos personalizados** para gestión documental, indicadores (KPI) y flujos de aprobación.  
- **Autenticación segura y balanceo de servicios** mediante **NGINX + SSL**.  
- **Automatización de despliegues** con **Docker + Docker Compose**.  
- **SMTP relay institucional** configurado con **SPF, DKIM y DMARC**.  
- **Gestión de variables de entorno** (`.env.dev`, `.env.pre`, `.env.prod`) según ambiente.  
- **Reportes PDF profesionales** con identidad visual OIT (PyPDF2 + ReportLab).  
- **Visualización de datos** y métricas con Power BI y endpoints REST.

---

## Arquitectura del Sistema

```mermaid
graph TD
    A[Cliente Web] -->|HTTPS| B[NGINX - Load Balancer]
    B --> C[Daphne ASGI]
    C --> D[Django App (Docker Container)]
    D --> E[(MySQL Cluster via ProxySQL)]
    D --> F[Redis Cache]
    D --> G[SMTP Relay SPF/DKIM/DMARC]
    D --> H[PDF Generator - ReportLab y PyPDF2]
