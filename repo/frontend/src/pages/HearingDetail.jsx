import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { hearingsAPI } from '../services/api';

function HearingDetail() {
  const { id } = useParams();
  const [hearing, setHearing] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHearingData();
  }, [id]);

  const loadHearingData = async () => {
    try {
      const hearingRes = await hearingsAPI.get(id);
      setHearing(hearingRes.data);

      try {
        const reportRes = await hearingsAPI.getReport(id);
        setReport(reportRes.data);
      } catch (e) {
        if (e.response?.status !== 404) {
          console.error('Error loading report:', e);
        }
      }
    } catch (error) {
      console.error('Error loading hearing:', error);
      setError('加载听证会数据失败');
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

  const getSpeakerRoleText = (role) => {
    switch (role) {
      case 'complainant':
        return '投诉者';
      case 'official':
        return '官员';
      default:
        return '未知';
    }
  };

  const getSpeakerRoleColor = (role) => {
    switch (role) {
      case 'complainant':
        return 'error';
      case 'official':
        return 'primary';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !hearing) {
    return <Alert severity="error">{error || '听证会不存在'}</Alert>;
  }

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Button
          component={Link}
          to="/hearings"
          startIcon={<ArrowBackIcon />}
          sx={{ mb: 2 }}
        >
          返回听证会列表
        </Button>
        <Typography variant="h4" gutterBottom>
          {hearing.title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={getStatusText(hearing.status)}
            color={getStatusColor(hearing.status)}
          />
          {hearing.district && <Chip label={`区域: ${hearing.district}`} />}
          <Chip label={`时间: ${new Date(hearing.scheduled_at).toLocaleString()}`} />
        </Box>
      </Box>

      {hearing.description && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            描述
          </Typography>
          <Typography>{hearing.description}</Typography>
        </Paper>
      )}

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              录音列表 ({hearing.recordings?.length || 0})
            </Typography>
            <List>
              {hearing.recordings?.map((rec) => (
                <ListItem key={rec.id} divider>
                  <ListItemText
                    primary={rec.filename}
                    secondary={
                      <>
                        麦克风: {rec.microphone_id}
                        {rec.location_name && ` | 位置: ${rec.location_name}`}
                        {rec.noise_level && ` | 噪声: ${rec.noise_level.toFixed(1)} dB`}
                      </>
                    }
                  />
                  <Chip label={rec.status} size="small" />
                </ListItem>
              ))}
              {(!hearing.recordings || hearing.recordings.length === 0) && (
                <ListItem>
                  <ListItemText primary="暂无录音" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          {hearing.status !== 'completed' && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                处理状态
              </Typography>
              {hearing.status === 'pending' && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  听证会待处理，请确保已添加录音后点击处理按钮
                </Alert>
              )}
              {hearing.status === 'processing' && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  听证会正在处理中，请稍候...
                </Alert>
              )}
              {hearing.status === 'failed' && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  处理失败，请重试
                </Alert>
              )}
            </Paper>
          )}

          {report && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  报告摘要
                </Typography>
                <Typography variant="body2" paragraph>
                  {report.summary}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  关键要点
                </Typography>
                {report.key_points?.map((point, idx) => (
                  <Typography key={idx} variant="body2" sx={{ ml: 2 }}>
                    • {point}
                  </Typography>
                ))}
                <Box sx={{ mt: 2 }}>
                  <Button
                    component={Link}
                    to={`/reports/${report.id}`}
                    variant="contained"
                    size="small"
                  >
                    查看完整报告
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {report && report.noise_level_analysis && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            噪声分析
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" variant="body2">
                    平均噪声
                  </Typography>
                  <Typography variant="h5">
                    {report.noise_level_analysis.average_level?.toFixed(1)} dB
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" variant="body2">
                    最大噪声
                  </Typography>
                  <Typography variant="h5">
                    {report.noise_level_analysis.max_level?.toFixed(1)} dB
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" variant="body2">
                    是否超标
                  </Typography>
                  <Typography variant="h5" color={report.noise_level_analysis.exceeds_standard ? 'error' : 'success'}>
                    {report.noise_level_analysis.exceeds_standard ? '是' : '否'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {report && report.zoning_recommendations && report.zoning_recommendations.length > 0 && (
        <Paper sx={{ p: 3 }}>
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
    </Box>
  );
}

export default HearingDetail;
