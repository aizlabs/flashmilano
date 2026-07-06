# Website Audio AWS Runbook

This runbook provisions S3-backed website audio at direct public S3 URLs:

```text
https://flashmilano-audio-prod.s3.eu-central-1.amazonaws.com/articles/.../article.mp3
```

Audio scripts and generated audio must come only from the public learner article. Never use
private source text, base article drafts, logs, metrics, prompts, or intermediate private files
as audio input or uploaded audio metadata.

## 1. AWS CLI And Profile Preflight

Run from the repository root:

```bash
aws --version
aws configure list-profiles
aws configure get region
aws sts get-caller-identity
```

Confirm the AWS account, CLI profile, and region before making changes. The S3 bucket is in
`eu-central-1`.

If using a named profile, export it before continuing:

```bash
export AWS_PROFILE=your-profile
```

Set the reusable names:

```bash
export AUDIO_BUCKET=flashmilano-audio-prod
export AUDIO_BUCKET_REGION=eu-central-1
export AUDIO_PUBLIC_BASE_URL=https://flashmilano-audio-prod.s3.eu-central-1.amazonaws.com
export AUDIO_PREFIX=articles
```

## 2. S3 Bucket

Create or reuse the bucket:

```bash
aws s3api head-bucket --bucket "$AUDIO_BUCKET" --region "$AUDIO_BUCKET_REGION" || \
aws s3api create-bucket \
  --bucket "$AUDIO_BUCKET" \
  --region "$AUDIO_BUCKET_REGION" \
  --create-bucket-configuration LocationConstraint="$AUDIO_BUCKET_REGION"
```

Block public ACLs but allow the explicit bucket policy below:

```bash
aws s3api put-public-access-block \
  --bucket "$AUDIO_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false
```

Allow public reads only for article audio objects:

```bash
aws s3api put-bucket-policy \
  --bucket "$AUDIO_BUCKET" \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "PublicReadArticleAudio",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::flashmilano-audio-prod/articles/*"
      }
    ]
  }'
```

Enforce bucket-owner ownership:

```bash
aws s3api put-bucket-ownership-controls \
  --bucket "$AUDIO_BUCKET" \
  --ownership-controls '{
    "Rules": [
      {
        "ObjectOwnership": "BucketOwnerEnforced"
      }
    ]
  }'
```

Enable default encryption:

```bash
aws s3api put-bucket-encryption \
  --bucket "$AUDIO_BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        },
        "BucketKeyEnabled": true
      }
    ]
  }'
```

## 3. Local Environment

Use these local `.env` values for website-ready audio:

```bash
AUDIO_ENABLED=true
AUDIO_UPLOAD_ENABLED=true
AUDIO_PROVIDER=openai
AUDIO_VOICE=alloy
AUDIO_FORMAT=mp3
AUDIO_PUBLIC_BASE_URL=https://flashmilano-audio-prod.s3.eu-central-1.amazonaws.com
AUDIO_S3_BUCKET=flashmilano-audio-prod
AUDIO_S3_REGION=eu-central-1
AUDIO_S3_PREFIX=articles
```

Keep `AUDIO_OUTPUT_PATH=./output/audio` for local working files. `output/audio` must remain
uncommitted.

For the normal one-source publishing workflow, use the wrapper command:

```bash
uv run flashmilano-publish-source private-input/source-1.source.txt
```

It generates A2 and B1 learner posts, enables OpenAI MP3 audio upload, and uses the standard
FlashMilano media defaults above. It still only reads private source files from approved private
input paths.

To generate A2 and B1 learner posts plus local audio artifacts from a private source in one manual
pipeline run:

```bash
AUDIO_ENABLED=true uv run flashmilano-manual --level A2 --level B1 private-input/source-1.source.txt
```

Local audio generation requires `OPENAI_API_KEY`. The command above creates local files under
`output/audio/`, but generated posts will keep `audio: null` unless upload is enabled and a public
audio URL can be built. For website-ready audio during the same run, use the `.env` values above,
including `AUDIO_UPLOAD_ENABLED=true`.

To backfill or regenerate audio for an existing public post, use the post-audio command:

```bash
uv run flashmilano-audio-post output/_posts/YYYY-MM-DD-HHMMSS-slug-level.md \
  --upload \
  --provider openai \
  --voice alloy \
  --format mp3 \
  --public-base-url https://flashmilano-audio-prod.s3.eu-central-1.amazonaws.com \
  --s3-bucket flashmilano-audio-prod \
  --s3-region eu-central-1 \
  --s3-prefix articles
```

This command accepts only public posts under `output/_posts`, derives the narration from the
public learner article body, writes local working files under `output/audio`, uploads to S3 when
`--upload` is set, and updates only the post's public audio front matter.

## 4. Verification

Verify bucket settings:

```bash
aws s3api get-public-access-block --bucket "$AUDIO_BUCKET"
aws s3api get-bucket-policy-status --bucket "$AUDIO_BUCKET"
aws s3api get-bucket-ownership-controls --bucket "$AUDIO_BUCKET"
aws s3api get-bucket-encryption --bucket "$AUDIO_BUCKET"
aws s3 ls "s3://$AUDIO_BUCKET/$AUDIO_PREFIX/"
```

After uploading an article audio file, verify delivery:

```bash
curl -sS -o /dev/null -w "HTTP %{http_code} (%{content_type})\n" \
  "$AUDIO_PUBLIC_BASE_URL/articles/YYYY/MM/article-slug/article.mp3"
```

Expected: `HTTP 200 (audio/mpeg)`.

## 5. Future CDN Option

CloudFront can be added later for lower latency and a custom media domain. If that happens, keep
the same S3 bucket and object keys, create a CloudFront distribution in front of the bucket, then
change `AUDIO_PUBLIC_BASE_URL` and existing post front matter to the new CDN base URL.
