# jamiiwallet/services/transaction_preprocessor.py

import logging
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from accounts.models import User
from kiini.helpers.validators import validate_eac_phone
from celery import shared_task

from jamiiwallet.services.cache_utils import (
    get_cached_user_id_by_email,
    cache_user_lookup_by_email,
    get_cached_user_id_by_phone,
    cache_user_lookup_by_phone,
)

logger = logging.getLogger(__name__)


def sync_pre_process_transaction(account_identifier: str, metadata: dict):
    """
    Perform synchronous validation and normalization before transaction processing.

    - Validates account_identifier (email or phone number)
    - Ensures metadata completeness
    - Returns validated (user, metadata)
    """

    logger.info(f"🔍 Starting pre-processing for identifier={account_identifier}")

    if not account_identifier:
        raise ValidationError("Account identifier is required.")

    # Ensure metadata dict is valid
    if metadata is None:
        metadata = {}

    user = None

    # -------- Validate identifier (email or phone) -------- #
    if "@" in str(account_identifier):  # treat as email
        # try cache first
        cached = get_cached_user_id_by_email(account_identifier)
        if cached:
            try:
                user = User.objects.get(pk=cached)
            except Exception:
                user = None

        if not user:
            try:
                user = User.objects.get(email=account_identifier)
                # cache for next time
                cache_user_lookup_by_email(account_identifier, str(user.id))
            except User.DoesNotExist:
                raise ValidationError(f"User with email '{account_identifier}' does not exist.")
    else:
        try:
            validate_eac_phone(account_identifier)
            # try cache first
            cached = get_cached_user_id_by_phone(account_identifier)
            if cached:
                try:
                    user = User.objects.get(pk=cached)
                except Exception:
                    user = None

            if not user:
                # encrypted lookup requires scanning or specialized index; reuse existing approach
                all_users = User.objects.all()
                found_user = next(
                    (u for u in all_users if u.phone_number == account_identifier), None
                )
                if not found_user:
                    raise ValidationError(f"User with phone '{account_identifier}' not found.")
                user = found_user
                cache_user_lookup_by_phone(account_identifier, str(user.id))
        except ValidationError as e:
            raise ValidationError(f"Invalid phone number: {e}")

    # -------- Metadata validation -------- #
    required_keys = ["source_txn_id", "merchant_id"]
    for key in required_keys:
        if key not in metadata or not metadata[key]:
            raise ValidationError(f"Metadata '{key}' is missing or empty.")

    # Optionally auto-fill missing optional metadata
    metadata.setdefault("validated_at", str(db_transaction.now()))

    logger.info(f"✅ Pre-processing passed for user={user.email} metadata={metadata}")
    return user, metadata


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def async_pre_process_transaction(self, account_identifier: str, metadata: dict):
    """
    Async pre-validation for account identifier and metadata.
    Called by TransactionEngine before debit/credit.

    Returns:
        dict: {status: 'success'|'failed', user_id, metadata, error}
    """
    try:
        with db_transaction.atomic():
            user, metadata = sync_pre_process_transaction(account_identifier, metadata)

            logger.info(f"Async pre-processing OK for user {user.email}")
            return {
                "status": "success",
                "user_id": str(user.id),
                "metadata": metadata,
            }

    except ValidationError as ve:
        logger.warning(f"Async pre-process failed: {ve}")
        return {"status": "failed", "error": str(ve)}

    except Exception as e:
        logger.error(f"Unexpected error in async pre-processing: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}