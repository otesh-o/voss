import { Platform } from "react-native";

import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";

import { registerDevice } from "./api";


Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});


export async function registerForVossPush(baseUrl: string) {
  if (!Device.isDevice) {
    return { ok: false, reason: "Push notifications need a physical device." };
  }

  const permission = await Notifications.requestPermissionsAsync();
  if (!permission.granted) {
    return { ok: false, reason: "Notification permission was denied." };
  }

  const projectId =
    Constants.expoConfig?.extra?.eas?.projectId ??
    Constants.easConfig?.projectId;

  if (!projectId) {
    return { ok: false, reason: "Missing Expo project ID for push notifications." };
  }

  const token = await Notifications.getExpoPushTokenAsync({ projectId });

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  await registerDevice(baseUrl, {
    push_token: token.data,
    platform: Platform.OS,
    device_name: Device.deviceName ?? "unknown device",
  });

  return { ok: true, token: token.data };
}
