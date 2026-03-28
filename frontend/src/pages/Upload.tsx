import { useState } from 'react';
import { Upload as AntUpload, Button, Card, Typography, Tag, Tabs, Steps, App, Table } from 'antd';
import { InboxOutlined, UploadOutlined, LoadingOutlined, CheckCircleOutlined, FileSearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { uploadSingle, uploadBulk } from '../api/client';
import type { UploadResponse } from '../types';

const { Dragger } = AntUpload;

export default function Upload() {
  const [results, setResults] = useState<UploadResponse[]>([]);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const { message } = App.useApp();

  const handleSingleUpload = async (file: File) => {
    setUploading(true);
    setCurrentStep(0);
    try {
      setCurrentStep(1);
      const result = await uploadSingle(file);
      setCurrentStep(2);
      setResults(prev => [result, ...prev]);
      message.success(`${file.name} uploaded successfully!`);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
      if (status === 409) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Duplicate file';
        message.warning(`⚠️ ${detail}`);
      } else {
        message.error(`Failed to upload ${file.name}`);
      }
    } finally {
      setUploading(false);
      setTimeout(() => setCurrentStep(-1), 2000);
    }
  };

  const handleBulkUpload = async (files: File[]) => {
    setUploading(true);
    setCurrentStep(0);
    try {
      setCurrentStep(1);
      const batch = await uploadBulk(files);
      setCurrentStep(2);
      setResults(prev => [...batch.marksheets, ...prev]);
      message.success(`Batch uploaded: ${batch.total_files} files`);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
      if (status === 409) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Duplicate file detected';
        message.warning(`⚠️ ${detail}`);
      } else {
        message.error('Bulk upload failed');
      }
    } finally {
      setUploading(false);
      setTimeout(() => setCurrentStep(-1), 2000);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'review': return 'orange';
      case 'failed': return 'red';
      case 'pending': return 'blue';
      case 'processing': return 'cyan';
      default: return 'default';
    }
  };

  return (
    <div>
      <Typography.Title level={3}>Upload Marksheets</Typography.Title>

      {currentStep >= 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Steps
            current={currentStep}
            items={[
              {
                title: 'Preparing',
                icon: currentStep === 0 ? <LoadingOutlined /> : undefined,
              },
              {
                title: 'Uploading',
                icon: currentStep === 1 ? <LoadingOutlined /> : undefined,
              },
              {
                title: 'Processing',
                icon: currentStep === 2 ? <CheckCircleOutlined /> : <FileSearchOutlined />,
              },
            ]}
          />
        </Card>
      )}

      <Tabs
        items={[
          {
            key: 'single',
            label: 'Single Upload',
            children: (
              <Card>
                <Dragger
                  accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.pdf"
                  multiple={false}
                  showUploadList={false}
                  customRequest={({ file }) => handleSingleUpload(file as File)}
                  disabled={uploading}
                >
                  <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                  <p className="ant-upload-text">Click or drag a marksheet image to upload</p>
                  <p className="ant-upload-hint">
                    Supports: JPEG, PNG, BMP, TIFF, WebP, PDF
                  </p>
                </Dragger>
              </Card>
            ),
          },
          {
            key: 'bulk',
            label: 'Bulk Upload',
            children: (
              <Card>
                <AntUpload
                  accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.pdf"
                  multiple
                  showUploadList
                  beforeUpload={(_, fileList) => {
                    handleBulkUpload(fileList as unknown as File[]);
                    return false;
                  }}
                  disabled={uploading}
                >
                  <Button icon={<UploadOutlined />} loading={uploading} size="large">
                    Select Multiple Files
                  </Button>
                </AntUpload>
              </Card>
            ),
          },
        ]}
      />

      {results.length > 0 && (
        <Card title="Upload Results" style={{ marginTop: 16 }}>
          <Table
            dataSource={results}
            rowKey="id"
            pagination={false}
            size="small"
            columns={[
              { title: 'File', dataIndex: 'file_name', key: 'file_name' },
              { title: 'Message', dataIndex: 'message', key: 'message', ellipsis: true },
              {
                title: 'Status',
                dataIndex: 'processing_status',
                key: 'status',
                render: (s: string) => <Tag color={statusColor(s)}>{s.toUpperCase()}</Tag>,
              },
            ] as ColumnsType<UploadResponse>}
          />
        </Card>
      )}
    </div>
  );
}
