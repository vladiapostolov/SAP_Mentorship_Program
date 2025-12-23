from dataclasses import dataclass
from flask_login import UserMixin

@dataclass
class User(UserMixin):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool = True

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
