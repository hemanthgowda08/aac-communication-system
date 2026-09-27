# PRJ_213 — Development of Augmentative and Alternative Communication in Indian Context

**Saathi AAC** is an accessible communication board for people who communicate more easily with visual symbols, words, and phrases. It is designed for use by a communicator, family member, teacher, or support worker on a phone, tablet, or computer.

## Problem statement

Design and develop a solution for development of Augmentative and Alternative Communication (AAC) in the Indian context using modern technologies to improve performance, automation, security, scalability, and real-world usability.

## Motivation and objectives

Speech can be inaccessible or unreliable for many people. Saathi provides a touch-friendly way to assemble a message, speak it using the device, and keep useful phrases available. The project prioritizes reliable basic communication, Indian-language vocabulary, practical personalization, privacy, and a working offline board.

## Features

- AAC categories and symbol tiles for needs, feelings, people, places, actions, health, food and social communication.
- Sentence builder with per-word removal, undo, clear, Speak/Stop, and phrase saving.
- Browser speech synthesis with `en-IN`, `hi-IN`, and `kn-IN` locale selection, voice matching, and a supported-voice fallback.
- Deterministic next-word recommendations for “I want”, “I need”, and “I am”, plus frequently used catalog words and saved-phrase recommendations.
- English, Hindi, and Kannada interface and AAC labels, with translated starter phrases.
- Accessible settings for language, speed, high contrast, larger text, and favorite categories.
- Flask REST API and SQLite persistence for catalog data, saved phrases, preferences, and item/phrase usage.
- Browser local storage fallback and a PWA service worker that caches the app shell and catalog for reopening offline.
- Web Bluetooth connection/send path for BLE devices implementing the Nordic UART Service, and a clearly labeled wireless simulation mode.

## Technology stack

- **Frontend:** React 18, Vite, JavaScript, CSS, Lucide icons.
- **Backend:** Python 3, Flask, Waitress WSGI server.
- **Database:** SQLite with foreign keys and parameterized statements.
- **Speech:** browser/device Web Speech API; no paid speech service.
- **Wireless:** browser Web Bluetooth GATT API (optional; secure context and compatible BLE UART device required).
- **Offline:** service worker, Cache Storage, local AAC catalog bundled with the frontend, and localStorage.

## Architecture and workflow

The React board loads its bundled catalog immediately, so sentence building, speech, and deterministic fallback suggestions do not depend on the API. When available, the frontend also loads server catalog data, saved phrases, preferences, and usage through the `/api` routes. Phrase, preference, and usage updates persist in SQLite; browser storage remains the offline fallback. See [ARCHITECTURE.md](ARCHITECTURE.md) for the component and data-flow diagrams.

## API endpoints

All API responses are JSON. Validation errors include an `error` message.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | API/database health |
| GET | `/api/categories` | Seeded AAC categories |
| GET | `/api/items` | Seeded multilingual AAC items |
| GET, POST | `/api/phrases` | List or create saved phrases; duplicate text is returned rather than duplicated |
| DELETE | `/api/phrases/<id>` | Delete a saved phrase |
| GET, PUT | `/api/preferences` | Read or update language, speech speed, accessibility options, and favorite categories |
| GET, POST | `/api/usage` | Read usage counts or increment an AAC item/saved phrase count |
| GET | `/api/suggestions?message=…&language=…` | Context recommendations, ranked by persistent use and including relevant frequently used phrases |

The frontend talks to a same-origin `/api` path. Vite proxies it to `AAC_API_PROXY` during development and preview. In deployment, route `/api` to the Flask service through the hosting reverse proxy.

## Database design

`backend/seed.json` is the shared seed catalog generated from the frontend content. On first startup, SQLite is initialized with category and AAC item rows, four starter phrases, and default preferences. The schema includes `categories`, `items`, singleton `preferences`, `saved_phrases`, `item_usage`, and `phrase_usage`. Foreign keys protect item/category and usage relationships. SQLite values are always bound as SQL parameters.

## AI/NLP suggestions

Recommendations are deterministic rules stored with the seed catalog, not an LLM. Prefix rules offer relevant words, while local and database usage counts rank frequently selected items. Frequently used saved phrases become suggestions when they match the current message. The same fixed rule map is used in the browser for offline fallback and in the API for personalized ordering.

## Indian-language support

The current reviewed starter vocabulary covers English, Hindi, and Kannada labels and common phrases. The UI and catalog are structured for more language dictionaries. Speech tries the matching Indian locale and falls back to a device voice if no match is installed. Speech availability and pronunciation depend on browser and operating-system voice packages.

## Speech

Saathi uses the browser's `SpeechSynthesis` API and local device voices. Empty messages are rejected with visible feedback, speech can be stopped, and speech speed is configurable. The browser or device may not provide Hindi/Kannada voices; in that case the selected device default voice is used.

## Accessibility

The board uses large touch targets, native keyboard-operable controls, a live sentence area, descriptive labels, visible focus, responsive layouts, high-contrast mode, larger text, adjustable speech speed, and explicit Speak/Stop controls. These features support a demo; they do not replace individualized AAC assessment or user testing.

## Offline architecture and limits

The service worker precaches the production app shell/assets and attempts to cache the public catalog API responses. It uses the cached app shell for a later offline navigation. Core words are also bundled locally, so communication and deterministic suggestions remain available if the API is down. Saved phrases and preferences are stored in localStorage and SQLite when online. If saved phrases/settings are changed while offline, the browser state is retained and reconciled with the API when connectivity returns. The browser must first visit the HTTPS/localhost app online so the service worker can install. Device speech can still depend on an installed voice; no offline voice is bundled.

## Wireless / Bluetooth architecture

The settings page detects whether `navigator.bluetooth` is exposed. With Web Bluetooth available, the communicator can select a BLE device that advertises the Nordic UART Service, connect, see the device/connection state, send the current message to its TX characteristic, and disconnect. If this browser, device, or page context cannot use Bluetooth, a simulation mode demonstrates the same connect/send/status flow and explicitly says the connection is simulated. The simulation never reports a physical device as connected.

Web Bluetooth requires a secure context (HTTPS or localhost), user interaction to open the device picker, and browser/device support. It is generally available in Chromium browsers on supported desktop/Android configurations; Safari and Firefox support is limited or absent, and there is no guarantee that arbitrary BLE peripherals expose the Nordic UART Service. A physical device was not available for this project run, so the hardware data path is implemented but was not verified against a real peripheral.

## Security and privacy

- The API binds to `127.0.0.1` by default; explicitly configure host/origins before exposing it.
- CORS allows only the configured `AAC_CORS_ORIGINS`; credentials are not enabled.
- Request bodies are limited in size and validated by type, length, language, category IDs, and usage increments.
- SQLite queries use bound parameters; foreign keys and unique normalized phrase text are enabled.
- Error responses do not return stack traces. Security headers include `nosniff`, `DENY` framing, and a no-referrer policy; Vite preview adds a restrictive CSP.
- No account, authentication, analytics, or cloud synchronization is included. This is a local single-profile demo. Do not expose its unauthenticated API to a public network without adding authentication, TLS termination, rate limits, backups, and a multi-user data model.
- User phrases are not sent to an LLM. Personalized suggestion queries go only to the configured Saathi API; suggestion URLs are not stored in the service-worker cache.

## Installation and running locally

Requirements: Node.js 18+, Python 3.10+, and npm.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run dev:full
```

Open the Vite URL printed by npm (usually `http://localhost:5173`). `dev:full` starts Flask on port 5000 and Vite with `/api` proxying to it. On Windows, activate the virtual environment with `.venv\Scripts\activate` first. Alternatively, run the backend and frontend separately with `npm run dev:api` and `npm run dev` in two terminals.

For a local production build and service-worker test, run `npm run build`, start the backend (`npm run start:api`), and start `npm run preview`. Vite preview is for local verification; use a production static host plus a WSGI server/reverse proxy for a real deployment.

## Environment variables

See [.env.example](.env.example). The app does not automatically read `.env`; export values in the shell or configure them in the hosting environment.

- `AAC_HOST` and `AAC_PORT`: backend bind host/port. Keep the default loopback bind for local use.
- `AAC_DATABASE`: SQLite file path.
- `AAC_CORS_ORIGINS`: comma-separated explicit browser origins allowed to call the API directly cross-origin.
- `AAC_API_PROXY`: backend URL used by Vite dev/preview proxy.
- `PYTHON`: optional Python executable used by `dev:full` and the API test runner.

## Testing

```sh
npm test
npm run build
```

Tests cover catalog and recommendation rules, speech locale/voice fallback, service-worker precaching/offline navigation/catalog-cache behavior, REST integration, seeded database content, phrase create/deduplicate/delete, input validation, preferences, usage-based suggestions, SQL-injection-shaped input, and CORS allowlisting. The project was also run in a browser for sentence building, suggestions, phrase persistence, language switching, and accessibility preference persistence. The service-worker offline behavior is tested with an isolated worker/cache harness; this environment did not provide a physical Bluetooth peripheral or a browser network emulator for a full device-level offline toggle.

## Deployment

Build the frontend with `npm run build`, install Python requirements, set `AAC_DATABASE` to persistent storage, bind the API behind an HTTPS reverse proxy, and serve `dist/` from a static host. Route same-origin `/api` requests to Waitress running `python -m backend.serve`. Set `AAC_CORS_ORIGINS` to exact origins if the frontend/API are separate. Keep the database file private and backed up. A public multi-user deployment requires authentication and user-scoped records, which are outside this demo's scope.

## Screenshots

Add presentation screenshots here after capturing the final application at the target display sizes.

## Limitations

- No accounts or multi-device/cloud sync; the database uses one preference profile and is intended for a local/demo instance.
- Offline changes persist in this browser and reconcile when the API becomes reachable; if site storage is cleared, browser-only offline changes are lost.
- Browser/device voice support and Bluetooth support differ. Bluetooth hardware testing requires a BLE peripheral implementing Nordic UART Service.
- Hindi/Kannada coverage is a starter vocabulary, not a complete or clinically validated AAC lexicon.
- No switch-scanning access method or clinical evaluation is included.

## SDG 9 alignment

The project demonstrates inclusive, adaptable digital infrastructure using common devices, low-cost deployment, local language support, and a modular API that can be expanded after user validation.

## Conclusion

Saathi now includes a working local-first AAC journey from symbol selection through speech, saved messages, personalization, persistent usage-based recommendations, API-backed data, PWA reopening, and an optional Bluetooth/simulation workflow. It is suitable for a college project demonstration and further user-centered testing.
