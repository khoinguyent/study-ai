import React from 'react';
import { useNotification } from './NotificationManager';

const NotificationTest: React.FC = () => {
  const { showNotification } = useNotification();

  const testNotifications = [
    {
      title: 'Upload Success',
      message: 'Document "example.pdf" has been uploaded successfully',
      status: 'success' as const,
    },
    {
      title: 'Upload Failed',
      message: 'Failed to upload "GT học phần Lịch sử Đảng cộng sản VN (C) Tr63-Tr140.pdf": Network error occurred',
      status: 'error' as const,
    },
    {
      title: 'Processing Document',
      message: 'Document is being processed and indexed',
      status: 'processing' as const,
    },
    {
      title: 'Document Indexed',
      message: 'Document has been indexed successfully with 15 chunks',
      status: 'completed' as const,
    },
    {
      title: 'Upload in Progress',
      message: 'Uploading "large-file.pdf" (45% complete)',
      status: 'uploading' as const,
    },
    {
      title: 'Indexing in Progress',
      message: 'Indexing document chunks for search',
      status: 'indexing' as const,
    },
    {
      title: 'Warning',
      message: 'Document size is larger than recommended',
      status: 'warning' as const,
    },
    {
      title: 'Information',
      message: 'Your document library has been updated',
      status: 'info' as const,
    },
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Notification System Test</h1>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {testNotifications.map((notification, index) => (
            <button
              key={index}
              onClick={() => showNotification(notification)}
              className={`p-4 rounded-lg border-2 border-dashed transition-all duration-200 hover:scale-105 ${
                notification.status === 'success' ? 'border-green-300 hover:border-green-400' :
                notification.status === 'error' ? 'border-red-300 hover:border-red-400' :
                notification.status === 'warning' ? 'border-yellow-300 hover:border-yellow-400' :
                notification.status === 'info' ? 'border-blue-300 hover:border-blue-400' :
                notification.status === 'uploading' ? 'border-blue-300 hover:border-blue-400' :
                notification.status === 'processing' ? 'border-purple-300 hover:border-purple-400' :
                notification.status === 'indexing' ? 'border-indigo-300 hover:border-indigo-400' :
                'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="text-center">
                <div className={`text-lg font-semibold mb-2 ${
                  notification.status === 'success' ? 'text-green-600' :
                  notification.status === 'error' ? 'text-red-600' :
                  notification.status === 'warning' ? 'text-yellow-600' :
                  notification.status === 'info' ? 'text-blue-600' :
                  notification.status === 'uploading' ? 'text-blue-600' :
                  notification.status === 'processing' ? 'text-purple-600' :
                  notification.status === 'indexing' ? 'text-indigo-600' :
                  'text-gray-600'
                }`}>
                  {notification.title}
                </div>
                <div className="text-xs text-gray-500">
                  {notification.status}
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>✅ Different colors for each status type</li>
            <li>✅ Auto-close functionality (except for ongoing processes)</li>
            <li>✅ Progress bars for uploading/processing/indexing</li>
            <li>✅ Smooth animations and hover effects</li>
            <li>✅ Responsive design</li>
            <li>✅ Reusable across the entire application</li>
            <li>✅ Context-based notification management</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NotificationTest;
