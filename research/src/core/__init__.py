"""
Core business logic for LottoNZ application

Note: submodules are imported explicitly by consumers (e.g.
``from src.core.prediction_engine import ...``). The package __init__ must not
eagerly import side-effectful modules — ``lotto_generator`` reads an Excel file
at import time and is intended to be run as a standalone script.
"""

__all__ = []
