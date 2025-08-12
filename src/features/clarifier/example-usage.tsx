import React from 'react';
import { View, StyleSheet, Text, Alert } from 'react-native';
import { ClarifierProvider, ClarifierSideChat, useClarifier } from './index';

// Example of a screen that uses the clarifier
export default function StudySetupScreen() {
  return (
    <View style={styles.wrap}>
      <ClarifierProvider
        sessionId="sess_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1','d2']}
        apiBase="/api"          // your gateway base
        token={undefined}       // pass bearer if available
        flow="quiz_setup"       // can be changed later to summary/highlights flows
        callbacks={{
          onStageChange: (stage, filled) => {
            console.log('Stage changed:', stage, filled);
            // You can update your UI based on the current stage
            // e.g., show progress indicator, update form fields, etc.
          },
          onDone: (filled) => {
            console.log('Generation started with:', filled);
            Alert.alert(
              'Quiz Generation Started!',
              `Generating ${filled?.requested_count || 'questions'} with ${filled?.question_types?.join(', ') || 'selected types'} at ${filled?.difficulty || 'mixed'} difficulty.`
            );
            // Navigate to quiz screen, show loading state, etc.
          },
          onError: (msg) => {
            console.warn('Clarifier error:', msg);
            Alert.alert('Error', msg);
            // Show error toast, retry button, etc.
          },
        }}
      >
        <ClarifierSideChat />
        {/* Your main content on the right */}
        <View style={styles.mainContent}>
          <Text style={styles.title}>Study Session Setup</Text>
          <Text style={styles.subtitle}>Use the AI assistant on the left to configure your quiz</Text>
          
          {/* You can also use the useClarifier hook to access state */}
          <ClarifierStatus />
        </View>
      </ClarifierProvider>
    </View>
  );
}

// Example of a component that uses the useClarifier hook
function ClarifierStatus() {
  const { ready, done, sending, stage, filled, error } = useClarifier();
  
  return (
    <View style={styles.statusContainer}>
      <Text style={styles.statusTitle}>Current Status</Text>
      <Text style={styles.statusText}>
        Ready: {ready ? '✅' : '⏳'} | 
        Done: {done ? '✅' : '⏳'} | 
        Sending: {sending ? '⏳' : '✅'}
      </Text>
      {stage && <Text style={styles.statusText}>Stage: {stage}</Text>}
      {filled && Object.keys(filled).length > 0 && (
        <Text style={styles.statusText}>
          Filled: {Object.entries(filled).map(([k, v]) => `${k}: ${v}`).join(', ')}
        </Text>
      )}
      {error && <Text style={styles.errorText}>Error: {error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { 
    flex: 1, 
    flexDirection: 'row' 
  },
  mainContent: { 
    flex: 1, 
    backgroundColor: '#FAFAFA',
    padding: 20
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#111827'
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 24
  },
  statusContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB'
  },
  statusTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
    color: '#111827'
  },
  statusText: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 4
  },
  errorText: {
    fontSize: 14,
    color: '#DC2626',
    marginTop: 8
  }
});

// Example of different flow types
export function DocumentSummaryScreen() {
  return (
    <View style={styles.wrap}>
      <ClarifierProvider
        sessionId="sess_summary_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1']}
        apiBase="/api"
        flow="doc_summary"
        callbacks={{
          onDone: (filled) => {
            console.log('Summary generation started:', filled);
            // Handle summary generation completion
          }
        }}
      >
        <ClarifierSideChat />
        <View style={styles.mainContent}>
          <Text style={styles.title}>Document Summary</Text>
          <Text style={styles.subtitle}>Configure summary parameters</Text>
        </View>
      </ClarifierProvider>
    </View>
  );
}

export function DocumentHighlightsScreen() {
  return (
    <View style={styles.wrap}>
      <ClarifierProvider
        sessionId="sess_highlights_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1']}
        apiBase="/api"
        flow="doc_highlights"
        callbacks={{
          onDone: (filled) => {
            console.log('Highlights generation started:', filled);
            // Handle highlights generation completion
          }
        }}
      >
        <ClarifierSideChat />
        <View style={styles.mainContent}>
          <Text style={styles.title}>Document Highlights</Text>
          <Text style={styles.subtitle}>Configure highlight parameters</Text>
        </View>
      </ClarifierProvider>
    </View>
  );
}

export function DocumentConclusionScreen() {
  return (
    <View style={styles.wrap}>
      <ClarifierProvider
        sessionId="sess_conclusion_123"
        userId="u_456"
        subjectId="subj_hist"
        docIds={['d1']}
        apiBase="/api"
        flow="doc_conclusion"
        callbacks={{
          onDone: (filled) => {
            console.log('Conclusion generation started:', filled);
            // Handle conclusion generation completion
          }
        }}
      >
        <ClarifierSideChat />
        <View style={styles.mainContent}>
          <Text style={styles.title}>Document Conclusion</Text>
          <Text style={styles.subtitle}>Configure conclusion parameters</Text>
        </View>
      </ClarifierProvider>
    </View>
  );
}

