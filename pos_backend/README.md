# POS Backend (Django + DRF + JWT + PostgreSQL)

## Puesta en marcha
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # ajusta credenciales de PostgreSQL
python manage.py makemigrations accounts inventory sales
python manage.py migrate
python manage.py createsuperuser   # luego edita su role a ADMIN en /admin/
python manage.py test
python manage.py runserver
```

## Endpoints
| Método | URL | Descripción |
|---|---|---|
| POST | /api/auth/token/ , /api/auth/token/refresh/ | Login JWT |
| GET | /api/auth/me/ | Usuario y rol |
| CRUD | /api/categories/ , /api/products/ | Admin escribe, cajero solo lee (sin cost_price) |
| GET | /api/products/by-code/{code}/ | Búsqueda por código de barras |
| POST | /api/shifts/open/ | `{"initial_cash": "100.00"}` |
| GET | /api/shifts/current/ | Turno abierto + resumen parcial |
| POST | /api/shifts/close/ | `{"final_cash_real": "350.00"}` → totales por método y diferencia |
| GET | /api/shifts/{id}/summary/ | Resumen de cualquier turno |
| POST | /api/sales/ | `{"payment_method":"CASH","items":[{"product":1,"quantity":2}]}` |
| GET | /api/sales/?shift={id} | Historial |
| POST | /api/sales/{id}/void/ | Anular (solo admin), repone stock |
