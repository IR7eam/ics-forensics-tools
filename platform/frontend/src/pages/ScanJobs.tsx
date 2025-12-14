import { useEffect, useMemo, useState } from 'react';
import { Button, Card, Form, Input, Modal, Space, Table, Tag, Tooltip, message } from 'antd';
import { apiClient } from '../api/client';

interface ScanJob {
  id?: number;
  name: string;
  initiated_by: string;
  target_range: string[];
  plugins: string[];
  status?: string;
  rate_limit_rps?: number;
  connect_timeout_s?: number;
  read_timeout_s?: number;
  max_retries?: number;
  retry_backoff_s?: number;
}

interface PluginSpec {
  name: string;
  protocol: string;
  device_types: string[];
  allowed_operations: string[];
  dangerous_operations: string[];
  description: string;
}

export function ScanJobsPage() {
  const [jobs, setJobs] = useState<ScanJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [pluginSpecs, setPluginSpecs] = useState<PluginSpec[]>([]);

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
    apiClient
      .get<PluginSpec[]>('/plugins')
      .then((res) => setPluginSpecs(res.data))
      .catch(() => message.error('Failed to load plugin registry'));
  }, []);

  const handleCreate = async (values: any) => {
    const payload: ScanJob = {
      name: values.name,
      initiated_by: values.initiated_by || 'ui',
      target_range: values.target_range ? values.target_range.split(',').map((t: string) => t.trim()) : [],
      plugins: values.plugins ? values.plugins.split(',').map((p: string) => p.trim()) : [],
      rate_limit_rps: values.rate_limit_rps ? Number(values.rate_limit_rps) : 1,
      connect_timeout_s: values.connect_timeout_s ? Number(values.connect_timeout_s) : 3,
      read_timeout_s: values.read_timeout_s ? Number(values.read_timeout_s) : 5,
      max_retries: values.max_retries ? Number(values.max_retries) : 1,
      retry_backoff_s: values.retry_backoff_s ? Number(values.retry_backoff_s) : 0.5
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

  const handleRun = async (jobId: number) => {
    try {
      await apiClient.post(`/scan-jobs/${jobId}/run`);
      message.success('Job queued');
      fetchJobs();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Queue failed');
    }
  };

  const handleCancel = async (jobId: number) => {
    try {
      await apiClient.post(`/scan-jobs/${jobId}/cancel`);
      message.success('Cancellation requested');
      fetchJobs();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Cancel failed');
    }
  };

  const pluginHints = useMemo(() => {
    return pluginSpecs.reduce<Record<string, PluginSpec>>((acc, spec) => {
      acc[spec.name] = spec;
      return acc;
    }, {});
  }, [pluginSpecs]);

  return (
    <Card
      title="Scan Jobs"
      extra={
        <Space>
          <Button onClick={fetchJobs}>Refresh</Button>
          <Button type="primary" onClick={() => setModalOpen(true)}>
            New Job
          </Button>
        </Space>
      }
    >
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
            render: (plugins: string[]) => (
              <Space wrap>
                {plugins?.map((p) => {
                  const spec = pluginHints[p];
                  const dangerous = spec?.dangerous_operations?.length;
                  return (
                    <Tooltip
                      key={p}
                      title={
                        spec
                          ? `${spec.description} | allowed: ${spec.allowed_operations.join(', ')} | dangerous: ${
                              spec.dangerous_operations?.join(', ') || 'none'
                            }`
                          : undefined
                      }
                    >
                      <Tag color={dangerous ? 'red' : 'blue'}>{p}</Tag>
                    </Tooltip>
                  );
                })}
              </Space>
            )
          },
          {
            title: 'Limits',
            dataIndex: 'rate_limit_rps',
            render: (_, row: ScanJob) => (
              <div>
                <div>RPS: {row.rate_limit_rps ?? '1'}</div>
                <div>
                  Timeouts: {row.connect_timeout_s ?? '3'}s / {row.read_timeout_s ?? '5'}s
                </div>
                <div>
                  Retries: {row.max_retries ?? '1'} @ {row.retry_backoff_s ?? '0.5'}s
                </div>
              </div>
            )
          },
          { title: 'Status', dataIndex: 'status', render: (status?: string) => <Tag>{status || 'n/a'}</Tag> },
          {
            title: 'Actions',
            render: (_, row) => (
              <Space>
                <Button size="small" onClick={() => handleRun(row.id!)}>
                  Queue
                </Button>
                <Button size="small" danger onClick={() => handleCancel(row.id!)}>
                  Cancel
                </Button>
              </Space>
            )
          }
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
          <Form.Item name="rate_limit_rps" label="Rate limit (requests/sec)" initialValue={1}>
            <Input type="number" min={0} step={0.1} />
          </Form.Item>
          <Form.Item name="connect_timeout_s" label="Connect timeout (s)" initialValue={3}>
            <Input type="number" min={0.1} step={0.1} />
          </Form.Item>
          <Form.Item name="read_timeout_s" label="Read timeout (s)" initialValue={5}>
            <Input type="number" min={0.1} step={0.1} />
          </Form.Item>
          <Form.Item name="max_retries" label="Max retries" initialValue={1}>
            <Input type="number" min={0} step={1} />
          </Form.Item>
          <Form.Item name="retry_backoff_s" label="Retry backoff (s)" initialValue={0.5}>
            <Input type="number" min={0} step={0.1} />
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
