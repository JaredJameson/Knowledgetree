/**
 * KnowledgeTree Register Page
 * User registration with email, password, and full name
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/context/AuthContext';
import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeToggle } from '@/components/theme-toggle';
import { useTheme } from '@/components/theme-provider';

export function RegisterPage() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const { theme } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(email, password, fullName || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('auth.register.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <img
              src={theme === 'dark' ? '/logo_biale.png' : '/logo_czarne.png'}
              alt="KnowledgeTree Logo"
              className="h-12 w-auto object-contain"
            />
            <div>
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
                {t('app.name')}
              </h1>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {t('auth.register.subtitle')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </div>

        {/* Register Card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('auth.register.title')}</CardTitle>
            <CardDescription>{t('auth.register.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="p-3 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-error-700 dark:text-error-400 text-sm">
                  {error}
                </div>
              )}

              {/* Full Name */}
              <div className="space-y-2">
                <label htmlFor="fullName" className="text-sm font-medium">
                  {t('auth.register.fullName')}
                </label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder={t('auth.register.fullNamePlaceholder')}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  {t('auth.register.email')}
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder={t('auth.register.emailPlaceholder')}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  {t('auth.register.password')}
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={loading}
                />
                <p className="text-xs text-neutral-500 dark:text-neutral-600">
                  {t('auth.register.passwordHint')}
                </p>
              </div>

              {/* Submit Button */}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? t('auth.register.registering') : t('auth.register.submit')}
              </Button>

              {/* Login Link */}
              <div className="text-center text-sm">
                <span className="text-neutral-600 dark:text-neutral-400">
                  {t('auth.register.hasAccount')}{' '}
                </span>
                <Link
                  to="/login"
                  className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
                >
                  {t('auth.register.loginLink')}
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-neutral-500 dark:text-neutral-600 mt-8">
          {t('auth.footer')}
        </p>
      </div>
    </div>
  );
}
