"""
KnowledgeTree Backend - Subscription Schemas
Pydantic schemas for subscription operations
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Subscription status matching Stripe"""
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    PAUSED = "paused"


class SubscriptionPlan(str, Enum):
    """Available subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Plan details for frontend
PLAN_DETAILS = {
    SubscriptionPlan.FREE: {
        "name": "Free",
        "price": 0,
        "currency": "USD",
        "interval": "month",
        "messages_limit": 50,
        "storage_gb": 1,
        "documents_limit": 100,
        "projects_limit": 3,
        "features": [
            "3 projects",
            "50 messages/month",
            "1 GB storage",
            "100 documents",
            "GPT-4o-mini model only",
            "Basic semantic search",
            "RAG chat",
            "PDF upload",
        ]
    },
    SubscriptionPlan.STARTER: {
        "name": "Starter",
        "price": 49,
        "currency": "USD",
        "interval": "month",
        "messages_limit": 1000,  # Increased from 500 for better value
        "storage_gb": 10,
        "documents_limit": 1000,
        "projects_limit": 10,
        "features": [
            "10 projects",
            "1,000 messages/month",
            "10 GB storage",
            "1,000 documents",
            "GPT-4o-mini model",
            "Advanced semantic search",
            "RAG chat",
            "Artifact generation",
            "Export (JSON, Markdown, CSV)",
            "Web crawling (100 pages/mo)",
        ]
    },
    SubscriptionPlan.PROFESSIONAL: {
        "name": "Professional",
        "price": 149,
        "currency": "USD",
        "interval": "month",
        "messages_limit": 5000,  # Increased from 2,000 for better value
        "storage_gb": 100,  # Increased from 50GB
        "documents_limit": 10000,
        "features": [
            "Unlimited projects",
            "5,000 messages/month",
            "100 GB storage",
            "10,000 documents",
            "Both LLM models (GPT-4o-mini + Claude)",
            "Advanced semantic search",
            "RAG chat with streaming",
            "All artifact types",
            "Export (JSON, Markdown, CSV)",
            "API access",
            "Web crawling (500 pages/mo)",
        ]
    },
    SubscriptionPlan.ENTERPRISE: {
        "name": "Enterprise",
        "price": 499,
        "currency": "USD",
        "interval": "month",
        "messages_limit": 20000,  # 20,000 messages/month
        "storage_gb": 1000,  # 1 TB storage
        "documents_limit": None,  # unlimited
        "features": [
            "Everything in Professional",
            "20,000 messages/month",
            "1 TB storage",
            "Unlimited documents",
            "Both LLM models (GPT-4o-mini + Claude)",
            "Priority API queue",
            "Web crawling (2,000 pages/mo)",
            "AI insights & workflows",
            "Email support (<24h response)",
        ]
    },
}


class SubscriptionResponse(BaseModel):
    """Subscription response model"""
    id: int
    user_id: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    plan: SubscriptionPlan
    status: SubscriptionStatus
    cancel_at_period_end: bool = False
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionDetailsResponse(SubscriptionResponse):
    """Extended subscription response with plan details"""
    plan_details: dict = Field(description="Plan pricing and features")
    is_demo: bool = Field(default=False, description="Whether this is a demo mode subscription")

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    """Create checkout session request"""
    plan: SubscriptionPlan = Field(..., description="Plan to subscribe to")
    success_url: Optional[str] = Field(None, description="URL to redirect on success")
    cancel_url: Optional[str] = Field(None, description="URL to redirect on cancel")


class CheckoutResponse(BaseModel):
    """Checkout session response"""
    checkout_url: str = Field(..., description="Stripe Checkout URL")
    subscription_id: Optional[int] = Field(None, description="Subscription ID if exists")


class PortalRequest(BaseModel):
    """Create billing portal session request"""
    return_url: str = Field(..., description="URL to redirect after portal")


class PortalResponse(BaseModel):
    """Billing portal session response"""
    portal_url: str = Field(..., description="Stripe Billing Portal URL")


class WebhookEvent(BaseModel):
    """Stripe webhook event"""
    id: str
    object: str = "event"
    api_version: str
    created: int
    data: dict
    type: str
