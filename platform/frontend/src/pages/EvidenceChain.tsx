import { useEffect, useState } from 'react';
import {
  Card,
  Table,
  Tag,
  message,
  Button,
  Space,
  Timeline,
  Row,
  Col,
  Statistic,
  Form,
  InputNumber,
  Select
} from 'antd';
import { ClockCircleOutlined, LinkOutlined, WarningOutlined } from '@ant-design/icons';
import { apiClient } from '../api/client';

interface EvidenceChainEntry {
  ref: string;
  type: string;
  timestamp: string;
  description: string;
  attack_stage?: string | null;
  risk_score?: number | null;
  relation?: string | null;
  protocol?: string | null;
  asset_id?: number | null;
}

interface EvidenceChainSummary {
  stage_counts: Record<string, number>;
  max_risk: number;
  total_entries: number;
}

interface EvidenceChainResponse {
  entries: EvidenceChainEntry[];
  summary: EvidenceChainSummary;
}

interface RawEvidence {
  id: number;
  observation_id?: number;
  hash: string;
  storage_path: string;
  context: Record<string, any>;
  created_at?: string;
}

const attackStages = [
  'reconnaissance',
  'intrusion',
  'lateral_movement',
  'control',
  'impact',
  'recovery'
];

export function EvidenceChainPage() {
  const [chain, setChain] = useState<EvidenceChainEntry[]>([]);
  const [summary, setSummary] = useState<EvidenceChainSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [evidence, setEvidence] = useState<RawEvidence[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [assetIdFilter, setAssetIdFilter] = useState<number | undefined>();
  const [stageFilter, setStageFilter] = useState<string | undefined>();

  const fetchChain = async (params?: { asset_id?: number; attack_stage?: string }) => {
    setLoading(true);
    try {
      const res = await apiClient.get<EvidenceChainResponse>('/analysis/evidence-chain', { params });
      setChain(res.data.entries);
      setSummary(res.data.summary);
    } catch (err) {
      console.error(err);
      message.error('Failed to fetch evidence chain');
    } finally {
      setLoading(false);
    }
  };

  const fetchEvidence = () => {
    setEvidenceLoading(true);
    apiClient
      .get<RawEvidence[]>('/evidence')
      .then((res) => setEvidence(res.data))
      .catch(() => message.error('Failed to fetch evidence records'))
      .finally(() => setEvidenceLoading(false));
  };

  useEffect(() => {
    fetchChain();
    fetchEvidence();
  }, []);

  const downloadEvidence = async (id: number) => {
    try {
      const response = await apiClient.get(`/evidence/${id}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `evidence-${id}.bin`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      message.error('Failed to download evidence');
    }
  };

  const renderTimelineIcon = (type: string) => {
    if (type === 'security_event') return <WarningOutlined />;
    if (type === 'link') return <LinkOutlined />;
    return <ClockCircleOutlined />;
  };

  const renderTimelineColor = (type: string) => {
    if (type === 'security_event') return 'red';
    if (type === 'raw_evidence') return 'blue';
    if (type === 'observation') return 'green';
    return 'gray';
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card
        title="Evidence Chain"
        extra={
          <Space>
            <Form
              layout="inline"
              onFinish={() => fetchChain({ asset_id: assetIdFilter, attack_stage: stageFilter })}
            >
              <Form.Item label="Asset ID">
                <InputNumber
                  min={1}
                  value={assetIdFilter}
                  placeholder="Any"
                  onChange={(value) => setAssetIdFilter(value ?? undefined)}
                />
              </Form.Item>
              <Form.Item label="Stage">
                <Select
                  allowClear
                  style={{ width: 180 }}
                  placeholder="Any"
                  value={stageFilter}
                  onChange={(value) => setStageFilter(value)}
                  options={attackStages.map((stage) => ({ label: stage, value: stage }))}
                />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                Apply
              </Button>
              <Button
                onClick={() => {
                  setAssetIdFilter(undefined);
                  setStageFilter(undefined);
                  fetchChain({});
                }}
                disabled={loading}
              >
                Reset
              </Button>
            </Form>
          </Space>
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic title="Entries" value={summary?.total_entries ?? 0} />
          </Col>
          <Col span={6}>
            <Statistic title="Max Risk" value={summary?.max_risk ?? 0} precision={3} />
          </Col>
          <Col span={12}>
            <Space wrap>
              {summary &&
                Object.entries(summary.stage_counts).map(([stage, count]) => (
                  <Tag key={stage} color="purple">
                    {stage}: {count}
                  </Tag>
                ))}
            </Space>
          </Col>
        </Row>

        <Timeline
          pending={loading ? 'Loading...' : undefined}
          items={chain.map((entry) => ({
            color: renderTimelineColor(entry.type),
            dot: renderTimelineIcon(entry.type),
            children: (
              <div>
                <div style={{ fontWeight: 600 }}>{entry.description}</div>
                <Space wrap size="small">
                  <Tag>{entry.type}</Tag>
                  {entry.protocol && <Tag color="blue">{entry.protocol}</Tag>}
                  {entry.attack_stage && <Tag color="volcano">{entry.attack_stage}</Tag>}
                  {entry.risk_score != null && <Tag color="magenta">risk {entry.risk_score.toFixed(3)}</Tag>}
                  <Tag>{new Date(entry.timestamp).toLocaleString()}</Tag>
                </Space>
              </div>
            )
          }))}
        />
      </Card>

      <Card title="Raw Evidence">
        <Table
          rowKey={(row) => String(row.id)}
          loading={evidenceLoading}
          dataSource={evidence}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: 'Observation', dataIndex: 'observation_id', width: 120 },
            { title: 'Hash', dataIndex: 'hash' },
            { title: 'Path', dataIndex: 'storage_path' },
            { title: 'Created', dataIndex: 'created_at', width: 180 },
            {
              title: 'Actions',
              dataIndex: 'id',
              width: 140,
              render: (_: any, record: RawEvidence) => (
                <Button onClick={() => downloadEvidence(record.id)}>Download</Button>
              )
            }
          ]}
        />
      </Card>
    </Space>
  );
}
