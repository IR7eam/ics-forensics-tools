import { useEffect, useState } from 'react';
import { Card, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface SecurityEvent {
  id: number;
  asset_id?: number;
  severity: string;
  impact?: string;
  description: string;
  created_at?: string;
}

export function EventsPage() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get<SecurityEvent[]>('/events')
      .then((res) => setEvents(res.data))
      .catch(() => message.error('Failed to fetch events'))
      .finally(() => setLoading(false));
  }, []);

  const severityColor = (severity: string) => {
    if (severity === 'high') return 'red';
    if (severity === 'medium') return 'orange';
    return 'blue';
  };

  return (
    <Card title="Security Events">
      <Table
        rowKey={(row) => String(row.id)}
        loading={loading}
        dataSource={events}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'Asset ID', dataIndex: 'asset_id', width: 100 },
          {
            title: 'Severity',
            dataIndex: 'severity',
            render: (value: string) => <Tag color={severityColor(value)}>{value}</Tag>
          },
          { title: 'Impact', dataIndex: 'impact' },
          { title: 'Description', dataIndex: 'description' },
          { title: 'Created At', dataIndex: 'created_at' }
        ]}
      />
    </Card>
  );
}
