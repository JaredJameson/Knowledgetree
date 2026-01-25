"""
KnowledgeTree Backend - Stripe Service
Stripe payment integration for subscriptions
"""

import logging
import os
from typing import Optional, Dict
from datetime import datetime

import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.user import User
from models.subscription import Subscription, SubscriptionStatus, SubscriptionPlan
from schemas.subscription import PLAN_DETAILS

logger = logging.getLogger(__name__)


class StripeService:
    """
    Stripe payment service for subscription management

    Features:
    - Create checkout sessions for new subscriptions
    - Manage existing subscriptions (upgrade/downgrade/cancel)
    - Handle Stripe webhooks
    - Create billing portal sessions
    """

    # Stripe price IDs (configured in Stripe Dashboard)
    PRICE_IDS = {
        SubscriptionPlan.STARTER: os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
        SubscriptionPlan.PROFESSIONAL: os.getenv("STRIPE_PRICE_PROFESSIONAL", "price_professional"),
        SubscriptionPlan.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise"),
    }

    def __init__(self):
        """Initialize Stripe client"""
        stripe.api_key = settings.STRIPE_API_KEY

    async def get_or_create_subscription(
        self,
        db: AsyncSession,
        user: User
    ) -> Subscription:
        """
        Get existing subscription or create new free subscription

        Args:
            db: Database session
            user: User object

        Returns:
            Subscription object
        """
        # Check if user has subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()

        # Create free subscription if none exists
        if not subscription:
            subscription = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.FREE.value,
                status=SubscriptionStatus.ACTIVE.value,
            )
            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)
            logger.info(f"Created free subscription for user {user.id}")

        return subscription

    async def create_checkout_session(
        self,
        db: AsyncSession,
        user: User,
        plan: SubscriptionPlan,
        success_url: str = None,
        cancel_url: str = None
    ) -> tuple[str, Optional[int]]:
        """
        Create Stripe Checkout session for subscription

        Args:
            db: Database session
            user: User to create subscription for
            plan: Plan to subscribe to
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel

        Returns:
            Tuple of (checkout URL, subscription ID)
        """
        # Validate plan
        if plan == SubscriptionPlan.FREE:
            raise ValueError("Cannot create checkout session for free plan")

        # Get or create subscription
        subscription = await self.get_or_create_subscription(db, user)

        # Get price ID for plan
        price_id = self.PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"No price ID configured for plan: {plan.value}")

        # Create Stripe customer if not exists
        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name or user.email,
                metadata={"user_id": str(user.id)}
            )
            subscription.stripe_customer_id = customer.id
            await db.commit()

        # Default URLs
        if not success_url:
            success_url = f"{settings.FRONTEND_URL}/billing?success=true"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL}/billing?canceled=true"

        # Create checkout session
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "subscription_id": str(subscription.id),
                    "plan": plan.value,
                },
                subscription_data={
                    "metadata": {
                        "user_id": str(user.id),
                        "plan": plan.value,
                    }
                }
            )

            logger.info(f"Created checkout session for user {user.id}: {checkout_session.id}")
            return checkout_session.url, subscription.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {str(e)}")
            raise Exception(f"Failed to create checkout session: {str(e)}")

    async def create_billing_portal_session(
        self,
        db: AsyncSession,
        user: User,
        return_url: str
    ) -> str:
        """
        Create Stripe Billing Portal session

        Allows users to manage subscription (cancel, update payment method, etc.)

        Args:
            db: Database session
            user: User
            return_url: URL to redirect after portal

        Returns:
            Billing portal URL
        """
        subscription = await self.get_or_create_subscription(db, user)

        if not subscription.stripe_customer_id:
            raise ValueError("No Stripe customer found. Please create a subscription first.")

        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=subscription.stripe_customer_id,
                return_url=return_url,
            )

            logger.info(f"Created billing portal session for user {user.id}")
            return portal_session.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe billing portal session creation failed: {str(e)}")
            raise Exception(f"Failed to create billing portal session: {str(e)}")

    async def handle_webhook(
        self,
        db: AsyncSession,
        event_type: str,
        event_data: dict
    ) -> None:
        """
        Handle Stripe webhook events

        Supported events:
        - checkout.session.completed: New subscription created
        - customer.subscription.updated: Subscription changed
        - customer.subscription.deleted: Subscription canceled
        - invoice.paid: Payment succeeded

        Args:
            db: Database session
            event_type: Stripe event type
            event_data: Event data payload
        """
        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(db, event_data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(db, event_data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(db, event_data)
        elif event_type == "invoice.paid":
            await self._handle_invoice_paid(db, event_data)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")

    async def _handle_checkout_completed(
        self,
        db: AsyncSession,
        event_data: dict
    ) -> None:
        """Handle checkout.session.completed event"""
        session = event_data.get("data", {}).get("object", {})
        subscription_data = session.get("subscription", {})
        customer_id = session.get("customer")
        metadata = session.get("metadata", {})

        user_id = int(metadata.get("user_id", 0))
        if not user_id:
            logger.error("No user_id in checkout session metadata")
            return

        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.error(f"No subscription found for user {user_id}")
            return

        # Update subscription
        subscription.stripe_subscription_id = subscription_data.get("id")
        subscription.stripe_customer_id = customer_id
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.plan = metadata.get("plan", SubscriptionPlan.STARTER.value)

        # Set period dates
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start")
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end")
        )

        await db.commit()
        logger.info(f"Updated subscription {subscription.id} from checkout completion")

    async def _handle_subscription_updated(
        self,
        db: AsyncSession,
        event_data: dict
    ) -> None:
        """Handle customer.subscription.updated event"""
        stripe_subscription = event_data.get("data", {}).get("object", {})
        stripe_sub_id = stripe_subscription.get("id")

        # Find subscription by Stripe ID
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.warning(f"No subscription found for Stripe ID: {stripe_sub_id}")
            return

        # Update status
        subscription.status = stripe_subscription.get("status")
        subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)

        # Update period dates
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.get("current_period_start")
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.get("current_period_end")
        )

        # Update cancellation info
        if stripe_subscription.get("cancel_at"):
            subscription.cancel_at = datetime.fromtimestamp(
                stripe_subscription.get("cancel_at")
            )

        await db.commit()
        logger.info(f"Updated subscription {subscription.id} from Stripe webhook")

    async def _handle_subscription_deleted(
        self,
        db: AsyncSession,
        event_data: dict
    ) -> None:
        """Handle customer.subscription.deleted event"""
        stripe_subscription = event_data.get("data", {}).get("object", {})
        stripe_sub_id = stripe_subscription.get("id")

        # Find subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.warning(f"No subscription found for Stripe ID: {stripe_sub_id}")
            return

        # Update to canceled
        subscription.status = SubscriptionStatus.CANCELED.value
        subscription.canceled_at = datetime.fromtimestamp(
            stripe_subscription.get("canceled_at")
        )

        # Downgrade to free plan
        subscription.plan = SubscriptionPlan.FREE.value

        await db.commit()
        logger.info(f"Canceled subscription {subscription.id} from Stripe webhook")

    async def _handle_invoice_paid(
        self,
        db: AsyncSession,
        event_data: dict
    ) -> None:
        """Handle invoice.paid event"""
        invoice = event_data.get("data", {}).get("object", {})
        subscription_id = invoice.get("subscription")

        if not subscription_id:
            return

        # Find subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return

        # Reactivate if was past due
        if subscription.status == SubscriptionStatus.PAST_DUE.value:
            subscription.status = SubscriptionStatus.ACTIVE.value
            await db.commit()
            logger.info(f"Reactivated subscription {subscription.id} from invoice payment")

    async def cancel_subscription(
        self,
        db: AsyncSession,
        user: User,
        at_period_end: bool = True
    ) -> Subscription:
        """
        Cancel user's subscription

        Args:
            db: Database session
            user: User
            at_period_end: If True, cancel at period end; if False, cancel immediately

        Returns:
            Updated subscription
        """
        subscription = await self.get_or_create_subscription(db, user)

        if not subscription.stripe_subscription_id:
            raise ValueError("No Stripe subscription to cancel")

        try:
            if at_period_end:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
            else:
                # Cancel immediately
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED.value
                subscription.canceled_at = datetime.utcnow()
                subscription.plan = SubscriptionPlan.FREE.value

            await db.commit()
            logger.info(f"Canceled subscription {subscription.id} for user {user.id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")


# Global instance
stripe_service = StripeService()
