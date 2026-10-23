# Setting up the Website Health Report Reminder in Coolify

This guide walks through installing the **health‑check** script and updating the existing `hosting‑renewal‑reminders.py` that lives in the `scripts/pyrunner` folder of your AI‑OS repository.

You can keep this file in the repository so you can open it at any time.

---

## 1️⃣  Folder structure

```text
AI‑OS/                     ── root of your repo
│   ├─ scripts/
│   │   └─ pyrunner/
│   │        ├─ hosting‑renewal‑reminders.py   ← your original reminder script
│   │        └─ health_check.py                ← **new file** (add this)
│   └─ docs/
│         └─ Setup/
│               └─ health‑report‑setup.md      ← *this file*
```

*If you’re using a different clone (e.g. `aios-pyrunner`), put the two files in that repo’s `scripts/pyrunner/` folder instead.*

---

## 2️⃣  Add the health‑check script

1. Open the file `./scripts/pyrunner/health_check.py`.  If it does not exist, create it.
2. Copy the entire content of the script (provided above in the conversation) into that file.
3. Save.

---

## 3️⃣  Update `hosting‑renewal‑reminders.py`

1. Open `./scripts/pyrunner/hosting‑renewal‑reminders.py`.
2. Any section that builds the email body should be replaced with the new implementation shared earlier (importing `health_check`, appending the HTML body, attaching the plain‑text summary).
3. The file **already contains** the updated logic; just double‑check that the following lines appear at the top:
   ```python
   from health_check import health_check as run_health_check, render_html
   HAS_HEALTH_CHECK = True
   ```
4. Save.

---

## 4️⃣  Commit & Push

```bash
# In VS Code: Source Control → Stage the two files → Commit
# Or from terminal
cd /Users/banksdada/Desktop/AI_OS

git add scripts/pyrunner/health_check.py scripts/pyrunner/hosting-renewal-reminders.py

git commit -m "Add health‑check routine and update renewal email"

git push origin main  # or your default branch
```

---

## 5️⃣  Configure Coolify environment

1. Go to the Coolify dashboard → *Your Project* → **Environment**.
2. Add the following variables for the `pyrunner` service (or the service you’re using):
   ```text
   DRY_RUN                      true
   SENDER_NAME                   Webawesome Consult UK
   GMAIL_ADDRESS                 your‑account@example.com
   GMAIL_APP_PASSWORD            <app‑password>
   BANK_ACCOUNT_NAME             Accounts Payable – Webawesome
   BANK_NAME                     Monzo
   BANK_SORT_CODE                12‑34‑56
   BANK_ACCOUNT_NUMBER           12345678
   REPLY_TO                      your‑account@example.com
   INCLUDE_HEALTH_REPORT         true
   WP_SITES = [
     {
       "url": "https://your‑site.com",
       "user": "aios",
       "app_password": "xxxx xxxx"
     }
     // add more entries for all your WordPress sites
   ]
   ```
3. Click **Save**.

---

## 6️⃣  Verify with a dry‑run

```bash
cd scripts/pyrunner
DRY_RUN=true python3 hosting-renewal-reminders.py
```

You should see in the logs messages like:

```
[DRY RUN] Would send email to client@example.com
```
and a JSON block printed that represents the health report.

If everything looks good, change `DRY_RUN` back to `false` in the environment and the real emails will start shipping.

---

## 7️⃣  Next steps

* Add new client rows to your Google‑Sheet (used by the reminder script).
* Check the “Sent” folder of the Gmail account you used in `GMAIL_ADDRESS` to verify the email format.
* Monitor the Coolify logs for any errors and troubleshoot as needed.

---

**TL;DR**

* Create `scripts/pyrunner/health_check.py` with the provided code.
* Update `hosting-renewal-reminders.py` to import it and prepend the report to the email.
* Commit & push the changes.
* Set the Coolify environment variables above.
* Run a dry‑run and then set `DRY_RUN=false`.

Good luck – let me know if any step needs further clarification!