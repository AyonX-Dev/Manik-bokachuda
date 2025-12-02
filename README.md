# 🔄 Blogger Sitemap → Auto Decode → Playlist Extractor  
## 📡 Auto GitHub Push + 📢 Telegram Notifications  
Automated system for extracting **Title**, **Thumbnail**, and **Decoded Playlist URL** from Blogger posts listed inside a **sitemap.xml** — and pushing results to GitHub + sending notifications to Telegram channel.

---

# 🚀 Features

✔ Fetches sitemap:  
``https://www.streamecho.top/sitemap.xml``

✔ For each new `<loc>` page:  
- Fetches page HTML (Blogger compatible)  
- Extracts **Post Title**  
- Extracts **Thumbnail (og:image / twitter:image / itemprop=image / first <img>)**  
- Extracts `data-encrypted="..."` value  
- Decodes Base64 (same logic as HTML decoder tool)  
- Detects playlist links (`.m3u8`, `.m3u`, `.mpd`, `.mp4`, `.ts`, `.aac`)  

✔ Saves results into:  
- `decoded_results.txt` (auto updated)  
- `sitemap_urls.txt` (tracks already scanned posts)  
- `found_playlists.txt` (tracks extracted playlist links)

✔ Posts to **Telegram channel** automatically.  
✔ Runs automatically **every day** + manual workflow trigger.

---

# 📂 Folder Structure

```
your-repo/
  scripts/
    process_sitemap.py
  .github/
    workflows/
      sitemap-watch.yml
  sitemap_urls.txt
  found_playlists.txt
  decoded_results.txt   (auto generated)
  README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone or create a GitHub repository

```
git clone https://github.com/yourname/yourrepo.git
cd yourrepo
```

---

## 2️⃣ Create required files

### Create tracker files (empty):

```
echo "# sitemap urls collected by actions" > sitemap_urls.txt
echo "# found playlist urls" > found_playlists.txt
```

---

## 3️⃣ Add project structure

Create directory:
```
mkdir -p scripts
mkdir -p .github/workflows
```

Now place these two files:

### 📌 `scripts/process_sitemap.py`  
(Full script provided in project. Handles: sitemap read, Blogger parsing, decoding, playlist extraction.)

### 📌 `.github/workflows/sitemap-watch.yml`  
(Workflow that runs daily, commits results, sends Telegram message.)

---

## 4️⃣ Add, Commit and Push

```
git add .
git commit -m "Initial commit: Added sitemap processor + workflow"
git push
```

---

# 🔑 Setup GitHub Secrets (IMPORTANT)

Go to:

**Repo → Settings → Secrets and variables → Actions**

Create these secrets:

| Secret Name | Value |
|------------|--------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram BotFather token |
| `TELEGRAM_CHAT_ID`   | Your Telegram Channel ID (e.g., -1001234567890) |

👉 If your **main branch has protection rules** and GitHub Actions cannot push, then also create:

| Secret Name | Value |
|-------------|--------|
| `PUSH_TOKEN` | A GitHub Personal Access Token (classic) with `repo` permission |

Workflow will automatically use `PUSH_TOKEN` when available.

---

# ▶️ Running the Workflow

You can run it manually:

```
GitHub → Actions → “Sitemap → Decode → GitHub + Telegram” → Run workflow
```

Or it will run automatically every day at 01:00 UTC.

---

# 📦 Output Files

### `decoded_results.txt`
Contains:
```
Post Title
Thumbnail URL
Decoded Playlist URL
Post URL
---
```

### `/tmp/new_posts.txt`
Temporary file used to generate Telegram messages.

### `found_playlists.txt`
All unique playlist links.

### `sitemap_urls.txt`
All processed `<loc>` entries from sitemap.

---

# 📢 Telegram Message Format

Each new item is posted like:

```
<b>Post Title</b>
Thumbnail: https://example.com/image.jpg
Playlist: <code>https://example.com/live.m3u8</code>
Source: https://www.streamecho.top/2025/11/.../auto.html
```

HTML formatting is supported because `parse_mode="HTML"` is used.

---

# 🛠 Troubleshooting

### ❌ Workflow not pushing to GitHub  
✔ Enable `GITHUB_TOKEN` write permission  
✔ OR add `PUSH_TOKEN` secret (PAT token)  
✔ Disable branch protection OR allow GitHub Actions to bypass

---

### ❌ Telegram not receiving messages  
✔ Check bot is admin in channel  
✔ Correct chat_id (starts with `-100...`)  
✔ Check bot token validity

---

### ❌ Thumbnail not detected  
Blogger sometimes loads images via JS.  
Script tries multiple methods:
- og:image
- twitter:image
- itemprop=image
- link rel=image_src
- first <img>
- noscript fallback

---

# ❤️ Credits

Automated playlist extractor system developed to replicate browser-based decoder logic into a server-side GitHub Action environment with Blogger compatibility.

---

# ✔️ Ready To Go

You can now copy this README.md into your repository.
