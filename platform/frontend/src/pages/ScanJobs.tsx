import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Modal, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface ScanJob {
  id?: number;
  name: string;
  initiated_by: string;
  target_range: string[];
  plugins: string[];
  status?: string;
}

export function ScanJobsPage() {
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchJobs = () => {
    setLoading(true);
    apiClient
      .get<ScanJob[]>('/scan-jobs')
      .then((res) => setJobs(res.data))
      .catch(() => message.error('Failed to fetch scan jobs'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleCreate = async (values: any) => {
    const payload: ScanJob = {
      name: values.name,
      initiated_by: values.initiated_by || 'ui',
      target_range: values.target_range ? values.target_range.split(',').map((t: string) => t.trim()) : [],
      plugins: values.plugins ? values.plugins.split(',').map((p: string) => p.trim()) : []
    };
    try {
      await apiClient.post('/scan-jobs', payload);
      message.success('Scan job created');
      setModalOpen(false);
      fetchJobs();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Failed to create job');
    }
  };

  return (
    <Card title="Scan Jobs" extra={<Button onClick={() => setModalOpen(true)}>New Job</Button>}>
      <Table
        rowKey={(row) => String(row.id)}
        loading={loading}
        dataSource={jobs}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'Name', dataIndex: 'name' },
          { title: 'Initiated By', dataIndex: 'initiated_by' },
          {
            title: 'Targets',
            dataIndex: 'target_range',
            render: (targets: string[]) => targets?.map((t) => <Tag key={t}>{t}</Tag>)
          },
          {
            title: 'Plugins',
            dataIndex: 'plugins',
            render: (plugins: string[]) => plugins?.map((p) => <Tag key={p}>{p}</Tag>)
          },
          { title: 'Status', dataIndex: 'status' }
        ]}
      />

      <Modal open={modalOpen} title="Create Scan Job" onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Job Name" rules={[{ required: true, message: 'Required' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="initiated_by" label="Initiated By">
            <Input placeholder="analyst" />
          </Form.Item>
          <Form.Item name="target_range" label="Targets (comma separated)">
            <Input placeholder="10.0.0.5, 10.0.0.6" />
          </Form.Item>
          <Form.Item name="plugins" label="Plugins (comma separated)">
            <Input placeholder="modbus, opcua, snmp" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
