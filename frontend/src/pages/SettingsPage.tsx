/**
 * KnowledgeTree - Settings Page
 * User settings and preferences management
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import {
  User as UserIcon,
  Shield,
  Bell,
  Palette,
  Save,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();

  const [saving, setSaving] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState('pl');

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      // In a real app, this would call an update profile API
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success(t('settings.profileSaved', 'Profile saved successfully'));
      await refreshUser();
    } catch (err) {
      toast.error(t('settings.saveFailed', 'Failed to save profile'));
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = () => {
    // Navigate to password change page or show modal
    toast.info(t('settings.passwordChange', 'Password change feature coming soon'));
  };

  const handleDeleteAccount = async () => {
    if (
      !confirm(
        t(
          'settings.confirmDelete',
          'Are you sure you want to delete your account? This action cannot be undone.'
        )
      )
    ) {
      return;
    }

    toast.info(t('settings.deleteAccount', 'Account deletion feature coming soon'));
  };

  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{t('settings.title', 'Settings')}</h1>
        <p className="text-muted-foreground">
          {t('settings.subtitle', 'Manage your account settings and preferences')}
        </p>
      </div>

      {/* Profile Settings */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <UserIcon className="h-5 w-5" />
            <CardTitle>{t('settings.profile', 'Profile')}</CardTitle>
          </div>
          <CardDescription>
            {t('settings.profileDescription', 'Update your personal information')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">{t('settings.fullName', 'Full Name')}</Label>
            <Input
              id="fullName"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder={t('settings.fullNamePlaceholder', 'Enter your full name')}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">{t('settings.email', 'Email')}</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled
            />
            <p className="text-xs text-muted-foreground">
              {t('settings.emailReadOnly', 'Email cannot be changed')}
            </p>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSaveProfile} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {t('settings.saving', 'Saving...')}
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  {t('settings.save', 'Save Changes')}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            <CardTitle>{t('settings.security', 'Security')}</CardTitle>
          </div>
          <CardDescription>
            {t('settings.securityDescription', 'Manage your password and security settings')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={handleChangePassword} variant="outline">
            {t('settings.changePassword', 'Change Password')}
          </Button>
        </CardContent>
      </Card>

      {/* Preferences */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            <CardTitle>{t('settings.preferences', 'Preferences')}</CardTitle>
          </div>
          <CardDescription>
            {t('settings.preferencesDescription', 'Customize your application experience')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="notifications">
                {t('settings.notifications', 'Email Notifications')}
              </Label>
              <p className="text-sm text-muted-foreground">
                {t('settings.notificationsDescription', 'Receive updates about your projects')}
              </p>
            </div>
            <Switch
              id="notifications"
              checked={notifications}
              onCheckedChange={setNotifications}
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="language">{t('settings.language', 'Language')}</Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger id="language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pl">Polski</SelectItem>
                <SelectItem value="en">English</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Link */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            <CardTitle>{t('settings.subscription', 'Subscription')}</CardTitle>
          </div>
          <CardDescription>
            {t('settings.subscriptionDescription', 'Manage your subscription and billing')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => navigate('/billing')} variant="outline">
            {t('settings.manageSubscription', 'Manage Subscription')}
          </Button>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">
            {t('settings.dangerZone', 'Danger Zone')}
          </CardTitle>
          <CardDescription>
            {t('settings.dangerZoneDescription', 'Irreversible actions')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleDeleteAccount} variant="destructive">
            {t('settings.deleteAccount', 'Delete Account')}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
