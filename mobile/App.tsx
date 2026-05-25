import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import {
  chatWithVoss,
  fetchAgenda,
  fetchHealth,
  fetchHistory,
  fetchModeState,
  fetchReminders,
  setVossMode,
} from "./src/api";
import type { AgendaItem, HealthState, MessageRecord, ModeOption } from "./src/types";

const DEFAULT_BASE_URL = "http://192.168.1.100:8000";

function formatAgendaItem(item: AgendaItem) {
  const timeRef = item.time_reference || "unspecified";
  return `${item.id}  ${item.title}\n${timeRef}  ${item.status}  ${item.priority}`;
}

export default function App() {
  const [baseUrlInput, setBaseUrlInput] = useState(DEFAULT_BASE_URL);
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_BASE_URL);
  const [health, setHealth] = useState<HealthState | null>(null);
  const [mode, setMode] = useState("build");
  const [modes, setModes] = useState<ModeOption[]>([]);
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [reminders, setReminders] = useState<AgendaItem[]>([]);
  const [history, setHistory] = useState<MessageRecord[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  const modeRows = useMemo(() => {
    return modes.map((item) => (
      <Pressable
        key={item.name}
        onPress={() => handleModeChange(item.name)}
        style={[
          styles.modeChip,
          item.name === mode ? styles.modeChipActive : null,
        ]}
      >
        <Text
          style={[
            styles.modeChipText,
            item.name === mode ? styles.modeChipTextActive : null,
          ]}
        >
          {item.name}
        </Text>
      </Pressable>
    ));
  }, [modes, mode]);

  async function loadAll(targetBaseUrl: string) {
    setLoading(true);
    try {
      const [healthData, modeData, agendaData, reminderData, historyData] = await Promise.all([
        fetchHealth(targetBaseUrl),
        fetchModeState(targetBaseUrl),
        fetchAgenda(targetBaseUrl),
        fetchReminders(targetBaseUrl),
        fetchHistory(targetBaseUrl),
      ]);

      setHealth(healthData);
      setMode(modeData.mode);
      setModes(modeData.modes);
      setAgenda(agendaData.items);
      setReminders(reminderData.items);
      setHistory(historyData.items);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      setHealth({ ok: false, report: messageText });
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    setApiBaseUrl(baseUrlInput.trim());
  }

  async function handleSend() {
    const trimmed = message.trim();
    if (!trimmed || sending) {
      return;
    }

    setSending(true);
    try {
      const response = await chatWithVoss(apiBaseUrl, trimmed);
      setHistory((current) => [
        ...current,
        { role: "user", content: trimmed },
        { role: "assistant", content: response.reply },
      ]);
      setMode(response.mode);
      setMessage("");
      if (response.reminders.length) {
        Alert.alert("Voss reminder", response.reminders.join("\n"));
      }
      await loadAll(apiBaseUrl);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      Alert.alert("Voss could not reply", messageText);
    } finally {
      setSending(false);
    }
  }

  async function handleModeChange(nextMode: string) {
    try {
      const response = await setVossMode(apiBaseUrl, nextMode);
      setMode(response.mode);
      setModes(response.modes);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : String(error);
      Alert.alert("Mode update failed", messageText);
    }
  }

  useEffect(() => {
    loadAll(apiBaseUrl);
  }, [apiBaseUrl]);

  return (
    <LinearGradient colors={["#f8f1e2", "#efe2cc", "#e7d4b3"]} style={styles.gradient}>
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" />
        <ScrollView contentContainerStyle={styles.container}>
          <View style={styles.hero}>
            <Text style={styles.kicker}>Voss Mobile</Text>
            <Text style={styles.title}>Your backend now has a phone-shaped doorway.</Text>
            <Text style={styles.subtitle}>
              Point this app at the Voss service running on your laptop. Same brain. Better surface.
            </Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Connection</Text>
            <Text style={styles.label}>Voss backend URL</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              value={baseUrlInput}
              onChangeText={setBaseUrlInput}
              placeholder="http://192.168.1.100:8000"
              placeholderTextColor="#8d7f6f"
              style={styles.input}
            />
            <Pressable onPress={handleConnect} style={styles.primaryButton}>
              <Text style={styles.primaryButtonText}>Connect</Text>
            </Pressable>
            <Text style={styles.meta}>
              Use your laptop&apos;s local network IP, not localhost, when connecting from a phone.
            </Text>
            <Text style={styles.health}>
              {health ? (health.ok ? "System ready." : `Needs attention: ${health.report}`) : "Checking system status..."}
            </Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Mode</Text>
            <View style={styles.modeRow}>{modeRows}</View>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Conversation</Text>
            <View style={styles.messages}>
              {loading ? (
                <ActivityIndicator color="#9a3412" />
              ) : history.length ? (
                history.map((entry, index) => (
                  <View
                    key={`${entry.role}-${index}`}
                    style={[
                      styles.messageBubble,
                      entry.role === "assistant" ? styles.assistantBubble : styles.userBubble,
                    ]}
                  >
                    <Text style={styles.messageRole}>
                      {entry.role === "assistant" ? "Voss" : "You"}
                    </Text>
                    <Text style={styles.messageText}>{entry.content}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.empty}>No conversation yet.</Text>
              )}
            </View>
            <TextInput
              multiline
              value={message}
              onChangeText={setMessage}
              placeholder="Talk to Voss naturally."
              placeholderTextColor="#8d7f6f"
              style={[styles.input, styles.composer]}
            />
            <Pressable onPress={handleSend} style={styles.primaryButton}>
              <Text style={styles.primaryButtonText}>{sending ? "Sending..." : "Send"}</Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Agenda</Text>
            <Text style={styles.meta}>{agenda.length} open item{agenda.length === 1 ? "" : "s"}</Text>
            <View style={styles.list}>
              {agenda.length ? (
                agenda.map((item) => (
                  <View key={item.id} style={styles.listCard}>
                    <Text style={styles.listText}>{formatAgendaItem(item)}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.empty}>No open agenda items.</Text>
              )}
            </View>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Due Reminders</Text>
            <Text style={styles.meta}>{reminders.length} due reminder{reminders.length === 1 ? "" : "s"}</Text>
            <View style={styles.list}>
              {reminders.length ? (
                reminders.map((item) => (
                  <View key={item.id} style={styles.listCard}>
                    <Text style={styles.listText}>{formatAgendaItem(item)}</Text>
                  </View>
                ))
              ) : (
                <Text style={styles.empty}>No reminders are currently due.</Text>
              )}
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  safe: {
    flex: 1,
  },
  container: {
    padding: 20,
    gap: 18,
  },
  hero: {
    paddingTop: 16,
    paddingBottom: 6,
  },
  kicker: {
    color: "#9a3412",
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
  },
  title: {
    marginTop: 10,
    color: "#1f1b17",
    fontSize: 31,
    lineHeight: 38,
    fontWeight: "700",
  },
  subtitle: {
    marginTop: 10,
    color: "#5c5248",
    fontSize: 16,
    lineHeight: 24,
  },
  card: {
    backgroundColor: "rgba(255,255,255,0.88)",
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: "#d9c8b1",
    shadowColor: "#5e4330",
    shadowOpacity: 0.1,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 5,
  },
  cardTitle: {
    color: "#1f1b17",
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 14,
  },
  label: {
    color: "#5c5248",
    fontSize: 13,
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  input: {
    borderWidth: 1,
    borderColor: "#d7c8b7",
    borderRadius: 18,
    backgroundColor: "#fffaf3",
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: "#1f1b17",
    fontSize: 16,
  },
  composer: {
    minHeight: 110,
    textAlignVertical: "top",
    marginTop: 8,
  },
  primaryButton: {
    marginTop: 12,
    backgroundColor: "#9a3412",
    borderRadius: 999,
    paddingVertical: 14,
    alignItems: "center",
  },
  primaryButtonText: {
    color: "#fff8f0",
    fontSize: 15,
    fontWeight: "700",
  },
  meta: {
    marginTop: 10,
    color: "#75685c",
    fontSize: 13,
    lineHeight: 18,
  },
  health: {
    marginTop: 14,
    color: "#40352d",
    fontSize: 14,
    lineHeight: 20,
  },
  modeRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  modeChip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#d4c1aa",
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#f6efe5",
  },
  modeChipActive: {
    backgroundColor: "#9a3412",
    borderColor: "#9a3412",
  },
  modeChipText: {
    color: "#5c5248",
    fontWeight: "600",
  },
  modeChipTextActive: {
    color: "#fff8f0",
  },
  messages: {
    gap: 12,
  },
  messageBubble: {
    borderRadius: 18,
    padding: 14,
  },
  userBubble: {
    backgroundColor: "#efe4d4",
  },
  assistantBubble: {
    backgroundColor: "#fbf5ea",
    borderLeftWidth: 4,
    borderLeftColor: "#9a3412",
  },
  messageRole: {
    color: "#7b6b5d",
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 6,
  },
  messageText: {
    color: "#221c18",
    fontSize: 15,
    lineHeight: 22,
  },
  list: {
    gap: 10,
  },
  listCard: {
    borderRadius: 16,
    backgroundColor: "#fffaf3",
    padding: 14,
    borderWidth: 1,
    borderColor: "#eadfce",
  },
  listText: {
    color: "#332a23",
    fontSize: 14,
    lineHeight: 21,
  },
  empty: {
    color: "#75685c",
    fontSize: 14,
  },
});
