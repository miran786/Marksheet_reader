import { useEffect, useState } from 'react';
import {
  Table, Typography, Button, Space, Modal, Form, Input, Select, Tag,
  Tabs, Popconfirm, Card, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  getMappings, createMapping, deleteMapping,
  getUnresolved, resolveMapping, getSubjects,
} from '../api/client';
import type { MappingRuleResponse, MarkResponse, StandardSubject } from '../types';

export default function MappingAdmin() {
  const { message } = App.useApp();
  const [mappings, setMappings] = useState<MappingRuleResponse[]>([]);
  const [unresolved, setUnresolved] = useState<MarkResponse[]>([]);
  const [subjects, setSubjects] = useState<StandardSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const load = () => {
    setLoading(true);
    Promise.all([getMappings(), getUnresolved(), getSubjects()])
      .then(([m, u, s]) => { setMappings(m); setUnresolved(u); setSubjects(s); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (values: { raw_text: string; standard_subject_id: number }) => {
    try {
      await createMapping(values);
      message.success('Mapping created');
      setModalOpen(false);
      form.resetFields();
      load();
    } catch {
      message.error('Failed to create mapping');
    }
  };

  const handleDelete = async (id: number) => {
    await deleteMapping(id);
    message.success('Mapping deleted');
    load();
  };

  const handleResolve = async (markId: number, subjectId: number) => {
    await resolveMapping(markId, subjectId);
    message.success('Mapping resolved — rule auto-created for future use');
    load();
  };

  const mappingColumns = [
    { title: 'Raw Text (OCR)', dataIndex: 'raw_text', key: 'raw' },
    {
      title: 'Maps To', key: 'maps_to',
      render: (_: unknown, r: MappingRuleResponse) => (
        <Tag color="blue">{r.standard_subject_name || `ID: ${r.standard_subject_id}`}</Tag>
      ),
    },
    {
      title: 'Board', dataIndex: 'board_name', key: 'board',
      render: (v: string | null) => v || 'Global',
    },
    {
      title: 'Source', key: 'source',
      render: (_: unknown, r: MappingRuleResponse) => (
        <Tag color={r.is_manual ? 'purple' : 'cyan'}>{r.is_manual ? 'Manual' : 'Auto'}</Tag>
      ),
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, r: MappingRuleResponse) => (
        <Popconfirm title="Delete this mapping?" onConfirm={() => handleDelete(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  const unresolvedColumns = [
    { title: 'Raw Subject Name', dataIndex: 'raw_subject_name', key: 'raw' },
    {
      title: 'Marks', key: 'marks',
      render: (_: unknown, r: MarkResponse) =>
        r.marks_obtained != null ? `${r.marks_obtained}/${r.max_marks || '?'}` : '-',
    },
    {
      title: 'Map To Subject', key: 'resolve',
      render: (_: unknown, r: MarkResponse) => (
        <Select
          size="small"
          style={{ width: 250 }}
          placeholder="Select standard subject"
          showSearch
          optionFilterProp="label"
          options={subjects.map(s => ({ label: `${s.name} (${s.code})`, value: s.id }))}
          onChange={(val) => handleResolve(r.id, val)}
        />
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>Subject Mappings</Typography.Title>
      <Tabs items={[
        {
          key: 'rules',
          label: `Mapping Rules (${mappings.length})`,
          children: (
            <>
              <Space style={{ marginBottom: 16 }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
                  Add Mapping Rule
                </Button>
              </Space>
              <Table
                dataSource={mappings}
                columns={mappingColumns}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 20 }}
              />
            </>
          ),
        },
        {
          key: 'unresolved',
          label: (
            <span>
              Unresolved {unresolved.length > 0 && <Tag color="red">{unresolved.length}</Tag>}
            </span>
          ),
          children: (
            <Card>
              <Typography.Paragraph type="secondary">
                These subjects could not be automatically mapped. Select the correct standard subject
                to resolve them. A mapping rule will be auto-created for future use.
              </Typography.Paragraph>
              <Table
                dataSource={unresolved}
                columns={unresolvedColumns}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 20 }}
              />
            </Card>
          ),
        },
      ]} />

      <Modal
        title="Add Mapping Rule"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="raw_text" label="Raw Text (as OCR reads it)" rules={[{ required: true }]}>
            <Input placeholder="e.g., MATHEMATICS-041" />
          </Form.Item>
          <Form.Item name="standard_subject_id" label="Maps to Standard Subject" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={subjects.map(s => ({ label: `${s.name} (${s.code})`, value: s.id }))}
              placeholder="Select subject"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
