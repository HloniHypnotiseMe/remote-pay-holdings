# RemotePay Holdings

RemotePay Holdings is a C6 product source for Tax, Secretarial, Compliance and Corporate Governance workflows. It is used internally and is being structured for external product delivery.

## Platform boundary

Domain agents and contracts remain in this repository. Shared platform capabilities belong to C6 SaaS Core.

Current shared integration:
- Tax Secretarial evidence uses `tax-secretarial/core/c6_evidence.py`.
- Set `C6_EVIDENCE_API_URL` to the C6 SaaS Core base URL to publish evidence contracts.
- If the endpoint is unavailable or not configured, the publisher returns **GAP** rather than claiming verification.
- Win events remain on the existing C6 Win Engine contract.

## Evidence rule

Domain evidence statuses are normalized to the C6 shared vocabulary:

`EXISTS → WORKS → VERIFIED → LIVE`

Unsupported or unavailable proof becomes `GAP`. The product does not promote UI state or local agent output into verified customer claims.

## Productization status

The domain contracts and agents exist in the repository. External API/auth/tenant integration into C6 SaaS Core is still a wiring task and is not represented as live.
