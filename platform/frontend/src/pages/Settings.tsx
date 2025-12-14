import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Table, Tag, Typography, message } from 'antd';
import { apiClient, setAuthToken } from '../api/client';

interface PluginSpec {
  name: string;
  protocol: string;
  device_types: string[];
  allowed_operations: string[];
  dangerous_operations: string[];
  description: string;
}

export function SettingsPage() {
  const [form] = Form.useForm();
  const savedToken = localStorage.getItem('ics-token') || '';
  const [token, setToken] = useState(savedToken);
  const [plugins, setPlugins] = useState<PluginSpec[]>([]);

  useEffect(() => {
    apiClient
      .get<PluginSpec[]>('/plugins')
      .then((res) => setPlugins(res.data))
      .catch(() => message.error('Failed to load plugin registry'));
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
