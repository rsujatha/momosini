# Deploy to Google Cloud Run (from scratch)

The whole app — the FastAPI web layer, the one ADK agent, and the bundled stdio MCP server —
ships as **one container**. The agent spawns the MCP server as a local subprocess, so there is
no second service to stand up. These steps assume you are starting with **no GCP account**.

Deployed model: **DeepSeek** (`ADK_MODEL=deepseek/deepseek-chat`, via LiteLlm). The only secret
the container needs at runtime is `DEEPSEEK_API_KEY`, injected by Cloud Run from Secret Manager —
never baked into the image (`.dockerignore` keeps `.env` out).

> One critical setting: the backend keeps onboarding sessions **in memory**, and Cloud Run is
> serverless. Deploy with **`--max-instances=1`** so a live conversation is never split across
> two instances. (`--min-instances=1` keeps one instance warm for a smooth demo — optional, see
> the cost note at the end.)

---

## 0. One-time account setup

1. Create/sign in to a Google account, then go to <https://console.cloud.google.com> and accept
   the terms. New accounts get a **$300 free trial credit**; Cloud Run also has an always-free
   monthly tier.
2. **Enable billing** (required even on the free tier): Console → Billing → link a billing
   account. Nothing here will bill meaningfully at demo scale.
3. **Install the gcloud CLI:** <https://cloud.google.com/sdk/docs/install> (macOS: `brew install
   --cask google-cloud-sdk`). Then authenticate:
   ```bash
   gcloud auth login
   ```

## 1. Create a project and pick a region

```bash
# Pick any globally-unique id (lowercase, digits, hyphens).
export PROJECT_ID="mom-day-organiser-$(date +%s)"
export REGION="us-central1"          # any Cloud Run region is fine
export SERVICE="mom-day-organiser"

gcloud projects create "$PROJECT_ID"
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
```

If you have more than one billing account, link it explicitly:
```bash
gcloud billing accounts list
gcloud billing projects link "$PROJECT_ID" --billing-account=XXXXXX-XXXXXX-XXXXXX
```

## 2. Enable the APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## 3. Store the DeepSeek key in Secret Manager

Never pass the key in shell history or bake it into the image. Create the secret from a prompt
(piped in, so it is not echoed):

```bash
printf '%s' 'PASTE_YOUR_DEEPSEEK_KEY' | gcloud secrets create deepseek-key --data-file=-
```

Grant the Cloud Run runtime service account permission to read it:

```bash
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
gcloud secrets add-iam-policy-binding deepseek-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 4. Deploy

`--source .` lets Cloud Build build the image from `deploy/Dockerfile` and push it for you
(it auto-creates an Artifact Registry repo on first run). Run this from the **repo root**:

```bash
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --max-instances=1 \
  --min-instances=1 \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars=ADK_MODEL=deepseek/deepseek-chat \
  --set-secrets=DEEPSEEK_API_KEY=deepseek-key:latest
```

> If gcloud asks which Dockerfile to use, point it at `deploy/Dockerfile`. To be explicit you can
> instead build first: `gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE/app" .`
> then `gcloud run deploy "$SERVICE" --image ...` with the same flags.

On success gcloud prints a **Service URL** (`https://mom-day-organiser-XXXX.a.run.app`). Open it —
the tracker UI loads at `/`, and onboarding drives `/converse`.

## 5. Verify

```bash
URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
curl -sS "$URL/" | head -c 200          # should return the tracker HTML
```
Then open `$URL` in a browser and complete an onboarding conversation end to end.

## 6. Update after a code change

Re-run the **same** `gcloud run deploy --source .` command from step 4. Each deploy is a new
revision; traffic shifts to it automatically.

## 7. Teardown (stop all costs)

```bash
gcloud run services delete "$SERVICE" --region "$REGION"
# or remove everything:
gcloud projects delete "$PROJECT_ID"
```

---

## Cost note

`--min-instances=1` keeps one instance always warm (no cold-start lag during a demo) but you are
billed for that idle instance — typically a few dollars a month at this size, often inside the
free tier. To minimise cost outside demo windows, redeploy with `--min-instances=0`; keep
`--max-instances=1` regardless, since that is the flag protecting in-memory sessions.

## Security checklist before sharing the URL

- `DEEPSEEK_API_KEY` is in Secret Manager, **not** in the image or repo (`.env` is gitignored and
  in `.dockerignore`).
- The service is `--allow-unauthenticated`, so anyone with the URL can use the agent and spend
  your DeepSeek quota. Fine for a judged demo; delete or lock down the service afterward.
- Personal data still stays in the parent's browser (localStorage); only `age_months` reaches a
  knowledge tool. The deployment does not change the privacy model.
