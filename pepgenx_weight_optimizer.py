import json
from typing import Dict, Any


WEIGHT_BOUNDS = {
    "dwell": (1, 200),
    "distance": (1, 200),
    "avg_pallets": (1, 200),
    "format": (1, 200),
}

# Enforce decreasing importance
WEIGHT_ORDER = ["dwell", "distance", "avg_pallets", "format"]


# ==============================
# Prompt Builder
# ==============================

def build_pepgenx_prompt(
    current_weights: Dict[str, float],
    kpis: Dict[str, Any],
    business_notes: str | None = None,
) -> str:
    prompt = f"""
You are an optimization assistant for last-mile routing.

We use OR-Tools with the following cost function:

Cost =
W_dwell * dwell_time
+ W_distance * distance
+ W_avg_pallets * avg_pallets
+ W_format * store_format_penalty

Current weights:
{json.dumps(current_weights, indent=2)}

Observed KPIs from last run:
{json.dumps(kpis, indent=2)}

Business objectives:
1. Minimize total route duration
2. Reduce SLA violations
3. Keep truck capacity respected
4. Avoid long dwell-time stops late in routes

Constraints:
- All weights must be positive numbers
- Importance order must be:
  dwell >= distance >= avg_pallets >= format
- Max weight value = 200

Return ONLY valid JSON with this schema:
{{
  "dwell": number,
  "distance": number,
  "avg_pallets": number,
  "format": number
}}
"""

    if business_notes:
        prompt += f"\nAdditional business context:\n{business_notes}\n"

    return prompt.strip()


# ==============================
# Response Validation
# ==============================

def validate_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Validates and clamps LLM-generated weights.
    """

    # Check all required keys
    for key in WEIGHT_BOUNDS:
        if key not in weights:
            raise ValueError(f"Missing weight: {key}")

    # Clamp bounds
    for key, (low, high) in WEIGHT_BOUNDS.items():
        weights[key] = float(weights[key])
        weights[key] = max(low, min(high, weights[key]))

    # Enforce ordering
    for i in range(len(WEIGHT_ORDER) - 1):
        higher = WEIGHT_ORDER[i]
        lower = WEIGHT_ORDER[i + 1]
        if weights[higher] < weights[lower]:
            weights[higher] = weights[lower]

    return weights


# ==============================
# PepGenX Client Wrapper
# ==============================

class PepGenXWeightOptimizer:
    """
    Thin wrapper around PepGenX (or any LLM client)
    that returns optimized routing weights.
    """

    def __init__(self, pepgenx_client):
        """
        pepgenx_client must expose:
        pepgenx_client.generate(prompt: str) -> str (JSON)
        """
        self.client = pepgenx_client

    def optimize_weights(
        self,
        current_weights: Dict[str, float],
        kpis: Dict[str, Any],
        business_notes: str | None = None,
    ) -> Dict[str, float]:
        """
        Main entrypoint used by routing system.
        """

        prompt = build_pepgenx_prompt(
            current_weights=current_weights,
            kpis=kpis,
            business_notes=business_notes,
        )

        # ---- Call PepGenX / LLM ----
        raw_response = self.client.generate(prompt)

        # ---- Parse JSON ----
        try:
            new_weights = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from PepGenX: {raw_response}") from e

        # ---- Validate + clamp ----
        validated = validate_weights(new_weights)

        return validated
