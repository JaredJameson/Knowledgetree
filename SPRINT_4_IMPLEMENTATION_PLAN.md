# Sprint 4 - RAG Chat + VPS Deployment Plan
**Date:** 2026-01-21
**Goal:** Complete RAG Chat Interface + Deploy to VPS
**Target:** STARTER TIER ($49/mo) with full production deployment

---

## Sprint 4 Requirements Analysis

### Already Implemented ✅

**Chat UI (100% Complete)**
- ✅ Chat interface with message list and input area
- ✅ Message formatting (ReactMarkdown, code highlighting with Prism)
- ✅ Conversation sidebar with list/rename/delete
- ✅ New conversation button
- ✅ Auto-scroll to bottom
- ✅ Copy message functionality
- ✅ Delete confirmation dialog

**RAG Backend (100% Complete)**
- ✅ Anthropic Claude API integration
- ✅ RAG pipeline (BGE-M3 embedding → vector search → context building)
- ✅ Conversation context management (last 10 messages)
- ✅ Error handling (rate limits, API errors)
- ✅ Retrieved chunks with similarity scores
- ✅ Source attribution and citations

**Conversation Features (100% Complete)**
- ✅ Save conversation history (messages table)
- ✅ Load past conversations
- ✅ Delete conversations
- ✅ Rename conversations
- ✅ Export conversation (Markdown)
- ✅ Artifact panel integration (view, update, delete, regenerate)

### Missing Features ❌

**Monetization (0% Complete)**
- ❌ Pricing page (Free vs Starter vs Pro vs Enterprise)
- ❌ Stripe integration (subscription checkout)
- ❌ User dashboard (current plan, usage limits)
- ❌ Usage tracking (chat messages per month)
- ❌ Upgrade/downgrade flows

**Streaming Responses (0% Complete)**
- ❌ Token-by-token streaming display
- ❌ Real-time response rendering

**VPS Deployment (0% Complete)**
- ❌ Production configuration
- ❌ Docker compose for production
- ❌ Nginx reverse proxy configuration
- ❌ SSL certificate setup
- ❌ Environment variable management
- ❌ Database migration scripts
- ❌ Backup strategy

---

## Implementation Plan - Step by Step

### Phase 1: Streaming Responses (Day 1-2)

**Frontend Changes**

1. **Update Chat API Client**
   - File: `frontend/src/lib/api.ts`
   - Add streaming support to `sendMessage`
   - Use `fetch` with `ReadableStream` instead of Axios
   - Implement token-by-token rendering

2. **Update ChatPage Component**
   - File: `frontend/src/pages/ChatPage.tsx`
   - Add streaming message state
   - Implement incremental rendering
   - Show typing indicator during stream

**Backend Changes**

3. **Update Chat Endpoint**
   - File: `backend/api/routes/chat.py`
   - Add `StreamingResponse` from FastAPI
   - Stream Claude API tokens
   - Implement SSE (Server-Sent Events)

---

### Phase 2: Stripe Integration (Day 3-5)

**Backend Setup**

1. **Install Stripe Dependencies**
   ```bash
   cd backend
   pip install stripe
   ```

2. **Create Stripe Service**
   - File: `backend/services/stripe_service.py`
   - Customer management
   - Subscription creation/cancellation
   - Webhook handling

3. **Add Subscription Models**
   - File: `backend/models/subscription.py`
   - `Subscription` model (user_id, plan, status, stripe_subscription_id)
   - `Usage` model (user_id, metric, value, period)

4. **Create Subscription Endpoints**
   - File: `backend/api/routes/subscriptions.py`
   - `POST /subscriptions/create-checkout-session`
   - `POST /subscriptions/webhook` (Stripe webhooks)
   - `GET /subscriptions/current` (user's current plan)
   - `POST /subscriptions/cancel`

5. **Update Main App**
   - File: `backend/main.py`
   - Register subscription routes
   - Add Stripe webhook verification

**Frontend Setup**

6. **Install Stripe.js**
   ```bash
   cd frontend
   npm install @stripe/stripe-js
   ```

7. **Create Pricing Page**
   - File: `frontend/src/pages/PricingPage.tsx`
   - Display 4 tiers: Free, Starter, Pro, Enterprise
   - Feature comparison table
   - "Get Started" buttons

8. **Create Checkout Flow**
   - File: `frontend/src/pages/CheckoutPage.tsx`
   - Stripe Checkout integration
   - Success/cancel handling

9. **Add User Dashboard**
   - File: `frontend/src/pages/AccountPage.tsx`
   - Current plan display
   - Usage statistics (messages this month)
   - Upgrade/downgrade buttons
   - Billing history

10. **Add Subscription Context**
    - File: `frontend/src/context/SubscriptionContext.tsx`
    - Fetch user's subscription
    - Check usage limits
    - Show upgrade prompts

---

### Phase 3: Usage Tracking (Day 6)

**Backend Implementation**

1. **Create Usage Middleware**
   - File: `backend/api/middleware/usage_tracking.py`
   - Track API calls per user
   - Count chat messages
   - Check limits before processing

2. **Update Chat Endpoint**
   - File: `backend/api/routes/chat.py`
   - Increment message counter
   - Return usage headers

**Frontend Implementation**

3. **Display Usage in Dashboard**
   - File: `frontend/src/pages/AccountPage.tsx`
   - Messages sent this month
   - Percentage of plan limit
   - Reset date

---

### Phase 4: VPS Deployment Setup (Day 7-10)

#### Day 7: Environment Configuration

1. **Create Production Environment Files**
   - `.env.production` template
   - Environment variable documentation
   - Secrets management guide

2. **Docker Configuration**
   - `docker-compose.prod.yml`
   - Production-optimized Dockerfiles
   - Multi-stage builds
   - Health check endpoints

3. **Nginx Configuration**
   - `nginx/nginx.conf`
   - Reverse proxy setup
   - SSL/TLS configuration
   - Static file serving
   - WebSocket support (for streaming)

#### Day 8: Database Setup

1. **Production Database Initialization**
   - `scripts/init-db.sh`
   - Automated migrations
   - Backup scripts

2. **Create Backup Strategy**
   - Automated daily backups
   - Point-in-time recovery
   - Off-site backup storage

#### Day 9: SSL & Security

1. **SSL Certificate Setup**
   - Let's Encrypt with Certbot
   - Auto-renewal configuration
   - HTTPS only mode

2. **Security Hardening**
   - CORS configuration
   - Rate limiting
   - API authentication
   - Firewall rules

#### Day 10: Deployment Scripts

1. **Create Deployment Scripts**
   - `scripts/deploy.sh` - Main deployment
   - `scripts/update.sh` - Zero-downtime updates
   - `scripts/rollback.sh` - Emergency rollback

2. **Monitoring Setup**
   - Error tracking (Sentry or similar)
   - Uptime monitoring
   - Performance metrics
   - Log aggregation

3. **Documentation**
   - `docs/DEPLOYMENT.md` - Deployment guide
   - `docs/MAINTENANCE.md` - Maintenance procedures
   - `docs/TROUBLESHOOTING.md` - Common issues

---

## Detailed Implementation Steps

### Step 1: Streaming Responses (Priority: HIGH)

**Backend: `backend/api/routes/chat.py`**

```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Streaming chat endpoint using SSE"""

    async def generate():
        try:
            # RAG retrieval
            chunks = []
            if request.use_rag:
                chunks = await rag_service.retrieve_relevant_chunks(
                    query=request.message,
                    project_id=request.project_id,
                    max_chunks=request.max_context_chunks,
                    min_similarity=request.min_similarity
                )

            # Build context
            context = rag_service.build_context(chunks, request.message)

            # Stream Claude response
            async for token in rag_service.stream_claude_response(
                message=request.message,
                context=context,
                conversation_id=request.conversation_id,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            # Send completion signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Frontend: `frontend/src/pages/ChatPage.tsx`**

```typescript
const handleSendMessage = async () => {
  if (!inputMessage.trim() || sending) return;

  setSending(true);
  const userMessage: ChatMessage = {
    role: 'user',
    content: inputMessage,
    created_at: new Date().toISOString(),
  };

  setMessages(prev => [...prev, userMessage]);

  // Create assistant message placeholder
  const assistantMessage: ChatMessage = {
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString(),
  };
  setMessages(prev => [...prev, assistantMessage]);

  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      },
      body: JSON.stringify({
        message: inputMessage,
        project_id: selectedProjectId,
        conversation_id: selectedConversationId,
        use_rag: useRag,
        max_context_chunks: maxContextChunks,
      }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error('No response body');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') break;

          const parsed = JSON.parse(data);
          if (parsed.token) {
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg?.role === 'assistant') {
                lastMsg.content += parsed.token;
              }
              return updated;
            });
          }
        }
      }
    }
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to send message');
  } finally {
    setSending(false);
    setInputMessage('');
  }
};
```

### Step 2: Stripe Integration (Priority: HIGH)

**Backend: `backend/services/stripe_service.py`**

```python
import stripe
from core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    PRICES = {
        'starter': 'price_starter_id',  # $49/mo
        'professional': 'price_professional_id',  # $149/mo
        'enterprise': 'price_enterprise_id',  # $499/mo
    }

    async def create_checkout_session(
        self,
        user_id: int,
        plan: str,
        success_url: str,
        cancel_url: str
    ) -> str:
        """Create Stripe checkout session"""

        price_id = self.PRICES.get(plan)
        if not price_id:
            raise ValueError(f"Invalid plan: {plan}")

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.email,
            metadata={
                'user_id': str(user_id),
                'plan': plan,
            }
        )

        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhooks"""

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await self.activate_subscription(
                user_id=int(session['metadata']['user_id']),
                plan=session['metadata']['plan'],
                stripe_subscription_id=session['subscription']
            )

        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await self.cancel_subscription(
                stripe_subscription_id=subscription['id']
            )
```

### Step 3: VPS Deployment Configuration (Priority: CRITICAL)

**`docker-compose.prod.yml`**

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:80"
    environment:
      - VITE_API_BASE_URL=https://api.yourdomain.com
    restart: unless-stopped
    networks:
      - knowledgetree-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/knowledgetree
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
    depends_on:
      - db
    networks:
      - knowledgetree-network

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    restart: unless-stopped
    networks:
      - knowledgetree-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  knowledgetree-network:
    driver: bridge

volumes:
  postgres_data:
```

**`nginx/nginx.conf`**

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support for streaming
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name app.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/app.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /usr/share/nginx/html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Success Metrics

### Sprint 4 Features
- ✅ Chat streaming with <1s first token latency
- ✅ Stripe subscriptions working end-to-end
- ✅ Usage tracking accurate
- ✅ Pricing page converts visitors

### VPS Deployment
- ✅ Application deployed on VPS
- ✅ SSL certificates valid
- ✅ Database backups automated
- ✅ Uptime >99.5%
- ✅ Zero-downtime deployments working

### Business Metrics
- ✅ 5 paying Starter users ($245 MRR)
- ✅ Churn rate <20%
- ✅ Average response time <2s
- ✅ 100+ conversations per week

---

## Next Steps After Sprint 4

1. **Monitor Performance**
   - Track error rates
   - Monitor API costs
   - Collect user feedback

2. **Iterate on Features**
   - Improve chat quality
   - Add more export formats
   - Enhance search accuracy

3. **Prepare for Sprint 5**
   - AI-powered insights
   - Document summaries
   - Trend analysis

---

**Status:** Ready to begin Sprint 4 implementation
**Estimated Completion:** 10 days
**Target:** STARTER TIER launch with VPS deployment
