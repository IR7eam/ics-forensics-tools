import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Timeline, Typography } from 'antd';
import { apiClient } from '../api/client';

interface Asset {
  id: number;
  ip_address?: string;
  hostname?: string;
  device_type?: string | null;
}

interface SecurityEvent {
  id: number;
  event_type: string;
  severity: string;
  created_at?: string;
  description?: string;
}

export function DashboardPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);

  useEffect(() => {
    apiClient.get<Asset[]>('/assets').then((res) => setAssets(res.data)).catch(() => setAssets([]));
    apiClient
      .get<SecurityEvent[]>('/events')
      .then((res) => setEvents(res.data.slice(0, 5)))
      .catch(() => setEvents([]));
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="Assets" value={assets.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Recent Events" value={events.length} />
          </Card>
        </Col>
      </Row>
      <Card title="Recent Security Events" style={{ marginTop: 16 }}>
        <Timeline>
          {events.map((event) => (
            <Timeline.Item color={event.severity === 'high' ? 'red' : 'blue'} key={event.id}>
              <strong>{event.event_type}</strong> — {event.description || 'no description'}
            </Timeline.Item>
          ))}
          {events.length === 0 && <Typography.Text type="secondary">No events yet</Typography.Text>}
        </Timeline>
      </Card>
    </div>
  );
}
