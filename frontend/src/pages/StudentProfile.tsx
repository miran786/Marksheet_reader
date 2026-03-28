import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Statistic,
  Table,
  Tag,
  Button,
  Typography,
  Space,
  Progress,
  Row,
  Col,
  Skeleton,
  Empty,
  App,
} from 'antd';
import { ArrowLeftOutlined, EyeOutlined } from '@ant-design/icons';
import api from '../api/client';

const { Title } = Typography;

interface Mark {
  subject: string;
  raw_subject: string;
  marks_obtained: number | null;
  max_marks: number | null;
  grade: string | null;
  is_verified: boolean;
}

interface Marksheet {
  id: number;
  file_name: string;
  processing_status: string;
  board_name: string | null;
  uploaded_at: string;
  confidence_score: number | null;
  total_obtained: number | null;
  total_max: number | null;
  percentage: number | null;
  subjects_count: number;
  marks: Mark[];
}

interface SubjectAttempt {
  marksheet_id: number;
  marks_obtained: number | null;
  max_marks: number | null;
  percentage: number | null;
  grade: string | null;
}

interface SubjectSummary {
  subject: string;
  attempts: SubjectAttempt[];
}

interface StudentProfileData {
  student: {
    id: number;
    name: string;
    roll_number: string | null;
    board_name: string | null;
    exam_year: number | null;
    exam_type: string | null;
    school_name: string | null;
  };
  marksheets: Marksheet[];
  subject_summary: SubjectSummary[];
  total_marksheets: number;
}

const statusColor: Record<string, string> = {
  completed: 'green',
  review: 'orange',
  failed: 'red',
  pending: 'blue',
  processing: 'cyan',
};

function getProgressColor(pct: number): string {
  if (pct >= 60) return '#52c41a';
  if (pct >= 40) return '#faad14';
  return '#ff4d4f';
}

export default function StudentProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [profile, setProfile] = useState<StudentProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.get(`/students/${id}/profile`)
      .then(r => setProfile(r.data))
      .catch(() => message.error('Failed to load student profile'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')} style={{ marginBottom: 16 }}>
          Back to Students
        </Button>
        <Card>
          <Skeleton active paragraph={{ rows: 10 }} />
        </Card>
      </div>
    );
  }

  if (!profile) {
    return (
      <div>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/students')} style={{ marginBottom: 16 }}>
          Back to Students
        </Button>
        <Card>
          <Empty description="Student not found" />
        </Card>
      </div>
    );
  }

  const { student, marksheets, total_marksheets } = profile;

  // Average percentage across all marksheets that have a percentage value
  const marksheetsWithPct = marksheets.filter(m => m.percentage != null);
  const avgPercentage = marksheetsWithPct.length > 0
    ? marksheetsWithPct.reduce((sum, m) => sum + (m.percentage ?? 0), 0) / marksheetsWithPct.length
    : null;

  // Best subject: from subject_summary, subject with highest average percentage across attempts
  let bestSubject = '-';
  if (profile.subject_summary.length > 0) {
    let bestAvg = -1;
    for (const s of profile.subject_summary) {
      const attemptsWithPct = s.attempts.filter(a => a.percentage != null);
      if (attemptsWithPct.length === 0) continue;
      const avg = attemptsWithPct.reduce((sum, a) => sum + (a.percentage ?? 0), 0) / attemptsWithPct.length;
      if (avg > bestAvg) {
        bestAvg = avg;
        bestSubject = s.subject;
      }
    }
  }

  // Subject performance table — from latest marksheet's marks array
  const latestMarksheet = marksheets.length > 0 ? marksheets[0] : null;
  const subjectColumns = [
    { title: 'Subject', dataIndex: 'subject', key: 'subject' },
    {
      title: 'Marks Obtained',
      dataIndex: 'marks_obtained',
      key: 'marks_obtained',
      render: (v: number | null) => v ?? '-',
    },
    {
      title: 'Max Marks',
      dataIndex: 'max_marks',
      key: 'max_marks',
      render: (v: number | null) => v ?? '-',
    },
    {
      title: 'Percentage',
      key: 'percentage',
      render: (_: unknown, r: Mark) => {
        if (r.marks_obtained == null || r.max_marks == null || r.max_marks === 0) return '-';
        const pct = (r.marks_obtained / r.max_marks) * 100;
        return (
          <Space>
            <Progress
              percent={parseFloat(pct.toFixed(1))}
              size="small"
              style={{ width: 120 }}
              strokeColor={getProgressColor(pct)}
            />
          </Space>
        );
      },
    },
    {
      title: 'Grade',
      dataIndex: 'grade',
      key: 'grade',
      render: (v: string | null) => v || '-',
    },
  ];

  // Marksheet history table
  const historyColumns = [
    { title: 'File', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
    {
      title: 'Board',
      dataIndex: 'board_name',
      key: 'board_name',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Status',
      dataIndex: 'processing_status',
      key: 'status',
      render: (s: string) => (
        <Tag color={statusColor[s] || 'default'}>{s.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Total Score',
      key: 'total_score',
      render: (_: unknown, r: Marksheet) =>
        r.total_obtained != null && r.total_max != null
          ? `${r.total_obtained} / ${r.total_max}`
          : '-',
    },
    {
      title: 'Percentage',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (v: number | null) => v != null ? `${v.toFixed(1)}%` : '-',
    },
    {
      title: 'Uploaded At',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, r: Marksheet) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/marksheets/${r.id}`)}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/students')}
        style={{ marginBottom: 16 }}
      >
        Back to Students
      </Button>

      {/* Header Card */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={3} style={{ marginBottom: 16 }}>{student.name}</Title>
        <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }}>
          <Descriptions.Item label="Roll Number">{student.roll_number || '-'}</Descriptions.Item>
          <Descriptions.Item label="Board">{student.board_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="School">{student.school_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="Exam Year">{student.exam_year || '-'}</Descriptions.Item>
          <Descriptions.Item label="Exam Type">{student.exam_type || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Summary Stats */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Total Marksheets" value={total_marksheets} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Average Percentage"
              value={avgPercentage != null ? parseFloat(avgPercentage.toFixed(1)) : '-'}
              suffix={avgPercentage != null ? '%' : ''}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title="Best Subject" value={bestSubject} />
          </Card>
        </Col>
      </Row>

      {/* Subject Performance Table */}
      <Card title="Subject Performance (Latest Marksheet)" style={{ marginBottom: 16 }}>
        {latestMarksheet && latestMarksheet.marks.length > 0 ? (
          <Table
            dataSource={latestMarksheet.marks}
            columns={subjectColumns}
            rowKey="subject"
            pagination={false}
            scroll={{ x: 600 }}
          />
        ) : (
          <Empty description="No subject data available" />
        )}
      </Card>

      {/* Marksheet History Table */}
      <Card title="Marksheet History">
        {marksheets.length > 0 ? (
          <Table
            dataSource={marksheets}
            columns={historyColumns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            scroll={{ x: 800 }}
          />
        ) : (
          <Empty description="No marksheets found" />
        )}
      </Card>
    </div>
  );
}
