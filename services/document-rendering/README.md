# document-rendering-service

Microservicio stateless de compilación y despacho documental de **AgroFactura Cloud**.

## Responsabilidades
- Compilación de plantillas HTML5/CSS vectorizadas con Jinja2 para facturas agrícolas.
- Motor de renderizado binario PDF de alta fidelidad (US-04).
- Despacho y sincronización desatendida a Google Drive mediante adaptadores modulares (US-04).
- Despacho automático de notificaciones por correo electrónico transaccional hacia clientes y gestoría contable (US-05).
- Soporte para ejecución en modo simulado (*mock mode*) en desarrollo local e integración continua.
