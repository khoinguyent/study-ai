export interface NotificationTemplate {
  title: string;
  message: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
}

export const notificationTemplates = {
  upload: {
    uploading: (fileName: string, subjectName: string, categoryName: string): NotificationTemplate => ({
      title: 'Uploading...',
      message: `"${fileName}" is being uploaded to ${subjectName} - ${categoryName}`,
      status: 'uploading'
    }),
    processing: (fileName: string): NotificationTemplate => ({
      title: 'Processing...',
      message: `"${fileName}" is being processed and indexed for quiz generation`,
      status: 'processing'
    }),
    completed: (fileName: string, subjectName: string, categoryName: string): NotificationTemplate => ({
      title: 'Upload Complete',
      message: `"${fileName}" uploaded successfully to ${subjectName} - ${categoryName}`,
      status: 'completed'
    }),
    failed: (fileName: string): NotificationTemplate => ({
      title: 'Upload Failed',
      message: `Failed to upload "${fileName}". Please try again.`,
      status: 'failed'
    })
  },
  
  // Generic templates for other types of notifications
  generic: {
    success: (title: string, message: string): NotificationTemplate => ({
      title,
      message,
      status: 'completed'
    }),
    error: (title: string, message: string): NotificationTemplate => ({
      title,
      message,
      status: 'failed'
    }),
    info: (title: string, message: string): NotificationTemplate => ({
      title,
      message,
      status: 'processing'
    })
  }
};

export const getNotificationTemplate = (
  type: 'upload' | 'generic',
  status: 'uploading' | 'processing' | 'completed' | 'failed',
  fileName?: string,
  subjectName?: string,
  categoryName?: string
): NotificationTemplate => {
  switch (type) {
    case 'upload':
      switch (status) {
        case 'uploading':
          return notificationTemplates.upload.uploading(fileName!, subjectName!, categoryName!);
        case 'processing':
          return notificationTemplates.upload.processing(fileName!);
        case 'completed':
          return notificationTemplates.upload.completed(fileName!, subjectName!, categoryName!);
        case 'failed':
          return notificationTemplates.upload.failed(fileName!);
        default:
          return notificationTemplates.upload.processing(fileName!);
      }
    case 'generic':
      switch (status) {
        case 'completed':
          return notificationTemplates.generic.success('Success', 'Operation completed successfully');
        case 'failed':
          return notificationTemplates.generic.error('Error', 'Operation failed');
        default:
          return notificationTemplates.generic.info('Info', 'Operation in progress');
      }
    default:
      return notificationTemplates.generic.info('Info', 'Operation in progress');
  }
};
