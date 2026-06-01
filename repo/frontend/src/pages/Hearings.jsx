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
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  LinearProgress,
} from '@mui/material';
import { Add as AddIcon, PlayArrow as PlayIcon, Visibility as VisibilityIcon } from '@mui/icons-material';
import { hearingsAPI, recordingsAPI } from '../services/api';

function Hearings() {
  const [hearings, setHearings] = useState([]);
  const [recordings, setRecordings] = useState([]);
  const [openCreate, setOpenCreate] = useState(false);
  const [newHearing, setNewHearing] = useState({
    title: '',
    description: '',
    district: '',
    scheduled_at: new Date().toISOString().slice(0, 16),
  });
  const [selectedHearing, setSelectedHearing] = useState(null);
  const [openAddRecording, setOpenAddRecording] = useState(false);
  const [selectedRecordingId, setSelectedRecordingId] = useState('');
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [hearingsRes, recordingsRes] = await Promise.all([
        hearingsAPI.list(),
        recordingsAPI.list(),
      ]);
      setHearings(hearingsRes.data);
      setRecordings(recordingsRes.data.filter((r) => !r.hearing_id));
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateHearing = async () => {
    try {
      await hearingsAPI.create({
        ...newHearing,
        scheduled_at: new Date(newHearing.scheduled_at).toISOString(),
      });
      setOpenCreate(false);
      setNewHearing({
        title: '',
        description: '',
        district: '',
        scheduled_at: new Date().toISOString().slice(0, 16),
      });
      loadData();
    } catch (error) {
      console.error('Error creating hearing:', error);
    }
  };

  const handleProcessHearing = async (hearingId) => {
    setProcessingId(hearingId);
    try {
      await hearingsAPI.process(hearingId);
      setProcessingId(null);
      loadData();
    } catch (error) {
      console.error('Error processing hearing:', error);
      setProcessingId(null);
    }
  };

  const handleAddRecording = async () => {
    if (!selectedHearing || !selectedRecordingId) return;

    try {
      await hearingsAPI.addRecording(selectedHearing.id, selectedRecordingId);
      setOpenAddRecording(false);
      setSelectedRecordingId('');
      loadData();
    } catch (error) {
      console.error('Error adding recording:', error);
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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">听证会管理</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenCreate(true)}
        >
          创建听证会
        </Button>
      </Box>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>标题</TableCell>
              <TableCell>区域</TableCell>
              <TableCell>时间</TableCell>
              <TableCell>录音数量</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hearings.map((hearing) => (
              <TableRow key={hearing.id}>
                <TableCell>{hearing.id}</TableCell>
                <TableCell>{hearing.title}</TableCell>
                <TableCell>{hearing.district || '-'}</TableCell>
                <TableCell>{new Date(hearing.scheduled_at).toLocaleString()}</TableCell>
                <TableCell>{hearing.recordings?.length || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={getStatusText(hearing.status)}
                    color={getStatusColor(hearing.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    component={Link}
                    to={`/hearings/${hearing.id}`}
                    size="small"
                    title="查看详情"
                  >
                    <VisibilityIcon />
                  </IconButton>
                  {(hearing.status === 'pending' || hearing.status === 'failed') &&
                    (hearing.recordings?.length || 0) > 0 && (
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleProcessHearing(hearing.id)}
                        disabled={processingId === hearing.id}
                        title="开始处理"
                      >
                        {processingId === hearing.id ? (
                          <LinearProgress size={20} />
                        ) : (
                          <PlayIcon />
                        )}
                      </IconButton>
                    )}
                  {hearing.status === 'pending' && (
                    <IconButton
                      size="small"
                      color="success"
                      onClick={() => {
                        setSelectedHearing(hearing);
                        setOpenAddRecording(true);
                      }}
                      title="添加录音"
                    >
                      <AddIcon />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="sm" fullWidth>
        <DialogTitle>创建新听证会</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="标题"
              value={newHearing.title}
              onChange={(e) => setNewHearing({ ...newHearing, title: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="描述"
              value={newHearing.description}
              onChange={(e) => setNewHearing({ ...newHearing, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              label="区域"
              value={newHearing.district}
              onChange={(e) => setNewHearing({ ...newHearing, district: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="时间"
              type="datetime-local"
              value={newHearing.scheduled_at}
              onChange={(e) => setNewHearing({ ...newHearing, scheduled_at: e.target.value })}
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreate(false)}>取消</Button>
          <Button onClick={handleCreateHearing} variant="contained" color="primary">
            创建
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openAddRecording} onClose={() => setOpenAddRecording(false)} maxWidth="sm" fullWidth>
        <DialogTitle>添加录音到听证会</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>选择录音</InputLabel>
            <Select
              value={selectedRecordingId}
              onChange={(e) => setSelectedRecordingId(e.target.value)}
              label="选择录音"
            >
              {recordings.map((rec) => (
                <MenuItem key={rec.id} value={rec.id}>
                  {rec.filename} - {rec.microphone_id}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddRecording(false)}>取消</Button>
          <Button onClick={handleAddRecording} variant="contained" color="primary">
            添加
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Hearings;
