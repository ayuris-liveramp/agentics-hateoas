# ADR-006: Ed25519 Over RS256 for JWT Authentication

## Status
Accepted

## Context

Early in development (commit ef569e4), JWT authentication was implemented using RS256 (RSA-2048). However, during Phase 2 development (commit c108130), the team made a deliberate switch to Ed25519 (Edwards-curve Digital Signature Algorithm).

**Initial implementation**: RS256 (RSA asymmetric cryptography)
- 2048-bit keys (typical)
- Well-established, widely supported
- Larger keys and signatures
- Slower signature generation

**Later evolution**: Ed25519 (Elliptic Curve)
- 256-bit keys
- Modern elliptic curve algorithm
- Smaller keys and signatures
- Faster operations

The team chose to migrate because Ed25519 offered superior cryptographic properties with simpler implementation.

## Decision

Use Ed25519 (EdDSA with Curve25519) for all JWT token signing and validation, replacing RS256.

```python
# Before (RS256)
jwt.encode(claims, private_key, algorithm='RS256')

# After (Ed25519)
jwt.encode(claims, private_key, algorithm='EdDSA')
```

Ed25519 is used for:
- **Token Generation**: Leaf API signs JWT tokens with private key
- **Token Validation**: Root App verifies tokens with public key
- **Key Distribution**: Public key shared between leaf and root
- **Agent Authentication**: Agents pass JWT in Authorization header

## Rationale

### Why Ed25519?

**Cryptographic Superiority:**
- EdDSA is **mathematically simpler** than RSA (fewer parameters, cleaner algorithms)
- **Highly resistant** to implementation errors (single canonical signature per message)
- **Constant-time** operations prevent timing attacks
- **Better collision resistance** for same key size
- NIST, NSA, and cryptographic community recommend Ed25519

**Size Efficiency:**
- **Keys**: 256 bits (vs 2048 bits for RS256) = 8x smaller
- **Signatures**: 64 bytes (vs 256 bytes for RS256) = 4x smaller
- **Performance**: Faster signing and verification

**Performance:**
- **Signing**: ~10x faster than RS256
- **Verification**: ~5x faster than RS256
- **Throughput**: Root App can validate more JWT tokens per second
- **Latency**: Token validation delays reduced

**Modernization:**
- Ed25519 is the **modern standard** (adopted by TLS 1.3, SSH, Signal, etc.)
- Better alignment with current cryptographic best practices
- Future-proof: unlikely to be deprecated
- Simpler to understand and implement correctly

**Practical Benefits:**
- Reduced complexity: fewer parameters to manage
- Easier deployment: smaller key files
- Better tool support: newer crypto libraries have excellent EdDSA support
- Standards alignment: FIPS 186-5 includes EdDSA

### Why Not RS256?

- ✗ Older algorithm (from 1977)
- ✗ Requires larger key sizes for equivalent security
- ✗ More complex math (potential for implementation errors)
- ✗ Slower operations
- ✗ Not recommended for new projects

### Why Not ECDSA?

Ed25519 is superior to other elliptic curve options:
- ✓ Deterministic (ECDSA requires random nonce, Ed25519 is deterministic)
- ✓ Simpler (fewer parameters)
- ✓ Better timing properties
- ✓ No rogue key attacks possible (like ECDSA)

## Consequences

### Positive
- ✅ Better cryptographic security with smaller key sizes
- ✅ Faster signature generation and validation
- ✅ Simplified key management (256-bit keys vs 2048-bit)
- ✅ Modern standard (TLS 1.3, SSH use Ed25519)
- ✅ Smaller JWT tokens (4 bytes signatures vs 256 bytes)
- ✅ Reduced computation on verification (Root App crawling)
- ✅ Future-proof cryptography
- ✅ Cleaner implementation (less error-prone)

### Negative
- ❌ Less widespread than RS256 (though rapidly changing)
- ❌ Not all legacy systems support Ed25519
- ❌ Migration effort from existing RS256 tokens
- ❌ Requires Python 3.8+ with cryptography library
- ❌ Agents expecting RS256 need update (edge case)

## Technical Details

### Key Generation

**Ed25519 keypair** (for demo, using `cryptography` library):
```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate keypair
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Export to PEM format
private_pem = private_key.private_bytes(
    encoding=Encoding.PEM,
    format=PrivateFormat.PKCS8,
    encryption_algorithm=NoEncryption()
)

public_pem = public_key.public_bytes(
    encoding=Encoding.PEM,
    format=PublicFormat.SubjectPublicKeyInfo
)
```

**Key Sizes**:
- Private key: 32 bytes (256 bits)
- Public key: 32 bytes (256 bits)
- Signature: 64 bytes (512 bits)

### Token Generation

**Leaf API** (generate JWT):
```python
import jwt
from datetime import datetime, timedelta

claims = {
    'sub': user_id,           # Subject (user identifier)
    'role': 'user',           # Role for RBAC
    'iat': datetime.utcnow(), # Issued at
    'exp': datetime.utcnow() + timedelta(hours=24)  # Expiration
}

token = jwt.encode(
    claims,
    private_key,
    algorithm='EdDSA'
)
```

### Token Validation

**Root App** (verify JWT):
```python
import jwt

try:
    payload = jwt.decode(
        token,
        public_key,
        algorithms=['EdDSA']
    )
    user_id = payload['sub']
    role = payload['role']
except jwt.InvalidSignatureError:
    # Token invalid or tampered
    return error_response()
except jwt.ExpiredSignatureError:
    # Token expired
    return error_response()
```

### JWT Claims

Standard claims used:
- **sub**: Subject (user ID) — identifies the token holder
- **role**: Role claim — for RBAC (admin, user, public)
- **iat**: Issued at — token creation timestamp
- **exp**: Expiration — when token is no longer valid

### Migration from RS256

**Phase 1**: Update authentication middleware
```python
# Accept both algorithms during transition
jwt.decode(token, public_key, algorithms=['EdDSA', 'RS256'])
```

**Phase 2**: Reissue all tokens as EdDSA
```python
# New tokens use EdDSA
token = jwt.encode(claims, ed25519_key, algorithm='EdDSA')
```

**Phase 3**: Deprecate RS256
```python
# Accept only EdDSA
jwt.decode(token, public_key, algorithms=['EdDSA'])
```

## Implementation

### Key Storage

**Demo Setup** (`leaf_api/auth/`):
```
leaf_api/auth/
├── ed25519_private_key.pem    (kept secret, not in git)
├── ed25519_public_key.pem     (shared with root app)
└── __init__.py                (key loading)
```

**Production Setup** (recommended):
- Private key in secret management (HashiCorp Vault, AWS Secrets Manager, etc.)
- Public key distributed to all verifying services
- Rotate keys periodically (e.g., quarterly)

### Dependencies

**Python cryptography library** (required):
```python
pip install cryptography>=41.0.0
pip install PyJWT>=2.8.0
```

### JWT Workflow

```
1. User authenticates to Leaf API
   ↓
2. Leaf API generates Ed25519 JWT token
   ├─ Payload: user_id, role, exp
   ├─ Signed with private Ed25519 key
   └─ Returns to user/agent
   
3. Agent includes JWT in requests: Authorization: Bearer <token>
   ↓
4. Root App receives request
   ├─ Extracts token from Authorization header
   ├─ Verifies signature with Ed25519 public key
   ├─ Validates exp claim
   └─ Extracts role for RBAC
```

## Security Properties

### What This Provides
- ✅ **Authentication**: Verifies who the user claims to be
- ✅ **Non-repudiation**: User can't deny creating token (proof of signature)
- ✅ **Integrity**: Token content can't be modified without invalidating signature
- ✅ **Cryptographic security**: Uses modern, highly-secure algorithm

### What This Doesn't Provide
- ❌ **Confidentiality**: JWT is signed but not encrypted (base64 is human-readable)
- ❌ **Authorization**: JWT proves who you are, not what you can do (role claim is separate)
- ❌ **Freshness guarantee**: No guarantee token is recent (check exp claim)

### Use in This System

**Leaf API**:
- Validates JWT signature to confirm agent identity
- Extracts role claim for field-level visibility (ADR-005)
- Issues new tokens on user login

**Root App**:
- Validates JWT when crawling protected leaf APIs
- Passes JWT to leaf APIs (Bearer token)
- Doesn't need to generate tokens (only validate)

## Related Commits

- **ef569e4**: Initial JWT auth with RS256
- **c108130**: Switch from RS256 to Ed25519

## Key Rotation Strategy

**For production**:
1. Keep current key active for 30+ days
2. Generate new key
3. Both keys valid during transition period
4. After transition, deprecate old key
5. Archive old key (in case needed)

**Validation code**:
```python
# Accept both current and previous key
jwt.decode(token, public_key, algorithms=['EdDSA'])
# (in production, try both keys if first fails)
```

## Comparison: Ed25519 vs RS256

| Property | Ed25519 | RS256 | Winner |
|----------|---------|-------|--------|
| Key size | 256 bits | 2048 bits | Ed25519 (8x smaller) |
| Signature size | 64 bytes | 256 bytes | Ed25519 (4x smaller) |
| Sign speed | Fast | Slow | Ed25519 (10x faster) |
| Verify speed | Fast | Slower | Ed25519 (5x faster) |
| Math complexity | Simple | Complex | Ed25519 |
| Timing attack risk | None | Medium | Ed25519 |
| Adoption | Growing | Universal | RS256 (but changing) |
| Recommendation | Modern standard | Legacy | Ed25519 |

## References

- **Commits**: ef569e4 (initial), c108130 (switch to Ed25519)
- **Code**:
  - `leaf_api/auth/jwt_handler.py` — Token generation and validation
  - `leaf_api/middleware/jwt_handler.py` — JWT extraction and verification
  - `root_app/crawler/api_client.py` — JWT inclusion in leaf API requests
  - `leaf_api/auth/ed25519_*.pem` — Key files (private not in repo)
- **Standards & Research**:
  - [RFC 8032 - ECDSA and EdDSA Signatures](https://tools.ietf.org/html/rfc8032)
  - [NIST FIPS 186-5 (EdDSA)](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-5.pdf)
  - [Bernstein et al. - Elliptic Curves](https://hyperelliptic.org/EFD/g1p/index.html)
- **Related ADRs**:
  - [ADR-005](005-role-based-schema-filtering.md) — Uses JWT role claims
  - [ADR-001](001-two-tier-microservice-architecture.md) — JWT validates inter-tier communication

## Future Enhancements

1. **Key rotation**: Implement automated key rotation
2. **JWK endpoint**: Expose public key via `/.well-known/jwks.json`
3. **Refresh tokens**: Add token refresh mechanism for long-lived sessions
4. **Rate limiting**: Use JWT claims for per-user rate limits
5. **Audit logging**: Log all JWT validations for security analysis
6. **Multi-key support**: Support multiple keys during transition periods
