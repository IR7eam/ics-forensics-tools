import { useEffect, useState } from 'react';
import { Card, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface EvidenceLink {
  id: number;
  from_ref: string;
  to_ref: string;
  relation: string;
  created_at?: string;
}

export function EvidenceChainPage() {
  const [links, setLinks] = useState<EvidenceLink[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get<EvidenceLink[]>('/evidence-links')
      .then((res) => setLinks(res.data))
      .catch(() => message.error('Failed to fetch evidence links'))
      .finally(() => setLoading(false));
  }, []);

  return (
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
  );
}
