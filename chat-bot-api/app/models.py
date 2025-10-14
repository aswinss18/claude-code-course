
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, text

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subscriber = Column(Boolean, server_default='FALSE', nullable=False)
    password = Column(String, nullable=False)
    ai_personality = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

