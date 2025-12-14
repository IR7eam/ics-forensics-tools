import { Card, Col, Divider, List, Row, Space, Spin, Tag, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { fetchRoadmap } from '../api/client';

type Item = {
  title: string;
  detail: string;
  status: string;
  category: string;
};

type RoadmapSummary = {
  iterations_remaining: number;
  focus_areas: string[];
  delivered: Item[];
  in_progress: Item[];
  remaining: Item[];
  blockers: string[];
};

const statusColor: Record<string, string> = {
  done: 'green',
  in_progress: 'orange',
  planned: 'blue'
};

function ItemList({ title, items }: { title: string; items: Item[] }) {
  return (
    <Card title={title} size="small" style={{ marginBottom: 16 }}>
      <List
        dataSource={items}
        renderItem={(item) => (
          <List.Item>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Tag color={statusColor[item.status] || 'default'}>{item.status}</Tag>
                <Tag>{item.category}</Tag>
                <Typography.Text strong>{item.title}</Typography.Text>
              </Space>
              <Typography.Text type="secondary">{item.detail}</Typography.Text>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );
}

export function RoadmapPage() {
  const [data, setData] = useState<RoadmapSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchRoadmap()
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
        <Spin />
      </div>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card>
        <Typography.Title level={4}>Technical roadmap</Typography.Title>
        <Typography.Paragraph>
          Remaining iterations: <Tag color="geekblue">{data.iterations_remaining}</Tag>
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>Focus areas</strong>
          <List
            dataSource={data.focus_areas}
            renderItem={(item) => <List.Item>- {item}</List.Item>}
            size="small"
          />
        </Typography.Paragraph>
        <Typography.Paragraph>
          <strong>Blockers & cautions</strong>
          <List
            dataSource={data.blockers}
            renderItem={(item) => <List.Item>- {item}</List.Item>}
            size="small"
          />
        </Typography.Paragraph>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <ItemList title="Delivered" items={data.delivered} />
        </Col>
        <Col xs={24} md={12}>
          <ItemList title="In progress" items={data.in_progress} />
        </Col>
      </Row>
      <Divider />
      <ItemList title="Planned next" items={data.remaining} />
    </Space>
  );
}
