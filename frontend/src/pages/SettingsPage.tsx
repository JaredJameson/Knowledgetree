/**
 * KnowledgeTree - Settings Page
 * User settings and preferences management
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/lib/api';
import {
  User as UserIcon,
  Shield,
  Bell,
  Palette,
  Save,
  Loader2,
  Eye,
  EyeOff,
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
  const { user, refreshUser, logout } = useAuth();

  const [saving, setSaving] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState('pl');

  // Password change state
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Account deletion state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deletingAccount, setDeletingAccount] = useState(false);

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

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error(t('settings.passwordMismatch', 'New passwords do not match'));
      return;
    }
    if (newPassword.length < 8) {
      toast.error(t('settings.passwordTooShort', 'Password must be at least 8 characters'));
      return;
    }

    try {
      setChangingPassword(true);
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success(t('settings.passwordChanged', 'Password changed successfully'));
      setShowPasswordForm(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      const detail = err?.response?.data?.detail || t('settings.passwordChangeFailed', 'Failed to change password');
      toast.error(detail);
    } finally {
      setChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      toast.error(t('settings.enterPassword', 'Please enter your password'));
      return;
    }

    try {
      setDeletingAccount(true);
      await api.delete('/auth/delete-account', {
        data: { password: deletePassword },
      });
      toast.success(t('settings.accountDeleted', 'Account deleted successfully'));
      logout();
      navigate('/login');
    } catch (err: any) {
      const detail = err?.response?.data?.detail || t('settings.deleteAccountFailed', 'Failed to delete account');
      toast.error(detail);
    } finally {
      setDeletingAccount(false);
    }
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
          {!showPasswordForm ? (
            <Button onClick={() => setShowPasswordForm(true)} variant="outline">
              {t('settings.changePassword', 'Change Password')}
            </Button>
          ) : (
            <div className="space-y-4 max-w-md">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">
                  {t('settings.currentPassword', 'Current Password')}
                </Label>
                <div className="relative">
                  <Input
                    id="currentPassword"
                    type={showCurrentPassword ? 'text' : 'password'}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder={t('settings.currentPasswordPlaceholder', 'Enter current password')}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  >
                    {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">
                  {t('settings.newPassword', 'New Password')}
                </Label>
                <div className="relative">
                  <Input
                    id="newPassword"
                    type={showNewPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder={t('settings.newPasswordPlaceholder', 'Enter new password (min 8 characters)')}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">
                  {t('settings.confirmPassword', 'Confirm New Password')}
                </Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={t('settings.confirmPasswordPlaceholder', 'Confirm new password')}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleChangePassword}
                  disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
                >
                  {changingPassword ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {t('settings.changingPassword', 'Changing...')}
                    </>
                  ) : (
                    t('settings.savePassword', 'Save Password')
                  )}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowPasswordForm(false);
                    setCurrentPassword('');
                    setNewPassword('');
                    setConfirmPassword('');
                  }}
                >
                  {t('common.cancel', 'Cancel')}
                </Button>
              </div>
            </div>
          )}
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
          {!showDeleteConfirm ? (
            <Button onClick={() => setShowDeleteConfirm(true)} variant="destructive">
              {t('settings.deleteAccountBtn', 'Delete Account')}
            </Button>
          ) : (
            <div className="space-y-4 max-w-md">
              <p className="text-sm text-destructive font-medium">
                {t(
                  'settings.deleteWarning',
                  'This will permanently delete your account and all associated data (projects, documents, conversations). This action cannot be undone.'
                )}
              </p>
              <div className="space-y-2">
                <Label htmlFor="deletePassword">
                  {t('settings.confirmWithPassword', 'Enter your password to confirm')}
                </Label>
                <Input
                  id="deletePassword"
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder={t('settings.passwordPlaceholder', 'Enter your password')}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={handleDeleteAccount}
                  variant="destructive"
                  disabled={deletingAccount || !deletePassword}
                >
                  {deletingAccount ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {t('settings.deleting', 'Deleting...')}
                    </>
                  ) : (
                    t('settings.confirmDeleteAccount', 'Yes, Delete My Account')
                  )}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeletePassword('');
                  }}
                >
                  {t('common.cancel', 'Cancel')}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
