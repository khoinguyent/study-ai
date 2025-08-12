import React, { useRef, useEffect } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useClarifier } from './ClarifierContext';

export default function ClarifierSideChat({ style }: { style?: any }) {
  const { ready, done, sending, error, messages, sendText } = useClarifier();
  const [draft, setDraft] = React.useState('');
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 0);
  }, [messages.length]);

  const onQuick = (q: string) => { 
    setDraft(q); 
    onSend(); 
  };
  
  const onSend = () => {
    if (!draft.trim()) return;
    const text = draft.trim();
    setDraft('');
    sendText(text);
  };

  const placeholder = done ? 'Generation started…' : 'e.g., "MCQ and True/False", or "12 hard MCQs"';

  return (
    <View style={[styles.container, style]}>
      <View style={styles.header}>
        <Text style={styles.title}>AI Study Assistant</Text>
        <Text style={styles.sub}>Clarifier</Text>
      </View>

      <ScrollView ref={scrollRef} style={styles.scroll} contentContainerStyle={styles.scrollInner}>
        {messages.map(m => (
          <View key={m.id} style={styles.row}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>🤖</Text>
            </View>
            <View style={styles.bubble}>
              <Text style={styles.text}>{m.text}</Text>
              {!!m.quick?.length && (
                <View style={styles.quickWrap}>
                  {m.quick.map(q => (
                    <Pressable key={q} style={styles.chip} onPress={() => onQuick(q)}>
                      <Text style={styles.chipText}>{q}</Text>
                    </Pressable>
                  ))}
                </View>
              )}
            </View>
          </View>
        ))}
        {!ready && !error ? <ActivityIndicator style={{ marginTop: 12 }} /> : null}
        {error ? <Text style={styles.err}>{error}</Text> : null}
      </ScrollView>

      <KeyboardAvoidingView 
        behavior={Platform.select({ ios: 'padding', android: undefined })} 
        keyboardVerticalOffset={Platform.select({ ios: 64, android: 0 })}
      >
        <View style={styles.composer}>
          <TextInput
            style={styles.input}
            placeholder={placeholder}
            value={draft}
            editable={ready && !sending && !done}
            onChangeText={setDraft}
            onSubmitEditing={onSend}
            returnKeyType="send"
          />
          <Pressable
            disabled={!ready || sending || !draft.trim() || done}
            onPress={onSend}
            style={({ pressed }) => [
              styles.sendBtn,
              (!ready || sending || !draft.trim() || done) && styles.sendBtnDisabled,
              pressed && styles.sendBtnPressed
            ]}
          >
            <Text style={styles.sendText}>{sending ? '...' : 'Send'}</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: 360, // fixed left panel
    backgroundColor: '#fff',
    borderRightWidth: StyleSheet.hairlineWidth,
    borderRightColor: '#E5E7EB',
    height: '100%',
  },
  header: { 
    padding: 12, 
    borderBottomWidth: StyleSheet.hairlineWidth, 
    borderBottomColor: '#E5E7EB' 
  },
  title: { 
    fontSize: 16, 
    fontWeight: '600' 
  },
  sub: { 
    fontSize: 12, 
    color: '#6B7280', 
    marginTop: 2 
  },
  scroll: { 
    flex: 1 
  },
  scrollInner: { 
    padding: 12, 
    paddingBottom: 16 
  },
  row: { 
    flexDirection: 'row', 
    gap: 8, 
    marginBottom: 10 
  },
  avatar: { 
    width: 24, 
    height: 24, 
    borderRadius: 12, 
    backgroundColor: '#EEF2FF', 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  avatarText: { 
    fontSize: 12 
  },
  bubble: { 
    maxWidth: 280, 
    backgroundColor: '#F3F4F6', 
    borderRadius: 16, 
    paddingHorizontal: 12, 
    paddingVertical: 8 
  },
  text: { 
    fontSize: 14, 
    color: '#111827' 
  },
  quickWrap: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    gap: 6, 
    marginTop: 8 
  },
  chip: { 
    borderWidth: 1, 
    borderColor: '#E5E7EB', 
    paddingHorizontal: 8, 
    paddingVertical: 4, 
    borderRadius: 999 
  },
  chipText: { 
    fontSize: 12, 
    color: '#111827' 
  },
  composer: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 8, 
    padding: 10, 
    borderTopWidth: StyleSheet.hairlineWidth, 
    borderTopColor: '#E5E7EB' 
  },
  input: { 
    flex: 1, 
    backgroundColor: '#F9FAFB', 
    borderWidth: 1, 
    borderColor: '#E5E7EB', 
    borderRadius: 10, 
    paddingHorizontal: 12, 
    paddingVertical: Platform.OS === 'ios' ? 12 : 8, 
    fontSize: 14 
  },
  sendBtn: { 
    backgroundColor: '#111827', 
    paddingHorizontal: 16, 
    paddingVertical: 10, 
    borderRadius: 10 
  },
  sendBtnDisabled: { 
    opacity: 0.4 
  },
  sendBtnPressed: { 
    opacity: 0.8 
  },
  sendText: { 
    color: '#fff', 
    fontWeight: '600' 
  },
  err: { 
    color: '#DC2626', 
    marginTop: 8, 
    fontSize: 12 
  },
});

