import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Modal, Space, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface Asset {
  id?: number;
  hostname?: string;
  ip?: string;
  device_type?: string | null;
  vendor?: string | null;
  model?: string | null;
  protocols?: string[] | null;
}

export function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchAssets = () => {
    setLoading(true);
    apiClient
      .get<Asset[]>('/assets')
      .then((res) => setAssets(res.data))
      .catch(() => message.error('Failed to fetch assets'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleCreate = async (values: Asset & { protocols?: string }) => {
    try {
      const payload: Asset = {
        ...values,
        protocols: values.protocols
          ? values.protocols
              .toString()
              .split(',')
              .map((p) => p.trim())
              .filter(Boolean)
          : []
      };
      await apiClient.post('/assets', payload);
      message.success('Asset created');
      setModalOpen(false);
      fetchAssets();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Create asset failed');
    }
  };

  return (
    <Card title="Assets" extra={<Button onClick={() => setModalOpen(true)}>New Asset</Button>}>
      <Table
        rowKey={(row) => String(row.id)}
        loading={loading}
        dataSource={assets}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'Hostname', dataIndex: 'hostname' },
          { title: 'IP Address', dataIndex: 'ip' },
          { title: 'Device Type', dataIndex: 'device_type' },
          { title: 'Vendor', dataIndex: 'vendor' },
          { title: 'Model', dataIndex: 'model' },
          {
            title: 'Protocols',
            dataIndex: 'protocols',
            render: (protocols?: string[]) => (
              <Space wrap>
                {protocols?.map((p) => (
                  <Tag key={p}>{p}</Tag>
                )) || <Tag color="default">n/a</Tag>}
              </Space>
            )
          }
        ]}
      />

      <Modal open={modalOpen} title="Create Asset" onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form layout="vertical" onFinish={handleCreate}>
          <Form.Item name="hostname" label="Hostname">
            <Input />
          </Form.Item>
          <Form.Item name="ip" label="IP Address" rules={[{ required: true, message: 'IP is required' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="device_type" label="Device Type">
            <Input placeholder="e.g., plc, gateway, server" />
          </Form.Item>
          <Form.Item name="vendor" label="Vendor">
            <Input />
          </Form.Item>
          <Form.Item name="model" label="Model">
            <Input />
          </Form.Item>
          <Form.Item name="protocols" label="Protocols (comma separated)">
            <Input placeholder="modbus, s7, opcua" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Save
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
