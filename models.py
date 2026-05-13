from sqlalchemy import Column, Integer, String
from database import Base

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    branch_name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)