import { useState } from 'react';
import { Button, Card, Form, Input, Typography, message } from 'antd';
import { setAuthToken } from '../api/client';

export function SettingsPage() {
  const [form] = Form.useForm();
  const savedToken = localStorage.getItem('ics-token') || '';
  const [token, setToken] = useState(savedToken);

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
    </Card>
  );
}
