# billing-core-service

Microservicio transaccional del backend de **AgroFactura Cloud**.

## Responsabilidades
- Autenticación federada y por credenciales con JWT (US-01).
- Directorio de clientes y cooperativas compradoras con validación de NIF/CIF español (US-02).
- Motor de reglas fiscales agrarias: Régimen Especial de Agricultura, Ganadería y Pesca (REAGP al 12%) y retención de IRPF (2%) (US-03).
- Secuenciador correlativo atómico y estricto conforme a la Ley Antifraude y reglamento VeriFactu (US-03, US-06).
