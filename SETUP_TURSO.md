# Tetco RDO — Turso (libSQL) live-edit setup

This site uses [Turso](https://turso.tech) — a hosted, SQLite-compatible
database — so that edits to the **Universities** list persist and are
visible to every visitor anywhere in the world.

## What's in this folder

| File | What to do with it |
|---|---|
| `index.html` | The site. Edit `TURSO_URL` + `TURSO_AUTH_TOKEN` near the bottom, then push to GitHub. |
| `schema.sql` | One-time seed for your Turso DB (creates the table + 48 universities). |
| `build_universities_db.py` | Optional — rebuilds a local SQLite snapshot from `index.html`. Not used by the live site anymore. |
| `universities.sqlite` | Optional — the local SQLite snapshot. Not used by the live site anymore. |
| `push.sh` | Optional helper to clone the repo and push your changes. |

## ⚠️ Security model — read first

You chose **"anyone who visits the site can edit"**. That means:

- The Turso auth token has to live in the publicly-readable JavaScript.
- Anyone can view-source, copy the token, and write to your DB directly.
- Bots/scrapers that find the token can wipe data, fill it with junk, or
  burn through your Turso free-tier limits.

**Mitigations baked in:**
- The page exposes a "↺ Reset Data" button (top of the Universities list)
  that wipes the table and re-seeds the original 48 rows. Anyone can
  press it, but it's also your way to recover from vandalism.
- If Turso is unreachable or the token is wrong, the page falls back to
  the inline 48-row dataset and still works (read-only client-side).

**Strongly recommended:** use a fresh Turso DB just for this demo. Don't
reuse a token that has access to anything else.

## One-time setup (≈5 minutes)

### 1. Create a Turso account + database
1. Sign up at https://turso.tech — free, no credit card.
2. Install the Turso CLI on your Mac:
   ```bash
   brew install tursodatabase/tap/turso
   turso auth login
   ```
3. Create the database:
   ```bash
   turso db create tetco-rdo
   ```
4. Open the SQL shell on it and paste the contents of `schema.sql`:
   ```bash
   turso db shell tetco-rdo < schema.sql
   ```
   You should see no errors. Verify:
   ```bash
   turso db shell tetco-rdo "SELECT COUNT(*) FROM universities"
   ```
   Expected: `48`.

### 2. Get the URL and auth token
```bash
turso db show tetco-rdo --url
# → libsql://tetco-rdo-<your-org>.turso.io     ← copy this

turso db tokens create tetco-rdo
# → eyJhbGciOi...                              ← copy this
```

### 3. Paste them into `index.html`
Open `index.html`, search for `TURSO_URL`, and replace the two lines:

```js
const TURSO_URL        = 'libsql://YOUR-DATABASE-NAME.turso.io';
const TURSO_AUTH_TOKEN = 'YOUR_TURSO_AUTH_TOKEN_HERE';
```

with your actual values:

```js
const TURSO_URL        = 'libsql://tetco-rdo-yourname.turso.io';
const TURSO_AUTH_TOKEN = 'eyJhbGciOi...your full token...';
```

Save.

### 4. Push to GitHub Pages
- **GUI route**: GitHub Desktop → drag the new `index.html` over the existing one → commit → push.
- **Terminal route**:
  ```bash
  cd /path/to/local/clone/of/tetco
  cp "/Users/.../tetco-update/index.html" index.html
  git add index.html
  git commit -m "Wire universities list to Turso live DB"
  git push
  ```
  (You don't need to push `universities.sqlite` anymore — the live site
  reads from Turso instead.)

### 5. Verify
1. Open https://calx-ksa-sa.github.io/tetco/ (give GitHub Pages ~1 min to rebuild).
2. Open DevTools → Console. You should see:
   `[RDO] Loaded 48 universities from Turso`
3. Click any university → ✏️ Edit → change a name → Save. Console:
   `[RDO] Turso UPDATE id=X OK`
4. Open the same URL on your phone or another browser — your edit is there.

## Day-to-day

- **Edit a university:** open it in the app, click ✏️, save. Live for everyone.
- **Delete a university:** open it, click 🗑️, confirm. Gone for everyone.
- **Reset everything:** click "↺ Reset Data" at the top of the Universities list.
- **Run ad-hoc SQL from the browser console:**
  ```js
  await rdoQuery("SELECT name_en, postdoc_r FROM universities WHERE postdoc_r > 0 ORDER BY postdoc_r DESC")
  ```

## When things break

| Symptom in console | What it means | Fix |
|---|---|---|
| `Using inline UNI_DATA fallback — Turso not configured` | You forgot to paste your URL/token. | Edit `index.html`, fill them in, push again. |
| `Turso save failed: 401` or `403` | Token wrong or expired. | `turso db tokens create tetco-rdo` again, paste the new token. |
| `Turso save failed: not found` | Wrong DB URL. | `turso db show tetco-rdo --url` and re-paste. |
| Vandalism — bad data showing | Someone wrote junk via the public token. | Click "↺ Reset Data" on the Universities list. |

## Rotating the token

If you ever leak the token (e.g. by accidentally pasting it in chat),
rotate it immediately:

```bash
turso db tokens invalidate tetco-rdo            # kill all old tokens
turso db tokens create tetco-rdo                # mint a fresh one
# → paste the new token into index.html, push
```

That's it.

---

# Email notifications for @mentions (EmailJS)

The comment box now supports `@mentions` — type `@` and pick a person from
the team or stakeholder list. When you post the comment, every mentioned
person gets an email with the comment text and a link to the page.

**This is optional.** If you skip the EmailJS setup below, the page still
works — but instead of sending automatically, it will open your computer's
default mail app with the recipients and message pre-filled, and you click
"Send" yourself. That's the `mailto:` fallback.

## Why EmailJS

- Free tier: 200 emails/month, no credit card.
- Sends from your own Gmail / Outlook / SMTP without a backend.
- Three IDs paste into `index.html`, that's it.

## Setup (≈5 minutes)

### 1. Sign up
Go to https://www.emailjs.com and create a free account.

### 2. Add an email service
Dashboard → "Email Services" → "Add New Service".
Pick Gmail (easiest) or Outlook or any SMTP provider you control.
Authorize it. Copy the **Service ID** (e.g. `service_abc1234`).

### 3. Create a template
Dashboard → "Email Templates" → "Create New Template".
Set the template variables to match what `index.html` sends:

- **To Email:** `{{to_email}}`
- **From Name:** `{{from_name}}`
- **Subject:** `{{subject}}`
- **Content / HTML:**
  ```
  Hi {{to_name}},

  {{from_name}} mentioned you in a comment on {{context_type}} —
  "{{context_title}}".

  Comment:
  "{{comment_text}}"

  Open it: {{page_url}}

  — RDO Research Management Platform
  ```

Save. Copy the **Template ID** (e.g. `template_xyz5678`).

### 4. Get your Public Key
Dashboard → "Account" → "General". Copy the **Public Key**
(e.g. `aBcDeFgHiJkLmNoPq`).

### 5. Paste the three IDs into `index.html`
Search for `EMAILJS_PUBLIC_KEY` near the bottom of the file. Replace:

```js
const EMAILJS_PUBLIC_KEY  = 'YOUR_EMAILJS_PUBLIC_KEY';
const EMAILJS_SERVICE_ID  = 'YOUR_EMAILJS_SERVICE_ID';
const EMAILJS_TEMPLATE_ID = 'YOUR_EMAILJS_TEMPLATE_ID';
```

with your actual values. Save and push.

### 6. Test
1. Open the live site.
2. Click any record → scroll to "Comments & Feedback".
3. Type `@` — the people picker pops up.
4. Pick a name from the list (you, ideally — easiest to verify).
5. Add some text and click Post.
6. Check the recipient's inbox within a minute.
7. Browser console should say: `[RDO] EmailJS sent 1 notifications`.

If EmailJS fails for any reason, you'll see
`EmailJS unavailable — ... — falling back to mailto`
and the system will open your mail app instead. Either way the comment
itself is saved.

## Lock down the public key

The EmailJS public key is in your page source, like all client-side keys.
EmailJS lets you restrict use by domain — strongly recommended:

Dashboard → "Account" → "Security" → add `calx-ksa-sa.github.io` as the
only allowed domain. Now scrapers grabbing your key from `view-source`
can't use it from anywhere else.

## Adding people to the @mention pool

The picker pulls from two pools:

1. **Team Members** (`Team` icon → "Add Member") — must have a valid email,
   the form now requires it.
2. **Stakeholders** (`Stakeholders` register) — picked up automatically
   when their `contact` field is an email.

Anyone added via the in-app form is immediately mentionable.
