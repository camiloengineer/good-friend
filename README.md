# good-friend

Sistema de marcaje automático para gestión de asistencia.

## Estructura

```
good-friend/
├── main.py
├── config.py
├── services/
│   ├── email_service.py
│   ├── holiday_service.py
│   └── marcaje_service.py
├── utils/
│   ├── delay_manager.py
│   └── rut_validator.py
├── tests/
│   └── test_email_service.py
├── logs/
├── requirements.txt
├── .env
└── README.md
```

## Instalación y magia

```bash
pip install -r requirements.txt
python main.py
```

## Testing

```bash
pytest tests/ -v
```

## Licencia

MIT License
