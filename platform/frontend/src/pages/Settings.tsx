import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, InputNumber, Space, Table, Tag, Typography, message } from 'antd';
import { apiClient, setAuthToken } from '../api/client';

interface PluginSpec {
  name: string;
  protocol: string;
  device_types: string[];
  allowed_operations: string[];
  dangerous_operations: string[];
  description: string;
}

interface BaselineProfile {
  id: number;
  asset_id?: number;
  protocol: string;
  metrics_baseline: Record<string, number>;
  trained_at?: string;
}

export function SettingsPage() {
  const [form] = Form.useForm();
  const savedToken = localStorage.getItem('ics-token') || '';
  const [token, setToken] = useState(savedToken);
  const [plugins, setPlugins] = useState<PluginSpec[]>([]);
  const [baselines, setBaselines] = useState<BaselineProfile[]>([]);
  const [baselineForm] = Form.useForm();
  const [evaluateForm] = Form.useForm();

  useEffect(() => {
    apiClient
      .get<PluginSpec[]>('/plugins')
      .then((res) => setPlugins(res.data))
      .catch(() => message.error('Failed to load plugin registry'));

    apiClient
      .get<BaselineProfile[]>('/baselines/')
      .then((res) => setBaselines(res.data))
      .catch(() => message.warning('Could not fetch baselines')); // not fatal
  }, []);

  const handleSave = () => {
    const newToken = form.getFieldValue('token') || '';
    localStorage.setItem('ics-token', newToken);
    setAuthToken(newToken);
    setToken(newToken);
    message.success('Token saved to local storage');
  };

  const handleLogout = () => {
    localStorage.removeItem('ics-token');
    setAuthToken(undefined);
    setToken('');
    message.info('Cleared token');
  };

  const handleTrainBaseline = async () => {
    try {
      const values = await baselineForm.validateFields();
      const res = await apiClient.post('/analysis/baseline/train', values);
      message.success(`Baseline trained (id=${res.data.id})`);
      setBaselines((prev) => [res.data as BaselineProfile, ...prev]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Baseline training failed';
      message.error(detail);
    }
  };

  const handleEvaluateBaseline = async () => {
    try {
      const values = await evaluateForm.validateFields();
      const payload = { ...values, metrics: JSON.parse(values.metrics) };
      const res = await apiClient.post('/analysis/baseline/evaluate', payload);
      const deviations = res.data.deviations || {};
      const deviationKeys = Object.keys(deviations);
      if (deviationKeys.length) {
        message.warning(`Deviation detected for ${deviationKeys.join(', ')}`);
      } else {
        message.success('No baseline deviations');
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Baseline evaluation failed';
      message.error(detail);
    }
  };

  return (
    <Card title="Settings">
      <Typography.Paragraph>
        API Base URL: <strong>{import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}</strong>
      </Typography.Paragraph>
      <Form form={form} layout="vertical" initialValues={{ token }}>
        <Form.Item name="token" label="Bearer Token">
          <Input.Password placeholder="Paste JWT" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" onClick={handleSave} style={{ marginRight: 8 }}>
            Save Token
          </Button>
          <Button danger onClick={handleLogout}>
            Clear Token
          </Button>
        </Form.Item>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        Baseline training (analyst role)
      </Typography.Title>
      <Form form={baselineForm} layout="inline" initialValues={{ observations_limit: 100 }}>
        <Form.Item name="asset_id" label="Asset ID" rules={[{ required: true, message: 'Provide asset id' }]}>
          <InputNumber min={1} placeholder="e.g., 1" />
        </Form.Item>
        <Form.Item name="protocol" label="Protocol" rules={[{ required: true }]}> 
          <Input placeholder="opc-ua, modbus/tcp..." />
        </Form.Item>
        <Form.Item name="observations_limit" label="Obs Limit">
          <InputNumber min={1} max={500} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" onClick={handleTrainBaseline}>Train baseline</Button>
        </Form.Item>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        Evaluate metrics against baseline
      </Typography.Title>
      <Form form={evaluateForm} layout="vertical">
        <Space style={{ width: '100%' }} direction="vertical">
          <Form.Item name="asset_id" label="Asset ID" rules={[{ required: true }]}> 
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="protocol" label="Protocol" rules={[{ required: true }]}> 
            <Input placeholder="opc-ua" />
          </Form.Item>
          <Form.Item
            name="metrics"
            label="Metrics JSON"
            rules={[{ required: true, message: 'Provide metrics as JSON, e.g., {"latency_ms": 110}' }]}
          >
            <Input.TextArea rows={3} placeholder='{"latency_ms": 120, "status": 1}' />
          </Form.Item>
          <Form.Item name="threshold" label="Z-score threshold" initialValue={3}>
            <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button onClick={handleEvaluateBaseline} type="primary">Evaluate</Button>
          </Form.Item>
        </Space>
      </Form>

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        Baseline profiles
      </Typography.Title>
      <Table
        rowKey={(row) => String(row.id)}
        dataSource={baselines}
        pagination={{ pageSize: 5 }}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'Asset ID', dataIndex: 'asset_id', width: 100 },
          { title: 'Protocol', dataIndex: 'protocol' },
          { title: 'Trained At', dataIndex: 'trained_at' },
          {
            title: 'Metrics',
            dataIndex: 'metrics_baseline',
            render: (metrics: Record<string, number>) => (
              <Typography.Text code>{JSON.stringify(metrics)}</Typography.Text>
            )
          }
        ]}
      />

      <Typography.Title level={5} style={{ marginTop: 24 }}>
        Protocol plugins (read-only defaults)
      </Typography.Title>
      <Table
        rowKey={(row) => row.name}
        dataSource={plugins}
        pagination={false}
        columns={[
          { title: 'Name', dataIndex: 'name' },
          { title: 'Protocol', dataIndex: 'protocol' },
          {
            title: 'Device Types',
            dataIndex: 'device_types',
            render: (values: string[]) => values?.map((v) => <Tag key={v}>{v}</Tag>)
          },
          { title: 'Description', dataIndex: 'description', ellipsis: true },
          {
            title: 'Allowed Ops',
            dataIndex: 'allowed_operations',
            render: (ops: string[]) => ops?.map((op) => <Tag key={op}>{op}</Tag>)
          },
          {
            title: 'Dangerous (opt-in only)',
            dataIndex: 'dangerous_operations',
            render: (ops: string[]) =>
              ops?.length ? ops.map((op) => <Tag color="red" key={op}>{op}</Tag>) : <Tag>none</Tag>
          }
        ]}
      />
    </Card>
  );
}
