# Voss Mobile

This is the first real phone-facing client for Voss.

## What it does

- Connects to the Voss backend over your local network
- Shows conversation history
- Sends chat messages
- Switches modes
- Shows agenda items
- Shows due reminders

## What it does not do yet

- Voice input
- Voice output
- Push notifications
- Authentication
- Remote internet access outside your local network

## Run it

1. Start the Voss backend on your laptop.
2. Make sure the backend is reachable on your local network.
3. From this `mobile` folder:

```powershell
npm install
npx expo start
```

4. Open the Expo app on your phone and connect to the same Wi-Fi.
5. In the app, enter your laptop's local IP, for example:

```text
http://192.168.1.100:8000
```

Do not use `localhost` from your phone.
