# Hito 1: Definición del Proyecto, Modelo de Negocio y Arquitectura de Referencia

Este documento enlaza a la memoria técnica completa del **Hito 1** para el proyecto **AgroFactura Cloud**:

👉 **[Ver Memoria Técnica Completa de Hito 1 (docs/README.md)](./README.md)**

---

### Resumen de Contenidos Desarrollados

- **[1. Definición del Dominio y Problemática de Negocio](./README.md#1-definición-del-dominio-y-problemática-de-negocio):** Caso de uso real del agricultor familiar, sustitución de hojas de cálculo de Excel manuales, riesgos fiscales/legales (RD 1619/2012 y Ley Antifraude / VeriFactu) y casuística impositiva agraria (REAGP con compensación al 12%/10.5% e IRPF al 2%).
- **[2. Justificación Teórica bajo NIST SP 800-145](./README.md#2-justificación-teórica-bajo-nist-sp-800-145):** Análisis exhaustivo de las 5 características esenciales de la nube (Autoservicio bajo demanda, Acceso amplio a la red, Asignación común de recursos, Rápida elasticidad estacional agraria y Servicio medido).
- **[3. Mapeo de Actores bajo NIST SP 500-292 e Impacto Económico](./README.md#3-mapeo-de-actores-bajo-nist-sp-500-292-e-impacto-económico):** Roles de Consumidor, Proveedor, Intermediario (Google Drive, OAuth, Resend), Auditor (AEAT) y Operador; Análisis comparativo CapEx vs OpEx con aprovechamiento de capas gratuitas (*Free Tiers* a coste ~0 €).
- **[4. Arquitectura de Referencia y Microservicios](./README.md#4-arquitectura-de-referencia-y-microservicios):** Desacoplamiento entre `billing-core-service` (transaccional/fiscal) y `document-rendering-service` (stateless, renderizado PDF y conectores externos), con diagramas Mermaid de componentes y de secuencia.
- **[5. Especificación Sintética de la API REST](./README.md#5-especificación-sintética-de-la-api-rest):** Contratos JSON, rutas, métodos HTTP y códigos de estado semánticos para ambos microservicios.
- **[6. Catálogo de Historias de Usuario (Backlog Inicial)](./README.md#6-catálogo-de-historias-de-usuario-backlog-inicial):** Historias de usuario (US-01 a US-06) con formato estándar, criterios de aceptación Gherkin y tareas técnicas.
- **[7. Configuración de Ingeniería de Software en GitHub](./README.md#7-configuración-de-ingeniería-de-software-en-github):** Políticas de ramas (GitHub Flow), convención de commits semánticos, gestión del tablero con GitHub Projects y plantillas de trabajo en `.github/`.
