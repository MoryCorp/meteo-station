import { useState, useEffect } from 'react'
import { ComposedChart, LineChart, Line, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function App() {
  const [current, setCurrent] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [tempHistory, setTempHistory] = useState(null)
  const [pressureHistory, setPressureHistory] = useState(null)
  const [windHistory, setWindHistory] = useState(null)
  const [rainHistory, setRainHistory] = useState(null)

  const [stations, setStations] = useState(null)
  const [tempAverage, setTempAverage] = useState(null)
  const [pressureAverage, setPressureAverage] = useState(null)
  const [windAverage, setWindAverage] = useState(null)

  const [tempPeriod, setTempPeriod] = useState('daily')
  const [pressurePeriod, setPressurePeriod] = useState('daily')
  const [windPeriod, setWindPeriod] = useState('daily')
  const [rainPeriod, setRainPeriod] = useState('daily')

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
  const fetchTempHistory = async (period) => {
    try {
      const res = await fetch(`/api/history/temperature?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setTempHistory(data)
      }
    } catch (err) {
      console.error('Temperature history fetch error:', err)
    }
  }

  // Fetch pressure history
  const fetchPressureHistory = async (period) => {
    try {
      const res = await fetch(`/api/history/pressure?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setPressureHistory(data)
      }
    } catch (err) {
      console.error('Pressure history fetch error:', err)
    }
  }

  // Fetch wind history
  const fetchWindHistory = async (period) => {
    try {
      const res = await fetch(`/api/history/wind?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setWindHistory(data)
      }
    } catch (err) {
      console.error('Wind history fetch error:', err)
    }
  }

  // Fetch rain history
  const fetchRainHistory = async (period) => {
    try {
      const res = await fetch(`/api/history/rain?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setRainHistory(data)
      }
    } catch (err) {
      console.error('Rain history fetch error:', err)
    }
  }

  // Fetch stations data
  const fetchStations = async () => {
    try {
      const res = await fetch('/api/stations')
      if (res.ok) {
        const data = await res.json()
        setStations(data)
      }
    } catch (err) {
      console.error('Stations fetch error:', err)
    }
  }

  // Fetch temperature average
  const fetchTempAverage = async (period) => {
    try {
      const res = await fetch(`/api/history/average/temperature?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setTempAverage(data)
      }
    } catch (err) {
      console.error('Temperature average fetch error:', err)
    }
  }

  // Fetch pressure average
  const fetchPressureAverage = async (period) => {
    try {
      const res = await fetch(`/api/history/average/pressure?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setPressureAverage(data)
      }
    } catch (err) {
      console.error('Pressure average fetch error:', err)
    }
  }

  // Fetch wind average
  const fetchWindAverage = async (period) => {
    try {
      const res = await fetch(`/api/history/average/wind?period=${period}`)
      if (res.ok) {
        const data = await res.json()
        setWindAverage(data)
      }
    } catch (err) {
      console.error('Wind average fetch error:', err)
    }
  }

  // Initial load
  useEffect(() => {
    const loadAll = async () => {
      await fetchCurrent()
      await fetchForecast()
      await fetchStations()
      await fetchTempHistory('daily')
      await fetchPressureHistory('daily')
      await fetchWindHistory('daily')
      await fetchRainHistory('daily')
      await fetchTempAverage('daily')
      await fetchPressureAverage('daily')
      await fetchWindAverage('daily')
      setLoading(false)
    }
    loadAll()

    // Refresh current data every 2 minutes
    const currentInterval = setInterval(() => {
      fetchCurrent()
    }, 120000)

    // Refresh stations every 15 minutes
    const stationsInterval = setInterval(() => {
      fetchStations()
    }, 900000)

    // Refresh history every 10 minutes
    const historyInterval = setInterval(() => {
      fetchTempHistory(tempPeriod)
      fetchPressureHistory(pressurePeriod)
      fetchWindHistory(windPeriod)
      fetchRainHistory(rainPeriod)
      fetchTempAverage(tempPeriod)
      fetchPressureAverage(pressurePeriod)
      fetchWindAverage(windPeriod)
    }, 600000)

    // Refresh all data when tab becomes visible again
    let lastVisibilityTime = Date.now()
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const timeSinceLastVisible = Date.now() - lastVisibilityTime
        // If tab was hidden for more than 5 minutes, refresh everything
        if (timeSinceLastVisible > 300000) {
          fetchCurrent()
          fetchStations()
          fetchTempHistory(tempPeriod)
          fetchPressureHistory(pressurePeriod)
          fetchWindHistory(windPeriod)
          fetchRainHistory(rainPeriod)
          fetchTempAverage(tempPeriod)
          fetchPressureAverage(pressurePeriod)
          fetchWindAverage(windPeriod)
          fetchForecast()
        }
      } else {
        lastVisibilityTime = Date.now()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      clearInterval(currentInterval)
      clearInterval(stationsInterval)
      clearInterval(historyInterval)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  // Refresh history when period changes
  useEffect(() => {
    fetchTempHistory(tempPeriod)
    fetchTempAverage(tempPeriod)
  }, [tempPeriod])

  useEffect(() => {
    fetchPressureHistory(pressurePeriod)
    fetchPressureAverage(pressurePeriod)
  }, [pressurePeriod])

  useEffect(() => {
    fetchWindHistory(windPeriod)
    fetchWindAverage(windPeriod)
  }, [windPeriod])

  useEffect(() => {
    fetchRainHistory(rainPeriod)
  }, [rainPeriod])

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

        {/* Stations Comparison Table */}
        <StationsTable stations={stations} />

        {/* Temperature History */}
        <HistoryChart
          title="Température"
          data={tempHistory}
          averageData={tempAverage}
          period={tempPeriod}
          setPeriod={setTempPeriod}
          renderChart={(data, avgData) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  tickFormatter={(value) => {
                    if (tempPeriod === 'daily') {
                      return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                    }
                    return new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                  }}
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
                  name="IGAROU17"
                />
                {avgData && (
                  <Line
                    type="monotone"
                    dataKey="temp_avg"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Moyenne Garéoult"
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          )}
        />

        {/* Pressure History */}
        <HistoryChart
          title="Pression atmosphérique"
          data={pressureHistory}
          averageData={pressureAverage}
          period={pressurePeriod}
          setPeriod={setPressurePeriod}
          renderChart={(data, avgData) => (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  tickFormatter={(value) => {
                    if (pressurePeriod === 'daily') {
                      return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                    }
                    return new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                  }}
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
                  name="IGAROU17"
                />
                {avgData && (
                  <Line
                    type="monotone"
                    dataKey="pressure_avg"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Moyenne Garéoult"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        />

        {/* Wind Speed History */}
        <HistoryChart
          title="Vent - Vitesse"
          data={windHistory}
          averageData={windAverage}
          period={windPeriod}
          setPeriod={setWindPeriod}
          renderChart={(data, avgData) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  tickFormatter={(value) => {
                    if (windPeriod === 'daily') {
                      return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                    }
                    return new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                  }}
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
                  name="IGAROU17"
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
                {avgData && (
                  <Line
                    type="monotone"
                    dataKey="wind_avg"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Moyenne Garéoult"
                  />
                )}
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
          hideButtons={true}
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  tickFormatter={(value) => {
                    if (windPeriod === 'daily') {
                      return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                    }
                    return new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                  }}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  label={{ value: 'Degrés', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
                  domain={[0, 360]}
                  ticks={[0, 45, 90, 135, 180, 225, 270, 315, 360]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px'
                  }}
                  formatter={(value) => [`${value}°`, 'Direction']}
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
          renderChart={(data) => (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  tickFormatter={(value) => {
                    if (rainPeriod === 'daily') {
                      return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
                    }
                    return new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })
                  }}
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
            <div>⟳ Stations voisines: 15 min</div>
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
          <span className="font-bold text-gray-800">{current.wind_dir}°</span>
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

function HistoryChart({ title, data, averageData, period, setPeriod, hideButtons, renderChart }) {
  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
        <h2 className="text-gray-800 font-bold text-lg mb-4">{title}</h2>
        <div className="text-gray-500 text-center py-8">Données non disponibles</div>
      </div>
    )
  }

  // Merge average data with main data if available
  let mergedData = data.data
  if (averageData && averageData.data && averageData.data.length > 0) {
    // Create a map of average data by timestamp
    const avgMap = {}
    averageData.data.forEach(item => {
      avgMap[item.time] = item
    })

    // Merge the data
    mergedData = data.data.map(item => {
      const avgItem = avgMap[item.time]
      if (avgItem) {
        return {
          ...item,
          temp_avg: avgItem.temp,
          pressure_avg: avgItem.pressure,
          wind_avg: avgItem.wind_speed
        }
      }
      return item
    })
  }

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-gray-800 font-bold text-lg">{title}</h2>
        {!hideButtons && (
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
          </div>
        )}
      </div>
      {renderChart(mergedData, averageData)}
    </div>
  )
}

function StationsTable({ stations }) {
  if (!stations || !stations.stations || stations.stations.length === 0) {
    return null
  }

  return (
    <div className="bg-white border border-gray-300 p-4 rounded-lg shadow-sm">
      <h2 className="text-gray-800 font-bold text-lg mb-4">Stations Garéoult - Comparaison</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-3 text-gray-700 font-semibold">ID</th>
              <th className="text-left py-2 px-3 text-gray-700 font-semibold">Nom</th>
              <th className="text-right py-2 px-3 text-gray-700 font-semibold">Temp (°C)</th>
              <th className="text-right py-2 px-3 text-gray-700 font-semibold">Pression (hPa)</th>
              <th className="text-right py-2 px-3 text-gray-700 font-semibold">Vent (km/h)</th>
              <th className="text-right py-2 px-3 text-gray-700 font-semibold">Direction (°)</th>
              <th className="text-right py-2 px-3 text-gray-700 font-semibold">Observation</th>
            </tr>
          </thead>
          <tbody>
            {stations.stations.map((station, idx) => (
              <tr
                key={idx}
                className={`border-b border-gray-100 ${station.is_main ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
              >
                <td className="py-2 px-3">
                  <span className={`font-mono text-xs ${station.is_main ? 'font-bold text-blue-700' : 'text-gray-600'}`}>
                    {station.id}
                  </span>
                </td>
                <td className="py-2 px-3 text-gray-800">
                  {station.name || 'N/A'}
                  {station.is_main && <span className="ml-2 text-xs text-blue-600 font-semibold">(Station principale)</span>}
                </td>
                <td className="py-2 px-3 text-right font-semibold text-blue-600">
                  {station.temp != null ? station.temp.toFixed(1) : '--'}
                </td>
                <td className="py-2 px-3 text-right font-semibold text-purple-600">
                  {station.pressure != null ? station.pressure.toFixed(1) : '--'}
                </td>
                <td className="py-2 px-3 text-right font-semibold text-cyan-600">
                  {station.wind_speed != null ? station.wind_speed.toFixed(1) : '--'}
                </td>
                <td className="py-2 px-3 text-right font-semibold text-green-600">
                  {station.wind_dir != null ? station.wind_dir : '--'}
                </td>
                <td className="py-2 px-3 text-right text-xs text-gray-500">
                  {station.observation_time ? new Date(station.observation_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
