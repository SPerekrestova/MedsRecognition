"""Unified Supabase service for authentication and profile management."""

from functools import lru_cache
from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings
from app.core.logging_config import logger
from app.schemas.profile import ProfileUpdate, ProfileInDB


class AuthService:

    def __init__(self):
        self.supabase = None
        try:
            if (
                not settings.SUPABASE_URL
                or not hasattr(settings, "SUPABASE_SERVICE_ROLE_KEY")
                or not settings.SUPABASE_SERVICE_ROLE_KEY
            ):
                logger.error("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in environment")
                return

            options = ClientOptions(
                postgrest_client_timeout=60, storage_client_timeout=120, auto_refresh_token=True
            )

            supabase_url = settings.SUPABASE_URL
            logger.info(f"Initializing Supabase client with URL: {supabase_url}")

            self.supabase: Client = create_client(
                supabase_url, settings.SUPABASE_SERVICE_ROLE_KEY, options=options
            )

        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.supabase = None

    def create_user_with_profile(
        self, email: str, password: str, username: Optional[str] = None
    ) -> Optional[ProfileInDB]:
        try:
            try:
                logger.info(f"Attempting to create user with email: {email}")
                auth_response = self.supabase.auth.sign_up({"email": email, "password": password})
                logger.info(f"Auth response received: {auth_response}")
            except Exception as auth_err:
                logger.error(f"Error during user creation with Supabase: {auth_err}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"User creation failed: {str(auth_err)}",
                )

            if not auth_response or not auth_response.user:
                logger.error("Auth response did not contain user data")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create user"
                )

            # Get the user ID from the response
            user_id = auth_response.user.id
            logger.info(f"User created with ID: {user_id}")

            profile = self.create_profile(user_id, username or email.split("@")[0])

            logger.info(f"Successfully created user and profile for {email}")
            return profile

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user with profile: {e}")
            return None

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Authenticate user and return session data."""
        try:
            try:
                auth_response = self.supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
            except Exception as auth_err:
                logger.error(f"Authentication error with Supabase: {auth_err}")
                return False, None

            if not auth_response or not auth_response.user:
                logger.warning(f"Authentication failed for {email}: No user in response")
                return False, None

            # Get user profile
            profile = self.get_user_profile(auth_response.user.id)

            session = auth_response.session

            # Return successful authentication result
            return True, {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": {
                    "user_id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "role": auth_response.user.role,  # Include the user's role
                    "profile": profile.model_dump() if profile else None,
                },
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, None

    def get_user_profile(self, user_id: UUID) -> Optional[ProfileInDB]:
        try:
            response = (
                self.supabase.from_("profiles")
                .select("*")
                .eq("id", str(user_id))
                .single()
                .execute()
            )
            return ProfileInDB(**response.data) if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            return None

    def update_user_profile(
        self, user_id: UUID, profile_data: ProfileUpdate
    ) -> Optional[ProfileInDB]:
        try:
            response = (
                self.supabase.from_("profiles")
                .update(profile_data.model_dump(exclude_unset=True, exclude_none=True))
                .eq("id", str(user_id))
                .execute()
            )

            return ProfileInDB(**response.data[0]) if response.data else None
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return None

    def delete_user_with_profile(self, user_id: UUID) -> bool:
        """Delete user and their profile."""
        try:
            # Delete profile first (due to foreign key constraint)
            (self.supabase.from_("profiles").delete().eq("id", str(user_id)).execute())

            # Delete auth user
            self.supabase.auth.admin.delete_user(str(user_id))
            return True
        except Exception as e:
            logger.error(f"Error deleting user with profile: {e}")
            return False

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and get user data."""
        try:
            user_response = self.supabase.auth.get_user(token)
            if not user_response or not hasattr(user_response, "user") or not user_response.user:
                return None

            user_id = user_response.user.id

            # Get profile for the user
            profile = self.get_user_profile(user_id)

            return {
                "id": str(user_id),
                "email": profile.email,
                "profile": profile.model_dump() if profile else None,
            }
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def create_profile(self, user_id: str, username: Optional[str] = None) -> Optional[ProfileInDB]:
        """Create a profile for an existing user."""
        try:
            # First check if profile exists
            existing_profile = (
                self.supabase.from_("profiles")
                .select("*")
                .eq("id", str(user_id))
                .single()
                .execute()
            )

            if existing_profile.data:
                # Profile exists, return it
                return ProfileInDB(**existing_profile.data)

            # Create new profile if it doesn't exist
            data = {
                "id": str(user_id),
                "username": username or "User",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # Insert the profile data
            profile_response = self.supabase.from_("profiles").insert(data).execute()

            if not profile_response.data:
                logger.error("Failed to create profile")
                return None

            return ProfileInDB(**profile_response.data[0])

        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return None

    def logout_user(self, token: str) -> bool:
        try:
            self.supabase.auth.sign_out(jwt=token, scope="global")
            return True
        except Exception as e:
            logger.error(f"Error logging out user with profile: {e}")
            return False

    def refresh_session(self, token: str) -> Optional[Any]:
        try:
            response_obj = self.supabase.auth.refresh_session(token)

            session_obj = response_obj.session
            session_dict = session_obj.dict() if hasattr(session_obj, "dict") else session_obj
            return session_dict
        except Exception as e:
            logger.error(f"Error logging out user with profile: {e}")
            return None


@lru_cache()
def get_auth_service() -> AuthService:
    """Get or create Supabase service instance."""
    return AuthService()
