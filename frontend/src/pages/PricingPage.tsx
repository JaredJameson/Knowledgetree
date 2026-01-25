/**
 * KnowledgeTree - Pricing Page
 * Plan selection and subscription management with Polish localization
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765';
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

interface Plan {
  name: string;
  price: number;
  currency: string;
  interval: string;
  messages_limit: number | null;
  storage_gb: number;
  documents_limit: number | null;
  features: string[];
}

interface PlansData {
  free: Plan;
  starter: Plan;
  professional: Plan;
  enterprise: Plan;
}

export default function PricingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [plans, setPlans] = useState<PlansData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/v1/subscriptions/plans`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data);
      }
    } catch (error) {
      console.error('Nie udało się pobrać planów:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planKey: string) => {
    // W trybie demo, nie pozwalaj na subskrypcje
    if (DEMO_MODE) {
      navigate('/dashboard');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    if (planKey === 'free') {
      navigate('/dashboard');
      return;
    }

    setCheckoutLoading(true);
    setSelectedPlan(planKey);

    try {
      const response = await fetch(`${API_URL}/api/v1/subscriptions/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan: planKey,
          success_url: `${window.location.origin}/dashboard?checkout=success`,
          cancel_url: `${window.location.origin}/pricing?checkout=canceled`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.checkout_url;
      } else {
        const error = await response.json();
        console.error('Płatność nieudana:', error);
        alert('Nie udało się utworzyć sesji płatności. Spróbuj ponownie.');
      }
    } catch (error) {
      console.error('Błąd płatności:', error);
      alert('Wystąpił błąd. Spróbuj ponownie.');
    } finally {
      setCheckoutLoading(false);
      setSelectedPlan(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">{t('common.loading', 'Ładowanie...')}</p>
        </div>
      </div>
    );
  }

  if (!plans) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">Nie udało się załadować planów. Spróbuj ponownie później.</p>
          <Button onClick={() => navigate('/dashboard')}>
            {t('common.back', 'Powrót')}
          </Button>
        </div>
      </div>
    );
  }

  const plansOrder: (keyof PlansData)[] = ['free', 'starter', 'professional', 'enterprise'];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Demo Mode Banner */}
        {DEMO_MODE && (
          <Alert className="mb-8 border-blue-500 bg-blue-50 dark:bg-blue-950">
            <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <AlertDescription className="text-blue-800 dark:text-blue-200">
              <strong>{t('billing.demoMode.title')}</strong> - {t('billing.demoMode.description')}
            </AlertDescription>
          </Alert>
        )}

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-50 mb-4">
            {t('pricing.title')}
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            {t('pricing.subtitle')}
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {plansOrder.map((planKey) => {
            const plan = plans[planKey];
            const isPopular = planKey === 'starter';

            return (
              <Card
                key={planKey}
                className={`relative overflow-hidden ${
                  isPopular ? 'ring-2 ring-blue-600 transform scale-105' : ''
                }`}
              >
                {isPopular && (
                  <div className="absolute top-0 left-0 right-0 bg-blue-600 text-white text-center py-2 text-sm font-semibold">
                    {t('pricing.mostPopular')}
                  </div>
                )}

                <CardHeader className={isPopular ? 'pt-12' : ''}>
                  <CardTitle>{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-gray-900 dark:text-gray-50">
                      {plan.price === 0 ? t('billing.plans.free') : `${plan.price} zł`}
                    </span>
                    {plan.price > 0 && (
                      <span className="text-gray-600 dark:text-gray-400">{t('pricing.perMonth')}</span>
                    )}
                  </div>
                </CardHeader>

                <CardContent>
                  <ul className="space-y-3">
                    <li className="flex items-start">
                      <Check className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700 dark:text-gray-300">
                        {plan.messages_limit === null
                          ? t('pricing.features.unlimitedMessages')
                          : `${plan.messages_limit.toLocaleString()} ${t('subscription.limits.messagesPerMonth')}`
                        }
                      </span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700 dark:text-gray-300">
                        {plan.storage_gb}{t('pricing.features.storage')}
                      </span>
                    </li>
                    <li className="flex items-start">
                      <Check className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700 dark:text-gray-300">
                        {plan.documents_limit === null
                          ? t('pricing.features.unlimitedDocuments')
                          : `${plan.documents_limit.toLocaleString()} ${t('pricing.features.documents')}`
                        }
                      </span>
                    </li>

                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <Check className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>

                <CardFooter>
                  <Button
                    onClick={() => handleSubscribe(planKey)}
                    disabled={checkoutLoading && selectedPlan === planKey}
                    className={`w-full ${
                      isPopular
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-50'
                    }`}
                  >
                    {checkoutLoading && selectedPlan === planKey ? (
                      <span className="flex items-center justify-center">
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                        {t('common.loading', 'Ładowanie...')}
                      </span>
                    ) : planKey === 'free' || DEMO_MODE ? (
                      t('pricing.getStarted')
                    ) : (
                      t('pricing.subscribe')
                    )}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* FAQ Section */}
        <Card className="mt-16 max-w-3xl mx-auto">
          <CardHeader>
            <CardTitle className="text-center">{t('pricing.faq.title')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
                {t('pricing.faq.changePlan.question')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {t('pricing.faq.changePlan.answer')}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
                {t('pricing.faq.freeTrial.question')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {t('pricing.faq.freeTrial.answer')}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
                {t('pricing.faq.paymentMethods.question')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {t('pricing.faq.paymentMethods.answer')}
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-50 mb-2">
                {t('pricing.faq.cancelAnytime.question')}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {t('pricing.faq.cancelAnytime.answer')}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Contact Section */}
        {!DEMO_MODE && (
          <div className="mt-16 text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {t('pricing.contact.needCustom')}
            </p>
            <Button
              onClick={() => navigate('/contact')}
              className="bg-gray-900 text-white hover:bg-gray-800"
            >
              {t('pricing.contact.contactSales')}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
