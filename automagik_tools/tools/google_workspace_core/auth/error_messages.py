"""
Enhanced error messages with actionable user guidance for OAuth authentication.

Provides structured, user-friendly error messages that help users quickly
resolve authentication issues without needing to understand technical details.
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ErrorType(Enum):
    """Categories of authentication errors"""

    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"
    INSUFFICIENT_SCOPES = "insufficient_scopes"
    CLIENT_NOT_CONFIGURED = "client_not_configured"
    SESSION_ALREADY_BOUND = "session_already_bound"
    INVALID_STATE = "invalid_state"
    CALLBACK_TIMEOUT = "callback_timeout"
    NETWORK_ERROR = "network_error"
    GENERIC_AUTH_ERROR = "generic_auth_error"


@dataclass
class AuthErrorGuidance:
    """
    Structured error message with actionable guidance.

    Provides consistent, helpful error messages across all OAuth operations.
    """

    error_type: ErrorType
    title: str
    message: str
    user_action: str
    technical_details: Optional[str] = None
    help_url: Optional[str] = None
    code_example: Optional[str] = None

    def format(self, include_technical: bool = False, use_emojis: bool = True) -> str:
        """
        Format as user-friendly message.

        Args:
            include_technical: Include technical details section
            use_emojis: Use emojis for better visual hierarchy

        Returns:
            Formatted error message
        """
        emoji_prefix = "🔐 " if use_emojis else ""
        action_prefix = "✅ " if use_emojis else "→ "
        tech_prefix = "🔧 " if use_emojis else "Technical: "
        doc_prefix = "📚 " if use_emojis else "Docs: "
        code_prefix = "💡 " if use_emojis else "Example: "

        lines = [
            f"{emoji_prefix}Authentication Error: {self.title}",
            "",
            self.message,
            "",
            f"{action_prefix}Action Required:",
        ]

        # Add indented action steps
        for line in self.user_action.split("\n"):
            lines.append(f"   {line}")

        # Add code example if provided
        if self.code_example:
            lines.extend(["", f"{code_prefix}Example:", ""])
            for line in self.code_example.split("\n"):
                lines.append(f"   {line}")

        # Add technical details if requested
        if include_technical and self.technical_details:
            lines.extend(["", f"{tech_prefix}Technical Details:", f"   {self.technical_details}"])

        # Add documentation link
        if self.help_url:
            lines.extend(["", f"{doc_prefix}Documentation: {self.help_url}"])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "error_type": self.error_type.value,
            "title": self.title,
            "message": self.message,
            "user_action": self.user_action,
            "technical_details": self.technical_details,
            "help_url": self.help_url,
            "code_example": self.code_example,
        }


class AuthErrorMessages:
    """
    Centralized error message templates with guidance.

    Provides consistent, actionable error messages for all OAuth scenarios.
    """

    BASE_DOCS_URL = "https://github.com/namastexlabs/automagik-tools/blob/main/docs"

    @staticmethod
    def token_expired(user_email: str, service_name: str) -> AuthErrorGuidance:
        """Error message for expired tokens"""
        return AuthErrorGuidance(
            error_type=ErrorType.TOKEN_EXPIRED,
            title="Token Expired",
            message=f"Your authentication token for {service_name} has expired. This is normal and happens after a period of time for security reasons.",
            user_action=(
                f"Please reauthenticate to continue:\n"
                f"\n"
                f"Call start_google_auth with your email and service name:\n"
                f'  user_email: "{user_email}"\n'
                f'  service_name: "{service_name}"\n'
                f"\n"
                f"Then follow the browser link to grant permissions."
            ),
            code_example=(
                f"# Reauthenticate\n"
                f"start_google_auth(\n"
                f'    user_google_email="{user_email}",\n'
                f'    service_name="{service_name}"\n'
                f")"
            ),
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#token-expired",
        )

    @staticmethod
    def token_revoked(user_email: str, service_name: str, reason: Optional[str] = None) -> AuthErrorGuidance:
        """Error message for revoked tokens"""
        reasons = [
            "You changed your Google account password",
            "You manually revoked access in your Google Account settings",
            "The app's credentials were reset",
            "Security concerns detected by Google",
        ]

        reason_text = f"Common reasons:\n" + "\n".join(f"  • {r}" for r in reasons)

        if reason:
            reason_text = f"Reason: {reason}\n\n" + reason_text

        return AuthErrorGuidance(
            error_type=ErrorType.TOKEN_REVOKED,
            title="Token Revoked",
            message=f"Your authentication token has been revoked and is no longer valid.\n\n{reason_text}",
            user_action=(
                f"You need to reauthenticate completely:\n"
                f"\n"
                f"1. Call start_google_auth with your email\n"
                f"2. Follow the browser link\n"
                f"3. Grant permissions again\n"
                f"\n"
                f"Your previous sessions and data are safe, only authentication needs renewal."
            ),
            code_example=(
                f"# Complete reauthentication\n"
                f"start_google_auth(\n"
                f'    user_google_email="{user_email}",\n'
                f'    service_name="{service_name}"\n'
                f")"
            ),
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#token-revoked",
        )

    @staticmethod
    def insufficient_scopes(
        user_email: str, service_name: str, required_scopes: List[str], current_scopes: List[str]
    ) -> AuthErrorGuidance:
        """Error message for insufficient permissions"""
        missing = sorted(set(required_scopes) - set(current_scopes))

        scope_names = {
            "https://www.googleapis.com/auth/gmail.readonly": "Read Gmail messages",
            "https://www.googleapis.com/auth/gmail.send": "Send emails",
            "https://www.googleapis.com/auth/gmail.modify": "Modify Gmail messages",
            "https://www.googleapis.com/auth/drive.readonly": "Read Google Drive files",
            "https://www.googleapis.com/auth/drive": "Full Google Drive access",
            "https://www.googleapis.com/auth/calendar.readonly": "Read calendar events",
            "https://www.googleapis.com/auth/calendar": "Manage calendar events",
            "https://www.googleapis.com/auth/documents": "Edit Google Docs",
            "https://www.googleapis.com/auth/spreadsheets": "Edit Google Sheets",
        }

        missing_descriptions = []
        for scope in missing:
            name = scope_names.get(scope, scope.split("/")[-1])
            missing_descriptions.append(f"  • {name}")

        missing_text = "\n".join(missing_descriptions)

        return AuthErrorGuidance(
            error_type=ErrorType.INSUFFICIENT_SCOPES,
            title="Insufficient Permissions",
            message=(
                f"Your current authentication for {service_name} doesn't have all required permissions.\n"
                f"\n"
                f"Missing permissions:\n"
                f"{missing_text}"
            ),
            user_action=(
                f"Reauthenticate to grant additional permissions:\n"
                f"\n"
                f"1. Call start_google_auth (same as before)\n"
                f"2. On the Google consent screen, you'll see the new permissions\n"
                f"3. Grant all requested permissions\n"
                f"\n"
                f"This is safe - you're just giving the same app more permissions."
            ),
            code_example=(
                f"# Reauthenticate with broader permissions\n"
                f"start_google_auth(\n"
                f'    user_google_email="{user_email}",\n'
                f'    service_name="{service_name}"\n'
                f")"
            ),
            technical_details=f"Missing scopes: {', '.join(missing)}",
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#scopes",
        )

    @staticmethod
    def client_not_configured() -> AuthErrorGuidance:
        """Error message for missing OAuth client configuration"""
        return AuthErrorGuidance(
            error_type=ErrorType.CLIENT_NOT_CONFIGURED,
            title="OAuth Client Not Configured",
            message=(
                "OAuth client credentials are not configured. You need to set up OAuth credentials "
                "before users can authenticate."
            ),
            user_action=(
                "Configure OAuth credentials using one of these methods:\n"
                "\n"
                "Method 1: Environment Variables (Recommended)\n"
                "  export GOOGLE_OAUTH_CLIENT_ID='your-client-id'\n"
                "  export GOOGLE_OAUTH_CLIENT_SECRET='your-client-secret'\n"
                "  export GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/oauth2callback'\n"
                "\n"
                "Method 2: Client Secrets File\n"
                "  1. Download client_secret.json from Google Cloud Console\n"
                "  2. Set path: export GOOGLE_CLIENT_SECRET_PATH='/path/to/client_secret.json'\n"
                "\n"
                "Method 3: Default Location\n"
                "  Place client_secret.json in the auth directory"
            ),
            code_example=(
                "# Example: Set environment variables\n"
                "export GOOGLE_OAUTH_CLIENT_ID='123456789.apps.googleusercontent.com'\n"
                "export GOOGLE_OAUTH_CLIENT_SECRET='GOCSPX-abc123...'\n"
                "export GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/oauth2callback'"
            ),
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_SETUP.md",
        )

    @staticmethod
    def session_already_bound(session_id: str, current_user: str, requested_user: str) -> AuthErrorGuidance:
        """Error message for session already authenticated as different user"""
        return AuthErrorGuidance(
            error_type=ErrorType.SESSION_ALREADY_BOUND,
            title="Session Already Authenticated",
            message=(
                f"This session is already authenticated as {current_user}. "
                f"You cannot switch to {requested_user} without logging out first."
            ),
            user_action=(
                f"To authenticate as {requested_user}, choose one of these options:\n"
                f"\n"
                f"Option 1: Start a new session\n"
                f"  Open a new terminal/browser and authenticate there\n"
                f"\n"
                f"Option 2: Log out first (Advanced)\n"
                f"  1. Call: logout_google_auth()\n"
                f"  2. Then authenticate as new user\n"
                f"\n"
                f"Recommended: Use Option 1 to keep both sessions active."
            ),
            technical_details=f"Session {session_id} bound to {current_user}, cannot bind to {requested_user}",
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#multiple-users",
        )

    @staticmethod
    def invalid_state(state: Optional[str] = None, reason: str = "unknown") -> AuthErrorGuidance:
        """Error message for invalid OAuth state parameter"""
        return AuthErrorGuidance(
            error_type=ErrorType.INVALID_STATE,
            title="Invalid Authentication State",
            message=(
                "The authentication callback received an invalid or expired state parameter. "
                "This usually happens if:\n"
                "  • The authentication link expired (>10 minutes old)\n"
                "  • The link was used more than once\n"
                "  • Browser cookies were cleared during authentication"
            ),
            user_action=(
                "Please restart the authentication process:\n"
                "\n"
                "1. Call start_google_auth again\n"
                "2. You'll get a fresh authentication link\n"
                "3. Click the link within 10 minutes\n"
                "4. Complete authentication in one attempt\n"
                "\n"
                "Tip: Keep the terminal/app open during authentication."
            ),
            technical_details=f"State: {state}, Reason: {reason}",
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#state-validation",
        )

    @staticmethod
    def callback_timeout(timeout_seconds: int = 300) -> AuthErrorGuidance:
        """Error message for authentication callback timeout"""
        minutes = timeout_seconds // 60

        return AuthErrorGuidance(
            error_type=ErrorType.CALLBACK_TIMEOUT,
            title="Authentication Timeout",
            message=(
                f"The authentication process timed out after {minutes} minutes. "
                f"You didn't complete the Google login within the allowed time."
            ),
            user_action=(
                "Please try again and complete authentication faster:\n"
                "\n"
                "1. Call start_google_auth\n"
                "2. Immediately click the authentication link\n"
                "3. Complete Google login within {minutes} minutes\n"
                "4. Don't close the terminal/app during authentication\n"
                "\n"
                "Tips:\n"
                "  • Have your Google password ready\n"
                "  • Close unnecessary browser tabs\n"
                "  • Check your internet connection"
            ),
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_GUIDE.md#timeouts",
        )

    @staticmethod
    def network_error(error: Exception, service_name: str) -> AuthErrorGuidance:
        """Error message for network-related errors"""
        return AuthErrorGuidance(
            error_type=ErrorType.NETWORK_ERROR,
            title="Network Error",
            message=(
                f"A network error occurred while authenticating with {service_name}. "
                f"This could be due to:\n"
                f"  • Internet connection issues\n"
                f"  • Firewall blocking requests\n"
                f"  • Google services temporarily unavailable\n"
                f"  • Proxy configuration problems"
            ),
            user_action=(
                "Please check your connection and try again:\n"
                "\n"
                "1. Verify internet connection: ping google.com\n"
                "2. Check firewall settings\n"
                "3. If using proxy, verify configuration\n"
                "4. Try again in a few minutes\n"
                "\n"
                "If problem persists, check Google Cloud Status:\n"
                "  https://status.cloud.google.com"
            ),
            technical_details=str(error),
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_TROUBLESHOOTING.md#network-errors",
        )

    @staticmethod
    def generic_auth_error(error: Exception, user_email: str, service_name: str = "unknown") -> AuthErrorGuidance:
        """Generic error message with troubleshooting steps"""
        return AuthErrorGuidance(
            error_type=ErrorType.GENERIC_AUTH_ERROR,
            title="Authentication Error",
            message=f"An unexpected error occurred during authentication for {service_name}.",
            user_action=(
                f"Please try these troubleshooting steps:\n"
                f"\n"
                f"Step 1: Clear cached credentials\n"
                f'  clear_google_auth(user_google_email="{user_email}")\n'
                f"\n"
                f"Step 2: Reauthenticate\n"
                f'  start_google_auth(user_google_email="{user_email}", service_name="{service_name}")\n'
                f"\n"
                f"Step 3: If still failing, check:\n"
                f"  • OAuth client configuration (environment variables)\n"
                f"  • Internet connection\n"
                f"  • Google Cloud Console for app status\n"
                f"\n"
                f"If the problem persists, report issue with the technical details below."
            ),
            code_example=(
                f"# Clear and reauthenticate\n"
                f'clear_google_auth(user_google_email="{user_email}")\n'
                f'start_google_auth(user_google_email="{user_email}", service_name="{service_name}")'
            ),
            technical_details=f"{type(error).__name__}: {str(error)}",
            help_url=f"{AuthErrorMessages.BASE_DOCS_URL}/OAUTH_TROUBLESHOOTING.md",
        )

    @staticmethod
    def format_error_for_llm(guidance: AuthErrorGuidance) -> str:
        """
        Format error message optimized for LLM consumption.

        Provides clear, actionable information that an LLM can use to
        help users resolve authentication issues.
        """
        return (
            f"AUTHENTICATION_ERROR:\n"
            f"Type: {guidance.error_type.value}\n"
            f"Title: {guidance.title}\n"
            f"\n"
            f"USER_MESSAGE:\n"
            f"{guidance.message}\n"
            f"\n"
            f"RESOLUTION_STEPS:\n"
            f"{guidance.user_action}\n"
            f"\n"
            f"CODE_EXAMPLE:\n"
            f"{guidance.code_example or 'N/A'}\n"
            f"\n"
            f"DOCUMENTATION: {guidance.help_url or 'N/A'}\n"
            f"TECHNICAL_DETAILS: {guidance.technical_details or 'N/A'}"
        )
