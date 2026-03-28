import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Descriptions, Table, Tag, Button, Typography, Space, Input,
  Select, Skeleton, Empty, App,
} from 'antd';
import {
  ArrowLeftOutlined, CheckOutlined, ZoomInOutlined, ZoomOutOutlined,
  RotateRightOutlined, ColumnWidthOutlined,
} from '@ant-design/icons';
import { getMarksheet, updateMark, verifyMarksheet, getSubjects } from '../api/client';
import type { MarksheetResponse, MarkResponse, StandardSubject } from '../types';

export default function MarksheetDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [marksheet, setMarksheet] = useState<MarksheetResponse | null>(null);
  const [subjects, setSubjects] = useState<StandardSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [fitWidth, setFitWidth] = useState(false);
  const { message } = App.useApp();

  const load = () => {
    setLoading(true);
    Promise.all([
      getMarksheet(Number(id)),
      getSubjects(),
    ])
      .then(([ms, subs]) => { setMarksheet(ms); setSubjects(subs); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleMarkUpdate = async (markId: number, field: string, value: unknown) => {
    if (!marksheet) return;
    try {
      await updateMark(marksheet.id, markId, { [field]: value });
      message.success('Mark updated');
      load();
    } catch {
      message.error('Failed to update mark');
    }
  };

  const handleVerify = async () => {
    if (!marksheet) return;
    try {
      await verifyMarksheet(marksheet.id);
      message.success('Marksheet verified successfully');
      load();
    } catch {
      message.error('Failed to verify marksheet');
    }
  };

  if (loading) {
    return (
      <div>
        <Skeleton active paragraph={{ rows: 2 }} style={{ marginBottom: 16 }} />
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
        <Card style={{ marginTop: 16 }}>
          <Skeleton.Image active style={{ width: '100%', height: 300 }} />
        </Card>
        <Card style={{ marginTop: 16 }}>
          <Skeleton active paragraph={{ rows: 6 }} />
        </Card>
      </div>
    );
  }

  if (!marksheet) {
    return (
      <Empty description="Marksheet not found">
        <Button type="primary" onClick={() => navigate('/marksheets')}>
          Back to Marksheets
        </Button>
      </Empty>
    );
  }

  const confidenceColor = (c: number | null) => {
    if (c == null) return 'default';
    if (c >= 85) return 'green';
    if (c >= 60) return 'orange';
    return 'red';
  };

  const columns = [
    {
      title: 'Raw Subject Name', dataIndex: 'raw_subject_name', key: 'raw',
      render: (v: string, r: MarkResponse) => (
        <Input
          defaultValue={v}
          size="small"
          onBlur={(e) => {
            if (e.target.value !== v) handleMarkUpdate(r.id, 'raw_subject_name', e.target.value);
          }}
        />
      ),
    },
    {
      title: 'Mapped Subject', key: 'mapped',
      render: (_: unknown, r: MarkResponse) => (
        <Select
          size="small"
          style={{ width: '100%' }}
          value={r.standard_subject_id}
          placeholder="Select subject"
          showSearch
          optionFilterProp="label"
          options={subjects.map(s => ({ label: `${s.name} (${s.code})`, value: s.id }))}
          onChange={(val) => handleMarkUpdate(r.id, 'standard_subject_id', val)}
        />
      ),
    },
    {
      title: 'Confidence', key: 'conf',
      render: (_: unknown, r: MarkResponse) => (
        <Tag color={confidenceColor(r.mapping_confidence)}>
          {r.mapping_confidence != null ? `${r.mapping_confidence.toFixed(0)}%` : 'N/A'}
        </Tag>
      ),
    },
    {
      title: 'Marks', key: 'marks',
      render: (_: unknown, r: MarkResponse) =>
        r.marks_obtained != null
          ? `${r.marks_obtained}${r.max_marks ? ` / ${r.max_marks}` : ''}`
          : '-',
    },
    {
      title: 'Grade', dataIndex: 'grade', key: 'grade',
      render: (v: string | null) => v || '-',
    },
    {
      title: 'Verified', key: 'verified',
      render: (_: unknown, r: MarkResponse) => (
        <Tag color={r.is_verified ? 'green' : 'default'}>
          {r.is_verified ? 'Yes' : 'No'}
        </Tag>
      ),
    },
  ];

  const imageUrl = `/api/marksheets/${marksheet.id}/image`;

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.25));
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);
  const handleFitWidth = () => {
    setFitWidth(prev => !prev);
    if (!fitWidth) setZoom(1);
  };

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/marksheets')}>Back</Button>
        {marksheet.processing_status === 'review' && (
          <Button type="primary" icon={<CheckOutlined />} onClick={handleVerify}>
            Verify All & Complete
          </Button>
        )}
      </Space>

      <Card title={`Marksheet: ${marksheet.file_name}`} style={{ marginBottom: 16 }}>
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }}>
          <Descriptions.Item label="Student">{marksheet.student_name || '-'}</Descriptions.Item>
          <Descriptions.Item label="Board">{marksheet.board_name || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Status">
            <Tag color={marksheet.processing_status === 'completed' ? 'green' : 'orange'}>
              {marksheet.processing_status.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Confidence">
            {marksheet.confidence_score != null ? `${marksheet.confidence_score.toFixed(0)}%` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Uploaded">{new Date(marksheet.uploaded_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="File Type">{marksheet.file_type.toUpperCase()}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title="Uploaded Image"
        style={{ marginBottom: 16 }}
        extra={
          <Space>
            <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} size="small" title="Zoom Out" />
            <Typography.Text style={{ minWidth: 50, textAlign: 'center', display: 'inline-block' }}>
              {Math.round(zoom * 100)}%
            </Typography.Text>
            <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} size="small" title="Zoom In" />
            <Button icon={<RotateRightOutlined />} onClick={handleRotate} size="small" title="Rotate 90 degrees" />
            <Button
              icon={<ColumnWidthOutlined />}
              onClick={handleFitWidth}
              size="small"
              type={fitWidth ? 'primary' : 'default'}
              title="Fit to Width"
            />
          </Space>
        }
      >
        <div style={{
          overflow: 'auto',
          maxHeight: 600,
          textAlign: 'center',
          border: '1px solid #f0f0f0',
          borderRadius: 4,
          padding: 8,
        }}>
          <img
            src={imageUrl}
            alt="Marksheet"
            style={{
              transform: `scale(${zoom}) rotate(${rotation}deg)`,
              transformOrigin: 'center center',
              transition: 'transform 0.3s ease',
              maxWidth: fitWidth ? '100%' : 'none',
              width: fitWidth ? '100%' : 'auto',
            }}
          />
        </div>
      </Card>

      <Card title={`Extracted Marks (${marksheet.marks.length} subjects)`}>
        <Table
          dataSource={marksheet.marks}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
          scroll={{ x: 700 }}
        />
      </Card>
    </div>
  );
}
