import { useEffect, useState } from 'react';
import { Card, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface SecurityEvent {
  id: number;
  asset_id?: number;
  severity: string;
  attack_stage?: string;
  risk_score?: number;
  recommendations?: string[];
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
          { title: 'Stage', dataIndex: 'attack_stage', render: (v) => v || 'unknown' },
          {
            title: 'Risk',
            dataIndex: 'risk_score',
            render: (v?: number) => <Tag color={v && v >= 0.7 ? 'red' : v && v >= 0.4 ? 'orange' : 'blue'}>{v ?? 0}</Tag>
          },
          { title: 'Impact', dataIndex: 'impact' },
          { title: 'Description', dataIndex: 'description' },
          {
            title: 'Recommendations',
            dataIndex: 'recommendations',
            render: (recs?: string[]) => (recs && recs.length ? recs.join('; ') : 'n/a')
          },
          { title: 'Created At', dataIndex: 'created_at' }
        ]}
      />
    </Card>
  );
}
