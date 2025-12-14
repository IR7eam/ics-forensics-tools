import { useEffect, useState } from 'react';
import { Card, Table, Tag, message, Button, Space } from 'antd';
import { apiClient } from '../api/client';

interface EvidenceLink {
  id: number;
  from_ref: string;
  to_ref: string;
  relation: string;
  created_at?: string;
}

interface RawEvidence {
  id: number;
  observation_id?: number;
  hash: string;
  storage_path: string;
  context: Record<string, any>;
  created_at?: string;
}

export function EvidenceChainPage() {
  const [links, setLinks] = useState<EvidenceLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [evidence, setEvidence] = useState<RawEvidence[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get<EvidenceLink[]>('/evidence-links')
      .then((res) => setLinks(res.data))
      .catch(() => message.error('Failed to fetch evidence links'))
      .finally(() => setLoading(false));

    setEvidenceLoading(true);
    apiClient
      .get<RawEvidence[]>('/evidence')
      .then((res) => setEvidence(res.data))
      .catch(() => message.error('Failed to fetch evidence records'))
      .finally(() => setEvidenceLoading(false));
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

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="Evidence Chain">
        <Table
          rowKey={(row) => String(row.id)}
          loading={loading}
          dataSource={links}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 80 },
            { title: 'From', dataIndex: 'from_ref' },
            { title: 'To', dataIndex: 'to_ref' },
            {
              title: 'Relation',
              dataIndex: 'relation',
              render: (value: string) => <Tag color="purple">{value}</Tag>
            },
            { title: 'Created At', dataIndex: 'created_at' }
          ]}
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
