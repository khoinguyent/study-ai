import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { NotificationProvider, NotificationPortal } from "./components/notifications/NotificationContext";
import "./components/notifications/notificationTheme.css";
import './index.css';

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <NotificationProvider>
      <App />
      {/* Toasts render here, above all content */}
      <NotificationPortal />
    </NotificationProvider>
  </React.StrictMode>
); 