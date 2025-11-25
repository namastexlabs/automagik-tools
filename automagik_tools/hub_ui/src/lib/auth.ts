/**
 * Authentication context and user session management.
 * Stores user info after WorkOS AuthKit login.
 */

const USER_STORAGE_KEY = 'hub_user';

export interface UserInfo {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  workspace_id: string;
  workspace_name: string;
  workspace_slug: string;
  is_super_admin: boolean;
  mfa_enabled: boolean;
}

// Get stored user info
export function getUserInfo(): UserInfo | null {
  const stored = localStorage.getItem(USER_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored) as UserInfo;
  } catch {
    return null;
  }
}

// Store user info after login
export function setUserInfo(user: UserInfo): void {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

// Clear user info on logout
export function clearUserInfo(): void {
  localStorage.removeItem(USER_STORAGE_KEY);
}

// Check if current user is super admin
export function isSuperAdmin(): boolean {
  const user = getUserInfo();
  return user?.is_super_admin ?? false;
}

// Get workspace info
export function getWorkspaceInfo(): { id: string; name: string; slug: string } | null {
  const user = getUserInfo();
  if (!user) return null;

  return {
    id: user.workspace_id,
    name: user.workspace_name,
    slug: user.workspace_slug,
  };
}

// Get user display name
export function getUserDisplayName(): string {
  const user = getUserInfo();
  if (!user) return 'User';

  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  if (user.first_name) {
    return user.first_name;
  }
  return user.email.split('@')[0];
}

// Get user initials for avatar
export function getUserInitials(): string {
  const user = getUserInfo();
  if (!user) return '?';

  if (user.first_name && user.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
  }
  if (user.first_name) {
    return user.first_name.substring(0, 2).toUpperCase();
  }
  return user.email.substring(0, 2).toUpperCase();
}
