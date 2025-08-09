import React from 'react';
import { useNotification } from './NotificationManager';

const NotificationModalTest: React.FC = () => {
  const { showNotification } = useNotification();

  const showExactImageNotification = () => {
    showNotification({
      title: 'Document Indexed',
      message: 'Document 04174666-ccf1-4ef9-9c8b-3b3a9aa9d93d has been indexed successfully with 1 chunks',
      status: 'indexing',
    });
  };

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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Exact Image Design</h2>
          <p className="text-gray-600 mb-6">
            This button will show the exact notification from the new image - "Document Indexed" with solid dark background and white text.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={showExactImageNotification}
              className="p-4 bg-indigo-50 border-2 border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-indigo-600 mb-2">Exact Image Notification</div>
                <div className="text-sm text-indigo-500">Shows the exact "Document Indexed" notification from the new image</div>
              </div>
            </button>
            
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">New Design Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>✅ <strong>Solid Dark Background</strong> - Dark colored backgrounds (red, green, blue, etc.)</li>
            <li>✅ <strong>White Text</strong> - All text is white for contrast</li>
            <li>✅ <strong>White Lightning Bolt Icon</strong> - For indexing notifications</li>
            <li>✅ <strong>No Status Tag</strong> - Removed status badges like in the image</li>
            <li>✅ <strong>Timestamp with Seconds</strong> - Shows "12:16:36 PM" format</li>
            <li>✅ <strong>White Close Button</strong> - X button in white</li>
            <li>✅ <strong>Exact Message</strong> - "Document Indexed" with specific document ID</li>
            <li>✅ <strong>Top Right Positioning</strong> - Matches the image layout exactly</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NotificationModalTest;
