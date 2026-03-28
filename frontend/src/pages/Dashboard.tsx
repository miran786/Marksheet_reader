import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Typography, Skeleton, Empty, Button, List, Tag } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  TeamOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  BankOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  UploadOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons';
import { getDashboardStats, getMarksheets } from '../api/client';
import type { DashboardStats, MarksheetResponse } from '../types';

const statusColor: Record<string, string> = {
  completed: 'green',
  review: 'orange',
  failed: 'red',
  pending: 'blue',
  processing: 'cyan',
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentMarksheets, setRecentMarksheets] = useState<MarksheetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getMarksheets({ page: 1, page_size: 5 }),
    ])
      .then(([s, ms]) => {
        setStats(s);
        setRecentMarksheets(Array.isArray(ms) ? ms.slice(0, 5) : []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <Typography.Title level={3}>Dashboard</Typography.Title>
        <Row gutter={[16, 16]}>
          {Array.from({ length: 8 }).map((_, i) => (
            <Col xs={24} sm={12} md={8} lg={6} key={i}>
              <Card>
                <Skeleton active paragraph={{ rows: 1 }} />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  }

  if (!stats) {
    return (
      <Empty
        description="Failed to load dashboard stats"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" onClick={() => window.location.reload()}>Retry</Button>
      </Empty>
    );
  }

  const cards = [
    { title: 'Total Students', value: stats.total_students, icon: <TeamOutlined />, color: '#1890ff' },
    { title: 'Total Marksheets', value: stats.total_marksheets, icon: <FileTextOutlined />, color: '#722ed1' },
    { title: 'Completed', value: stats.completed, icon: <CheckCircleOutlined />, color: '#52c41a' },
    { title: 'Pending Review', value: stats.pending_review, icon: <WarningOutlined />, color: '#faad14' },
    { title: 'Failed', value: stats.failed, icon: <CloseCircleOutlined />, color: '#ff4d4f' },
    { title: 'Boards', value: stats.total_boards, icon: <BankOutlined />, color: '#13c2c2' },
    { title: 'Standard Subjects', value: stats.total_subjects, icon: <BookOutlined />, color: '#eb2f96' },
    { title: 'Unresolved Mappings', value: stats.unresolved_mappings, icon: <QuestionCircleOutlined />, color: '#fa8c16' },
  ];

  return (
    <div>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        {cards.map(c => (
          <Col xs={24} sm={12} md={8} lg={6} key={c.title}>
            <Card hoverable>
              <Statistic
                title={c.title}
                value={c.value}
                prefix={<span style={{ color: c.color }}>{c.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {/* Quick Upload Card */}
        <Col xs={24} md={8}>
          <Card
            hoverable
            onClick={() => navigate('/upload')}
            style={{ textAlign: 'center', cursor: 'pointer' }}
          >
            <CloudUploadOutlined style={{ fontSize: 48, color: '#1677ff', marginBottom: 12 }} />
            <Typography.Title level={4} style={{ margin: 0 }}>Quick Upload</Typography.Title>
            <Typography.Text type="secondary">
              Upload a new marksheet for processing
            </Typography.Text>
            <div style={{ marginTop: 12 }}>
              <Button type="primary" icon={<UploadOutlined />}>Upload Now</Button>
            </div>
          </Card>
        </Col>

        {/* Recent Activity */}
        <Col xs={24} md={16}>
          <Card title="Recent Activity (Last 5 Marksheets)">
            {recentMarksheets.length === 0 ? (
              <Empty
                description="No marksheets yet -- upload your first one!"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={() => navigate('/upload')}>
                  Upload Marksheet
                </Button>
              </Empty>
            ) : (
              <List
                dataSource={recentMarksheets}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        key="view"
                        size="small"
                        type="link"
                        onClick={() => navigate(`/marksheets/${item.id}`)}
                      >
                        View
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={item.file_name}
                      description={
                        <>
                          {item.student_name || 'Unknown student'} &middot;{' '}
                          {new Date(item.uploaded_at).toLocaleString()}
                        </>
                      }
                    />
                    <Tag color={statusColor[item.processing_status] || 'default'}>
                      {item.processing_status.toUpperCase()}
                    </Tag>
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
