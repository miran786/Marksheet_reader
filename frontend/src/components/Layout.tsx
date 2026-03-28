import { Layout as AntLayout, Menu, theme, Typography, Button, Tooltip, Space, Tag } from 'antd';
import {
  DashboardOutlined,
  UploadOutlined,
  FileTextOutlined,
  TeamOutlined,
  LinkOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/upload', icon: <UploadOutlined />, label: 'Upload Marksheets' },
  { key: '/marksheets', icon: <FileTextOutlined />, label: 'Marksheets' },
  { key: '/students', icon: <TeamOutlined />, label: 'Students' },
  { key: '/mappings', icon: <LinkOutlined />, label: 'Subject Mappings' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();
  const { isDark, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        breakpoint="lg"
        collapsedWidth={80}
        style={{ background: token.colorBgContainer }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          overflow: 'hidden',
        }}>
          <Typography.Title level={4} style={{ margin: 0, color: token.colorPrimary, whiteSpace: 'nowrap' }}>
            MarkSheet Reader
          </Typography.Title>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <AntLayout>
        <Header style={{
          padding: '0 24px',
          background: token.colorBgContainer,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <Typography.Text strong style={{ fontSize: 16 }}>
            Automated Marksheet Reader
          </Typography.Text>
          <Space size="middle">
            <Space size="small">
              <UserOutlined />
              <Typography.Text>{user?.username}</Typography.Text>
              <Tag color={user?.role === 'admin' ? 'gold' : 'blue'}>
                {user?.role}
              </Tag>
            </Space>
            <Tooltip title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              <Button
                type="text"
                size="large"
                icon={isDark ? <SunOutlined /> : <MoonOutlined />}
                onClick={toggleTheme}
                style={{ fontSize: 18 }}
              />
            </Tooltip>
            <Tooltip title="Logout">
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={logout}
                danger
              >
                Logout
              </Button>
            </Tooltip>
          </Space>
        </Header>
        <Content style={{ margin: 24, minHeight: 280 }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}
