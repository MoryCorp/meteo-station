import { useState, useEffect } from 'react'
import { ComposedChart, LineChart, Line, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

// Convert wind direction in degrees to cardinal direction
function getCardinalDirection(degrees) {
  if (degrees == null || degrees < 0) return ''

  const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
  const index = Math.round(((degrees % 360) / 22.5))
  return directions[index % 16]
}

function App() {
  const [current, setCurrent] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [tempHistory, setTempHistory] = useState(null)
  const [pressureHistory, setPressureHistory] = useState(null)
  const [windHistory, setWindHistory] = useState(null)
  const [rainHistory, setRainHistory] = useState(null)

  const [tempPeriod, setTempPeriod] = useState('daily')
  const [pressurePeriod, setPressurePeriod] = useState('daily')
  const [windPeriod, setWindPeriod] = useState('daily')
  const [rainPeriod, setRainPeriod] = useState('daily')

  // Mode comparaison
  const [compareMode, setCompareMode] = useState(false)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch current data
  const fetchCurrent = async () => {
    try {
      const res = await fetch('/api/current')
      if (!res.ok) throw new Error('Failed to fetch current data')
      const data = await res.json()
      setCurrent(data)
    } catch (err) {
      setError(err.message)
    }
  }

  // Fetch forecast
  const fetchForecast = async () => {
    try {
      const res = await fetch('/api/forecast')
      if (res.ok) {
        const data = await res.json()
        setForecast(data)
      }
    } catch (err) {
      console.error('Forecast fetch error:', err)
    }
  }

  // Fetch temperature history
  const fetchTempHistory = async (period, compare = false) => {
    try {
      const url = `/api/history/temperature?period=${period}${compare ? '&compare=true' : ''}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setTempHistory(data)
      }
    } catch (err) {
      console.error('Temperature history fetch error:', err)
    }
  }

  // Fetch pressure history
  const fetchPressureHistory = async (period, compare = false) => {
    try {
      const url = `/api/history/pressure?period=${period}${compare ? '&compare=true' : ''}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setPressureHistory(data)
      }
    } catch (err) {
      console.error('Pressure history fetch error:', err)
    }
  }

  // Fetch wind history
  const fetchWindHistory = async (period, compare = false) => {
    try {
      const url = `/api/history/wind?period=${period}${compare ? '&compare=true' : ''}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setWindHistory(data)
      }
    } catch (err) {
      console.error('Wind history fetch error:', err)
    }
  }

  // Fetch rain history
  const fetchRainHistory = async (period, compare = false) => {
    try {
      const url = `/api/history/rain?period=${period}${compare ? '&compare=true' : ''}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setRainHistory(data)
      }
    } catch (err) {
      console.error('Rain history fetch error:', err)
    }
  }

  // Initial load
  useEffect(() => {
    const loadAll = async () => {
      await fetchCurrent()
      await fetchForecast()
      await fetchTempHistory('daily')
      await fetchPressureHistory('daily')
      await fetchWindHistory('daily')
      await fetchRainHistory('daily')
      setLoading(false)
    }
    loadAll()

    // Refresh current data every 2 minutes
    const currentInterval = setInterval(() => {
      fetchCurrent()
    }, 120000)

    // Refresh history every 10 minutes
    const historyInterval = setInterval(() => {
      fetchTempHistory(tempPeriod)
      fetchPressureHistory(pressurePeriod)
      fetchWindHistory(windPeriod)
      fetchRainHistory(rainPeriod)
    }, 600000)

    // Refresh all data when tab becomes visible again
    let lastVisibilityTime = Date.now()
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const timeSinceLastVisible = Date.now() - lastVisibilityTime
        // If tab was hidden for more than 5 minutes, refresh everything
        if (timeSinceLastVisible > 300000) {
          fetchCurrent()
          fetchTempHistory(tempPeriod)
          fetchPressureHistory(pressurePeriod)
          fetchWindHistory(windPeriod)
          fetchRainHistory(rainPeriod)
          fetchForecast()
        }
      } else {
        lastVisibilityTime = Date.now()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      clearInterval(currentInterval)
      clearInterval(historyInterval)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  // Refresh history when period or compare mode changes
  useEffect(() => {
    fetchTempHistory(tempPeriod, compareMode)
  }, [tempPeriod, compareMode])

  useEffect(() => {
    fetchPressureHistory(pressurePeriod, compareMode)
  }, [pressurePeriod, compareMode])

  useEffect(() => {
    fetchWindHistory(windPeriod, compareMode)
  }, [windPeriod, compareMode])

  useEffect(() => {
    fetchRainHistory(rainPeriod, compareMode)
  }, [rainPeriod, compareMode])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-gray-700 text-xl">Chargement des données météo...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-red-600 text-xl">Erreur: {error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-[1800px] mx-auto space-y-4">

        {/* Header */}
        <Header data={current} />

        {/* Current Metrics */}
        <div className="grid grid-cols-4 gap-4">
          <WindMetric data={current} />
          <TempMetric data={current} />
          <PressureMetric data={current} />
          <UVMetric data={current} />
        </div>

        {/* Temperature History */}
        <HistoryChart
          title="Température"
          data={tempHistory}
          period={tempPeriod}
          setPeriod={setTempPeriod}
          compareMode={compareMode}
          setCompareMode={setCompareMode}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: '°C', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="temp_low"
                  fill="#3b82f6"
                  fillOpacity={0.2}
                  stroke="none"
                  name="Min"
                />
                <Area
                  type="monotone"
                  dataKey="temp_high"
                  fill="#ef4444"
                  fillOpacity={0.2}
                  stroke="none"
                  name="Max"
                />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={false}
                  name="Température"
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
          renderCompareChart={(compData) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={compData.current.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: '°C', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                {/* Courbe actuelle - bleue */}
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={false}
                  name={compData.current.label}
                />
                {/* Courbe précédente - grise pointillée */}
                <Line
                  type="monotone"
                  data={compData.previous.data}
                  dataKey="temp"
                  stroke="#9ca3af"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name={compData.previous.label}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        />

        {/* Pressure History */}
        <HistoryChart
          title="Pression atmosphérique"
          data={pressureHistory}
          period={pressurePeriod}
          setPeriod={setPressurePeriod}
          compareMode={compareMode}
          setCompareMode={setCompareMode}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'hPa', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                  domain={['dataMin - 5', 'dataMax + 5']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="pressure"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={false}
                  name="Pression"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
          renderCompareChart={(compData) => (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={compData.current.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'hPa', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                  domain={['dataMin - 5', 'dataMax + 5']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                {/* Courbe actuelle - violette */}
                <Line
                  type="monotone"
                  dataKey="pressure"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={false}
                  name={compData.current.label}
                />
                {/* Courbe précédente - grise pointillée */}
                <Line
                  type="monotone"
                  data={compData.previous.data}
                  dataKey="pressure"
                  stroke="#9ca3af"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name={compData.previous.label}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        />

        {/* Wind Speed History */}
        <HistoryChart
          title="Vent - Vitesse"
          data={windHistory}
          period={windPeriod}
          setPeriod={setWindPeriod}
          compareMode={compareMode}
          setCompareMode={setCompareMode}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'km/h', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="wind_speed"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={false}
                  name="Vitesse"
                />
                <Line
                  type="monotone"
                  dataKey="wind_gust"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="5 5"
                  name="Rafales"
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
          renderCompareChart={(compData) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={compData.current.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'km/h', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                {/* Courbe actuelle - bleue */}
                <Line
                  type="monotone"
                  dataKey="wind_speed"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={false}
                  name={`Vitesse (${compData.current.label})`}
                />
                {/* Courbe précédente - grise pointillée */}
                <Line
                  type="monotone"
                  data={compData.previous.data}
                  dataKey="wind_speed"
                  stroke="#9ca3af"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name={`Vitesse (${compData.previous.label})`}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        />

        {/* Wind Direction History */}
        <HistoryChart
          title="Vent - Direction"
          data={windHistory}
          period={windPeriod}
          setPeriod={setWindPeriod}
          compareMode={compareMode}
          hideCompare={true}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'Direction', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                  domain={[0, 360]}
                  ticks={[0, 45, 90, 135, 180, 225, 270, 315, 360]}
                  tickFormatter={(value) => `${value}° (${getCardinalDirection(value)})`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                  formatter={(value) => [`${value}° (${getCardinalDirection(value)})`, 'Direction']}
                />
                <Line
                  type="monotone"
                  dataKey="wind_dir"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name="Direction"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        />

        {/* Rain History */}
        <HistoryChart
          title="Pluviométrie"
          data={rainHistory}
          period={rainPeriod}
          setPeriod={setRainPeriod}
          compareMode={compareMode}
          setCompareMode={setCompareMode}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="label"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'mm', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                />
                <Bar
                  dataKey="rain"
                  fill="#3b82f6"
                  name="Pluie"
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
          renderCompareChart={(compData) => {
            // Fusionner les données pour afficher les barres côte à côte
            const mergedData = compData.current.data.map((item, idx) => ({
              ...item,
              rain_current: item.rain,
              rain_previous: compData.previous.data[idx]?.rain || 0
            }))
            return (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={mergedData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="label"
                    stroke="#6b7280"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#6b7280"
                    tick={{ fill: '#6b7280', fontSize: 12 }}
                    label={{ value: 'mm', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px'
                    }}
                  />
                  <Bar
                    dataKey="rain_current"
                    fill="#3b82f6"
                    name={compData.current.label}
                  />
                  <Bar
                    dataKey="rain_previous"
                    fill="#9ca3af"
                    name={compData.previous.label}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )
          }}
        />

        {/* Forecast */}
        <ForecastPanel forecast={forecast} />

      </div>
    </div>
  )
}

function Header({ data }) {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const localTime = currentTime.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

  const obsTime = data.observation_time ? new Date(data.observation_time).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }) : 'N/A'

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Station météo Garéoult</h1>
          <div className="text-gray-600 mt-1">Station {data.station_id}</div>
          <div className="mt-2 text-xs text-gray-500 space-y-0.5">
            <div>⟳ Données actuelles: 2 min</div>
            <div>⟳ Historique: 10 min</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-gray-800 text-lg font-semibold">{localTime}</div>
          <div className="text-gray-600 text-sm mt-1">Dernière observation: {obsTime}</div>
          <div className="flex items-center justify-end gap-2 mt-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-green-600 text-sm font-medium">En ligne</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function WindMetric({ data }) {
  const current = data.current
  const seuils = data.seuils.vent

  const speedColor = current.wind_speed >= seuils.danger ? 'text-red-600' :
                     current.wind_speed >= seuils.attention ? 'text-orange-500' :
                     'text-blue-600'

  const gustColor = current.wind_gust >= seuils.danger ? 'text-red-600' :
                    current.wind_gust >= seuils.attention ? 'text-orange-500' :
                    'text-blue-600'

  const cardinalDirection = getCardinalDirection(current.wind_dir)

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="text-gray-600 text-sm font-medium mb-2">Vent</div>
      <div className={`text-4xl font-bold ${speedColor}`}>{current.wind_speed.toFixed(0)}</div>
      <div className="text-gray-500 text-sm">km/h</div>
      <div className="mt-3 space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Rafales:</span>
          <span className={`font-bold ${gustColor}`}>{current.wind_gust.toFixed(0)} km/h</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Direction:</span>
          <span className="font-bold text-gray-800">{current.wind_dir}° ({cardinalDirection})</span>
        </div>
      </div>
    </div>
  )
}

function TempMetric({ data }) {
  const current = data.current

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="text-gray-600 text-sm font-medium mb-2">Température</div>
      <div className="text-4xl font-bold text-blue-600">{current.temp.toFixed(1)}°C</div>
      <div className="mt-3 space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Max 7j:</span>
          <span className="font-bold text-red-600">{data.stats_7d.max_temp?.toFixed(1) || '--'}°C</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Min 7j:</span>
          <span className="font-bold text-blue-600">{data.stats_7d.min_temp?.toFixed(1) || '--'}°C</span>
        </div>
      </div>
    </div>
  )
}

function PressureMetric({ data }) {
  const current = data.current
  const trend = current.pressure_trend

  const trendIcon = trend.trend === 'falling_rapidly' ? '↓↓' :
                    trend.trend === 'falling' ? '↓' :
                    trend.trend === 'rising' ? '↑' :
                    '→'

  const trendColor = trend.trend === 'falling_rapidly' ? 'text-red-600' :
                     trend.trend === 'falling' ? 'text-orange-500' :
                     trend.trend === 'rising' ? 'text-green-600' :
                     'text-gray-500'

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="text-gray-600 text-sm font-medium mb-2">Pression</div>
      <div className="text-4xl font-bold text-purple-600">{current.pressure.toFixed(1)}</div>
      <div className="text-gray-500 text-sm">hPa</div>
      <div className="mt-3 flex items-center gap-2">
        <span className="text-gray-600 text-sm">Tendance 3h:</span>
        <span className={`text-xl font-bold ${trendColor}`}>{trendIcon}</span>
        <span className={`font-bold ${trendColor}`}>{trend.change >= 0 ? '+' : ''}{trend.change}</span>
      </div>
    </div>
  )
}

function UVMetric({ data }) {
  const uv = data.current.uv

  const uvColor = uv >= 8 ? 'text-red-600' :
                  uv >= 6 ? 'text-orange-500' :
                  uv >= 3 ? 'text-yellow-500' :
                  'text-green-600'

  const uvBgColor = uv >= 8 ? 'bg-red-500' :
                    uv >= 6 ? 'bg-orange-500' :
                    uv >= 3 ? 'bg-yellow-500' :
                    'bg-green-500'

  const uvLevel = uv >= 8 ? 'Très élevé' :
                  uv >= 6 ? 'Élevé' :
                  uv >= 3 ? 'Modéré' :
                  'Faible'

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="text-gray-600 text-sm font-medium mb-2">Indice UV</div>
      <div className={`text-4xl font-bold ${uvColor}`}>{uv}</div>
      <div className={`text-sm font-medium mt-1 ${uvColor}`}>{uvLevel}</div>
      <div className="mt-3">
        <div className="w-full bg-gray-200 h-3 rounded overflow-hidden">
          <div
            className={`h-full ${uvBgColor}`}
            style={{ width: `${Math.min(100, (uv / 11) * 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}

function HistoryChart({ title, data, period, setPeriod, compareMode, setCompareMode, hideCompare, renderChart, renderCompareChart }) {
  // Vérifier si on a des données valides
  const hasData = data && (
    (data.compare && data.current?.data?.length > 0) ||
    (!data.compare && data.data?.length > 0)
  )

  if (!hasData) {
    return (
      <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
        <h2 className="text-gray-800 font-bold text-lg mb-4">{title}</h2>
        <div className="text-gray-500 text-center py-8">Données non disponibles</div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-gray-800 font-bold text-lg">{title}</h2>
        <div className="flex items-center gap-2">
          {/* Boutons de période */}
          <div className="flex gap-2">
            <button
              onClick={() => setPeriod('daily')}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                period === 'daily'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              24H
            </button>
            <button
              onClick={() => setPeriod('weekly')}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                period === 'weekly'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              7J
            </button>
            <button
              onClick={() => setPeriod('monthly')}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                period === 'monthly'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              30J
            </button>
            <button
              onClick={() => setPeriod('yearly')}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                period === 'yearly'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Année
            </button>
          </div>

          {/* Séparateur et bouton Comparer */}
          {!hideCompare && setCompareMode && (
            <>
              <div className="w-px h-6 bg-gray-300 mx-2" />
              <button
                onClick={() => setCompareMode(!compareMode)}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  compareMode
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Comparer
              </button>
            </>
          )}
        </div>
      </div>

      {/* Légende en mode comparaison */}
      {compareMode && data.compare && data.current && data.previous && (
        <div className="flex gap-4 mb-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-blue-500" />
            <span className="text-gray-600">{data.current.label}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-gray-400" style={{ borderTop: '2px dashed #9ca3af' }} />
            <span className="text-gray-600">{data.previous.label}</span>
          </div>
        </div>
      )}

      {/* Graphique */}
      {compareMode && data.compare && renderCompareChart ? (
        renderCompareChart(data)
      ) : (
        renderChart(data.compare ? data.current.data : data.data)
      )}
    </div>
  )
}

function ForecastPanel({ forecast }) {
  if (!forecast || !forecast.forecasts || forecast.forecasts.length === 0) {
    return (
      <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
        <h2 className="text-gray-800 font-bold text-lg mb-4">Prévisions 5 jours</h2>
        <div className="text-gray-500 text-center">Prévisions non disponibles</div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <h2 className="text-gray-800 font-bold text-lg mb-4">Prévisions 5 jours</h2>
      <div className="grid grid-cols-5 gap-3">
        {forecast.forecasts.map((day, idx) => (
          <div key={idx} className="bg-gray-50 p-3 rounded border border-gray-200 text-center">
            <div className="text-gray-800 font-semibold mb-2">{day.day}</div>
            <div className="flex justify-center gap-2 text-sm mb-2">
              <span className="text-red-600 font-bold">{day.temp_max}°</span>
              <span className="text-gray-400">/</span>
              <span className="text-blue-600 font-bold">{day.temp_min}°</span>
            </div>
            <div className="w-full bg-gray-200 h-2 rounded overflow-hidden mb-1">
              <div
                className="h-full bg-blue-500"
                style={{ width: `${day.precip_chance}%` }}
              />
            </div>
            <div className="text-blue-600 text-xs font-semibold">
              {day.precip_chance}% | {day.precip_amount.toFixed(1)} mm
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
