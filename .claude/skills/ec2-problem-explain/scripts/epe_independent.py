"""Common numerical and method checks for one independent solution."""
import math


def independent_errors(key, item):
    errors = []
    if item.get('method') not in ('exact', 'symbolic', 'numerical', 'proof', 'qualitative') or not isinstance(item.get('conclusion'), str) or not item['conclusion'].strip():
        errors.append(f'{key}: 검증 방법·결론 필요')
    if item.get('method') == 'numerical':
        tolerance, residual = item.get('tolerance'), item.get('residual')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (tolerance, residual)) or not 0 <= residual <= tolerance or tolerance <= 0:
            errors.append(f'{key}: 유한한 tolerance>0 및 0<=residual<=tolerance 필요')
    return errors
