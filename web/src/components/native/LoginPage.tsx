import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { Mail, Lock, Crown, Brain } from 'lucide-react';
import { LoginRequest } from '../../types';
import apiService from '../../services/api';
import { Button, Input, Card } from './index';

const LoginPage: React.FC = () => {
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const handleInputChange = (field: keyof LoginRequest, value: string): void => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleSubmit = async (): Promise<void> => {
    setIsLoading(true);
    setErrors({});
    
    try {
      const response = await apiService.login(formData);
      localStorage.setItem('token', response.access_token);
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Login error:', error);
      Alert.alert('Login Failed', error instanceof Error ? error.message : 'Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Card style={styles.card}>
        {/* Header/Branding */}
        <View style={styles.header}>
          <View style={styles.logo}>
            <View style={styles.logoIcon}>
              <Brain size={24} color="#ffffff" />
            </View>
          </View>
          <Text style={styles.welcomeText}>Welcome Back</Text>
          <Text style={styles.welcomeSubtitle}>Sign in to your StudyAI account</Text>
        </View>

        {/* Login Form */}
        <View style={styles.form}>
          <Input
            label="Email Address"
            placeholder="Enter your email"
            value={formData.email}
            onChangeText={(text) => handleInputChange('email', text)}
            keyboardType="email-address"
            autoCapitalize="none"
            error={errors.email}
          />

          <Input
            label="Password"
            placeholder="Enter your password"
            value={formData.password}
            onChangeText={(text) => handleInputChange('password', text)}
            secureTextEntry
            error={errors.password}
          />

          <Button
            title={isLoading ? 'Signing In...' : 'Sign In'}
            onPress={handleSubmit}
            disabled={isLoading}
            style={styles.signInButton}
          />
        </View>

        {/* Account Creation Link */}
        <View style={styles.signupLink}>
          <Text style={styles.signupText}>Don't have an account? </Text>
          <Text style={styles.signupLinkText} onPress={() => window.location.href = '/signup'}>
            Sign Up
          </Text>
        </View>

        {/* Premium Features Section */}
        <View style={styles.premiumFeatures}>
          <View style={styles.premiumHeader}>
            <Crown size={20} color="#3b82f6" />
            <Text style={styles.premiumTitle}>Premium Features</Text>
          </View>
          <View style={styles.premiumList}>
            <Text style={styles.premiumItem}>• Organized document folders</Text>
            <Text style={styles.premiumItem}>• Unlimited question generation</Text>
            <Text style={styles.premiumItem}>• Advanced analytics & progress tracking</Text>
            <Text style={styles.premiumItem}>• Priority AI processing</Text>
          </View>
        </View>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  contentContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    maxWidth: 420,
    alignSelf: 'center',
    width: '100%',
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    marginBottom: 24,
  },
  logoIcon: {
    backgroundColor: '#3b82f6',
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  welcomeText: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
  form: {
    marginBottom: 24,
  },
  signInButton: {
    marginTop: 8,
  },
  signupLink: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 32,
  },
  signupText: {
    fontSize: 14,
    color: '#6b7280',
  },
  signupLinkText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '600',
  },
  premiumFeatures: {
    backgroundColor: '#f0f9ff',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e0f2fe',
  },
  premiumHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  premiumTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f2937',
    marginLeft: 8,
  },
  premiumList: {
    gap: 8,
  },
  premiumItem: {
    color: '#3b82f6',
    fontSize: 14,
    lineHeight: 20,
  },
});

export default LoginPage; 