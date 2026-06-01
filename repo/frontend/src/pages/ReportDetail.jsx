import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Download as DownloadIcon } from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { reportsAPI } from '../services/api';

function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadReport();
  }, [id]);

  const loadReport = async () => {
    try {
      const res = await reportsAPI.get(id);
      setReport(res.data);
    } catch (error) {
      console.error('Error loading report:', error);
      setError('加载报告失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const res = await reportsAPI.download(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${id}.md`);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !report) {
    return <Alert severity="error">{error || '报告不存在'}</Alert>;
  }

  const priority = report.zoning_recommendations?.[0]?.priority || 'medium';

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

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Button
          component={Link}
          to="/reports"
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 2 }}
        >
          返回报告列表
        </Button>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4">报告 #{report.id}</Typography>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleDownload}
          >
            下载 Markdown
          </Button>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`优先级: ${getPriorityText(priority)}`}
            color={getPriorityColor(priority)}
          />
          <Chip
            label={report.sent_to_env_dept ? '已发送环保局' : '未发送环保局'}
            color={report.sent_to_env_dept ? 'success' : 'default'}
          />
          <Chip
            label={report.sent_to_planning ? '已发送规划委' : '未发送规划委'}
            color={report.sent_to_planning ? 'success' : 'default'}
          />
          <Chip label={`听证会ID: ${report.hearing_id}`} />
          <Chip label={`创建时间: ${new Date(report.created_at).toLocaleString()}`} />
        </Box>
      </Box>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                关键要点
              </Typography>
              <Typography variant="h5">{report.key_points?.length || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                区划调整建议
              </Typography>
              <Typography variant="h5">{report.zoning_recommendations?.length || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                平均噪声水平
              </Typography>
              <Typography variant="h5">
                {report.noise_level_analysis?.average_level?.toFixed(1) || 'N/A'} dB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          摘要
        </Typography>
        <Typography>{report.summary}</Typography>
      </Paper>

      {report.key_points && report.key_points.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            关键要点
          </Typography>
          {report.key_points.map((point, idx) => (
            <Typography key={idx} variant="body1" sx={{ mb: 1, ml: 2 }}>
              • {point}
            </Typography>
          ))}
        </Paper>
      )}

      {report.zoning_recommendations && report.zoning_recommendations.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            区划调整建议
          </Typography>
          <Grid container spacing={2}>
            {report.zoning_recommendations.map((rec, idx) => (
              <Grid item xs={12} md={6} key={idx}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="subtitle1">{rec.type}</Typography>
                      <Chip
                        label={rec.priority}
                        color={rec.priority === 'high' ? 'error' : rec.priority === 'medium' ? 'warning' : 'success'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      涉及区域: {rec.area}
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {rec.description}
                    </Typography>
                    <Typography variant="body2" color="primary">
                      预期效果: {rec.estimated_effect}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      <Divider sx={{ my: 3 }} />

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          完整报告 (Markdown)
        </Typography>
        <Box
          sx={{
            bgcolor: '#fafafa',
            p: 3,
            borderRadius: 1,
            overflow: 'auto',
            maxHeight: '600px',
          }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {report.full_markdown}
          </ReactMarkdown>
        </Box>
      </Paper>
    </Box>
  );
}

export default ReportDetail;
