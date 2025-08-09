import React from 'react';
import { useNotification } from './NotificationManager';

const NotificationModalTest: React.FC = () => {
  const { showNotification } = useNotification();

  const showExactImageNotification = () => {
    showNotification({
      title: 'Upload Failed',
      message: 'Failed to upload "GT học phần Lịch sử Đảng cộng sản VN (C) Tr63-Tr140.pdf": Network error occurred',
      status: 'error',
    });
  };

  const showDocumentIndexedNotification = () => {
    showNotification({
      title: 'Document Indexed',
      message: 'Document 04174666-ccf1-4ef9-9c8b-3b3a9aa9d93d has been indexed successfully with 1 chunks',
      status: 'indexing',
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
            This button will show the exact notification from the image - "Upload Failed" with light red background, white icon with red exclamation mark, and status tag.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={showExactImageNotification}
              className="p-4 bg-red-50 border-2 border-red-200 rounded-lg hover:bg-red-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-red-600 mb-2">Exact Image Notification</div>
                <div className="text-sm text-red-500">Shows the exact "Upload Failed" notification from the image</div>
              </div>
            </button>
            
            <button
              onClick={showDocumentIndexedNotification}
              className="p-4 bg-indigo-50 border-2 border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors duration-200"
            >
              <div className="text-center">
                <div className="text-lg font-semibold text-indigo-600 mb-2">Document Indexed</div>
                <div className="text-sm text-indigo-500">Test the indexing notification</div>
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
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Image Design Features</h2>
          <ul className="space-y-2 text-gray-700">
            <li>✅ <strong>Light Colored Background</strong> - Light red, green, blue backgrounds (not solid dark)</li>
            <li>✅ <strong>White Circular Icon</strong> - Icons in white circles with colored symbols</li>
            <li>✅ <strong>Dark Text</strong> - All text is dark grey/black for readability</li>
            <li>✅ <strong>Status Tags</strong> - Colored badges with white text (e.g., "Failed")</li>
            <li>✅ <strong>Timestamp</strong> - Shows time in bottom right corner</li>
            <li>✅ <strong>Close Button</strong> - X button in top right corner</li>
            <li>✅ <strong>Exact Message</strong> - "Upload Failed" with specific error message</li>
            <li>✅ <strong>Top Right Positioning</strong> - Matches the image layout exactly</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NotificationModalTest;
