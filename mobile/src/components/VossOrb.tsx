import { useEffect, useMemo, useRef } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";

type OrbState = "idle" | "ready" | "listening" | "thinking" | "speaking";

type Props = {
  state: OrbState;
};

const STATE_COPY: Record<OrbState, { label: string; detail: string; glow: string }> = {
  idle: {
    label: "Idle",
    detail: "Voss is standing by.",
    glow: "#d0a96a",
  },
  ready: {
    label: "Ready",
    detail: "The channel is open.",
    glow: "#2f8f83",
  },
  listening: {
    label: "Listening",
    detail: "The orb is taking you in.",
    glow: "#1481a8",
  },
  thinking: {
    label: "Thinking",
    detail: "Pulling signals together.",
    glow: "#9a3412",
  },
  speaking: {
    label: "Speaking",
    detail: "Voss is responding.",
    glow: "#315c9c",
  },
};

export function VossOrb({ state }: Props) {
  const pulse = useRef(new Animated.Value(0)).current;
  const rotate = useRef(new Animated.Value(0)).current;
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    pulse.stopAnimation();
    rotate.stopAnimation();
    shimmer.stopAnimation();

    const pulseRange =
      state === "thinking" ? [0.94, 1.08] :
      state === "listening" ? [0.95, 1.05] :
      state === "speaking" ? [0.97, 1.03] :
      state === "ready" ? [0.98, 1.02] :
      [0.99, 1.01];

    const pulseDuration =
      state === "thinking" ? 950 :
      state === "listening" ? 800 :
      state === "speaking" ? 700 :
      state === "ready" ? 1400 :
      2000;

    pulse.setValue(0);
    rotate.setValue(0);
    shimmer.setValue(0);

    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1,
          duration: pulseDuration,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 0,
          duration: pulseDuration,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
    );

    const rotateLoop = Animated.loop(
      Animated.timing(rotate, {
        toValue: 1,
        duration: state === "thinking" ? 4200 : state === "listening" ? 2800 : state === "speaking" ? 6500 : 9000,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );

    const shimmerLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, {
          toValue: 1,
          duration: state === "thinking" ? 900 : state === "listening" ? 650 : 1400,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(shimmer, {
          toValue: 0,
          duration: state === "thinking" ? 900 : state === "listening" ? 650 : 1400,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ]),
    );

    pulseLoop.start();
    rotateLoop.start();
    shimmerLoop.start();

    return () => {
      pulseLoop.stop();
      rotateLoop.stop();
      shimmerLoop.stop();
    };
  }, [pulse, rotate, shimmer, state]);

  const scale = pulse.interpolate({
    inputRange: [0, 1],
    outputRange:
      state === "thinking" ? [0.94, 1.08] :
      state === "listening" ? [0.95, 1.05] :
      state === "speaking" ? [0.97, 1.03] :
      state === "ready" ? [0.98, 1.02] :
      [0.99, 1.01],
  });

  const haloOpacity = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange:
      state === "thinking" ? [0.28, 0.62] :
      state === "listening" ? [0.24, 0.58] :
      state === "speaking" ? [0.24, 0.54] :
      [0.16, 0.3],
  });

  const ringRotation = rotate.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  const copy = useMemo(() => STATE_COPY[state], [state]);

  return (
    <View style={styles.wrapper}>
      <Animated.View
        style={[
          styles.halo,
          {
            opacity: haloOpacity,
            backgroundColor: copy.glow,
            transform: [{ scale }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.outerRing,
          {
            borderColor: copy.glow,
            transform: [{ rotate: ringRotation }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.middleRing,
          {
            borderColor: copy.glow,
            transform: [{ scale }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.core,
          {
            transform: [{ scale }],
            shadowColor: copy.glow,
          },
        ]}
      >
        <View style={[styles.coreInset, { borderColor: copy.glow }]}>
          <View style={[styles.coreKernel, { backgroundColor: copy.glow }]} />
        </View>
      </Animated.View>
      <View style={styles.copy}>
        <Text style={styles.label}>{copy.label}</Text>
        <Text style={styles.detail}>{copy.detail}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
  },
  halo: {
    position: "absolute",
    width: 250,
    height: 250,
    borderRadius: 125,
  },
  outerRing: {
    position: "absolute",
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 1.5,
    opacity: 0.35,
  },
  middleRing: {
    position: "absolute",
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 2,
    opacity: 0.45,
  },
  core: {
    width: 132,
    height: 132,
    borderRadius: 66,
    backgroundColor: "rgba(255,255,255,0.14)",
    alignItems: "center",
    justifyContent: "center",
    shadowOpacity: 0.38,
    shadowRadius: 28,
    shadowOffset: { width: 0, height: 0 },
    elevation: 10,
  },
  coreInset: {
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 1.5,
    backgroundColor: "rgba(255,255,255,0.22)",
    alignItems: "center",
    justifyContent: "center",
  },
  coreKernel: {
    width: 28,
    height: 28,
    borderRadius: 14,
    opacity: 0.95,
  },
  copy: {
    marginTop: 150,
    alignItems: "center",
  },
  label: {
    color: "#1f1b17",
    fontSize: 18,
    fontWeight: "700",
  },
  detail: {
    marginTop: 6,
    color: "#6a5e51",
    fontSize: 14,
  },
});
