import React from 'react';
import { useNotification } from './NotificationManager';

const NotificationModalTest: React.FC = () => {
  const { showNotification } = useNotification();

  const showUploadFailedNotification = () => {
    showNotification({
      title: 'Upload Failed',
      message: 'Failed to upload "GT học phần Lịch sử Đảng cộng sản VN (C) Tr63-Tr140.pdf": Network error occurred',
      status: 'error',
    });
  };

  const showUploadSuccessNotification = () => {
    showNotification({
      title: 'Upload Success',
      message: 'Document "example.pdf" has been uploaded successfully',
      status: 'success',
    });
  };

  const showProcessingNotification = () => {
    showNotification({
      title: 'Processing Document',
      message: 'Document is being processed and indexed',
      status: 'processing',
    });
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Notification Modal Test</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Modal-Style Notifications</h2>
          <p className="text-gray-600 mb-6">
            These notifications match the design from the image - rectangular popups with colored backgrounds, 
            icons with background circles, status tags, and timestamps.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={showUploadFailedNotification}
              className="p-4 bg-red-50 border-2 border-red-200 rounded-lg hover:bg-red-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-red-600 mb-2">Upload Failed</div>
                <div className="text-sm text-red-500">Test the error notification</div>
              </div>
            </button>
            
            <button
              onClick={showUploadSuccessNotification}
              className="p-4 bg-green-50 border-2 border-green-200 rounded-lg hover:bg-green-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-green-600 mb-2">Upload Success</div>
                <div className="text-sm text-green-500">Test the success notification</div>
              </div>
            </button>
            
            <button
              onClick={showProcessingNotification}
              className="p-4 bg-purple-50 border-2 border-purple-200 rounded-lg hover:bg-purple-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-purple-600 mb-2">Processing</div>
                <div className="text-sm text-purple-500">Test the processing notification</div>
              </div>
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Design Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>✅ <strong>Modal-style popup</strong> - Rectangular design with rounded corners</li>
            <li>✅ <strong>Colored backgrounds</strong> - Different colors for each status type</li>
            <li>✅ <strong>Icon with background circle</strong> - Icons are placed in colored circles</li>
            <li>✅ <strong>Status tags</strong> - Small colored badges showing the status</li>
            <li>✅ <strong>Timestamps</strong> - Shows when the notification was created</li>
            <li>✅ <strong>Close button</strong> - X button in the top right corner</li>
            <li>✅ <strong>Positioned in top right</strong> - Matches the image layout</li>
            <li>✅ <strong>Smooth animations</strong> - Slide-in from right with hover effects</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NotificationModalTest;
