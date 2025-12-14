import { Layout, Menu, Typography } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  DatabaseOutlined,
  RadarChartOutlined,
  FileSearchOutlined,
  BranchesOutlined,
  FileTextOutlined,
  SettingOutlined,
  AuditOutlined,
  ProjectOutlined
} from '@ant-design/icons';
import type { ReactNode } from 'react';

const { Header, Content, Sider } = Layout;

interface Props {
  children: ReactNode;
}

export function AppLayout({ children }: Props) {
  const location = useLocation();
  const selectedKey = location.pathname === '/' ? '/dashboard' : location.pathname;
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 48, margin: 16, color: 'white', fontWeight: 600 }}>ICS Forensics</div>
        <Menu theme="dark" mode="inline" selectedKeys={[selectedKey]}>
          <Menu.Item key="/dashboard" icon={<DashboardOutlined />}>
            <Link to="/dashboard">Dashboard</Link>
          </Menu.Item>
          <Menu.Item key="/assets" icon={<DatabaseOutlined />}>
            <Link to="/assets">Assets</Link>
          </Menu.Item>
          <Menu.Item key="/scan-jobs" icon={<RadarChartOutlined />}>
            <Link to="/scan-jobs">Scan Jobs</Link>
          </Menu.Item>
          <Menu.Item key="/events" icon={<FileSearchOutlined />}>
            <Link to="/events">Events</Link>
          </Menu.Item>
          <Menu.Item key="/audit" icon={<AuditOutlined />}>
            <Link to="/audit">Audit</Link>
          </Menu.Item>
          <Menu.Item key="/evidence" icon={<BranchesOutlined />}>
            <Link to="/evidence">Evidence Chain</Link>
          </Menu.Item>
          <Menu.Item key="/reports" icon={<FileTextOutlined />}>
            <Link to="/reports">Reports</Link>
          </Menu.Item>
          <Menu.Item key="/roadmap" icon={<ProjectOutlined />}>
            <Link to="/roadmap">Roadmap</Link>
          </Menu.Item>
          <Menu.Item key="/settings" icon={<SettingOutlined />}>
            <Link to="/settings">Settings</Link>
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 16px' }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            ICS Forensics Platform
          </Typography.Title>
        </Header>
        <Content style={{ margin: '16px' }}>{children}</Content>
      </Layout>
    </Layout>
  );
}
