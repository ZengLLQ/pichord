from app.config import AppConfig, config
from app.services.instrument_service import InstrumentService, instrument_service


def get_config() -> AppConfig:
    return config


def get_instrument_service() -> InstrumentService:
    return instrument_service
