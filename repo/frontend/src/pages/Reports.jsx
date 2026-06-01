import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  IconButton,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { reportsAPI } from '../services/api';

function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSent, setFilterSent] = useState('');

  useEffect(() => {
    loadReports();
  }, [filterSent]);

  const loadReports = async () => {
    try {
      const params = {};
      if (filterSent === 'sent_env') {
        params.sent_to_env_dept = true;
      } else if (filterSent === 'not_sent_env') {
        params.sent_to_env_dept = false;
      } else if (filterSent === 'sent_planning') {
        params.sent_to_planning = true;
      } else if (filterSent === 'not_sent_planning') {
        params.sent_to_planning = false;
      }

      const res = await reportsAPI.list(params);
      setReports(res.data);
    } catch (error) {
      console.error('Error loading reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (reportId) => {
    try {
      const res = await reportsAPI.download(reportId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportId}.md`);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const handleSendEmail = async (reportId, target) => {
    try {
      await reportsAPI.sendEmail(reportId, target);
      loadReports();
    } catch (error) {
      console.error('Error sending email:', error);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      default:
        return 'success';
    }
  };

  const getPriorityText = (priority) => {
    switch (priority) {
      case 'critical':
        return '紧急';
      case 'high':
        return '高';
      case 'medium':
        return '中';
      default:
        return '低';
    }
  };

  if (loading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, alignItems: 'center' }}>
        <Typography variant="h4">报告管理</Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>筛选</InputLabel>
          <Select
            value={filterSent}
            onChange={(e) => setFilterSent(e.target.value)}
            label="筛选"
          >
            <MenuItem value="">全部</MenuItem>
            <MenuItem value="sent_env">已发送环保局</MenuItem>
            <MenuItem value="not_sent_env">未发送环保局</MenuItem>
            <MenuItem value="sent_planning">已发送规划委</MenuItem>
            <MenuItem value="not_sent_planning">未发送规划委</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>听证会ID</TableCell>
              <TableCell>优先级</TableCell>
              <TableCell>环保局</TableCell>
              <TableCell>规划委</TableCell>
              <TableCell>创建时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reports.map((report) => {
              const priority = report.zoning_recommendations?.[0]?.priority || 'medium';
              return (
                <TableRow key={report.id}>
                  <TableCell>{report.id}</TableCell>
                  <TableCell>#{report.hearing_id}</TableCell>
                  <TableCell>
                    <Chip
                      label={getPriorityText(priority)}
                      color={getPriorityColor(priority)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {report.sent_to_env_dept ? (
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="已发送"
                        color="success"
                        size="small"
                      />
                    ) : (
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleSendEmail(report.id, 'env_dept')}
                        title="发送到环保局"
                      >
                        <EmailIcon />
                      </IconButton>
                    )}
                  </TableCell>
                  <TableCell>
                    {report.sent_to_planning ? (
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="已发送"
                        color="success"
                        size="small"
                      />
                    ) : (
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleSendEmail(report.id, 'planning')}
                        title="发送到规划委"
                      >
                        <EmailIcon />
                      </IconButton>
                    )}
                  </TableCell>
                  <TableCell>{new Date(report.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <IconButton
                      component={Link}
                      to={`/reports/${report.id}`}
                      size="small"
                      title="查看详情"
                    >
                      <VisibilityIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDownload(report.id)}
                      title="下载Markdown"
                    >
                      <DownloadIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}

export default Reports;
