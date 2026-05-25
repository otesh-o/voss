# Voss Mobile

This is the first real phone-facing client for Voss.

## What it does

- Connects to the Voss backend over your local network
- Uses an orb-first home screen instead of a plain chatbot layout
- Shows conversation history
- Sends chat messages
- Supports press-and-hold voice input through the orb
- Speaks Voss replies on the phone
- Can register the phone for Expo push notifications
- Switches modes
- Shows agenda items
- Shows due reminders

## What it does not do yet

- Fully autonomous background notification scheduling
- Authentication
- Remote internet access outside your local network

## Run it

1. Start the Voss backend on your laptop.
   Recommended:

```powershell
python run_backend.py
```

2. Make sure the backend is reachable on your local network.
3. If you want mobile voice input, the backend also needs a valid `OPENAI_API_KEY` for transcription.
4. If you want push notifications, configure an Expo project ID for the app and keep the Voss backend running somewhere reachable.
5. From this `mobile` folder:

```powershell
npm install
npx expo start
```

6. Open the Expo app on your phone and connect to the same Wi-Fi.
7. In the app, enter your laptop's local IP, for example:

```text
http://192.168.1.100:8000
```

Do not use `localhost` from your phone.

Push notifications are wired for Expo delivery, but they still depend on:
- a physical device
- notification permission
- a valid Expo project ID
- the Voss backend being alive to send reminders out
