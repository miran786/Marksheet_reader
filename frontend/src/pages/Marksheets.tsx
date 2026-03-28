import { useEffect, useState } from 'react';
import { Table, Tag, Button, Typography, Space, Select, Popconfirm, Skeleton, Empty, Card, App } from 'antd';
import { EyeOutlined, CheckOutlined, DeleteOutlined, UploadOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getMarksheets, verifyMarksheet, deleteMarksheet, bulkVerifyMarksheets } from '../api/client';
import type { MarksheetResponse } from '../types';

const statusColor: Record<string, string> = {
  completed: 'green',
  review: 'orange',
  failed: 'red',
  pending: 'blue',
  processing: 'cyan',
};

export default function Marksheets() {
  const [data, setData] = useState<MarksheetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [bulkVerifying, setBulkVerifying] = useState(false);
  const navigate = useNavigate();
  const { message } = App.useApp();

  const load = () => {
    setLoading(true);
    getMarksheets({ status: statusFilter })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [statusFilter]);

  const handleVerify = async (id: number) => {
    try {
      await verifyMarksheet(id);
      message.success('Marksheet verified');
      load();
    } catch {
      message.error('Failed to verify marksheet');
    }
  };

  const handleBulkVerify = async () => {
    setBulkVerifying(true);
    try {
      const result = await bulkVerifyMarksheets(90);
      message.success(`Auto-verified: ${result.verified ?? 0} marksheets verified, ${result.skipped ?? 0} skipped`);
      load();
    } catch {
      message.error('Failed to bulk verify marksheets');
    } finally {
      setBulkVerifying(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteMarksheet(id);
      message.success('Marksheet deleted');
      load();
    } catch {
      message.error('Failed to delete marksheet');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'File', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
    {
      title: 'Student', dataIndex: 'student_name', key: 'student_name',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Board', dataIndex: 'board_name', key: 'board_name',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Subjects', key: 'subjects',
      render: (_: unknown, r: MarksheetResponse) => r.marks.length,
    },
    {
      title: 'Confidence', dataIndex: 'confidence_score', key: 'confidence',
      render: (v: number | null) => v != null ? `${v.toFixed(0)}%` : '-',
    },
    {
      title: 'Status', dataIndex: 'processing_status', key: 'status',
      render: (s: string) => <Tag color={statusColor[s] || 'default'}>{s.toUpperCase()}</Tag>,
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, r: MarksheetResponse) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/marksheets/${r.id}`)}>
            View
          </Button>
          {r.processing_status === 'review' && (
            <Button size="small" type="primary" icon={<CheckOutlined />} onClick={() => handleVerify(r.id)}>
              Verify
            </Button>
          )}
          <Popconfirm title="Delete this marksheet?" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div>
        <Typography.Title level={3}>Marksheets</Typography.Title>
        <Card>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Typography.Title level={3}>Marksheets</Typography.Title>
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="Filter by status"
          allowClear
          style={{ width: 200 }}
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { label: 'Pending', value: 'pending' },
            { label: 'Processing', value: 'processing' },
            { label: 'Review', value: 'review' },
            { label: 'Completed', value: 'completed' },
            { label: 'Failed', value: 'failed' },
          ]}
        />
        <Button onClick={load}>Refresh</Button>
        <Popconfirm
          title="Auto-Verify Marksheets"
          description="This will verify all marksheets with confidence ≥ 90%. Continue?"
          onConfirm={handleBulkVerify}
          okText="Yes, Verify"
          cancelText="Cancel"
        >
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={bulkVerifying}
          >
            Auto-Verify (≥90%)
          </Button>
        </Popconfirm>
      </Space>
      {data.length === 0 ? (
        <Card>
          <Empty
            description="No marksheets yet -- upload your first one!"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('/upload')}>
              Upload Marksheet
            </Button>
          </Empty>
        </Card>
      ) : (
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          scroll={{ x: 800 }}
        />
      )}
    </div>
  );
}
