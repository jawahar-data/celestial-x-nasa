# CELESTIAL X 2.0 — Production Cloud Deployment & Custom Domain Guide
### NASA Space Apps Challenge 2026

This guide provides instructions for deploying **CELESTIAL X 2.0** to production cloud platforms (Google Cloud Run / Streamlit Community Cloud) and mapping your custom domain (purchased on **GoDaddy**, e.g., `www.celestialx.com`).

---

## 1. Cloud Deployment Options

### Option A: Google Cloud Run (Recommended for Scalability & High Traffic)
Google Cloud Run provides a serverless container environment with autoscaling, custom domain SSL termination, and low latency.

#### Prerequisites:
1. Google Cloud SDK (`gcloud`) installed.
2. Google Cloud project created with billing enabled.

#### Step-by-Step Deployment:
```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project <YOUR_GCP_PROJECT_ID>

# 2. Enable Required GCP APIs
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com

# 3. Store API Secrets in Secret Manager
echo -n "YOUR_NASA_API_KEY" | gcloud secrets create NASA_API_KEY --data-file=-
echo -n "YOUR_METEOMATICS_USERNAME" | gcloud secrets create METEOMATICS_USERNAME --data-file=-
echo -n "YOUR_METEOMATICS_PASSWORD" | gcloud secrets create METEOMATICS_PASSWORD --data-file=-

# 4. Build and Deploy Container to Cloud Run
gcloud run deploy celestial-x-nasa \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --set-secrets NASA_API_KEY=NASA_API_KEY:latest \
    --set-secrets METEOMATICS_USERNAME=METEOMATICS_USERNAME:latest \
    --set-secrets METEOMATICS_PASSWORD=METEOMATICS_PASSWORD:latest
```

---

### Option B: Streamlit Community Cloud (Quickest Public Showcase)
1. Fork or push this repository to GitHub: `https://github.com/<YOUR_USER>/celestial-x-nasa`.
2. Navigate to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account and click **New app**.
4. Select repository: `celestial-x-nasa`, branch: `main`, main file path: `app.py`.
5. Under **Advanced Settings** -> **Secrets**, paste your API credentials:
   ```toml
   NASA_API_KEY = "YOUR_NASA_KEY"
   METEOMATICS_USERNAME = "YOUR_METEOMATICS_USER"
   METEOMATICS_PASSWORD = "YOUR_METEOMATICS_PASS"
   ```
6. Click **Deploy!**

---

## 2. GoDaddy Custom Domain Setup (e.g., `www.celestialx.com`)

To map your custom domain purchased on GoDaddy to your deployed CELESTIAL X application:

### Step 1: Map Domain in Cloud Run Console
1. In Google Cloud Console, navigate to **Cloud Run** > **Custom Domains** (or **Manage Custom Domains**).
2. Click **Add Mapping**.
3. Select service: `celestial-x-nasa`.
4. Enter your custom domain (e.g. `www.celestialx.com` or apex `celestialx.com`).
5. Cloud Run will display the exact DNS records to add into GoDaddy.

---

### Step 2: Configure GoDaddy DNS Zone
1. Log in to your **GoDaddy Domain Portfolio** at [dcc.godaddy.com](https://dcc.godaddy.com).
2. Click your domain name -> Click **DNS** or **Manage DNS**.
3. In the **DNS Records** table, add or edit the following records:

#### A. Subdomain Mapping (`www.celestialx.com`):
| Type | Name / Host | Value / Points To | TTL |
| :--- | :--- | :--- | :--- |
| **CNAME** | `www` | `ghs.googlehosted.com.` | 1 Hour (or 1/2 hour) |

#### B. Apex Root Domain Mapping (`celestialx.com`):
Add the four Google Cloud Anycast IPv4 records:
| Type | Name / Host | Value / Points To | TTL |
| :--- | :--- | :--- | :--- |
| **A** | `@` | `216.239.32.21` | 1 Hour |
| **A** | `@` | `216.239.34.21` | 1 Hour |
| **A** | `@` | `216.239.36.21` | 1 Hour |
| **A** | `@` | `216.239.38.21` | 1 Hour |

And the four IPv6 records:
| Type | Name / Host | Value / Points To | TTL |
| :--- | :--- | :--- | :--- |
| **AAAA** | `@` | `2001:4860:4802:32::15` | 1 Hour |
| **AAAA** | `@` | `2001:4860:4802:34::15` | 1 Hour |
| **AAAA** | `@` | `2001:4860:4802:36::15` | 1 Hour |
| **AAAA** | `@` | `2001:4860:4802:38::15` | 1 Hour |

---

### Step 3: SSL Certificate Provisioning
- Google Cloud automatically provisions an authorized, renewed **Let's Encrypt / Google Trust Services SSL Certificate** for your domain once DNS propagation completes.
- Propagation typically completes within 15–45 minutes worldwide.
- Verify status: `https://www.celestialx.com`.

---

## 3. Local Verification & Docker Run
To build and test the production Docker container locally before deploying:

```bash
# Build local container
docker build -t celestial-x-nasa:local .

# Run container on port 8080
docker run -p 8080:8080 \
  -e NASA_API_KEY="YOUR_KEY" \
  celestial-x-nasa:local

# Open in browser
# http://localhost:8080
```
