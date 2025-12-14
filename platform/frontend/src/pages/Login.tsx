import { useState } from 'react';
import { Button, Card, Form, Input, message, Typography } from 'antd';
import { login, setAuthToken } from '../api/client';

interface Props {
  onLogin: (token: string) => void;
}

export function LoginPage({ onLogin }: Props) {
  const [loading, setLoading] = useState(false);

  const handleFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const tokenResponse = await login(values.username, values.password);
      setAuthToken(tokenResponse.access_token);
      onLogin(tokenResponse.access_token);
      message.success('Authenticated successfully');
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <Card style={{ width: 360 }}>
        <Typography.Title level={4}>Sign in</Typography.Title>
        <Form layout="vertical" onFinish={handleFinish} initialValues={{ username: 'admin', password: 'admin' }}>
          <Form.Item name="username" label="Username" rules={[{ required: true, message: 'Username required' }]}>
            <Input autoFocus placeholder="dev" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, message: 'Password required' }]}>
            <Input.Password placeholder="dev" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              Get Token
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
