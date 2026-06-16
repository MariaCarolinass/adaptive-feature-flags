from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Adaptive Feature Flags"
    database_url: str = "sqlite:///./db.sqlite3"
    models_dir: str = "storage/models"
    environment: str = "development"
    log_level: str = "INFO"
    positive_event_types: list[str] = [
        "addtocart",
        "transaction",
        "checkout_upsell_clicked",
        "pricing_details_opened",
        "upgrade_cta_clicked",
        "cart_reminder_clicked",
        "hero_cta_clicked",
        "search_suggestion_selected",
        "retention_banner_clicked",
        "community_invite_clicked",
        "onboarding_completed",
        "first_task_created",
        "profile_completed",
        "first_success_action_taken",
        "weekly_digest_opened",
        "streak_banner_clicked",
        "alert_center_opened",
        "purchase_completed",
        "subscription_upgraded",
        "login_form_submitted",
        "signup_form_submitted",
        "magic_link_requested",
        "magic_link_verified",
        "social_login_clicked",
        "login_success",
        "signup_completed",
        "password_reset_requested",
        "password_reset_completed",
    ]
    view_event_types: list[str] = [
        "view",
        "checkout_upsell_shown",
        "pricing_tooltip_shown",
        "upgrade_prompt_shown",
        "cart_reminder_shown",
        "homepage_hero_seen",
        "search_suggestions_shown",
        "retention_banner_shown",
        "community_invite_shown",
        "onboarding_step_shown",
        "empty_state_shown",
        "profile_setup_shown",
        "success_tip_shown",
        "weekly_digest_shown",
        "streak_banner_shown",
        "alert_center_shown",
        "community_digest_shown",
        "login_page_viewed",
        "signup_page_viewed",
        "magic_link_prompt_shown",
        "social_login_prompt_shown",
        "password_reset_prompt_shown",
        "signup_form_shown",
    ]
    intermediate_positive_event_types: list[str] = [
        "addtocart",
        "checkout_upsell_clicked",
        "pricing_details_opened",
        "upgrade_cta_clicked",
        "cart_reminder_clicked",
        "hero_cta_clicked",
        "search_suggestion_selected",
        "retention_banner_clicked",
        "community_invite_clicked",
        "onboarding_completed",
        "first_task_created",
        "profile_completed",
        "first_success_action_taken",
        "weekly_digest_opened",
        "streak_banner_clicked",
        "alert_center_opened",
        "login_form_submitted",
        "signup_form_submitted",
        "magic_link_requested",
        "social_login_clicked",
        "password_reset_requested",
    ]
    terminal_positive_event_types: list[str] = [
        "transaction",
        "purchase_completed",
        "subscription_upgraded",
        "login_success",
        "signup_completed",
        "magic_link_verified",
        "password_reset_completed",
    ]
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    cors_allowed_origins: list[str] = ["http://localhost", "http://127.0.0.1", "http://localhost:3000"]
    enable_docs: bool = True
    auth_enabled: bool = False
    auth_jwt_secret: str = ""
    auth_issuer_key: str = ""
    auth_token_expire_minutes: int = 60
    auth_exempt_paths: list[str] = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/auth/token"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_json_loads=True,
    )


settings = Settings()
