# Usage tracking model for subscription limits
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Usage(Base):
    """Usage tracking model for subscription plan limits."""

    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Metric type: messages_sent, tokens_used, documents_uploaded, storage_used_mb
    metric = Column(String, nullable=False, index=True)

    # Current usage value
    value = Column(Integer, nullable=False, default=0)

    # Period: daily, monthly, yearly
    period = Column(String, nullable=False, default="monthly")

    # Period boundaries
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False)

    # Relationships
    user = relationship("User", back_populates="usage_records")

    def __repr__(self):
        return f"<Usage(user_id={self.user_id}, metric={self.metric}, value={self.value}, period={self.period})>"
