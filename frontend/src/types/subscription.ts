/**
 * Subscription type definitions
 * Matches backend subscription schemas
 */

export type SubscriptionPlan = 'free' | 'starter' | 'professional' | 'enterprise';

export type SubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'canceled'
  | 'incomplete'
  | 'incomplete_expired'
  | 'past_due'
  | 'paused';

export interface Subscription {
  id: number;
  user_id: number;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  plan: SubscriptionPlan;
  status: SubscriptionStatus;
  cancel_at_period_end: boolean;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at: string | null;
  canceled_at: string | null;
  trial_start: string | null;
  trial_end: string | null;
}

export interface SubscriptionDetails extends Subscription {
  plan_details: PlanDetails;
  // Usage tracking
  messages_sent: number | null;
  storage_used_mb: number | null;
  documents_uploaded: number | null;
}

export interface PlanDetails {
  name: string;
  price: number;
  currency: string;
  interval: string;
  messages_limit: number | null;
  storage_gb: number;
  documents_limit: number | null;
  features: string[];
}

export interface CheckoutRequest {
  plan: SubscriptionPlan;
  success_url?: string;
  cancel_url?: string;
}

export interface CheckoutResponse {
  checkout_url: string;
  subscription_id: number | null;
}

export interface PortalRequest {
  return_url: string;
}

export interface PortalResponse {
  portal_url: string;
}

export interface PlansResponse {
  [key: string]: PlanDetails;
}

// Plan labels for display
export const PLAN_LABELS: Record<SubscriptionPlan, string> = {
  free: 'Free',
  starter: 'Starter',
  professional: 'Professional',
  enterprise: 'Enterprise',
};

// Status labels for display
export const STATUS_LABELS: Record<SubscriptionStatus, string> = {
  trialing: 'Trial',
  active: 'Active',
  canceled: 'Canceled',
  incomplete: 'Incomplete',
  incomplete_expired: 'Expired',
  past_due: 'Past Due',
  paused: 'Paused',
};

// Status colors for badges
export const STATUS_COLORS: Record<SubscriptionStatus, string> = {
  trialing: 'default',
  active: 'default',
  canceled: 'secondary',
  incomplete: 'destructive',
  incomplete_expired: 'destructive',
  past_due: 'destructive',
  paused: 'warning',
};
