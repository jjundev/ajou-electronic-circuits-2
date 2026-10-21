"""Versioned review reuse; missing or changed evidence never inherits approval."""
from copy import deepcopy

from epe_shared import PERSONALIZED_REVIEW_POLICY, validate_style_audit

POLICY_VERSION = PERSONALIZED_REVIEW_POLICY

def carry_reviews(stored, fresh, references, reusable):
    result = deepcopy(fresh)
    result['review_policy_version'] = POLICY_VERSION
    result['references'] = references
    audit = fresh.get('learning_style_audit', {})
    snapshot = audit.get('learning_style') if isinstance(audit, dict) else None
    valid_style = (isinstance(snapshot, dict) and isinstance(audit.get('items'), dict)
                   and not validate_style_audit(stored.get('learning_style_audit'),
                                                snapshot, list(audit['items'])))
    if reusable and valid_style and stored.get('review_policy_version') == POLICY_VERSION:
        for key in ('content', 'independent'):
            if stored.get(key, {}).get('status') == 'pass':
                result[key] = deepcopy(stored[key])
        if isinstance(stored.get('learning_style_audit'), dict):
            result['learning_style_audit'] = deepcopy(stored['learning_style_audit'])
    return result
