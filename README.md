# Buko Bantay

Buko Bantay ("coconut guardian") is a web app that checks photos of coconut leaves and tells the user whether the leaf looks healthy or shows one of three problems, with practical, referenced advice for each. It works in **English, Filipino and Bikol** and can be installed on a phone as a PWA.

> **Decision support, not a diagnosis.** Pesticide and fungicide products, rates and legal status differ between countries, and many of the cited sources are from India. Confirm any chemical treatment with a local agricultural technician and follow the product label.

## What it detects

| Class | Meaning |
|---|---|
| Caterpillar damage | Coconut black-headed caterpillar (*Opisina arenosella*) |
| Gray leaf spot | Grey blight (*Pestalotiopsis palmarum*) |
| Leaf rot | Fungal leaf rot disease complex |
| Healthy leaf | No problem detected |

The model was tested on 132 leaf photos: 97.7% accurate overall, but it missed 3 of 9 healthy leaves. If it reports a disease on a leaf that looks healthy, double-check before treating.

## How the app works

1. **Sign in.** Users register with an email and password (or log in with an older username). Passwords are stored only as bcrypt hashes, and accounts lock for 5 minutes after 5 failed attempts.
2. **Stay signed in.** After login the browser stores a random session token (not the password) in its localStorage. On refresh the app reads the token and signs the user back in. Tokens last 30 days and are invalidated on log out. The server stores only a SHA-256 hash of each token.
3. **Scan a leaf.** On the Scan page the user takes a photo or uploads one.
4. **Quality check.** Blurry, too dark, or washed-out photos are rejected before classification, with a message asking the user to retake the photo.
5. **Classify.** The photo is resized to 256x256 and run through a TensorFlow Lite model.
6. **Show the result.** The app shows the predicted class, the confidence, advice with numbered references, and a disclosure. If confidence is below the chosen strictness (90%, 80% or 65%), it shows an "unclear photo" warning and **no recommendation**.
7. **Dashboard.** Each scan is saved with its result, time, confidence and a small thumbnail. The Home page shows totals, a health breakdown, the most common issue, and recent scans.
8. **Local storage.** Scan history is saved in the browser's localStorage, separately for each account, so it survives refreshes and restarts. It keeps the latest 50 scans per account because browsers allow only about 5 MB. Only a small thumbnail of each photo is stored, not the full image.

## Project files

| File | Purpose |
|---|---|
| `app.py` | Gradio app: pages, navigation, login flow, scanning, browser storage |
| `auth.py` | Accounts (SQLite `users.db`), password hashing, login lockout, session tokens, theme and avatar helpers |
| `dashboard.py` | Scan records, thumbnails and the dashboard page |
| `quality.py` | Blur and brightness checks for uploaded photos |
| `i18n.py` | English / Filipino / Bikol texts and result page builder |
| `strings.py` | Extra UI strings (accounts, photo-quality messages) |
| `recommendations.py` | Advice text and numbered source list |
| `requirements.txt` | Python libraries with pinned versions |
| `coconut_leaf_model.tflite` | Trained TFLite model (**you must supply this**) |
| `class_names.txt` | One class name per line, in the model's output order (**you must supply this**) |

`users.db` (and an `avatars/` folder, if profile pictures are used) are created automatically next to the app.

## Installation

**Requirements:** a recent Python 3 (3.10 or newer is recommended) and `pip`.

1. **Get the files.** Put all the files above in one folder, including `coconut_leaf_model.tflite` and `class_names.txt`.

2. **Create a virtual environment (recommended).**

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install the libraries.** `requirements.txt` lists the exact versions the app was built with.

   ```bash
   pip install -r requirements.txt
   ```

4. **Set the storage secret.** The browser data (session token and scan history) is encrypted with this value. Choose a long random string and keep it the same between runs, or saved data becomes unreadable after a restart.

   ```bash
   # macOS / Linux
   export BUKO_SECRET="put-a-long-random-string-here"
   # Windows (PowerShell)
   $env:BUKO_SECRET = "put-a-long-random-string-here"
   ```

   If it is not set, the app falls back to a placeholder value. That is fine for testing but not for real use.

5. **Run the app.**

   ```bash
   python app.py
   ```

6. **Open it** at `http://localhost:7860`. To use another port, set `PORT` (for example `PORT=8080 python app.py`). The app listens on all network interfaces, so on the same Wi-Fi it can be opened from a phone at `http://<your-computer-ip>:7860`.

### Install on a phone (PWA)

Open the app in the phone's browser and choose **Add to Home Screen** (or **Install app**). Note that browsers generally require HTTPS for installing and for camera access, except on `localhost`, so a real deployment should be served over HTTPS.

## Configuration and tuning

- **Warning strictness** (Settings page): 90%, 80% or 65% confidence cut-off for the unclear-photo warning.
- **Photo-quality thresholds:** `BLUR_MIN`, `DARK_MAX` and `BRIGHT_MIN` at the top of `quality.py`. Print the measured values for your own photos with:

  ```bash
  python quality.py photo.jpg
  ```
- **History size:** `MAX_RECORDS` in `dashboard.py`.
- **Session length:** `SESSION_DAYS` in `auth.py`.
- **List registered accounts:** `python auth.py list`

## Troubleshooting

- **Logged out after every restart, or history disappears:** `BUKO_SECRET` changed or is not set to the same value each run.
- **`FileNotFoundError` for the model or class names:** `coconut_leaf_model.tflite` and `class_names.txt` must sit next to `app.py`.
- **Good photos rejected as blurry or dark:** adjust the thresholds in `quality.py`.
- **Camera does not open:** the browser needs HTTPS (or `localhost`) and camera permission.
- **History is lost:** it lives in that browser's localStorage, so clearing site data or switching browsers or devices starts fresh.

## Notes

- Filipino and Bikol texts are shortened versions of the English advice and should be reviewed by a native speaker.
- Advice is tied to the numbered references shown with each result; edit it in `recommendations.py` and keep the source numbers in step.
