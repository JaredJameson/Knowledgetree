/**
 * KnowledgeTree - Billing Page
 * Subscription management and plan selection with Polish localization
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { subscriptionsApi } from '@/lib/api';
import type {
  SubscriptionDetails,
  PlansResponse,
  SubscriptionPlan,
} from '@/types/subscription';
import { PLAN_LABELS, STATUS_LABELS } from '@/types/subscription';
import {
  Check,
  CreditCard,
  Zap,
  FileText,
  Database,
  ArrowRight,
  Loader2,
  AlertCircle,
  Crown,
  Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export default function BillingPage() {
  const { t } = useTranslation();

  const [subscription, setSubscription] = useState<SubscriptionDetails | null>(null);
  const [plans, setPlans] = useState<PlansResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for success/canceled from checkout
  const urlParams = new URLSearchParams(window.location.search);
  const checkoutSuccess = urlParams.get('success');
  const checkoutCanceled = urlParams.get('canceled');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (checkoutSuccess) {
      // Reload subscription after successful checkout
      loadData();
      // Clear URL params
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [checkoutSuccess]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subResponse, plansResponse] = await Promise.all([
        subscriptionsApi.getMySubscription(),
        subscriptionsApi.getPlans(),
      ]);

      setSubscription(subResponse.data);
      setPlans(plansResponse.data);
    } catch (err: any) {
      console.error('Nie udało się załadować danych rozliczeniowych:', err);
      setError(err.response?.data?.detail || 'Nie udało się załadować informacji o rozliczeniach');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (plan: SubscriptionPlan) => {
    if (DEMO_MODE) {
      setError(t('billing.demoMode.noSubscriptionNeeded', 'Subskrypcja nie jest wymagana w trybie demo'));
      return;
    }

    if (plan === 'free') {
      setError(t('billing.errors.alreadyOnFree', 'Nie można wybrać darmowego planu. Masz już aktywny darmowy plan.'));
      return;
    }

    try {
      setCheckoutLoading(true);
      setError(null);

      const response = await subscriptionsApi.createCheckout({
        plan,
        success_url: `${window.location.origin}/billing?success=true`,
        cancel_url: `${window.location.origin}/billing?canceled=true`,
      });

      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
    } catch (err: any) {
      console.error('Tworzenie płatności nieudane:', err);
      setError(err.response?.data?.detail || 'Nie udało się utworzyć sesji płatności');
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleManageBilling = async () => {
    if (DEMO_MODE) {
      setError(t('billing.demoMode.noSubscriptionNeeded', 'Subskrypcja nie jest wymagana w trybie demo'));
      return;
    }

    try {
      setCheckoutLoading(true);
      setError(null);

      const response = await subscriptionsApi.createBillingPortal({
        return_url: `${window.location.origin}/billing`,
      });

      // Redirect to Stripe Billing Portal
      window.location.href = response.data.portal_url;
    } catch (err: any) {
      console.error('Tworzenie portalu płatności nieudane:', err);
      setError(err.response?.data?.detail || 'Nie udało się otworzyć portalu płatności');
    } finally {
      setCheckoutLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (DEMO_MODE) {
      return;
    }

    if (!confirm(t('billing.confirmCancel'))) {
      return;
    }

    try {
      setCheckoutLoading(true);
      setError(null);

      await subscriptionsApi.cancelSubscription(true);

      // Reload subscription
      await loadData();
    } catch (err: any) {
      console.error('Anulowanie nieudane:', err);
      setError(err.response?.data?.detail || 'Nie udało się anulować subskrypcji');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container max-w-7xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{t('billing.title')}</h1>
        <p className="text-muted-foreground">
          {t('billing.subtitle')}
        </p>
      </div>

      {/* Demo Mode Banner */}
      {DEMO_MODE && (
        <Alert className="mb-6 border-blue-500 bg-blue-50 dark:bg-blue-950">
          <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <AlertDescription className="text-blue-800 dark:text-blue-200">
            <strong>{t('billing.demoMode.title')}</strong> - {t('billing.demoMode.description')}
          </AlertDescription>
        </Alert>
      )}

      {/* Checkout Messages */}
      {checkoutSuccess && (
        <Alert className="mb-6 border-green-500 bg-green-50 dark:bg-green-950">
          <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            {t('billing.checkoutSuccess')}
          </AlertDescription>
        </Alert>
      )}

      {checkoutCanceled && (
        <Alert className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {t('billing.checkoutCanceled')}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="mb-6 border-destructive bg-destructive/10">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <AlertDescription className="text-destructive">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Current Subscription */}
      {subscription && (
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Crown className="h-5 w-5" />
                  {t('billing.currentPlan')}: {PLAN_LABELS[subscription.plan]}
                </CardTitle>
                <CardDescription>
                  {subscription.plan_details.name} - {subscription.plan_details.price === 0
                    ? t('billing.plans.free')
                    : `${subscription.plan_details.price} zł/${subscription.plan_details.interval}`
                  }
                </CardDescription>
              </div>
              <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
                {STATUS_LABELS[subscription.status]}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">{t('billing.documents')}</p>
                  <p className="font-medium">
                    {subscription.plan_details.documents_limit === null
                      ? t('billing.unlimited')
                      : `${subscription.plan_details.documents_limit.toLocaleString()}`
                    }
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">{t('billing.storage')}</p>
                  <p className="font-medium">{subscription.plan_details.storage_gb} GB</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">{t('billing.messages')}</p>
                  <p className="font-medium">
                    {subscription.plan_details.messages_limit === null
                      ? t('billing.unlimited')
                      : `${subscription.plan_details.messages_limit.toLocaleString()}/miesiąc`
                    }
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            {!DEMO_MODE && subscription.plan !== 'free' && (
              <>
                <Button onClick={handleManageBilling} disabled={checkoutLoading} variant="outline">
                  <CreditCard className="h-4 w-4 mr-2" />
                  {t('billing.managePayment')}
                </Button>
                <Button onClick={handleCancelSubscription} disabled={checkoutLoading} variant="destructive">
                  {t('billing.cancelSubscription')}
                </Button>
              </>
            )}
          </CardFooter>
        </Card>
      )}

      {/* Plan Selection - Hide in DEMO mode */}
      {!DEMO_MODE && (
        <>
          <div className="mb-4">
            <h2 className="text-2xl font-bold mb-2">{t('billing.choosePlan')}</h2>
            <p className="text-muted-foreground">
              {t('billing.choosePlanSubtitle')}
            </p>
          </div>

          {plans && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(plans).map(([planKey, plan]) => {
                const isSelected = subscription?.plan === planKey;
                const planType = planKey as SubscriptionPlan;

                return (
                  <Card
                    key={planKey}
                    className={`relative ${
                      isSelected ? 'border-primary border-2' : ''
                    } ${planKey === 'professional' ? 'md:col-span-2' : ''}`}
                  >
                    {planKey === 'professional' && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <Badge className="bg-primary text-primary-foreground">
                          {t('billing.mostPopular')}
                        </Badge>
                      </div>
                    )}

                    <CardHeader>
                      <CardTitle>{plan.name}</CardTitle>
                      <div className="mt-4">
                        <span className="text-4xl font-bold">
                          {plan.price === 0 ? t('billing.plans.free') : `${plan.price} zł`}
                        </span>
                        {plan.price > 0 && (
                          <span className="text-muted-foreground">/{plan.interval}</span>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-3">
                        {plan.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm">
                            <Check className="h-4 w-4 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                    <CardFooter>
                      {isSelected ? (
                        <Button className="w-full" disabled variant="outline">
                          {t('billing.currentPlan')}
                        </Button>
                      ) : (
                        <Button
                          className="w-full"
                          onClick={() => handleSelectPlan(planType)}
                          disabled={checkoutLoading}
                        >
                          {checkoutLoading ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <>
                              {t('billing.selectPlan')}
                              <ArrowRight className="h-4 w-4 ml-2" />
                            </>
                          )}
                        </Button>
                      )}
                    </CardFooter>
                  </Card>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Feature Comparison - Hide in DEMO mode */}
      {!DEMO_MODE && (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>{t('billing.featureComparison')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">Funkcja</th>
                    <th className="text-center py-3 px-4 font-medium">{t('billing.plans.free')}</th>
                    <th className="text-center py-3 px-4 font-medium">{t('billing.plans.starter')}</th>
                    <th className="text-center py-3 px-4 font-medium">{t('billing.plans.professional')}</th>
                    <th className="text-center py-3 px-4 font-medium">{t('billing.plans.enterprise')}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-3 px-4">{t('subscription.features.projects')}</td>
                    <td className="text-center py-3 px-4">3</td>
                    <td className="text-center py-3 px-4">10</td>
                    <td className="text-center py-3 px-4">{t('billing.unlimited')}</td>
                    <td className="text-center py-3 px-4">{t('billing.unlimited')}</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4">{t('subscription.limits.messagesPerMonth')}</td>
                    <td className="text-center py-3 px-4">50</td>
                    <td className="text-center py-3 px-4">500</td>
                    <td className="text-center py-3 px-4">2 000</td>
                    <td className="text-center py-3 px-4">{t('billing.unlimited')}</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4">{t('subscription.limits.storage')}</td>
                    <td className="text-center py-3 px-4">1 GB</td>
                    <td className="text-center py-3 px-4">10 GB</td>
                    <td className="text-center py-3 px-4">50 GB</td>
                    <td className="text-center py-3 px-4">500 GB</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4">{t('subscription.features.documents')}</td>
                    <td className="text-center py-3 px-4">100</td>
                    <td className="text-center py-3 px-4">1 000</td>
                    <td className="text-center py-3 px-4">10 000</td>
                    <td className="text-center py-3 px-4">{t('billing.unlimited')}</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-medium">{t('subscription.plans.free')}</td>
                    <td className="text-center py-3 px-4 font-bold">{t('billing.plans.free')}</td>
                    <td className="text-center py-3 px-4 font-bold">49 zł/miesiąc</td>
                    <td className="text-center py-3 px-4 font-bold">149 zł/miesiąc</td>
                    <td className="text-center py-3 px-4 font-bold">499 zł/miesiąc</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
