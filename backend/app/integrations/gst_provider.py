"""Boundary for a future authorized provider. No simulated portal responses."""
from typing import Protocol


class GSTProvider(Protocol):
    def register_einvoice(self, company_id: int, payload: dict) -> dict: ...
    def cancel_einvoice(self, company_id: int, irn: str, reason: str) -> dict: ...
    def create_eway_bill(self, company_id: int, payload: dict) -> dict: ...


class NotConfiguredGSTProvider:
    def register_einvoice(self, company_id: int, payload: dict) -> dict:
        raise NotImplementedError('Authorized GST provider is not configured')

    def cancel_einvoice(self, company_id: int, irn: str, reason: str) -> dict:
        raise NotImplementedError('Authorized GST provider is not configured')

    def create_eway_bill(self, company_id: int, payload: dict) -> dict:
        raise NotImplementedError('Authorized GST provider is not configured')
