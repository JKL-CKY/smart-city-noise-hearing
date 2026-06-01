import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet';
import {
  Box,
  Typography,
  Paper,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import L from 'leaflet';
import { noiseMapAPI } from '../services/api';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const reportIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const getNoiseColor = (level) => {
  if (level < 40) return '#4CAF50';
  if (level < 55) return '#8BC34A';
  if (level < 70) return '#FFEB3B';
  if (level < 85) return '#FF9800';
  return '#F44336';
};

function NoiseMap() {
  const [heatmapData, setHeatmapData] = useState([]);
  const [reportPoints, setReportPoints] = useState([]);
  const [devices, setDevices] = useState([]);
  const [timeRange, setTimeRange] = useState(7);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [districts, setDistricts] = useState([]);
  const [newReportOpen, setNewReportOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [newReport, setNewReport] = useState({
    title: '',
    description: '',
    noise_level: '',
    reporter_name: '',
    reporter_contact: '',
  });

  useEffect(() => {
    loadData();
  }, [timeRange, selectedDistrict]);

  const loadData = async () => {
    try {
      const endTime = new Date();
      const startTime = new Date();
      startTime.setDate(startTime.getDate() - timeRange);

      const [heatmapRes, reportsRes, devicesRes] = await Promise.all([
        noiseMapAPI.getHeatmap({
          start_time: startTime.toISOString(),
          end_time: endTime.toISOString(),
        }),
        noiseMapAPI.getReportPoints({ status: 'pending' }),
        noiseMapAPI.getDevices(),
      ]);

      setHeatmapData(heatmapRes.data.heatmap_data || []);
      setReportPoints(reportsRes.data || []);
      setDevices(devicesRes.data || []);

      const uniqueDistricts = [...new Set(devicesRes.data.map((d) => d.district).filter(Boolean))];
      setDistricts(uniqueDistricts);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleMapClick = (e) => {
    setSelectedLocation({
      latitude: e.latlng.lat,
      longitude: e.latlng.lng,
    });
    setNewReportOpen(true);
  };

  const handleSubmitReport = async () => {
    if (!selectedLocation) return;

    try {
      await noiseMapAPI.createReportPoint({
        ...newReport,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
        noise_level: parseFloat(newReport.noise_level) || null,
      });
      setNewReportOpen(false);
      setNewReport({
        title: '',
        description: '',
        noise_level: '',
        reporter_name: '',
        reporter_contact: '',
      });
      setSelectedLocation(null);
      loadData();
    } catch (error) {
      console.error('Error submitting report:', error);
    }
  };

  const center = [39.9042, 116.4074];

  const filteredHeatmap = selectedDistrict
    ? heatmapData.filter((d) => {
        const device = devices.find((dev) => dev.microphone_id === d.microphone_id);
        return device && device.district === selectedDistrict;
      })
    : heatmapData;

  const avgNoise = filteredHeatmap.length
    ? filteredHeatmap.reduce((sum, d) => sum + d.noise_level, 0) / filteredHeatmap.length
    : 0;

  const maxNoise = filteredHeatmap.length
    ? Math.max(...filteredHeatmap.map((d) => d.noise_level))
    : 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        噪声地图
      </Typography>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                平均噪声水平
              </Typography>
              <Typography variant="h4" color={getNoiseColor(avgNoise)}>
                {avgNoise.toFixed(1)} dB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                最大噪声水平
              </Typography>
              <Typography variant="h4" color={getNoiseColor(maxNoise)}>
                {maxNoise.toFixed(1)} dB
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                监测点数量
              </Typography>
              <Typography variant="h4">{devices.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" variant="body2">
                待处理举报
              </Typography>
              <Typography variant="h4" color="error">
                {reportPoints.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <Typography gutterBottom>时间范围 (天)</Typography>
            <Slider
              value={timeRange}
              onChange={(e, val) => setTimeRange(val)}
              min={1}
              max={30}
              marks={[
                { value: 1, label: '1天' },
                { value: 7, label: '7天' },
                { value: 14, label: '14天' },
                { value: 30, label: '30天' },
              ]}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>区域</InputLabel>
              <Select
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                label="区域"
              >
                <MenuItem value="">全部区域</MenuItem>
                {districts.map((d) => (
                  <MenuItem key={d} value={d}>
                    {d}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={12} md={4}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip label="< 40dB" sx={{ backgroundColor: '#4CAF50', color: 'white' }} />
              <Chip label="40-55dB" sx={{ backgroundColor: '#8BC34A', color: 'white' }} />
              <Chip label="55-70dB" sx={{ backgroundColor: '#FFEB3B' }} />
              <Chip label="70-85dB" sx={{ backgroundColor: '#FF9800', color: 'white' }} />
              <Chip label="> 85dB" sx={{ backgroundColor: '#F44336', color: 'white' }} />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ height: '600px', position: 'relative' }}>
        <MapContainer
          center={center}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
          onClick={handleMapClick}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />

          {filteredHeatmap.map((point, index) => (
            <CircleMarker
              key={`heatmap-${index}`}
              center={[point.latitude, point.longitude]}
              radius={15}
              fillColor={getNoiseColor(point.noise_level)}
              color={getNoiseColor(point.noise_level)}
              weight={1}
              opacity={0.8}
              fillOpacity={0.6}
            >
              <Popup>
                <Box>
                  <Typography variant="subtitle2">{point.location_name || '监测点'}</Typography>
                  <Typography variant="body2">噪声水平: {point.noise_level.toFixed(1)} dB</Typography>
                  <Typography variant="body2">时间: {new Date(point.recorded_at).toLocaleString()}</Typography>
                </Box>
              </Popup>
            </CircleMarker>
          ))}

          {reportPoints.map((point) => (
            <Marker
              key={`report-${point.id}`}
              position={[point.latitude, point.longitude]}
              icon={reportIcon}
            >
              <Popup className="report-point-popup">
                <Typography variant="subtitle2" color="error">
                  {point.title}
                </Typography>
                {point.description && (
                  <Typography variant="body2">{point.description}</Typography>
                )}
                {point.noise_level && (
                  <Typography variant="body2">噪声: {point.noise_level} dB</Typography>
                )}
                {point.reporter_name && (
                  <Typography variant="body2">举报人: {point.reporter_name}</Typography>
                )}
                <Typography variant="caption" color="textSecondary">
                  {new Date(point.created_at).toLocaleString()}
                </Typography>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </Paper>

      <Dialog open={newReportOpen} onClose={() => setNewReportOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>提交噪声举报</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            {selectedLocation && (
              <Typography variant="body2" gutterBottom>
                位置: {selectedLocation.latitude.toFixed(6)}, {selectedLocation.longitude.toFixed(6)}
              </Typography>
            )}
            <TextField
              fullWidth
              label="标题"
              value={newReport.title}
              onChange={(e) => setNewReport({ ...newReport, title: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="描述"
              value={newReport.description}
              onChange={(e) => setNewReport({ ...newReport, description: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              label="噪声水平 (dB)"
              type="number"
              value={newReport.noise_level}
              onChange={(e) => setNewReport({ ...newReport, noise_level: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="您的姓名"
              value={newReport.reporter_name}
              onChange={(e) => setNewReport({ ...newReport, reporter_name: e.target.value })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="联系方式"
              value={newReport.reporter_contact}
              onChange={(e) => setNewReport({ ...newReport, reporter_contact: e.target.value })}
              margin="normal"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewReportOpen(false)}>取消</Button>
          <Button onClick={handleSubmitReport} variant="contained" color="primary">
            提交举报
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default NoiseMap;
