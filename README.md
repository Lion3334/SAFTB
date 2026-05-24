# SAFTB Lifetime Leaderboard

A beach volleyball scorekeeping web app for tracking individual player stats, lifetime records, and head-to-head matchups.

## Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) account (free tier)
- A [GitHub](https://github.com) repository
- A [Streamlit Community Cloud](https://streamlit.io/cloud) account (free tier)

---

## 1. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com).
2. In your project dashboard, go to **SQL Editor**.
3. Paste and run the contents of [`schema.sql`](schema.sql). This creates the `players` and `games` tables.
4. In **Project Settings → API**, copy:
   - **Project URL** (looks like `https://xxxx.supabase.co`)
   - **anon / public** key

---

## 2. Configure Secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and fill in:

```toml
supabase_url = "https://your-project-id.supabase.co"
supabase_anon_key = "your-anon-key-here"
admin_password = "choose-a-strong-password"
```

> `secrets.toml` is gitignored. Never commit it.

---

## 3. Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## 4. Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (make sure `secrets.toml` is **not** committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your GitHub repo, branch (`main`), and set the main file to `app.py`.
4. Under **Advanced settings → Secrets**, paste the contents of your `secrets.toml`.
5. Click **Deploy**. Streamlit will install dependencies and launch the app.

---

## File Structure

```
/
├── app.py                        # Main Streamlit app
├── db.py                         # Supabase client + all DB queries
├── stats.py                      # Stat calculation logic (pure Python)
├── schema.sql                    # Run once in Supabase SQL editor
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── secrets.toml              # gitignored — your credentials
│   └── secrets.toml.example     # safe to commit — template
└── README.md
```

---

## Notes

- **Tie scores** (equal scores) count as neither a win nor a loss for either team.
- The leaderboard auto-refreshes every 60 seconds after a game is logged.
- Stat calculations run in Python from raw game data — no SQL views required.
