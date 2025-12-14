import { useEffect, useState } from 'react';
import { Card, Table, Form, Input, Button, Space, Tag, Tooltip } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { fetchAuditLogs } from '../api/client';

interface AuditLog {
  id: number;
  actor: string;
  action: string;
  resource: string;
  status: string;
  detail: Record<string, unknown>;
  timestamp: string;
}

const statusColor: Record<string, string> = {
  success: 'green',
  denied: 'red',
  error: 'orange'
};

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async (filters?: Record<string, unknown>) => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs(filters || { limit: 200 });
      setLogs(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load({ limit: 200 });
  }, []);

  const columns: ColumnsType<AuditLog> = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      render: (value: string) => new Date(value).toLocaleString()
    },
    { title: 'Actor', dataIndex: 'actor' },
    { title: 'Action', dataIndex: 'action' },
    { title: 'Resource', dataIndex: 'resource' },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (value: string) => <Tag color={statusColor[value] || 'blue'}>{value}</Tag>
    },
    {
      title: 'Detail',
      dataIndex: 'detail',
      render: (detail: Record<string, unknown>) => (
        <Tooltip title={JSON.stringify(detail)}>{Object.keys(detail || {}).length ? 'View' : '—'}</Tooltip>
      )
    }
  ];

  return (
    <Card title="Audit Trail" extra={<span>Latest platform actions</span>}>
      <Form layout="inline" onFinish={load} style={{ marginBottom: 16 }}>
        <Form.Item name="actor">
          <Input placeholder="Actor" allowClear />
        </Form.Item>
        <Form.Item name="action">
          <Input placeholder="Action" allowClear />
        </Form.Item>
        <Form.Item name="resource">
          <Input placeholder="Resource" allowClear />
        </Form.Item>
        <Form.Item name="status">
          <Input placeholder="Status" allowClear />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              Filter
            </Button>
            <Button onClick={() => load({ limit: 200 })}>Reset</Button>
          </Space>
        </Form.Item>
      </Form>
      <Table
        size="small"
        rowKey="id"
        dataSource={logs}
        columns={columns}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
}
