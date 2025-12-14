import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Modal, Select, Table, Tag, message } from 'antd';
import { apiClient } from '../api/client';

interface Report {
  id: number;
  title?: string;
  format: string;
  file_path?: string;
  scope?: Record<string, any>;
  parameters?: Record<string, any>;
}

export function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchReports = () => {
    setLoading(true);
    apiClient
      .get<Report[]>('/reports')
      .then((res) => setReports(res.data))
      .catch(() => message.error('Failed to fetch reports'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async (values: any) => {
    try {
      const payload = {
        title: values.title || 'ICS Forensics Report',
        format: values.format,
        scope: values.scope ? JSON.parse(values.scope) : {},
        parameters: values.parameters ? JSON.parse(values.parameters) : {}
      };
      await apiClient.post('/reports/generate', payload);
      message.success('Report generation triggered');
      setModalOpen(false);
      fetchReports();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || 'Failed to generate report');
    }
  };

  return (
    <Card title="Reports" extra={<Button onClick={() => setModalOpen(true)}>Generate</Button>}>
      <Table
        rowKey={(row) => String(row.id)}
        loading={loading}
        dataSource={reports}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 80 },
          { title: 'Title', dataIndex: 'title' },
          {
            title: 'Format',
            dataIndex: 'format',
            render: (fmt: string) => <Tag color="geekblue">{fmt}</Tag>
          },
          { title: 'File Path', dataIndex: 'file_path' }
        ]}
      />

      <Modal open={modalOpen} title="Generate Report" onCancel={() => setModalOpen(false)} footer={null} destroyOnClose>
        <Form layout="vertical" onFinish={handleGenerate}>
          <Form.Item name="title" label="Title">
            <Input placeholder="ICS Forensics Report" />
          </Form.Item>
          <Form.Item name="format" label="Format" rules={[{ required: true, message: 'Select format' }]}>
            <Select
              options={[
                { value: 'html', label: 'HTML' },
                { value: 'pdf', label: 'PDF' },
                { value: 'docx', label: 'DOCX' }
              ]}
              placeholder="Choose output"
            />
          </Form.Item>
          <Form.Item name="scope" label="Scope JSON">
            <Input.TextArea placeholder='{"assets": [1, 2]}' rows={3} />
          </Form.Item>
          <Form.Item name="parameters" label="Parameters JSON">
            <Input.TextArea placeholder='{"notes": "demo"}' rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              Generate
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
