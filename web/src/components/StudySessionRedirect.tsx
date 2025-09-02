import React from 'react';
import { useParams, Navigate } from 'react-router-dom';

export default function StudySessionRedirect() {
  const { sessionId } = useParams();
  return <Navigate to={`/quiz/session/${sessionId}`} replace />;
}
