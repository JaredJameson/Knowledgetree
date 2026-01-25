"""
KnowledgeTree Backend - Subscription Routes
Stripe payment and subscription management endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe

from core.database import get_db
from core.config import settings
from api.dependencies import get_current_active_user
from models.user import User
from models.subscription import Subscription, SubscriptionPlan
from schemas.subscription import (
    SubscriptionResponse,
    SubscriptionDetailsResponse,
    CheckoutRequest,
    CheckoutResponse,
    PortalRequest,
    PortalResponse,
    PLAN_DETAILS,
)

from services.stripe_service import stripe_service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
logger = logging.getLogger(__name__)


@router.get("/my-subscription", response_model=SubscriptionDetailsResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription with plan details

    In DEMO_MODE, returns unlimited enterprise plan regardless of actual subscription
    """
    # Demo mode: Return unlimited enterprise plan
    if settings.DEMO_MODE:
        from schemas.subscription import PLAN_DETAILS, SubscriptionPlan
        plan = SubscriptionPlan.ENTERPRISE
        plan_details = PLAN_DETAILS.get(plan, {}).copy()

        # Override with enterprise plan values (DEMO_MODE)
        plan_details.update({
            "documents_limit": None,  # Unlimited
            "messages_limit": 20000,  # 20K messages/month
            "storage_gb": 500,  # 500 GB (not 10000 - that was a bug!)
            "projects_limit": None,  # Unlimited
        })

        return SubscriptionDetailsResponse(
            id=0,
            user_id=current_user.id,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            plan="enterprise",
            status="active",
            cancel_at_period_end=False,
            current_period_start=None,
            current_period_end=None,
            cancel_at=None,
            canceled_at=None,
            trial_start=None,
            trial_end=None,
            plan_details=plan_details,
            is_demo=True
        )

    subscription = await stripe_service.get_or_create_subscription(db, current_user)

    # Add plan details
    plan = SubscriptionPlan(subscription.plan)
    plan_details = PLAN_DETAILS.get(plan, {})

    return SubscriptionDetailsResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        stripe_customer_id=subscription.stripe_customer_id,
        stripe_subscription_id=subscription.stripe_subscription_id,
        plan=subscription.plan,
        status=subscription.status,
        cancel_at_period_end=subscription.cancel_at_period_end,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at=subscription.cancel_at,
        canceled_at=subscription.canceled_at,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
        plan_details=plan_details
    )


@router.get("/plans", response_model=dict)
async def get_available_plans():
    """
    Get all available subscription plans with pricing and features
    """
    from schemas.subscription import PLAN_DETAILS, SubscriptionPlan

    return {
        plan.value: PLAN_DETAILS[plan]
        for plan in [
            SubscriptionPlan.FREE,
            SubscriptionPlan.STARTER,
            SubscriptionPlan.PROFESSIONAL,
            SubscriptionPlan.ENTERPRISE,
        ]
    }


@router.get("/config")
async def get_config():
    """
    Get public configuration (demo mode, feature flags, etc.)

    This endpoint doesn't require authentication and provides
    information about the current system configuration.
    """
    return {
        "demo_mode": settings.DEMO_MODE,
        "environment": settings.ENVIRONMENT,
        "features": {
            "web_crawling": settings.ENABLE_WEB_CRAWLING,
            "ai_insights": settings.ENABLE_AI_INSIGHTS,
            "agentic_workflows": settings.ENABLE_AGENTIC_WORKFLOWS,
        }
    }


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe Checkout session for new subscription

    Returns a Stripe Checkout URL that the user should be redirected to
    to complete the payment process.

    In DEMO_MODE, returns an error since payments are not needed.
    """
    if settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Płatności nie są wymagane w trybie demonstracyjnym. Wszystkie funkcje są dostępne bez ograniczeń."
        )

    try:
        checkout_url, subscription_id = await stripe_service.create_checkout_session(
            db=db,
            user=current_user,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )

        return CheckoutResponse(
            checkout_url=checkout_url,
            subscription_id=subscription_id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout session creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/billing-portal", response_model=PortalResponse)
async def create_billing_portal_session(
    request: PortalRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create Stripe Billing Portal session

    Returns a URL to the Stripe Billing Portal where users can:
    - View payment history
    - Update payment methods
    - Cancel subscription
    - Change plan

    In DEMO_MODE, returns an error since payments are not needed.
    """
    if settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portal płatności nie jest dostępny w trybie demonstracyjnym."
        )

    try:
        portal_url = await stripe_service.create_billing_portal_session(
            db=db,
            user=current_user,
            return_url=request.return_url
        )

        return PortalResponse(portal_url=portal_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Billing portal session creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create billing portal session: {str(e)}"
        )


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel user's subscription

    Args:
        at_period_end: If True, cancel at period end (default). If False, cancel immediately.

    Returns:
        Updated subscription
    """
    try:
        subscription = await stripe_service.cancel_subscription(
            db=db,
            user=current_user,
            at_period_end=at_period_end
        )

        return SubscriptionResponse.model_validate(subscription)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events

    Supported events:
    - checkout.session.completed: New subscription created
    - customer.subscription.updated: Subscription changed
    - customer.subscription.deleted: Subscription canceled
    - invoice.paid: Payment succeeded
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe signature found"
        )

    # Read request body
    payload = await request.body()
    event = None

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}"
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signature: {str(e)}"
        )

    # Handle event
    try:
        await stripe_service.handle_webhook(
            db=db,
            event_type=event.type,
            event_data=event.data.object
        )

        logger.info(f"Processed webhook event: {event.type}")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        # Still return 200 to avoid retry loops
        return {"status": "error", "message": str(e)}
