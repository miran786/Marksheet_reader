import { useEffect, useState } from 'react';
import { Table, Typography, Input, Space, Tag, Button } from 'antd';
import { SearchOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getStudents } from '../api/client';
import type { StudentResponse } from '../types';

export default function Students() {
  const [students, setStudents] = useState<StudentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const load = () => {
    setLoading(true);
    getStudents({ page, search: search || undefined })
      .then(res => { setStudents(res.students); setTotal(res.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [page, search]);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: 'Name', dataIndex: 'name', key: 'name',
      render: (v: string, record: StudentResponse) => (
        <span
          style={{ color: '#1677ff', cursor: 'pointer' }}
          onClick={() => navigate(`/students/${record.id}`)}
        >
          {v}
        </span>
      ),
    },
    { title: 'Roll Number', dataIndex: 'roll_number', key: 'roll' },
    {
      title: 'Board', dataIndex: 'board_name', key: 'board',
      render: (v: string | null) => v ? <Tag>{v}</Tag> : '-',
    },
    { title: 'Exam Year', dataIndex: 'exam_year', key: 'year', render: (v: number | null) => v || '-' },
    { title: 'Exam Type', dataIndex: 'exam_type', key: 'type', render: (v: string | null) => v || '-' },
    { title: 'School', dataIndex: 'school_name', key: 'school', render: (v: string | null) => v || '-', ellipsis: true },
    { title: 'Marksheets', dataIndex: 'marksheet_count', key: 'ms_count' },
    {
      title: 'Profile', key: 'profile',
      render: (_: unknown, record: StudentResponse) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate(`/students/${record.id}`)}
        >
          Profile
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>Students</Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="Search by name or roll number"
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          style={{ width: 300 }}
          allowClear
        />
      </Space>
      <Table
        dataSource={students}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: setPage,
          showTotal: (t) => `Total ${t} students`,
        }}
      />
    </div>
  );
}
