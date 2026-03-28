import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Form, Input, Select, Space, Modal, App } from 'antd';
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons';
import { getSubjects, createSubject, exportCSV } from '../api/client';
import type { StandardSubject } from '../types';

export default function Settings() {
  const { message } = App.useApp();
  const [subjects, setSubjects] = useState<StandardSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const load = () => {
    setLoading(true);
    getSubjects().then(setSubjects).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (values: { name: string; code: string; category?: string }) => {
    try {
      await createSubject(values);
      message.success('Subject added');
      setModalOpen(false);
      form.resetFields();
      load();
    } catch {
      message.error('Failed to add subject');
    }
  };

  const handleExport = async () => {
    try {
      const blob = await exportCSV();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'marksheet_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('CSV exported');
    } catch {
      message.error('Export failed');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Code', dataIndex: 'code', key: 'code' },
    { title: 'Category', dataIndex: 'category', key: 'category', render: (v: string | null) => v || '-' },
  ];

  return (
    <div>
      <Typography.Title level={3}>Settings</Typography.Title>

      <Card title="Export Data" style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>
          Export All Marks as CSV
        </Button>
        <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
          Downloads a CSV file with all student marks data for ERP import.
        </Typography.Paragraph>
      </Card>

      <Card
        title="Standard Subjects"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Add Subject
          </Button>
        }
      >
        <Table
          dataSource={subjects}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>

      <Modal
        title="Add Standard Subject"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Subject Name" rules={[{ required: true }]}>
            <Input placeholder="e.g., Mathematics" />
          </Form.Item>
          <Form.Item name="code" label="Subject Code" rules={[{ required: true }]}>
            <Input placeholder="e.g., MATH" />
          </Form.Item>
          <Form.Item name="category" label="Category">
            <Select
              placeholder="Select category"
              allowClear
              options={[
                { label: 'Science', value: 'Science' },
                { label: 'Language', value: 'Language' },
                { label: 'Commerce', value: 'Commerce' },
                { label: 'Arts', value: 'Arts' },
                { label: 'Other', value: 'Other' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
