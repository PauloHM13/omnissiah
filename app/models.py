# app/models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    must_change_password: bool
    phone: Optional[str] = None
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

@dataclass
class Doctor:
    user_id: int
    full_name: str
    crm: Optional[str] = None
    specialty: Optional[str] = None
    rqe: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
