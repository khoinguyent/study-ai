import React from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { ClarifierProvider } from '../../../src/features/clarifier/ClarifierContext';
import ClarifierSideChat from '../../../src/features/clarifier/ClarifierSideChat';
import { useClarifierUI } from './clarifierUI';

const WIDTH = 360;

export default function ClarifierDrawer() {
  const { isOpen, params, close } = useClarifierUI();
  const anim = React.useRef(new Animated.Value(0)).current; // 0: closed, 1: open

  React.useEffect(() => {
    Animated.timing(anim, {
      toValue: isOpen ? 1 : 0,
      duration: 220,
      useNativeDriver: true,
    }).start();
  }, [isOpen]);

  if (!params) return null;

  const translateX = anim.interpolate({ inputRange: [0, 1], outputRange: [-WIDTH, 0] });
  const backdropOpacity = anim.interpolate({ inputRange: [0, 1], outputRange: [0, 0.25] });

  return (
    <>
      {/* Backdrop */}
      <Animated.View
        pointerEvents={isOpen ? 'auto' : 'none'}
        style={[StyleSheet.absoluteFill, { backgroundColor: '#000', opacity: backdropOpacity }]}
      >
        <Pressable style={{ flex: 1 }} onPress={close} />
      </Animated.View>

      {/* Left drawer */}
      <Animated.View style={[styles.panel, { transform: [{ translateX }] }]}>
        <View style={styles.header}>
          <Text style={styles.title}>Study Setup</Text>
          <Pressable onPress={close}>
            <Text style={styles.close}>Close</Text>
          </Pressable>
        </View>

        <ClarifierProvider
          sessionId={params.sessionId}
          userId={params.userId}
          subjectId={params.subjectId}
          docIds={params.docIds}
          apiBase={params.apiBase}
          token={params.token}
          flow={params.flow ?? 'quiz_setup'}
          callbacks={{
            onDone: () => {
              close();
              // downstream toast remains where it exists currently
            },
          }}
        >
          <ClarifierSideChat />
        </ClarifierProvider>
      </Animated.View>
    </>
  );
}

const styles = StyleSheet.create({
  panel: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    width: WIDTH,
    backgroundColor: '#fff',
    borderRightWidth: StyleSheet.hairlineWidth,
    borderRightColor: '#E5E7EB',
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 8,
  },
  header: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: { fontSize: 16, fontWeight: '600' },
  close: { color: '#2563EB', fontWeight: '600' },
});


