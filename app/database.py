from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(String, primary_key=True)
    contact_id = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    stage = Column(Integer, default=0)        # 0=initial sent, 1-4=follow-up index
    status = Column(String, default="active") # active | booked | enrolled | unresponsive
    last_contact = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def close(self):
        self.engine.dispose()

    def _session(self) -> Session:
        return self.SessionLocal()

    def create_lead(
        self,
        lead_id: str,
        contact_id: str,
        first_name: str,
        phone: str,
        email: str,
    ) -> Lead:
        with self._session() as session:
            lead = Lead(
                lead_id=lead_id,
                contact_id=contact_id,
                first_name=first_name,
                phone=phone,
                email=email,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            session.expunge(lead)
            return lead

    def create_lead_if_not_exists(
        self,
        lead_id: str,
        contact_id: str,
        first_name: str,
        phone: str,
        email: str,
    ) -> Optional[Lead]:
        with self._session() as session:
            existing = session.get(Lead, lead_id)
            if existing:
                return None
            lead = Lead(
                lead_id=lead_id,
                contact_id=contact_id,
                first_name=first_name,
                phone=phone,
                email=email,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            session.expunge(lead)
            return lead

    def get_lead(self, lead_id: str) -> Optional[Lead]:
        with self._session() as session:
            lead = session.get(Lead, lead_id)
            if lead:
                session.expunge(lead)
            return lead

    def get_lead_by_contact_id(self, contact_id: str) -> Optional[Lead]:
        with self._session() as session:
            lead = session.query(Lead).filter(Lead.contact_id == contact_id).first()
            if lead:
                session.expunge(lead)
            return lead

    def update_lead(self, lead_id: str, **kwargs) -> None:
        with self._session() as session:
            lead = session.get(Lead, lead_id)
            if lead:
                for key, value in kwargs.items():
                    setattr(lead, key, value)
                session.commit()
