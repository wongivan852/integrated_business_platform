# Integrated Business Platform - SSO Implementation Plan

**Date:** October 2, 2025
**Version:** 2.0.0 - SSO Enabled
**Status:** 🔧 Implementation Ready

---

## Executive Summary

The current integrated business platform uses iframe embedding with independent authentication for each secondary app. This creates:

**Problems:**
- ❌ Users must log in separately to each app
- ❌ No session sharing between apps
- ❌ Security concerns with multiple credentials
- ❌ Poor user experience
- ❌ Difficult to manage permissions centrally

**Solution: JWT-Based SSO**
- ✅ Single login for all apps
- ✅ Centralized user management
- ✅ Secure token-based authentication
- ✅ Seamless app switching
- ✅ Unified permission system

---

## Current Architecture Analysis

### Master Platform (integrated_business_platform)
- **Framework:** Django 4.2.16
- **Auth:** Session-based (Django built-in)
- **User Model:** Custom User with UserProfile
- **Database:** PostgreSQL
- **Reverse Proxy:** Nginx

### Secondary Apps
1. **company-leave-system** (Port 8001)
2. **company-cost-quotation-system** (Port 8002)
3. **company_expense_claim_system** (Port 8003)
4. **company_crm_system** (Port 8004)
5. **company_asset_management** (Port 8005)
6. **stripe-dashboard** (Port 8006)

### Current Integration Method
- Iframe embedding
- URL-based redirection
- Independent authentication per app
- No token passing

---

## SSO Architecture Design

### Authentication Flow

```
┌─────────────┐
│   User      │
└─────┬───────┘
      │ 1. Login
      ▼
┌─────────────────────┐
│  Master Platform    │
│  (SSO Provider)     │
│  - Validates creds  │
│  - Issues JWT token │
└─────┬───────────────┘
      │ 2. JWT Token
      ▼
┌─────────────────────┐
│  Secondary Apps     │
│  (SSO Consumers)    │
│  - Validate token   │
│  - Create session   │
│  - Auto-login       │
└─────────────────────┘
```

### JWT Token Structure

```json
{
  "user_id": 123,
  "username": "john.doe",
  "email": "john@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_staff": false,
  "is_superuser": false,
  "department": "Engineering",
  "company": "Krystal Education",
  "permissions": {
    "leave_system": true,
    "quotation_system": true,
    "expense_system": true,
    "crm_system": false,
    "asset_management": false,
    "stripe_dashboard": false
  },
  "exp": 1696348800,
  "iat": 1696345200
}
```

---

## Implementation Components

### 1. Master Platform (SSO Provider)

#### A. JWT Token Generation
- Install: `djangorestframework-simplejwt`
- Create custom JWT serializer with user permissions
- Add token endpoints:
  - `/api/sso/token/` - Generate SSO token
  - `/api/sso/refresh/` - Refresh token
  - `/api/sso/validate/` - Validate token

#### B. SSO Middleware
- Inject JWT token into secondary app requests
- Handle token refresh automatically
- Track active sessions

#### C. User Synchronization API
- `/api/sso/user/` - Get current user data
- `/api/sso/permissions/` - Get user permissions
- `/api/sso/validate-token/` - Validate and decode token

### 2. Secondary Apps (SSO Consumers)

#### A. SSO Authentication Backend
- Custom Django authentication backend
- Validates JWT tokens from master platform
- Creates/updates local user records
- Maps permissions to Django groups

#### B. SSO Middleware
- Intercepts requests with SSO token
- Validates token with master platform
- Auto-authenticates user
- Falls back to local auth if token invalid

#### C. Configuration
- Add master platform URL
- Configure JWT secret (shared)
- Set up token validation endpoints

### 3. Shared Components

#### A. Shared Secret Key
- Environment variable: `SSO_SECRET_KEY`
- Used for JWT signing and verification
- Must be same across all apps

#### B. User Data Sync
- Master platform is source of truth
- Secondary apps cache user data locally
- Periodic sync for user updates

---

## Implementation Steps

### Phase 1: Master Platform Setup (2-3 hours)

1. **Install Dependencies**
   ```bash
   pip install djangorestframework-simplejwt==5.3.0
   ```

2. **Create SSO App**
   ```
   integrated_business_platform/
   └── sso/
       ├── __init__.py
       ├── models.py          # SSOToken model
       ├── serializers.py     # User serializer
       ├── views.py           # Token endpoints
       ├── urls.py            # SSO URLs
       └── middleware.py      # SSO middleware
   ```

3. **Update Settings**
   - Add SSO app to INSTALLED_APPS
   - Configure SimpleJWT
   - Add SSO middleware
   - Set SSO_SECRET_KEY

4. **Create API Endpoints**
   - Token generation endpoint
   - Token validation endpoint
   - User info endpoint
   - Permission check endpoint

### Phase 2: Secondary Apps Setup (1-2 hours per app)

1. **Create SSO Module**
   ```
   app_name/
   └── sso_integration/
       ├── __init__.py
       ├── backend.py         # SSO auth backend
       ├── middleware.py      # SSO middleware
       └── utils.py           # Helper functions
   ```

2. **Update Settings**
   - Add SSO authentication backend
   - Add SSO middleware
   - Configure master platform URL
   - Set SSO_SECRET_KEY (same as master)

3. **Update User Model (Optional)**
   - Add SSO user ID field
   - Add last sync timestamp
   - Add method to sync from master

### Phase 3: Integration & Testing (2-3 hours)

1. **Test SSO Flow**
   - Login to master platform
   - Access each secondary app
   - Verify auto-login works
   - Test token refresh
   - Test logout propagation

2. **Test Edge Cases**
   - Expired token handling
   - Invalid token handling
   - Network failure handling
   - Permission changes
   - User deactivation

3. **Performance Testing**
   - Token validation speed
   - API response times
   - Concurrent user handling

### Phase 4: Deployment (1-2 hours)

1. **Update Environment Variables**
   - Set SSO_SECRET_KEY on all servers
   - Set MASTER_PLATFORM_URL
   - Update ALLOWED_HOSTS

2. **Database Migrations**
   - Run migrations on master platform
   - Run migrations on secondary apps

3. **Deploy Updates**
   - Deploy master platform first
   - Deploy secondary apps one by one
   - Verify SSO works after each deployment

---

## Configuration Examples

### Master Platform `.env`
```bash
# SSO Configuration
SSO_SECRET_KEY=your-very-secure-sso-secret-key-change-in-production
SSO_TOKEN_LIFETIME=3600  # 1 hour
SSO_REFRESH_LIFETIME=86400  # 24 hours

# JWT Settings
JWT_ALGORITHM=HS256
JWT_ALLOW_REFRESH=True
```

### Secondary App `.env`
```bash
# SSO Configuration
SSO_MASTER_URL=http://localhost:8000
SSO_SECRET_KEY=your-very-secure-sso-secret-key-change-in-production
SSO_ENABLED=True

# Fallback to local auth if SSO fails
SSO_FALLBACK_LOCAL_AUTH=True
```

---

## Security Considerations

### Token Security
- ✅ Short token lifetime (1 hour)
- ✅ Refresh token rotation
- ✅ Secure secret key (256-bit minimum)
- ✅ HTTPS in production
- ✅ Token blacklisting on logout

### API Security
- ✅ Rate limiting on token endpoints
- ✅ IP whitelist for secondary apps
- ✅ CORS configuration
- ✅ Request signing
- ✅ Audit logging

### User Security
- ✅ Immediate permission propagation
- ✅ Token invalidation on user deactivation
- ✅ Session tracking
- ✅ Multi-factor authentication (optional)

---

## API Endpoints Reference

### Master Platform

#### 1. Generate SSO Token
```http
POST /api/sso/token/
Content-Type: application/json

{
  "username": "john.doe",
  "password": "password123"
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "username": "john.doe",
    "email": "john@company.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### 2. Validate Token
```http
POST /api/sso/validate/
Authorization: Bearer <token>

Response 200:
{
  "valid": true,
  "user": { ... },
  "permissions": { ... }
}
```

#### 3. Get User Info
```http
GET /api/sso/user/
Authorization: Bearer <token>

Response 200:
{
  "id": 123,
  "username": "john.doe",
  "email": "john@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "permissions": { ... }
}
```

#### 4. Refresh Token
```http
POST /api/sso/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response 200:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Secondary Apps

#### 1. SSO Login
```http
GET /sso/login/?token=<jwt_token>

Response: Redirect to app home (authenticated)
```

#### 2. SSO Logout
```http
POST /sso/logout/

Response: Redirect to master platform logout
```

---

## Migration Strategy

### For Users
1. **Transparent Migration**
   - Existing sessions remain valid
   - First app access triggers SSO setup
   - No action required from users

2. **Graceful Fallback**
   - SSO failure → local login
   - Clear error messages
   - Support contact information

### For Administrators
1. **Pre-Deployment**
   - Review user permissions
   - Export user data
   - Test in staging environment

2. **During Deployment**
   - Deploy master platform
   - Wait 5 minutes for verification
   - Deploy secondary apps sequentially

3. **Post-Deployment**
   - Monitor error logs
   - Verify user access
   - Collect feedback

---

## Monitoring & Maintenance

### Metrics to Monitor
- SSO token generation rate
- Token validation success rate
- Token validation response time
- Failed authentication attempts
- Active SSO sessions

### Logs to Track
- Token generation events
- Token validation requests
- Authentication failures
- Permission denials
- API errors

### Regular Tasks
- Weekly: Review failed auth logs
- Monthly: Rotate SSO secret (if compromised)
- Quarterly: Security audit
- Yearly: Update dependencies

---

## Troubleshooting Guide

### Issue: "Token validation failed"
**Cause:** Secret key mismatch or expired token

**Solution:**
1. Verify SSO_SECRET_KEY matches on all apps
2. Check token expiration time
3. Test token generation manually

### Issue: "User not authenticated after SSO"
**Cause:** Backend not properly configured

**Solution:**
1. Verify SSO backend in AUTHENTICATION_BACKENDS
2. Check SSO middleware order
3. Review user creation/sync logic

### Issue: "Permission denied after SSO login"
**Cause:** Permissions not synced

**Solution:**
1. Check UserProfile permissions on master
2. Verify permission serialization in token
3. Test permission check endpoint

---

## Future Enhancements

### Short Term (Next Sprint)
- [ ] Add SSO session dashboard
- [ ] Implement token blacklist
- [ ] Add audit logging
- [ ] Create admin tools

### Medium Term (Next Quarter)
- [ ] Add OAuth2 support
- [ ] Implement MFA
- [ ] Add SSO analytics
- [ ] Create mobile app SSO

### Long Term (Next Year)
- [ ] SAML support
- [ ] LDAP integration
- [ ] Federated identity
- [ ] Biometric authentication

---

## Success Criteria

### Must Have
- ✅ Single login works for all apps
- ✅ Permissions synced from master
- ✅ No separate logins required
- ✅ Secure token handling
- ✅ Graceful error handling

### Should Have
- ✅ Token refresh works automatically
- ✅ Logout propagates to all apps
- ✅ Fast token validation (< 100ms)
- ✅ Comprehensive logging
- ✅ Admin monitoring tools

### Nice to Have
- ⏳ SSO analytics dashboard
- ⏳ Real-time session tracking
- ⏳ Advanced security features
- ⏳ Mobile app support

---

## Conclusion

This SSO implementation will:
1. **Eliminate redundant logins** across all business apps
2. **Centralize user management** in one platform
3. **Improve security** with token-based auth
4. **Enhance user experience** with seamless navigation
5. **Simplify administration** with unified permissions

**Estimated Total Time:** 10-15 hours
**Risk Level:** Medium
**Impact:** High

---

**Status:** 📋 Ready for Implementation
**Next Step:** Begin Phase 1 - Master Platform Setup

**Last Updated:** October 2, 2025
**Prepared by:** System Integration Team
