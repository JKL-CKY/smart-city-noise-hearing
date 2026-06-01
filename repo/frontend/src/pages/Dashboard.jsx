import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { hearingsAPI, noiseMapAPI, reportsAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

function Dashboard() {
  const [stats, setStats] = useState({
    totalHearings: 0,
    completedHearings: 0,
    pendingHearings: 0,
    totalReports: 0,
    totalDevices: 0,
    pendingReports: 0,
  });
  const [districtStats, setDistrictStats] = useState([]);
  const [recentHearings, setRecentHearings] = useState([]);
  const [recentReports, setRecentReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [hearingsRes, reportsRes, devicesRes, districtRes] = await Promise.all([
        hearingsAPI.list({ limit: 5 }),
        reportsAPI.list({ limit: 5 }),
        noiseMapAPI.getDevices(),
        noiseMapAPI.getDistrictStats(),
      ]);

      const allHearings = await hearingsAPI.list();
      const allReports = await reportsAPI.list();
      const pendingReports = await noiseMapAPI.getReportPoints({ status: 'pending' });

      setStats({
        totalHearings: allHearings.data.length,
        completedHearings: allHearings.data.filter((h) => h.status === 'completed').length,
        pendingHearings: allHearings.data.filter((h) => h.status === 'pending').length,
        totalReports: allReports.data.length,
        totalDevices: devicesRes.data.length,
        pendingReports: pendingReports.data.length,
      });

      const districtData = Object.entries(districtRes.data.district_stats || {}).map(
        ([name, data]) => ({
          name,
          avg_noise: data.avg_noise_level,
          max_noise: data.max_noise_level,
          recordings: data.recordings_count,
          reports: data.report_points,
        })
      );
      setDistrictStats(districtData);

      setRecentHearings(hearingsRes.data);
      setRecentReports(reportsRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'processing':
        return '处理中';
      case 'failed':
        return '失败';
      default:
        return '待处理';
    }
  };

  if (loading) {
    return <LinearProgress />;
  }

  const completionRate = stats.totalHearings > 0
    ? Math.round((stats.completedHearings / stats.totalHearings) * 100)
    : 0;

  const pieData = [
    { name: '已完成', value: stats.completedHearings },
    { name: '处理中', value: stats.totalHearings - stats.completedHearings - stats.pendingHearings },
    { name: '待处理', value: stats.pendingHearings },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        数据概览
      </Typography>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                听证会总数
              </Typography>
              <Typography variant="h3">{stats.totalHearings}</Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  完成率: {completionRate}%
                </Typography>
                <LinearProgress variant="determinate" value={completionRate} sx={{ mt: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                生成报告
              </Typography>
              <Typography variant="h3">{stats.totalReports}</Typography>
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Chip
                  label={`已发送环保局: ${recentReports.filter(r => r.sent_to_env_dept).length}`}
                  color="success"
                  size="small"
                />
                <Chip
                  label={`已发送规划委: ${recentReports.filter(r => r.sent_to_planning).length}`}
                  color="primary"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                麦克风设备
              </Typography>
              <Typography variant="h3">{stats.totalDevices}</Typography>
              <Box sx={{ mt: 2 }}>
                <Chip
                  label={`待处理举报: ${stats.pendingReports}`}
                  color="error"
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              各区域噪声水平
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={districtStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'dB', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="avg_noise" name="平均噪声" fill="#1976d2" />
                <Bar dataKey="max_noise" name="最大噪声" fill="#dc004e" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              听证会状态分布
            </Typography>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              最近听证会
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>标题</TableCell>
                  <TableCell>区域</TableCell>
                  <TableCell>状态</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentHearings.map((hearing) => (
                  <TableRow key={hearing.id}>
                    <TableCell>{hearing.title}</TableCell>
                    <TableCell>{hearing.district || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={getStatusText(hearing.status)}
                        color={getStatusColor(hearing.status)}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              最近报告
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>听证会ID</TableCell>
                  <TableCell>优先级</TableCell>
                  <TableCell>发送状态</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recentReports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>#{report.hearing_id}</TableCell>
                    <TableCell>
                      {report.zoning_recommendations?.[0]?.priority || 'medium'}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {report.sent_to_env_dept && (
                          <Chip label="环保局" color="success" size="small" />
                        )}
                        {report.sent_to_planning && (
                          <Chip label="规划委" color="primary" size="small" />
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
