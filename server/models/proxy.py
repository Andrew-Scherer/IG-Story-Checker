from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base, BaseModel

class Proxy(Base, BaseModel):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    ip = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship with Session model
    sessions = relationship("Session", back_populates="proxy")

    def __str__(self):
        return f"{self.ip}:{self.port}:{self.username}:{self.password}"

    def __repr__(self):
        return f"<Proxy {self.ip}:{self.port}>"
